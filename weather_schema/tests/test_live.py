"""Unit tests for live weather agent + weather silence."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from weather_schema.compose import compose_prompt
from weather_schema.live import (
    WeatherSilenceResult,
    _merge_enrichments,
    _parse_wyi_temperature,
    _parse_wyi_wind,
    build_live_packet,
    check_weather_silence,
    fetch_buoy_wave_ht_sig,
    fetch_open_meteo_forecast,
    fetch_wyi_observation,
    is_weather_silence,
)

_DATASET_CFG = {
    "cabin": {
        "latitude": 49.2026,
        "longitude": -53.4859,
        "timezone": "America/St_Johns",
    },
    "weather": {
        "hourly_variables": [
            "cloud_cover",
            "visibility",
            "weather_code",
            "relative_humidity_2m",
            "wind_speed_10m",
            "wind_direction_10m",
            "shortwave_radiation",
            "temperature_2m",
            "precipitation",
        ],
        "wind_speed_unit": "kmh",
    },
}

_WEATHER_CFG = {
    "live": {
        "staleness_hours": 3.0,
        "forecast_api": "https://api.open-meteo.com/v1/forecast",
        "forecast_days": 2,
        "wyi": {
            "station_code": "wyi",
            "past_conditions_url": "https://weather.gc.ca/past_conditions/index_e.html",
        },
        "buoy": {
            "dataset": "SMA_bonavista",
            "erddap_base": "https://www.smartatlantic.ca/erddap/tabledap",
            "lookback_hours": 6,
        },
    }
}


def _om_response() -> dict:
    return {
        "hourly": {
            "time": ["2026-07-21T17:00", "2026-07-21T18:00"],
            "cloud_cover": [100, 90],
            "visibility": [55960.0, 50000.0],
            "weather_code": [3, 3],
            "relative_humidity_2m": [45, 46],
            "wind_speed_10m": [21.6, 20.0],
            "wind_direction_10m": [250, 245],
            "shortwave_radiation": [584.0, 400.0],
            "temperature_2m": [25.0, 24.0],
            "precipitation": [0.0, 0.0],
        }
    }


def _mock_session(*, om_json=None, wyi_html=None, buoy_json=None, om_status=200):
    session = MagicMock()

    def get(url, params=None, timeout=None):  # noqa: ARG001
        resp = MagicMock()
        resp.url = url
        if "open-meteo" in url:
            resp.status_code = om_status
            if om_status >= 400:
                resp.raise_for_status.side_effect = Exception("open-meteo down")
                return resp
            resp.json.return_value = om_json or _om_response()
            resp.raise_for_status.return_value = None
            return resp
        if "weather.gc.ca" in url:
            resp.status_code = 200
            resp.text = wyi_html or _WYI_HTML
            resp.url = f"{url}?station=wyi"
            resp.raise_for_status.return_value = None
            return resp
        if "smartatlantic" in url:
            resp.status_code = 200 if buoy_json is not None else 404
            resp.json.return_value = buoy_json or {"table": {"rows": []}}
            resp.raise_for_status.return_value = None
            return resp
        resp.status_code = 404
        return resp

    session.get.side_effect = get
    return session


_WYI_HTML = """
<table id="past24Table"><tbody>
<tr><td colspan="15">21 July 2026</td></tr>
<tr>
  <td>16:30</td><td>n/a</td>
  <td>26&nbsp;(26.4)</td><td>80</td>
  <td>SSW 19 gusts 31</td><td>SSW 12</td>
  <td>28</td><td>82</td><td>36</td><td>10</td><td>50</td>
  <td>102.0</td><td>30.1</td><td>n/a</td><td>n/a</td>
