"""Unit tests for DREAMBERRY-WEATHER-SCHEMA.md — buckets + worked examples."""

from __future__ import annotations

import pytest

from weather_schema.buckets import (
    atmosphere_token,
    obscuration_token,
    precip_token,
    sea_state_token,
    season_token,
    sky_token,
    solar_tokens,
    wind_token,
)
from weather_schema.compose import (
    TRIGGER,
    assert_closed_vocabulary,
    compose_prompt,
    prompt_tokens,
)
from weather_schema.vector import feature_vector, precip_class, weighted_distance
from weather_schema.vocabulary import CLOSED_VOCABULARY


# --- Bucketing tables -------------------------------------------------------


@pytest.mark.parametrize(
    "cloud, expected",
    [
        (0, "clear sky"),
        (6, "clear sky"),
        (7, "mostly clear sky"),
        (31, "mostly clear sky"),
        (32, "partly cloudy sky"),
        (56, "partly cloudy sky"),
        (57, "mostly cloudy sky"),
        (93, "mostly cloudy sky"),
        (94, "overcast sky"),
        (100, "overcast sky"),
        (None, None),
    ],
)
def test_sky_token(cloud, expected):
    assert sky_token(cloud) == expected


@pytest.mark.parametrize(
    "vis, rh, code, expected",
    [
        (600, 98, 45, "fog"),
        (300, 98, 45, "dense fog"),
        (None, 98, 45, "fog"),
        (1800, 95, 75, "misty"),
        (1800, 80, 0, "hazy"),
        (7000, 50, 0, "light haze on the horizon"),
        (40000, 62, 0, None),
        (None, 50, 0, None),
    ],
)
def test_obscuration_token(vis, rh, code, expected):
    assert obscuration_token(vis, rh, code) == expected


@pytest.mark.parametrize(
    "code, expected",
    [
        (0, None),
        (45, None),
        (48, None),
        (51, "light drizzle"),
        (75, "heavy snow"),
        (95, "thunderstorm"),
        (99, "thunderstorm with hail"),
        (None, None),
    ],
)
def test_precip_token(code, expected):
    assert precip_token(code) == expected


@pytest.mark.parametrize(
    "wave, expected",
    [
        (0, "glassy calm sea"),
        (0.05, "calm rippled sea"),
        (0.10, "calm rippled sea"),
        (0.15, "calm sea"),
        (0.40, "calm sea"),
        (0.50, "calm sea"),
        (1.1, "slight sea"),
        (1.25, "slight sea"),
        (3.2, "rough sea"),
        (4.0, "rough sea"),
        (5.1, "very rough sea"),
        (7.0, "heavy stormy sea"),
        (None, None),
    ],
)
def test_sea_state_token(wave, expected):
    assert sea_state_token(wave) == expected


@pytest.mark.parametrize(
    "wind, expected",
    [
        (0, "still air"),
        (5.9, "still air"),
        (6, "light breeze"),
        (14, "light breeze"),
        (19, "light breeze"),
        (22, "breezy"),
        (38, "breezy"),
        (57, "strong wind"),
        (76, "gale-force wind"),
        (100, "storm-force wind"),
        (None, None),
    ],
)
def test_wind_token(wind, expected):
    assert wind_token(wind) == expected


@pytest.mark.parametrize(
    "month, expected",
    [
        (12, "winter"),
        (1, "winter"),
        (2, "winter"),
        (3, "late winter"),
        (4, "late winter"),
        (5, "spring"),
        (7, "summer"),
        (9, "autumn"),
        (10, "autumn"),
        (11, "late autumn"),
    ],
)
def test_season_token(month, expected):
    assert season_token(month) == expected


def test_solar_overcast_suppresses_golden():
    tod, light = solar_tokens(3.0, after_solar_noon=False, cloud_cover=88)
    assert tod == "dawn"
    assert light == "flat overcast light"


def test_solar_clear_keeps_golden():
    tod, light = solar_tokens(2.0, after_solar_noon=True, cloud_cover=20)
    assert tod == "dusk"
    assert light == "golden hour light"


def test_atmosphere_frozen():
    assert atmosphere_token(-9, 62, None) == "frozen, frost-rimed"


def test_atmosphere_suppressed_by_snow():
    assert atmosphere_token(-3, 95, "heavy snow") is None


def test_atmosphere_rime_fog():
    assert atmosphere_token(0, 100, None, weather_code=48) == "rime frost"


# --- Worked examples (schema §3.4) ------------------------------------------


