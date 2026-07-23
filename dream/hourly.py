"""Hourly path: weather → generate → gate → publish/hold/noise.

Maps outcomes per DREAMBERRY.md §7 (hold / honored collapse / signal_lost).
Local artifacts under `config/hourly.yaml:paths`; optional `R2Store` mirrors to R2.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np
import yaml
from PIL import Image

from dream.config import canonical_frame_path, load_dream_config, resolve_path
from dream.gates.evaluate import FrameEvaluation, evaluate_frame
from dream.storage import (
    FADE_MS_DREAM,
    FADE_MS_SIGNAL,
    next_dream_number_from_names,
    save_local_publish,
    save_local_signal_lost,
)
from weather_schema.live import (
    build_live_packet,
    check_weather_silence,
    load_dataset_config,
    load_weather_config,
)

__all__ = [
    "HourlyResult",
    "run_hourly",
    "crash_to_signal_lost",
    "hour_seed",
    "make_noise_image",
    "OUTCOME_PUBLISHED",
    "OUTCOME_HOLD",
    "OUTCOME_SIGNAL_LOST",
]

# Public noise field is small + lossy — channel-dead aesthetic, not print archive.
SIGNAL_LOST_SIZE = (1280, 960)

OUTCOME_PUBLISHED = "published"
OUTCOME_HOLD = "hold"
OUTCOME_SIGNAL_LOST = "signal_lost"

FAILURE_WEATHER_SILENCE = "weather_silence"
FAILURE_SIGNAL_LOST = "signal_lost"
FAILURE_IDENTITY_COLLAPSE = "identity_collapse"

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


def hour_seed(pkt: Mapping[str, Any], *, salt: int = 0) -> int:
    """Deterministic torch seed for the weather hour being dreamed.

    Same hour → same first-attempt seed (replayable). Next hour → a different
    seed so dial-0 can twitch (cloud/water texture) without raising denoise.
    `salt` (`config/hourly.yaml:base_seed`) shifts the whole sequence for A/B.
    """
    key = (
        pkt.get("open_meteo_hour_utc")
        or pkt.get("exif_iso")
        or pkt.get("timestamp")
        or pkt.get("time_local")
        or "unknown"
    )
    digest = hashlib.blake2b(f"{int(salt)}|{key}".encode(), digest_size=8).digest()
    # Torch CPU generators want a non-negative 32-bit-ish int.
    return int.from_bytes(digest, "big") % (2**31)


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


def _dream_timestamp(pkt: Mapping[str, Any], now: datetime) -> str:
    """The instant being dreamed, in the archive's ISO-Z form (matches Cloudberry)."""
    ts = pkt.get("exif_iso") or pkt.get("timestamp") or pkt.get("open_meteo_hour_utc")
    if ts:
        return str(ts).replace("+00:00", "Z")
    return now.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _next_dream_number(out_dir: Path, store: Any | None = None) -> int:
    if store is not None:
        return int(store.next_dream_number())
    names = (
        [p.name for p in out_dir.iterdir() if p.is_file()] if out_dir.exists() else []
    )
    return next_dream_number_from_names(names)


