"""Dreamberry M2 dream engine — SDXL + ControlNet + real-frame anchor.

The dead Cloudberry camera dreaming: a weather-nearest real frame is the img2img
init, ControlNet (depth + soft-edge) from the canonical geometry frame locks the
rocks/horizon/cabin-edge, IP-Adapter carries atmosphere, and the dream dial (0-10)
controls how hard the ghost is allowed to drift off the rocks.
"""

from dream.dial import DIAL_MIN, DIAL_MAX, DialParams, dial_schedule

__all__ = ["DialParams", "dial_schedule", "DIAL_MIN", "DIAL_MAX"]
