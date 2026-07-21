"""Hourly path: weather → generate → gate → publish/hold/noise (issue #14).

Wires the live weather packet (issue #13) through the M2 dream engine and the M3
validators, mapping outcomes to the three brief failure modes
(DREAMBERRY.md §7):

  - weather silence  → HOLD: never generate; keep the last frame; status only.
  - identity collapse → dial-aware. At dial-0 (public default) a collapse forces
    a fresh-seed retry and, if it still won't grip, a HOLD of the last good
    frame. At high dial the collapse is honored and PUBLISHED (the pointer moves).
  - signal lost      → every attempt to generate threw: publish a NOISE field.

A clean frame that passes both gates is PUBLISHED, updating the public pointer,
with validator scores + any failure_mode written into the provenance sidecar.

Delivery to R2 / Pages is M5; here artifacts land locally under
`config/hourly.yaml:paths` (data/dream/, gitignored). The engine and the frame
evaluator are injectable so the orchestration logic is testable without models.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np
import yaml
from PIL import Image

from dream.config import canonical_frame_path, load_dream_config, resolve_path
from dream.gates.evaluate import FrameEvaluation, evaluate_frame
from dream.sidecar import build_sidecar, write_sidecar
from weather_schema.live import (
    build_live_packet,
    check_weather_silence,
    load_dataset_config,
    load_weather_config,
)

__all__ = [
    "HourlyResult",
    "run_hourly",
    "make_noise_image",
    "OUTCOME_PUBLISHED",
    "OUTCOME_HOLD",
    "OUTCOME_SIGNAL_LOST",
]

OUTCOME_PUBLISHED = "published"
OUTCOME_HOLD = "hold"
OUTCOME_SIGNAL_LOST = "signal_lost"

FAILURE_WEATHER_SILENCE = "weather_silence"
FAILURE_SIGNAL_LOST = "signal_lost"
FAILURE_IDENTITY_COLLAPSE = "identity_collapse"

_DREAM_RE = re.compile(r"_DREAM(\d+)\.JPG$")

# The frame evaluator contract: (image, packet, dial) -> FrameEvaluation.
Evaluator = Callable[[Any, Mapping[str, Any], float], FrameEvaluation]


@dataclass
class HourlyResult:
    """What one hourly tick decided, plus the status.json it wrote."""

    outcome: str  # OUTCOME_*
    failure_mode: str | None
    hold_reason: str | None
    attempts: int
    status: dict[str, Any]
    dream_id: str | None = None
    sidecar: dict[str, Any] | None = None
    image_path: str | None = None
    packet: dict[str, Any] = field(default_factory=dict)


# --- small helpers ----------------------------------------------------------


def make_noise_image(size: tuple[int, int], *, seed: int = 0) -> Image.Image:
    """Deterministic white-noise/static field for the signal-lost aesthetic."""
    rng = np.random.default_rng(seed)
    arr = rng.integers(0, 256, size=(size[1], size[0], 3), dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


def _dream_timestamp(pkt: Mapping[str, Any], now: datetime) -> str:
    """The instant being dreamed, in the archive's ISO-Z form (matches Cloudberry)."""
    ts = pkt.get("exif_iso") or pkt.get("timestamp") or pkt.get("open_meteo_hour_utc")
    if ts:
        return str(ts).replace("+00:00", "Z")
    return now.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _next_dream_number(out_dir: Path) -> int:
    mx = 0
    if out_dir.exists():
        for p in out_dir.glob("*_DREAM*.JPG"):
            m = _DREAM_RE.search(p.name)
            if m:
                mx = max(mx, int(m.group(1)))
    return mx + 1


