"""9-feature retrieval vector — schema §4."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from weather_schema.buckets import season_token
from weather_schema.compose import normalize_packet

# Onshore bearing for north-facing cabin window (degrees from true north).
# Camera looks north over ocean; onshore ≈ wind from the north (0°).
DEFAULT_THETA_SHORE_DEG = 0.0

FEATURE_WEIGHTS: tuple[float, ...] = (
    3.0,  # solar_elevation
    2.0,  # cloud_cover
    2.5,  # visibility
    2.5,  # precip_class
    1.5,  # wave_ht_sig
    1.0,  # wind_speed
    0.5,  # wind_dir_onshore
    0.5,  # rh
    0.5,  # temperature
)

FEATURE_NAMES: tuple[str, ...] = (
    "solar_elevation",
    "cloud_cover",
    "visibility",
    "precip_class",
    "wave_ht_sig",
    "wind_speed_10m",
    "wind_dir_onshore",
    "rh",
    "temperature_2m",
)

# Season families for hard retrieval gate (§4.3)
SEASON_FAMILY: dict[str, frozenset[str]] = {
    "winter": frozenset({"winter", "late winter"}),
    "late winter": frozenset({"winter", "late winter", "spring"}),
    "spring": frozenset({"late winter", "spring"}),
    "summer": frozenset({"summer"}),
    "autumn": frozenset({"autumn", "late autumn"}),
    "late autumn": frozenset({"autumn", "late autumn"}),
}


def precip_class(weather_code: int | None) -> int:
    """Ordinal precip family: none0 / drizzle1 / rain2 / freezing3 / snow4 / storm5."""
    if weather_code is None:
        return 0
    c = int(weather_code)
    if c in {0, 1, 2, 3, 45, 48}:
        return 0
    if c in {51, 53, 55}:
        return 1
    if c in {61, 63, 65, 80, 81, 82}:
        return 2
    if c in {56, 57, 66, 67}:
        return 3
    if c in {71, 73, 75, 77, 85, 86}:
        return 4
    if c in {95, 96, 99}:
        return 5
    return 0


def season_family(month: int) -> frozenset[str]:
    return SEASON_FAMILY[season_token(month)]


def _solar_feature(elev: float) -> float:
    # sin(elev) then min-max over elev ∈ [−18°, +65°]
    lo = math.sin(math.radians(-18.0))
    hi = math.sin(math.radians(65.0))
    s = math.sin(math.radians(float(elev)))
    return (s - lo) / (hi - lo)


def _vis_feature(visibility: float | None, weather_code: int | None, rh: float | None) -> float | None:
    """Return normalized visibility feature, or None to drop (§4.4)."""
    if visibility is not None:
        v = max(0.0, min(20000.0, float(visibility))) / 20000.0
        return math.sqrt(v)

    # null visibility: treat as clear (20000) only if non-fog and RH < 90
    code = int(weather_code) if weather_code is not None else None
    humidity = float(rh) if rh is not None else None
    foggy = code in {45, 48}
    wet = humidity is not None and humidity >= 90
    if not foggy and (humidity is None or humidity < 90) and not wet:
        # clear-air default
        return math.sqrt(1.0)
    return None


def feature_vector(
    pkt: Mapping[str, Any],
    *,
    theta_shore_deg: float = DEFAULT_THETA_SHORE_DEG,
) -> tuple[list[float | None], list[float]]:
    """
    Build the 9-feature vector.

    Returns (values, weights) where missing features are None and should be
    dropped + renormalized by the distance function.
    """
    p = normalize_packet(pkt)
    vals: list[float | None] = [None] * 9
    weights = list(FEATURE_WEIGHTS)

    vals[0] = _solar_feature(p["solar_elevation"])

    if p["cloud_cover"] is not None:
        vals[1] = float(p["cloud_cover"]) / 100.0

    vals[2] = _vis_feature(
        p["visibility"], p["weather_code"], p["relative_humidity_2m"]
    )

    vals[3] = precip_class(p["weather_code"]) / 5.0

    if p["wave_ht_sig"] is not None:
        vals[4] = max(0.0, min(6.0, float(p["wave_ht_sig"]))) / 6.0

    if p["wind_speed_10m"] is not None:
        vals[5] = max(0.0, min(100.0, float(p["wind_speed_10m"]))) / 100.0

    if p["wind_direction_10m"] is not None:
        theta = math.radians(float(p["wind_direction_10m"]))
        shore = math.radians(float(theta_shore_deg))
        # cos(θ − θ_shore) ∈ [−1,1] → [0,1]
        vals[6] = (math.cos(theta - shore) + 1.0) / 2.0

    if p["relative_humidity_2m"] is not None:
        vals[7] = float(p["relative_humidity_2m"]) / 100.0

    if p["temperature_2m"] is not None:
        t = max(-20.0, min(25.0, float(p["temperature_2m"])))
        vals[8] = (t - (-20.0)) / (25.0 - (-20.0))

    return vals, weights


def weighted_distance(
    a: Sequence[float | None],
    b: Sequence[float | None],
    weights: Sequence[float] | None = None,
) -> float:
    """Weighted Euclidean with null-drop-renormalize (§4.2 / §4.4)."""
    w = list(weights) if weights is not None else list(FEATURE_WEIGHTS)
    present_w = 0.0
    acc = 0.0
    for i, (ai, bi) in enumerate(zip(a, b, strict=True)):
        if ai is None or bi is None:
            continue
        present_w += w[i]
        acc += w[i] * (float(ai) - float(bi)) ** 2
    if present_w <= 0:
        return float("inf")
    # renormalize so distances stay comparable across missingness patterns
    scale = sum(w) / present_w
    return math.sqrt(acc * scale)
