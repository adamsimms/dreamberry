#!/usr/bin/env python3
"""Private dream-dial sweep for local review (M6 / issue #21).

The public window is locked to **artist-only, dial 0** (DREAMBERRY.md §6). Dial
experiments happen here, privately, and must never touch the public pointer:

  * writes only under `data/dream/dial/` (gitignored) — a dedicated sandbox,
    kept out of the hourly archive and its DREAM### roll counter;
  * never imports `dream.storage`, never uploads to R2, never writes status.json;
  * emits a plain `contact.html` per packet so a sweep can be eyeballed locally
    without muddling the public frames.

Usage:
  PYTHONPATH=. .venv/bin/python scripts/dial_sweep.py \
    --packet data/weather/2017-09-18T09:59:44.000Z_GOPR2537.JPG.json \
    --dials 0 2 4 6 8 10 --seed 1234

  # a couple of seeds per dial, into a named run
  PYTHONPATH=. .venv/bin/python scripts/dial_sweep.py --packet <pkt.json> \
    --dials 0 5 10 --seeds 1 2 3 --run mid-dial-probe
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from dream.config import load_dream_config, resolve_path  # noqa: E402
from dream.pipeline import DreamEngine  # noqa: E402
from dream.sidecar import write_sidecar  # noqa: E402
from dream_generate import dream_timestamp, enrich_packet  # noqa: E402

# Hard-wired private sandbox — deliberately NOT generation.outputs_dir, so a
# sweep can never be confused with (or promoted into) the hourly archive.
DIAL_ROOT = REPO_ROOT / "data" / "dream" / "dial"


def _contact_sheet(out_dir: Path, packet_name: str, entries: list[dict]) -> None:
    """Tiny static gallery for local eyeballing — never published."""
    cells = []
    for e in entries:
        cells.append(
            f"""<figure>
  <img src="{html.escape(e['file'])}" loading="lazy" alt="dial {e['dial']} seed {e['seed']}" />
  <figcaption>dial {e['dial']:g} · seed {e['seed']}</figcaption>
</figure>"""
        )
    doc = f"""<!doctype html>
<meta charset="utf-8">
<title>dial sweep — {html.escape(packet_name)}</title>
<style>
  body {{ background:#0a0b0d; color:#e9e6df; font:14px system-ui; margin:2rem; }}
  h1 {{ font-weight:500; font-size:1rem; color:#9a978f; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:1rem; }}
  figure {{ margin:0; }}
  img {{ width:100%; border:1px solid #2a2b2f; border-radius:3px; display:block; }}
  figcaption {{ color:#9a978f; font-size:.75rem; margin-top:.35rem; letter-spacing:.04em; }}
  p.note {{ color:#6b6862; font-size:.8rem; }}
</style>
<h1>Dial sweep — {html.escape(packet_name)}</h1>
<p class="note">Private review only. Public window stays artist-only @ dial 0.</p>
<div class="grid">
{chr(10).join(cells)}
</div>
"""
    (out_dir / "contact.html").write_text(doc)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--packet", required=True, help="Weather packet JSON")
    ap.add_argument(
        "--dials",
        type=float,
        nargs="+",
        default=[0, 2, 4, 6, 8, 10],
        help="Dial values to sweep (default 0 2 4 6 8 10)",
    )
    ap.add_argument("--seeds", type=int, nargs="+", help="One or more seeds per dial")
    ap.add_argument("--seed", type=int, default=0, help="Single seed (if --seeds absent)")
    ap.add_argument("--run", default=None, help="Optional run label (subfolder)")
    ap.add_argument("--prompt", default=None, help="Override composed prompt")
    args = ap.parse_args()

    seeds = args.seeds if args.seeds else [args.seed]

    dream_cfg = load_dream_config()
    packet_path = resolve_path(args.packet)
    with open(packet_path) as f:
        pkt = enrich_packet(json.load(f))

    stem = packet_path.name.replace(".json", "")
    out_dir = DIAL_ROOT / stem
    if args.run:
        out_dir = out_dir / args.run
    out_dir.mkdir(parents=True, exist_ok=True)

    engine = DreamEngine(dream_cfg)
    print(f"Device: {engine.device}  |  packet: {packet_path.name}")
    print(f"Private sweep → {out_dir}  (never published)")

    timestamp = dream_timestamp(pkt)
    entries: list[dict] = []
    for dial in args.dials:
        for seed in seeds:
            result = engine.generate(pkt, dial=dial, seed=seed, prompt=args.prompt)
            # Deliberately NOT the _DREAM### archive convention — these are probes.
            name = f"dial{dial:g}_seed{seed}"
            img_path = out_dir / f"{name}.png"
            result.image.save(img_path, "PNG", optimize=True)
            result.sidecar["dream_id"] = f"{timestamp}_DIAL_{name}"
            write_sidecar(out_dir / f"{name}.json", result.sidecar)
            entries.append({"file": img_path.name, "dial": dial, "seed": seed})
            print(f"  dial {dial:g} seed {seed} → {img_path.name}")

    _contact_sheet(out_dir, packet_path.name, entries)
    print(f"Contact sheet: {out_dir / 'contact.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
