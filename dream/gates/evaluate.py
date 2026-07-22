"""Per-frame gate evaluation for the hourly path.

Combines the two M3 validators — identity collapse (DINOv2 kNN + horizon
displacement, dial-aware) and season lock (calibrated CLIP zero-shot) — into a
single accept/retry decision plus the validator_scores block that goes into the
provenance sidecar.

The decision itself (`frame_decision`) is pure and unit-tested; `evaluate_frame`
wraps it with the (lazy, heavy) model calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from dream.gates.embed import DinoReference, embed_image
from dream.gates.horizon import horizon_displacement
from dream.gates.identity import IdentityScores, collapse_verdict
from dream.gates.season import classify_season, season_verdict

__all__ = ["FrameEvaluation", "frame_decision", "evaluate_frame"]


@dataclass(frozen=True)
class FrameEvaluation:
    """Outcome of gating one candidate frame."""

    accept: bool
    reject_reason: str | None  # "identity_collapse" | "season_lock" | None
    failure_mode: str | None  # "identity_collapse" (honored dissolve) | None
    validator_scores: dict[str, Any]


def frame_decision(
    collapse_action: str,
    season_action: str,
) -> tuple[bool, str | None, str | None]:
    """Map the two dial-aware verdicts to (accept, reject_reason, failure_mode).

    Season lock is a hard ethic: a warm-in-cold hallucination ("refuse") always
    blocks publish, at any dial (no summer-green February — DREAMBERRY.md §6).

    Identity collapse is dial-aware (from `collapse_verdict`):
      - "pass"             → accept, clean frame.
      - "honored_dissolve" → accept; the dial is high enough that collapse is the
        intended truest state, so it is published and *updates the pointer*
        (DREAMBERRY.md line 250), tagged failure_mode="identity_collapse".
      - "regen_or_hold"    → reject; at low dial the window must hold, so the
        caller retries with a fresh seed and, if exhausted, holds the last good
        frame (DREAMBERRY.md line 113 "regeneration/hold").
    """
    if season_action == "refuse":
        return False, "season_lock", None
    if collapse_action == "pass":
        return True, None, None
    if collapse_action == "honored_dissolve":
        return True, None, "identity_collapse"
    return False, "identity_collapse", None


def evaluate_frame(
    image,
    pkt: Mapping[str, Any],
    dial: float,
    gates_cfg: Mapping[str, Any],
    *,
    dino_ref: DinoReference,
    canonical,
    calibration: Mapping[str, float] | None = None,
    exclude: set[str] | None = None,
) -> FrameEvaluation:
    """Run both gates on a candidate frame and decide accept/retry."""
    id_cfg = gates_cfg["identity_collapse"]

    emb = embed_image(image, gates_cfg["models"]["dino"])
    dino_dist, nearest = dino_ref.knn_distance(
        emb, k=int(id_cfg.get("knn", 3)), exclude=exclude
    )
    hd = horizon_displacement(image, canonical)
    scores = IdentityScores(dino_dist, hd, nearest)
    collapse = collapse_verdict(scores, dial, id_cfg)

    season_scores = classify_season(image, gates_cfg, calibration=calibration)
    sv = season_verdict(season_scores, int(pkt["month"]), gates_cfg["season_lock"])

    accept, reject_reason, failure_mode = frame_decision(collapse["action"], sv.action)

    validator_scores = {
        "dino_distance": scores.dino_distance,
        "horizon_displacement": scores.horizon_displacement,
        "nearest_real": scores.nearest_real,
        "collapse": collapse,
        "season": sv.as_dict(),
    }
    return FrameEvaluation(
        accept=accept,
        reject_reason=reject_reason,
        failure_mode=failure_mode,
        validator_scores=validator_scores,
    )
