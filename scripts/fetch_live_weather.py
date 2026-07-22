#!/usr/bin/env python3
"""Fetch a live weather condition packet for Dreamberry inference.

Examples:
  PYTHONPATH=. .venv/bin/python scripts/fetch_live_weather.py
  PYTHONPATH=. .venv/bin/python scripts/fetch_live_weather.py --write
  PYTHONPATH=. .venv/bin/python scripts/fetch_live_weather.py --no-wyi --no-buoy
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from weather_schema.live import (  # noqa: E402
    build_live_packet,
    check_weather_silence,
    load_weather_config,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch live weather packet for inference")
    ap.add_argument(
        "--write",
        action="store_true",
        help="Write packet to data/live/current.json (from config/weather.yaml)",
    )
    ap.add_argument("--no-wyi", action="store_true", help="Skip ECCC WYI enrichment")
    ap.add_argument("--no-buoy", action="store_true", help="Skip SmartAtlantic buoy")
    ap.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print JSON (default: on)",
    )
    args = ap.parse_args()

    pkt = build_live_packet(
        fetch_wyi=not args.no_wyi,
        fetch_buoy=not args.no_buoy,
    )
    silence = check_weather_silence(pkt)

    if args.write:
        weather_cfg = load_weather_config()
        out_path = REPO_ROOT / weather_cfg["paths"]["live_current"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(pkt, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"Wrote {out_path.relative_to(REPO_ROOT)}", file=sys.stderr)

    indent = 2 if args.pretty else None
    print(json.dumps(pkt, ensure_ascii=False, indent=indent))

    if silence.is_silence:
        print(
            f"weather_silence: {', '.join(silence.reasons)}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
