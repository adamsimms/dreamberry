"""Unit tests for weather nearest-neighbor retrieval (§4.3–§4.4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from weather_schema.retrieve import IndexEntry, WeatherNNIndex


def _vec(**overrides: float | None) -> list[float | None]:
    base: list[float | None] = [0.5] * 9
    names = [
        "solar_elevation",
        "cloud_cover",
        "visibility",
        "precip_class",
        "wave_ht_sig",
        "wind_speed_10m",
        "wind_dir_onshore",
        "rh",
        "temperature_2m",
    ]
    for i, name in enumerate(names):
        if name in overrides:
            base[i] = overrides[name]
    return base


def _index(entries: list[IndexEntry]) -> WeatherNNIndex:
    return WeatherNNIndex(entries)


def test_season_gate_blocks_summer_to_winter():
    """Summer query must not retrieve winter anchors even when closer."""
    index = _index(
        [
            IndexEntry("winter_close.jpg", month=1, feature_vector=_vec(solar_elevation=0.51)),
            IndexEntry("summer_far.jpg", month=7, feature_vector=_vec(solar_elevation=0.9)),
        ]
    )
    pkt = {"month": 8, "solar_elevation": 50.0, "weather_code": 0}
    hits = index.query(pkt, k=5)
    assert len(hits) == 1
    assert hits[0]["filename"] == "summer_far.jpg"
    assert "winter_close.jpg" not in {h["filename"] for h in hits}


def test_season_gate_late_winter_adjacency():
    """Late-winter query may match winter and spring, not summer."""
    index = _index(
        [
            IndexEntry("jan.jpg", month=1, feature_vector=_vec()),
            IndexEntry("mar.jpg", month=3, feature_vector=_vec()),
            IndexEntry("jul.jpg", month=7, feature_vector=_vec()),
        ]
    )
    pkt = {"month": 4, "solar_elevation": 20.0, "weather_code": 0}
    hits = index.query(pkt, k=5)
    names = {h["filename"] for h in hits}
    assert names == {"jan.jpg", "mar.jpg"}
    assert "jul.jpg" not in names


def test_season_gate_autumn_late_autumn():
    """Autumn and late autumn are mutually reachable; summer is not."""
    index = _index(
        [
            IndexEntry("oct.jpg", month=10, feature_vector=_vec()),
            IndexEntry("nov.jpg", month=11, feature_vector=_vec()),
            IndexEntry("aug.jpg", month=8, feature_vector=_vec()),
        ]
    )
    pkt = {"month": 10, "solar_elevation": 25.0, "weather_code": 0}
    hits = index.query(pkt, k=5)
    names = {h["filename"] for h in hits}
    assert names == {"oct.jpg", "nov.jpg"}


def test_query_distance_ordering():
    """Among same-season candidates, results are sorted by ascending distance."""
    index = _index(
        [
            IndexEntry("near.jpg", month=8, feature_vector=_vec(cloud_cover=0.51)),
            IndexEntry("mid.jpg", month=8, feature_vector=_vec(cloud_cover=0.55)),
            IndexEntry("far.jpg", month=8, feature_vector=_vec(cloud_cover=0.9)),
        ]
    )
    pkt = {"month": 8, "solar_elevation": 30.0, "cloud_cover": 50.0, "weather_code": 0}
    hits = index.query(pkt, k=3)
    assert [h["filename"] for h in hits] == ["near.jpg", "mid.jpg", "far.jpg"]
    assert hits[0]["distance"] < hits[1]["distance"] < hits[2]["distance"]


def test_query_respects_k():
    index = _index(
        [
            IndexEntry(f"img{i}.jpg", month=8, feature_vector=_vec(cloud_cover=0.5 + i * 0.01))
            for i in range(10)
        ]
    )
    pkt = {"month": 8, "solar_elevation": 30.0, "cloud_cover": 50.0, "weather_code": 0}
    assert len(index.query(pkt, k=3)) == 3


def test_null_drop_skips_one_sided_null():
    """When query wave is null, anchor wave values do not affect distance (§4.4)."""
    from weather_schema.vector import feature_vector

    pkt = {
        "month": 8,
        "solar_elevation": 30.0,
        "cloud_cover": 50.0,
        "weather_code": 0,
        "wave_ht_sig": None,
    }
    q_vals, _ = feature_vector(pkt)
    low_wave = list(q_vals)
    low_wave[4] = 0.1
    high_wave = list(q_vals)
    high_wave[4] = 0.9

    index = _index(
        [
            IndexEntry("low.jpg", month=8, feature_vector=low_wave),
            IndexEntry("high.jpg", month=8, feature_vector=high_wave),
        ]
    )
    hits = index.query(pkt, k=2)
    assert hits[0]["distance"] == pytest.approx(0.0, abs=1e-9)
    assert hits[1]["distance"] == pytest.approx(0.0, abs=1e-9)


def test_include_prompt():
    index = _index(
        [
            IndexEntry(
                "one.jpg",
                month=8,
                feature_vector=_vec(),
                prompt="cldbry window view, summer",
            )
        ]
    )
    pkt = {"month": 8, "solar_elevation": 30.0, "weather_code": 0}
    hits = index.query(pkt, k=1, include_prompt=True)
    assert hits[0]["prompt"] == "cldbry window view, summer"


def test_save_load_roundtrip(tmp_path: Path):
    index = _index(
        [
            IndexEntry("x.jpg", month=8, feature_vector=_vec(), prompt="p"),
            IndexEntry("y.jpg", month=1, feature_vector=_vec(cloud_cover=0.2)),
        ]
    )
    path = tmp_path / "index.json"
    index.save(path)
    loaded = WeatherNNIndex.load(path)
    assert len(loaded) == 2
    pkt = {"month": 8, "solar_elevation": 30.0, "cloud_cover": 50.0, "weather_code": 0}
    assert index.query(pkt, k=1) == loaded.query(pkt, k=1)


def test_build_from_captions_line(tmp_path: Path):
    captions = tmp_path / "captions.jsonl"
    row = {
        "filename": "2017-08-16T08:00:36.000Z_GOPR1957.JPG",
        "month": 8,
        "feature_vector": _vec(),
        "prompt": "summer prompt",
    }
    captions.write_text(json.dumps(row) + "\n")
    index = WeatherNNIndex.build_from_captions(captions)
    assert len(index) == 1
    assert index.entries[0].filename == row["filename"]
