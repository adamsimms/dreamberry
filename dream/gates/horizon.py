"""Horizon-line extraction + stability vs the canonical frame (issue #9 / #11).

The whole scene is "how far can you see the islands," so the sea/sky boundary is
the single most identity-bearing edge. We estimate a per-column horizon profile
(row of strongest vertical brightness gradient in the central band) and compare
the generated profile against the canonical frame's; displacement is the mean
absolute row difference normalized by image height.

Pure NumPy/OpenCV — no learned models, so this is fully unit-testable.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

# Central vertical band to search for the horizon (fractions of height). The
# horizon in this fixed window sits a bit below mid-frame; searching a band
# avoids locking onto sky cloud edges or foreground rock.
_BAND_TOP = 0.20
_BAND_BOTTOM = 0.75


def _to_gray(image: Image.Image, width: int) -> np.ndarray:
    h = max(1, round(image.height * width / image.width))
    g = image.convert("L").resize((width, h), Image.BILINEAR)
    return np.asarray(g, dtype=np.float32) / 255.0


def horizon_profile(image: Image.Image, width: int = 256) -> np.ndarray:
    """Per-column horizon row (normalized 0-1 height). Robust to flat skies."""
    gray = _to_gray(image, width)
    h, w = gray.shape
    top = int(h * _BAND_TOP)
    bottom = int(h * _BAND_BOTTOM)
    band = gray[top:bottom, :]
    if band.shape[0] < 3:
        return np.full(w, 0.5, dtype=np.float32)

    # Vertical gradient; the horizon is where brightness drops from sky to sea.
    grad = np.abs(np.diff(band, axis=0))
    rows = np.argmax(grad, axis=0).astype(np.float32)  # per column, within band
    # Light smoothing across columns to reject per-column noise.
    kernel = np.ones(9, dtype=np.float32) / 9.0
    rows = np.convolve(rows, kernel, mode="same")
    # Map band-relative row → full-image normalized height.
    return (rows + top) / float(h)


def horizon_displacement(
    image: Image.Image,
    canonical: Image.Image,
    *,
    width: int = 256,
) -> float:
    """Mean |Δ horizon row| between image and canonical, as a fraction of height."""
    a = horizon_profile(image, width)
    b = horizon_profile(canonical, width)
    n = min(len(a), len(b))
    return float(np.mean(np.abs(a[:n] - b[:n])))
