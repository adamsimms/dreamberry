# M2 — Dream engine (SDXL + ControlNet + real-frame anchor)

Implements brief [DREAMBERRY.md](DREAMBERRY.md) §3 and §6 (issues #7, #8).

## The dial-0 lock

Every dream is built on a **real morning**:

1. **Weather-nearest anchor** (`dream/anchor.py`) — the M1 `WeatherNNIndex` picks a
   same-season Cloudberry frame matching the packet; used as the **img2img init**
   and the **IP-Adapter** atmosphere source. Falls back to the canonical frame.
2. **ControlNet depth + soft-edge** (`dream/controls.py`) — extracted from the
   **canonical geometry frame** only, locking rocks / horizon / cabin-edge.
3. **IP-Adapter** — carries the anchor's palette/atmosphere.
4. **LoRA** — optional mid-dial identity reservoir (follow-on). `lora_path: null`
   by default; the dial-0 lock relies on anchor + ControlNet, not LoRA, by design.

Output is SDXL-native 4:3 (`1024x768`); SUPIR upscale to ~4000x3000 is M4.

## Dream dial (0-10)

`dream/dial.py` is the single source of truth for the §6 schedule (interpolated
between anchor points). As the dial rises, denoise + LoRA weight climb while the
ControlNet/IP-Adapter grip loosens — the ghost drifting off the rocks. At dial 10
a deliberate seeded defocus renders the dissolve. **Public launch is locked to
artist-only, dial = 0.**

| dial | denoise | controlnet | ip-adapter | lora | defocus |
|---|---|---|---|---|---|
| 0 | 0.35 | 0.90 | 0.70 | 0.20 | 0.0 |
| 2 | 0.50 | 0.75 | 0.60 | 0.40 | 0.0 |
| 5 | 0.70 | 0.50 | 0.40 | 0.60 | 0.0 |
| 8 | 0.85 | 0.30 | 0.20 | 0.80 | 0.0 |
| 10 | 0.95 | 0.10 | 0.05 | 1.00 | 1.0 |

## Setup

```bash
.venv/bin/pip install -r requirements-dream.txt
```

Models are all currently ungated (see `config/dream.yaml`). An optional HuggingFace
token avoids rate-limit stalls — put `HF_TOKEN=...` in `.env` (gitignored) or run
`huggingface-cli login`. First run downloads SDXL base + ControlNets + IP-Adapter +
annotators (~several GB, cached).

Device is auto-detected (cuda / mps / cpu). On Apple Silicon (MPS) a 1024x768,
30-step dial-0 still takes ~60-80s. Attention slicing is disabled when IP-Adapter
is active (diffusers 0.39 incompatibility); VAE slicing stays on.

## Generate

```bash
# dial-0 from an archive weather packet
PYTHONPATH=. .venv/bin/python scripts/dream_generate.py \
  --packet data/weather/2017-09-18T09:59:44.000Z_GOPR2537.JPG.json --dial 0 --seed 1234

# dial sweep
PYTHONPATH=. .venv/bin/python scripts/dream_generate.py \
  --packet data/weather/<packet>.json --dials 0 2 5 8 10 --seed 1234
```

Each run writes `data/dream/outputs/<TIMESTAMP>_DREAM<###>.JPG` and a matching JSON
provenance sidecar. Dreams are named like the Cloudberry archive itself
(`TIMESTAMP_GOPR####.JPG` → `TIMESTAMP_DREAM###.JPG`): `TIMESTAMP` is the instant
being dreamed (the weather packet's `exif_iso`), and `DREAM###` is an
auto-incrementing roll counter across the outputs dir. The sidecar carries the
weather packet, seed, dial params, prompt, anchor id, edge-crop, model versions,
and device (validator scores + failure mode reserved for M3/M5). Saved as JPEG
q95 4:4:4 to match the archive medium. Outputs and cached control maps live under
`data/dream/` (gitignored).

## Tests

```bash
PYTHONPATH=. .venv/bin/python -m pytest dream/tests -q
```

Covers the dial schedule: exact anchor points, interpolation, monotonic trends,
clamping, and the dial-0 no-dissolve guarantee.
