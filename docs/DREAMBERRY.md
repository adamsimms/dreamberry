# Dreamberry — Project Brief

> Sibling to Cloudberry, not an extension of the archive product.
> Cloudberry stays closed and sacred — see [pinchards.is PRODUCT.md](https://github.com/adamsimms/pinchards.is/blob/main/docs/PRODUCT.md).
> Artistic lineage: [practice-forward-brief.md](https://github.com/adamsimms/pinchards.is/blob/main/docs/practice-forward-brief.md)
> (§5 “Generative afterlife of a closed corpus”).

**Status:** Build  
**Working title:** Dreamberry  
**Artist:** Adam Simms  
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

**Output (web / private archive):** generate and publish at **SDXL-native 4:3 (~1024×768)**. **SUPIR → ~4000×3000** is **on-demand only** for selected keepers / print (`modal run modal_app.py::upscale_archive`) — not on the hourly cron.

**Provenance:** **JSON sidecar only** (no embedded EXIF/XMP requirement). Fields: weather packet, seed, base+LoRA version, dial, prompt, anchor-frame id, validator scores, failure mode.

**LoRA training spec:** kohya_ss; 4:3 aspect buckets; **keep native fisheye** (de-fisheye is an M7/variant experiment); rank 32; ~2.5–4k steps; **weather-derived captions** (from the schema); season-balanced sampling; night in a separate bucket.

**Baseline success (first public lock):** at dial ≈ 0, a viewer who knows Cloudberry recognizes the same rocks / horizon / cabin-edge under plausible current weather, clearly labeled generated. Indistinguishable-from-GoPro is **not** the bar — honesty is.

### Validators (the two failure modes, made concrete)

- **Identity collapse:** **DINOv2 kNN** distance to the real-frame distribution + a **horizon-edge stability** check against the canonical edge map. Dial-aware: at low dial a collapse triggers regeneration/hold; at high dial it is *expected and honored*.
- **Season lock:** **same-season retrieval** (hard gate) + a **calibrated CLIP zero-shot** season classifier that trips a regen/refusal if the output's season mismatches the date. No summer-green February.
- **Dissolve rendering:** a **deliberate, seeded, structure-weighted defocus** — never emergent high-denoise mush. The ghost's failure to grip is composed, not accidental.



### Weather → conditioning (resolved by [weather spike](610da137-04d1-4491-92be-14fdff5d9d23))

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

**Cadence:** hourly, **24 hours** (night included as experiment; drop nights later if results are weak). First-attempt seed is **hour-derived** (hash of the weather hour) so dial-0 can twitch between hours without raising denoise; same hour stays replayable.

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


*(Indicative schedule from the [pipeline spike](8ffaca47-0a48-4ca2-b606-e878e70f4312); tune during dial experiments. As the dial rises the real-frame anchor lets go and the LoRA "memory" takes over — the ghost drifting off the rocks.)*

**Control modes (all remain live options — decide per context):**

1. **Artist-only** — Adam sets dial.
2. **Visitor / exhibition** — UI control or physical dial in a gallery.
3. **Data-driven** — dial derived from another signal (fog, wave height, wind, visibility, solar elevation, model confidence). Weather deciding how hard the place dreams.
4. **Doris's dial** — the named collaborator holds a remote control over the dream variable (see §4). Human authority over the hallucination; keeps the oral-history ethic alive in a computational piece.

**M6 public default (locked):** **artist-only, dial = 0.** Produce many dial sweeps privately during development; visitor / data-driven / Doris modes stay open but do not block the first public window.

---



## 7. Failure modes (conceptual, not bugs)

Cloudberry failed from cold, dark, power, modem. Dreamberry inherits that honesty — but its primary "failure" is reframed as its **truest state**.

### Primary — Identity collapse (the truest state)

When the ghost cannot hold the window (low confidence, high dial, undertrained night, bad season fit), the image **dissolves / defocuses / softens** rather than inventing a false sharp place. This is not an error screen — it is the dead camera failing to grip the rocks, and it is honored as such. Detected via **DINOv2 kNN + horizon-edge** check; rendered as a **deliberate seeded defocus** (never emergent mush) — see §5.

### Secondary — Weather silence → **hold**

When Open-Meteo / WYI / buoy feeds fail or are stale beyond tolerance: **do not generate a new frame**. Leave `current.png` untouched; update `status.json` (`hold:true`, `failure_mode:"weather_silence"`, `last_success_at`). The dream stays; the sensors went quiet — waiting, like the Pi that never woke.

### Tertiary — Provider / GPU / dream-path outage → **white noise / static**

When Modal/GPU fails, generation throws after retries, gates reject every attempt, or publish/R2 blows up: show a **white-noise / static field** (or swap `current` to a noise asset) and set `failure_mode:"signal_lost"`. Different from weather silence: the *channel* (or this hour's dream) is dead — broadcast failure, not a sleeping cabin. Next successful hour restores the window. Do **not** hold the previous dream over a broken hour.

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
- **Aspect ratio: 4:3** end to end; hourly/archive output **SDXL-native (~1024×768)**; SUPIR ~4000×3000 on demand for print/keepers only.
- **Time source: EXIF** `DateTimeOriginal`, not the filename timestamp, for pairing historical weather.
- **Coverage skew:** dense Aug–Oct, thin Nov–Mar — the machine will know summer better than February. Held as content (memory is uneven), not silently corrected.

---



## 9. Presentation (first public / M6 intent)

- **One live image** at `/dreamberry` — window, not archive UX. **No text overlay and no honesty mark on the image itself** for the web piece.
- **Hour-scale crossfade:** each new dream eases in over ~1 hour; cold loads mid-join via `previous.webp` + `fade_started_at` (e.g. arrive at :30 → ~50/50). Signal lost fades to noise (and back) in ~10s — in and out of the dream.
- **Honesty lives in the drawer**, same grammar as Cloudberry's photograph-details drawer (EXIF / camera / map). Dreamberry's drawer holds:
  - **Generation** — labeled generated; base + LoRA/model version; dial value + control mode; generated-at timestamp; last-success / hold / signal_lost state
  - **Weather** — the condition packet used for this frame (Open-Meteo @ cabin, WYI, buoy waves, solar elevation) + data attributions
  - **Image** — dimensions, seed, anchor-frame id, validator scores, failure mode if any
- Image stays clean; details are opt-in via the drawer (↑↓ / toggle), not dashboard chrome.
- **Public = one current frame only; private = full hourly archive** (+ JSON sidecars). Web is a window, not a second gallery.
- **Gallery seam:** in a physical exhibition, honesty/telemetry lives off the dream — separate station or with the print room — never on the image itself. Full presentation contract: **[DREAMBERRY-EXHIBITION.md](DREAMBERRY-EXHIBITION.md)**.
- No cross-link from `/cloudberry/archive/` until the piece is solid.
- Exhibition (locked direction): dream **out of the cabin window** (Mug Up parallel) — not a framed monitor; Cloudberry prints in a **separate room** (≥10 @ ~16×20/20×30); silent/slow; tide/moon as soft grip modulator; bake-off before locking medium (RGB matrix / Campbell-line LED / flexible LED curtain / fabric+fans+projection; e-ink for simple/street; matrices scale to ~10×12 ft).

---



## 10. Repo, shipping, and work tracking



### Repository

- **New GitHub repo:** `adamsimms/dreamberry` — all Dreamberry code, docs, training notes, orchestration, and window UI. (Siblings `adamsimms/waves` and `adamsimms/windows` are separate projects; Dreamberry shares the buoy data source with Waves but is its own thing.)
- **Not** in `pinchards.is` (archive stays sacred). Canonical brief + weather schema live in this repo under `docs/`. Pinchards may keep a short pointer only.
- **art.adamsimms.xyz** serves `/dreamberry` (assemble or mount from Dreamberry build artifacts — same family as other art sections).



### Infrastructure (v1 — resolved by [infra spike](08bc0b0d-f2a1-45a1-bc61-9c5dd881b807))

24 images/day at SDXL-native on A10 is modest GPU — the axis is **reliability + low babysitting**, not maximizing resolution every hour.

**Cloudflare verdict (validated):** Cloudflare is the **right delivery home**, not the right **compute/orchestrator**.


| Layer                                            | Verdict                                 | Why                                                                                                                                                                         |
| ------------------------------------------------ | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **GPU + hourly cron**                            | **Not Cloudflare** → **Modal**          | Workers cannot run SDXL/ControlNet; Workers Cron calling an external GPU = two failure surfaces, no built-in retry. Modal collapses schedule + GPU into one Python process. |
| **Object storage (gen archive + current frame)** | **Yes — R2**                            | Zero egress, S3 API for Modal writes, already holds Cloudberry images; custom domain + CDN for `current.png`.                                                               |
| **Public window site**                           | **Yes — Pages under art.adamsimms.xyz** | Matches the art family; static window + drawer; no need for a second host.                                                                                                  |
| **All-Cloudflare**                               | **Wrong**                               | Would force Workers→external GPU anyway; free Worker CPU limits make orchestration awkward.                                                                                 |
| **Zero-Cloudflare**                              | **Viable escape hatch**                 | all-Modal (Volume + web endpoint) if you ever leave CF — same generation code.                                                                                              |


- **Modal does both scheduling and GPU** (`modal.Cron` hourly → weather fetch → gate → generate on **A10**, base model + LoRA + ControlNet on a Volume). **SUPIR** is a separate on-demand L40S job for keepers/print.
- **Storage/delivery on Cloudflare R2 + Pages:** `archive/<TIMESTAMP>_DREAM###.png` + `.json`; `current/current.webp`; `current/status.json`. Prefer a **dedicated Dreamberry R2 bucket** (or clear `dreamberry/` prefixes) — never write into Cloudberry image buckets.
- **Dead-man switch:** **healthchecks.io** (free).
- **Hold behavior:** on weather-silence, leave `public/current` untouched and update only `status.json`.
- **Signal-lost behavior:** on GPU/provider outage, gate exhaustion, or publish failure, publish noise/static as current (or dedicated noise asset) + `failure_mode:"signal_lost"`.
- Identity-collapse frames *do* update the pointer (a successful "failure").
- **Cost:** target roughly **~$2–4/day** steady-state after native-only hourly (was ~$9–10/day with hourly SUPIR on L40S); on-demand SUPIR billed per job.



### Issues as the plan

Track work as **GitHub Issues**: [#1–#24](https://github.com/adamsimms/dreamberry/issues). Prefer issues over a backlog doc. Labels: `dataset`, `model`, `weather`, `window`, `infra`, `concept`, `docs`, `blocked`.

**Naming:** milestones use `M` (milestone), not `v` (version). The public artwork has no “version number” — M0…M7 are delivery chunks you can hand to Cursor as “build this.”

### Milestone deliverables (8)

About **8 milestones** is the right grain for this project: each is one focused Cursor build (≈2–4 issues), with a crisp **done-when**. Fewer than ~6 lumps too much into one chat; more than ~10 is admin without clearer handoffs.


| Milestone                       | Done when                                                                                           | Issues       | Agent                        |
| ------------------------------- | --------------------------------------------------------------------------------------------------- | ------------ | ---------------------------- |
| **M0 — Dataset**                | Curated JPEGs + EXIF times + ERA5 packets ready                                                     | #2–#4        | Composer                     |
| **M1 — Weather conditioning**   | `compose_prompt` + weather-NN anchor index offline                                                  | #5–#6        | Opus → Composer              |
| **M2 — Dream engine**           | SDXL+ControlNet+anchor runs; `canonical_frame` + dial schedule                                      | #7–#8        | Opus                         |
| **M3 — Quality gates**          | Collapse + season validators; dial-0 eval baseline                                                  | #9–#11       | Opus                         |
| **M4 — Hourly generation path** | Weather → generate+gate → sidecar → SUPIR (ad-hoc OK)                                               | #12–#15      | Composer + Opus (#14)        |
| **M5 — Platform**               | Modal hourly cron + R2 public/private + honest hold                                                 | #16–#17, #19 | Composer + Opus review (#19) |
| **M6 — Public window**          | `art.adamsimms.xyz/dreamberry` live (artist dial 0) + drawer + about                                | #18, #20–#22 | Opus + Composer (#20)        |
| **M7 — Forgetting**             | Containered dreams-about-dreams (+ de-fisheye); first public adapter untouched; end timing variable | #23–#25      | Opus                         |


**Cursor prompt pattern:** `Build milestone M0 — Dataset (issues #2–#4). Follow docs/DREAMBERRY.md. Use Composer for mechanical work.`

### Coding-agent model routing

Use the **Cursor chat model** (or subagent model) that matches the *kind* of work — not only the milestone number.


| Model                          | Use when                                                                                                                                                                     | Typical issues                                             |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| **Opus 4.8** (or current Opus) | Conceptual integrity, architecture, validators that encode failure modes, about/ethics copy, dial semantics, anything that could quietly resurrect the “live camera” fiction | #5, #7–#11, #14, #18–#19, #21–#22, #24                     |
| **Composer 2.5-fast**          | Spec already decided; mechanical implement / download / boilerplate / wiring / tests against fixed tables                                                                    | #2–#4, #6 (once vector spec frozen), #12–#13, #15–#17, #20 |
| **Either → Opus review**       | Composer implements; Opus reviews for honesty / season lock / hold behavior before merge                                                                                     | #14, #18, #19 especially                                   |


**Rules of thumb**

- If the brief already names the tool and acceptance criteria → **Composer**.
- If a wrong choice would change the *artwork* (elegy, identity collapse, weather-as-truth, labeling) → **Opus**.
- Prefer **one milestone (or one issue) per chat** when using Composer; keep Opus chats for judgment-heavy milestones (M2–M3, M6 honesty).
- Subagents: Composer for parallel mechanical tasks; Opus for synthesis / review.

**Issue → suggested model** (default; override when stuck)


| #                      | Suggested                                                 |
| ---------------------- | --------------------------------------------------------- |
| 2, 3, 4                | Composer                                                  |
| 5                      | Opus (implement) → Composer (tests) OK once tables locked |
| 6                      | Composer (after #5)                                       |
| 7, 8, 9, 10, 11        | Opus                                                      |
| 12, 13, 15, 16, 17, 20 | Composer                                                  |
| 14, 18, 19             | Opus (or Composer + Opus review)                          |
| 21, 22, 24             | Opus                                                      |
| 23                     | Composer or Opus (experiment design = Opus)               |


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
- Whether the private gen log is ever exhibited as abundance-sublime — prefer secret-but-open; see exhibition brief
- **M7 spike (before opening forgetting):** climate/geography container rails; variable end-timing mechanism; mix schedule — no hard calendar date yet
- Whether/when to bring Doris's voice (oral history) into the piece
- When to open visitor / data-driven / Doris dial modes (**M6** stays artist-only @ 0; exhibition visitor dissolve dial shelved — see exhibition brief)
- After M3: whether to A/B FLUX / Z-Image / Flux Klein (only if dial-0 lock is solid and look is hated)
- Exhibition medium lock + tide/moon grip mapping — [DREAMBERRY-EXHIBITION.md](DREAMBERRY-EXHIBITION.md) §9

---



## 13. Naming note

**Dreamberry** keeps the berry lineage (bakeapple / Cloudberry) and allows night without contradiction. Internal artifacts may use `dreamberry-lora`, `dreamberry-window`, etc.

---



## Decisions log

**2026-07-20 (initial):** Title Dreamberry; URL `art.adamsimms.xyz/dreamberry`; new repo `adamsimms/dreamberry` tracked via Issues; 24h hourly, night experimental; failures = identity collapse + weather silence; honesty in details drawer, no image overlay; archive sacred & separate; public = current frame, private = full archive; weather labels via EXIF DateTimeOriginal; solo; quality over cost.

**2026-07-20 (Opus review):**

- **Reframe:** "the dead camera dreaming," not "still running" — resolves the elegy conflict; identity collapse is the *truest state*.
- **Weather = the only truth**; real-now / dreamed-view asymmetry is the honest core.
- **Mortality:** dreams-about-dreams = built-in *forgetting* / ending (**M7**), first-class.
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
- **Infra** ([spike](08bc0b0d-f2a1-45a1-bc61-9c5dd881b807)): **Modal** (cron + GPU) → **R2** archive + `current`/`status.json` → **Pages** window; **healthchecks.io** dead-man switch; all-Modal escape hatch if leaving Cloudflare. (2026-07-23: hourly **A10** native; SUPIR on-demand.)

**2026-07-21 (milestone plan + agent routing):**

- Plan as **milestone deliverables** — use `M` not `v` (milestones ≠ software versions).
- Grain: **8 milestones (M0–M7)**; former “v1 window” split into M4 path / M5 platform / M6 public window.
- **Coding-agent routing:** Opus 4.8 for judgment; Composer 2.5-fast for mechanical/spec’d implement; Opus review for gate/hold/UI honesty.

**2026-07-21 (design decisions pass):**

- **M7:** no hard end date (variable timing); **container spike #25** before forgetting — may invent trees/placement, must not leave NL maritime climate/geography.
- **Canonical:** locked `2017-09-18T09:59:44.000Z_GOPR2537.JPG`; backup `GOPR2479`; weather-NN for weather.
- **Dawn/dusk:** stay in main day training (not a night-style separate bucket) unless M3 eval says otherwise.
- **Print:** on-demand upscale only.
- **Models:** keep SDXL; A/B FLUX/etc. only after M3 if lock solid and look hated.
- **Provenance:** JSON sidecar only.
- **Silence split:** weather → hold; GPU/provider → white noise / `signal_lost`.
- **Shadows:** reproduce.
- **Exclude:** `2018-02-26T11:54:20.000Z_GOPR4086.JPG` (selfie).
- **Public/private:** one live frame; full private archive.

**2026-07-22 (exhibition brief):** Physical presentation contract in **[DREAMBERRY-EXHIBITION.md](DREAMBERRY-EXHIBITION.md)** — out of the window; two rooms (dream vs Cloudberry prints); tide/moon grip; bake-off shortlist; e-ink simple/street track; flip-disc as sibling.

**2026-07-23 (hour-derived seeds):** Dial-0 first-attempt seed = blake2 of `open_meteo_hour_utc` (+ `base_seed` salt). Same hour replayable; successive hours can micro-vary under identity lock. Absolute override via `seed_base` / `--seed-base` only.

**2026-07-23 (Modal cost cut):** Hourly path publishes **SDXL-native** on **A10** (~32 GiB); **SUPIR ~4000×3000 on-demand only** (`upscale_archive`). Gate exhaustion / publish failure → **`signal_lost` noise** for that hour (weather silence still **hold**). Target ~$2–4/day vs ~$9–10/day with hourly L40S+SUPIR.

