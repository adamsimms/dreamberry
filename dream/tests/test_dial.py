"""Tests for the dream-dial schedule (brief §6)."""

from __future__ import annotations

import pytest

from dream.dial import (
    DEFAULT_DIAL,
    DIAL_MAX,
    DIAL_MIN,
    NightLightingConfig,
    apply_night_lighting,
    dial_schedule,
    resolve_generation_params,
)


def test_default_is_dial_zero():
    assert DEFAULT_DIAL == 0.0
    p = dial_schedule()
    assert p.dial == 0.0


@pytest.mark.parametrize(
    "dial, denoise, cn, ip, lora",
    [
        (0.0, 0.35, 0.90, 0.70, 0.20),
        (2.0, 0.50, 0.75, 0.60, 0.40),
        (5.0, 0.70, 0.50, 0.40, 0.60),
        (8.0, 0.85, 0.30, 0.20, 0.80),
        (10.0, 0.95, 0.10, 0.05, 1.00),
    ],
)
def test_anchor_points_exact(dial, denoise, cn, ip, lora):
    p = dial_schedule(dial)
    assert p.denoise_strength == denoise
    assert p.controlnet_scale == cn
    assert p.ip_adapter_scale == ip
    assert p.lora_scale == lora


def test_midpoint_interpolation():
    # halfway between dial 0 and 2
    p = dial_schedule(1.0)
    assert p.denoise_strength == pytest.approx(0.425)
    assert p.controlnet_scale == pytest.approx(0.825)
    assert p.ip_adapter_scale == pytest.approx(0.65)
    assert p.lora_scale == pytest.approx(0.30)


def test_monotonic_trends():
    dials = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    params = [dial_schedule(d) for d in dials]
    denoise = [p.denoise_strength for p in params]
    cn = [p.controlnet_scale for p in params]
    lora = [p.lora_scale for p in params]
    # denoise + lora rise; controlnet grip falls as the ghost drifts
    assert denoise == sorted(denoise)
    assert lora == sorted(lora)
    assert cn == sorted(cn, reverse=True)


def test_clamped_out_of_range():
    assert dial_schedule(-3).dial == DIAL_MIN
    assert dial_schedule(99).dial == DIAL_MAX
    assert dial_schedule(-3).denoise_strength == 0.35
    assert dial_schedule(99).denoise_strength == 0.95


def test_defocus_only_at_high_dial():
    assert dial_schedule(0).defocus_strength == 0.0
    assert dial_schedule(5).defocus_strength == 0.0
    assert dial_schedule(8).defocus_strength == 0.0
    assert dial_schedule(9).defocus_strength == pytest.approx(0.5)
    assert dial_schedule(10).defocus_strength == 1.0


def test_dial_zero_defocus_is_zero():
    # The locked launch state must never dissolve.
    assert dial_schedule(DEFAULT_DIAL).defocus_strength == 0.0


def test_night_lighting_darkens_dial_zero():
    day = resolve_generation_params(0.0, {"solar_elevation": 20.0})
    night = resolve_generation_params(0.0, {"solar_elevation": -20.0})
    assert day.denoise_strength == 0.35
    assert day.controlnet_scale == 0.90
    assert day.ip_adapter_scale == 0.70
    assert night.dial == 0.0
    assert night.denoise_strength == 0.70
    assert night.controlnet_scale == 0.50
    assert night.ip_adapter_scale == 0.25
    assert night.defocus_strength == 0.0


def test_night_lighting_threshold_is_civil_twilight():
    # Same boundary as curation / weather-NN: night when elev < −6°.
    at_boundary = resolve_generation_params(0.0, {"solar_elevation": -6.0})
    just_below = resolve_generation_params(0.0, {"solar_elevation": -6.01})
    assert at_boundary.denoise_strength == 0.35
    assert just_below.denoise_strength == 0.70


def test_night_lighting_missing_elev_is_noop():
    p = resolve_generation_params(0.0, {"month": 1})
    assert p.denoise_strength == 0.35


def test_night_lighting_disabled():
    night = NightLightingConfig(enabled=False)
    p = resolve_generation_params(
        0.0, {"solar_elevation": -20.0}, night=night
    )
    assert p.denoise_strength == 0.35


def test_night_lighting_does_not_loosen_high_dial():
    # Dial 10 is already freer than the night overlay; keep dial-10 scales.
    p = resolve_generation_params(10.0, {"solar_elevation": -20.0})
    assert p.denoise_strength == 0.95
    assert p.controlnet_scale == 0.10
    assert p.ip_adapter_scale == 0.05
    assert p.defocus_strength == 1.0


def test_apply_night_lighting_preserves_dial_label():
    base = dial_schedule(0.0)
    out = apply_night_lighting(base, {"solar_elevation": -12.0})
    assert out.dial == 0.0
    assert out.lora_scale == base.lora_scale
