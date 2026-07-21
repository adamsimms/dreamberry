"""Unit tests for M3 quality gates — pure logic, no model downloads."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from dream.gates.embed import DinoReference
from dream.gates.horizon import horizon_displacement, horizon_profile
from dream.gates.identity import IdentityScores, collapse_verdict
from dream.gates.season import (
    COARSE_SEASONS,
    expected_coarse_season,
    season_verdict,
)


ID_CFG = {
    "dino_distance_fail": 0.45,
    "horizon_displacement_fail": 0.06,
    "enforced_below_dial": 3.0,
    "knn": 3,
}
SEASON_CFG = {"refuse_margin": 0.05}


# --- horizon -----------------------------------------------------------------


def _split_image(boundary_frac: float, w=256, h=192) -> Image.Image:
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    b = int(h * boundary_frac)
    arr[:b] = 230  # bright sky
    arr[b:] = 40  # dark sea
    return Image.fromarray(arr)


def test_horizon_profile_locates_boundary():
    prof = horizon_profile(_split_image(0.5))
    assert abs(float(np.median(prof)) - 0.5) < 0.03


def test_horizon_displacement_zero_for_identical():
    img = _split_image(0.5)
    assert horizon_displacement(img, img) < 0.01


def test_horizon_displacement_tracks_shift():
    a = _split_image(0.5)
    b = _split_image(0.62)
    d = horizon_displacement(a, b)
    assert 0.08 < d < 0.16


# --- collapse verdict (dial-aware) ------------------------------------------


def test_no_collapse_passes():
    s = IdentityScores(dino_distance=0.2, horizon_displacement=0.02, nearest_real=["x"])
    v = collapse_verdict(s, dial=0.0, cfg=ID_CFG)
    assert v["collapsed"] is False
    assert v["action"] == "pass"


def test_collapse_low_dial_regens():
    s = IdentityScores(dino_distance=0.7, horizon_displacement=0.02, nearest_real=["x"])
    v = collapse_verdict(s, dial=0.0, cfg=ID_CFG)
    assert v["collapsed"] is True
    assert v["enforced"] is True
    assert v["action"] == "regen_or_hold"


def test_collapse_high_dial_honored():
    s = IdentityScores(dino_distance=0.7, horizon_displacement=0.2, nearest_real=["x"])
    v = collapse_verdict(s, dial=9.0, cfg=ID_CFG)
    assert v["collapsed"] is True
    assert v["enforced"] is False
    assert v["action"] == "honored_dissolve"


def test_horizon_alone_triggers_collapse():
    s = IdentityScores(dino_distance=0.1, horizon_displacement=0.2, nearest_real=["x"])
    v = collapse_verdict(s, dial=0.0, cfg=ID_CFG)
    assert v["collapsed"] is True
    assert any("horizon" in r for r in v["reasons"])


def test_nan_dino_does_not_trigger():
    s = IdentityScores(dino_distance=float("nan"), horizon_displacement=0.02, nearest_real=[])
    v = collapse_verdict(s, dial=0.0, cfg=ID_CFG)
    assert v["collapsed"] is False


# --- season verdict (asymmetric) --------------------------------------------


@pytest.mark.parametrize(
    "month, expected",
    [(1, "winter"), (2, "winter"), (3, "winter"), (4, "winter"), (5, "spring"),
     (7, "summer"), (9, "autumn"), (11, "autumn")],
)
def test_expected_coarse_season(month, expected):
    assert expected_coarse_season(month) == expected


def _scores(top: str, gap: float = 0.5) -> dict:
    return {s: (gap if s == top else 0.0) for s in COARSE_SEASONS}


def test_season_match_passes():
    v = season_verdict(_scores("winter"), month=1, cfg=SEASON_CFG)
    assert v.action == "pass"


def test_summer_green_winter_refused():
    v = season_verdict(_scores("summer"), month=1, cfg=SEASON_CFG)
    assert v.action == "refuse"
    assert v.expected == "winter" and v.predicted == "summer"


def test_spring_in_winter_is_warn_not_refuse():
    v = season_verdict(_scores("spring"), month=2, cfg=SEASON_CFG)
    assert v.action == "warn"


def test_cold_in_summer_is_warn_only():
    # dreaming colder stays within the container → soft warning, never refuse
    v = season_verdict(_scores("winter"), month=7, cfg=SEASON_CFG)
    assert v.action == "warn"


def test_refuse_margin_respected():
    # summer barely over winter, below margin → not refused
    scores = {s: 0.0 for s in COARSE_SEASONS}
    scores["summer"] = 0.02
    v = season_verdict(scores, month=1, cfg={"refuse_margin": 0.05})
    assert v.action != "refuse"


# --- DINOv2 reference query -------------------------------------------------


def test_dino_knn_distance_and_exclude():
    embs = np.eye(4, dtype=np.float32)  # 4 orthonormal refs
    ref = DinoReference(filenames=["a", "b", "c", "d"], embeddings=embs)
    query = embs[0].copy()
    d, nearest = ref.knn_distance(query, k=1)
    assert nearest == ["a"]
    assert d < 1e-6
    # exclude the self-match → nearest becomes an orthogonal frame (distance 1.0)
    d2, nearest2 = ref.knn_distance(query, k=1, exclude={"a"})
    assert "a" not in nearest2
    assert abs(d2 - 1.0) < 1e-6
