"""Unit tests for provenance sidecar schema."""

from __future__ import annotations

from pathlib import Path

import pytest

from dream.anchor import Anchor
from dream.dial import dial_schedule
from dream.sidecar import (
    LABELED_GENERATED,
    ProvenanceSidecar,
    build_sidecar,
    validate_sidecar,
    write_sidecar,
)

_SAMPLE_PACKET = {
    "time_local": "2026-07-21T17:00",
    "cloud_cover": 100,
    "visibility": 55960.0,
    "weather_code": 3,
    "relative_humidity_2m": 45,
    "wind_speed_10m": 21.6,
    "wind_direction_10m": 250,
    "shortwave_radiation": 584.0,
    "temperature_2m": 26.4,
    "precipitation": 0.0,
    "wave_ht_sig": None,
    "solar_elevation": 35.2,
    "month": 7,
    "after_solar_noon": True,
    "timezone": "America/St_Johns",
    "latitude": 49.2026,
    "longitude": -53.4859,
    "source": "open-meteo-forecast+wyi",
    "fetched_at": "2026-07-21T20:30:00+00:00",
}

_MODELS = {
    "base": "stabilityai/stable-diffusion-xl-base-1.0",
    "vae": "madebyollin/sdxl-vae-fp16-fix",
    "controlnet_depth": "diffusers/controlnet-depth-sdxl-1.0-small",
    "controlnet_softedge": "alimama-creative/EcomXL_controlnet_softedge",
    "ip_adapter_repo": "h94/IP-Adapter",
    "ip_adapter_weight": "ip-adapter_sdxl.bin",
    "lora_path": None,
    "use_ip_adapter": True,
}

_ANCHOR = Anchor(
    filename="2017-09-18T09:59:44.000Z_GOPR2537.JPG",
    path=Path("data/raw/2017-09-18T09:59:44.000Z_GOPR2537.JPG"),
    distance=0.12,
    source="weather_nn",
)


def test_build_sidecar_sample():
    params = dial_schedule(0.0)
    sidecar = build_sidecar(
        pkt=_SAMPLE_PACKET,
        params=params,
        prompt="cldbry window view of Pinchard's Island, Newfoundland, summer, daytime",
        anchor=_ANCHOR,
        seed=42,
        size=(1024, 768),
        models=_MODELS,
        device="cpu",
        dtype="torch.float32",
        edge_crop={"top": 0.09, "right": 0.12, "bottom": 0.0, "left": 0.0},
        generated_at="2026-07-21T20:31:00+00:00",
    )
    assert sidecar["labeled"] == LABELED_GENERATED
    assert sidecar["seed"] == 42
    assert sidecar["anchor_frame"] == _ANCHOR.filename
    assert sidecar["weather_packet"] == _SAMPLE_PACKET
    assert sidecar["validator_scores"] is None
    assert sidecar["failure_mode"] is None
    assert validate_sidecar(sidecar) == []


def test_validate_sidecar_catches_missing_fields():
    sidecar = build_sidecar(
        pkt=_SAMPLE_PACKET,
        params=dial_schedule(0.0),
        prompt="test",
        anchor=_ANCHOR,
        seed=1,
        size=(1024, 768),
        models=_MODELS,
        device="cpu",
        dtype="torch.float32",
    )
    del sidecar["prompt"]
    errors = validate_sidecar(sidecar)
    assert any("prompt" in e for e in errors)


def test_validator_scores_and_failure_mode_hooks():
    sidecar = build_sidecar(
        pkt=_SAMPLE_PACKET,
        params=dial_schedule(0.0),
        prompt="test",
        anchor=_ANCHOR,
        seed=1,
        size=(1024, 768),
        models=_MODELS,
        device="cpu",
        dtype="torch.float32",
        validator_scores={"identity": 0.91, "season": 1.0},
        failure_mode=None,
    )
    assert sidecar["validator_scores"]["identity"] == 0.91
    assert validate_sidecar(sidecar) == []


def test_provenance_sidecar_roundtrip():
    params = dial_schedule(2.0)
    raw = build_sidecar(
        pkt=_SAMPLE_PACKET,
        params=params,
        prompt="test prompt",
        anchor=_ANCHOR,
        seed=7,
        size=(1024, 768),
        models=_MODELS,
        device="mps",
        dtype="torch.float16",
        dream_id="2026-07-21T20:30:00.000Z_DREAM001",
    )
    typed = ProvenanceSidecar.from_dict(raw)
    assert typed.dream_id.endswith("DREAM001")
    assert typed.dial_params["denoise_strength"] == params.denoise_strength


def test_write_sidecar(tmp_path: Path):
    sidecar = build_sidecar(
        pkt=_SAMPLE_PACKET,
        params=dial_schedule(0.0),
        prompt="test",
        anchor=_ANCHOR,
        seed=1,
        size=(1024, 768),
        models=_MODELS,
        device="cpu",
        dtype="torch.float32",
        dream_id="2026-07-21T20:30:00.000Z_DREAM001",
    )
    out = tmp_path / "2026-07-21T20:30:00.000Z_DREAM001.json"
    write_sidecar(out, sidecar)
    assert out.exists()
    assert '"labeled": "generated"' in out.read_text()


def test_write_sidecar_rejects_invalid(tmp_path: Path):
    with pytest.raises(ValueError, match="invalid sidecar"):
        write_sidecar(tmp_path / "bad.json", {"labeled": "generated"})
