# Dreamberry M5 — Platform (Modal + R2)

Issues **#16** (Modal cron + GPU), **#17** (R2 storage), and **#19** (graceful
failure / hold honesty).

---

## Locked decisions

| Topic | Choice |
|---|---|
| Orchestrator / GPU (hourly) | **Modal** `A10`, cron `5 * * * *`, ~32 GiB |
| Hourly output | **SDXL-native** (~1024×768); no SUPIR on cron |
| SUPIR keepers / print | On-demand `upscale_archive` on **L40S** → `archive/<id>_4k.png` |
| Bucket | `art-adamsimms-xyz-dreamberry` (dedicated — never Cloudberry) |
| Archive | `archive/<TIMESTAMP>_DREAM###.png` + `.json` (**PNG lossless**) |
| Public pointer | `current/current.webp` + `.json` + `previous.webp` + `status.json` (**WebP lossless**) |
| Signal lost | `current/signal_lost.webp` |
| Hold | update `status.json` only — leave `current.webp` untouched (**weather silence only**) |
| Window fade | dream→dream **1h** mid-join; signal_lost in/out **~10s** (`fade_ms` / `fade_started_at` / `previous`) |
| LoRA | not required for dial-0; train later |
| Dead-man | healthchecks.io via `HEALTH_PING_URL` |

---

## Layout on R2

```
archive/2017-08-16T08:00:37.000Z_DREAM001.png
archive/2017-08-16T08:00:37.000Z_DREAM001.json
current/current.webp
current/previous.webp      # prior dream for mid-join crossfade
current/current.json
current/status.json
current/signal_lost.webp   # only when channel is dead
```

Public URL example: `https://dreamberry.adamsimms.xyz/current/current.webp`

`status.json` fade fields for the public window:

| Field | Role |
|---|---|
| `previous` | Basename under `current/` to blend from (`previous.webp`, `current.webp`, or `signal_lost.webp`) |
| `fade_ms` | Crossfade duration — `3600000` dream→dream; `10000` signal_lost in/out |
| `fade_started_at` | ISO time the transition began — cold loads mid-join via wall clock |

---

## One-time setup

### 1. Env

Ensure `.env` has (see `.env.example`):

- `CF_R2_ENDPOINT` = S3 API host `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`
- `CF_R2_PUBLIC_BASE_URL` = custom domain (e.g. `https://dreamberry.adamsimms.xyz`)
- `CF_R2_BUCKET`, `CF_R2_ACCESS_KEY_ID`, `CF_R2_SECRET`
- `HF_TOKEN`, `HEALTH_PING_URL`

### 2. Modal secret

```bash
cd dreamberry   # repo root
.venv/bin/python scripts/create_modal_secret.py
```

### 3. Sync corpus → Modal Volume (~7.6G raw — once)

```bash
.venv/bin/python scripts/sync_modal_data.py
```

### 4. Deploy cron

```bash
.venv/bin/modal deploy modal_app.py
```

Modal requires a **payment method** on the account before GPU functions will run
(even for a one-shot `modal run`). Add one at https://modal.com/settings/billing

### 5. Smoke one tick

```bash
.venv/bin/modal run modal_app.py
# or
.venv/bin/modal run modal_app.py::run_once --dial 0
```

On-demand SUPIR for one archive keeper (does not move `current/`):

```bash
.venv/bin/modal run modal_app.py::upscale_archive --dream-id '2017-08-16T08:00:37.000Z_DREAM001'
```

Prefetch SUPIR weights onto the HF Volume once (large download; only needed for keepers):

```bash
.venv/bin/modal run modal_app.py::prefetch_supir
```

The image deliberately excludes `data/` — the `dreamberry-data` Volume mounts at
`/root/dreamberry/data` (mounting over a non-empty image path fails). Fanghua-Yu
SUPIR is cloned to `/opt/SUPIR` at image build; `SUPIR_ROOT` is set in the image.

Local R2-only publish test (uses local GPU/MPS if available):

```bash
PYTHONPATH=. .venv/bin/python scripts/dream_hourly.py --packet data/weather/<frame>.json --r2
```

---

## Code map

| Piece | Path |
|---|---|
| R2 client + encode PNG/WebP | `dream/storage.py` |
| Hourly path (optional `store=`) | `dream/hourly.py` |
| Health ping | `dream/healthcheck.py` |
| Modal app | `modal_app.py` |
| Platform config | `config/platform.yaml` |

---

## #19 — graceful failure / hold honesty

Normative contract: [DREAMBERRY.md §7](DREAMBERRY.md). Mapped in `dream/hourly.py`.
**Weather silence** → **hold**; dream/channel breaks (generation throws after
retries, gates reject every attempt, publish/R2 fails) → **signal_lost** noise
for that hour. Do not merge the two aesthetics — do not hold the previous dream
over a broken hour.

Honesty guarantees enforced (and unit-tested in `test_hourly.py` / `test_storage.py`):

- A hold **never overwrites** `current.webp` — only `status.json` is rewritten
  (R2 `publish_hold` touches status only).
- `current.webp` is only ever written by a *publish*; `signal_lost` writes a
  **separate** `signal_lost.webp` key and merely repoints `status.current`. So a
  hold that follows a signal_lost **reverts** the pointer from noise back to the
  last real dream — noise never masquerades as a held dream.
- `status.json` carries `last_success_at` **and** `last_success_dream_id`, both
  preserved across holds and signal-lost hours, so the next good hour — or a
  later hold — always restores the correct dream and its provenance.
- First-ever hold (nothing published yet): `current` and `dream_id` are `null` —
  there is no honest frame to show.
- Dead-man switch (`modal_app.py`): a completed tick, **including a hold**, pings
  healthy — silence is a legitimate honored state, not a system fault. Only
  `signal_lost` (channel dead) hits `/fail` and pages.

---

## Not in this slice

- **#18 / #20** public window UI on Pages (M6 — done)
- Forecast batch / weather-bucket cache (cost follow-ons; deferred)
