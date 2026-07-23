#!/usr/bin/env python3
"""Private native-resolution night comparison for DREAM033.

This experiment never publishes to current/ or archive/. It compares:
baseline, a same-season solar-mismatch parameter override, and a cross-season
deep-night anchor selected outside the production retrieval API.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

import requests
import yaml
from PIL import Image, ImageStat

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dream.anchor import Anchor, select_anchor  # noqa: E402
from dream.config import (  # noqa: E402
    load_dataset_config,
    load_dream_config,
    resolve_path,
)
from dream.dial import DialParams, dial_schedule  # noqa: E402
from dream.hourly import _default_evaluator  # noqa: E402
from dream.pipeline import DreamEngine  # noqa: E402
from dream.sidecar import write_sidecar  # noqa: E402
from weather_schema.buckets import season_token  # noqa: E402
from weather_schema.retrieve import IndexEntry, WeatherNNIndex  # noqa: E402
from weather_schema.vector import feature_vector, weighted_distance  # noqa: E402

DREAM_ID = "2026-07-23T02:30:00Z_DREAM033"
SIDECAR_URL = f"https://dreamberry.adamsimms.xyz/archive/{DREAM_ID}.json"
DEFAULT_OUTPUT_DIR = Path("data/dream/night_ab")
FORBIDDEN_CROSS_SEASON_TOKENS = ("snow", "frozen", "frost")
MAX_CROSS_SEASON_LUMINANCE = 30.0


def fetch_packet(url: str = SIDECAR_URL) -> dict[str, Any]:
    """Fetch the immutable archived packet used by DREAM033."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    sidecar = response.json()
    return dict(sidecar["weather_packet"])


def solar_mismatch_params() -> DialParams:
    """Requested dial 0 with explicit effective parameters for approach 1."""
    return replace(
        dial_schedule(0.0),
        denoise_strength=0.70,
        controlnet_scale=0.50,
        ip_adapter_scale=0.25,
    )


def select_cross_season_night(
    index: WeatherNNIndex,
    pkt: Mapping[str, Any],
    raw_dir: Path,
    *,
    max_luminance: float = MAX_CROSS_SEASON_LUMINANCE,
) -> tuple[IndexEntry, float]:
    """Pick the nearest non-summer astronomical-night anchor for the private A/B.

    Production retrieval remains untouched. Winter-coded captions are excluded
    so this tests borrowed darkness without knowingly importing snow or frost.
    """
    query_values, _ = feature_vector(pkt, theta_shore_deg=index.theta_shore_deg)
    candidates: list[tuple[float, IndexEntry]] = []

    for entry in index.entries:
        if season_token(entry.month) == "summer":
            continue
        if entry.solar_elevation is None or entry.solar_elevation >= -18.0:
            continue
        prompt = (entry.prompt or "").lower()
        if any(token in prompt for token in FORBIDDEN_CROSS_SEASON_TOKENS):
            continue
        path = raw_dir / entry.filename
        if not path.exists():
            continue
        luminance = float(ImageStat.Stat(Image.open(path).convert("L")).mean[0])
        if luminance > max_luminance:
            continue
        distance = weighted_distance(query_values, entry.feature_vector, index.weights)
        candidates.append((distance, entry))

    if not candidates:
        raise RuntimeError("no snow-free cross-season deep-night anchor available")

    candidates.sort(key=lambda item: (item[0], item[1].filename))
    distance, entry = candidates[0]
    return entry, float(distance)


def _entry_for(index: WeatherNNIndex, filename: str) -> IndexEntry:
    for entry in index.entries:
        if entry.filename == filename:
            return entry
    raise KeyError(f"anchor missing from weather-NN index: {filename}")


