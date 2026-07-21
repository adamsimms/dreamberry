# Dreamberry M4 — Hourly pipeline status

M4 covers the live hourly inference path. This document tracks what landed in the
repo and what remains for follow-on issues.

---

## Issue #13 — Live weather agent ✅

**Module:** `weather_schema/live.py`  
**Config:** `config/weather.yaml` (+ cabin coords from `config/dataset.yaml`)  
**CLI:** `scripts/fetch_live_weather.py`

### What it does

Builds an hourly **live** condition packet with the same field names as archive ERA5
packets so `compose_prompt`, `feature_vector`, and `WeatherNNIndex` stay symmetric.

| Source | Role |
|---|---|
| Open-Meteo Forecast @ cabin | Primary — all core hourly variables |
| ECCC Pool's Island WYI | Temperature (primary); wind fallback when Open-Meteo wind is null |
| SmartAtlantic Bonavista ERDDAP (`SMA_bonavista`) | `wave_ht_sig` when recent data exists |
| Computed (`weather_schema/solar.py`) | `solar_elevation`, `month`, `after_solar_noon` |

### Weather silence (detection only)

`is_weather_silence(pkt)` / `check_weather_silence(pkt)` implement schema §6.2:

- Staleness: Open-Meteo hour older than tolerance (default 3 h) or fetch failed
- Core-field loss: `cloud_cover`, `visibility`, and `weather_code` all null
- Buoy-only loss does **not** trigger silence

**Not wired into generation** — issue #14 will connect silence → hold behavior.

### CLI

```bash
# Print live packet JSON to stdout
PYTHONPATH=. .venv/bin/python scripts/fetch_live_weather.py

# Write data/live/current.json (gitignored)
PYTHONPATH=. .venv/bin/python scripts/fetch_live_weather.py --write

# Skip enrichments (Open-Meteo only)
PYTHONPATH=. .venv/bin/python scripts/fetch_live_weather.py --no-wyi --no-buoy
```

Exit code `2` when weather silence would trigger (packet still printed/written).

### Known gaps

- **WYI:** HTML scrape of ECCC past-24h page — best-effort; fragile if GC changes markup
- **Buoy:** ERDDAP `SMA_bonavista` may have no recent rows (dataset historically 2017–2018);
  returns `wave_ht_sig: null` with `wave_source: "null"` — never invented

---

## Issue #15 — Provenance sidecar ✅

**Module:** `dream/sidecar.py`  
**Docs:** [M4-SIDECAR.md](M4-SIDECAR.md)

Formal typed schema (`ProvenanceSidecar`), `build_sidecar()`, `validate_sidecar()`,
`write_sidecar()`. `DreamEngine` refactored to use the shared builder; CLI still writes
`<TIMESTAMP>_DREAM###.json` beside each JPG.

Hooks for #14: optional `validator_scores` and `failure_mode` (default `null`).

---

## Not in this milestone

| Issue | Title | Owner / status |
|---|---|---|
| **#14** | Hourly generate + gate wiring | Opus — connects live fetch, silence hold, validators |
| **#12** | SUPIR upscale | Deferred |

---

## Tests

```bash
PYTHONPATH=. .venv/bin/python -m pytest weather_schema/tests/test_live.py dream/tests/test_sidecar.py -q
```

Optional live smoke (network):

```bash
PYTHONPATH=. .venv/bin/python scripts/fetch_live_weather.py | head
```
