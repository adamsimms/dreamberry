# Dreamberry

The dead [Cloudberry](https://art.adamsimms.xyz/cloudberry/archive/) camera **dreaming** — a labeled generative window on Pinchard's Island, Newfoundland, conditioned by live weather.

**Canonical URL (intended):** [art.adamsimms.xyz/dreamberry](https://art.adamsimms.xyz/dreamberry)

This is a **sibling** to the Cloudberry archive, not an extension of it. The archive stays sacred and separate.

## Docs

- [Project brief](docs/DREAMBERRY.md) — concept, architecture, dial, failure modes, infra
- [Weather → image schema](docs/DREAMBERRY-WEATHER-SCHEMA.md) — symmetric train/live conditioning
- [M5 Platform](docs/M5-PLATFORM.md) — Modal cron + R2 delivery
- [M6 Public window](docs/M6-WINDOW.md) — `/dreamberry` window + drawer + about

## Stack (first public release)

- **Generation:** SDXL + ControlNet + IP-Adapter + weather-nearest real-frame anchor + LoRA (mid-dial)
- **Compute / cron:** Modal
- **Storage / window:** Cloudflare R2 + Pages (under art.adamsimms.xyz)
- **Tracking:** GitHub Issues — milestones **M0–M7**

## Status

Build. Work tracked in [Issues](https://github.com/adamsimms/dreamberry/issues) by **milestone (M0–M7)** — not version numbers.

| Milestone | Done when |
|---|---|
| **M0 Dataset** | Curated images + EXIF + ERA5 packets |
| **M1 Weather conditioning** | Schema + weather-NN anchors |
| **M2 Dream engine** | SDXL pipeline + dial + canonical_frame |
| **M3 Quality gates** | Validators + dial-0 eval |
| **M4 Hourly generation path** | Agent → gate → sidecar → upscale |
| **M5 Platform** | Modal cron + R2 + hold |
| **M6 Public window** | Live `/dreamberry` |
| **M7 Forgetting** | Containered dreams-about-dreams (+ de-fisheye); variable end |

**Agent routing** (see [docs/DREAMBERRY.md](docs/DREAMBERRY.md) §10): **Opus 4.8** for judgment; **Composer 2.5-fast** for mechanical/spec’d work. Prompt: `Build milestone M0 …`.
