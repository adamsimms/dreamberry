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

Wired into generation by **issue #14** below (silence → hold).

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

## Issue #14 — Hourly generate + gate wiring ✅

**Modules:** `dream/hourly.py`, `dream/gates/evaluate.py`  
**Config:** `config/hourly.yaml` (+ `config/gates.yaml`, `config/dream.yaml`, `config/weather.yaml`)  
**CLI:** `scripts/dream_hourly.py`

### What it does

One tick — `run_hourly(dial=0.0)` — assembles the live packet (#13), generates
through the M2 engine, runs the M3 gates (`evaluate_frame`), and maps the outcome
to the three brief failure modes (DREAMBERRY.md §7), writing the public window +
private archive locally (R2/Pages delivery is M5).

### Failure-mode mapping

| Condition | Outcome | `failure_mode` | Pointer |
|---|---|---|---|
| Weather silence (stale/dead feeds) | **hold** — never generate | `weather_silence` | untouched |
| Season lock refuses (warm-in-cold) | retry; then **hold** last good | `null` (`hold_reason: season_lock`) | untouched |
| Identity collapse, dial < enforced | retry; then **hold** last good | `null` (`hold_reason: identity_collapse`) | untouched |
| Identity collapse, dial ≥ enforced | **publish** — honored dissolve | `identity_collapse` | **moves** |
| Clean frame passes both gates | **publish** | `null` | **moves** |
| Every attempt throws (no frame) | **signal lost** — noise field | `signal_lost` | noise; `last_success_at` preserved |

The per-frame `pass`/`retry` mapping (`frame_decision`) is pure and unit-tested;
season refusal is a hard ethic that blocks publish at any dial (no summer-green
February). Published frames get `validator_scores` (DINOv2 kNN distance, horizon
displacement, nearest real frames, collapse + season verdicts) in the sidecar.

`status.json` (public): `updated_at`, `hold`, `failure_mode`, `hold_reason`,
`last_success_at`, `last_success_dream_id`, `current`, `dream_id`, `dial`,
`attempts`, `reasons`. A hold points `current` at the last successful dream
(`current.webp`), never at a `signal_lost` noise field — see M5-PLATFORM §#19.

### CLI

```bash
# live weather, dial-0 public default (needs GPU + gate refs)
PYTHONPATH=. .venv/bin/python scripts/dream_hourly.py

# replay an archive packet (no network); still generates
PYTHONPATH=. .venv/bin/python scripts/dream_hourly.py --packet data/weather/<frame>.json

# decide only, no artifacts written
PYTHONPATH=. .venv/bin/python scripts/dream_hourly.py --packet <pkt.json> --dry-run
```

Requires the M3 gate references (`scripts/build_gates_refs.py`) for the real path.
Artifacts land under `config/hourly.yaml:paths` (`data/dream/`, gitignored).

---

## Not in this milestone

| Issue | Title | Owner / status |
|---|---|---|
| **#12** | SUPIR upscale | Deferred |
| **#16–#19** | Modal cron + R2/Pages delivery, dead-man switch | M5 |

---

## Tests

```bash
PYTHONPATH=. .venv/bin/python -m pytest \
  weather_schema/tests/test_live.py dream/tests/test_sidecar.py dream/tests/test_hourly.py -q
```

`test_hourly.py` fakes the engine + gates, so it covers the full decision matrix
(silence hold, publish, honored dissolve, persistent-collapse hold, season hold,
retry-then-accept, signal lost) without any downloads or GPU.

Optional live smoke (network):

```bash
PYTHONPATH=. .venv/bin/python scripts/fetch_live_weather.py | head
```
