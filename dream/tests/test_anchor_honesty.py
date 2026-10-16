"""Twilight honesty: luminance + band gates for dial-0 anchors (#27)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from PIL import Image

from dream.anchor import (
    AnchorHonestyConfig,
    NoHonestNightAnchorError,
    select_anchor,
)
from weather_schema.retrieve import IndexEntry, WeatherNNIndex


def _vec(**overrides: float | None) -> list[float | None]:
    base: list[float | None] = [0.5] * 9
    names = [
        "solar_elevation",
        "cloud_cover",
        "visibility",
        "precip_class",
        "wave_ht_sig",
        "wind_speed_10m",
        "wind_dir_onshore",
        "rh",
        "temperature_2m",
    ]
    for i, name in enumerate(names):
        if name in overrides:
            base[i] = overrides[name]
    return base


def _grey_jpeg(path: Path, value: int) -> None:
    Image.new("RGB", (64, 48), (value, value, value)).save(path, format="JPEG")


def _dream_cfg(tmp_path: Path, entries: list[IndexEntry]) -> dict:
    raw = tmp_path / "raw"
    raw.mkdir()
    index = WeatherNNIndex(entries, solar_band_filter=True)
    index_path = tmp_path / "weather_nn_index.json"
    index.save(index_path)

    canonical = "canonical_day.JPG"
    _grey_jpeg(raw / canonical, 200)

    dataset = {
        "canonical_frame": canonical,
        "paths": {
            "raw_dir": str(raw),
            "weather_nn_index": str(index_path),
        },
    }
    ds_path = tmp_path / "dataset.yaml"
    ds_path.write_text(yaml.safe_dump(dataset))

    return {
        "paths": {"dataset_config": str(ds_path)},
        "anchor_honesty": {
            "enabled": True,
            "solar_band_filter": True,
            "luminance_gate": True,
            "luminance_gate_solar_elevation_deg": -4.0,
            "max_mean_luminance": 80.0,
            "query_k": 10,
            "relax_luminance_if_empty": True,
        },
    }


def test_twilight_rejects_bright_prefers_dark(tmp_path: Path):
    """DREAM006-style: bright same-season hit skipped for darker night frame."""
    raw = tmp_path / "raw"
    bright = "bright_dawnish.jpg"
    dark = "dark_twilight.jpg"
    # Paths created inside _dream_cfg raw; write after cfg builds raw via entries only.
    entries = [
        IndexEntry(
            bright,
            month=8,
            feature_vector=_vec(cloud_cover=0.50),
            solar_elevation=-7.0,
        ),
        IndexEntry(
            dark,
            month=8,
            feature_vector=_vec(cloud_cover=0.90),
            solar_elevation=-8.0,
        ),
    ]
    cfg = _dream_cfg(tmp_path, entries)
    raw = Path(yaml.safe_load(Path(cfg["paths"]["dataset_config"]).read_text())["paths"]["raw_dir"])
    _grey_jpeg(raw / bright, 160)  # > 80
    _grey_jpeg(raw / dark, 40)

    pkt = {
        "month": 8,
        "solar_elevation": -8.5,
        "cloud_cover": 50.0,
        "weather_code": 0,
    }
    anchor = select_anchor(pkt, cfg)
    assert anchor.filename == dark
    assert anchor.source == "weather_nn"
    assert anchor.mean_luminance is not None and anchor.mean_luminance < 80
    assert any(r["reason"] == "luminance_too_high" for r in anchor.reject_reasons)


def test_twilight_relaxes_to_darkest_when_all_bright(tmp_path: Path):
    entries = [
        IndexEntry(
            "a.jpg",
            month=8,
            feature_vector=_vec(cloud_cover=0.50),
            solar_elevation=-8.0,
        ),
        IndexEntry(
            "b.jpg",
            month=8,
            feature_vector=_vec(cloud_cover=0.55),
            solar_elevation=-9.0,
        ),
    ]
    cfg = _dream_cfg(tmp_path, entries)
    raw = Path(yaml.safe_load(Path(cfg["paths"]["dataset_config"]).read_text())["paths"]["raw_dir"])
    _grey_jpeg(raw / "a.jpg", 150)
    _grey_jpeg(raw / "b.jpg", 120)

    pkt = {"month": 8, "solar_elevation": -8.5, "cloud_cover": 50.0, "weather_code": 0}
    anchor = select_anchor(pkt, cfg)
    assert anchor.filename == "b.jpg"
    assert anchor.source == "weather_nn_relaxed"
    assert any(r["reason"] == "luminance_relaxed" for r in anchor.reject_reasons)


def test_night_refuses_day_canonical_when_no_hits(tmp_path: Path):
    """Empty night pool must not resurrect the bright geometry master."""
    cfg = _dream_cfg(tmp_path, entries=[])
    pkt = {"month": 8, "solar_elevation": -12.0, "weather_code": 0}
    with pytest.raises(NoHonestNightAnchorError):
        select_anchor(pkt, cfg)


def test_day_query_still_falls_back_to_canonical(tmp_path: Path):
    cfg = _dream_cfg(tmp_path, entries=[])
    pkt = {"month": 8, "solar_elevation": 35.0, "weather_code": 0}
    anchor = select_anchor(pkt, cfg)
    assert anchor.source == "canonical_fallback"
    assert anchor.filename == "canonical_day.JPG"


def test_honesty_disabled_skips_luminance_gate(tmp_path: Path):
    entries = [
        IndexEntry(
            "bright.jpg",
            month=8,
            feature_vector=_vec(),
            solar_elevation=-8.0,
        ),
    ]
    cfg = _dream_cfg(tmp_path, entries)
    raw = Path(yaml.safe_load(Path(cfg["paths"]["dataset_config"]).read_text())["paths"]["raw_dir"])
    _grey_jpeg(raw / "bright.jpg", 180)
    cfg["anchor_honesty"]["enabled"] = False

    pkt = {"month": 8, "solar_elevation": -8.5, "weather_code": 0}
    anchor = select_anchor(pkt, cfg, honesty=AnchorHonestyConfig(enabled=False))
    assert anchor.filename == "bright.jpg"
    assert anchor.source == "weather_nn"
