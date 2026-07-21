#!/usr/bin/env python3
"""Extract EXIF DateTimeOriginal and build data/manifest.json."""

from __future__ import annotations

import argparse
import sys
from datetime import timezone

from PIL import Image
from PIL.ExifTags import TAGS

from dataset_common import (
    REPO_ROOT,
    iso_z,
    load_catalog,
    load_config,
    parse_exif_datetime,
    resolve_path,
    solar_elevation_deg,
    write_json,
)

sys.path.insert(0, str(REPO_ROOT / "scripts"))


def exif_datetime_original(path) -> str | None:
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if not exif:
                return None
            tag_map = {TAGS.get(k, k): v for k, v in exif.items()}
            for key in ("DateTimeOriginal", "DateTime", "DateTimeDigitized"):
                if key in tag_map:
                    return tag_map[key]
    except Exception:  # noqa: BLE001
        return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Build manifest from EXIF")
    args = parser.parse_args()

    cfg = load_config()
    raw_dir = resolve_path(cfg["paths"]["raw_dir"])
    manifest_path = resolve_path(cfg["paths"]["manifest"])
    exclude = set(cfg["curation"]["exclude_filenames"])

    photos = load_catalog(cfg)
    catalog_by_name = {p["filename"]: p for p in photos}

    entries = []
    missing_files = []
    exif_missing = []
    exif_mismatch = []

    for i, photo in enumerate(photos):
        fn = photo["filename"]
        path = raw_dir / fn
        catalog_iso = photo.get("captureDateIso")
        catalog_dt = None
        if catalog_iso:
            from dateutil import parser as date_parser

            catalog_dt = date_parser.parse(catalog_iso).astimezone(timezone.utc)

        row = {
            "filename": fn,
            "path": str(path.relative_to(REPO_ROOT)),
            "catalog_iso": catalog_dt.isoformat().replace("+00:00", "Z") if catalog_dt else None,
            "exif_raw": None,
            "exif_iso": None,
            "exif_ok": False,
            "exif_catalog_delta_sec": None,
            "excluded": fn in exclude,
            "exclusion_reason": "indoor_selfie" if fn in exclude else None,
            "width": None,
            "height": None,
            "aspect_ok": False,
            "solar_elevation_deg": None,
            "bucket": None,
            "dedupe_group": None,
            "weight": 1.0,
            "image_url": photo.get("imageUrl"),
        }

        if not path.exists():
            missing_files.append(fn)
            entries.append(row)
            continue

        try:
            with Image.open(path) as img:
                row["width"] = img.width
                row["height"] = img.height
                exp_w = cfg["curation"]["expected_width"]
                exp_h = cfg["curation"]["expected_height"]
                row["aspect_ok"] = (
                    img.width == exp_w
                    and img.height == exp_h
                    and img.width * 3 == img.height * 4
                )
        except Exception:  # noqa: BLE001
            pass

        raw = exif_datetime_original(path)
        row["exif_raw"] = raw
        exif_dt = parse_exif_datetime(raw)
        if exif_dt:
            row["exif_iso"] = iso_z(exif_dt)
            row["exif_ok"] = True
            row["solar_elevation_deg"] = round(solar_elevation_deg(cfg, exif_dt), 3)
            if catalog_dt:
                delta = abs((exif_dt - catalog_dt).total_seconds())
                row["exif_catalog_delta_sec"] = int(delta)
                if delta > 2:
                    exif_mismatch.append(
                        {
                            "filename": fn,
                            "exif_iso": row["exif_iso"],
                            "catalog_iso": row["catalog_iso"],
                            "delta_sec": int(delta),
                        }
                    )
        else:
            exif_missing.append(fn)

        entries.append(row)
        if (i + 1) % 200 == 0:
            print(f"  processed {i + 1}/{len(photos)}")

    manifest = {
        "version": 1,
        "canonical_frame": cfg["canonical_frame"],
        "cabin": cfg["cabin"],
        "counts": {
            "catalog": len(photos),
            "present_on_disk": sum(1 for e in entries if (raw_dir / e["filename"]).exists()),
            "exif_ok": sum(1 for e in entries if e["exif_ok"]),
            "exif_missing": len(exif_missing),
            "exif_catalog_mismatch_gt2s": len(exif_mismatch),
            "excluded": sum(1 for e in entries if e["excluded"]),
            "missing_files": len(missing_files),
        },
        "exif_mismatches": exif_mismatch,
        "entries": entries,
    }

    write_json(manifest_path, manifest)
    print(f"Wrote {manifest_path}")
    print(f"  present={manifest['counts']['present_on_disk']} exif_ok={manifest['counts']['exif_ok']}")
    print(f"  mismatches(>2s)={manifest['counts']['exif_catalog_mismatch_gt2s']} missing_files={len(missing_files)}")
    return 0 if not missing_files else 1


if __name__ == "__main__":
    raise SystemExit(main())
