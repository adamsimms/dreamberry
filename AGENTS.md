# Agent notes

Dreamberry is built primarily with Cursor. Prefer **one milestone (or one issue)
per chat** when the work is mechanical.

## Model routing

Full table: [docs/DREAMBERRY.md](docs/DREAMBERRY.md) §10.

| Prefer | When |
|--------|------|
| **Opus** (judgment) | Concept, dial semantics, validators encoding failure modes, about/ethics copy, hold vs signal-lost, anything that could quietly resurrect a live-camera fiction |
| **Composer** (mechanical) | Spec already decided; scripts, wiring, tests against fixed tables, Modal/R2 boilerplate |

Pattern: `Build milestone M7 — … Follow docs/DREAMBERRY.md.`

## Hard rules

- Sibling to Cloudberry — never write into Cloudberry R2 buckets or mix generated frames into the archive.
- Label generation in the **drawer**, not as an overlay on the image.
- Weather silence → **hold**; GPU/channel failure → **signal lost**. Keep both.
- Season lock is ethical, not cosmetic.
- Secrets only via `.env` / Modal Secrets — see [SECURITY.md](SECURITY.md).

## Canonical docs

1. [docs/DREAMBERRY.md](docs/DREAMBERRY.md) — brief
2. [docs/DREAMBERRY-WEATHER-SCHEMA.md](docs/DREAMBERRY-WEATHER-SCHEMA.md) — conditioning contract
3. Milestone notes under `docs/M*.md`
4. [CONTRIBUTING.md](CONTRIBUTING.md)
