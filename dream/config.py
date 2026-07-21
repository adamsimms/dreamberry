"""Dream-engine configuration loading + device/dtype resolution."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DREAM_CONFIG_PATH = REPO_ROOT / "config" / "dream.yaml"


def _load_dotenv() -> None:
    """Load .env (HF_TOKEN etc.) if python-dotenv is available. Best-effort."""
    try:
        from dotenv import load_dotenv
    except Exception:  # noqa: BLE001
        return
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def load_dream_config(path: Path | str | None = None) -> dict[str, Any]:
    _load_dotenv()
    p = Path(path) if path else DREAM_CONFIG_PATH
    with open(p) as f:
        cfg = yaml.safe_load(f)
    return cfg


def load_dataset_config(dream_cfg: dict[str, Any]) -> dict[str, Any]:
    rel = dream_cfg["paths"]["dataset_config"]
    p = Path(rel)
    if not p.is_absolute():
        p = REPO_ROOT / rel
    with open(p) as f:
        return yaml.safe_load(f)


def resolve_path(rel: str | Path) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else REPO_ROOT / p


def canonical_frame_path(dream_cfg: dict[str, Any]) -> Path:
    ds = load_dataset_config(dream_cfg)
    raw_dir = resolve_path(ds["paths"]["raw_dir"])
    return raw_dir / ds["canonical_frame"]


def resolve_device(requested: str) -> str:
    if requested and requested != "auto":
        return requested
    try:
        import torch
    except Exception:  # noqa: BLE001
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def resolve_dtype(requested: str, device: str):
    import torch

    if requested == "float16":
        return torch.float16
    if requested == "float32":
        return torch.float32
    # auto
    return torch.float32 if device == "cpu" else torch.float16


def hf_token() -> str | None:
    _load_dotenv()
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
