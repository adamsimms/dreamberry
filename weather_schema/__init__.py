"""Deterministic weather → prompt + feature vector (Dreamberry M1).

Symmetry contract: the same compose_prompt / feature_vector run on ERA5 archive
packets (captioning) and live forecast packets (inference).
"""

from weather_schema.compose import TRIGGER, compose_prompt, normalize_packet
from weather_schema.retrieve import WeatherNNIndex
from weather_schema.vocabulary import CLOSED_VOCABULARY
from weather_schema.vector import feature_vector, precip_class, season_family, weighted_distance

__all__ = [
    "TRIGGER",
    "CLOSED_VOCABULARY",
    "WeatherNNIndex",
    "compose_prompt",
    "normalize_packet",
    "feature_vector",
    "precip_class",
    "season_family",
    "weighted_distance",
]
