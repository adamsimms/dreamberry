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

## GitHub Projects

Issues here are about the work: concept, model, weather, exhibition design, docs. Applications, calls, residencies and their deadlines are tracked in the private studio repo (see Private material), not here. Do not open apply issues in this repo.

**Issue titles:** no kind prefix. Do not start titles with `[residency]`, `Apply -`, `M7 spike:`, or similar. Kind lives on labels (`concept`, `model`, `weather`, `exhibition`, `docs`, …). Leave existing titles unless asked to rename.

## Private material

Applications, funder and call records, the CV, contact details and private research notes live in the private repo **adamsimms/studio** (`~/Documents/GitHub/studio`; read its `AGENTS.md` first). Dreamberry applications are `applications/<cycle>-<call>-dreamberry/`; private research is in `research/dreamberry/`. Nothing from studio comes into this repo unless an issue says so and Adam approved it. Never put a phone number or home address here; a global pre-commit guard blocks them.

Media (renders, maquettes, visual tests, experiment output) never stays in this repo's ignored folders: they are not backed up. It goes to the project's synced Drive folder, `$MEDIA_DIR` (`30 STUDIO/32 PROJECTS/DREAMBERRY/`): `01 REFERENCES`, `02 STUDIES` (concept and visual exploration), `03 TESTS` (technical experiments), `04 ARTWORK` (the finished work's own media), `05 DOCUMENTATION` (one folder per activity, named like studio's). Inside 02 and 03, one dated folder per piece of work: `<YYYY-MM> <name>`. `data/dream/` is for rebuildable caches only.

Public `docs/` stay sparse contracts: record decisions about the work, not application history. `sketchpad/` is scratch only.

## Bibliography / Zotero

Zotero is the PDF and source library (public library, collection Dreamberry `MI5FLXGH`). [docs/BIBLIOGRAPHY.md](docs/BIBLIOGRAPHY.md) is generated from it; rebuild with `node ~/Documents/GitHub/studio/scripts/zotero/build-bibliography.mjs dreamberry --out docs/BIBLIOGRAPHY.md` and do not edit it by hand. The art brief remains canon for the work. Writing to Zotero is publishing: only write batches Adam approved. Do not query `~/Zotero/zotero.sqlite`. Do not invent citations.

## Support

No funder support to acknowledge yet. When an award lands, add the funder and its required acknowledgement wording here and in the README.
