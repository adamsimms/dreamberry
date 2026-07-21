# Dreamberry — Project Brief

> Sibling to Cloudberry, not an extension of the archive product.
> Cloudberry stays closed and sacred — see [pinchards.is PRODUCT.md](https://github.com/adamsimms/pinchards.is/blob/main/docs/PRODUCT.md).
> Artistic lineage: [practice-forward-brief.md](https://github.com/adamsimms/pinchards.is/blob/main/docs/practice-forward-brief.md)
> (§5 “Generative afterlife of a closed corpus”).

**Status:** Build  
**Working title:** Dreamberry  
**Artist:** Adam Simms (solo)  
**Canonical URL:** [art.adamsimms.xyz/dreamberry](https://art.adamsimms.xyz/dreamberry)  
**Source repo:** [`adamsimms/dreamberry`](https://github.com/adamsimms/dreamberry)  
**Work tracking:** GitHub Issues on that repo  
**Quality over cost.** No budget ceiling; prefer the instrument that holds the place.

---

## 1. One sentence

Dreamberry is the dead Cloudberry camera **dreaming** — a labeled generative window that hallucinates the same fixed view of Pinchard's Island from an archive it can no longer add to and a live weather feed that is the last true thing about the place, and that dissolves when the ghost can no longer grip the rocks.

---

## 2. Why this, after Cloudberry

Cloudberry claimed an uninterrupted foothold through solar, Pi, modem, and GoPro. The camera died — from cold, dark, too little sun. The archive is finite. **Doris named that ending** ("d'once y'done wit'da island, dat'll be it"); the closure is an elegy, not an outage to patch.

So Dreamberry is emphatically **not** the camera running again. Restoring the live foothold would undo the elegy. The apparatus is gone; what remains is an archive and a weather feed, and the machine can only **hallucinate** the window it used to hold. That is precisely why it is *Dreamberry* and not *Cloudberry II*, why the images are **generated, not captured**, and why **identity collapse is the truest state, not the failure state** — the ghost cannot grip the rocks. Resettlement happened to the camera too.

Dreamberry asks: **can a machine be present at a place it can no longer photograph — and is that a gift or a consolation prize?**

It inherits telepresence and the abundance-sublime, but replaces capture with *inference*. The infrastructure is still the artwork: archive + weather + model as a body-less remote presence. Attribution lives in the details drawer — the same honesty as Cloudberry naming its hardware.

**The weather is the only thing still true.** The rocks are remembered and invented; the wind, cloud, fog, and sea are real, right now, at the island. Dreamberry is real atmosphere haunting a remembered frame — the last genuine live signal animating a fiction.

**Tone:** wonder, sublimity, tenderness.  
**Off-limits:** NFT drops, climate-campaign framing, tourism bait, passing synthetic frames as photographs, resurrecting the "live camera" fiction.

---

## 3. Relationship to the archive

| Cloudberry | Dreamberry |
|---|---|
| Closed photographic archive | Live generative window |
| Sacred, unaltered corpus | Separate R2 prefix / catalog |
| Citations as photographs | Labeled **generated** in details drawer (no overlay) |
| No public cross-link until Dreamberry is solid | May link later; never mix into archive |

- **Public surface:** current frame only — a true window, not a second gallery.
- **Private:** full hourly generation archive (for training critique, exhibition, artist study).
- **Training rule (v1):** the model trains/anchors **only** on Cloudberry originals — no generated frames in the mix. Keeps identity sharp for the success baseline.
- **Training rule (later chapter → the ending):** intentionally feed Dreamberry's own outputs back into training — *dreams about dreams* — and let the window slowly soften, drift, and forget. This is not just an experiment; it is a candidate **mortality** for the piece (see §4). A second, self-inflicted resettlement: the machine forgets the place until it can no longer hold it. Kept separate and labeled; never silently pollutes the v1 adapter.

---

## 4. Conceptual tensions (hold, don't hide)

These are load-bearing. The practice-forward brief demands they be *held*, not resolved.

- **Elegy vs. resurrection — resolved by dreaming.** Dreamberry never restores the live foothold. It is a haunting: a dead apparatus dreaming. Every generated frame is labeled; identity collapse is honored as the truest state.
- **Mortality — Dreamberry should be able to end.** An artwork that runs forever is weaker than one that will also die. The *dreams-about-dreams* loop is the built-in death: the model trains on its own hallucinations and slowly forgets the real window — a slow forgetting the piece performs on itself. Treated as a first-class future arc (`v2-forgetting`), not a footnote.
- **Weather as the only truth.** The single genuinely-live signal is the atmosphere at the island *now*. Everything visual is memory or invention. This asymmetry — real now, dreamed view — is the honest core of the telepresence.
- **Indigenous debt (open thread, unresolved).** Dreamberry is a settler apparatus trained to synthetically re-occupy resettled, colonized land (Ktaqmkuk; Mi'kmaq / Beothuk erasure the practice already commits a debt to). A machine hallucinating presence on that ground is not neutral. Held as an open ethical tension, per the practice ethic — acknowledged in the about text, not smoothed away.
- **Family authority.** Artist has permission to depict the cabin's view. Doris and family retain authority over their own story; the door stays open for their voice to enter the work (below).
- **Doris and the dream dial (opportunity).** Rather than the dial being an anonymous slider, **Doris could hold a remote control over the dream variable** — the named collaborator deciding how hard the machine is allowed to dream the place she resettled from. This puts human authority over the hallucination, and keeps the oral-history ethic alive in a purely computational piece. Carried as a design option in §6.

---

## 5. The instrument

### Training / anchor corpus
- **1,652** Cloudberry JPEGs (catalog count; R2: `art-adamsimms-xyz-cloudberry-images`)
- Fixed frame from cabin *Precious Memories* (`49.2026°N, 53.4859°W`), Aug 2017–Mar 2018
- GoPro HERO4 Black, **4:3, 4000×3000**, visible barrel/fisheye distortion
- Dense Aug–Oct; thinner winter; few true night frames — night is experimental

### Generation architecture (v1 — resolved by [pipeline spike](8ffaca47-0a48-4ca2-b606-e878e70f4312))

**A plain LoRA does NOT lock composition** — it teaches the *look* but not the geometry. Dreamberry is a **control** problem, so the lock comes from anchoring, not fine-tuning.

**Base model: SDXL (v1).** The only 2026 base where multi-ControlNet + IP-Adapter + img2img denoise control + tile-upscale are all mature and interoperable; OpenRAIL++ keeps future print sales legal. **Z-Image (Apache-2.0, 6B)** runs as a parallel *quality-experiment* track. FLUX.1-dev is set aside for v1 (non-commercial license + thinner control ecosystem).

**Canonical geometry frame:** pick **one** clear, well-lit Cloudberry original as the fixed ControlNet geometry source (rocks / horizon / cabin-edge). Criteria: midday-ish, high visibility, no fog/snow wipeout, representative of the frame (not a malfunction-burst oddity). Record its filename in repo config as `canonical_frame`. Weather-nearest retrieval still chooses the **img2img/IP-Adapter** atmosphere anchor per hour; ControlNet geometry preferably derives from `canonical_frame` (or a same-season twin of it) so composition does not wander with weather matches.

**The pipeline (dial-0 lock):**
1. **Weather-nearest-neighbor retrieval** picks a *real* same-season Cloudberry frame matching current weather (see schema doc) → used as the **img2img init**. A real morning underlies every dream.
2. **ControlNet depth (primary) + soft-edge/HED (horizon)** from the **canonical geometry frame** (and/or the weather anchor) lock rocks / horizon / cabin-edge geometry.
3. **IP-Adapter** carries palette/atmosphere from the weather anchor.
4. **LoRA** is the **mid-dial identity reservoir** (the learned "Cloudberry look"), *not* the geometry lock — its weight rises as the dial climbs and the anchor's grip loosens.

**Output:** generate at SDXL-native 4:3, then **upscale to ~4000×3000 with SUPIR** to match Cloudberry.

**LoRA training spec:** kohya_ss; 4:3 aspect buckets; **keep native fisheye** (de-fisheye is a v2 variant); rank 32; ~2.5–4k steps; **weather-derived captions** (from the schema); season-balanced sampling; night in a separate bucket.

**Baseline success (v1 lock):** at dial ≈ 0, a viewer who knows Cloudberry recognizes the same rocks / horizon / cabin-edge under plausible current weather, clearly labeled generated. Indistinguishable-from-GoPro is **not** the bar — honesty is.

### Validators (the two failure modes, made concrete)
- **Identity collapse:** **DINOv2 kNN** distance to the real-frame distribution + a **horizon-edge stability** check against the canonical edge map. Dial-aware: at low dial a collapse triggers regeneration/hold; at high dial it is *expected and honored*.
- **Season lock:** **same-season retrieval** (hard gate) + a **calibrated CLIP zero-shot** season classifier that trips a regen/refusal if the output's season mismatches the date. No summer-green February.
- **Dissolve rendering:** a **deliberate, seeded, structure-weighted defocus** — never emergent high-denoise mush. The ghost's failure to grip is composed, not accidental.

### Weather → conditioning (resolved by [weather spike](610da137-04d1-4491-92be-14fdff5d9d23))
Full spec: **[DREAMBERRY-WEATHER-SCHEMA.md](DREAMBERRY-WEATHER-SCHEMA.md)**. A deterministic map from numeric weather/ocean/sky/astronomy → a fixed-slot prompt (trigger `cldbry window view of Pinchard's Island, Newfoundland` + season, light, sky, fog, precip, sea state, wind) and a 9-feature weighted retrieval vector. **Symmetry contract:** one `compose_prompt` code path runs on both ERA5-archive packets (captioning) and live packets (inference), so training and live vocabularies are identical by construction. Thresholds are authoritative (oktas/METAR, WMO No. 782 fog/mist, WMO 4677 precip, WMO 3700/Douglas sea state, Beaufort wind, USNO twilight + golden hour, NL-adjusted seasons).

### Live condition sources (v1 stack)

Primary source is **Open-Meteo at the cabin coordinates**, chosen because it provides *both* live forecast *and* ERA5 historical/reanalysis with identical variables — keeping train-time and run-time conditioning symmetric. WYI and the buoy enrich the same schema.

| Role | Source | Notes |
|---|---|---|
| Primary fields (train + live) | **Open-Meteo @ cabin** | Cloud (total/low/mid/high), visibility, precip + WMO code, solar radiation, wind; historical ERA5 for training labels |
| Land obs enrichment | ECCC Pool's Island **WYI** (~12 km) | Closest real station (live only; history harder) |
| Sea roughness | SmartAtlantic Bonavista Bay buoy (~59 km) | Wave height / period; may be null → graceful |
| Time / season | Solar elevation & azimuth (computed) | Hard season + time-of-day lock |

**Real-time definition:** each frame reflects the island's **actual current local time, current weather, and current sun position** — a dreamed frame of the real *now*. That symmetry (real now, dreamed view) is the honest telepresence.

**Cadence:** hourly, **24 hours** (night included as experiment; drop nights later if results are weak).

**Season ethics:** season must not be wrong (no summer green in February). Prefer refusal over a pretty lie.

**Attribution (in drawer):** Open-Meteo (CC-BY 4.0), ECCC (open data licence), SmartAtlantic/CIOOS (CC-BY 4.0).

**Provenance:** every generated frame writes a JSON sidecar — weather packet, seed, base+LoRA version, dial, prompt, anchor-frame id, validator scores, failure mode. Powers the drawer, enables reproducibility, and *becomes* the dataset for the `v2-forgetting` loop.

---

## 6. Dream dial (0–10) — open design space

| Dial | Behavior | img2img denoise | ControlNet weight | IP-Adapter | LoRA weight |
|---|---|---|---|---|---|
| **0** | Real morning, locked (anchored) | ~0.35 | ~0.9 | ~0.7 | ~0.2 |
| **2** | Slight atmospheric drift | ~0.5 | ~0.75 | ~0.6 | ~0.4 |
| **5** | Interpretive; identity legible | ~0.7 | ~0.5 | ~0.4 | ~0.6 |
| **8** | Dreamlike; identity strains | ~0.85 | ~0.3 | ~0.2 | ~0.8 |
| **10** | Dissolves — the truest state | ~0.95 + seeded defocus | ~0.1 | ~0.05 | ~1.0 |

*(Indicative schedule from the [pipeline spike](8ffaca47-0a48-4ca2-b606-e878e70f4312); tune during dial experiments. As the dial rises the real-frame anchor lets go and the LoRA "memory" takes over — the ghost drifting off the rocks.)*

**Control modes (all remain live options — decide per context):**

1. **Artist-only** — Adam sets dial.
2. **Visitor / exhibition** — UI control or physical dial in a gallery.
3. **Data-driven** — dial derived from another signal (fog, wave height, wind, visibility, solar elevation, model confidence). Weather deciding how hard the place dreams.
4. **Doris's dial** — the named collaborator holds a remote control over the dream variable (see §4). Human authority over the hallucination; keeps the oral-history ethic alive in a computational piece.

**v1 public default (locked):** **artist-only, dial = 0.** Produce many dial sweeps privately during development; visitor / data-driven / Doris modes stay open but do not block launch.

---

## 7. Failure modes (conceptual, not bugs)

Cloudberry failed from cold, dark, power, modem. Dreamberry inherits that honesty — but its primary "failure" is reframed as its **truest state**.

### Primary — Identity collapse (the truest state)
When the ghost cannot hold the window (low confidence, high dial, undertrained night, bad season fit), the image **dissolves / defocuses / softens** rather than inventing a false sharp place. This is not an error screen — it is the dead camera failing to grip the rocks, and it is honored as such. Detected via **DINOv2 kNN + horizon-edge** check; rendered as a **deliberate seeded defocus** (never emergent mush) — see §5.

### Secondary — Weather silence
When Open-Meteo / WYI / buoy feeds fail or are stale beyond tolerance: withhold a new frame (or show a quiet empty/grey field) and surface that the sensors are silent. Remoteness again — infrastructure sets the limit. (Provider/GPU outage is handled the same way — hold.)

**Hold behavior:** clock may advance; image may not. Timestamp of last successful generation stays visible — waiting, like the Pi that never woke.

Keep to these two in v1; do not expand into a menu of gimmick failures.

---

## 8. Dataset & curation

Documented decisions for preparing the ~1,652 originals:

- **Malfunction bursts are KEPT.** Clusters of many frames within minutes (e.g. Oct 20 / Oct 28 / Sep 15) were **manual tests**, not glitches — they are real images of the view and stay in the corpus.
- **Near-duplicates: dedupe.** Many calm/clear hours are nearly identical; downweight or dedupe so training isn't dominated by "calm afternoon."
- **Night: separate bucket.** Train/evaluate night apart; it is experimental and may be dropped from public if weak.
- **Barrel/fisheye distortion: keep first (authentic GoPro look).** A **de-fisheyed** variant is an explicit later experiment (a second, "corrected" way of dreaming the window).
- **Aspect ratio: 4:3** end to end; output ~4000×3000 to match Cloudberry.
- **Time source: EXIF `DateTimeOriginal`**, not the filename timestamp, for pairing historical weather (the archive catalog already prefers EXIF via `pinchard_photo_capture_datetime` → `captureDateIso`; re-read/verify from full JPEGs).
- **Coverage skew:** dense Aug–Oct, thin Nov–Mar — the machine will know summer better than February. Held as content (memory is uneven), not silently corrected.

---

## 9. Presentation (v1 intent)

- **One live image** at `/dreamberry` — window, not archive UX. **No text overlay and no honesty mark on the image itself** for the web piece.
- **Honesty lives in the drawer**, same grammar as Cloudberry's photograph-details drawer (EXIF / camera / map). Dreamberry's drawer holds:
  - **Generation** — labeled generated; base + LoRA/model version; dial value + control mode; generated-at timestamp; last-success / hold state
  - **Weather** — the condition packet used for this frame (Open-Meteo @ cabin, WYI, buoy waves, solar elevation) + data attributions
  - **Image** — dimensions, seed, anchor-frame id, validator scores, failure mode if any
- Image stays clean; details are opt-in via the drawer (↑↓ / toggle), not dashboard chrome.
- **Gallery seam (in conversation, not merged):** in a physical exhibition, the honesty/telemetry lives on a **separate screen or wall panel tethered to the image** — the dream and its provenance in dialogue across a gap, never printed onto the dream itself.
- No cross-link from `/cloudberry/archive/` until the piece is solid.
- Exhibition path later: physical dial (incl. Doris's), room-as-window, dual channel with archive stills — beyond the first web spike.

---

## 10. Repo, shipping, and work tracking

### Repository
- **New GitHub repo:** `adamsimms/dreamberry` — all Dreamberry code, docs, training notes, orchestration, and window UI. (Siblings `adamsimms/waves` and `adamsimms/windows` are separate projects; Dreamberry shares the buoy data source with Waves but is its own thing.)
- **Not** in `pinchards.is` (archive stays sacred). Canonical brief + weather schema live in this repo under `docs/`. Pinchards may keep a short pointer only.
- **art.adamsimms.xyz** serves `/dreamberry` (assemble or mount from Dreamberry build artifacts — same family as other art sections).

### Infrastructure (v1 — resolved by [infra spike](08bc0b0d-f2a1-45a1-bc61-9c5dd881b807))
24 images/day is trivial GPU (~12–24 GPU-hrs/mo) — the axis is **reliability + low babysitting**, not cost.

**Cloudflare verdict (validated):** Cloudflare is the **right delivery home**, not the right **compute/orchestrator**.

| Layer | Verdict | Why |
|---|---|---|
| **GPU + hourly cron** | **Not Cloudflare** → **Modal** | Workers cannot run SDXL/ControlNet; Workers Cron calling an external GPU = two failure surfaces, no built-in retry. Modal collapses schedule + GPU into one Python process. |
| **Object storage (gen archive + current frame)** | **Yes — R2** | Zero egress, S3 API for Modal writes, already holds Cloudberry images; custom domain + CDN for `current.png`. |
| **Public window site** | **Yes — Pages under art.adamsimms.xyz** | Matches the art family; static window + drawer; no need for a second host. |
| **All-Cloudflare** | **Wrong** | Would force Workers→external GPU anyway; free Worker CPU limits make orchestration awkward. |
| **Zero-Cloudflare** | **Viable escape hatch** | all-Modal (Volume + web endpoint) if you ever leave CF — same generation code. |

- **Modal does both scheduling and GPU** (`modal.Cron` hourly → weather fetch → gate → generate on **L40S**, base model + LoRA + ControlNet baked into a Volume).
- **Storage/delivery on Cloudflare R2 + Pages:** `private/archive/YYYY/MM/DD/HH.png` + `.json`; `public/current.png`; `public/status.json`. Prefer a **dedicated Dreamberry R2 bucket** (or clear `dreamberry/` prefixes) — never write into Cloudberry image buckets.
- **Dead-man switch:** **healthchecks.io** (free).
- **Hold behavior:** on weather-silence OR provider/GPU outage, leave `public/current.png` untouched and update only `status.json`. Identity-collapse frames *do* update the pointer.
- **Cost:** ~$0–20/mo effective; worst realistic ~$50.

### Issues as the plan
Track work as **GitHub Issues** on `adamsimms/dreamberry`. Milestones: `v0-research`, `v1-window`, `v2-forgetting`. Prefer issues over a backlog doc. Labels: `dataset`, `model`, `weather`, `window`, `infra`, `concept`, `blocked`.

**Seed issues (create when repo opens):**

| # | Title | Area | Milestone |
|---|---|---|---|
| 1 | Land canonical brief + README in repo | docs | v0 |
| 2 | Dataset: download originals; verify EXIF DateTimeOriginal | dataset | v0 |
| 3 | Dataset: dedupe, night-bucket, keep manual-test bursts, 4:3 | dataset | v0 |
| 4 | Dataset: historical weather (Open-Meteo/ERA5) per EXIF time | dataset | v0 |
| 5 | Weather→description schema (symmetric train/live) | weather / concept | v0 |
| 6 | Weather-nearest-neighbor retrieval (real-frame anchor) | model / weather | v0 |
| 7 | Generation pipeline spike: base model + ControlNet + anchor | model | v0 |
| 8 | Dream-dial parameter schedule (0–10) | model / concept | v0 |
| 9 | Identity-collapse detector + dissolve rendering | model / concept | v0 |
| 10 | Season-lock validator | model / concept | v0 |
| 11 | Eval harness: held-out frames, CLIP/LPIPS, horizon stability | model | v0 |
| 12 | Upscale to 4:3 ~4000×3000 | model | v1 |
| 13 | Weather agent: Open-Meteo + WYI + buoy + solar → packet | weather | v1 |
| 14 | Generate + gate: season lock, identity collapse, weather silence | model / concept | v1 |
| 15 | Provenance JSON sidecar per frame | infra | v1 |
| 16 | Orchestration + GPU infra (per infra spike; not CF-locked) | infra | v1 |
| 17 | Storage: public current frame + private full archive | infra | v1 |
| 18 | Public window UI at `/dreamberry` (single frame + drawer) | window | v1 |
| 19 | Graceful failure / hold (weather + provider outage) | infra / concept | v1 |
| 20 | Mount `/dreamberry` on art Pages | infra | v1 |
| 21 | Dial experiments; decide public control mode (incl. Doris) | concept | v1 |
| 22 | About text: honesty, attributions, held Indigenous debt | concept / docs | v1 |
| 23 | De-fisheye variant experiment | dataset / model | v2 |
| 24 | Dreams-about-dreams: self-training / forgetting arc | model / concept | v2 |

---

## 11. Build sequence

1. **Repo + issues** — create `adamsimms/dreamberry`; seed issues; land canonical brief.
2. **Dataset prep** — download / curate; dedupe, night-bucket, keep manual-test bursts; pair historical weather via **EXIF `DateTimeOriginal`** (verify against catalog `captureDateIso`).
3. **Schema + retrieval** — build the symmetric weather→description schema and the weather-nearest-neighbor anchor index (research spike output).
4. **Generation spike** — stand up base model + geometry lock + real-frame anchor; validate dial-0 identity on held-out hours via the eval harness.
5. **Validators** — season lock + identity-collapse detector wired to the two failure modes.
6. **Weather agent** — hourly job builds the condition packet (Open-Meteo primary + WYI + buoy + solar).
7. **Generate + gate + store** — run pipeline; write frame + provenance sidecar; public = current, private = full.
8. **Public window** — single-frame page + details drawer at `/dreamberry`.
9. **Dial experiments** — artist sweeps; then evaluate visitor / data-driven / Doris control.
10. **(v2) Forgetting** — open the dreams-about-dreams arc and the de-fisheye variant.

---

## 12. Open decisions (non-blocking)

- Which exact Cloudberry filename becomes `canonical_frame` (pick during dataset prep)
- Whether nights stay after first month of results
- Success bar beyond baseline (how close to GoPro is "enough")
- Drawer field list / copy; about-text wording for the held Indigenous debt
- Whether the private gen log is ever exhibited as abundance-sublime
- Trigger criteria + intended endpoint for the `v2-forgetting` arc
- Whether/when to bring Doris's voice (oral history) into the piece
- When to open visitor / data-driven / Doris dial modes (v1 stays artist-only @ 0)

---

## 13. Naming note

**Dreamberry** keeps the berry lineage (bakeapple / Cloudberry) and allows night without contradiction. Internal artifacts may use `dreamberry-lora`, `dreamberry-window`, etc.

---

## Decisions log

**2026-07-20 (initial):** Title Dreamberry; URL `art.adamsimms.xyz/dreamberry`; new repo `adamsimms/dreamberry` tracked via Issues; 24h hourly, night experimental; failures = identity collapse + weather silence; honesty in details drawer, no image overlay; archive sacred & separate; public = current frame, private = full archive; weather labels via EXIF DateTimeOriginal; solo; quality over cost.

**2026-07-20 (Opus review):**
- **Reframe:** "the dead camera dreaming," not "still running" — resolves the elegy conflict; identity collapse is the *truest state*.
- **Weather = the only truth**; real-now / dreamed-view asymmetry is the honest core.
- **Mortality:** dreams-about-dreams = built-in *forgetting* / ending (`v2-forgetting`), first-class.
- **Architecture corrected:** LoRA alone does NOT lock composition → geometry lock (ControlNet) + real-frame anchor (weather-NN → img2img); LoRA only if it earns its place. Details from research spikes.
- **Weather conditioning:** deterministic, symmetric train/live schema (spike).
- **Data primary:** Open-Meteo (historical + live symmetric); WYI + buoy enrich.
- **Provenance sidecar** per frame; **eval harness** required.
- **Dataset:** keep manual-test bursts (real); dedupe; night bucket; keep fisheye first, de-fisheye later; 4:3 4000×3000.
- **Seam:** none on the web image; gallery telemetry on a *separate tethered screen* — in conversation, not merged.
- **Doris's dial:** named-collaborator control over the dream variable (option).
- **Held tensions:** Indigenous debt (unresolved, acknowledged), family authority (permission held).
- **Infra:** not locked to Cloudflare (spike).
**2026-07-20 (spikes integrated):**
- **Generation** ([spike](8ffaca47-0a48-4ca2-b606-e878e70f4312)): **SDXL** v1 (Z-Image parallel track); lock = real-frame img2img anchor + **ControlNet depth + soft-edge** + IP-Adapter; **LoRA = mid-dial identity reservoir**, not the lock (kohya_ss, 4:3 buckets, native fisheye, rank 32, ~2.5–4k steps, weather captions, season-balanced); collapse = **DINOv2 kNN + horizon-edge**; season = same-season retrieval + calibrated CLIP zero-shot; dissolve = **deliberate seeded defocus**; upscale = **SUPIR** → ~4000×3000. FLUX dev set aside (license).
- **Weather** ([spike](610da137-04d1-4491-92be-14fdff5d9d23)): deterministic symmetric schema in **[DREAMBERRY-WEATHER-SCHEMA.md](DREAMBERRY-WEATHER-SCHEMA.md)** — fixed-slot prompt + 9-feature retrieval vector; one `compose_prompt` path for captioning + inference; authoritative thresholds.
- **Infra** ([spike](08bc0b0d-f2a1-45a1-bc61-9c5dd881b807)): **Modal** (cron + GPU, L40S) → **R2** archive + `current.png`/`status.json` → **Pages** window; **healthchecks.io** dead-man switch; ~$0–20/mo; all-Modal escape hatch if leaving Cloudflare.

**2026-07-20 (build kickoff):**
- Repo `adamsimms/dreamberry` created; brief + weather schema moved; seed issues opened.
- **v1 dial default:** artist-only, dial = 0.
- **Canonical geometry frame:** pick one clear Cloudberry original during dataset prep; record as `canonical_frame`.
- **Cloudflare validated:** right for R2 + Pages delivery; wrong as GPU/orchestrator — Modal owns compute + cron.

