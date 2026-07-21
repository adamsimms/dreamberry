#!/usr/bin/env python3
"""Sync local Dreamberry corpus into the Modal data Volume (M5).

Uploads the pieces the hourly tick needs on L40S:
  data/raw/          — Cloudberry originals (anchor + ControlNet source)
  data/captions/     — weather_nn_index.json (+ captions)
  data/gates/        — DINOv2 index + season calibration
  data/curated/      — curated lists (optional; small)

Does NOT upload data/dream/ (generated) or data/weather/ (ERA5 packets;
live inference fetches Open-Meteo).

Usage:
  PYTHONPATH=. .venv/bin/python scripts/sync_modal_data.py
  PYTHONPATH=. .venv/bin/python scripts/sync_modal_data.py --dry-run
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VOLUME = "dreamberry-data"

# (local relative path, remote path inside the Volume which mounts at data/)
SYNCS = (
    ("data/raw", "raw"),
    ("data/captions", "captions"),
    ("data/gates", "gates"),
    ("data/curated", "curated"),
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--volume", default=VOLUME)
    args = ap.parse_args()

    modal = REPO / ".venv" / "bin" / "modal"
    if not modal.exists():
        modal = Path(sys.executable).parent / "modal"

    if not args.dry_run:
        # create_if_missing equivalent for CLI
        subprocess.run(
            [str(modal), "volume", "create", args.volume],
            cwd=REPO,
            check=False,
            capture_output=True,
        )

    for local_rel, remote in SYNCS:
        local = REPO / local_rel
        if not local.exists():
            print(f"skip missing {local_rel}")
            continue
        cmd = [str(modal), "volume", "put", args.volume, str(local), remote]
        print(" ".join(cmd))
        if args.dry_run:
            continue
        subprocess.check_call(cmd, cwd=REPO)

    print("done — volume:", args.volume)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
