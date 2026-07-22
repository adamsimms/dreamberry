#!/usr/bin/env python3
"""Generate a Dreamberry still from a weather packet.

Runs the dial-0 lock by default: weather-nearest real frame (img2img init) +
ControlNet depth+soft-edge from the canonical geometry frame + IP-Adapter
atmosphere. Writes a PNG and a JSON provenance sidecar.

Examples:
  # dial-0 from a specific archive weather packet
  PYTHONPATH=. python scripts/dream_generate.py \
    --packet data/weather/2017-09-18T09:59:44.000Z_GOPR2537.JPG.json

  # a small dial sweep for the same packet
  PYTHONPATH=. python scripts/dream_generate.py --packet <pkt.json> \
    --dials 0 2 5 --seed 1234
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from astral.sun import noon

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from dataset_common import cabin_location, load_config, parse_exif_datetime  # noqa: E402
from dream.config import load_dream_config, resolve_path  # noqa: E402
from dream.pipeline import DreamEngine  # noqa: E402
from dream.sidecar import write_sidecar  # noqa: E402


def enrich_packet(pkt: dict) -> dict:
    """Add after_solar_noon from EXIF instant (symmetry with caption path)."""
    if "after_solar_noon" in pkt and pkt["after_solar_noon"] is not None:
        return pkt
    dt = parse_exif_datetime(pkt.get("exif_iso"))
    if dt is None:
        return pkt
    ds = load_config()
    loc = cabin_location(ds)
    tz = ZoneInfo(ds["cabin"]["timezone"])
    dt_local = dt.astimezone(tz)
    solar_noon = noon(loc.observer, date=dt_local.date(), tzinfo=tz)
    pkt = dict(pkt)
    pkt["after_solar_noon"] = dt_local >= solar_noon
    return pkt


_DREAM_RE = re.compile(r"_DREAM(\d+)\.JPG$")


def dream_timestamp(pkt: dict) -> str:
    """The instant being dreamed, in the archive's ISO-Z form (matches Cloudberry)."""
    ts = pkt.get("exif_iso") or pkt.get("timestamp")
    if ts:
        return str(ts)
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def next_dream_number(out_dir: Path) -> int:
    """Next roll counter across existing dreams (mirrors the GoPro GOPR#### counter)."""
    mx = 0
    for p in out_dir.glob("*_DREAM*.JPG"):
        m = _DREAM_RE.search(p.name)
        if m:
            mx = max(mx, int(m.group(1)))
    return mx + 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--packet", required=True, help="Weather packet JSON (repo-relative or absolute)")
    ap.add_argument("--dial", type=float, default=0.0, help="Single dial value (0-10)")
    ap.add_argument("--dials", type=float, nargs="+", help="Dial sweep (overrides --dial)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None, help="Output dir (default: generation.outputs_dir)")
    ap.add_argument("--prompt", default=None, help="Override composed prompt")
    args = ap.parse_args()

    dream_cfg = load_dream_config()
    packet_path = resolve_path(args.packet)
    with open(packet_path) as f:
        pkt = enrich_packet(json.load(f))

    out_dir = resolve_path(args.out) if args.out else resolve_path(dream_cfg["paths"]["outputs_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    dials = args.dials if args.dials else [args.dial]

    engine = DreamEngine(dream_cfg)
    print(f"Device: {engine.device}  |  packet: {packet_path.name}")

    timestamp = dream_timestamp(pkt)
    for dial in dials:
        result = engine.generate(pkt, dial=dial, seed=args.seed, prompt=args.prompt)
        # Each dream gets its own roll number, like a consecutive shot on the camera.
        number = next_dream_number(out_dir)
        name = f"{timestamp}_DREAM{number:03d}"
        jpg_path = out_dir / f"{name}.JPG"
        json_path = out_dir / f"{name}.json"
        result.sidecar["dream_id"] = name
        result.image.save(jpg_path, "JPEG", quality=95, subsampling=0)
        write_sidecar(json_path, result.sidecar)
        print(f"  dial {dial:g} → {jpg_path.name}")
        print(f"    prompt: {result.sidecar['prompt']}")
        print(f"    anchor: {result.sidecar['anchor_frame']} ({result.sidecar['anchor_source']})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
