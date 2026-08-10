"""Dreamberry dream engine — SDXL + ControlNet + real-frame anchor.

The dead Cloudberry camera dreaming: a weather-nearest real frame is the img2img
init, ControlNet (depth + soft-edge) from the canonical geometry frame locks the
rocks/horizon/cabin-edge, IP-Adapter carries atmosphere, and the dream dial (0-10)
controls how hard the ghost is allowed to drift off the rocks.
"""

from dream.dial import (
    DIAL_MIN,
    DIAL_MAX,
    DialParams,
    NightLightingConfig,
    dial_schedule,
    resolve_generation_params,
)

__all__ = [
    "DialParams",
    "NightLightingConfig",
    "dial_schedule",
    "resolve_generation_params",
    "DIAL_MIN",
    "DIAL_MAX",
]
