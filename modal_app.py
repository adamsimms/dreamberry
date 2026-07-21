"""Dreamberry Modal app — hourly GPU cron + R2 delivery (M5 / issues #16–#17).

Modal owns schedule + L40S. Cloudflare owns R2 (this app writes) and Pages (M6).

Deploy:
  .venv/bin/modal deploy modal_app.py

One-shot (no cron wait):
  .venv/bin/modal run modal_app.py::hourly_tick

Sync corpus to the data Volume first (see docs/M5-PLATFORM.md):
  .venv/bin/python scripts/sync_modal_data.py
"""

from __future__ import annotations

from pathlib import Path

import modal

REPO = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------

app = modal.App("dreamberry")

hf_vol = modal.Volume.from_name("dreamberry-hf-cache", create_if_missing=True)
data_vol = modal.Volume.from_name("dreamberry-data", create_if_missing=True)

# Secret `dreamberry` must contain at least:
#   HF_TOKEN, CF_R2_BUCKET, CF_R2_ENDPOINT, CF_R2_ACCESS_KEY_ID, CF_R2_SECRET,
#   CF_R2_PUBLIC_BASE_URL, HEALTH_PING_URL
secrets = [modal.Secret.from_name("dreamberry")]

_IGNORE = [
    ".git",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    # Entire data/ comes from the dreamberry-data Volume (raw + indexes + gates).
    # Mounting a Volume over a non-empty image path fails.
    "data",
    "*.pyc",
    ".DS_Store",
    ".env",
    ".env.*",
]

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1", "libglib2.0-0")
    .pip_install(
        # Light deps
        "Pillow>=10.0.0",
        "PyYAML>=6.0",
        "requests>=2.31.0",
        "astral>=3.2",
        "python-dateutil>=2.8.0",
        "python-dotenv>=1.0",
        "boto3>=1.34",
        "numpy>=1.26",
        # GPU / diffusion stack (CUDA wheels resolve on Modal's Linux)
        "torch>=2.3",
        "torchvision>=0.18",
        "diffusers>=0.30",
        "transformers>=4.44",
        "accelerate>=0.33",
        "safetensors>=0.4",
        "huggingface_hub>=0.24",
        "controlnet-aux>=0.0.9",
        "opencv-python-headless>=4.9",
        "lpips>=0.1.4",
    )
    .env(
        {
            "HF_HOME": "/models",
            "PYTHONPATH": "/root/dreamberry",
            "HF_XET_HIGH_PERFORMANCE": "1",
        }
    )
    .add_local_dir(
        str(REPO),
        remote_path="/root/dreamberry",
        ignore=_IGNORE,
    )
)


def _run_tick(*, dial: float = 0.0) -> dict:
    """Shared body for cron + manual run (executed inside the container)."""
    import os
    import sys

    sys.path.insert(0, "/root/dreamberry")
    os.chdir("/root/dreamberry")

    from dream.healthcheck import ping_healthcheck
    from dream.hourly import OUTCOME_SIGNAL_LOST, run_hourly
    from dream.storage import R2Store, r2_config_from_env

    store = R2Store(r2_config_from_env())
    result = run_hourly(dial=dial, store=store, write=True)

    # Dead-man: a completed tick (including weather-silence hold) is healthy.
    # Only signal_lost (channel dead) fails the check.
    ping = ping_healthcheck(failed=(result.outcome == OUTCOME_SIGNAL_LOST))

    return {
        "outcome": result.outcome,
        "failure_mode": result.failure_mode,
        "hold_reason": result.hold_reason,
        "dream_id": result.dream_id,
        "attempts": result.attempts,
        "status": result.status,
        "healthcheck": ping,
    }


@app.function(
    image=image,
    gpu="L40S",
    timeout=30 * 60,
    memory=32768,
    volumes={
        "/models": hf_vol,
        "/root/dreamberry/data": data_vol,
    },
    secrets=secrets,
    # :05 past each hour — Open-Meteo current-hour row usually present.
    schedule=modal.Cron("5 * * * *"),
)
def hourly_tick() -> dict:
    """Scheduled live hour: weather → generate → gate → R2."""
    return _run_tick(dial=0.0)


@app.function(
    image=image,
    gpu="L40S",
    timeout=30 * 60,
    memory=32768,
    volumes={
        "/models": hf_vol,
        "/root/dreamberry/data": data_vol,
    },
    secrets=secrets,
)
def run_once(dial: float = 0.0) -> dict:
    """Manual one-shot for smoke tests (`modal run modal_app.py::run_once`)."""
    return _run_tick(dial=dial)


@app.local_entrypoint()
def main(dial: float = 0.0):
    """`modal run modal_app.py` → one remote tick."""
    out = run_once.remote(dial=dial)
    print(out)
