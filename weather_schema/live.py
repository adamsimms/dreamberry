"""Live weather packet builder + weather-silence detection (M4 / issue #13).

Symmetry contract: output matches archive packet field names so compose_prompt,
feature_vector, and WeatherNNIndex work unchanged at inference time.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

import requests
import yaml

from weather_schema.solar import enrich_solar_fields

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_CONFIG_PATH = REPO_ROOT / "config" / "dataset.yaml"
WEATHER_CONFIG_PATH = REPO_ROOT / "config" / "weather.yaml"

_HOURLY_FIELDS = (
    "cloud_cover",
    "visibility",
    "weather_code",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "shortwave_radiation",
    "temperature_2m",
    "precipitation",
)

_WIND_CARDINALS: dict[str, float] = {
    "N": 0.0,
    "NNE": 22.5,
    "NE": 45.0,
    "ENE": 67.5,
    "E": 90.0,
    "ESE": 112.5,
    "SE": 135.0,
    "SSE": 157.5,
    "S": 180.0,
    "SSW": 202.5,
    "SW": 225.0,
    "WSW": 247.5,
    "W": 270.0,
    "WNW": 292.5,
    "NW": 315.0,
    "NNW": 337.5,
}

_WIND_RE = re.compile(
    r"^(?P<dir>[NSEW]{1,3})\s+(?P<speed>\d+)(?:\s+gusts\s+\d+)?$",
    re.IGNORECASE,
)
_TEMP_DECIMAL_RE = re.compile(r"\(([\d.]+)\)")


@dataclass(frozen=True)
class WeatherSilenceResult:
    """Structured weather-silence verdict (schema §6.2 — detection only)."""

    is_silence: bool
    reasons: list[str] = field(default_factory=list)
    staleness_hours: float | None = None
    open_meteo_failed: bool = False
    core_fields_missing: bool = False


def load_dataset_config(path: Path | str | None = None) -> dict[str, Any]:
    p = Path(path) if path else DATASET_CONFIG_PATH
    with open(p) as f:
        return yaml.safe_load(f)


def load_weather_config(path: Path | str | None = None) -> dict[str, Any]:
    p = Path(path) if path else WEATHER_CONFIG_PATH
    with open(p) as f:
        return yaml.safe_load(f)


def _at(hourly: dict[str, Any], key: str, idx: int) -> Any:
    vals = hourly.get(key)
    if vals is None or idx >= len(vals):
        return None
    return vals[idx]


def _parse_local_hour(time_local: str, tz_name: str) -> datetime:
    """Parse Open-Meteo local hour label into timezone-aware datetime."""
    dt_naive = datetime.strptime(time_local, "%Y-%m-%dT%H:%M")
    return dt_naive.replace(tzinfo=ZoneInfo(tz_name))


def fetch_open_meteo_forecast(
    session: requests.Session,
    dataset_cfg: Mapping[str, Any],
    weather_cfg: Mapping[str, Any],
    *,
    now: datetime | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Fetch the current-hour Open-Meteo forecast row for the cabin."""
    live = weather_cfg["live"]
    api = live["forecast_api"]
    variables = ",".join(dataset_cfg["weather"]["hourly_variables"])
    tz_name = dataset_cfg["cabin"]["timezone"]
    params = {
        "latitude": dataset_cfg["cabin"]["latitude"],
        "longitude": dataset_cfg["cabin"]["longitude"],
        "hourly": variables,
        "wind_speed_unit": dataset_cfg["weather"]["wind_speed_unit"],
        "timezone": tz_name,
        "forecast_days": int(live.get("forecast_days", 2)),
    }
    meta: dict[str, Any] = {"open_meteo_failed": False, "open_meteo_error": None}
    try:
        resp = session.get(api, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        meta["open_meteo_failed"] = True
        meta["open_meteo_error"] = str(exc)
        return None, meta

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    if not times:
        meta["open_meteo_failed"] = True
        meta["open_meteo_error"] = "empty hourly.time"
        return None, meta

    now = now or datetime.now(timezone.utc)
    dt_local_now = now.astimezone(ZoneInfo(tz_name))
    target_label = dt_local_now.strftime("%Y-%m-%dT%H:00")

    idx = None
    for i, t in enumerate(times):
        if t == target_label:
            idx = i
            break
    if idx is None:
        # Fall back to the nearest hour at or before now.
        best_i = 0
        best_dt = _parse_local_hour(times[0], tz_name)
        for i, t in enumerate(times):
            dt = _parse_local_hour(t, tz_name)
            if dt <= dt_local_now.replace(minute=0, second=0, microsecond=0):
                best_i = i
                best_dt = dt
        idx = best_i
        target_label = times[idx]
        hour_dt = best_dt
    else:
        hour_dt = _parse_local_hour(target_label, tz_name)

    pkt = {
        "time_local": target_label,
        "cloud_cover": _at(hourly, "cloud_cover", idx),
        "visibility": _at(hourly, "visibility", idx),
        "weather_code": _at(hourly, "weather_code", idx),
        "relative_humidity_2m": _at(hourly, "relative_humidity_2m", idx),
        "wind_speed_10m": _at(hourly, "wind_speed_10m", idx),
        "wind_direction_10m": _at(hourly, "wind_direction_10m", idx),
        "shortwave_radiation": _at(hourly, "shortwave_radiation", idx),
        "temperature_2m": _at(hourly, "temperature_2m", idx),
        "precipitation": _at(hourly, "precipitation", idx),
        "open_meteo_time_local": target_label,
        "open_meteo_hour_utc": hour_dt.astimezone(timezone.utc).isoformat(),
    }
    meta["open_meteo_time_local"] = target_label
    meta["open_meteo_hour_utc"] = pkt["open_meteo_hour_utc"]
    return pkt, meta


def _parse_wyi_temperature(raw: str) -> float | None:
    text = re.sub(r"\s+", " ", raw.replace("\xa0", " ")).strip()
    m = _TEMP_DECIMAL_RE.search(text)
    if m:
        return float(m.group(1))
    head = text.split()[0] if text else ""
    try:
        return float(head)
    except ValueError:
        return None


def _parse_wyi_wind(raw: str) -> tuple[float | None, float | None]:
    text = re.sub(r"\s+", " ", raw.replace("\xa0", " ")).strip()
    m = _WIND_RE.match(text)
    if not m:
        return None, None
    speed = float(m.group("speed"))
    direction = _WIND_CARDINALS.get(m.group("dir").upper())
    return speed, direction


def fetch_wyi_observation(
    session: requests.Session,
    weather_cfg: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Best-effort scrape of the latest WYI hourly observation (ECCC HTML)."""
    wyi = weather_cfg["live"]["wyi"]
    url = wyi["past_conditions_url"]
    params = {"station": wyi["station_code"]}
    try:
        resp = session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except Exception:  # noqa: BLE001
        return None

    tbody = re.search(r"<tbody>(.*?)</tbody>", html, re.S)
    if not tbody:
        return None

    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", tbody.group(1), re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(cells) < 5:
            continue
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
        time_label = cells[0]
        if not re.match(r"\d{1,2}:\d{2}", time_label):
            continue
        temp = _parse_wyi_temperature(cells[2])
        wind_speed, wind_dir = _parse_wyi_wind(cells[4])
        if temp is None and wind_speed is None:
            continue
        return {
            "temperature_2m": temp,
            "wind_speed_10m": wind_speed,
            "wind_direction_10m": wind_dir,
            "wyi_time_local": time_label,
            "wyi_source_url": resp.url,
        }
    return None


def fetch_buoy_wave_ht_sig(
    session: requests.Session,
    weather_cfg: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Fetch the most recent significant wave height from SmartAtlantic ERDDAP."""
    buoy = weather_cfg["live"]["buoy"]
    lookback = int(buoy.get("lookback_hours", 6))
    url = (
        f"{buoy['erddap_base']}/{buoy['dataset']}.json"
        f"?wave_ht_sig,time&time>=now-{lookback}hours"
    )
    try:
        resp = session.get(url, timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
    except Exception:  # noqa: BLE001
        return None

    rows = data.get("table", {}).get("rows", [])
    if not rows:
        return None

    wave_ht_sig = None
    observed_at = None
    for row in reversed(rows):
        if not row or len(row) < 2:
            continue
        val, ts = row[0], row[1]
        if val is None:
            continue
        try:
            wave_ht_sig = float(val)
        except (TypeError, ValueError):
            continue
        observed_at = ts
        break

    if wave_ht_sig is None:
        return None
    return {
        "wave_ht_sig": round(wave_ht_sig, 3),
        "buoy_time_utc": observed_at,
        "buoy_dataset": buoy["dataset"],
    }


def _merge_enrichments(
    base: dict[str, Any],
    *,
    wyi: dict[str, Any] | None,
    buoy: dict[str, Any] | None,
) -> dict[str, Any]:
    pkt = dict(base)
    enrichments: list[str] = []

    pkt["temperature_source"] = "open-meteo"
    pkt["wind_source"] = "open-meteo"
    pkt["wave_source"] = "null"
    pkt["wave_ht_sig"] = None

    if wyi:
        enrichments.append("wyi")
        if wyi.get("temperature_2m") is not None:
            pkt["temperature_2m"] = wyi["temperature_2m"]
            pkt["temperature_source"] = "wyi"
        if pkt.get("wind_speed_10m") is None and wyi.get("wind_speed_10m") is not None:
            pkt["wind_speed_10m"] = wyi["wind_speed_10m"]
            pkt["wind_source"] = "wyi"
            if wyi.get("wind_direction_10m") is not None:
                pkt["wind_direction_10m"] = wyi["wind_direction_10m"]
        pkt["wyi_time_local"] = wyi.get("wyi_time_local")
        pkt["wyi_source_url"] = wyi.get("wyi_source_url")

    if buoy and buoy.get("wave_ht_sig") is not None:
        enrichments.append("buoy")
        pkt["wave_ht_sig"] = buoy["wave_ht_sig"]
        pkt["wave_source"] = "buoy"
        pkt["buoy_time_utc"] = buoy.get("buoy_time_utc")
        pkt["buoy_dataset"] = buoy.get("buoy_dataset")

    source = "open-meteo-forecast"
    if enrichments:
        source = f"{source}+{'+'.join(enrichments)}"
    pkt["source"] = source
    return pkt


def build_live_packet(
    *,
    dataset_cfg: Mapping[str, Any] | None = None,
    weather_cfg: Mapping[str, Any] | None = None,
    session: requests.Session | None = None,
    now: datetime | None = None,
    fetch_wyi: bool = True,
    fetch_buoy: bool = True,
) -> dict[str, Any]:
    """Assemble a live condition packet for inference."""
    dataset_cfg = dataset_cfg or load_dataset_config()
    weather_cfg = weather_cfg or load_weather_config()
    now = now or datetime.now(timezone.utc)
    fetched_at = now.isoformat()

    own_session = session is None
    session = session or requests.Session()
    try:
        om_row, om_meta = fetch_open_meteo_forecast(
            session, dataset_cfg, weather_cfg, now=now
        )

        base: dict[str, Any] = {}
        if om_row:
            base.update({k: om_row[k] for k in _HOURLY_FIELDS if k in om_row})
            base["time_local"] = om_row["time_local"]
            base["open_meteo_time_local"] = om_row.get("open_meteo_time_local")
            base["open_meteo_hour_utc"] = om_row.get("open_meteo_hour_utc")
        else:
            base["time_local"] = now.astimezone(
                ZoneInfo(dataset_cfg["cabin"]["timezone"])
            ).strftime("%Y-%m-%dT%H:00")

        base.update(enrich_solar_fields(dataset_cfg, now))

        wyi = fetch_wyi_observation(session, weather_cfg) if fetch_wyi else None
        buoy = fetch_buoy_wave_ht_sig(session, weather_cfg) if fetch_buoy else None
        pkt = _merge_enrichments(base, wyi=wyi, buoy=buoy)

        pkt["fetched_at"] = fetched_at
        pkt["open_meteo_failed"] = bool(om_meta.get("open_meteo_failed"))
        if om_meta.get("open_meteo_error"):
            pkt["open_meteo_error"] = om_meta["open_meteo_error"]

        silence = check_weather_silence(
            pkt,
            staleness_hours=float(weather_cfg["live"].get("staleness_hours", 3.0)),
            now=now,
        )
        pkt["staleness_hours"] = silence.staleness_hours
        pkt["weather_silence"] = silence.is_silence
        pkt["weather_silence_reasons"] = silence.reasons
        return pkt
    finally:
        if own_session:
            session.close()


def _core_fields_missing(pkt: Mapping[str, Any]) -> bool:
    return (
        pkt.get("cloud_cover") is None
        and pkt.get("visibility") is None
        and pkt.get("weather_code") is None
    )


def _open_meteo_staleness_hours(
    pkt: Mapping[str, Any],
    *,
    now: datetime,
) -> float | None:
    hour_utc = pkt.get("open_meteo_hour_utc")
    if not hour_utc:
        time_local = pkt.get("open_meteo_time_local") or pkt.get("time_local")
        tz_name = pkt.get("timezone")
        if time_local and tz_name:
            try:
                hour_utc = (
                    _parse_local_hour(time_local, tz_name)
                    .astimezone(timezone.utc)
                    .isoformat()
                )
            except ValueError:
                return None
        else:
            return None
    try:
        hour_dt = datetime.fromisoformat(str(hour_utc).replace("Z", "+00:00"))
    except ValueError:
        return None
    if hour_dt.tzinfo is None:
        hour_dt = hour_dt.replace(tzinfo=timezone.utc)
    delta = now - hour_dt.astimezone(timezone.utc)
    return max(0.0, delta.total_seconds() / 3600.0)


def check_weather_silence(
    pkt: Mapping[str, Any],
    *,
    staleness_hours: float = 3.0,
    now: datetime | None = None,
) -> WeatherSilenceResult:
    """Detect weather silence per schema §6.2 (detection only — #14 wires action)."""
    now = now or datetime.now(timezone.utc)
    reasons: list[str] = []
    open_meteo_failed = bool(pkt.get("open_meteo_failed"))
    core_missing = _core_fields_missing(pkt)
    stale_hours = _open_meteo_staleness_hours(pkt, now=now)

    if open_meteo_failed:
        reasons.append("open_meteo_fetch_failed")
    if stale_hours is not None and stale_hours > staleness_hours:
        reasons.append(f"open_meteo_stale>{staleness_hours}h")
    elif open_meteo_failed:
        pass
    elif stale_hours is None and open_meteo_failed:
        reasons.append("open_meteo_hour_unknown")
    if core_missing:
        reasons.append("core_fields_missing")

    is_silence = bool(reasons)
    return WeatherSilenceResult(
        is_silence=is_silence,
        reasons=reasons,
        staleness_hours=stale_hours,
        open_meteo_failed=open_meteo_failed,
        core_fields_missing=core_missing,
    )


def is_weather_silence(
    pkt: Mapping[str, Any],
    *,
    staleness_hours: float = 3.0,
    now: datetime | None = None,
) -> bool:
    """Return True when weather silence should withhold generation (schema §6.2)."""
    return check_weather_silence(
        pkt, staleness_hours=staleness_hours, now=now
    ).is_silence


def weather_silence_to_dict(result: WeatherSilenceResult) -> dict[str, Any]:
    return asdict(result)
