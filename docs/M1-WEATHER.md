# M1 — Weather conditioning (dataset captions)

## Package

`weather_schema/` implements [DREAMBERRY-WEATHER-SCHEMA.md](DREAMBERRY-WEATHER-SCHEMA.md):

- `compose_prompt(pkt)` — fixed-slot prompt (issue #5)
- `feature_vector(pkt)` / `weighted_distance` — 9-feature retrieval helpers (issue #6)
- `WeatherNNIndex` — season-gated nearest-neighbor index over archive frames (issue #6)

Symmetry: the same functions run on ERA5 archive packets (captioning) and live forecast packets (inference).

## Tests

```bash
PYTHONPATH=. pytest weather_schema/tests -q
```

Worked examples A–E from the schema doc are asserted exactly.

## Caption curated set

Requires M0 weather packets under `data/weather/` and curated JSONL.

```bash
PYTHONPATH=. python scripts/caption_dataset.py
# → data/captions/captions.jsonl
```

Re-run after weather re-fetch or schema threshold changes.

## Weather NN index (issue #6)

Build the retrieval index from caption feature vectors (preferred):

```bash
PYTHONPATH=. python scripts/build_weather_nn_index.py
# → data/captions/weather_nn_index.json
```

Rebuild vectors from weather packets instead of stored captions:

```bash
PYTHONPATH=. python scripts/build_weather_nn_index.py --from-weather
```

Query smoke test (top-5 same-season neighbors for a weather packet):

```bash
PYTHONPATH=. python scripts/build_weather_nn_index.py \
  --query data/weather/2017-08-16T08:00:36.000Z_GOPR1957.JPG.json \
  -k 5 --include-prompt
```

Programmatic use:

```python
from weather_schema.retrieve import WeatherNNIndex

index = WeatherNNIndex.load("data/captions/weather_nn_index.json")
hits = index.query(live_packet, k=5, include_prompt=True)
# → [{"filename": "...", "distance": 0.12, "prompt": "..."}, ...]
```

Season gate (§4.3): candidates are filtered to the query's season family *before*
distance is computed (`late winter` ↔ {winter, spring}; autumn ↔ late autumn; never
summer↔winter). Missing features use null-drop-renormalize via `weighted_distance` (§4.4).
