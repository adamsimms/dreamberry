"""Unit tests for the hourly path decision logic.

The heavy engine and gate models are faked so the orchestration — weather
silence → hold, generate + gate with retries, publish/hold/signal-lost mapping —
is exercised without any downloads or network.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from PIL import Image

from dream.gates.evaluate import FrameEvaluation, frame_decision
from dream.hourly import (
    OUTCOME_HOLD,
    OUTCOME_PUBLISHED,
    OUTCOME_SIGNAL_LOST,
    SIGNAL_LOST_SIZE,
    crash_to_signal_lost,
    make_noise_image,
    run_hourly,
)

NOW = datetime(2026, 7, 21, 15, 0, tzinfo=timezone.utc)


def _valid_sidecar() -> dict:
    return {
        "generated_at": NOW.isoformat(),
        "labeled": "generated",
        "dial": 0.0,
        "dial_params": {"denoise": 0.4},
        "prompt": "cldbry window view",
        "seed": 0,
        "width": 8,
        "height": 8,
        "anchor_frame": "frame.JPG",
        "anchor_source": "archive",
        "models": {
            "base": "sdxl",
            "vae": "vae",
            "controlnet_depth": "cn_depth",
            "controlnet_softedge": "cn_edge",
        },
        "weather_packet": {"month": 7},
    }


class FakeEngine:
    """Returns a canned frame, or raises for the first `n_raise` calls."""

    def __init__(self, *, n_raise: int = 0):
        self.n_raise = n_raise
        self.calls = 0
        self.image = Image.new("RGB", (8, 8), (120, 120, 120))

    def generate(self, pkt, *, dial=0.0, seed=None, **kwargs):
        self.calls += 1
        if self.calls <= self.n_raise:
            raise RuntimeError("gpu dead")
        return SimpleNamespace(image=self.image, sidecar=_valid_sidecar())


def _eval(collapse_action: str, season_action: str) -> FrameEvaluation:
    accept, reject, fm = frame_decision(collapse_action, season_action)
    return FrameEvaluation(
        accept=accept,
        reject_reason=reject,
        failure_mode=fm,
        validator_scores={
            "dino_distance": 0.2,
            "horizon_displacement": 0.03,
            "nearest_real": ["a.JPG"],
            "collapse": {"action": collapse_action},
            "season": {"action": season_action},
        },
    )


def _cfgs(tmp_path):
    return dict(
        dream_cfg={
            "generation": {"width": 8, "height": 8},
            # Unit tests stay at native size — no SUPIR download.
            "upscale": {"enabled": False},
        },
        gates_cfg={},
        weather_cfg={"live": {"staleness_hours": 3.0}},
        dataset_cfg={},
        hourly_cfg={
            "retries": 2,
            "base_seed": 0,
            "paths": {
                "public_dir": str(tmp_path / "public"),
                "archive_dir": str(tmp_path / "archive"),
            },
        },
    )


def _fresh_packet() -> dict:
    return {
        "month": 7,
        "cloud_cover": 50,
        "visibility": 40000.0,
        "weather_code": 3,
        "open_meteo_failed": False,
        "open_meteo_hour_utc": NOW.isoformat(),
    }


# --- pure decision ----------------------------------------------------------


def test_frame_decision_pass():
    assert frame_decision("pass", "pass") == (True, None, None)


def test_frame_decision_season_refuse_blocks_at_any_dial():
    assert frame_decision("pass", "refuse") == (False, "season_lock", None)
    assert frame_decision("honored_dissolve", "refuse") == (False, "season_lock", None)


def test_frame_decision_honored_dissolve_publishes_as_collapse():
    assert frame_decision("honored_dissolve", "warn") == (True, None, "identity_collapse")


def test_frame_decision_regen_or_hold_rejects():
    assert frame_decision("regen_or_hold", "pass") == (False, "identity_collapse", None)


# --- orchestration ----------------------------------------------------------


def test_weather_silence_holds_without_generating(tmp_path):
    engine = FakeEngine()
    pkt = {"open_meteo_failed": True}
    result = run_hourly(
        dial=0.0,
        packet=pkt,
        engine=engine,
        evaluate_fn=lambda *a: _eval("pass", "pass"),
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_HOLD
    assert result.failure_mode == "weather_silence"
    assert engine.calls == 0
    assert "open_meteo_fetch_failed" in result.status["reasons"]
    # No current frame written on a hold.
    assert not (tmp_path / "public" / "current.webp").exists()


def test_clean_frame_publishes_and_moves_pointer(tmp_path):
    engine = FakeEngine()
    result = run_hourly(
        dial=0.0,
        packet=_fresh_packet(),
        engine=engine,
        evaluate_fn=lambda *a: _eval("pass", "pass"),
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_PUBLISHED
    assert result.failure_mode is None
    assert engine.calls == 1
    assert result.status["hold"] is False
    assert result.status["last_success_at"] == NOW.isoformat()
    assert (tmp_path / "public" / "current.webp").exists()
    assert (tmp_path / "public" / "current.json").exists()
    # Sidecar carries validator scores + archived PNG copy exists.
    assert result.sidecar["validator_scores"]["collapse"]["action"] == "pass"
    assert list((tmp_path / "archive").glob("*_DREAM*.png"))


def test_honored_dissolve_publishes_with_collapse_failure_mode(tmp_path):
    engine = FakeEngine()
    result = run_hourly(
        dial=8.0,
        packet=_fresh_packet(),
        engine=engine,
        evaluate_fn=lambda *a: _eval("honored_dissolve", "pass"),
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_PUBLISHED
    assert result.failure_mode == "identity_collapse"
    assert result.status["hold"] is False


def test_persistent_collapse_holds_last_good_frame(tmp_path):
    engine = FakeEngine()
    result = run_hourly(
        dial=0.0,
        packet=_fresh_packet(),
        engine=engine,
        evaluate_fn=lambda *a: _eval("regen_or_hold", "pass"),
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_HOLD
    assert result.failure_mode is None
    assert result.hold_reason == "identity_collapse"
    assert engine.calls == 3  # retries=2 → 3 attempts
    assert not (tmp_path / "public" / "current.webp").exists()


def test_persistent_season_refuse_holds(tmp_path):
    engine = FakeEngine()
    result = run_hourly(
        dial=0.0,
        packet=_fresh_packet(),
        engine=engine,
        evaluate_fn=lambda *a: _eval("pass", "refuse"),
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_HOLD
    assert result.hold_reason == "season_lock"


def test_retry_then_accept_publishes(tmp_path):
    engine = FakeEngine()
    evals = iter([_eval("regen_or_hold", "pass"), _eval("pass", "pass")])
    result = run_hourly(
        dial=0.0,
        packet=_fresh_packet(),
        engine=engine,
        evaluate_fn=lambda *a: next(evals),
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_PUBLISHED
    assert result.attempts == 2
    assert engine.calls == 2


def test_all_generations_fail_is_signal_lost(tmp_path):
    engine = FakeEngine(n_raise=99)
    result = run_hourly(
        dial=0.0,
        packet=_fresh_packet(),
        engine=engine,
        evaluate_fn=lambda *a: _eval("pass", "pass"),
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_SIGNAL_LOST
    assert result.failure_mode == "signal_lost"
    assert (tmp_path / "public" / "signal_lost.webp").exists()
    # A prior good frame's pointer is preserved via last_success_at.
    assert result.status["current"] == "signal_lost.webp"


def test_signal_lost_preserves_prior_last_success(tmp_path):
    cfgs = _cfgs(tmp_path)
    # Seed a prior successful status.
    pub = tmp_path / "public"
    pub.mkdir(parents=True)
    (pub / "status.json").write_text(
        json.dumps({"last_success_at": "2026-07-21T14:00:00+00:00", "current": "current.webp"})
    )
    result = run_hourly(
        dial=0.0,
        packet=_fresh_packet(),
        engine=FakeEngine(n_raise=99),
        evaluate_fn=lambda *a: _eval("pass", "pass"),
        now=NOW,
        **cfgs,
    )
    assert result.outcome == OUTCOME_SIGNAL_LOST
    assert result.status["last_success_at"] == "2026-07-21T14:00:00+00:00"


def test_publish_records_last_success_dream_id(tmp_path):
    result = run_hourly(
        dial=0.0,
        packet=_fresh_packet(),
        engine=FakeEngine(),
        evaluate_fn=lambda *a: _eval("pass", "pass"),
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_PUBLISHED
    assert result.status["last_success_dream_id"] == result.dream_id
    assert result.status["current"] == "current.webp"


def test_first_ever_hold_shows_nothing(tmp_path):
    # No prior success on disk → a hold has no honest frame to point at.
    result = run_hourly(
        dial=0.0,
        packet={"open_meteo_failed": True},
        engine=FakeEngine(),
        evaluate_fn=lambda *a: _eval("pass", "pass"),
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_HOLD
    assert result.status["current"] is None
    assert result.status["dream_id"] is None


def test_hold_after_signal_lost_reverts_to_dream_not_noise(tmp_path):
    # The locked #19 contract: hold restores the last *dream*, never noise.
    pub = tmp_path / "public"
    pub.mkdir(parents=True)
    (pub / "status.json").write_text(
        json.dumps(
            {
                "hold": False,
                "failure_mode": "signal_lost",
                "last_success_at": "2026-07-21T14:00:00+00:00",
                "last_success_dream_id": "2026-07-21T14:00:00Z_DREAM007",
                "current": "signal_lost.webp",
                "dream_id": None,
            }
        )
    )
    result = run_hourly(
        dial=0.0,
        packet={"open_meteo_failed": True},
        engine=FakeEngine(),
        evaluate_fn=lambda *a: _eval("pass", "pass"),
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_HOLD
    assert result.failure_mode == "weather_silence"
    # Pointer must move OFF the noise field back to the held dream.
    assert result.status["current"] == "current.webp"
    assert result.status["dream_id"] == "2026-07-21T14:00:00Z_DREAM007"
    assert result.status["last_success_dream_id"] == "2026-07-21T14:00:00Z_DREAM007"


def test_signal_lost_preserves_last_success_dream_id(tmp_path):
    pub = tmp_path / "public"
    pub.mkdir(parents=True)
    (pub / "status.json").write_text(
        json.dumps(
            {
                "last_success_at": "2026-07-21T14:00:00+00:00",
                "last_success_dream_id": "2026-07-21T14:00:00Z_DREAM007",
                "current": "current.webp",
                "dream_id": "2026-07-21T14:00:00Z_DREAM007",
            }
        )
    )
    result = run_hourly(
        dial=0.0,
        packet=_fresh_packet(),
        engine=FakeEngine(n_raise=99),
        evaluate_fn=lambda *a: _eval("pass", "pass"),
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_SIGNAL_LOST
    assert result.status["current"] == "signal_lost.webp"
    assert result.status["dream_id"] is None
    # The dream is preserved for the next good hour / a later hold.
    assert result.status["last_success_dream_id"] == "2026-07-21T14:00:00Z_DREAM007"


def test_make_noise_image_is_deterministic():
    a = make_noise_image((16, 12), seed=7)
    b = make_noise_image((16, 12), seed=7)
    assert a.size == (16, 12)
    assert a.tobytes() == b.tobytes()


def test_publish_mirrors_to_r2_store(tmp_path):
    from dream.tests.test_storage import FakeR2

    store = FakeR2()
    engine = FakeEngine()
    result = run_hourly(
        dial=0.0,
        packet=_fresh_packet(),
        engine=engine,
        evaluate_fn=lambda *a: _eval("pass", "pass"),
        store=store,
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_PUBLISHED
    assert any(k.endswith(".png") for k in store.objects)
    assert "current/current.webp" in store.objects
    assert "current/status.json" in store.objects


def test_hold_updates_r2_status_only(tmp_path):
    from dream.tests.test_storage import FakeR2

    store = FakeR2()
    # Seed a prior current frame in the fake bucket.
    store.objects["current/current.webp"] = b"prior"
    result = run_hourly(
        dial=0.0,
        packet={"open_meteo_failed": True},
        engine=FakeEngine(),
        evaluate_fn=lambda *a: _eval("pass", "pass"),
        store=store,
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_HOLD
    assert store.objects["current/current.webp"] == b"prior"
    assert json.loads(store.objects["current/status.json"])["hold"] is True


def test_gate_exception_holds_after_producing_frames(tmp_path):
    engine = FakeEngine()

    def boom(*_a):
        raise RuntimeError("dino offline")

    result = run_hourly(
        dial=0.0,
        packet=_fresh_packet(),
        engine=engine,
        evaluate_fn=boom,
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_HOLD
    assert result.hold_reason and "gate:" in result.hold_reason


def test_publish_exception_holds_last_good(tmp_path):
    engine = FakeEngine()

    class BoomStore:
        def read_status(self):
            return {}

        def next_dream_number(self):
            return 1

        def publish_frame(self, **_kw):
            raise RuntimeError("R2 down")

        def publish_hold(self, status):
            return {"status": "current/status.json"}

    result = run_hourly(
        dial=0.0,
        packet=_fresh_packet(),
        engine=engine,
        evaluate_fn=lambda *a: _eval("pass", "pass"),
        store=BoomStore(),
        now=NOW,
        **_cfgs(tmp_path),
    )
    assert result.outcome == OUTCOME_HOLD
    assert result.hold_reason and "publish_failed" in result.hold_reason


def test_crash_to_signal_lost_writes_small_noise(tmp_path):
    cfgs = _cfgs(tmp_path)
    result = crash_to_signal_lost(
        dial=0.0,
        error="boom",
        now=NOW,
        dream_cfg=cfgs["dream_cfg"],
        hourly_cfg=cfgs["hourly_cfg"],
    )
    assert result.outcome == OUTCOME_SIGNAL_LOST
    noise = Image.open(tmp_path / "public" / "signal_lost.webp")
    assert noise.size == SIGNAL_LOST_SIZE
