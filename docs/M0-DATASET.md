# M0 — Dataset pipeline

Curated Cloudberry JPEGs, verified EXIF timestamps, and Open-Meteo ERA5 historical weather packets for Dreamberry training (M1+).

**Spec:** [DREAMBERRY.md §8](DREAMBERRY.md) (curation) and [DREAMBERRY-WEATHER-SCHEMA.md](DREAMBERRY-WEATHER-SCHEMA.md) (weather fields).

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_m0.py
```

Or step-by-step:

```bash
python scripts/download_images.py    # → data/raw/
python scripts/build_manifest.py     # → data/manifest.json
python scripts/curate_dataset.py     # → data/curated/day.jsonl, night.jsonl
python scripts/fetch_weather.py      # → data/weather/*.json, index.json
```

Catalog source: `../pinchards.is/data/catalog.json` (1,652 photos). CDN: `https://cloudberry-images.adamsimms.xyz/`.

## Config

| File | Purpose |
|---|---|
| `config/dataset.yaml` | Cabin coords, canonical frame, curation thresholds, paths |
| `config/canonical_frame.txt` | Geometry master filename |

**Cabin:** 49.2026°N, 53.4859°W · timezone `America/St_Johns`  
**Canonical frame:** `2017-09-18T09:59:44.000Z_GOPR2537.JPG`

## Curation rules

### Exclusions

- **Hard exclude (training + retrieval):** `2018-02-26T11:54:20.000Z_GOPR4086.JPG` (indoor selfie)
- **Malfunction/manual-test bursts:** kept (real window views)
- **Cabin shadows:** kept
- **Fisheye:** kept native (4000×3000, 4:3)

### Night bucket

**Method:** solar elevation at cabin coordinates (via `astral`), not clock time.

- **Night** when solar elevation **< −6°** (civil twilight end, USNO definition)
- **Dawn/dusk** (elevation ≥ −6°) stay in the **day** bucket — golden-hour frames remain in main training set
- Night is experimental; may be dropped from public release later

### Dedupe

**Method:** perceptual hash (`imagehash.phash`), Hamming distance ≤ 5 within the same **local calendar day** (`America/St_Johns`) and bucket.

- First frame in a near-duplicate cluster → `weight: 1.0`, `dedupe_representative: true`
- Subsequent near-duplicates → `weight: 0.25` (downweighted, not dropped — preserves weather extremes)
- Goal: reduce calm-afternoon dominance without destroying diversity

### Time source

**Authoritative:** EXIF `DateTimeOriginal` re-read from each JPEG.  
Catalog `captureDateIso` is compared; deltas > 2 s are logged in `manifest.exif_mismatches`.

## Weather packets

**Source:** [Open-Meteo Historical / ERA5 Archive API](https://open-meteo.com/en/docs/historical-weather-api) at cabin lat/lon, paired to EXIF local hour.

**Fields fetched** (per DREAMBERRY-WEATHER-SCHEMA §1):

| Field | Notes |
|---|---|
| `cloud_cover` | % |
| `visibility` | m |
| `weather_code` | WMO 4677 |
| `relative_humidity_2m` | % |
| `wind_speed_10m` | km/h |
| `wind_direction_10m` | ° (retrieval-only in v1) |
| `shortwave_radiation` | W/m² (retrieval tie-breaker) |
| `temperature_2m` | °C (weak atmosphere modifier) |
| `precipitation` | mm (retrieval tie-breaker) |
| `solar_elevation` | computed locally from EXIF + coords |
| `wave_ht_sig` | null at M0 (buoy history deferred; sea-state slot omitted in captions) |

One JSON file per frame under `data/weather/<filename>.json`; summary in `data/weather/index.json`.

## Outputs (committed)

| Path | Git | Description |
|---|---|---|
| `data/raw/` | **ignored** | Downloaded JPEGs (~8 GB) |
| `data/manifest.json` | committed | Full catalog + EXIF verification |
| `data/curated/day.jsonl` | committed | Day-bucket training-eligible frames |
| `data/curated/night.jsonl` | committed | Night-bucket (experimental) |
| `data/curated/summary.json` | committed | Counts + method documentation |
| `data/weather/` | committed | Per-frame ERA5 packets + index |

## Run statistics

_Last pipeline run: 2026-07-21._

| Metric | Count |
|---|---|
| Catalog photos | 1,652 |
| Downloaded (raw) | 1,652 (8.2 GB on disk, gitignored) |
| EXIF OK | 1,652 |
| EXIF vs catalog mismatch (>2 s) | 1 (`2017-08-18T18:00:58.000Z_GOPR2000.JPG` — 3600 s; EXIF authoritative) |
| All 4000×3000 4:3 | 1,652 |
| Excluded (selfie) | 1 |
| Day bucket | 1,367 (1,194 dedupe representatives, 173 downweighted) |
| Night bucket | 284 (259 representatives, 25 downweighted) |
| Training-eligible total | 1,651 |
| Weather packets (ERA5) | 1,651 / 1,651 |

## Issues

- #2 Download + EXIF verification
- #3 Curation (dedupe, night, 4:3)
- #4 Historical weather (ERA5)
