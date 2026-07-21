"""Dreamberry M3 quality gates (issues #9-#11).

Two failure modes made concrete (DREAMBERRY.md §Validators):
  - identity collapse: DINOv2 kNN distance + horizon-edge stability, dial-aware
  - season lock: hard same-season retrieval (M1) + calibrated CLIP zero-shot

Plus an offline eval harness (CLIP / LPIPS / horizon stability) for the dial-0
baseline. Heavy models (DINOv2, CLIP, LPIPS) are imported lazily so the pure
logic here stays unit-testable without downloads.
"""

from dream.gates.evaluate import FrameEvaluation, evaluate_frame, frame_decision
from dream.gates.identity import (
    IdentityScores,
    collapse_verdict,
    horizon_displacement,
)
from dream.gates.season import SeasonVerdict, season_verdict

__all__ = [
    "IdentityScores",
    "collapse_verdict",
    "horizon_displacement",
    "SeasonVerdict",
    "season_verdict",
    "FrameEvaluation",
    "evaluate_frame",
    "frame_decision",
]
