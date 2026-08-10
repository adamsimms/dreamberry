"""Focused tests for DreamEngine generation hooks."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from dream.anchor import Anchor
from dream.dial import DialParams
from dream.pipeline import DreamEngine


class _FakePipe:
    def __init__(self) -> None:
        self.ip_scale = None
        self.call_kwargs = None

    def set_ip_adapter_scale(self, scale: float) -> None:
        self.ip_scale = scale

    def __call__(self, **kwargs):
        self.call_kwargs = kwargs
        return SimpleNamespace(images=[Image.new("RGB", (16, 12), "black")])


def _engine_cfg(tmp_path: Path, **extra) -> dict:
    cfg = {
        "models": {
            "base": "base",
            "vae": "vae",
            "controlnet_depth": "depth",
            "controlnet_softedge": "edge",
            "ip_adapter_repo": "ip",
            "ip_adapter_weight": "ip.bin",
            "lora_path": None,
        },
        "runtime": {"device": "cpu", "use_ip_adapter": True},
        "generation": {
            "width": 16,
            "height": 12,
            "controlnet_depth_base": 1.0,
            "controlnet_softedge_base": 0.7,
            "steps": 1,
            "guidance_scale": 1.0,
            "negative_prompt": None,
            "edge_crop": None,
        },
        "paths": {"controls_dir": str(tmp_path)},
    }
    cfg.update(extra)
    return cfg


def _patch_engine(engine: DreamEngine, pipe: _FakePipe, anchor_path: Path, monkeypatch):
    def fake_load() -> None:
        engine._pipe = pipe
        engine._dtype = "float32"
        engine._use_ip_adapter = True
        engine._has_lora = False

    monkeypatch.setattr(engine, "load", fake_load)
    monkeypatch.setattr(
        "dream.pipeline.build_control_images",
        lambda *args, **kwargs: (
            Image.new("RGB", (16, 12)),
            Image.new("RGB", (16, 12)),
        ),
    )
    monkeypatch.setattr(
        "dream.pipeline.canonical_frame_path",
        lambda cfg: anchor_path,
    )


def test_generate_uses_and_reports_params_override(tmp_path: Path, monkeypatch):
    anchor_path = tmp_path / "anchor.jpg"
    Image.new("RGB", (16, 12), "grey").save(anchor_path)

    engine = DreamEngine(_engine_cfg(tmp_path))
    pipe = _FakePipe()
    _patch_engine(engine, pipe, anchor_path, monkeypatch)

    params = DialParams(
        dial=0.0,
        denoise_strength=0.70,
        controlnet_scale=0.50,
        ip_adapter_scale=0.25,
        lora_scale=0.20,
        defocus_strength=0.0,
    )
    anchor = Anchor("anchor.jpg", anchor_path, 0.1, "weather_nn")
    result = engine.generate(
        {"solar_elevation": -20.0, "month": 7},
        dial=0.0,
        params_override=params,
        prompt="night",
        anchor=anchor,
        seed=0,
    )

    assert pipe.ip_scale == 0.25
    assert pipe.call_kwargs["strength"] == 0.70
    assert pipe.call_kwargs["controlnet_conditioning_scale"] == [0.50, 0.35]
    assert result.sidecar["dial"] == 0.0
    assert result.sidecar["dial_params"] == params.as_dict()


def test_generate_applies_night_lighting_from_packet(tmp_path: Path, monkeypatch):
    anchor_path = tmp_path / "anchor.jpg"
    Image.new("RGB", (16, 12), "grey").save(anchor_path)

    engine = DreamEngine(
        _engine_cfg(
            tmp_path,
            night_lighting={
                "enabled": True,
                "solar_elevation_deg": -6.0,
                "denoise_strength": 0.70,
                "controlnet_scale": 0.50,
                "ip_adapter_scale": 0.25,
                "defocus_strength": 0.0,
            },
        )
    )
    pipe = _FakePipe()
    _patch_engine(engine, pipe, anchor_path, monkeypatch)

    anchor = Anchor("anchor.jpg", anchor_path, 0.1, "weather_nn")
    result = engine.generate(
        {"solar_elevation": -20.0, "month": 7},
        dial=0.0,
        prompt="night",
        anchor=anchor,
        seed=0,
    )

    assert pipe.ip_scale == 0.25
    assert pipe.call_kwargs["strength"] == 0.70
    assert pipe.call_kwargs["controlnet_conditioning_scale"] == [0.50, 0.35]
    assert result.sidecar["dial"] == 0.0
    assert result.sidecar["dial_params"]["denoise_strength"] == 0.70
    assert result.sidecar["dial_params"]["controlnet_scale"] == 0.50
    assert result.sidecar["dial_params"]["ip_adapter_scale"] == 0.25


def test_generate_day_keeps_dial_zero_lock(tmp_path: Path, monkeypatch):
    anchor_path = tmp_path / "anchor.jpg"
    Image.new("RGB", (16, 12), "grey").save(anchor_path)

    engine = DreamEngine(
        _engine_cfg(
            tmp_path,
            night_lighting={
                "enabled": True,
                "solar_elevation_deg": -6.0,
                "denoise_strength": 0.70,
                "controlnet_scale": 0.50,
                "ip_adapter_scale": 0.25,
                "defocus_strength": 0.0,
            },
        )
    )
    pipe = _FakePipe()
    _patch_engine(engine, pipe, anchor_path, monkeypatch)

    anchor = Anchor("anchor.jpg", anchor_path, 0.1, "weather_nn")
    result = engine.generate(
        {"solar_elevation": 35.0, "month": 7},
        dial=0.0,
        prompt="daytime",
        anchor=anchor,
        seed=0,
    )

    assert pipe.ip_scale == 0.70
    assert pipe.call_kwargs["strength"] == 0.35
    assert result.sidecar["dial_params"]["denoise_strength"] == 0.35
    assert result.sidecar["dial_params"]["controlnet_scale"] == 0.90
