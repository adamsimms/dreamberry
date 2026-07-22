# Dreamberry

The dead [Cloudberry](https://art.adamsimms.xyz/cloudberry/archive/) camera **dreaming** — a labeled generative window on Pinchard's Island, Newfoundland, conditioned by live weather.

**Canonical:** [art.adamsimms.xyz/dreamberry](https://art.adamsimms.xyz/dreamberry)  
**Live window:** [art.adamsimms.xyz/dreamberry/window](https://art.adamsimms.xyz/dreamberry/window/)  
**Artist:** [Adam Simms](https://adamsimms.xyz)

A **sibling** to the Cloudberry archive, not an extension of it. The archive stays sacred and separate.

> Dreamberry asks: can a machine be present at a place it can no longer photograph — and is that a gift or a consolation prize?

## How it works

Every hour, Modal wakes an L40S GPU, pulls the island's real weather, finds the nearest real Cloudberry morning, and dreams a new frame of the same fixed view. Cloudflare R2 holds the private archive and the public pointer the window observes. The image is labeled **generated** in the details drawer — never on the picture itself.

```
                         Pinchard's Island (now)
                    Open-Meteo · WYI · SmartAtlantic
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Modal  (cron + L40S)                                                │
│                                                                      │
│   live weather ──► compose_prompt + weather-NN anchor                │
│                         │                                            │
│                         ▼                                            │
│   SDXL + ControlNet + IP-Adapter + dial                              │
│   (geometry from canonical frame; atmosphere from real morning)      │
│                         │                                            │
│                         ▼                                            │
│   quality gates ──► sidecar JSON ──► SUPIR upscale                   │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│  R2 private archive     │   │  R2 public pointer      │
│  archive/*.png + .json  │   │  current/current.webp   │
│                         │   │  current/status.json    │
└─────────────────────────┘   └───────────┬─────────────┘
                                          │ observe only
                                          ▼
                          ┌───────────────────────────────┐
                          │  art.adamsimms.xyz/dreamberry │
                          │  window + drawer + about      │
                          └───────────────────────────────┘

Hold (weather silence): leave current.webp; update status.json only
Signal lost (GPU/channel): publish static / noise; failure_mode set
```

**Weather is the only thing still true.** Rocks and cabin-edge are memory or invention; wind, fog, and sea are real, right now, at the island.

## Stack

| Layer | Choice |
|-------|--------|
| Generation | SDXL + ControlNet + IP-Adapter + weather-NN real-frame anchor (+ LoRA at mid-dial) |
| Compute / cron | [Modal](https://modal.com) (L40S, hourly) |
| Storage / CDN | Cloudflare R2 (`art-adamsimms-xyz-dreamberry`) |
| Public site | Cloudflare Pages under [art.adamsimms.xyz](https://github.com/adamsimms/art.adamsimms.xyz) |
| Dead-man | healthchecks.io |
| Tracking | [GitHub Issues](https://github.com/adamsimms/dreamberry/issues) |

## Repo layout

| Path | Purpose |
|------|---------|
| `dream/` | Generation pipeline, dial, gates, hourly path, R2 storage |
| `weather_schema/` | Symmetric train/live prompt + retrieval vector |
| `window/` | Static public bundle (landing, live window, about) |
| `scripts/` | Dataset, weather, Modal, eval, R2 helpers |
| `config/` | YAML locks (dream, gates, hourly, platform, weather) |
| `docs/` | Project brief, schema, and per-milestone notes |
| `modal_app.py` | Modal cron + one-shot entrypoints |
| `data/` | Local corpus / indexes (gitignored bulk; fixtures as needed) |

## Local development

Python 3.11+ recommended. GPU work runs on Modal; local is for weather schema, sidecars, window, and tests.

```bash
git clone https://github.com/adamsimms/dreamberry.git
cd dreamberry
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill R2 / HF / healthcheck as needed
```

Weather schema + unit tests (no GPU):

```bash
pytest weather_schema/tests dream/tests
```

Public window (observes R2; does not generate):

```bash
cd window && python3 -m http.server 8080
# → http://localhost:8080/window/?base=<r2-or-fixture-base>
```

Platform deploy (after secrets + Modal Volume sync) — see [docs/M5-PLATFORM.md](docs/M5-PLATFORM.md):

```bash
.venv/bin/python scripts/create_modal_secret.py
.venv/bin/modal deploy modal_app.py
.venv/bin/modal run modal_app.py::run_once --dial 0
```

Never commit `.env` or R2 credentials. See [SECURITY.md](SECURITY.md).

## Docs

| Doc | What |
|-----|------|
| [docs/DREAMBERRY.md](docs/DREAMBERRY.md) | Concept, architecture, dial, failure modes, infra |
| [docs/DREAMBERRY-WEATHER-SCHEMA.md](docs/DREAMBERRY-WEATHER-SCHEMA.md) | Symmetric train/live conditioning |
| [docs/M5-PLATFORM.md](docs/M5-PLATFORM.md) | Modal cron + R2 delivery |
| [docs/M6-WINDOW.md](docs/M6-WINDOW.md) | `/dreamberry` window + drawer + about |
| [window/README.md](window/README.md) | Static bundle layout |

Milestone notes: [M0](docs/M0-DATASET.md) · [M1](docs/M1-WEATHER.md) · [M2](docs/M2-DREAM-ENGINE.md) · [M3](docs/M3-QUALITY-GATES.md) · [M4](docs/M4-HOURLY.md)

## Related

| Repo | Role |
|------|------|
| [pinchards.is](https://github.com/adamsimms/pinchards.is) | Cloudberry archive source (sacred, closed corpus) |
| [cloudberry](https://github.com/adamsimms/cloudberry) | Field rig that captured the originals |
| [art.adamsimms.xyz](https://github.com/adamsimms/art.adamsimms.xyz) | Portfolio host; assembles `/dreamberry` |
| [adrift](https://github.com/adamsimms/adrift) · [waves](https://github.com/adamsimms/waves) · [dory](https://github.com/adamsimms/dory) | Sibling art experiences on the same island weather |

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).  
Security reports: [SECURITY.md](SECURITY.md).  
Changes: [CHANGELOG.md](CHANGELOG.md).

MIT — see [LICENSE](LICENSE).
