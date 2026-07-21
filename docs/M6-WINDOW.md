# Dreamberry M6 — Public window

Issues **#18** (window UI), **#21** (dial scope / private sweeps), **#22** (about
copy). **#20** (mount on art Pages) is Composer's — see the assemble contract
below.

**Done when:** `art.adamsimms.xyz/dreamberry` is live (artist dial 0) with the
window, drawer, and about page.

---

## Surfaces

| Path | File (this repo) | Role |
|---|---|---|
| `/dreamberry` | `window/index.html` | Portfolio landing — intro + live hero + links |
| `/dreamberry/window` | `window/window/index.html` | The live piece — one image + drawer, no nav |
| `/dreamberry/info` | `window/info/index.html` | About — honesty, failure states, attributions |

Shared assets in `window/assets/` (`config.js`, `wmo.js`, `window.js`,
`style.css`). Everything is **static, no build step** — the bundle is copied
verbatim to `dist/dreamberry/` by the art site (see #20).

---

## #18 — the window

One live image, no overlay, chrome-less. A Cloudberry-grammar drawer (↑/↓ or the
corner toggle) holds three sections + a state line:

- **Generation** — labeled generated, dial + control mode, base model, LoRA,
  generated-at, frame id.
- **Weather — the only live signal** — the condition packet (Open-Meteo, WYI,
  buoy, solar) + attributions.
- **Image** — dimensions, seed, anchor frame, validator scores, failure mode.

### Data source

The window is a pure observer. It reads what the Modal cron wrote to R2
(`config/platform.yaml → r2.public_base_url`, default
`https://dreamberry.adamsimms.xyz`):

```
current/status.json    ← polled every 60s (the pointer + state)
current/current.json   ← sidecar for the shown dream (drawer provenance)
current/current.webp   ← the dream (via <img>)
current/signal_lost.webp
```

Local dev against a fixture: append `?base=<url>` to the page URL.

### Refresh UX (locked)

Weather changing behind glass, not a slideshow. Poll `status.json`; act on the
`dream_id` / `current` change per the honesty split (issue #19):

| State | Window behaviour |
|---|---|
| **published** (new `dream_id`) | prefetch, then **crossfade** old → new (~5.5s) |
| **hold** | **do not touch the image**; drawer note updates quietly |
| **signal_lost** | **crossfade into** the noise field |
| nothing published yet | honest "waiting for the first dream…" |

No toast, no "updated" chrome. `prefers-reduced-motion` → near-instant swap.

### R2 CORS + cache (apply in #18/#20)

Cross-origin JSON fetches (`art.adamsimms.xyz` → `dreamberry.adamsimms.xyz`)
need CORS on the bucket. Images use `<img>` and don't. Canonical rules live in
`config/r2-cors.json`. Apply with Wrangler (preferred):

```bash
# from art.adamsimms.xyz, Node ≥22
npx wrangler r2 bucket cors set art-adamsimms-xyz-dreamberry \
  --file ../dreamberry/config/r2-cors.json
```

S3 API fallback: `scripts/apply_r2_cors.py` (token must allow PutBucketCors).

`current/` objects get `Cache-Control: public, max-age=300` on write
(`dream/storage.py`). The client also cache-busts (`?v=<dream_id>`, `?t=<now>`).

---

## #21 — dial scope (public stays artist @ 0)

The public window is **artist-only, dial 0**, permanently for v1. Visitor /
data-driven / Doris dials stay open as future modes but are **not** wired to any
public control (DREAMBERRY.md §6).

Dial experiments run privately via `scripts/dial_sweep.py`, which:

- writes only under `data/dream/dial/` (gitignored sandbox),
- never imports `dream.storage`, never uploads to R2, never writes `status.json`,
- keeps its files out of the `_DREAM###` archive roll counter,
- emits a `contact.html` per packet for local eyeballing.

```bash
PYTHONPATH=. .venv/bin/python scripts/dial_sweep.py \
  --packet data/weather/<frame>.json --dials 0 2 4 6 8 10 --seed 1234
```

---

## #22 — about copy

`window/info/index.html` carries the honesty surface: generated label, the
weather-is-the-only-truth framing, the three failure states in plain language,
data attributions, and one held paragraph naming the Indigenous / Ktaqmkuk debt
without resolving it. The drawer stays telemetry-only; the ethics live on the
info page.

---

## #20 — mount on art Pages (Composer)

The art site (`art.adamsimms.xyz`, Astro) assembles sibling static bundles into
`dist/` via `scripts/assemble-*.mjs` (see `assemble-cloudberry-archive.mjs`).
Dreamberry follows the same pattern:

1. `scripts/assemble-dreamberry.mjs` copies this repo's `window/` → `dist/dreamberry/`.
2. `assemble:dreamberry` is wired into `assemble:siblings` and CI checks out
   `adamsimms/dreamberry` as `.dreamberry` (`DREAMBERRY_REPO_PATH`).
3. Trailing-slash redirects + modest `/dreamberry/*` cache headers live on the
   art site; CSP report-only allows `dreamberry.adamsimms.xyz` for `img-src` /
   `connect-src`.
4. R2 CORS for JSON fetches: `scripts/apply_r2_cors.py` (run once with R2 keys
   in `.env`). Short `Cache-Control` on `current/` objects is set by
   `dream/storage.py` on write.
5. No cross-link from `/cloudberry/archive/` yet (DREAMBERRY.md §9).

Contract: `window/` is self-contained and path-relative, so a straight
recursive copy to `/dreamberry/` is all that's required.
