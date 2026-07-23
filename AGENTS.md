# Agent notes

Dreamberry is built primarily with Cursor. Prefer **one milestone (or one issue)
per chat** when the work is mechanical.

## Model routing

| Prefer | When | Typical issues |
|--------|------|----------------|
| **Opus** (judgment) | Concept, dial semantics, validators encoding failure modes, about/ethics copy, hold vs signal-lost, anything that could quietly resurrect a live-camera fiction | #5, #7–#11, #14, #18–#19, #21–#22, #24 |
| **Composer** (mechanical) | Spec already decided; scripts, wiring, tests against fixed tables, Modal/R2 boilerplate | #2–#4, #6 (after vector frozen), #12–#13, #15–#17, #20 |
| **Composer → Opus review** | Composer implements; Opus reviews honesty / season lock / hold before merge | #14, #18, #19 especially |

**Rules of thumb**

- Brief already names the tool and acceptance criteria → **Composer**.
- Wrong choice would change the *artwork* (elegy, identity collapse, weather-as-truth, labeling) → **Opus**.
- One milestone (or one issue) per chat for mechanical work; keep Opus chats for judgment-heavy milestones (M2–M3, M6 honesty).

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
3. [docs/DREAMBERRY-EXHIBITION.md](docs/DREAMBERRY-EXHIBITION.md) — physical exhibition contract

Do not add milestone status notes under `docs/`. Full policy (sparse docs + keep in sync):
[`.cursor/rules/docs.mdc`](.cursor/rules/docs.mdc).

Also: [CONTRIBUTING.md](CONTRIBUTING.md).
