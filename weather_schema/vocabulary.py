"""Closed token vocabulary for validation."""

from __future__ import annotations

SEASON = frozenset(
    {"winter", "late winter", "spring", "summer", "autumn", "late autumn"}
)
TIME_OF_DAY = frozenset(
    {
        "night",
        "deep twilight",
        "twilight",
        "dawn",
        "dusk",
        "early morning",
        "late afternoon",
        "daytime",
        "midday",
    }
)
LIGHT = frozenset(
    {
        "blue hour light",
        "golden hour light",
        "low warm sunlight",
        "soft daylight",
        "bright overhead sun",
        "flat overcast light",
    }
)
SKY = frozenset(
    {
        "clear sky",
        "mostly clear sky",
        "partly cloudy sky",
        "mostly cloudy sky",
        "overcast sky",
    }
)
OBSCURATION = frozenset(
    {"dense fog", "fog", "misty", "hazy", "light haze on the horizon"}
)
PRECIP = frozenset(
    {
        "light drizzle",
        "drizzle",
        "heavy drizzle",
        "freezing drizzle",
        "heavy freezing drizzle",
        "light rain",
        "rain",
        "heavy rain",
        "freezing rain",
        "heavy freezing rain",
        "light snow",
        "snow",
        "heavy snow",
        "snow grains",
        "passing rain showers",
        "rain showers",
        "heavy rain showers",
        "snow showers",
        "heavy snow showers",
        "thunderstorm",
        "thunderstorm with hail",
    }
)
SEA = frozenset(
    {
        "glassy calm sea",
        "calm rippled sea",
        "calm sea",
        "slight sea",
        "moderate sea",
        "rough sea",
        "very rough sea",
        "heavy stormy sea",
    }
)
WIND = frozenset(
    {
        "still air",
        "light breeze",
        "breezy",
        "strong wind",
        "gale-force wind",
        "storm-force wind",
    }
)
ATMOSPHERE = frozenset({"frost", "frozen, frost-rimed", "raw damp cold", "rime frost"})

CLOSED_VOCABULARY = (
    SEASON | TIME_OF_DAY | LIGHT | SKY | OBSCURATION | PRECIP | SEA | WIND | ATMOSPHERE
)

DAY_TIME_TOKENS = frozenset(
    {"dawn", "dusk", "early morning", "late afternoon", "daytime", "midday"}
)

SNOWISH_PRECIP = frozenset(
    {
        "light snow",
        "snow",
        "heavy snow",
        "snow grains",
        "snow showers",
        "heavy snow showers",
        "freezing drizzle",
        "heavy freezing drizzle",
        "freezing rain",
        "heavy freezing rain",
    }
)
