"""Unit tests for archive studio index helpers."""

from __future__ import annotations

from dream.archive_index import (
    build_index_document,
    entry_from_dream_id,
    entry_from_sidecar,
)


def test_entry_from_dream_id():
    e = entry_from_dream_id("2026-10-16T12:30:00Z_DREAM2073")
    assert e["cabin_day"] == "2026-10-16"
    assert e["png"].endswith("_DREAM2073.png")
    assert e["thumb"].endswith("thumbs/2026-10-16T12:30:00Z_DREAM2073.webp")
    assert e["weather_summary"] is None


def test_entry_from_sidecar_cabin_time():
    sc = {
        "generated_at": "2026-10-16T13:05:40+00:00",
        "dial": 0.0,
        "failure_mode": None,
        "anchor_frame": "2017-10-11T11:58:50.000Z_GOPR2884.JPG",
        "anchor_source": "weather_nn",
        "weather_packet": {
            "open_meteo_hour_utc": "2026-10-16T12:30:00Z",
            "weather_code": 2,
            "temperature_2m": 4.3,
        },
    }
    e = entry_from_sidecar(sc, dream_id="2026-10-16T12:30:00Z_DREAM2073")
    assert e["dream_id"] == "2026-10-16T12:30:00Z_DREAM2073"
    assert e["png"].endswith("_DREAM2073.png")
    assert e["cabin_day"] == "2026-10-16"
    assert e["cabin_time"]  # NDT/NST offset from 12:30Z
    assert e["cabin_feed"]  # short header e.g. "16 Oct"
    assert "partly cloudy" in (e["weather_summary"] or "")
    assert "4°C" in (e["weather_summary"] or "")


def test_build_index_newest_first():
    entries = [
        {"dream_id": "2026-10-01T00:00:00Z_DREAM001"},
        {"dream_id": "2026-10-16T12:30:00Z_DREAM2073"},
        {"dream_id": "2026-10-10T00:00:00Z_DREAM010"},
    ]
    doc = build_index_document(entries)
    assert doc["count"] == 3
    assert doc["entries"][0]["dream_id"].startswith("2026-10-16")
    assert doc["entries"][-1]["dream_id"].startswith("2026-10-01")
