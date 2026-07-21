#!/usr/bin/env python3
"""Build M3 gate references: DINOv2 real-frame index + CLIP season calibration.

- DINOv2 index: embed archive day frames → data/gates/dino_index.npz. This is the
  "real-frame distribution" the identity-collapse detector measures against (#9).
- Season calibration: CLIP zero-shot has class priors; we estimate a per-class
  bias over a season-balanced archive sample so the classifier isn't biased toward
  whatever season CLIP over-predicts (#10). Saved to data/gates/season_calibration.json.

Usage:
  PYTHONPATH=. .venv/bin/python scripts/build_gates_refs.py            # all day frames
  PYTHONPATH=. .venv/bin/python scripts/build_gates_refs.py --cap 120  # stratified sample
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dream.config import resolve_path  # noqa: E402
from dream.gates.embed import DinoReference, embed_image  # noqa: E402
from dream.gates.season import (  # noqa: E402
    COARSE_SEASONS,
    classify_season,
    expected_coarse_season,
)
from weather_schema.vector import precip_class  # noqa: E402
from PIL import Image  # noqa: E402


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def curated_day_frames(dataset_cfg: dict) -> list[dict]:
    path = resolve_path(dataset_cfg["paths"]["curated_day"])
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def frame_packet(dataset_cfg: dict, filename: str) -> dict | None:
    wdir = resolve_path(dataset_cfg["paths"]["weather_dir"])
    p = wdir / f"{filename}.json"
    if not p.exists():
        return None
    return json.load(open(p))


def stratified_sample(rows: list[dict], packets: dict, cap: int, seed: int) -> list[dict]:
    """Even sample across (coarse season x precip class)."""
    if cap <= 0 or cap >= len(rows):
        return rows
    rng = np.random.default_rng(seed)
    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        pkt = packets.get(r["filename"])
        if pkt is None:
            continue
        key = (expected_coarse_season(pkt["month"]), precip_class(pkt.get("weather_code")))
        buckets[key].append(r)
    keys = list(buckets)
    per = max(1, cap // max(1, len(keys)))
    out: list[dict] = []
    for key in keys:
        grp = buckets[key]
        idx = rng.permutation(len(grp))[:per]
        out.extend(grp[i] for i in idx)
    return out[:cap]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gates-config", default="config/gates.yaml")
    ap.add_argument("--cap", type=int, default=None, help="Override dino_index_cap")
    ap.add_argument("--skip-dino", action="store_true")
    ap.add_argument("--skip-calibration", action="store_true")
    args = ap.parse_args()

    gates = load_yaml(resolve_path(args.gates_config))
    dataset_cfg = load_yaml(resolve_path("config/dataset.yaml"))
    raw_dir = resolve_path(dataset_cfg["paths"]["raw_dir"])

    rows = curated_day_frames(dataset_cfg)
    packets = {}
    for r in rows:
        pkt = frame_packet(dataset_cfg, r["filename"])
        if pkt is not None:
            packets[r["filename"]] = pkt

    cap = args.cap if args.cap is not None else int(gates["paths"].get("dino_index_cap", 0))
    sample = stratified_sample(rows, packets, cap, gates["eval"]["seed"])
    print(f"Reference sample: {len(sample)} / {len(rows)} day frames")

    if not args.skip_dino:
        model_id = gates["models"]["dino"]
        names, embs = [], []
        for i, r in enumerate(sample):
            fp = raw_dir / r["filename"]
            if not fp.exists():
                continue
            embs.append(embed_image(Image.open(fp), model_id))
            names.append(r["filename"])
            if (i + 1) % 25 == 0:
                print(f"  DINOv2 {i + 1}/{len(sample)}")
        ref = DinoReference(filenames=names, embeddings=np.vstack(embs))
        out = resolve_path(gates["paths"]["dino_index"])
        ref.save(out)
        print(f"DINOv2 index: {len(ref)} frames → {out}")

    if not args.skip_calibration:
        by_season: dict[str, list[dict]] = defaultdict(list)
        for r in sample:
            pkt = packets.get(r["filename"])
            if pkt:
                by_season[expected_coarse_season(pkt["month"])].append(r)
        acc = {s: [] for s in COARSE_SEASONS}
        for season, grp in by_season.items():
            for r in grp[:30]:  # cap per season for speed
                fp = raw_dir / r["filename"]
                if not fp.exists():
                    continue
                sc = classify_season(Image.open(fp), gates)  # uncalibrated
                for s in COARSE_SEASONS:
                    acc[s].append(sc[s])
        # Bias = mean uncalibrated log-prob per class; subtracting it debiases.
        calibration = {
            s: float(np.mean(v)) if v else 0.0 for s, v in acc.items()
        }
        out = resolve_path(gates["paths"]["season_calibration"])
        out.parent.mkdir(parents=True, exist_ok=True)
        json.dump(calibration, open(out, "w"), indent=2)
        print(f"Season calibration → {out}: {calibration}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
