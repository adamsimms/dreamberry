#!/usr/bin/env python3
"""Build and query the weather nearest-neighbor index.

Usage:
  PYTHONPATH=. python scripts/build_weather_nn_index.py
  PYTHONPATH=. python scripts/build_weather_nn_index.py --query data/weather/FOO.json
  PYTHONPATH=. python scripts/build_weather_nn_index.py --from-weather
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from dataset_common import load_config, resolve_path  # noqa: E402
from weather_schema.retrieve import WeatherNNIndex  # noqa: E402


def build_index(cfg: dict, *, from_weather: bool) -> WeatherNNIndex:
    night_thresh = float(cfg["curation"]["night_solar_elevation_deg"])
    if from_weather:
        weather_dir = resolve_path(cfg["paths"]["weather_dir"])
        curated = [
            resolve_path(cfg["paths"]["curated_day"]),
            resolve_path(cfg["paths"]["curated_night"]),
        ]
        return WeatherNNIndex.build_from_weather(
            weather_dir,
            curated_paths=curated,
            night_solar_elevation_deg=night_thresh,
        )

    captions_path = resolve_path(cfg["paths"]["captions"])
    return WeatherNNIndex.build_from_captions(
        captions_path,
        night_solar_elevation_deg=night_thresh,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        help="Output index path (default: config paths.weather_nn_index)",
    )
    ap.add_argument(
        "--from-weather",
        action="store_true",
        help="Rebuild vectors from weather packets instead of captions.jsonl",
    )
    ap.add_argument(
        "--query",
        metavar="WEATHER_JSON",
        help="Smoke-test query against saved index (or build in-memory first)",
    )
    ap.add_argument("-k", type=int, default=5, help="Top-k neighbors (default 5)")
    ap.add_argument(
        "--include-prompt",
        action="store_true",
        help="Include anchor prompt strings in query output",
    )
    args = ap.parse_args()

    cfg = load_config()
    out_path = resolve_path(args.out or cfg["paths"]["weather_nn_index"])

    if args.query:
        query_path = resolve_path(args.query)
        with open(query_path) as f:
            pkt = json.load(f)
        if out_path.exists():
            index = WeatherNNIndex.load(out_path)
        else:
            index = build_index(cfg, from_weather=args.from_weather)
        hits = index.query(pkt, k=args.k, include_prompt=args.include_prompt)
        print(json.dumps(hits, indent=2, ensure_ascii=False))
        return 0

    index = build_index(cfg, from_weather=args.from_weather)
    index.save(out_path)
    print(f"Wrote {len(index)} entries → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
