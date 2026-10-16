"""Weather-nearest real-frame anchor selection (brief §3, step 1).

A real morning underlies every dream: the weather-NN index picks a same-season,
same-day/night Cloudberry frame matching the packet, used as the img2img init AND
the IP-Adapter atmosphere source. Falls back to the canonical frame if no index /
no match on the day side.

Twilight honesty (#27): night/low-sun queries reject auto-exposed bright anchors
by mean luminance, prefer the same USNO solar band, and never fall back to the
bright day canonical when the packet is night-side.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from dream.config import load_dataset_config, resolve_path
from weather_schema.retrieve import (
    DEFAULT_NIGHT_SOLAR_ELEVATION_DEG,
    is_night_elevation,
)
from weather_schema.solar_bands import solar_band

# Defaults mirrored in config/dream.yaml:anchor_honesty (issue #27).
DEFAULT_MAX_MEAN_LUMINANCE = 110.0
DEFAULT_LUMINANCE_GATE_SOLAR_ELEVATION_DEG = -4.0
DEFAULT_QUERY_K = 20


@dataclass(frozen=True)
class AnchorHonestyConfig:
    enabled: bool = True
    solar_band_filter: bool = True
    luminance_gate: bool = True
    luminance_gate_solar_elevation_deg: float = DEFAULT_LUMINANCE_GATE_SOLAR_ELEVATION_DEG
    max_mean_luminance: float = DEFAULT_MAX_MEAN_LUMINANCE
    query_k: int = DEFAULT_QUERY_K
    relax_luminance_if_empty: bool = True


def anchor_honesty_from_mapping(data: Mapping[str, Any] | None) -> AnchorHonestyConfig:
    if not data:
        return AnchorHonestyConfig()
    return AnchorHonestyConfig(
        enabled=bool(data.get("enabled", True)),
        solar_band_filter=bool(data.get("solar_band_filter", True)),
        luminance_gate=bool(data.get("luminance_gate", True)),
        luminance_gate_solar_elevation_deg=float(
            data.get(
                "luminance_gate_solar_elevation_deg",
                DEFAULT_LUMINANCE_GATE_SOLAR_ELEVATION_DEG,
            )
        ),
        max_mean_luminance=float(
            data.get("max_mean_luminance", DEFAULT_MAX_MEAN_LUMINANCE)
        ),
        query_k=int(data.get("query_k", DEFAULT_QUERY_K)),
        relax_luminance_if_empty=bool(data.get("relax_luminance_if_empty", True)),
    )


@dataclass(frozen=True)
class Anchor:
    filename: str
    path: Path
    distance: float | None
    source: str  # "weather_nn" | "weather_nn_relaxed" | "canonical_fallback"
    mean_luminance: float | None = None
    reject_reasons: tuple[dict[str, Any], ...] = field(default_factory=tuple)


class NoHonestNightAnchorError(RuntimeError):
    """Night-side packet has no usable dark archive frame (do not use day canonical)."""

    def __init__(
        self,
        message: str,
        *,
        reject_reasons: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.reject_reasons = list(reject_reasons or [])


def _raw_dir(dream_cfg: dict[str, Any]) -> Path:
    ds = load_dataset_config(dream_cfg)
    return resolve_path(ds["paths"]["raw_dir"])


def _canonical(dream_cfg: dict[str, Any]) -> tuple[str, Path]:
    ds = load_dataset_config(dream_cfg)
    fn = ds["canonical_frame"]
    return fn, _raw_dir(dream_cfg) / fn


def _mean_luminance(path: Path) -> float:
    from PIL import Image, ImageStat

    with Image.open(path) as im:
        return float(ImageStat.Stat(im.convert("L")).mean[0])


def _query_elev(pkt: Mapping[str, Any]) -> float | None:
    raw = pkt.get("solar_elevation")
    return None if raw is None else float(raw)


def select_anchor(
    pkt: Mapping[str, Any],
    dream_cfg: dict[str, Any],
    *,
    exclude: set[str] | None = None,
    honesty: AnchorHonestyConfig | None = None,
) -> Anchor:
    """Pick the weather-nearest same-season archive frame for `pkt`.

    `exclude` drops candidate filenames (leave-one-out for held-out eval).
    """
    cfg = honesty if honesty is not None else anchor_honesty_from_mapping(
        dream_cfg.get("anchor_honesty")
    )
    ds = load_dataset_config(dream_cfg)
    raw_dir = _raw_dir(dream_cfg)
    index_path = resolve_path(ds["paths"]["weather_nn_index"])
    elev = _query_elev(pkt)
    night_side = elev is not None and is_night_elevation(
        elev, night_solar_elevation_deg=DEFAULT_NIGHT_SOLAR_ELEVATION_DEG
    )
    rejects: list[dict[str, Any]] = []

    if index_path.exists():
        from weather_schema.retrieve import WeatherNNIndex

        index = WeatherNNIndex.load(index_path)
        if cfg.enabled:
            index.solar_band_filter = cfg.solar_band_filter
        k = max(5, cfg.query_k if cfg.enabled else 5)
        hits = index.query(pkt, k=k, exclude=exclude)

        passing: list[tuple[dict[str, Any], Path, float]] = []
        dark_fallback: list[tuple[dict[str, Any], Path, float]] = []

        for hit in hits:
            candidate = raw_dir / hit["filename"]
            if not candidate.exists():
                rejects.append(
                    {
                        "filename": hit["filename"],
                        "reason": "missing_file",
                        "distance": float(hit["distance"]),
                    }
                )
                continue
            try:
                luma = _mean_luminance(candidate)
            except Exception as exc:  # noqa: BLE001 — skip unreadable; keep hour alive
                rejects.append(
                    {
                        "filename": hit["filename"],
                        "reason": "luminance_read_failed",
                        "detail": f"{type(exc).__name__}: {exc}",
                        "distance": float(hit["distance"]),
                    }
                )
                continue

            dark_fallback.append((hit, candidate, luma))
            gate_active = (
                cfg.enabled
                and cfg.luminance_gate
                and elev is not None
                and elev < cfg.luminance_gate_solar_elevation_deg
            )
            if gate_active and luma > cfg.max_mean_luminance:
                rejects.append(
                    {
                        "filename": hit["filename"],
                        "reason": "luminance_too_high",
                        "mean_luminance": round(luma, 3),
                        "max_mean_luminance": cfg.max_mean_luminance,
                        "solar_elevation": hit.get("solar_elevation"),
                        "solar_band": hit.get("solar_band")
                        or (
                            solar_band(float(hit["solar_elevation"]))
                            if hit.get("solar_elevation") is not None
                            else None
                        ),
                        "distance": float(hit["distance"]),
                    }
                )
                continue
            passing.append((hit, candidate, luma))

        if passing:
            hit, path, luma = passing[0]
            return Anchor(
                filename=hit["filename"],
                path=path,
                distance=float(hit["distance"]),
                source="weather_nn",
                mean_luminance=round(luma, 3),
                reject_reasons=tuple(rejects),
            )

        if (
            cfg.enabled
            and cfg.relax_luminance_if_empty
            and dark_fallback
            and elev is not None
            and elev < cfg.luminance_gate_solar_elevation_deg
        ):
            # Best-effort: darkest remaining same-class hit (never day canonical).
            dark_fallback.sort(key=lambda item: (item[2], item[0]["distance"]))
            hit, path, luma = dark_fallback[0]
            rejects.append(
                {
                    "filename": hit["filename"],
                    "reason": "luminance_relaxed",
                    "mean_luminance": round(luma, 3),
                    "max_mean_luminance": cfg.max_mean_luminance,
                    "distance": float(hit["distance"]),
                }
            )
            return Anchor(
                filename=hit["filename"],
                path=path,
                distance=float(hit["distance"]),
                source="weather_nn_relaxed",
                mean_luminance=round(luma, 3),
                reject_reasons=tuple(rejects),
            )

        if night_side:
            raise NoHonestNightAnchorError(
                "no honest night/twilight archive anchor after luminance/band gates",
                reject_reasons=rejects,
            )

    if night_side:
        raise NoHonestNightAnchorError(
            "no weather-NN night/twilight anchor available (refusing day canonical)",
            reject_reasons=rejects,
        )

    fn, path = _canonical(dream_cfg)
    luma = None
    if path.exists():
        try:
            luma = round(_mean_luminance(path), 3)
        except Exception:  # noqa: BLE001
            luma = None
    return Anchor(
        filename=fn,
        path=path,
        distance=None,
        source="canonical_fallback",
        mean_luminance=luma,
        reject_reasons=tuple(rejects),
    )
