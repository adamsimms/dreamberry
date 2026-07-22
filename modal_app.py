"""Dreamberry Modal app — hourly GPU cron + R2 delivery (M5 / issues #16–#17, #12).

Modal owns schedule + L40S. Cloudflare owns R2 (this app writes) and Pages (M6).

Deploy:
  .venv/bin/modal deploy modal_app.py

One-shot (no cron wait):
  .venv/bin/modal run modal_app.py::hourly_tick

Sync corpus to the data Volume first (see docs/M5-PLATFORM.md):
  .venv/bin/python scripts/sync_modal_data.py

Prefetch SUPIR weights onto the HF Volume (once):
  .venv/bin/modal run modal_app.py::prefetch_supir
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
    "third_party",
]

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1", "libglib2.0-0", "git")
    # CUDA torch + xformers must come from the PyTorch index (PyPI xformers is
    # CPU-only and breaks SUPIR tile VAE).
    .pip_install(
        "torch==2.10.0",
        "torchvision==0.25.0",
        "xformers==0.0.35",
        index_url="https://download.pytorch.org/whl/cu128",
    )
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
        # Diffusion stack (torch already pinned above)
        "diffusers>=0.30",
        "transformers>=4.44",
        "accelerate>=0.33",
        "safetensors>=0.4",
        "huggingface_hub>=0.24",
        "controlnet-aux>=0.0.9",
        "opencv-python-headless>=4.9",
        "lpips>=0.1.4",
        # SUPIR (Fanghua-Yu) — do NOT pin their frozen transformers==4.28
        "einops>=0.7",
        "omegaconf>=2.3",
        "open-clip-torch==2.24.0",  # >2.24 breaks SUPIR CLIP attn_mask (77×77 vs 1×1)
        "pytorch-lightning>=2.1",
        "kornia>=0.6.9",
        "timm>=0.9",
        "openai-clip>=1.0.1",
        # Runtime deps for k_diffusion.sampling only (full k-diffusion pulls
        # wandb/clean-fid/etc. and blows up Modal's pip resolver).
        "scipy>=1.11.0",
        "torchsde>=0.2.6",
        "torchdiffeq>=0.2.3",
    )
    .run_commands(
        # SUPIR's RestoreEDMSampler imports k_diffusion.sampling — install the
        # package without its heavy optional deps, then empty __init__.py so
        # `from k_diffusion.sampling import …` does not pull training extras.
        "pip install --no-deps 'k-diffusion==0.1.1.post1'",
        "python -c \"from pathlib import Path; import site; "
        "p = Path(site.getsitepackages()[0]) / 'k_diffusion' / '__init__.py'; "
        "p.write_text('')\"",
        # Verify sampling imports without the training extras.
        "python -c \"from k_diffusion.sampling import get_sigmas_karras; print('k_diffusion.sampling ok')\"",
        # Official SUPIR code (LLaVA optional — we pass the weather prompt instead).
        "git clone --depth 1 https://github.com/Fanghua-Yu/SUPIR.git /opt/SUPIR",
    )
    .env(
        {
            "HF_HOME": "/models",
            "PYTHONPATH": "/root/dreamberry",
            "HF_XET_HIGH_PERFORMANCE": "1",
            "SUPIR_ROOT": "/opt/SUPIR",
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
        "sidecar_size": (
            {
                "width": (result.sidecar or {}).get("width"),
                "height": (result.sidecar or {}).get("height"),
                "upscale": (result.sidecar or {}).get("upscale"),
            }
            if result.sidecar
            else None
        ),
        "healthcheck": ping,
    }


_VOLUMES = {
    "/models": hf_vol,
    "/root/dreamberry/data": data_vol,
}

# SUPIR + SDXL need headroom beyond the dream stack alone.
_TIMEOUT = 45 * 60
_MEMORY = 65536


@app.function(
    image=image,
    gpu="L40S",
    timeout=_TIMEOUT,
    memory=_MEMORY,
    volumes=_VOLUMES,
    secrets=secrets,
    # :05 past each hour — Open-Meteo current-hour row usually present.
    schedule=modal.Cron("5 * * * *"),
)
def hourly_tick() -> dict:
    """Scheduled live hour: weather → generate → gate → SUPIR → R2."""
    return _run_tick(dial=0.0)


@app.function(
    image=image,
    gpu="L40S",
    timeout=_TIMEOUT,
    memory=_MEMORY,
    volumes=_VOLUMES,
    secrets=secrets,
)
def run_once(dial: float = 0.0) -> dict:
    """Manual one-shot for smoke tests (`modal run modal_app.py::run_once`)."""
    return _run_tick(dial=dial)


@app.function(
    image=image,
    timeout=60 * 60,
    memory=8192,
    volumes={"/models": hf_vol},
    secrets=secrets,
)
def prefetch_supir() -> dict:
    """Download SUPIR + SDXL ckpts into the HF Volume (no GPU needed)."""
    import os
    import sys

    sys.path.insert(0, "/root/dreamberry")
    os.chdir("/root/dreamberry")
    os.environ.setdefault("HF_HOME", "/models")

    from dream.config import load_dream_config
    from dream.upscale import _resolve_weights

    up = dict(load_dream_config().get("upscale") or {})
    up["download_weights"] = True
    sdxl, f_ckpt, q_ckpt = _resolve_weights(up)
    hf_vol.commit()
    return {
        "sdxl": str(sdxl),
        "supir_f": str(f_ckpt),
        "supir_q": str(q_ckpt),
        "sdxl_bytes": sdxl.stat().st_size,
        "supir_f_bytes": f_ckpt.stat().st_size,
    }


@app.local_entrypoint()
def main(dial: float = 0.0):
    """`modal run modal_app.py` → one remote tick."""
    out = run_once.remote(dial=dial)
    print(out)