def _read_status(path: Path, store: Any | None = None) -> dict[str, Any]:
    if store is not None:
        return store.read_status()
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _write_status(
    path: Path,
    status: Mapping[str, Any],
    store: Any | None = None,
    *,
    hold: bool = False,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(dict(status), f, ensure_ascii=False, indent=2)
        f.write("\n")
    if store is not None:
        if hold:
            store.publish_hold(status)
        else:
            store.put_json("current/status.json", status)


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
    store: Any | None = None,
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

    `store` is an optional `R2Store` (M5). When set, prior status and dream
    counters come from R2, and publish/hold/signal_lost outcomes are mirrored
    there (PNG archive / WebP current).

    Seeds: when `seed_base` is omitted, the first attempt uses `hour_seed(pkt)`
    (salted by `config/hourly.yaml:base_seed`); retries bump `+ i`. Pass
    `seed_base` to force an absolute seed (CLI / A/B).
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
    prior = _read_status(status_path, store)
    last_success_at = prior.get("last_success_at")
    # The last *successful dream* pointer — never a noise frame. `current.webp`
    # is only ever overwritten by a publish (signal_lost writes a separate key),
    # so a hold restores the real dream even if the previous hour was noise.
    last_success_dream_id = prior.get("last_success_dream_id")

    retries = int(hourly_cfg.get("retries", 3)) if retries is None else int(retries)
    seed_salt = int(hourly_cfg.get("base_seed", 0))
    # Absolute override (CLI / tests) wins; otherwise derive from the weather hour
    # after the packet is assembled.
    seed_override = None if seed_base is None else int(seed_base)

    # 1) Assemble the only genuinely-live signal.
    try:
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
    except Exception as exc:  # noqa: BLE001 — dead sensors → hold, never crash the tick
        status = _status_hold(
            now=now,
            failure_mode=FAILURE_WEATHER_SILENCE,
            hold_reason=FAILURE_WEATHER_SILENCE,
            last_success_at=last_success_at,
            last_success_dream_id=last_success_dream_id,
            dial=dial,
            attempts=0,
            reasons=[f"weather_fetch_failed: {type(exc).__name__}: {exc}"],
            prior=prior,
        )
        if write:
            _write_status(status_path, status, store, hold=True)
        return HourlyResult(
            outcome=OUTCOME_HOLD,
            failure_mode=FAILURE_WEATHER_SILENCE,
            hold_reason=FAILURE_WEATHER_SILENCE,
            attempts=0,
            status=status,
            packet={},
        )

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
            last_success_dream_id=last_success_dream_id,
            dial=dial,
            attempts=0,
            reasons=list(silence.reasons),
            prior=prior,
        )
        if write:
            _write_status(status_path, status, store, hold=True)
        return HourlyResult(
            outcome=OUTCOME_HOLD,
            failure_mode=FAILURE_WEATHER_SILENCE,
            hold_reason=FAILURE_WEATHER_SILENCE,
            attempts=0,
            status=status,
            packet=pkt,
        )

    seed_base = (
        seed_override
        if seed_override is not None
        else hour_seed(pkt, salt=seed_salt)
    )

    # 3) Generate + gate with fresh-seed retries.
    if engine is None:
        from dream.pipeline import DreamEngine

        engine = DreamEngine(dream_cfg)
    if evaluate_fn is None:
        evaluate_fn = _default_evaluator(gates_cfg, dream_cfg)

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

        try:
            ev = evaluate_fn(result.image, pkt, dial)
        except Exception as exc:  # noqa: BLE001 — gate hiccup → retry / signal_lost
            last_error = f"gate:{type(exc).__name__}: {exc}"
            last_reject = last_error
            continue
        if ev.accept:
            try:
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
                    store=store,
                    dream_cfg=dream_cfg,
                    engine=engine,
                )
            except Exception as exc:  # noqa: BLE001 — R2 / disk → signal_lost (dream broke)
                last_error = f"publish_failed: {type(exc).__name__}: {exc}"
                break
        last_reject = ev.reject_reason

    # 4) Dream broke this hour (gen fail / gates reject / publish blow up) →
    # SIGNAL LOST (noise). Weather silence already returned hold above.
    return _signal_lost(
        pkt=pkt,
        dial=dial,
        attempts=attempts,
        now=now,
        last_success_at=last_success_at,
        last_success_dream_id=last_success_dream_id,
        error=last_error or last_reject,
        dream_cfg=dream_cfg,
        public_dir=public_dir,
        status_path=status_path,
        write=write,
        store=store,
    )


def crash_to_signal_lost(
    *,
    dial: float = 0.0,
    store: Any | None = None,
    error: str,
    now: datetime | None = None,
    dream_cfg: Mapping[str, Any] | None = None,
    hourly_cfg: Mapping[str, Any] | None = None,
) -> HourlyResult:
    """Last-resort noise write when the tick body crashed before a normal outcome."""
    now = _now(now)
    dream_cfg = dream_cfg or load_dream_config()
    hourly_cfg = hourly_cfg or _load_yaml(resolve_path("config/hourly.yaml"))
    public_dir = resolve_path(hourly_cfg["paths"]["public_dir"])
    status_path = public_dir / "status.json"
    prior = _read_status(status_path, store)
    return _signal_lost(
        pkt={},
        dial=dial,
        attempts=0,
        now=now,
        last_success_at=prior.get("last_success_at"),
        last_success_dream_id=prior.get("last_success_dream_id"),
        error=error,
        dream_cfg=dream_cfg,
        public_dir=public_dir,
        status_path=status_path,
        write=True,
        store=store,
    )


