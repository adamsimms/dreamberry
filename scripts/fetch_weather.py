#!/usr/bin/env python3
"""Fetch Open-Meteo ERA5 historical weather packets for curated frames."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from dataset_common import (
    REPO_ROOT,
    cabin_location,
    ensure_dirs,
    load_config,
    resolve_path,
    solar_elevation_deg,
    write_json,
)

sys.path.insert(0, str(REPO_ROOT / "scripts"))


def load_curated_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def utc_hour_key(exif_iso: str) -> datetime:
    dt = datetime.fromisoformat(exif_iso.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def local_hour_label(cfg, dt_utc: datetime) -> str:
    tz = ZoneInfo(cfg["cabin"]["timezone"])
    return dt_utc.astimezone(tz).strftime("%Y-%m-%dT%H:00")


def fetch_day_archive(
    session: requests.Session,
    cfg: dict,
    day: date,
) -> dict[str, dict]:
    """Fetch hourly ERA5 for one UTC calendar day; return map local_hour -> packet fields."""
    api = cfg["weather"]["archive_api"]
    variables = ",".join(cfg["weather"]["hourly_variables"])
    params = {
        "latitude": cfg["cabin"]["latitude"],
        "longitude": cfg["cabin"]["longitude"],
        "start_date": day.isoformat(),
        "end_date": day.isoformat(),
        "hourly": variables,
        "wind_speed_unit": cfg["weather"]["wind_speed_unit"],
        "timezone": cfg["cabin"]["timezone"],
    }
    resp = session.get(api, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    result: dict[str, dict] = {}
    for i, t in enumerate(times):
        pkt = {
            "time_local": t,
            "cloud_cover": _at(hourly, "cloud_cover", i),
            "visibility": _at(hourly, "visibility", i),
            "weather_code": _at(hourly, "weather_code", i),
            "relative_humidity_2m": _at(hourly, "relative_humidity_2m", i),
            "wind_speed_10m": _at(hourly, "wind_speed_10m", i),
            "wind_direction_10m": _at(hourly, "wind_direction_10m", i),
            "shortwave_radiation": _at(hourly, "shortwave_radiation", i),
            "temperature_2m": _at(hourly, "temperature_2m", i),
            "precipitation": _at(hourly, "precipitation", i),
            "wave_ht_sig": None,
            "source": "open-meteo-era5-archive",
            "latitude": cfg["cabin"]["latitude"],
            "longitude": cfg["cabin"]["longitude"],
        }
        result[t] = pkt
    return result


def _at(hourly: dict, key: str, idx: int):
    vals = hourly.get(key)
    if vals is None or idx >= len(vals):
        return None
    return vals[idx]


def enrich_packet(cfg: dict, frame: dict, era5: dict) -> dict:
    exif_iso = frame["exif_iso"]
    dt_utc = datetime.fromisoformat(exif_iso.replace("Z", "+00:00"))
    tz = ZoneInfo(cfg["cabin"]["timezone"])
    dt_local = dt_utc.astimezone(tz)
    hour_label = dt_local.strftime("%Y-%m-%dT%H:00")

    base = dict(era5.get(hour_label, {}))
    base["filename"] = frame["filename"]
    base["exif_iso"] = exif_iso
    base["bucket"] = frame.get("bucket")
    base["solar_elevation"] = round(solar_elevation_deg(cfg, dt_utc), 3)
    base["month"] = dt_local.month
    base["timezone"] = cfg["cabin"]["timezone"]
    base["paired_at"] = datetime.now(timezone.utc).isoformat()
    return base


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch ERA5 weather packets")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    cfg = load_config()
    day_path = resolve_path(cfg["paths"]["curated_day"])
    night_path = resolve_path(cfg["paths"]["curated_night"])
    weather_dir = resolve_path(cfg["paths"]["weather_dir"])
    index_path = resolve_path(cfg["paths"]["weather_index"])
    ensure_dirs(weather_dir)

    frames = load_curated_jsonl(day_path) + load_curated_jsonl(night_path)
    if args.limit:
        frames = frames[: args.limit]

    # Group frames by local date for efficient API calls
    by_local_date: dict[date, list[dict]] = defaultdict(list)
    tz = ZoneInfo(cfg["cabin"]["timezone"])
    for frame in frames:
        dt = datetime.fromisoformat(frame["exif_iso"].replace("Z", "+00:00")).astimezone(tz)
        by_local_date[dt.date()].append(frame)

    dates = sorted(by_local_date.keys())
    print(f"Fetching weather for {len(frames)} frames across {len(dates)} local dates...")

    cache: dict[str, dict] = {}
    index_rows = []
    missing = []

    with requests.Session() as session:
        for i, d in enumerate(dates, 1):
            try:
                day_data = fetch_day_archive(session, cfg, d)
                cache.update(day_data)
            except Exception as exc:  # noqa: BLE001
                print(f"  WARN: failed day {d}: {exc}")
                time.sleep(2)
                try:
                    day_data = fetch_day_archive(session, cfg, d)
                    cache.update(day_data)
                except Exception as exc2:  # noqa: BLE001
                    print(f"  ERROR: retry failed {d}: {exc2}")
                    for frame in by_local_date[d]:
                        missing.append(frame["filename"])
                    continue

            if i % 10 == 0 or i == len(dates):
                print(f"  days {i}/{len(dates)} cache_hours={len(cache)}")
            time.sleep(0.15)

        for frame in frames:
            dt = datetime.fromisoformat(frame["exif_iso"].replace("Z", "+00:00")).astimezone(tz)
            hour_label = dt.strftime("%Y-%m-%dT%H:00")
            era5 = cache.get(hour_label)
            if not era5:
                missing.append(frame["filename"])
                continue

            pkt = enrich_packet(cfg, frame, {hour_label: era5})
            out = weather_dir / f"{frame['filename']}.json"
            write_json(out, pkt)
            index_rows.append(
                {
                    "filename": frame["filename"],
                    "exif_iso": frame["exif_iso"],
                    "bucket": frame.get("bucket"),
                    "weather_path": str(out.relative_to(REPO_ROOT)),
                    "hour_local": hour_label,
                    "cloud_cover": pkt.get("cloud_cover"),
                    "weather_code": pkt.get("weather_code"),
                    "solar_elevation": pkt.get("solar_elevation"),
                }
            )

    index = {
        "source": cfg["weather"]["archive_api"],
        "variables": cfg["weather"]["hourly_variables"],
        "counts": {
            "frames_requested": len(frames),
            "packets_written": len(index_rows),
            "missing": len(missing),
        },
        "missing_filenames": missing,
        "frames": index_rows,
    }
    write_json(index_path, index)

    print(f"Weather packets: {len(index_rows)}/{len(frames)} written to {weather_dir}")
    if missing:
        print(f"  missing: {len(missing)}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