</tr>
</tbody></table>
"""


NOW = datetime(2026, 7, 21, 19, 30, tzinfo=timezone.utc)  # 17:00 America/St_Johns


def test_parse_wyi_helpers():
    assert _parse_wyi_temperature("26 (26.4)") == 26.4
    speed, direction = _parse_wyi_wind("SSW 19 gusts 31")
    assert speed == 19.0
    assert direction == 202.5


def test_fetch_open_meteo_forecast_mock():
    session = _mock_session()
    row, meta = fetch_open_meteo_forecast(
        session, _DATASET_CFG, _WEATHER_CFG, now=NOW
    )
    assert row is not None
    assert meta["open_meteo_failed"] is False
    assert row["cloud_cover"] == 100
    assert row["time_local"] == "2026-07-21T17:00"


def test_fetch_wyi_observation_mock():
    session = _mock_session()
    obs = fetch_wyi_observation(session, _WEATHER_CFG)
    assert obs is not None
    assert obs["temperature_2m"] == 26.4
    assert obs["wind_speed_10m"] == 19.0


def test_fetch_buoy_wave_mock():
    session = _mock_session(
        buoy_json={
            "table": {
                "rows": [
                    [0.5, "2026-07-21T18:00:00Z"],
                    [0.8, "2026-07-21T19:00:00Z"],
                ]
            }
        }
    )
    obs = fetch_buoy_wave_ht_sig(session, _WEATHER_CFG)
    assert obs is not None
    assert obs["wave_ht_sig"] == 0.8


def test_merge_enrichments_prefers_wyi_temp_and_om_wind():
    base = {
        "temperature_2m": 25.0,
        "wind_speed_10m": 21.6,
        "wind_direction_10m": 250,
    }
    wyi = {"temperature_2m": 26.4, "wind_speed_10m": 19.0, "wind_direction_10m": 202.5}
    pkt = _merge_enrichments(base, wyi=wyi, buoy=None)
    assert pkt["temperature_2m"] == 26.4
    assert pkt["temperature_source"] == "wyi"
    assert pkt["wind_speed_10m"] == 21.6
    assert pkt["wind_source"] == "open-meteo"


def test_merge_enrichments_wyi_wind_fallback():
    base = {"temperature_2m": 25.0, "wind_speed_10m": None}
    wyi = {"temperature_2m": 26.4, "wind_speed_10m": 19.0, "wind_direction_10m": 202.5}
    pkt = _merge_enrichments(base, wyi=wyi, buoy=None)
    assert pkt["wind_speed_10m"] == 19.0
    assert pkt["wind_source"] == "wyi"


def test_build_live_packet_mock_compose_ready():
    session = _mock_session(
        buoy_json={"table": {"rows": [[1.2, "2026-07-21T19:00:00Z"]]}}
    )
    pkt = build_live_packet(
        dataset_cfg=_DATASET_CFG,
        weather_cfg=_WEATHER_CFG,
        session=session,
        now=NOW,
    )
    assert pkt["source"].startswith("open-meteo-forecast")
    assert pkt["temperature_source"] == "wyi"
    assert pkt["wave_source"] == "buoy"
    assert pkt["wave_ht_sig"] == 1.2
    assert pkt["solar_elevation"] is not None
    assert pkt["month"] == 7
    assert "after_solar_noon" in pkt
    prompt = compose_prompt(pkt)
    assert prompt.startswith("cldbry window view")


@pytest.mark.parametrize(
    "pkt, expected, reason_fragment",
    [
        (
            {"open_meteo_failed": True, "cloud_cover": 50},
            True,
            "open_meteo_fetch_failed",
        ),
        (
            {
                "open_meteo_failed": False,
                "open_meteo_hour_utc": "2026-07-21T10:00:00+00:00",
                "cloud_cover": 50,
                "timezone": "America/St_Johns",
            },
            True,
            "open_meteo_stale",
        ),
        (
            {
                "open_meteo_failed": False,
                "open_meteo_hour_utc": "2026-07-21T19:00:00+00:00",
                "cloud_cover": None,
                "visibility": None,
                "weather_code": None,
            },
            True,
            "core_fields_missing",
        ),
        (
            {
                "open_meteo_failed": False,
                "open_meteo_hour_utc": "2026-07-21T19:00:00+00:00",
                "cloud_cover": 80,
                "wave_ht_sig": None,
            },
            False,
            "",
        ),
        (
            {
                "open_meteo_failed": False,
                "cloud_cover": 50,
            },
            True,
            "open_meteo_hour_unknown",
        ),
    ],
)
def test_weather_silence_detection(pkt, expected, reason_fragment):
    result = check_weather_silence(pkt, staleness_hours=3.0, now=NOW)
    assert isinstance(result, WeatherSilenceResult)
    assert result.is_silence is expected
    if reason_fragment:
        assert any(reason_fragment in r for r in result.reasons)
    assert is_weather_silence(pkt, staleness_hours=3.0, now=NOW) is expected


def test_buoy_only_loss_does_not_trigger_silence():
    pkt = {
        "open_meteo_failed": False,
        "open_meteo_hour_utc": "2026-07-21T19:30:00+00:00",
        "cloud_cover": 100,
        "visibility": 20000,
        "weather_code": 3,
        "wave_ht_sig": None,
        "wave_source": "null",
    }
    assert is_weather_silence(pkt, staleness_hours=3.0, now=NOW) is False
