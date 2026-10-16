"""USNO solar-band helpers for twilight honesty (#27)."""

from __future__ import annotations

import pytest

from weather_schema.solar_bands import same_solar_band, solar_band


@pytest.mark.parametrize(
    "elev,band",
    [
        (-20.0, "night"),
        (-18.0, "astronomical_twilight"),
        (-15.0, "astronomical_twilight"),
        (-12.0, "nautical_twilight"),
        (-8.5, "nautical_twilight"),
        (-6.0, "civil_golden"),
        (-5.6, "civil_golden"),
        (0.0, "civil_golden"),
        (6.0, "civil_golden"),
        (6.01, "day"),
        (35.0, "day"),
    ],
)
def test_solar_band_boundaries(elev: float, band: str):
    assert solar_band(elev) == band


def test_same_solar_band():
    assert same_solar_band(-8.5, -7.0)
    assert not same_solar_band(-8.5, -5.6)
    assert not same_solar_band(-8.5, 30.0)
