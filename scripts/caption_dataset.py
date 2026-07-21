#!/usr/bin/env python3
"""Caption curated frames with compose_prompt (Dreamberry M1 / issue #5).

Reads weather packets + curated day/night lists, writes JSONL captions.
Also records after_solar_noon from astral solar noon (symmetry with live path).

Usage:
  python scripts/caption_dataset.py
  python scripts/caption_dataset.py --bucket day
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from astral.sun import noon

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from dataset_common import (  # noqa: E402
    cabin_location,
    load_config,
    parse_exif_datetime,
    resolve_path,
)
from weather_schema.compose import (  # noqa: E402
    assert_closed_vocabulary,
    compose_prompt,
)
from weather_schema.vector import feature_vector  # noqa: E402


def after_solar_noon(cfg: dict, dt_utc: datetime) -> bool:
    loc = cabin_location(cfg)
    tz = ZoneInfo(cfg["cabin"]["timezone"])
    dt_local = dt_utc.astimezone(tz)
    n = noon(loc.observer, date=dt_local.date(), tzinfo=tz)
    return dt_local >= n


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def caption_row(cfg: dict, weather_dir: Path, row: dict) -> dict | None:
    fn = row["filename"]
    wpath = weather_dir / f"{fn}.json"
    if not wpath.exists():
        return None
    with open(wpath) as f:
        pkt = json.load(f)

    dt = parse_exif_datetime(pkt.get("exif_iso") or row.get("exif_iso"))
    if dt is None:
        return None

    pkt = dict(pkt)
    pkt["after_solar_noon"] = after_solar_noon(cfg, dt)

    prompt = compose_prompt(pkt)
    assert_closed_vocabulary(prompt)
    vals, _weights = feature_vector(pkt)

    return {
        "filename": fn,
        "bucket": row.get("bucket") or pkt.get("bucket"),
        "weight": row.get("weight", 1.0),
        "dedupe_representative": row.get("dedupe_representative", True),
        "prompt": prompt,
        "feature_vector": vals,
        "month": pkt.get("month"),
        "solar_elevation": pkt.get("solar_elevation"),
        "after_solar_noon": pkt["after_solar_noon"],
        "weather_path": str(wpath.relative_to(REPO_ROOT)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bucket", choices=("day", "night", "all"), default="all")
    ap.add_argument(
        "--out",
        default="data/captions/captions.jsonl",
        help="Output JSONL path (repo-relative)",
    )
    args = ap.parse_args()

    cfg = load_config()
    weather_dir = resolve_path(cfg["paths"]["weather_dir"])
    out_path = resolve_path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sources: list[Path] = []
    if args.bucket in ("day", "all"):
        sources.append(resolve_path(cfg["paths"]["curated_day"]))
    if args.bucket in ("night", "all"):
        sources.append(resolve_path(cfg["paths"]["curated_night"]))

    written = 0
    missing = 0
    with open(out_path, "w") as out:
        for src in sources:
            for row in load_jsonl(src):
                cap = caption_row(cfg, weather_dir, row)
                if cap is None:
                    missing += 1
                    continue
                out.write(json.dumps(cap, ensure_ascii=False) + "\n")
                written += 1

    print(f"Wrote {written} captions → {out_path}")
    if missing:
        print(f"Skipped {missing} (missing weather or EXIF)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