def _anchor_for(
    entry: IndexEntry,
    distance: float,
    raw_dir: Path,
    *,
    source: str,
) -> Anchor:
    path = raw_dir / entry.filename
    if not path.exists():
        raise FileNotFoundError(path)
    return Anchor(
        filename=entry.filename,
        path=path,
        distance=distance,
        source=source,
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


def run_experiment(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    packet_url: str = SIDECAR_URL,
) -> dict[str, Any]:
    """Generate and gate all three variants without publishing."""
    pkt = fetch_packet(packet_url)
    dream_cfg = load_dream_config()
    dataset_cfg = load_dataset_config(dream_cfg)
    gates_cfg = _load_yaml(resolve_path("config/gates.yaml"))
    raw_dir = resolve_path(dataset_cfg["paths"]["raw_dir"])
    index = WeatherNNIndex.load(resolve_path(dataset_cfg["paths"]["weather_nn_index"]))

    baseline_anchor = select_anchor(pkt, dream_cfg)
    baseline_entry = _entry_for(index, baseline_anchor.filename)
    cross_entry, cross_distance = select_cross_season_night(index, pkt, raw_dir)
    cross_anchor = _anchor_for(
        cross_entry,
        cross_distance,
        raw_dir,
        source="weather_nn_cross_season_experiment",
    )

    baseline_params = dial_schedule(0.0)
    variants = (
        ("baseline", baseline_anchor, baseline_entry, baseline_params),
        (
            "dial_override",
            baseline_anchor,
            baseline_entry,
            solar_mismatch_params(),
        ),
        ("cross_season", cross_anchor, cross_entry, baseline_params),
    )

    output_dir = resolve_path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    engine = DreamEngine(dream_cfg)
    evaluator = _default_evaluator(gates_cfg, dream_cfg)
    summary: dict[str, Any] = {"dream_id": DREAM_ID, "variants": {}}

    for name, anchor, entry, params in variants:
        result = engine.generate(
            pkt,
            dial=0.0,
            params_override=params,
            seed=0,
            anchor=anchor,
        )
        evaluation = evaluator(result.image, pkt, 0.0)
        luminance = float(ImageStat.Stat(result.image.convert("L")).mean[0])

        experiment = {
            "variant": name,
            "requested_dial": 0.0,
            "effective_params": params.as_dict(),
            "query_solar_elevation": float(pkt["solar_elevation"]),
            "anchor_solar_elevation": entry.solar_elevation,
            "anchor_month": entry.month,
            "anchor_season": season_token(entry.month),
            "anchor_caption": entry.prompt,
            "anchor_mean_luminance": round(
                float(ImageStat.Stat(Image.open(anchor.path).convert("L")).mean[0]),
                3,
            ),
            "mean_luminance": round(luminance, 3),
            "would_publish": evaluation.accept,
            "reject_reason": evaluation.reject_reason,
        }
        sidecar = dict(result.sidecar)
        sidecar["validator_scores"] = evaluation.validator_scores
        sidecar["failure_mode"] = evaluation.failure_mode
        sidecar["experiment"] = experiment

        stem = f"DREAM033_{name}"
        result.image.save(output_dir / f"{stem}.png", "PNG")
        write_sidecar(output_dir / f"{stem}.json", sidecar)
        summary["variants"][name] = {
            "image": f"{stem}.png",
            "sidecar": f"{stem}.json",
            "anchor": anchor.filename,
            **experiment,
            "validator_scores": evaluation.validator_scores,
        }

    with open(output_dir / "DREAM033_summary.json", "w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-url", default=SIDECAR_URL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--select-only",
        action="store_true",
        help="Print candidate anchors without loading diffusion models",
    )
    args = parser.parse_args()

    if args.select_only:
        pkt = fetch_packet(args.packet_url)
        dream_cfg = load_dream_config()
        dataset_cfg = load_dataset_config(dream_cfg)
        index = WeatherNNIndex.load(
            resolve_path(dataset_cfg["paths"]["weather_nn_index"])
        )
        raw_dir = resolve_path(dataset_cfg["paths"]["raw_dir"])
        baseline = select_anchor(pkt, dream_cfg)
        cross, distance = select_cross_season_night(index, pkt, raw_dir)
        print(
            json.dumps(
                {
                    "baseline": baseline.filename,
                    "cross_season": cross.filename,
                    "cross_season_distance": distance,
                    "cross_season_elevation": cross.solar_elevation,
                    "cross_season_prompt": cross.prompt,
                },
                indent=2,
            )
        )
        return 0

    print(json.dumps(run_experiment(output_dir=args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
