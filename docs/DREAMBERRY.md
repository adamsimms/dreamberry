# Dreamberry — Project Brief

> Sibling to Cloudberry, not an extension of the archive product.
> Cloudberry stays closed and sacred — see [pinchards.is PRODUCT.md](https://github.com/adamsimms/pinchards.is/blob/main/docs/PRODUCT.md).
> Artistic lineage: [practice-forward-brief.md](https://github.com/adamsimms/pinchards.is/blob/main/docs/practice-forward-brief.md)
> (§5 “Generative afterlife of a closed corpus”).

**Status:** Build  
**Working title:** Dreamberry  
**Artist:** Adam Simms (solo)  
**Canonical URL:** [art.adamsimms.xyz/dreamberry](https://art.adamsimms.xyz/dreamberry)  
**Source repo:** `[adamsimms/dreamberry](https://github.com/adamsimms/dreamberry)`  
**Work tracking:** GitHub Issues on that repo  
**Quality over cost.** No budget ceiling; prefer the instrument that holds the place.

---

## 1. One sentence

Dreamberry is the dead Cloudberry camera **dreaming** — a window that hallucinates the same fixed view of Pinchard's Island from an archive it can no longer add to and a live weather feed that is the last true thing about the place, and that dissolves when the ghost can no longer grip the rocks.

---

## 2. Why this, after Cloudberry

Cloudberry claimed an uninterrupted foothold through solar, Pi, modem, and GoPro. The camera died — from cold, dark, too little sun. The archive is finite. **Doris named that ending** ("d'once y'done wit'da island, dat'll be it"); the closure is an elegy, not an outage to patch.

So Dreamberry is emphatically **not** the camera running again. Restoring the live foothold would undo the elegy. The apparatus is gone; what remains is an archive and a weather feed, and the machine can only **hallucinate** the window it used to hold. That is precisely why it is *Dreamberry* and not *Cloudberry II*, why the images are **generated, not captured**, and why **identity collapse is the truest state, not the failure state** — the ghost cannot grip the rocks. Resettlement happened to the camera too.

Dreamberry asks: **can a machine be present at a place it can no longer photograph — and is that a gift or a consolation prize?**

It inherits telepresence and the abundance-sublime, but replaces capture with *inference*. The infrastructure is still the artwork: archive + weather + model as a body-less remote presence. Attribution lives in the details drawer — the same honesty as Cloudberry naming its hardware.

**The weather is the only thing still true.** The rocks are remembered and invented; the wind, cloud, fog, and sea are real, right now, at the island. Dreamberry is real atmosphere haunting a remembered frame — the last genuine live signal animating a fiction.

**Tone:** wonder, sublimity, tenderness.  
**Off-limits:** NFT drops, climate-campaign framing, tourism bait.

---

## 3. Relationship to the archive


| Cloudberry                                     | Dreamberry                                           |
| ---------------------------------------------- | ---------------------------------------------------- |
| Closed photographic archive                    | Live generative window                               |
| Sacred, unaltered corpus                       | Separate R2 prefix / catalog                         |
| Citations as photographs                       | Labeled **generated** in details drawer (no overlay) |
| No public cross-link until Dreamberry is solid | May link later; never mix into archive               |


- **Public surface:** current frame only — a true window, not a second gallery.
- **Private:** full hourly generation archive (for training critique, exhibition, artist study).
- **Training rule (first adapter / M0–M6):** the model trains/anchors **only** on Cloudberry originals — no generated frames in the mix. Keeps identity sharp for the success baseline.
- **Training rule (later chapter → the ending / M7):** intentionally feed Dreamberry's own outputs back into training — *dreams about dreams* — and let the window slowly soften, drift, and forget. This is not just an experiment; it is a candidate **mortality** for the piece (see §4). A second, self-inflicted resettlement: the machine forgets the place until it can no longer hold it. Kept separate and labeled; never silently pollutes the first public adapter.

---

## 4. Conceptual tensions (hold, don't hide)

These are load-bearing. The practice-forward brief demands they be *held*, not resolved.

- **Elegy vs. resurrection — resolved by dreaming.** Dreamberry never restores the live foothold. It is a haunting: a dead apparatus dreaming. Every generated frame is labeled; identity collapse is honored as the truest state.
- **Mortality — Dreamberry should be able to end.** An artwork that runs forever is weaker than one that will also die. The *dreams-about-dreams* loop is the built-in death: the model trains on its own hallucinations and slowly forgets the real window — a slow forgetting the piece performs on itself. Treated as a first-class future arc (**M7 — Forgetting**), not a footnote.
  - **No hard calendar end date.** Timing stays a **variable** (stochastic / criteria-based) so even we don’t know exactly when the forgetting completes — open until a pre-M7 spike.
  - **Container required (spike before M7):** forgetting must not escape the place. Allowed: drifted placement, invented trees/scrub, soft identity. **Forbidden:** climate/geography teleport (no tropical beach, no alien geology). Same island, same cold maritime world — dreaming *within* the container, not out of it. Spike designs the rails (season lock, retrieval gates, validators, mix schedule).
- **Weather as the only truth.** The single genuinely-live signal is the atmosphere at the island *now*. Everything visual is memory or invention. This asymmetry — real now, dreamed view — is the honest core of the telepresence.
- **Indigenous debt (open thread, unresolved).** Dreamberry is a settler apparatus trained to synthetically re-occupy resettled, colonized land (Ktaqmkuk; Mi'kmaq / Beothuk erasure the practice already commits a debt to). A machine hallucinating presence on that ground is not neutral. Held as an open ethical tension, per the practice ethic — acknowledged in the about text, not smoothed away.
- **Family authority.** Artist has permission to depict the cabin's view. Doris and family retain authority over their own story; the door stays open for their voice to enter the work (below).
- **Doris and the dream dial (opportunity).** Named-collaborator control over the dream variable — design option in §6.

---

## 5. The instrument

### Training / anchor corpus

- **1,652** Cloudberry JPEGs (catalog count; R2: `art-adamsimms-xyz-cloudberry-images`)
- Fixed frame from cabin *Precious Memories* (`49.2026°N, 53.4859°W`), Aug 2017–Mar 2018
- GoPro HERO4 Black, **4:3, 4000×3000**, visible barrel/fisheye distortion
- Dense Aug–Oct; thinner winter; few true night frames — night is experimental

### Generation architecture (v1)

**A plain LoRA does NOT lock composition** — it teaches the *look* but not the geometry. Dreamberry is a **control** problem, so the lock comes from anchoring, not fine-tuning.

**Base model: SDXL** for the first public release. Best fit for this *control* problem (multi-ControlNet + IP-Adapter + img2img + tile-upscale; OpenRAIL++). **Do not swap mid-build.** **Case for change only after M3 eval:** if dial-0 lock is solid *and* the look is hated, then A/B **FLUX** (or Z-Image / Flux Klein) as a quality track — not before.

**Canonical geometry frame:** **one** geometry master + weather-NN for atmosphere (not a weather-class gallery of canons). Weather-NN already supplies rainy/foggy/storm matches for img2img/IP-Adapter.

- **Locked:** `2017-09-18T09:59:44.000Z_GOPR2537.JPG` — clear, cloudless, ~10:00 NDT, short shadows, sharp rock/horizon edges, minimal cabin wedge. ([archive](https://art.adamsimms.xyz/cloudberry/archive/?filename=2017-09-18T09%3A59%3A44.000Z_GOPR2537.JPG))
- **Backup:** `2017-09-15T09:59:52.000Z_GOPR2479.JPG` if the locked frame ever proves weak in ControlNet.
- Cloudless is preferred for the *geometry* master; clouds belong on weather anchors, not the ControlNet source.
- Prefer low cabin-shadow intrusion on the geometry master; shadowed days still enter via weather-NN and must be **reproduced** when solar geometry implies them (see §8).

**The pipeline (dial-0 lock):**

1. **Weather-nearest-neighbor retrieval** picks a *real* same-season Cloudberry frame matching current weather (see schema doc) → used as the **img2img init**. A real morning underlies every dream.
2. **ControlNet depth (primary) + soft-edge/HED (horizon)** from the **canonical geometry frame** lock rocks / horizon / cabin-edge geometry.
3. **IP-Adapter** carries palette/atmosphere from the weather anchor.
4. **LoRA** is the **mid-dial identity reservoir** (the learned "Cloudberry look"), *not* the geometry lock — its weight rises as the dial climbs and the anchor's grip loosens.

**Output (web / private archive):** generate at SDXL-native 4:3, then **upscale to ~4000×3000 with SUPIR** to match Cloudberry. **Print:** on-demand further upscale of selected frames only — do not store every hour at print resolution.

**Provenance:** **JSON sidecar only** (no embedded EXIF/XMP requirement). Fields: weather packet, seed, base+LoRA version, dial, prompt, anchor-frame id, validator scores, failure mode.

**LoRA training spec:** kohya_ss; 4:3 aspect buckets; **keep native fisheye** (de-fisheye is an M7/variant experiment); rank 32; ~2.5–4k steps; **weather-derived captions** (from the schema); season-balanced sampling; night in a separate bucket.

**Baseline success (first public lock):** at dial ≈ 0, a viewer who knows Cloudberry recognizes the same rocks / horizon / cabin-edge under plausible current weather, clearly labeled generated. Indistinguishable-from-GoPro is **not** the bar — honesty is.

### Validators (the two failure modes, made concrete)

- **Identity collapse:** **DINOv2 kNN** distance to the real-frame distribution + a **horizon-edge stability** check against the canonical edge map. Dial-aware: at low dial a collapse triggers regeneration/hold; at high dial it is *expected and honored*.
- **Season lock:** **same-season retrieval** (hard gate) + a **calibrated CLIP zero-shot** season classifier that trips a regen/refusal if the output's season mismatches the date. No summer-green February.
- **Dissolve rendering:** a **deliberate, seeded, structure-weighted defocus** — never emergent high-denoise mush. The ghost's failure to grip is composed, not accidental.

### Weather → conditioning

Full spec: **[DREAMBERRY-WEATHER-SCHEMA.md](DREAMBERRY-WEATHER-SCHEMA.md)**. A deterministic map from numeric weather/ocean/sky/astronomy → a fixed-slot prompt (trigger `cldbry window view of Pinchard's Island, Newfoundland` + season, light, sky, fog, precip, sea state, wind) and a 9-feature weighted retrieval vector. **Symmetry contract:** one `compose_prompt` code path runs on both ERA5-archive packets (captioning) and live packets (inference), so training and live vocabularies are identical by construction. Thresholds are authoritative (oktas/METAR, WMO No. 782 fog/mist, WMO 4677 precip, WMO 3700/Douglas sea state, Beaufort wind, USNO twilight + golden hour, NL-adjusted seasons).

### Live condition sources (v1 stack)

Primary source is **Open-Meteo at the cabin coordinates**, chosen because it provides *both* live forecast *and* ERA5 historical/reanalysis with identical variables — keeping train-time and run-time conditioning symmetric. WYI and the buoy enrich the same schema.


| Role                          | Source                                    | Notes                                                                                                                 |
| ----------------------------- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Primary fields (train + live) | **Open-Meteo @ cabin**                    | Cloud (total/low/mid/high), visibility, precip + WMO code, solar radiation, wind; historical ERA5 for training labels |
| Land obs enrichment           | ECCC Pool's Island **WYI** (~12 km)       | Closest real station (live only; history harder)                                                                      |
| Sea roughness                 | SmartAtlantic Bonavista Bay buoy (~59 km) | Wave height / period; may be null → graceful                                                                          |
| Time / season                 | Solar elevation & azimuth (computed)      | Hard season + time-of-day lock                                                                                        |


**Real-time definition:** each frame reflects the island's **actual current local time, current weather, and current sun position** — a dreamed frame of the real *now*. That symmetry (real now, dreamed view) is the honest telepresence.

**Cadence:** hourly, **24 hours** (night included as experiment; drop nights later if results are weak).

**Season ethics:** season must not be wrong (no summer green in February). Prefer refusal over a pretty lie.

**Attribution (in drawer):** Open-Meteo (CC-BY 4.0), ECCC (open data licence), SmartAtlantic/CIOOS (CC-BY 4.0).

---

## 6. Dream dial (0–10) — open design space


| Dial   | Behavior                        | img2img denoise        | ControlNet weight | IP-Adapter | LoRA weight |
| ------ | ------------------------------- | ---------------------- | ----------------- | ---------- | ----------- |
| **0**  | Real morning, locked (anchored) | ~0.35                  | ~0.9              | ~0.7       | ~0.2        |
| **2**  | Slight atmospheric drift        | ~0.5                   | ~0.75             | ~0.6       | ~0.4        |
| **5**  | Interpretive; identity legible  | ~0.7                   | ~0.5              | ~0.4       | ~0.6        |
| **8**  | Dreamlike; identity strains     | ~0.85                  | ~0.3              | ~0.2       | ~0.8        |
| **10** | Dissolves — the truest state    | ~0.95 + seeded defocus | ~0.1              | ~0.05      | ~1.0        |


*(Indicative schedule; tune during dial experiments. As the dial rises the real-frame anchor lets go and the LoRA "memory" takes over — the ghost drifting off the rocks.)*

**Control modes (all remain live options — decide per context):**

1. **Artist-only** — Adam sets dial.
2. **Visitor / exhibition** — UI control or physical dial in a gallery.
3. **Data-driven** — dial derived from another signal (fog, wave height, wind, visibility, solar elevation, model confidence). Weather deciding how hard the place dreams.
4. **Doris's dial** — the named collaborator holds a remote control over the dream variable. Human authority over the hallucination; keeps the oral-history ethic alive in a computational piece.

**M6 public default (locked):** **artist-only, dial = 0.** Produce many dial sweeps privately during development; visitor / data-driven / Doris modes stay open but do not block the first public window.

---

## 7. Failure modes (conceptual, not bugs)

Cloudberry failed from cold, dark, power, modem. Dreamberry inherits that honesty — but its primary "failure" is reframed as its **truest state**.

### Primary — Identity collapse (the truest state)

When the ghost cannot hold the window (low confidence, high dial, undertrained night, bad season fit), the image **dissolves / defocuses / softens** rather than inventing a false sharp place. This is not an error screen — it is the dead camera failing to grip the rocks, and it is honored as such. Detected via **DINOv2 kNN + horizon-edge** check; rendered as a **deliberate seeded defocus** (never emergent mush) — see §5.

### Secondary — Weather silence → **hold**

When Open-Meteo / WYI / buoy feeds fail or are stale beyond tolerance: **do not generate a new frame**. Leave `current/current.webp` untouched; update `current/status.json` (`hold:true`, `failure_mode:"weather_silence"`, `last_success_at`). The dream stays; the sensors went quiet — waiting, like the Pi that never woke.

### Tertiary — Provider / GPU outage → **white noise / static**

When Modal/GPU (or the generation path) fails after retries: show a **white-noise / static field** (or swap `current` to a noise asset) and set `failure_mode:"signal_lost"`. Different from weather silence: the *channel* is dead — broadcast failure, not a sleeping cabin. Next successful hour restores the window.

**Hold vs noise:** weather silence = presence stuck in time; signal lost = no dream at all. Keep both through **M6**; do not merge them into one aesthetic.

---

## 8. Dataset & curation

Documented decisions for preparing the ~1,652 originals:

- **Exclude selfie / non-window:** `2018-02-26T11:54:20.000Z_GOPR4086.JPG` (indoor test selfie) — **out of training and retrieval**.
- **Malfunction bursts are KEPT.** Clusters of many frames within minutes (e.g. Oct 20 / Oct 28 / Sep 15) were **manual tests**, not glitches — they are real images of the view and stay in the corpus (unless they are non-window like the selfie above).
- **Near-duplicates: dedupe.** Many calm/clear hours are nearly identical; downweight or dedupe so training isn't dominated by "calm afternoon."
- **Night: separate bucket.** Train/evaluate night apart; it is experimental and may be dropped from public if weak.
- **Dawn / dusk: keep in the main (day) set — do not split like night (for now).** Golden-hour / civil-twilight frames are well represented in the 8–20 capture window and are signaled by solar-elevation tokens in the weather schema. A third bucket only if M3 eval shows noon↔golden-hour confusion; then revisit.
- **Cabin shadows: reproduce.** Geometric cabin/roof shadows on the landscape are part of the window (the body of the place cast into the view). Do not exclude shadow frames; do not ask the model to ignore them. When solar geometry implies a cast, the dream may show it. Prefer a low-shadow frame as geometry `canonical_frame` so ControlNet edges aren’t dominated by a black wedge.
- **Barrel/fisheye distortion: keep first (authentic GoPro look).** A **de-fisheyed** variant is an explicit later experiment.
- **Aspect ratio: 4:3** end to end; hourly/archive output ~4000×3000; print upscale on demand only.
- **Time source: EXIF `DateTimeOriginal`**, not the filename timestamp, for pairing historical weather.
- **Coverage skew:** dense Aug–Oct, thin Nov–Mar — the machine will know summer better than February. Held as content (memory is uneven), not silently corrected.

---

## 9. Presentation (first public / M6 intent)

- **One live image** at `/dreamberry` — window, not archive UX. **No text overlay and no honesty mark on the image itself** for the web piece.
- **Honesty lives in the drawer**, same grammar as Cloudberry's photograph-details drawer (EXIF / camera / map). Dreamberry's drawer holds:
  - **Generation** — labeled generated; base + LoRA/model version; dial value + control mode; generated-at timestamp; last-success / hold / signal_lost state
  - **Weather** — the condition packet used for this frame (Open-Meteo @ cabin, WYI, buoy waves, solar elevation) + data attributions
  - **Image** — dimensions, seed, anchor-frame id, validator scores, failure mode if any
- Image stays clean; details are opt-in via the drawer (↑↓ / toggle), not dashboard chrome.
- **Public = one current frame only; private = full hourly archive** (+ JSON sidecars). Web is a window, not a second gallery.
- **Gallery seam (in conversation, not merged):** in a physical exhibition, the honesty/telemetry lives on a **separate screen or wall panel tethered to the image** — the dream and its provenance in dialogue across a gap, never printed onto the dream itself.
- No cross-link from `/cloudberry/archive/` until the piece is solid.
- Exhibition path later: physical dial (incl. Doris's), room-as-window, dual channel with archive stills — beyond the first web spike.

---

## 10. Repo, shipping, and work tracking

### Repository

- **New GitHub repo:** `adamsimms/dreamberry` — all Dreamberry code, docs, training notes, orchestration, and window UI. (Siblings `adamsimms/waves` and `adamsimms/windows` are separate projects; Dreamberry shares the buoy data source with Waves but is its own thing.)
- **Not** in `pinchards.is` (archive stays sacred). Canonical brief + weather schema live in this repo under `docs/`. Pinchards may keep a short pointer only.
- **art.adamsimms.xyz** serves `/dreamberry` (assemble or mount from Dreamberry build artifacts — same family as other art sections).

### Infrastructure (v1)

24 images/day is trivial GPU (~12–24 GPU-hrs/mo) — the axis is **reliability + low babysitting**, not cost.

**Cloudflare verdict (validated):** Cloudflare is the **right delivery home**, not the right **compute/orchestrator**.


| Layer                                            | Verdict                                 | Why                                                                                                                                                                         |
| ------------------------------------------------ | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **GPU + hourly cron**                            | **Not Cloudflare** → **Modal**          | Workers cannot run SDXL/ControlNet; Workers Cron calling an external GPU = two failure surfaces, no built-in retry. Modal collapses schedule + GPU into one Python process. |
| **Object storage (gen archive + current frame)** | **Yes — R2**                            | Zero egress, S3 API for Modal writes, already holds Cloudberry images; custom domain + CDN for `current/current.webp`.                                                               |
| **Public window site**                           | **Yes — Pages under art.adamsimms.xyz** | Matches the art family; static window + drawer; no need for a second host.                                                                                                  |
| **All-Cloudflare**                               | **Wrong**                               | Would force Workers→external GPU anyway; free Worker CPU limits make orchestration awkward.                                                                                 |
| **Zero-Cloudflare**                              | **Viable escape hatch**                 | all-Modal (Volume + web endpoint) if you ever leave CF — same generation code.                                                                                              |


- **Modal does both scheduling and GPU** (`modal.Cron` hourly → weather fetch → gate → generate on **L40S**, base model + LoRA + ControlNet baked into a Volume).
- **Storage/delivery on Cloudflare R2 + Pages:** `private/archive/YYYY/MM/DD/HH.png` + `.json`; `public/current/current.webp`; `public/current/status.json`. Prefer a **dedicated Dreamberry R2 bucket** (or clear `dreamberry/` prefixes) — never write into Cloudberry image buckets.
- **Dead-man switch:** **healthchecks.io** (free).
- **Hold behavior:** on weather-silence, leave `public/current/current.webp` untouched and update only `status.json`.
- **Signal-lost behavior:** on GPU/provider outage, publish noise/static as current (or dedicated noise asset) + `failure_mode:"signal_lost"`.
- Identity-collapse frames *do* update the pointer (a successful "failure").
- **Cost:** ~$0–20/mo effective; worst realistic ~$50.

### Issues as the plan

Track work as **GitHub Issues**: [#1–#24](https://github.com/adamsimms/dreamberry/issues). Prefer issues over a backlog doc. Labels: `dataset`, `model`, `weather`, `window`, `infra`, `concept`, `docs`, `blocked`.

**Naming:** milestones use `M` (milestone), not `v` (version). M0–M7 are delivery chunks. Agent routing: [AGENTS.md](../AGENTS.md).

### Milestone deliverables


| Milestone                       | Done when                                                                                           | Issues       |
| ------------------------------- | --------------------------------------------------------------------------------------------------- | ------------ |
| **M0 — Dataset**                | Curated JPEGs + EXIF times + ERA5 packets ready                                                     | #2–#4        |
| **M1 — Weather conditioning**   | `compose_prompt` + weather-NN anchor index offline                                                  | #5–#6        |
| **M2 — Dream engine**           | SDXL+ControlNet+anchor runs; `canonical_frame` + dial schedule                                      | #7–#8        |
| **M3 — Quality gates**          | Collapse + season validators; dial-0 eval baseline                                                  | #9–#11       |
| **M4 — Hourly generation path** | Weather → generate+gate → sidecar → SUPIR (ad-hoc OK)                                               | #12–#15      |
| **M5 — Platform**               | Modal hourly cron + R2 public/private + honest hold                                                 | #16–#17, #19 |
| **M6 — Public window**          | `art.adamsimms.xyz/dreamberry` live (artist dial 0) + drawer + about                                | #18, #20–#22 |
| **M7 — Forgetting**             | Containered dreams-about-dreams (+ de-fisheye); first public adapter untouched; end timing variable | #23–#25      |


---




## 11. Build sequence

Build **one milestone at a time** (issues in paren):

1. **M0 Dataset** (#2–#4)
2. **M1 Weather conditioning** (#5–#6)
3. **M2 Dream engine** (#7–#8)
4. **M3 Quality gates** (#9–#11) — offline dial-0 baseline
5. **M4 Hourly generation path** (#12–#15)
6. **M5 Platform** (#16–#17, #19)
7. **M6 Public window** (#18, #20–#22)
8. **M7 Forgetting** (#25 spike → #23–#24) — after the live window is solid; container first

---

## 12. Open decisions (non-blocking)

- `canonical_frame` locked: `2017-09-18T09:59:44.000Z_GOPR2537.JPG` (backup `GOPR2479`)
- Whether nights stay after first month of results
- Whether dawn/dusk need their own bucket after M3 eval (default: no — stay in day set)
- Success bar beyond baseline (how close to GoPro is "enough")
- Drawer field list / copy; about-text wording for the held Indigenous debt
- Whether the private gen log is ever exhibited as abundance-sublime
- **M7 spike (before opening forgetting):** climate/geography container rails; variable end-timing mechanism; mix schedule — no hard calendar date yet
- Whether/when to bring Doris's voice (oral history) into the piece
- When to open visitor / data-driven / Doris dial modes (**M6** stays artist-only @ 0)
- After M3: whether to A/B FLUX / Z-Image / Flux Klein (only if dial-0 lock is solid and look is hated)

---

## 13. Naming note

**Dreamberry** keeps the berry lineage (bakeapple / Cloudberry) and allows night without contradiction. Internal artifacts may use `dreamberry-lora`, `dreamberry-window`, etc.

---

## Decisions log

Delta only — full rationale lives in the sections above.

**2026-07-20:** Title, repo, URL, hourly 24h (night experimental), drawer honesty (no overlay), archive sacred/separate, public = current frame / private = full archive, EXIF pairing, quality over cost.

**2026-07-20 (architecture):** Dead-camera-dreaming reframe; identity collapse as truest state; weather as only live truth; M7 forgetting arc; ControlNet + weather-NN lock (LoRA mid-dial only); Open-Meteo primary; JSON sidecars; Modal → R2 → Pages (see §5, §7, §10). Schema: [DREAMBERRY-WEATHER-SCHEMA.md](DREAMBERRY-WEATHER-SCHEMA.md).

**2026-07-21:** Milestones M0–M7 (`M` not `v`); former “v1 window” split into M4/M5/M6. Agent routing → [AGENTS.md](../AGENTS.md).

**2026-07-21 (locks):** Canonical `GOPR2537` (backup `GOPR2479`); dawn/dusk in day set; print on-demand; SDXL until post-M3; weather silence → hold / GPU → `signal_lost`; reproduce cabin shadows; exclude selfie `GOPR4086`; M7 container spike #25 before forgetting (no hard end date).
