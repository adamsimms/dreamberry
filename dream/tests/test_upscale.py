"""Unit tests for publish upscale helpers (M4 / issue #12)."""

from __future__ import annotations

from PIL import Image

from dream.upscale import target_size, upscale_for_publish


def test_target_size_defaults():
    assert target_size({}) == (4000, 3000)
    assert target_size({"upscale": {"target_width": 2000, "target_height": 1500}}) == (
        2000,
        1500,
    )


def test_upscale_disabled_passthrough():
    img = Image.new("RGB", (64, 48), (10, 20, 30))
    out = upscale_for_publish(img, {"upscale": {"enabled": False}})
    assert out.image.size == (64, 48)
    assert out.meta["upscale"]["enabled"] is False


def test_lanczos_to_cloudberry_size():
    img = Image.new("RGB", (1024, 768), (40, 50, 60))
    cfg = {
        "upscale": {
            "enabled": True,
            "backend": "lanczos",
            "target_width": 4000,
            "target_height": 3000,
        }
    }
    out = upscale_for_publish(img, cfg, prompt="test", seed=1)
    assert out.image.size == (4000, 3000)
    assert out.meta["upscale"]["backend"] == "lanczos"
    assert out.meta["upscale"]["native_width"] == 1024
    assert out.meta["upscale"]["native_height"] == 768


def test_hourly_publish_upscales_when_enabled(tmp_path):
    """Accepted frames are published at target size (Lanczos backend)."""
    from types import SimpleNamespace

    from dream.gates.evaluate import FrameEvaluation
    from dream.hourly import OUTCOME_PUBLISHED, run_hourly
    from dream.tests.test_hourly import NOW, FakeEngine, _eval, _fresh_packet

    engine = FakeEngine()
    # FakeEngine returns 8×8; Lanczos will stretch to target.
    result = run_hourly(
        dial=0.0,
        packet=_fresh_packet(),
        engine=engine,
        evaluate_fn=lambda *a: _eval("pass", "pass"),
        now=NOW,
        dream_cfg={
            "generation": {"width": 8, "height": 8},
            "upscale": {
                "enabled": True,
                "backend": "lanczos",
                "target_width": 40,
                "target_height": 30,
            },
        },
        gates_cfg={},
        weather_cfg={"live": {"staleness_hours": 3.0}},
        dataset_cfg={},
        hourly_cfg={
            "retries": 0,
            "base_seed": 0,
            "paths": {
                "public_dir": str(tmp_path / "public"),
                "archive_dir": str(tmp_path / "archive"),
            },
        },
    )
    assert result.outcome == OUTCOME_PUBLISHED
    assert result.sidecar["width"] == 40
    assert result.sidecar["height"] == 30
    assert result.sidecar["upscale"]["backend"] == "lanczos"
    from PIL import Image as _Image

    published = _Image.open(tmp_path / "public" / "current.webp")
    assert published.size == (40, 30)
