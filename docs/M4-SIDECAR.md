# Dreamberry M4 — Provenance sidecar schema (issue #15)

Every generated still writes a JSON sidecar beside the PNG (`<TIMESTAMP>_DREAM###.json`).
The sidecar is the canonical provenance record for the public details drawer and the
private forgetting dataset.

Built by `dream/sidecar.py` — `DreamEngine.generate()` calls `build_sidecar()` via
`dream/pipeline.py`. The CLI (`scripts/dream_generate.py`) adds `dream_id` and writes
via `write_sidecar()`.

---

## Top-level fields

| Field | Type | Required | When null | Notes |
|---|---|---|---|---|
| `generated_at` | ISO-8601 UTC string | yes | never | Wall-clock time the frame was generated |
| `labeled` | string | yes | never | Always `"generated"` — honesty label for the details drawer |
| `dream_id` | string | no | pre-build | Set by CLI: `{timestamp}_DREAM{nnn}` matching the JPG basename |
| `dial` | float 0–10 | yes | never | Resolved dream dial position |
| `dial_params` | object | yes | never | Full dial schedule output (see below) |
| `prompt` | string | yes | never | Exact `compose_prompt()` string fed to the model |
| `seed` | integer | yes | never | Torch generator seed |
| `width` | integer | yes | never | Output pixels (published frame; SDXL-native when hourly upscale is off) |
| `height` | integer | yes | never | Output pixels |
| `edge_crop` | object | no | when zero | Fractional insets applied before resize (GoPro fisheye trim) |
| `anchor_frame` | string | yes | never | Cloudberry filename used as img2img / IP-Adapter init |
| `anchor_source` | string | yes | never | `"weather_nn"` or `"canonical_fallback"` |
| `anchor_distance` | float | no | canonical fallback | Weighted NN distance when `anchor_source` is `weather_nn` |
| `models` | object | yes | never | Model + LoRA versions (see below) |
| `device` | string | no | — | Resolved runtime device (`cpu`, `cuda`, `mps`) |
| `dtype` | string | no | — | Torch dtype used for inference |
| `weather_packet` | object | yes | never | Full condition packet (archive or live shape) |
| `validator_scores` | object | no | until #14 | Quality-gate scores; `null` until hourly validators wire in |
| `failure_mode` | string | no | until #14 | e.g. `"weather_silence"`, `"signal_lost"`; `null` on success |

---

## `dial_params` object

| Field | Type | Description |
|---|---|---|
| `dial` | float | Same as top-level `dial` |
| `denoise_strength` | float | img2img strength |
| `controlnet_scale` | float | Combined ControlNet scale multiplier |
| `ip_adapter_scale` | float | IP-Adapter atmosphere weight |
| `lora_scale` | float | LoRA weight (reported even when no LoRA loaded) |
| `defocus_strength` | float | Seeded defocus at high dial (0 below dial 8) |

Source of truth for the schedule: `dream/dial.py`.

---

## `models` object

| Field | Type | Description |
|---|---|---|
| `base` | string | SDXL base model ID |
| `vae` | string | VAE checkpoint ID |
| `controlnet_depth` | string | Depth ControlNet ID |
| `controlnet_softedge` | string | Soft-edge ControlNet ID |
| `ip_adapter` | string \| null | `"repo/weight"` when IP-Adapter active |
| `lora` | string \| null | Repo-relative LoRA path when loaded |
| `has_lora` | boolean | Whether a LoRA was applied |

---

## `weather_packet` object

Same schema as archive packets under `data/weather/` plus live-only metadata when
fetched via `scripts/fetch_live_weather.py`:

- Core conditioning fields: `cloud_cover`, `visibility`, `weather_code`,
  `relative_humidity_2m`, `wind_speed_10m`, `wind_direction_10m`,
  `shortwave_radiation`, `temperature_2m`, `precipitation`, `wave_ht_sig`
- Computed: `solar_elevation`, `month`, `after_solar_noon`, `timezone`,
  `latitude`, `longitude`
- Live provenance: `source`, `fetched_at`, `temperature_source`, `wind_source`,
  `wave_source`, optional `staleness_hours`, `weather_silence`

See [DREAMBERRY-WEATHER-SCHEMA.md](DREAMBERRY-WEATHER-SCHEMA.md) for field semantics.

---

## Validation

`validate_sidecar(sidecar) -> list[str]` returns human-readable errors (empty when valid).
`write_sidecar(path, sidecar)` validates before writing.

---

## Example (truncated)

```json
{
  "generated_at": "2026-07-21T20:31:00+00:00",
  "labeled": "generated",
  "dream_id": "2026-07-21T20:30:00.000Z_DREAM001",
  "dial": 0.0,
  "dial_params": {
    "dial": 0.0,
    "denoise_strength": 0.35,
    "controlnet_scale": 0.9,
    "ip_adapter_scale": 0.7,
    "lora_scale": 0.2,
    "defocus_strength": 0.0
  },
  "prompt": "cldbry window view of Pinchard's Island, Newfoundland, summer, daytime, ...",
  "seed": 42,
  "width": 1024,
  "height": 768,
  "anchor_frame": "2017-09-18T09:59:44.000Z_GOPR2537.JPG",
  "anchor_source": "weather_nn",
  "anchor_distance": 0.12,
  "validator_scores": null,
  "failure_mode": null,
  "weather_packet": { "...": "..." }
}
```
