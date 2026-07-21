"""Solar geometry helpers for weather packets (archive + live symmetry)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from astral import LocationInfo
from astral.sun import elevation, noon


def cabin_location(cfg: Mapping[str, Any]) -> LocationInfo:
    c = cfg["cabin"]
    return LocationInfo(
        name="Pinchards Island",
        region="Newfoundland",
        timezone=c["timezone"],
        latitude=c["latitude"],
        longitude=c["longitude"],
    )


def solar_elevation_deg(cfg: Mapping[str, Any], dt_utc: datetime) -> float:
    loc = cabin_location(cfg)
    tz = ZoneInfo(cfg["cabin"]["timezone"])
    dt_local = dt_utc.astimezone(tz)
    return float(elevation(loc.observer, dt_local))


def after_solar_noon(cfg: Mapping[str, Any], dt_utc: datetime) -> bool:
    loc = cabin_location(cfg)
    tz = ZoneInfo(cfg["cabin"]["timezone"])
    dt_local = dt_utc.astimezone(tz)
    solar_noon = noon(loc.observer, date=dt_local.date(), tzinfo=tz)
    return dt_local >= solar_noon


def enrich_solar_fields(cfg: Mapping[str, Any], dt_utc: datetime) -> dict[str, Any]:
    tz = ZoneInfo(cfg["cabin"]["timezone"])
    dt_local = dt_utc.astimezone(tz)
    return {
        "solar_elevation": round(solar_elevation_deg(cfg, dt_utc), 3),
        "month": dt_local.month,
        "after_solar_noon": after_solar_noon(cfg, dt_utc),
        "timezone": cfg["cabin"]["timezone"],
        "latitude": cfg["cabin"]["latitude"],
        "longitude": cfg["cabin"]["longitude"],
    }
