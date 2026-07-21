"""Identity-collapse detector + dial-aware verdict (issue #9).

Collapse = the ghost cannot grip the rocks. Measured two ways:
  1. DINOv2 kNN distance to the real-frame distribution (dream/gates/embed.py)
  2. horizon-line displacement vs the canonical frame (dream/gates/horizon.py)

Dial-aware verdict (DREAMBERRY.md §Primary — Identity collapse):
  - below `enforced_below_dial`: the window must hold. A collapse → action
    "regen_or_hold" (the caller regenerates with a new seed or holds the last
    good frame). This is the honest refusal, never a false sharp place.
  - at/above that dial: collapse is *expected and honored* — action
    "honored_dissolve" (the seeded defocus in dream/dial.py renders it).

The dissolve renderer itself already lives in dream/dial.py; this module only
detects and decides.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from dream.gates.horizon import horizon_displacement

__all__ = ["IdentityScores", "collapse_verdict", "horizon_displacement"]


@dataclass(frozen=True)
class IdentityScores:
    dino_distance: float
    horizon_displacement: float
    nearest_real: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _collapsed(scores: IdentityScores, cfg: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    dd = float(cfg.get("dino_distance_fail", 0.45))
    hd = float(cfg.get("horizon_displacement_fail", 0.06))
    if scores.dino_distance == scores.dino_distance and scores.dino_distance > dd:
        reasons.append(f"dino_distance {scores.dino_distance:.3f} > {dd}")
    if scores.horizon_displacement > hd:
        reasons.append(
            f"horizon_displacement {scores.horizon_displacement:.3f} > {hd}"
        )
    return (len(reasons) > 0), reasons


def collapse_verdict(
    scores: IdentityScores,
    dial: float,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """Dial-aware collapse decision.

    Returns {collapsed, action, reasons, enforced}. `action` is one of
    "pass", "regen_or_hold", "honored_dissolve".
    """
    enforced_below = float(cfg.get("enforced_below_dial", 3.0))
    enforced = float(dial) < enforced_below
    collapsed, reasons = _collapsed(scores, cfg)

    if not collapsed:
        action = "pass"
    elif enforced:
        action = "regen_or_hold"
    else:
        action = "honored_dissolve"

    return {
        "collapsed": collapsed,
        "action": action,
        "reasons": reasons,
        "enforced": enforced,
        "scores": scores.as_dict(),
    }
