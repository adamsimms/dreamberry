"""Identity-collapse detector + dial-aware verdict.

See DREAMBERRY.md §7. DINOv2 kNN + horizon displacement → `collapse_verdict`
(`regen_or_hold` below the enforced dial; `honored_dissolve` at/above it).
Dissolve rendering lives in dream/dial.py.
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
