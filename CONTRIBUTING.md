# Contributing to Dreamberry

Thanks for your interest. Dreamberry is a personal artwork — the dead Cloudberry camera dreaming a weather-conditioned window on Pinchard's Island. Small, focused improvements are welcome.

## Before you start

1. Read the [README](README.md) and the [project brief](docs/DREAMBERRY.md) (§1–§7 especially).
2. Review the [Code of Conduct](CODE_OF_CONDUCT.md).
3. Check [open issues](https://github.com/adamsimms/dreamberry/issues) and [milestones](https://github.com/adamsimms/dreamberry/milestones).
4. For large or concept-touching changes, open an issue first.

### Artistic boundaries (non-negotiable)

- This is **not** Cloudberry II. Do not restore a live-camera fiction.
- Generated frames are labeled **generated** in the drawer — never mixed into the Cloudberry archive.
- **Weather silence → hold**; **GPU/channel failure → signal lost**. Do not merge those aesthetics.
- Season must not lie (no summer green in February). Prefer refusal over a pretty lie.
- Off-limits: NFT framing, climate-campaign framing, tourism bait.

## Development setup

```bash
git clone https://github.com/adamsimms/dreamberry.git
cd dreamberry
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

GPU generation runs on **Modal**, not on a laptop GPU by default. Local work is weather schema, sidecars, window UI, scripts, and tests.

```bash
pytest weather_schema/tests dream/tests
```

Window preview:

```bash
cd window && python3 -m http.server 8080
```

## Project structure

```
dream/              # pipeline, dial, gates, hourly, R2
weather_schema/     # compose_prompt + retrieval (train ≡ live)
window/             # static public bundle for art Pages
scripts/            # dataset, weather, Modal, eval helpers
config/             # locked YAML (dream, gates, platform, …)
docs/               # brief + weather schema (+ sparse contracts only)
modal_app.py        # Modal cron entrypoint
```

## Pull requests

1. Branch from `main`.
2. Keep diffs focused — one concern per PR when possible.
3. Match existing Python / window style; prefer clarity over cleverness.
4. Add or update tests when changing schema, gates, or storage contracts.
5. Update [CHANGELOG.md](CHANGELOG.md) for user-visible or ops-visible changes.
6. Keep README / CONTRIBUTING / SECURITY / canonical `docs/` in sync when the change
   touches public behavior, setup, secrets, or a contract — same PR; no new doc files
   (see [`.cursor/rules/docs.mdc`](.cursor/rules/docs.mdc)).
7. Open a PR describing **what** changed, **why**, and how you tested it.

Concept, dial semantics, validators, about copy, and hold/signal-lost behavior are judgment-heavy — expect careful review against [docs/DREAMBERRY.md](docs/DREAMBERRY.md).

## Secrets

Never commit `.env`, R2 keys, Modal tokens, or Hugging Face tokens. Use `.env.example` placeholders only. See [SECURITY.md](SECURITY.md).

## Security

Do not open public issues for vulnerabilities. Email **hello@adamsimms.xyz** — details in [SECURITY.md](SECURITY.md).

## Work tracking

Milestones **M0–M7** are delivery chunks, not version numbers. Prefer linking a PR to the relevant issue.
