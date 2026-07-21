#!/usr/bin/env python3
"""M3 eval harness: dial-0 baseline over held-out frames (issue #11).

Holds out a stratified set of real frames (season x precip), generates a dream
from each frame's *own* weather packet with leave-one-out anchor selection (the
frame is excluded from both the weather-NN anchor pool and the DINOv2 reference
so scores aren't trivially self-matched), then scores:

  - identity: DINOv2 kNN distance to real frames + horizon displacement (#9)
  - season:  calibrated CLIP zero-shot verdict (#10)
  - fidelity: CLIP similarity + LPIPS vs the real held-out frame

Writes per-frame sidecars, an aggregate JSON, and a markdown report.

Usage:
  PYTHONPATH=. .venv/bin/python scripts/eval_dream.py --n 8
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from PIL import Image  # noqa: E402

from dream.config import canonical_frame_path, load_dream_config, resolve_path  # noqa: E402
from dream.gates.embed import DinoReference, embed_image  # noqa: E402
from dream.gates.horizon import horizon_displacement  # noqa: E402
from dream.gates.identity import IdentityScores, collapse_verdict  # noqa: E402
from dream.gates.metrics import clip_similarity, lpips_distance  # noqa: E402
from dream.gates.season import classify_season, season_verdict, expected_coarse_season  # noqa: E402
from dream.pipeline import DreamEngine  # noqa: E402
from dream_generate import enrich_packet  # noqa: E402
from weather_schema.vector import precip_class  # noqa: E402


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


def select_heldout(rows, packets, n, seed):
    """Even pick across (coarse season x precip class)."""
    rng = np.random.default_rng(seed)
    buckets = defaultdict(list)
    for r in rows:
        pkt = packets.get(r["filename"])
        if pkt is None:
            continue
        key = (expected_coarse_season(pkt["month"]), precip_class(pkt.get("weather_code")))
        buckets[key].append(r)
    keys = sorted(buckets)
    picked = []
    # round-robin across buckets until we hit n
    while len(picked) < n and keys:
        for key in list(keys):
            grp = buckets[key]
            if not grp:
                keys.remove(key)
                continue
            i = int(rng.integers(len(grp)))
            picked.append(grp.pop(i))
            if len(picked) >= n:
                break
    return picked


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gates-config", default="config/gates.yaml")
    ap.add_argument("--n", type=int, default=None, help="Override eval.n_frames")
    ap.add_argument("--seed", type=int, default=None, help="Override generation seed")
    args = ap.parse_args()

    gates = load_yaml(resolve_path(args.gates_config))
    dataset_cfg = load_yaml(resolve_path("config/dataset.yaml"))
    dream_cfg = load_dream_config()
    raw_dir = resolve_path(dataset_cfg["paths"]["raw_dir"])

    n = args.n if args.n is not None else int(gates["eval"]["n_frames"])
    seed = args.seed if args.seed is not None else int(gates["eval"]["seed"])
    dial = float(gates["eval"]["dial"])

    rows = curated_day_frames(dataset_cfg)
    packets = {}
    for r in rows:
        p = resolve_path(dataset_cfg["paths"]["weather_dir"]) / f"{r['filename']}.json"
        if p.exists():
            packets[r["filename"]] = json.load(open(p))

    heldout = select_heldout(rows, packets, n, gates["eval"]["seed"])
    print(f"Held-out: {len(heldout)} frames")

    dino_ref = DinoReference.load(resolve_path(gates["paths"]["dino_index"]))
    calib_path = resolve_path(gates["paths"]["season_calibration"])
    calibration = json.load(open(calib_path)) if calib_path.exists() else None

    canonical = Image.open(canonical_frame_path(dream_cfg)).convert("RGB")
    engine = DreamEngine(dream_cfg)
    print(f"Device: {engine.device}")

    id_cfg = gates["identity_collapse"]
    dino_model = gates["models"]["dino"]

    eval_dir = resolve_path(gates["paths"]["eval_dir"])
    eval_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, r in enumerate(heldout):
        fn = r["filename"]
        pkt = enrich_packet(dict(packets[fn]))
        real = Image.open(raw_dir / fn).convert("RGB")

        result = engine.generate(pkt, dial=dial, seed=seed, exclude_anchors={fn})
        gen = result.image

        emb = embed_image(gen, dino_model)
        dino_dist, nearest = dino_ref.knn_distance(
            emb, k=int(id_cfg.get("knn", 3)), exclude={fn}
        )
        hd = horizon_displacement(gen, canonical)
        scores = IdentityScores(dino_dist, hd, nearest)
        collapse = collapse_verdict(scores, dial, id_cfg)

        season_scores = classify_season(gen, gates, calibration=calibration)
        sv = season_verdict(season_scores, pkt["month"], gates["season_lock"])

        clip_sim = clip_similarity(gen, real)
        lp = lpips_distance(gen, real, gates["models"]["lpips_net"])

        rec = {
            "filename": fn,
            "prompt": result.sidecar["prompt"],
            "anchor_frame": result.sidecar["anchor_frame"],
            "anchor_distance": result.sidecar["anchor_distance"],
            "identity": collapse,
            "season": sv.as_dict(),
            "clip_similarity": clip_sim,
            "lpips": lp,
        }
        results.append(rec)

        # per-frame image + sidecar
        stem = f"eval_{expected_coarse_season(pkt['month'])}_{Path(fn).stem}"
        gen.save(eval_dir / f"{stem}.JPG", "JPEG", quality=95, subsampling=0)
        merged = dict(result.sidecar)
        merged["eval"] = rec
        json.dump(merged, open(eval_dir / f"{stem}.json", "w"), indent=2)

        print(
            f"  [{i + 1}/{len(heldout)}] {fn[:32]} "
            f"dino={dino_dist:.3f} horiz={hd:.3f} "
            f"season={sv.action}({sv.predicted}/{sv.expected}) "
            f"clip={clip_sim:.3f} lpips={lp:.3f} -> {collapse['action']}"
        )

    report = build_report(results, gates, seed, dial)
    json.dump(report, open(eval_dir / "baseline.json", "w"), indent=2)
    (eval_dir / "baseline.md").write_text(render_markdown(report))
    print(f"\nReport → {eval_dir / 'baseline.md'}")
    print(render_markdown(report))
    return 0


def _agg(vals):
    vals = [v for v in vals if v == v]  # drop NaN
    if not vals:
        return {"mean": None, "min": None, "max": None}
    return {
        "mean": round(statistics.fmean(vals), 4),
        "min": round(min(vals), 4),
        "max": round(max(vals), 4),
    }


def build_report(results, gates, seed, dial):
    return {
        "n": len(results),
        "seed": seed,
        "dial": dial,
        "config": {
            "identity_collapse": gates["identity_collapse"],
            "season_lock": gates["season_lock"],
            "eval": gates["eval"],
        },
        "aggregates": {
            "dino_distance": _agg([r["identity"]["scores"]["dino_distance"] for r in results]),
            "horizon_displacement": _agg(
                [r["identity"]["scores"]["horizon_displacement"] for r in results]
            ),
            "clip_similarity": _agg([r["clip_similarity"] for r in results]),
            "lpips": _agg([r["lpips"] for r in results]),
        },
        "counts": {
            "collapse_actions": _count([r["identity"]["action"] for r in results]),
            "season_actions": _count([r["season"]["action"] for r in results]),
        },
        "frames": results,
    }


def _count(items):
    c = defaultdict(int)
    for it in items:
        c[it] += 1
    return dict(c)


def render_markdown(report) -> str:
    a = report["aggregates"]
    lines = [
        f"# Dial-{report['dial']:g} eval baseline (n={report['n']}, seed={report['seed']})",
        "",
        "## Aggregates",
        "",
        "| metric | mean | min | max |",
        "|---|---|---|---|",
    ]
    for k in ("dino_distance", "horizon_displacement", "clip_similarity", "lpips"):
        m = a[k]
        lines.append(f"| {k} | {m['mean']} | {m['min']} | {m['max']} |")
    lines += [
        "",
        f"**Collapse actions:** {report['counts']['collapse_actions']}",
        "",
        f"**Season actions:** {report['counts']['season_actions']}",
        "",
        "## Per-frame",
        "",
        "| frame | dino | horizon | season | clip | lpips | action |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in report["frames"]:
        s = r["identity"]["scores"]
        lines.append(
            f"| {r['filename'][:28]} | {s['dino_distance']:.3f} | "
            f"{s['horizon_displacement']:.3f} | "
            f"{r['season']['action']}({r['season']['predicted']}) | "
            f"{r['clip_similarity']:.3f} | {r['lpips']:.3f} | {r['identity']['action']} |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
