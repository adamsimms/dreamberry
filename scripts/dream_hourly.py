#!/usr/bin/env python3
"""Run one Dreamberry hourly tick: weather → generate → gate → publish/hold/noise.

This is the M4 hourly path (issue #14). It fetches the live weather packet (or
replays a supplied packet), generates at the given dial, runs the identity +
season gates, and maps the outcome to the three brief failure modes, writing
public/status.json (+ current frame) and the private hourly archive locally.
R2 / Pages delivery is M5.

Examples:
  # live weather, dial-0 public default
  PYTHONPATH=. .venv/bin/python scripts/dream_hourly.py

  # replay an archive weather packet (no network), keep artifacts in a temp dir
  PYTHONPATH=. .venv/bin/python scripts/dream_hourly.py \
    --packet data/weather/<frame>.json

  # simulate weather silence handling without hitting the GPU
  PYTHONPATH=. .venv/bin/python scripts/dream_hourly.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from dream.config import resolve_path  # noqa: E402
from dream.hourly import OUTCOME_PUBLISHED, run_hourly  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dial", type=float, default=0.0, help="Dial value (0-10); public default 0")
    ap.add_argument("--packet", default=None, help="Replay a weather packet JSON instead of live fetch")
    ap.add_argument("--seed-base", type=int, default=None, help="Override base seed")
    ap.add_argument("--retries", type=int, default=None, help="Override retry count")
    ap.add_argument("--no-wyi", action="store_true", help="Skip WYI enrichment on live fetch")
    ap.add_argument("--no-buoy", action="store_true", help="Skip buoy enrichment on live fetch")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Decide + print but do not write artifacts",
    )
    args = ap.parse_args()

    packet = None
    if args.packet:
        with open(resolve_path(args.packet)) as f:
            packet = json.load(f)
        # Symmetry: archive packets carry after_solar_noon via enrich; live ones
        # already do. enrich_packet is idempotent, so apply it for replays.
        from dream_generate import enrich_packet

        packet = enrich_packet(packet)

    # A supplied packet is an intentional replay — don't let 2017 staleness trip
    # the live-feed weather-silence gate (still honors missing core fields).
    result = run_hourly(
        dial=args.dial,
        packet=packet,
        seed_base=args.seed_base,
        retries=args.retries,
        write=not args.dry_run,
        skip_silence=bool(packet is not None),
        fetch_wyi=not args.no_wyi,
        fetch_buoy=not args.no_buoy,
    )

    print(f"outcome:      {result.outcome}")
    print(f"failure_mode: {result.failure_mode}")
    if result.hold_reason:
        print(f"hold_reason:  {result.hold_reason}")
    print(f"attempts:     {result.attempts}")
    if result.dream_id:
        print(f"dream_id:     {result.dream_id}")
    if result.image_path:
        print(f"current:      {result.image_path}")
    if result.outcome == OUTCOME_PUBLISHED and result.sidecar:
        vs = result.sidecar.get("validator_scores", {})
        collapse = (vs.get("collapse") or {}).get("action")
        season = (vs.get("season") or {}).get("action")
        print(f"gates:        collapse={collapse} season={season}")
    print(f"status:       hold={result.status.get('hold')} last_success_at={result.status.get('last_success_at')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
