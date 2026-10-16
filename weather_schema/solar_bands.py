"""USNO solar-elevation bands for twilight honesty (#27).

Finer than the coarse day/night curation gate at −6°. Band names match
issue #27 / schema §2.6 phase groups used for retrieval filtering.
"""

from __future__ import annotations

# Band order from darkest to brightest (for adjacency widen if needed later).
SOLAR_BANDS: tuple[str, ...] = (
    "night",
    "astronomical_twilight",
    "nautical_twilight",
    "civil_golden",
    "day",
)


def solar_band(solar_elevation: float) -> str:
    """Map geometric solar elevation (deg) to a retrieval band.

    Boundaries align with USNO twilight + golden hour (§2.6):
    night < −18 ≤ astr. twilight < −12 ≤ nautical < −6 ≤ civil+golden ≤ +6 < day.
    """
    e = float(solar_elevation)
    if e < -18.0:
        return "night"
    if e < -12.0:
        return "astronomical_twilight"
    if e < -6.0:
        return "nautical_twilight"
    if e <= 6.0:
        return "civil_golden"
    return "day"


def same_solar_band(
    query_elevation: float,
    entry_elevation: float,
) -> bool:
    return solar_band(query_elevation) == solar_band(entry_elevation)
