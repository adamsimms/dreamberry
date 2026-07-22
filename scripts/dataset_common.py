"""Dataset paths, manifest helpers, and common I/O for the M0 pipeline."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from astral import LocationInfo
from astral.sun import elevation
from dateutil import parser as date_parser

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "dataset.yaml"


def load_config() -> dict[str, Any]:
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    return cfg


def resolve_path(rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else REPO_ROOT / p


def resolve_catalog_path(cfg: dict[str, Any]) -> Path:
    catalog_rel = cfg["catalog"]["path"]
    p = (CONFIG_PATH.parent / catalog_rel).resolve()
    if not p.exists():
        p = REPO_ROOT / catalog_rel
    return p.resolve()


def load_catalog(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    catalog_path = resolve_catalog_path(cfg)
    with open(catalog_path) as f:
        data = json.load(f)
    return data["photos"]


def cabin_location(cfg: dict[str, Any]) -> LocationInfo:
    c = cfg["cabin"]
    return LocationInfo(
        name="Pinchards Island",
        region="Newfoundland",
        timezone=c["timezone"],
        latitude=c["latitude"],
        longitude=c["longitude"],
    )


def parse_exif_datetime(raw: str | bytes | None) -> datetime | None:
    if not raw:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    raw = raw.strip()
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        dt = date_parser.parse(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def solar_elevation_deg(cfg: dict[str, Any], dt_utc: datetime) -> float:
    loc = cabin_location(cfg)
    dt_local = dt_utc.astimezone(
        __import__("zoneinfo").ZoneInfo(cfg["cabin"]["timezone"])
    )
    return float(elevation(loc.observer, dt_local))


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def ensure_dirs(*paths: Path) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Any) -> None:
    ensure_dirs(path.parent)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=False)
        f.write("\n")


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_dirs(path.parent)
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=False) + "\n")
