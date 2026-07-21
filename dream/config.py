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


def crop_signature(edge_crop: dict[str, Any] | None) -> str:
    """Short stable tag for cache filenames, e.g. 't9r12'."""
    if not edge_crop:
        return "full"
    parts = []
    for k in ("top", "right", "bottom", "left"):
        v = float(edge_crop.get(k, 0.0) or 0.0)
        if v:
            parts.append(f"{k[0]}{int(round(v * 100))}")
    return "".join(parts) if parts else "full"


def apply_edge_crop(image, edge_crop: dict[str, Any] | None):
    """Trim fractional insets from each edge (GoPro fisheye / window-edge border).

    Applied identically to the anchor init and the canonical control source so the
    two stay geometrically aligned. No-op when edge_crop is empty/zero.
    """
    if not edge_crop:
        return image
    w, h = image.size
    left = int(round(w * float(edge_crop.get("left", 0.0) or 0.0)))
    top = int(round(h * float(edge_crop.get("top", 0.0) or 0.0)))
    right = w - int(round(w * float(edge_crop.get("right", 0.0) or 0.0)))
    bottom = h - int(round(h * float(edge_crop.get("bottom", 0.0) or 0.0)))
    if (left, top, right, bottom) == (0, 0, w, h):
        return image
    return image.crop((left, top, right, bottom))


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
