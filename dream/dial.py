"""Dream dial (0–10) parameter schedule — DREAMBERRY.md §6.

Piecewise-linear anchors for denoise / ControlNet / IP-Adapter / LoRA.
Dial 10 adds seeded structure-weighted defocus. Tune during dial experiments.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

DIAL_MIN = 0.0
DIAL_MAX = 10.0

# Public launch default (locked, M6): artist-only, dial = 0.
DEFAULT_DIAL = 0.0

# (dial, img2img_denoise, controlnet_scale, ip_adapter_scale, lora_scale)
# Straight from §6. LoRA is the mid-dial identity *reservoir*, not the geometry
# lock — its weight rises with the dial. Until a LoRA is trained (follow-on),
# callers pass has_lora=False and lora_scale is reported but not applied.
_ANCHORS: tuple[tuple[float, float, float, float, float], ...] = (
    (0.0, 0.35, 0.90, 0.70, 0.20),
    (2.0, 0.50, 0.75, 0.60, 0.40),
    (5.0, 0.70, 0.50, 0.40, 0.60),
    (8.0, 0.85, 0.30, 0.20, 0.80),
    (10.0, 0.95, 0.10, 0.05, 1.00),
)

# Deliberate seeded defocus (§5/§6): dissolve is honored, not emergent. Ramps
# from 0 at dial 8 ("identity strains") to full at dial 10 ("dissolves").
_DEFOCUS_START = 8.0
_DEFOCUS_FULL = 10.0


@dataclass(frozen=True)
class DialParams:
    """Resolved generation parameters for a given dial position."""

    dial: float
    denoise_strength: float
    controlnet_scale: float
    ip_adapter_scale: float
    lora_scale: float
    defocus_strength: float

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _interp(dial: float, idx: int) -> float:
    """Piecewise-linear interpolation of anchor field `idx` (1-based into tuple)."""
    if dial <= _ANCHORS[0][0]:
        return _ANCHORS[0][idx]
    if dial >= _ANCHORS[-1][0]:
        return _ANCHORS[-1][idx]
    for i in range(len(_ANCHORS) - 1):
        d0 = _ANCHORS[i][0]
        d1 = _ANCHORS[i + 1][0]
        if d0 <= dial <= d1:
            t = (dial - d0) / (d1 - d0)
            return _ANCHORS[i][idx] + t * (_ANCHORS[i + 1][idx] - _ANCHORS[i][idx])
    return _ANCHORS[-1][idx]  # unreachable


def _defocus(dial: float) -> float:
    if dial <= _DEFOCUS_START:
        return 0.0
    if dial >= _DEFOCUS_FULL:
        return 1.0
    return (dial - _DEFOCUS_START) / (_DEFOCUS_FULL - _DEFOCUS_START)


def dial_schedule(dial: float = DEFAULT_DIAL) -> DialParams:
    """Resolve dream-dial parameters for `dial` in [0, 10] (clamped)."""
    d = _clamp(float(dial), DIAL_MIN, DIAL_MAX)
    return DialParams(
        dial=d,
        denoise_strength=round(_interp(d, 1), 4),
        controlnet_scale=round(_interp(d, 2), 4),
        ip_adapter_scale=round(_interp(d, 3), 4),
        lora_scale=round(_interp(d, 4), 4),
        defocus_strength=round(_defocus(d), 4),
    )
