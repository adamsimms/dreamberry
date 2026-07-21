"""Prompt composition — schema §3."""

from __future__ import annotations

from typing import Any, Mapping

from weather_schema import buckets
from weather_schema.vocabulary import CLOSED_VOCABULARY, DAY_TIME_TOKENS

TRIGGER = "cldbry window view of Pinchard's Island, Newfoundland"

# Accept both schema names and M0 packet aliases
_ALIASES = {
    "rh": "relative_humidity_2m",
    "relative_humidity_2m": "relative_humidity_2m",
    "wind": "wind_speed_10m",
    "wind_speed_10m": "wind_speed_10m",
    "wind_speed": "wind_speed_10m",
    "temp": "temperature_2m",
    "temperature_2m": "temperature_2m",
    "visibility": "visibility",
    "cloud_cover": "cloud_cover",
    "weather_code": "weather_code",
    "wave_ht_sig": "wave_ht_sig",
    "solar_elevation": "solar_elevation",
    "month": "month",
    "after_solar_noon": "after_solar_noon",
    "wind_direction_10m": "wind_direction_10m",
    "shortwave_radiation": "shortwave_radiation",
    "precipitation": "precipitation",
}


def _get(pkt: Mapping[str, Any], *keys: str, default=None):
    for k in keys:
        if k in pkt and pkt[k] is not None:
            return pkt[k]
        # allow explicit None to mean missing for optional fields
        if k in pkt:
            return pkt[k]
    return default


def normalize_packet(pkt: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize archive or live packet to the schema field set."""
    if "month" not in pkt or pkt["month"] is None:
        raise ValueError("packet requires month")
    if "solar_elevation" not in pkt or pkt["solar_elevation"] is None:
        raise ValueError("packet requires solar_elevation")

    after = pkt.get("after_solar_noon")
    if after is None and "hour_angle" in pkt and pkt["hour_angle"] is not None:
        after = float(pkt["hour_angle"]) >= 0
    if after is None:
        after = False  # default morning if caller didn't compute noon

    return {
        "month": int(pkt["month"]),
        "solar_elevation": float(pkt["solar_elevation"]),
        "after_solar_noon": bool(after),
        "cloud_cover": _num_or_none(pkt.get("cloud_cover")),
        "visibility": _num_or_none(pkt.get("visibility")),
        "weather_code": _int_or_none(pkt.get("weather_code")),
        "relative_humidity_2m": _num_or_none(
            _get(pkt, "relative_humidity_2m", "rh")
        ),
        "wave_ht_sig": _num_or_none(pkt.get("wave_ht_sig")),
        "wind_speed_10m": _num_or_none(
            _get(pkt, "wind_speed_10m", "wind", "wind_speed")
        ),
        "temperature_2m": _num_or_none(_get(pkt, "temperature_2m", "temp")),
        "wind_direction_10m": _num_or_none(pkt.get("wind_direction_10m")),
        "shortwave_radiation": _num_or_none(pkt.get("shortwave_radiation")),
        "precipitation": _num_or_none(pkt.get("precipitation")),
    }


def _num_or_none(v) -> float | None:
    if v is None:
        return None
    return float(v)


def _int_or_none(v) -> int | None:
    if v is None:
        return None
    return int(v)


def filt(xs):
    return [x for x in xs if x]


def compose_prompt(pkt: Mapping[str, Any]) -> str:
    """Deterministic fixed-slot prompt from a weather packet (schema §3.3)."""
    p = normalize_packet(pkt)

    slots: list[str] = [TRIGGER]
    slots.append(buckets.season_token(p["month"]))

    tod, light = buckets.solar_tokens(
        p["solar_elevation"],
        after_solar_noon=p["after_solar_noon"],
        cloud_cover=p["cloud_cover"],
    )
    slots.append(tod)
    slots.extend(filt([light]))

    sky = buckets.sky_token(p["cloud_cover"])
    slots.extend(filt([sky]))

    obsc = buckets.obscuration_token(
        p["visibility"], p["relative_humidity_2m"], p["weather_code"]
    )
    slots.extend(filt([obsc]))

    precip = buckets.precip_token(p["weather_code"])
    slots.extend(filt([precip]))

    sea = buckets.sea_state_token(p["wave_ht_sig"])
    slots.extend(filt([sea]))

    wind = buckets.wind_token(p["wind_speed_10m"])
    slots.extend(filt([wind]))

    atm = buckets.atmosphere_token(
        p["temperature_2m"],
        p["relative_humidity_2m"],
        precip,
        weather_code=p["weather_code"],
    )
    slots.extend(filt([atm]))

    return ", ".join(filt(slots))


def prompt_tokens(prompt: str) -> list[str]:
    """Peel condition tokens after the trigger (longest-match; handles commas in tokens)."""
    if not prompt.startswith(TRIGGER):
        raise ValueError("prompt missing trigger prefix")
    rest = prompt[len(TRIGGER) :].lstrip(", ").strip()
    if not rest:
        return []
    # Longest-first so "frozen, frost-rimed" wins over shorter fragments
    vocab = sorted(CLOSED_VOCABULARY, key=len, reverse=True)
    tokens: list[str] = []
    while rest:
        match = None
        for tok in vocab:
            if rest == tok or rest.startswith(tok + ", "):
                match = tok
                break
        if match is None:
            raise ValueError(f"unrecognized token sequence at: {rest!r}")
        tokens.append(match)
        rest = rest[len(match) :].lstrip(", ").strip()
    return tokens


def assert_closed_vocabulary(prompt: str) -> None:
    for tok in prompt_tokens(prompt):
        if tok not in CLOSED_VOCABULARY:
            raise AssertionError(f"token not in closed vocabulary: {tok!r}")