def _read_status(path: Path) -> dict[str, Any]:
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _write_status(path: Path, status: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(dict(status), f, ensure_ascii=False, indent=2)
        f.write("\n")


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


# --- default (model-backed) evaluator --------------------------------------


def _default_evaluator(gates_cfg: Mapping[str, Any], dream_cfg: Mapping[str, Any]) -> Evaluator:
    """Build an evaluator that lazily loads DINOv2 refs, canonical, calibration."""
    from dream.gates.embed import DinoReference

    state: dict[str, Any] = {}

    def _ensure_loaded() -> None:
        if state:
            return
        state["dino_ref"] = DinoReference.load(resolve_path(gates_cfg["paths"]["dino_index"]))
        state["canonical"] = Image.open(canonical_frame_path(dream_cfg)).convert("RGB")
        calib_path = resolve_path(gates_cfg["paths"]["season_calibration"])
        state["calibration"] = (
            json.load(open(calib_path)) if calib_path.exists() else None
        )

    def _evaluate(image, pkt: Mapping[str, Any], dial: float) -> FrameEvaluation:
        _ensure_loaded()
        return evaluate_frame(
            image,
            pkt,
            dial,
            gates_cfg,
            dino_ref=state["dino_ref"],
            canonical=state["canonical"],
            calibration=state["calibration"],
        )

    return _evaluate


# --- orchestration ----------------------------------------------------------


def run_hourly(
    *,
    dial: float = 0.0,
    packet: Mapping[str, Any] | None = None,
    engine: Any = None,
    evaluate_fn: Evaluator | None = None,
    now: datetime | None = None,
    seed_base: int | None = None,
    retries: int | None = None,
    write: bool = True,
    skip_silence: bool = False,
    dream_cfg: Mapping[str, Any] | None = None,
    gates_cfg: Mapping[str, Any] | None = None,
    weather_cfg: Mapping[str, Any] | None = None,
    dataset_cfg: Mapping[str, Any] | None = None,
    hourly_cfg: Mapping[str, Any] | None = None,
    fetch_wyi: bool = True,
    fetch_buoy: bool = True,
) -> HourlyResult:
    """Run one hourly tick and return the decision (+ status it wrote).

    `packet` short-circuits the live fetch (archive replay / tests). `engine` and
    `evaluate_fn` are injectable; when omitted they are constructed lazily so the
    heavy models are only touched on the real path. `skip_silence` bypasses the
    freshness gate for intentional replays of old archive packets (the staleness
    check exists to catch dead *live* feeds, not deliberate replays).
    """
    now = _now(now)
    dream_cfg = dream_cfg or load_dream_config()
    gates_cfg = gates_cfg or _load_yaml(resolve_path("config/gates.yaml"))
    weather_cfg = weather_cfg or load_weather_config()
    dataset_cfg = dataset_cfg or load_dataset_config()
    hourly_cfg = hourly_cfg or _load_yaml(resolve_path("config/hourly.yaml"))

    public_dir = resolve_path(hourly_cfg["paths"]["public_dir"])
    archive_dir = resolve_path(hourly_cfg["paths"]["archive_dir"])
    status_path = public_dir / "status.json"
    prior = _read_status(status_path)
    last_success_at = prior.get("last_success_at")

    retries = int(hourly_cfg.get("retries", 3)) if retries is None else int(retries)
    seed_base = int(hourly_cfg.get("base_seed", 0)) if seed_base is None else int(seed_base)

    # 1) Assemble the only genuinely-live signal.
    if packet is None:
        pkt = build_live_packet(
            dataset_cfg=dataset_cfg,
            weather_cfg=weather_cfg,
            now=now,
            fetch_wyi=fetch_wyi,
            fetch_buoy=fetch_buoy,
        )
    else:
        pkt = dict(packet)

    # 2) Weather silence → HOLD. The dream stays; the sensors went quiet.
    silence = check_weather_silence(
        pkt,
        staleness_hours=float(weather_cfg["live"].get("staleness_hours", 3.0)),
        now=now,
    )
    if silence.is_silence and not skip_silence:
        status = _status_hold(
            now=now,
            failure_mode=FAILURE_WEATHER_SILENCE,
            hold_reason=FAILURE_WEATHER_SILENCE,
            last_success_at=last_success_at,
            prior=prior,
            dial=dial,
            attempts=0,
            reasons=list(silence.reasons),
        )
        if write:
            _write_status(status_path, status)
        return HourlyResult(
            outcome=OUTCOME_HOLD,
            failure_mode=FAILURE_WEATHER_SILENCE,
            hold_reason=FAILURE_WEATHER_SILENCE,
            attempts=0,
            status=status,
            packet=pkt,
        )

    # 3) Generate + gate with fresh-seed retries.
    if engine is None:
        from dream.pipeline import DreamEngine

        engine = DreamEngine(dream_cfg)
    if evaluate_fn is None:
        evaluate_fn = _default_evaluator(gates_cfg, dream_cfg)

    produced_any = False
    last_reject: str | None = None
    last_error: str | None = None
    attempts = 0

    for i in range(retries + 1):
        attempts = i + 1
        seed = seed_base + i
        try:
            result = engine.generate(pkt, dial=dial, seed=seed)
        except Exception as exc:  # noqa: BLE001 — any generation failure = channel dead
            last_error = f"{type(exc).__name__}: {exc}"
            continue

        produced_any = True
        ev = evaluate_fn(result.image, pkt, dial)
        if ev.accept:
            return _publish(
                result=result,
                evaluation=ev,
                pkt=pkt,
                dial=dial,
                seed=seed,
                attempts=attempts,
                now=now,
                public_dir=public_dir,
                archive_dir=archive_dir,
                status_path=status_path,
                write=write,
            )
        last_reject = ev.reject_reason

    # 4a) Frames generated but every one was rejected by a gate → HOLD last good.
    if produced_any:
        status = _status_hold(
            now=now,
            failure_mode=None,
            hold_reason=last_reject or "gate_rejected",
            last_success_at=last_success_at,
            prior=prior,
            dial=dial,
            attempts=attempts,
            reasons=[last_reject] if last_reject else [],
        )
        if write:
            _write_status(status_path, status)
        return HourlyResult(
            outcome=OUTCOME_HOLD,
            failure_mode=None,
            hold_reason=last_reject or "gate_rejected",
            attempts=attempts,
            status=status,
            packet=pkt,
        )

    # 4b) Nothing generated at all → the channel is dead → SIGNAL LOST (noise).
    return _signal_lost(
        pkt=pkt,
        dial=dial,
        attempts=attempts,
        now=now,
        last_success_at=last_success_at,
        error=last_error,
        dream_cfg=dream_cfg,
        public_dir=public_dir,
        status_path=status_path,
        write=write,
    )


def _status_hold(
    *,
    now: datetime,
    failure_mode: str | None,
    hold_reason: str | None,
    last_success_at: str | None,
    prior: Mapping[str, Any],
    dial: float,
    attempts: int,
    reasons: list[str],
) -> dict[str, Any]:
    return {
        "updated_at": now.isoformat(),
        "hold": True,
        "failure_mode": failure_mode,
        "hold_reason": hold_reason,
        "last_success_at": last_success_at,
        "current": prior.get("current"),
        "dream_id": prior.get("dream_id"),
        "dial": float(dial),
        "attempts": attempts,
        "reasons": reasons,
    }


def _publish(
    *,
    result: Any,
    evaluation: FrameEvaluation,
    pkt: Mapping[str, Any],
    dial: float,
    seed: int,
    attempts: int,
    now: datetime,
    public_dir: Path,
    archive_dir: Path,
    status_path: Path,
    write: bool,
) -> HourlyResult:
    timestamp = _dream_timestamp(pkt, now)
    number = _next_dream_number(archive_dir) if write else 1
    dream_id = f"{timestamp}_DREAM{number:03d}"

    sidecar = dict(result.sidecar)
    sidecar["dream_id"] = dream_id
    sidecar["validator_scores"] = evaluation.validator_scores
    sidecar["failure_mode"] = evaluation.failure_mode

    current_name = "current.JPG"
    image_path = str(public_dir / current_name)

    if write:
        archive_dir.mkdir(parents=True, exist_ok=True)
        public_dir.mkdir(parents=True, exist_ok=True)
        # Private hourly archive (frame + provenance).
        result.image.save(archive_dir / f"{dream_id}.JPG", "JPEG", quality=95, subsampling=0)
        write_sidecar(archive_dir / f"{dream_id}.json", sidecar)
        # Public window: one current frame + its sidecar, pointer moves.
        result.image.save(public_dir / current_name, "JPEG", quality=95, subsampling=0)
        write_sidecar(public_dir / "current.json", sidecar)

    status = {
        "updated_at": now.isoformat(),
        "hold": False,
        "failure_mode": evaluation.failure_mode,
        "hold_reason": None,
        "last_success_at": now.isoformat(),
        "current": current_name,
        "dream_id": dream_id,
        "dial": float(dial),
        "attempts": attempts,
        "reasons": [],
    }
    if write:
        _write_status(status_path, status)

    return HourlyResult(
        outcome=OUTCOME_PUBLISHED,
        failure_mode=evaluation.failure_mode,
        hold_reason=None,
        attempts=attempts,
        status=status,
        dream_id=dream_id,
        sidecar=sidecar,
        image_path=image_path,
        packet=dict(pkt),
    )


def _signal_lost(
    *,
    pkt: Mapping[str, Any],
    dial: float,
    attempts: int,
    now: datetime,
    last_success_at: str | None,
    error: str | None,
    dream_cfg: Mapping[str, Any],
    public_dir: Path,
    status_path: Path,
    write: bool,
) -> HourlyResult:
    gen = dream_cfg["generation"]
    size = (int(gen["width"]), int(gen["height"]))
    noise_name = "signal_lost.JPG"
    image_path = str(public_dir / noise_name)

    if write:
        public_dir.mkdir(parents=True, exist_ok=True)
        make_noise_image(size, seed=int(now.timestamp())).save(
            public_dir / noise_name, "JPEG", quality=90
        )

    status = {
        "updated_at": now.isoformat(),
        "hold": False,
        "failure_mode": FAILURE_SIGNAL_LOST,
        "hold_reason": None,
        # last_success_at is preserved so the next good hour restores the window.
        "last_success_at": last_success_at,
        "current": noise_name,
        "dream_id": None,
        "dial": float(dial),
        "attempts": attempts,
        "reasons": [error] if error else [],
    }
    if write:
        _write_status(status_path, status)

    return HourlyResult(
        outcome=OUTCOME_SIGNAL_LOST,
        failure_mode=FAILURE_SIGNAL_LOST,
        hold_reason=None,
        attempts=attempts,
        status=status,
        image_path=image_path,
        packet=dict(pkt),
    )
