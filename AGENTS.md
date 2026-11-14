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

## Docs policy

### Canonical docs

1. [docs/DREAMBERRY.md](docs/DREAMBERRY.md) — brief
2. [docs/DREAMBERRY-WEATHER-SCHEMA.md](docs/DREAMBERRY-WEATHER-SCHEMA.md) — conditioning contract
3. [docs/DREAMBERRY-EXHIBITION.md](docs/DREAMBERRY-EXHIBITION.md) — physical exhibition contract

Add another `docs/*.md` only if it is a **decision record** or **ops contract** the code cannot own (e.g. eval baseline numbers). Default: **do not add a new doc**.

Allowed exceptions already in tree: `M3-BASELINE.md`, `M4-SIDECAR.md`, `M5-PLATFORM.md`, and `BIBLIOGRAPHY.md` (generated from Zotero; never edit by hand). Do not revive deleted `M*.md` status notes.

Also: [CONTRIBUTING.md](CONTRIBUTING.md).

### Never commit to docs/

- Milestone / issue status diaries ("landed ✅", "not in this slice")
- Agent routing, Cursor prompt patterns, model pickers → `AGENTS.md` only
- Setup already covered by README, CONTRIBUTING, or GitHub repo tabs
- Re-tables of hold / signal_lost / collapse — one home: `DREAMBERRY.md` §7; link it
- "Why included" padding, implementation checklists, AI-review changelogs that restate the brief
- README docs indexes or Contribute footers that duplicate GitHub header tabs

### Decision taxonomy

- **Work decision** (true whatever happens to any application): edit the brief or contract body in place, then add one dated line to its Decisions log saying what changed and where. Delete log lines a later change supersedes; git keeps the history.
- **Proposal choice** (made for one call: room layout, what to include, how to pitch): never goes here. It lives with the application in the private studio repo. If the show is confirmed it becomes that show's plan there; it reaches these docs only if it holds beyond that show.
- **Option or research** (a menu, a precedent, a finding): options go in the relevant section's shortlist; precedents go to Zotero as notes on the item.

### Writing rules

1. **One source of truth** — if it lives in the brief, schema, code, or an issue, do not paste it again.
2. **Delta only** — decisions logs record what changed, not a re-summary of architecture.
3. **Contracts over narration** — thresholds, field lists, R2 layout yes; process essays no (ethics/concept stay in the brief).
4. **Ship status → Issues/PRs**, not `docs/`.
5. **No module docstring stamps** (`M4 / issue #14`) — one-line purpose; tracking in git.
6. **README stays short** — how it works + local run; no docs catalog.

### Keep in sync (same PR)

When a change touches any of the following, update the matching surface in the **same PR** — edit the existing file; do not invent a new one:

| Change touches… | Update… |
|-----------------|---------|
| Public behavior, stack, or how to run locally | `README.md` |
| Dev setup, artistic boundaries, or PR expectations | `CONTRIBUTING.md` |
| Secrets, credentials, or vulnerability reporting | `SECURITY.md` / `.env.example` |
| Concept, ethics, dial, failure modes, infra decisions | `docs/DREAMBERRY.md` |
| Weather buckets, tokens, or train≡live symmetry | `docs/DREAMBERRY-WEATHER-SCHEMA.md` |
| Physical rooms, display medium, or exhibition encounter | `docs/DREAMBERRY-EXHIBITION.md` |
| R2 layout, Modal deploy, or hold delivery | `docs/M5-PLATFORM.md` (or README if one line) |
| Sidecar fields | `docs/M4-SIDECAR.md` + code/tests |
| User- or ops-visible shipping note | `CHANGELOG.md` |

Stale docs that contradict the code are a bug. Prefer a one-line fix over a new section.

### Before adding or expanding a doc

> Does this encode a decision or contract someone must follow later — or does it narrate that work happened?

If the latter → update the issue/PR, not `docs/`.

## GitHub Projects

Issues here are about the work: concept, model, weather, exhibition design, docs. Applications, calls, residencies and their deadlines are tracked in the private studio repo (see Private material), not here. Do not open apply issues in this repo.

**Issue titles:** no kind prefix. Do not start titles with `[residency]`, `Apply -`, `M7 spike:`, or similar. Kind lives on labels (`concept`, `model`, `weather`, `exhibition`, `docs`, …). Leave existing titles unless asked to rename.

## Private material

Applications, funder and call records, the CV, contact details and private research notes live in the private repo **adamsimms/studio** (`~/Documents/GitHub/studio`; read its `AGENTS.md` first). Dreamberry applications are `applications/<cycle>-<call>-dreamberry/`; private research is in `research/dreamberry/`. Nothing from studio comes into this repo unless an issue says so and Adam approved it. Never put a phone number or home address here; a global pre-commit guard blocks them.

Media (renders, maquettes, visual tests, experiment output) never stays in this repo's ignored folders: they are not backed up. It goes to the project's media folder, `$MEDIA_DIR` (`30 STUDIO/32 PROJECTS/DREAMBERRY/`), a local outbox that a daily job copies to off-site storage and clears 14 days after the copies are verified. Older media is fetched from that storage, not read back from `$MEDIA_DIR`. Stages: `01-REFERENCES`, `02-STUDIES` (concept and visual exploration), `03-TESTS` (technical experiments), `04-ARTWORK` (the finished work's own media), `05-DOCUMENTATION` (one folder per activity, named like studio's). Inside 02 and 03, one dated folder per piece of work: `<YYYY-MM>-<NAME>`. `data/dream/` is for rebuildable caches only.

Public `docs/` stay sparse contracts: record decisions about the work, not application history. `sketchpad/` is scratch only.

## Bibliography / Zotero

Zotero is the PDF and source library (public library, collection Dreamberry `MI5FLXGH`). [docs/BIBLIOGRAPHY.md](docs/BIBLIOGRAPHY.md) is generated from it; rebuild with `node ~/Documents/GitHub/studio/scripts/zotero/build-bibliography.mjs dreamberry --out docs/BIBLIOGRAPHY.md` and do not edit it by hand. The art brief remains canon for the work. Writing to Zotero is publishing: only write batches Adam approved. Do not query `~/Zotero/zotero.sqlite`. Do not invent citations.

## Support

No funder support to acknowledge yet. When an award lands, add the funder and its required acknowledgement wording here and in the README.
