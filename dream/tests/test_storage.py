"""Unit tests for R2 storage helpers (M5 / issues #16–#17).

Uses an in-memory fake store — no network. Encoding tests check PNG/WebP
round-trips stay lossless at the pixel level for tiny images.
"""

from __future__ import annotations

import json
from io import BytesIO

from PIL import Image

from dream.storage import (
    CURRENT_IMAGE_KEY,
    STATUS_KEY,
    encode_archive_png,
    encode_current_webp,
    next_dream_number_from_names,
    save_local_publish,
)


def test_next_dream_number_from_names():
    assert next_dream_number_from_names([]) == 1
    assert (
        next_dream_number_from_names(
            [
                "archive/2026-07-21T12:00:00.000Z_DREAM001.png",
                "archive/2026-07-21T13:00:00.000Z_DREAM007.png",
                "archive/2026-07-21T13:00:00.000Z_DREAM007.json",
            ]
        )
        == 8
    )


def test_encode_archive_png_roundtrip():
    img = Image.new("RGB", (4, 3), (10, 20, 30))
    raw = encode_archive_png(img)
    out = Image.open(BytesIO(raw))
    assert out.format == "PNG"
    assert out.tobytes() == img.tobytes()


def test_encode_current_webp_lossless_roundtrip():
    img = Image.new("RGB", (4, 3), (10, 20, 30))
    raw = encode_current_webp(img)
    out = Image.open(BytesIO(raw)).convert("RGB")
    assert Image.open(BytesIO(raw)).format == "WEBP"
    assert out.tobytes() == img.tobytes()


def test_save_local_publish_layout(tmp_path):
    img = Image.new("RGB", (8, 8), (1, 2, 3))
    sidecar = {
        "generated_at": "2026-07-21T00:00:00+00:00",
        "labeled": "generated",
        "dial": 0.0,
        "dial_params": {},
        "prompt": "x",
        "seed": 0,
        "width": 8,
        "height": 8,
        "anchor_frame": "a.JPG",
        "anchor_source": "archive",
        "models": {
            "base": "b",
            "vae": "v",
            "controlnet_depth": "d",
            "controlnet_softedge": "e",
        },
        "weather_packet": {},
        "dream_id": "2026-07-21T00:00:00.000Z_DREAM001",
    }
    status = {"current": "current.webp", "hold": False}
    pub = tmp_path / "current"
    arch = tmp_path / "archive"
    save_local_publish(
        image=img,
        sidecar=sidecar,
        status=status,
        dream_id="2026-07-21T00:00:00.000Z_DREAM001",
        public_dir=pub,
        archive_dir=arch,
    )
    assert (arch / "2026-07-21T00:00:00.000Z_DREAM001.png").exists()
    assert (arch / "2026-07-21T00:00:00.000Z_DREAM001.json").exists()
    assert (pub / "current.webp").exists()
    assert (pub / "current.json").exists()
    assert json.loads((pub / "status.json").read_text())["current"] == "current.webp"


class FakeR2:
    """Minimal stand-in for R2Store used by hourly integration tests."""

    def __init__(self):
        self.objects: dict[str, bytes] = {}
        self.statuses: list[dict] = []

    def next_dream_number(self) -> int:
        return next_dream_number_from_names(
            [k for k in self.objects if k.startswith("archive/") and k.endswith(".png")]
        )

    def read_status(self) -> dict:
        raw = self.objects.get(STATUS_KEY)
        return json.loads(raw.decode()) if raw else {}

    def publish_hold(self, status):
        self.statuses.append(dict(status))
        self.objects[STATUS_KEY] = (json.dumps(status) + "\n").encode()
        return {"status": STATUS_KEY}

    def publish_frame(self, *, dream_id, image, sidecar, status):
        from dream.storage import encode_archive_png, encode_current_webp

        png_key = f"archive/{dream_id}.png"
        self.objects[png_key] = encode_archive_png(image)
        self.objects[f"archive/{dream_id}.json"] = (
            json.dumps(dict(sidecar)) + "\n"
        ).encode()
        self.objects[CURRENT_IMAGE_KEY] = encode_current_webp(image)
        self.objects[STATUS_KEY] = (json.dumps(dict(status)) + "\n").encode()
        return {"archive_png": png_key, "current": CURRENT_IMAGE_KEY, "status": STATUS_KEY}

    def publish_signal_lost(self, *, image, status):
        from dream.storage import SIGNAL_LOST_KEY, encode_current_webp

        self.objects[SIGNAL_LOST_KEY] = encode_current_webp(image)
        self.objects[STATUS_KEY] = (json.dumps(dict(status)) + "\n").encode()
        return {"signal_lost": SIGNAL_LOST_KEY, "status": STATUS_KEY}

    def put_json(self, key, obj):
        self.objects[key] = (json.dumps(dict(obj)) + "\n").encode()
