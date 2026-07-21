#!/usr/bin/env python3
"""Curate manifest: night bucket, dedupe, write day.jsonl + night.jsonl."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import imagehash
from PIL import Image

from dataset_common import (
    REPO_ROOT,
    append_jsonl,
    load_config,
    resolve_path,
    write_json,
)

sys.path.insert(0, str(REPO_ROOT / "scripts"))


def local_date(cfg, exif_iso: str) -> str:
    dt = datetime.fromisoformat(exif_iso.replace("Z", "+00:00"))
    tz = ZoneInfo(cfg["cabin"]["timezone"])
    return dt.astimezone(tz).strftime("%Y-%m-%d")


def main() -> int:
    parser = argparse.ArgumentParser(description="Curate dataset buckets")
    args = parser.parse_args()

    cfg = load_config()
    manifest_path = resolve_path(cfg["paths"]["manifest"])
    raw_dir = resolve_path(cfg["paths"]["raw_dir"])
    day_path = resolve_path(cfg["paths"]["curated_day"])
    night_path = resolve_path(cfg["paths"]["curated_night"])

    with open(manifest_path) as f:
        manifest = json.load(f)

    night_threshold = float(cfg["curation"]["night_solar_elevation_deg"])
    hamming_threshold = int(cfg["curation"]["dedupe_hamming_threshold"])
    downweight = float(cfg["curation"]["dedupe_downweight"])

    eligible = [
        e
        for e in manifest["entries"]
        if e["exif_ok"]
        and not e["excluded"]
        and (raw_dir / e["filename"]).exists()
    ]

    day_entries: list[dict] = []
    night_entries: list[dict] = []

    for e in eligible:
        elev = e.get("solar_elevation_deg")
        if elev is not None and elev < night_threshold:
            e["bucket"] = "night"
            night_entries.append(e)
        else:
            e["bucket"] = "day"
            day_entries.append(e)

    # Dedupe within bucket, grouped by local calendar day
    def dedupe_bucket(entries: list[dict], bucket_name: str) -> None:
        by_day: dict[str, list[dict]] = defaultdict(list)
        for e in entries:
            by_day[local_date(cfg, e["exif_iso"])].append(e)

        group_id = 0
        for day, day_list in sorted(by_day.items()):
            day_list.sort(key=lambda x: x["exif_iso"])
            hashes: list[tuple[str, imagehash.ImageHash]] = []
            groups: list[list[dict]] = []

            for e in day_list:
                path = raw_dir / e["filename"]
                try:
                    with Image.open(path) as img:
                        h = imagehash.phash(img)
                except Exception:  # noqa: BLE001
                    e["dedupe_group"] = f"{bucket_name}-{day}-solo-{e['filename']}"
                    e["weight"] = 1.0
                    continue

                matched_group: list[dict] | None = None
                for gi, (gh, _) in enumerate(hashes):
                    if h - gh <= hamming_threshold:
                        matched_group = groups[gi]
                        break

                if matched_group is None:
                    gid = f"{bucket_name}-{day}-g{group_id}"
                    group_id += 1
                    hashes.append((h, gid))
                    groups.append([e])
                    e["dedupe_group"] = gid
                    e["weight"] = 1.0
                    e["dedupe_representative"] = True
                else:
                    rep = matched_group[0]
                    e["dedupe_group"] = rep["dedupe_group"]
                    e["weight"] = downweight
                    e["dedupe_representative"] = False
                    matched_group.append(e)

    dedupe_bucket(day_entries, "day")
    dedupe_bucket(night_entries, "night")

    def slim(e: dict) -> dict:
        return {
            "filename": e["filename"],
            "path": e["path"],
            "exif_iso": e["exif_iso"],
            "bucket": e["bucket"],
            "solar_elevation_deg": e.get("solar_elevation_deg"),
            "dedupe_group": e.get("dedupe_group"),
            "weight": e.get("weight", 1.0),
            "dedupe_representative": e.get("dedupe_representative", True),
            "width": e.get("width"),
            "height": e.get("height"),
            "aspect_ok": e.get("aspect_ok"),
            "canonical_frame": e["filename"] == cfg["canonical_frame"],
        }

    day_rows = [slim(e) for e in day_entries]
    night_rows = [slim(e) for e in night_entries]

    append_jsonl(day_path, day_rows)
    append_jsonl(night_path, night_rows)

    day_reps = sum(1 for r in day_rows if r.get("dedupe_representative"))
    night_reps = sum(1 for r in night_rows if r.get("dedupe_representative"))

    summary = {
        "night_definition": {
            "method": "solar_elevation",
            "threshold_deg": night_threshold,
            "description": "Night when solar elevation < −6° (civil twilight end, USNO). Dawn/dusk stay in day bucket.",
        },
        "dedupe": {
            "method": "perceptual_hash_phash",
            "hamming_threshold": hamming_threshold,
            "scope": "within bucket and local calendar day (America/St_Johns)",
            "representative_weight": 1.0,
            "duplicate_weight": downweight,
        },
        "counts": {
            "eligible_exif": len(eligible),
            "day_total": len(day_rows),
            "day_representatives": day_reps,
            "day_downweighted": len(day_rows) - day_reps,
            "night_total": len(night_rows),
            "night_representatives": night_reps,
            "night_downweighted": len(night_rows) - night_reps,
            "excluded": manifest["counts"]["excluded"],
        },
    }

    write_json(resolve_path("data/curated/summary.json"), summary)

    # Update manifest entries with bucket/dedupe fields
    by_name = {e["filename"]: e for e in manifest["entries"]}
    for e in day_entries + night_entries:
        by_name[e["filename"]].update(
            {
                "bucket": e["bucket"],
                "dedupe_group": e.get("dedupe_group"),
                "weight": e.get("weight", 1.0),
            }
        )
    write_json(manifest_path, manifest)

    print(f"Day:   {len(day_rows)} frames ({day_reps} representatives)")
    print(f"Night: {len(night_rows)} frames ({night_reps} representatives)")
    print(f"Wrote {day_path} and {night_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
