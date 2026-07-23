"""Tests for the private DREAM033 night comparison selector."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from night_ab_dream033 import (  # noqa: E402
    select_cross_season_night,
    solar_mismatch_params,
)
from weather_schema.retrieve import IndexEntry, WeatherNNIndex  # noqa: E402
from weather_schema.vector import feature_vector  # noqa: E402


def test_solar_mismatch_params_keep_requested_dial_zero():
    params = solar_mismatch_params()
    assert params.dial == 0.0
    assert params.denoise_strength == 0.70
    assert params.controlnet_scale == 0.50
    assert params.ip_adapter_scale == 0.25


def test_cross_season_selector_excludes_summer_winter_tokens_and_bright_frames(
    tmp_path: Path,
):
    pkt = {
        "month": 7,
        "solar_elevation": -20.0,
        "cloud_cover": 100.0,
        "weather_code": 3,
    }
    query_vector, _ = feature_vector(pkt)
    farther_vector = list(query_vector)
    farther_vector[1] = 0.5
    index = WeatherNNIndex(
        [
            IndexEntry(
                "summer.jpg",
                month=8,
                feature_vector=query_vector,
                prompt="summer, night",
                solar_elevation=-20.0,
            ),
            IndexEntry(
                "snow.jpg",
                month=1,
                feature_vector=query_vector,
                prompt="winter, night, snow, frozen",
                solar_elevation=-20.0,
            ),
            IndexEntry(
                "autumn.jpg",
                month=10,
                feature_vector=farther_vector,
                prompt="autumn, night, overcast sky",
                solar_elevation=-22.0,
            ),
            IndexEntry(
                "bright.jpg",
                month=11,
                feature_vector=query_vector,
                prompt="late autumn, night, overcast sky",
                solar_elevation=-24.0,
            ),
        ]
    )
    for filename, value in (
        ("summer.jpg", 1),
        ("snow.jpg", 1),
        ("autumn.jpg", 5),
        ("bright.jpg", 100),
    ):
        Image.new("L", (4, 4), value).save(tmp_path / filename)

    entry, distance = select_cross_season_night(index, pkt, tmp_path)
    assert entry.filename == "autumn.jpg"
    assert distance > 0.0