EXAMPLES = {
    "A": {
        "pkt": {
            "month": 10,
            "solar_elevation": 3.0,
            "after_solar_noon": False,
            "cloud_cover": 88,
            "visibility": 600,
            "rh": 98,
            "weather_code": 45,
            "wave_ht_sig": 0.4,
            "wind": 14,
            "temp": 8,
        },
        "prompt": (
            "cldbry window view of Pinchard's Island, Newfoundland, autumn, dawn, "
            "flat overcast light, mostly cloudy sky, fog, calm sea, light breeze"
        ),
    },
    "B": {
        "pkt": {
            "month": 2,
            "solar_elevation": 16.0,
            "after_solar_noon": False,
            "cloud_cover": 3,
            "visibility": 40000,
            "rh": 62,
            "weather_code": 0,
            "wave_ht_sig": 1.1,
            "wind": 22,
            "temp": -9,
        },
        "prompt": (
            "cldbry window view of Pinchard's Island, Newfoundland, winter, daytime, "
            "soft daylight, clear sky, slight sea, breezy, frozen, frost-rimed"
        ),
    },
    "C": {
        "pkt": {
            "month": 11,
            "solar_elevation": -5.0,
            "after_solar_noon": True,
            "cloud_cover": 100,
            "visibility": 15000,
            "rh": 85,
            "weather_code": 3,
            "wave_ht_sig": 3.2,
            "wind": 57,
            "temp": 4,
        },
        "prompt": (
            "cldbry window view of Pinchard's Island, Newfoundland, late autumn, dusk, "
            "flat overcast light, overcast sky, rough sea, strong wind"
        ),
    },
    "D": {
        "pkt": {
            "month": 9,
            "solar_elevation": 2.0,
            "after_solar_noon": True,
            "cloud_cover": 20,
            "visibility": 45000,
            "rh": 70,
            "weather_code": 1,
            "wave_ht_sig": 0.15,
            "wind": 8,
            "temp": 15,
        },
        "prompt": (
            "cldbry window view of Pinchard's Island, Newfoundland, autumn, dusk, "
            "golden hour light, mostly clear sky, calm sea, light breeze"
        ),
    },
    "E": {
        "pkt": {
            "month": 1,
            "solar_elevation": 9.0,
            "after_solar_noon": True,
            "cloud_cover": 100,
            "visibility": 1800,
            "rh": 95,
            "weather_code": 75,
            "wave_ht_sig": 5.1,
            "wind": 76,
            "temp": -3,
        },
        "prompt": (
            "cldbry window view of Pinchard's Island, Newfoundland, winter, late afternoon, "
            "flat overcast light, overcast sky, misty, heavy snow, very rough sea, "
            "gale-force wind"
        ),
    },
}


@pytest.mark.parametrize("label", list(EXAMPLES))
def test_worked_examples(label):
    ex = EXAMPLES[label]
    out = compose_prompt(ex["pkt"])
    assert out == ex["prompt"]
    assert_closed_vocabulary(out)


def test_trigger_always_present():
    p = compose_prompt(EXAMPLES["A"]["pkt"])
    assert p.startswith(TRIGGER)


def test_all_example_tokens_in_closed_vocab():
    for ex in EXAMPLES.values():
        for tok in prompt_tokens(ex["prompt"]):
            assert tok in CLOSED_VOCABULARY


def test_missing_optional_slots_omitted():
    # Minimum viable: trigger + season + tod
    p = compose_prompt(
        {
            "month": 8,
            "solar_elevation": 20.0,
            "after_solar_noon": False,
            "cloud_cover": None,
            "visibility": None,
            "weather_code": None,
            "wave_ht_sig": None,
            "wind_speed_10m": None,
            "temperature_2m": None,
            "rh": None,
        }
    )
    assert p == (
        "cldbry window view of Pinchard's Island, Newfoundland, summer, daytime, "
        "soft daylight"
    )


# --- Vector helpers ---------------------------------------------------------


def test_precip_class_ordinal():
    assert precip_class(0) == 0
    assert precip_class(51) == 1
    assert precip_class(63) == 2
    assert precip_class(66) == 3
    assert precip_class(75) == 4
    assert precip_class(95) == 5


def test_feature_vector_length():
    vals, weights = feature_vector(EXAMPLES["B"]["pkt"])
    assert len(vals) == 9
    assert len(weights) == 9
    # wind_direction optional — None is dropped at distance time (§4.4)
    assert vals[6] is None
    assert vals[0] is not None and vals[3] is not None



def test_weighted_distance_null_drop():
    a = [0.5] * 9
    b = [0.5] * 9
    b[4] = None  # missing wave
    a2 = list(a)
    a2[4] = None
    d = weighted_distance(a2, b)
    assert d == 0.0


def test_solar_feature_clamped_for_deep_night():
    from weather_schema.vector import _solar_feature

    assert _solar_feature(-18.0) == pytest.approx(0.0, abs=1e-9)
    assert _solar_feature(-90.0) == 0.0
    assert 0.0 <= _solar_feature(65.0) <= 1.0
    assert _solar_feature(90.0) == 1.0


def test_compose_alias_fallback_skips_present_none():
    from weather_schema.compose import normalize_packet

    pkt = {
        "month": 8,
        "solar_elevation": 30.0,
        "relative_humidity_2m": None,
        "rh": 72,
        "wind_speed_10m": None,
        "wind": 18.5,
        "temperature_2m": None,
        "temp": 12.0,
    }
    norm = normalize_packet(pkt)
    assert norm["relative_humidity_2m"] == 72.0
    assert norm["wind_speed_10m"] == 18.5
    assert norm["temperature_2m"] == 12.0
