"""Bucketing tables from DREAMBERRY-WEATHER-SCHEMA.md §2."""

from __future__ import annotations

from weather_schema.vocabulary import SNOWISH_PRECIP


def sky_token(cloud_cover: float | None) -> str | None:
    if cloud_cover is None:
        return None
    c = float(cloud_cover)
    if c <= 6:
        return "clear sky"
    if c <= 31:
        return "mostly clear sky"
    if c <= 56:
        return "partly cloudy sky"
    if c <= 93:
        return "mostly cloudy sky"
    return "overcast sky"


def obscuration_token(
    visibility: float | None,
    rh: float | None,
    weather_code: int | None,
) -> str | None:
    code = int(weather_code) if weather_code is not None else None
    vis = float(visibility) if visibility is not None else None
    humidity = float(rh) if rh is not None else None

    if code in {45, 48} or (vis is not None and vis < 1000):
        if vis is not None and vis < 400:
            return "dense fog"
        return "fog"

    if vis is None:
        return None

    if 1000 <= vis < 5000:
        if humidity is not None and humidity >= 90:
            return "misty"
        if humidity is not None and humidity < 90:
            return "hazy"
        return "misty"  # RH unknown: prefer wet coastal default for reduced vis

    if 5000 <= vis < 10000:
        return "light haze on the horizon"

    return None


_PRECIP: dict[int, str] = {
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    56: "freezing drizzle",
    57: "heavy freezing drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    66: "freezing rain",
    67: "heavy freezing rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    77: "snow grains",
    80: "passing rain showers",
    81: "rain showers",
    82: "heavy rain showers",
    85: "snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "thunderstorm with hail",
}


def precip_token(weather_code: int | None) -> str | None:
    if weather_code is None:
        return None
    code = int(weather_code)
    if code in {0, 1, 2, 3, 45, 48}:
        return None
    return _PRECIP.get(code)


def sea_state_token(wave_ht_sig: float | None) -> str | None:
    if wave_ht_sig is None:
        return None
    w = float(wave_ht_sig)
    if w == 0:
        return "glassy calm sea"
    if w <= 0.10:
        return "calm rippled sea"
    if w <= 0.50:
        return "calm sea"
    if w <= 1.25:
        return "slight sea"
    if w <= 2.50:
        return "moderate sea"
    if w <= 4.00:
        return "rough sea"
    if w <= 6.00:
        return "very rough sea"
    return "heavy stormy sea"


def wind_token(wind_speed_kmh: float | None) -> str | None:
    if wind_speed_kmh is None:
        return None
    v = float(wind_speed_kmh)
    if v < 6:
        return "still air"
    if v <= 19:
        return "light breeze"
    if v <= 38:
        return "breezy"
    if v <= 61:
        return "strong wind"
    if v <= 88:
        return "gale-force wind"
    return "storm-force wind"


def season_token(month: int) -> str:
    m = int(month)
    if m in {12, 1, 2}:
        return "winter"
    if m in {3, 4}:
        return "late winter"
    if m == 5:
        return "spring"
    if m in {6, 7, 8}:
        return "summer"
    if m in {9, 10}:
        return "autumn"
    if m == 11:
        return "late autumn"
    raise ValueError(f"invalid month: {month}")


def solar_tokens(
    solar_elevation: float,
    *,
    after_solar_noon: bool,
    cloud_cover: float | None,
) -> tuple[str, str | None]:
    """Return (time_of_day, light_token)."""
    e = float(solar_elevation)

    if e < -18:
        tod, light = "night", None
    elif e < -12:
        tod, light = "deep twilight", None
    elif e < -6:
        tod, light = "twilight", None
    elif e < -4:
        tod = "dusk" if after_solar_noon else "dawn"
        light = "blue hour light"
    elif e <= 6:
        tod = "dusk" if after_solar_noon else "dawn"
        light = "golden hour light"
    elif e <= 15:
        tod = "late afternoon" if after_solar_noon else "early morning"
        light = "low warm sunlight"
    elif e <= 35:
        tod, light = "daytime", "soft daylight"
    else:
        tod, light = "midday", "bright overhead sun"

    # Overcast / mostly cloudy suppresses directional light tokens
    if cloud_cover is not None and float(cloud_cover) >= 57:
        if tod in {
            "dawn",
            "dusk",
            "early morning",
            "late afternoon",
            "daytime",
            "midday",
        }:
            light = "flat overcast light"
        else:
            light = None

    return tod, light


def atmosphere_token(
    temperature_2m: float | None,
    rh: float | None,
    precip: str | None,
    weather_code: int | None = None,
) -> str | None:
    # Depositing rime fog (§2.3): obscuration + atmosphere rime frost
    if weather_code is not None and int(weather_code) == 48:
        return "rime frost"

    # Guard: precip already implies cold/wet — skip temperature atmosphere (§2.8)
    if precip is not None and precip in SNOWISH_PRECIP:
        return None

    if temperature_2m is None:
        return None

    t = float(temperature_2m)
    humidity = float(rh) if rh is not None else None

    if t <= -5:
        return "frozen, frost-rimed"
    if t <= 0:
        return "frost"
    if 0 < t <= 3 and humidity is not None and humidity >= 90:
        return "raw damp cold"
    return None
