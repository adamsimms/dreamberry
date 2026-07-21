"""Provenance sidecar schema for Dreamberry generations (M4 / issue #15).

Every generated still writes a JSON sidecar beside the JPG. The sidecar powers
the public details drawer and the private forgetting dataset.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from dream.anchor import Anchor
from dream.dial import DialParams

LABELED_GENERATED = "generated"

_REQUIRED_TOP_LEVEL = (
    "generated_at",
    "labeled",
    "dial",
    "dial_params",
    "prompt",
    "seed",
    "width",
    "height",
    "anchor_frame",
    "anchor_source",
    "models",
    "weather_packet",
)

_REQUIRED_MODEL_KEYS = ("base", "vae", "controlnet_depth", "controlnet_softedge")


@dataclass
class ProvenanceSidecar:
    """Typed provenance record for one generated frame."""

    generated_at: str
    labeled: str
    dial: float
    dial_params: dict[str, float]
    prompt: str
    seed: int
    width: int
    height: int
    anchor_frame: str
    anchor_source: str
    models: dict[str, Any]
    weather_packet: dict[str, Any]
    anchor_distance: float | None = None
    edge_crop: dict[str, float] | None = None
    device: str | None = None
    dtype: str | None = None
    dream_id: str | None = None
    validator_scores: dict[str, Any] | None = None
    failure_mode: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProvenanceSidecar:
        return cls(
            generated_at=str(data["generated_at"]),
            labeled=str(data["labeled"]),
            dial=float(data["dial"]),
            dial_params=dict(data["dial_params"]),
            prompt=str(data["prompt"]),
            seed=int(data["seed"]),
            width=int(data["width"]),
            height=int(data["height"]),
            anchor_frame=str(data["anchor_frame"]),
            anchor_source=str(data["anchor_source"]),
            models=dict(data["models"]),
            weather_packet=dict(data["weather_packet"]),
            anchor_distance=(
                None if data.get("anchor_distance") is None else float(data["anchor_distance"])
            ),
            edge_crop=(
                None if data.get("edge_crop") is None else dict(data["edge_crop"])
            ),
            device=data.get("device"),
            dtype=data.get("dtype"),
            dream_id=data.get("dream_id"),
            validator_scores=(
                None
                if data.get("validator_scores") is None
                else dict(data["validator_scores"])
            ),
            failure_mode=data.get("failure_mode"),
        )


def build_sidecar(
    *,
    pkt: Mapping[str, Any],
    params: DialParams,
    prompt: str,
    anchor: Anchor,
    seed: int,
    size: tuple[int, int],
    models: Mapping[str, Any],
    device: str,
    dtype: str,
    edge_crop: Mapping[str, float] | None = None,
    dream_id: str | None = None,
    validator_scores: Mapping[str, Any] | None = None,
    failure_mode: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a provenance sidecar dict for one generation."""
    sidecar = ProvenanceSidecar(
        generated_at=generated_at or datetime.now(timezone.utc).isoformat(),
        labeled=LABELED_GENERATED,
        dial=params.dial,
        dial_params=params.as_dict(),
        prompt=prompt,
        seed=int(seed),
        width=int(size[0]),
        height=int(size[1]),
        edge_crop=dict(edge_crop) if edge_crop else None,
        anchor_frame=anchor.filename,
        anchor_source=anchor.source,
        anchor_distance=anchor.distance,
        models=_models_block(models, use_ip_adapter=models.get("use_ip_adapter", True)),
        device=device,
        dtype=dtype,
        weather_packet=dict(pkt),
        dream_id=dream_id,
        validator_scores=dict(validator_scores) if validator_scores is not None else None,
        failure_mode=failure_mode,
    )
    return sidecar.to_dict()


def _models_block(models: Mapping[str, Any], *, use_ip_adapter: bool) -> dict[str, Any]:
    ip_repo = models.get("ip_adapter_repo")
    ip_weight = models.get("ip_adapter_weight")
    return {
        "base": models.get("base"),
        "vae": models.get("vae"),
        "controlnet_depth": models.get("controlnet_depth"),
        "controlnet_softedge": models.get("controlnet_softedge"),
        "ip_adapter": (
            f"{ip_repo}/{ip_weight}" if use_ip_adapter and ip_repo and ip_weight else None
        ),
        "lora": models.get("lora_path"),
        "has_lora": bool(models.get("lora_path")),
    }


def validate_sidecar(sidecar: Mapping[str, Any]) -> list[str]:
    """Return a list of validation errors (empty when valid)."""
    errors: list[str] = []

    for key in _REQUIRED_TOP_LEVEL:
        if key not in sidecar:
            errors.append(f"missing required field: {key}")

    if sidecar.get("labeled") != LABELED_GENERATED:
        errors.append(f"labeled must be {LABELED_GENERATED!r}")

    for key in ("dial_params", "models", "weather_packet"):
        val = sidecar.get(key)
        if val is not None and not isinstance(val, dict):
            errors.append(f"{key} must be an object")

    models = sidecar.get("models") or {}
    for key in _REQUIRED_MODEL_KEYS:
        if key not in models:
            errors.append(f"models.{key} is required")

    dial = sidecar.get("dial")
    if dial is not None:
        try:
            if not (0.0 <= float(dial) <= 10.0):
                errors.append("dial must be between 0 and 10")
        except (TypeError, ValueError):
            errors.append("dial must be numeric")

    seed = sidecar.get("seed")
    if seed is not None and not isinstance(seed, int):
        errors.append("seed must be an integer")

    for dim in ("width", "height"):
        val = sidecar.get(dim)
        if val is not None and (not isinstance(val, int) or val <= 0):
            errors.append(f"{dim} must be a positive integer")

    validator_scores = sidecar.get("validator_scores")
    if validator_scores is not None and not isinstance(validator_scores, dict):
        errors.append("validator_scores must be an object or null")

    failure_mode = sidecar.get("failure_mode")
    if failure_mode is not None and not isinstance(failure_mode, str):
        errors.append("failure_mode must be a string or null")

    return errors


def write_sidecar(path: Path | str, sidecar: Mapping[str, Any]) -> None:
    """Validate and write a sidecar JSON file."""
    errors = validate_sidecar(sidecar)
    if errors:
        raise ValueError("invalid sidecar: " + "; ".join(errors))
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(dict(sidecar), f, ensure_ascii=False, indent=2)
        f.write("\n")
