"""Thumb encode smoke test."""

from __future__ import annotations

from io import BytesIO

from PIL import Image

from dream.thumbs import THUMB_WIDTH, encode_thumb_webp, thumb_key


def test_thumb_key():
    assert thumb_key("2026-10-16T12:30:00Z_DREAM2073").endswith(
        "thumbs/2026-10-16T12:30:00Z_DREAM2073.webp"
    )


def test_encode_thumb_webp_shrinks():
    img = Image.new("RGB", (1024, 768), (12, 34, 56))
    raw = encode_thumb_webp(img)
    out = Image.open(BytesIO(raw))
    assert out.format == "WEBP"
    assert out.size[0] == THUMB_WIDTH
    assert len(raw) < 80_000
