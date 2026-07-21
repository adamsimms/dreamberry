"""Weather-nearest real-frame anchor selection (brief §3, step 1).

A real morning underlies every dream: the weather-NN index picks a same-season
Cloudberry frame matching the packet, used as the img2img init AND the IP-Adapter
atmosphere source. Falls back to the canonical frame if no index / no match.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from dream.config import load_dataset_config, resolve_path


@dataclass(frozen=True)
class Anchor:
    filename: str
    path: Path
    distance: float | None
    source: str  # "weather_nn" | "canonical_fallback"


def _raw_dir(dream_cfg: dict[str, Any]) -> Path:
    ds = load_dataset_config(dream_cfg)
    return resolve_path(ds["paths"]["raw_dir"])


def _canonical(dream_cfg: dict[str, Any]) -> tuple[str, Path]:
    ds = load_dataset_config(dream_cfg)
    fn = ds["canonical_frame"]
    return fn, _raw_dir(dream_cfg) / fn


def select_anchor(
    pkt: Mapping[str, Any],
    dream_cfg: dict[str, Any],
) -> Anchor:
    """Pick the weather-nearest same-season archive frame for `pkt`."""
    ds = load_dataset_config(dream_cfg)
    raw_dir = _raw_dir(dream_cfg)
    index_path = resolve_path(ds["paths"]["weather_nn_index"])

    if index_path.exists():
        from weather_schema.retrieve import WeatherNNIndex

        index = WeatherNNIndex.load(index_path)
        hits = index.query(pkt, k=5)
        for hit in hits:
            candidate = raw_dir / hit["filename"]
            if candidate.exists():
                return Anchor(
                    filename=hit["filename"],
                    path=candidate,
                    distance=float(hit["distance"]),
                    source="weather_nn",
                )

    fn, path = _canonical(dream_cfg)
    return Anchor(filename=fn, path=path, distance=None, source="canonical_fallback")
