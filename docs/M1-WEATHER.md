# M1 — Weather conditioning (dataset captions)

## Package

`weather_schema/` implements [DREAMBERRY-WEATHER-SCHEMA.md](DREAMBERRY-WEATHER-SCHEMA.md):

- `compose_prompt(pkt)` — fixed-slot prompt (issue #5)
- `feature_vector(pkt)` / `weighted_distance` — 9-feature retrieval helpers (issue #6)

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
