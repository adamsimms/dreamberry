#!/usr/bin/env python3
"""Run full M0 dataset pipeline: download → manifest → curate → weather."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"


def run(script: str, *extra: str) -> None:
    cmd = [sys.executable, str(SCRIPTS / script), *extra]
    print(f"\n=== {' '.join(cmd)} ===")
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


def main() -> int:
    steps = [
        ("download_images.py",),
        ("build_manifest.py",),
        ("curate_dataset.py",),
        ("fetch_weather.py",),
    ]
    for step in steps:
        run(*step)
    print("\nM0 pipeline complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
