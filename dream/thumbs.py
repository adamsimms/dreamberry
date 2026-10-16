"""Small WebP thumbs for the archive studio gallery (issue #37).

Stored at ``archive/thumbs/<dream_id>.webp`` so the browse UI never loads
full-resolution PNGs in the day grid.
"""

from __future__ import annotations

import io
from typing import Any

from PIL import Image

from dream.storage import ARCHIVE_PREFIX, R2Store

__all__ = [
    "THUMB_PREFIX",
    "THUMB_WIDTH",
    "thumb_key",
    "encode_thumb_webp",
    "put_archive_thumb",
]

THUMB_PREFIX = f"{ARCHIVE_PREFIX}thumbs/"
THUMB_WIDTH = 288


def thumb_key(dream_id: str) -> str:
    return f"{THUMB_PREFIX}{dream_id}.webp"


def encode_thumb_webp(image: Image.Image, *, width: int = THUMB_WIDTH) -> bytes:
    """Lossy WebP thumb (~Cloudberry thumb budget)."""
    rgb = image.convert("RGB")
    w, h = rgb.size
    if w > width:
        nh = max(1, round(h * (width / w)))
        rgb = rgb.resize((width, nh), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    rgb.save(buf, format="WEBP", quality=72, method=4)
    return buf.getvalue()


def put_archive_thumb(
    store: R2Store,
    *,
    dream_id: str,
    image: Image.Image,
) -> str:
    key = thumb_key(dream_id)
    store.put_bytes(
        key,
        encode_thumb_webp(image),
        content_type="image/webp",
        cache_control="public, max-age=86400",
    )
    return key


def put_archive_thumb_from_png_bytes(store: R2Store, *, dream_id: str, png: bytes) -> str:
    img = Image.open(io.BytesIO(png))
    return put_archive_thumb(store, dream_id=dream_id, image=img)