def _status_hold(
    *,
    now: datetime,
    failure_mode: str | None,
    hold_reason: str | None,
    last_success_at: str | None,
    last_success_dream_id: str | None,
    dial: float,
    attempts: int,
    reasons: list[str],
    prior: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    # Hold shows the last successful *dream* (current.webp), not the last write —
    # so a hold that follows a signal_lost reverts from noise back to the dream.
    # If nothing has ever succeeded there is nothing honest to show yet.
    has_success = bool(last_success_at)
    prior = prior or {}
    status: dict[str, Any] = {
        "updated_at": now.isoformat(),
        "hold": True,
        "failure_mode": failure_mode,
        "hold_reason": hold_reason,
        "last_success_at": last_success_at,
        "last_success_dream_id": last_success_dream_id,
        "current": "current.webp" if has_success else None,
        "dream_id": last_success_dream_id if has_success else None,
        "dial": float(dial),
        "attempts": attempts,
        "reasons": reasons,
    }
    if has_success and prior.get("current") == "signal_lost.webp":
        # Coming back from noise into the held dream — quick wake.
        status["previous"] = "signal_lost.webp"
        status["fade_ms"] = FADE_MS_SIGNAL
        status["fade_started_at"] = now.isoformat()
    elif has_success:
        # Preserve the live dream's mid-join fade so late visitors still blend.
        status["previous"] = prior.get("previous")
        status["fade_ms"] = int(prior.get("fade_ms") or FADE_MS_DREAM)
        status["fade_started_at"] = (
            prior.get("fade_started_at") or prior.get("last_success_at")
        )
    else:
        status["previous"] = None
        status["fade_ms"] = FADE_MS_DREAM
        status["fade_started_at"] = None
    return status


def _fade_for_publish(
    prior: Mapping[str, Any],
    *,
    public_dir: Path,
) -> tuple[str | None, int]:
    """Basename of the outgoing frame + fade duration for a new dream publish."""
    if prior.get("current") == "signal_lost.webp":
        return "signal_lost.webp", FADE_MS_SIGNAL
    if (
        (public_dir / "current.webp").exists()
        or prior.get("current") == "current.webp"
        or prior.get("last_success_dream_id")
    ):
        return "previous.webp", FADE_MS_DREAM
    return None, FADE_MS_DREAM


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
    store: Any | None = None,
    dream_cfg: Mapping[str, Any] | None = None,
    engine: Any | None = None,
) -> HourlyResult:
    timestamp = _dream_timestamp(pkt, now)
    number = _next_dream_number(archive_dir, store) if write else 1
    dream_id = f"{timestamp}_DREAM{number:03d}"

    sidecar = dict(result.sidecar)
    sidecar["dream_id"] = dream_id
    sidecar["validator_scores"] = evaluation.validator_scores
    sidecar["failure_mode"] = evaluation.failure_mode

    # Optional post-gate upscale (hourly live: disabled → SDXL-native publish;
    # on-demand SUPIR uses upscale_archive / upscale_for_publish with enabled).
    publish_image = result.image
    if dream_cfg is not None:
        from dream.upscale import upscale_for_publish

        if engine is not None and hasattr(engine, "unload"):
            engine.unload()
        up = upscale_for_publish(
            result.image,
            dream_cfg,
            prompt=str(sidecar.get("prompt") or ""),
            seed=int(seed),
        )
        publish_image = up.image
        sidecar.update(up.meta)
        sidecar["width"] = int(publish_image.size[0])
        sidecar["height"] = int(publish_image.size[1])

    current_name = "current.webp"
    image_path = str(public_dir / current_name)
    prior = _read_status(status_path, store)
    previous, fade_ms = _fade_for_publish(prior, public_dir=public_dir)
    started = now.isoformat()

    status = {
        "updated_at": started,
        "hold": False,
        "failure_mode": evaluation.failure_mode,
        "hold_reason": None,
        "last_success_at": started,
        "last_success_dream_id": dream_id,
        "current": current_name,
        "previous": previous,
        "fade_ms": fade_ms,
        "fade_started_at": started,
        "dream_id": dream_id,
        "dial": float(dial),
        "attempts": attempts,
        "reasons": [],
    }

    if write:
        status = save_local_publish(
            image=publish_image,
            sidecar=sidecar,
            status=status,
            dream_id=dream_id,
            public_dir=public_dir,
            archive_dir=archive_dir,
        )
        if store is not None:
            keys = store.publish_frame(
                dream_id=dream_id,
                image=publish_image,
                sidecar=sidecar,
                status=status,
            )
            # R2 is authoritative for previous (promote may no-op if current missing).
            status = store.read_status() or status
            status = {
                **status,
                **{f"r2_{k}": v for k, v in keys.items() if v},
            }
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
    last_success_dream_id: str | None,
    error: str | None,
    dream_cfg: Mapping[str, Any],
    public_dir: Path,
    status_path: Path,
    write: bool,
    store: Any | None = None,
) -> HourlyResult:
    # Small lossy noise — channel-dead aesthetic, not a print-size archive frame.
    size = SIGNAL_LOST_SIZE
    noise_name = "signal_lost.webp"
    image_path = str(public_dir / noise_name)
    noise = make_noise_image(size, seed=int(now.timestamp()))
    started = now.isoformat()
    # Outgoing layer is the last dream (still on disk as current.webp) when one exists.
    previous = "current.webp" if last_success_at else None

    status = {
        "updated_at": started,
        "hold": False,
        "failure_mode": FAILURE_SIGNAL_LOST,
        "hold_reason": None,
        # Success pointers are preserved so the next good hour — or a later hold —
        # restores the dream. current is the noise field; no dream is on screen.
        "last_success_at": last_success_at,
        "last_success_dream_id": last_success_dream_id,
        "current": noise_name,
        "previous": previous,
        "fade_ms": FADE_MS_SIGNAL,
        "fade_started_at": started,
        "dream_id": None,
        "dial": float(dial),
        "attempts": attempts,
        "reasons": [error] if error else [],
    }

    if write:
        save_local_signal_lost(image=noise, status=status, public_dir=public_dir)
        if store is not None:
            keys = store.publish_signal_lost(image=noise, status=status)
            status = {**status, **{f"r2_{k}": v for k, v in keys.items()}}
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
