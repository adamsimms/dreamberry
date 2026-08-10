"""Dream dial (0–10) parameter schedule — DREAMBERRY.md §6.

Piecewise-linear anchors for denoise / ControlNet / IP-Adapter / LoRA.
Dial 10 adds seeded structure-weighted defocus. Tune during dial experiments.

Night lighting (brief §6 data-driven solar): when solar elevation is below the
night-bucket threshold, dial-0 lock params are nudged darker so the prompt token
`night` is not overpowered by bright auto-exposed anchors + daytime ControlNet.
Public `dial` stays artist-set; only effective scales change.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Mapping

DIAL_MIN = 0.0
DIAL_MAX = 10.0

# Public launch default (locked, M6): artist-only, dial = 0.
DEFAULT_DIAL = 0.0

# Same boundary as curation / weather-NN night gate (civil twilight end, USNO).
DEFAULT_NIGHT_SOLAR_ELEVATION_DEG = -6.0

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


@dataclass(frozen=True)
class NightLightingConfig:
    """Solar-driven darkening overlay (DREAM033 A/B → production)."""

    enabled: bool = True
    solar_elevation_deg: float = DEFAULT_NIGHT_SOLAR_ELEVATION_DEG
    denoise_strength: float = 0.70
    controlnet_scale: float = 0.50
    ip_adapter_scale: float = 0.25
    defocus_strength: float = 0.0


DEFAULT_NIGHT_LIGHTING = NightLightingConfig()


def night_lighting_config_from_mapping(
    data: Mapping[str, Any] | None,
) -> NightLightingConfig:
    """Build night-lighting config from `config/dream.yaml:night_lighting`."""
    if not data:
        return DEFAULT_NIGHT_LIGHTING
    base = DEFAULT_NIGHT_LIGHTING
    return NightLightingConfig(
        enabled=bool(data.get("enabled", base.enabled)),
        solar_elevation_deg=float(
            data.get("solar_elevation_deg", base.solar_elevation_deg)
        ),
        denoise_strength=float(data.get("denoise_strength", base.denoise_strength)),
        controlnet_scale=float(data.get("controlnet_scale", base.controlnet_scale)),
        ip_adapter_scale=float(data.get("ip_adapter_scale", base.ip_adapter_scale)),
        defocus_strength=float(data.get("defocus_strength", base.defocus_strength)),
    )


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


def apply_night_lighting(
    params: DialParams,
    pkt: Mapping[str, Any] | None,
    *,
    night: NightLightingConfig | None = None,
) -> DialParams:
    """Nudge params darker when the packet is in the night bucket.

    Merge rule (so high dial stays freer than night-at-dial-0): take the more
    aggressive of dial schedule vs night overlay — higher denoise/defocus, lower
    ControlNet/IP. Public `dial` is unchanged.
    """
    cfg = DEFAULT_NIGHT_LIGHTING if night is None else night
    if not cfg.enabled or pkt is None:
        return params
    elev = pkt.get("solar_elevation")
    if elev is None or float(elev) >= cfg.solar_elevation_deg:
        return params
    return replace(
        params,
        denoise_strength=round(max(params.denoise_strength, cfg.denoise_strength), 4),
        controlnet_scale=round(min(params.controlnet_scale, cfg.controlnet_scale), 4),
        ip_adapter_scale=round(min(params.ip_adapter_scale, cfg.ip_adapter_scale), 4),
        defocus_strength=round(max(params.defocus_strength, cfg.defocus_strength), 4),
    )


def resolve_generation_params(
    dial: float = DEFAULT_DIAL,
    pkt: Mapping[str, Any] | None = None,
    *,
    night: NightLightingConfig | None = None,
) -> DialParams:
    """Dial schedule plus optional solar-driven night darkening."""
    return apply_night_lighting(dial_schedule(dial), pkt, night=night)
