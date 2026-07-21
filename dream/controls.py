"""Control-image extraction from the canonical geometry frame (brief §3, step 2).

Depth (primary) + soft-edge/HED (horizon) lock the rocks / horizon / cabin-edge.
These come from the *canonical* frame only (cloudless geometry source), never from
the weather anchor. Results are cached under paths.controls_dir keyed by frame stem
+ output size so we don't re-run the annotators every generation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

from dream.config import apply_edge_crop, crop_signature, resolve_path

_DEPTH_DETECTOR = None
_SOFTEDGE_DETECTOR = None


def _load_detectors():
    global _DEPTH_DETECTOR, _SOFTEDGE_DETECTOR
    if _DEPTH_DETECTOR is None or _SOFTEDGE_DETECTOR is None:
        from controlnet_aux import MidasDetector, PidiNetDetector

        _DEPTH_DETECTOR = MidasDetector.from_pretrained("lllyasviel/Annotators")
        _SOFTEDGE_DETECTOR = PidiNetDetector.from_pretrained("lllyasviel/Annotators")
    return _DEPTH_DETECTOR, _SOFTEDGE_DETECTOR


def _cache_paths(
    controls_dir: Path, stem: str, size: tuple[int, int], crop_sig: str
) -> tuple[Path, Path]:
    w, h = size
    depth = controls_dir / f"{stem}_depth_{w}x{h}_{crop_sig}.png"
    edge = controls_dir / f"{stem}_softedge_{w}x{h}_{crop_sig}.png"
    return depth, edge


def build_control_images(
    frame_path: Path | str,
    size: tuple[int, int],
    controls_dir: Path | str,
    *,
    edge_crop: dict[str, Any] | None = None,
    refresh: bool = False,
) -> tuple[Image.Image, Image.Image]:
    """Return (depth_image, softedge_image) at `size`, building + caching as needed.

    `edge_crop` is applied to the source frame before annotation so the control
    maps carry no window-edge vignette; it is baked into the cache key.
    """
    frame_path = Path(frame_path)
    controls_dir = resolve_path(controls_dir)
    controls_dir.mkdir(parents=True, exist_ok=True)

    crop_sig = crop_signature(edge_crop)
    depth_path, edge_path = _cache_paths(controls_dir, frame_path.stem, size, crop_sig)

    if not refresh and depth_path.exists() and edge_path.exists():
        return (
            Image.open(depth_path).convert("RGB"),
            Image.open(edge_path).convert("RGB"),
        )

    src = Image.open(frame_path).convert("RGB")
    src = apply_edge_crop(src, edge_crop)
    depth_det, edge_det = _load_detectors()

    # detect_resolution kept close to the source; output resized to the SDXL size
    depth = depth_det(src, detect_resolution=768, image_resolution=max(size))
    edge = edge_det(src, detect_resolution=768, image_resolution=max(size), safe=True)

    depth = depth.convert("RGB").resize(size, Image.BICUBIC)
    edge = edge.convert("RGB").resize(size, Image.BICUBIC)

    depth.save(depth_path)
    edge.save(edge_path)
    return depth, edge
