"""Private archive browse index (issue #37).

Builds ``archive/studio/index.json``: newest-first dream summaries for the
Access-gated studio UI. Object PNGs/sidecars stay at ``archive/<id>.{png,json}``.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from dream.storage import ARCHIVE_PREFIX, R2Store
from dream.thumbs import thumb_key

__all__ = [
    "STUDIO_PREFIX",
    "INDEX_KEY",
    "entry_from_dream_id",
    "entry_from_sidecar",
    "build_index_document",
    "list_archive_dream_ids",
    "rebuild_archive_index",
    "upsert_archive_index_entry",
]

STUDIO_PREFIX = f"{ARCHIVE_PREFIX}studio/"
INDEX_KEY = f"{STUDIO_PREFIX}index.json"
CABIN_TZ = ZoneInfo("America/St_Johns")

# Skip studio UI keys and non-frame artifacts (e.g. *_4k.png).
_DREAM_JSON_RE = re.compile(
    r"^archive/(?P<id>\d{4}-\d{2}-\d{2}T[^/]+_DREAM\d+)\.json$"
)
_WMO = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "slight snowfall",
    73: "moderate snowfall",
    75: "heavy snowfall",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    95: "thunderstorm",
}


def list_archive_dream_ids(store: R2Store) -> list[str]:
    """Dream ids that have an archive sidecar (not studio UI keys)."""
    ids: list[str] = []
    for key in store.list_keys(ARCHIVE_PREFIX):
        m = _DREAM_JSON_RE.match(key)
        if m:
            ids.append(m.group("id"))
    return ids


def _cabin_parts(iso: str | None) -> tuple[str | None, str | None, str | None]:
    """Return (day_key YYYY-MM-DD, time HH:MM, feed label) in cabin local time."""
    if not iso:
        return None, None, None
    raw = str(iso).strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None, None, None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(CABIN_TZ)
    day_key = local.strftime("%Y-%m-%d")
    time_hm = local.strftime("%H:%M")
    # Short column header: "16 Oct" (year only when not current calendar year).
    now = datetime.now(CABIN_TZ)
    day_num = str(local.day)
    mon = local.strftime("%b")
    if local.year == now.year:
        feed = f"{day_num} {mon}"
    else:
        feed = f"{day_num} {mon} {local.strftime('%y')}"
    return day_key, time_hm, feed


def _weather_summary(packet: Mapping[str, Any] | None) -> str | None:
    if not packet:
        return None
    parts: list[str] = []
    code = packet.get("weather_code")
    if code is not None:
        parts.append(_WMO.get(int(code), f"code {code}"))
    temp = packet.get("temperature_2m")
    if temp is not None:
        try:
            parts.append(f"{float(temp):.0f}°C")
        except (TypeError, ValueError):
            pass
    return ", ".join(parts) if parts else None


def entry_from_dream_id(dream_id: str) -> dict[str, Any]:
    """Lightweight browse row from the id alone (no sidecar fetch)."""
    when = dream_id.split("_DREAM")[0]
    day_key, time_hm, feed = _cabin_parts(when)
    return {
        "dream_id": dream_id,
        "generated_at": None,
        "dial": None,
        "failure_mode": None,
        "anchor_frame": None,
        "anchor_source": None,
        "weather_summary": None,
        "png": f"{ARCHIVE_PREFIX}{dream_id}.png",
        "json": f"{ARCHIVE_PREFIX}{dream_id}.json",
        "thumb": thumb_key(dream_id),
        "cabin_day": day_key,
        "cabin_time": time_hm,
        "cabin_feed": feed,
    }


def entry_from_sidecar(sidecar: Mapping[str, Any], *, dream_id: str) -> dict[str, Any]:
    """Compact browse row from a full provenance sidecar."""
    weather = sidecar.get("weather_packet") or {}
    # Prefer the weather hour (place-time) over wall-clock generate time.
    when = (
        weather.get("open_meteo_hour_utc")
        or weather.get("time_local")
        or sidecar.get("generated_at")
        or dream_id.split("_DREAM")[0]
    )
    day_key, time_hm, feed = _cabin_parts(str(when) if when else None)
    return {
        "dream_id": dream_id,
        "generated_at": sidecar.get("generated_at"),
        "dial": sidecar.get("dial"),
        "failure_mode": sidecar.get("failure_mode"),
        "anchor_frame": sidecar.get("anchor_frame"),
        "anchor_source": sidecar.get("anchor_source"),
        "weather_summary": _weather_summary(weather if isinstance(weather, Mapping) else None),
        "png": f"{ARCHIVE_PREFIX}{dream_id}.png",
        "json": f"{ARCHIVE_PREFIX}{dream_id}.json",
        "thumb": thumb_key(dream_id),
        "cabin_day": day_key,
        "cabin_time": time_hm,
        "cabin_feed": feed,
    }


def build_index_document(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Sort newest-first and wrap for the studio client."""

    def sort_key(e: Mapping[str, Any]) -> str:
        return str(e.get("dream_id") or "")

    ordered = sorted(entries, key=sort_key, reverse=True)
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(ordered),
        "newest_first": True,
        "entries": ordered,
    }


def rebuild_archive_index(
    store: R2Store,
    *,
    limit: int | None = None,
    enrich: bool = False,
) -> dict[str, Any]:
    """List archive dream ids → write ``archive/studio/index.json``.

    Default is key-derived rows (fast). Pass ``enrich=True`` to fetch each
    sidecar for dial / weather / failure fields (slow on large archives).
    Detail view still loads the full sidecar on demand.
    """
    ids = list_archive_dream_ids(store)
    ids.sort(reverse=True)
    if limit is not None:
        ids = ids[: max(0, int(limit))]
    entries: list[dict[str, Any]] = []
    for dream_id in ids:
        if enrich:
            sc = store.get_json(f"{ARCHIVE_PREFIX}{dream_id}.json")
            if not sc:
                continue
            entries.append(entry_from_sidecar(sc, dream_id=dream_id))
        else:
            entries.append(entry_from_dream_id(dream_id))
    doc = build_index_document(entries)
    store.put_json(INDEX_KEY, doc)
    return doc


def upsert_archive_index_entry(
    store: R2Store,
    *,
    dream_id: str,
    sidecar: Mapping[str, Any],
) -> dict[str, Any]:
    """Prepend/replace one entry without a full rescan (hourly path)."""
    existing = store.get_json(INDEX_KEY) or {}
    prev = list(existing.get("entries") or [])
    entry = entry_from_sidecar(sidecar, dream_id=dream_id)
    rest = [e for e in prev if e.get("dream_id") != dream_id]
    doc = build_index_document([entry, *rest])
    store.put_json(INDEX_KEY, doc)
    return doc
