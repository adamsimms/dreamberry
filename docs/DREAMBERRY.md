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
- **Sacred as product, remix outside:** the Cloudberry corpus stays closed inside the artworks (no generated frames mixed into Cloudberry R2; Dreamberry frames labeled generated in the drawer). Separately, Cloudberry stills, public Dreamberry window frames, and the private hourly dream archive are licensed **CC BY 4.0** for reuse outside the piece. Code stays **MIT**. See [NOTICE](../NOTICE). Weather upstreams and model weights keep their own deeds.
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

- **1,652** Cloudberry JPEGs, the training slice (`data/manifest.json`; R2: `art-adamsimms-xyz-cloudberry-images`). The public archive is 1,955; cite that number (§8).
- Fixed frame from cabin *Precious Memories* (`49.2026°N, 53.4859°W`), Aug 2017–Mar 2018
- GoPro HERO4 Black, **4:3, 4000×3000**, visible barrel/fisheye distortion
- Dense Aug–Oct; thinner winter; few true night frames — night is experimental



### Generation architecture (v1 — resolved by pipeline spike)

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



### Weather → conditioning (resolved by weather spike)

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

**Cadence:** hourly, **24 hours** (night included as experiment; drop nights later if results are weak). First-attempt seed is **hour-derived** (hash of the weather hour) so dial-0 can twitch between hours without raising denoise; same hour stays replayable. **Night lighting:** when `solar_elevation < −6°`, dial stays artist-set (usually 0) but effective denoise/ControlNet/IP nudge darker (DREAM033 A/B values in `config/dream.yaml:night_lighting`) so bright auto-exposed night anchors do not keep the window lit.

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


*(Indicative schedule from the pipeline spike; tune during dial experiments. As the dial rises the real-frame anchor lets go and the LoRA "memory" takes over — the ghost drifting off the rocks.)*

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

Same hold grammar when a night/twilight packet has **no honest dark archive anchor** after luminance/band gates (`failure_mode:"no_honest_night_anchor"`) — do not invent daylight from the geometry master (#27).

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



### What the corpus shows about Cloudberry's end

Checked 2026-09-18 against `data/manifest.json`, the public pinchards.is catalog and the recovered Pi SD card. The corpus is fixed; this changes only if an open question below closes.

- **Cite 1,955.** That is the public archive. The 1,652 training slice is an internal figure (`data/manifest.json`, taken before the July 2026 catalog additions). The 303 extra public files are all ISO 800, 1/2 s night-mode frames inside Aug 2017 to Mar 2018; they fill no silence.
- **Black hours while capture still ran.** 439 public frames are ISO 800 (434 also 1/2 s). On 3 Feb 2018 the GoPro wrote a normal window at 13:59 UTC (`GOPR3955`) and a near-black frame at 14:59 UTC (`GOPR3956`) with the sun about 23 degrees up. Failure lived in the photographs before the final silence. Per-frame lists: [`data/evidence/iso800.csv`](../data/evidence/iso800.csv) and the 55-frame visual pass [`data/evidence/class-c-visual-pass.csv`](../data/evidence/class-c-visual-pass.csv) (16 void, 37 dim window, 2 bright disk; no frost or smear confirmed).
- **Silences.** 55 calendar days have no frame. The longest, 33 days (14 Nov to 16 Dec 2017), is a camera or camera-connection failure, not a dead Pi: the card kept hourly wakes and logs GoPro `410 Gone` and Wi-Fi timeouts from 1 Dec ([cabinberry card logs](https://github.com/adamsimms/cloudberry/tree/main/docs/field/cabinberry-card)). Then 13 days (13 to 25 Feb 2018), 5 days (1 to 5 Jan 2018), and shorter gaps.
- **The end.** The last frame, `GOPR4132` (1 Mar 2018), is a successful winter dusk. The ending is the absence of a next hour.

Do not claim: the last frame shows the camera dying of frost; every dark JPEG is a malfunction (night and dusk are content); clock drift blacked out `GOPR3956` (the shutter was the Blink and the Hero4 meter); the Pi died in the 33-day gap.

Still open: whether `GOPR4102`'s truncation is capture-time or a later copy; how the recovered card's Hero3 test run maps onto the public Hero4 series.

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



### Infrastructure (v1 — resolved by infra spike)

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



### Work tracking

Plan and status live in GitHub [milestones](https://github.com/adamsimms/dreamberry/milestones) (M0 to M7; `M` for milestone, not version) and issues, not here. Agent and model routing: [AGENTS.md](../AGENTS.md).

---

## 11. Open decisions (non-blocking)

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
- Sleep: Dreamberry has no sleep state today. Whether it gets one (solar and battery, gallery power-down) and how it looks is open; it would be distinct from hold and signal lost (§7)

---



## 12. Naming note

**Dreamberry** keeps the berry lineage (bakeapple / Cloudberry) and allows night without contradiction. Internal artifacts may use `dreamberry-lora`, `dreamberry-window`, etc.

---



## Decisions log

One line per change, saying what changed and where. The body above is the current state; git keeps the history.

**2026-07-20 (founding):** Title, URL and repo; the reframe ("the dead camera dreaming"; identity collapse is the truest state); weather as the only truth; forgetting as the ending (M7); geometry lock plus a real-frame anchor; symmetric weather schema; provenance sidecar; honesty in the drawer, never on the image; archive sacred and separate; held tensions (Indigenous debt, family authority). §1 to §8.

**2026-07-20 (spikes):** Generation on SDXL with a real-frame anchor (§5); deterministic weather schema ([DREAMBERRY-WEATHER-SCHEMA.md](DREAMBERRY-WEATHER-SCHEMA.md)); Modal for cron and GPU, R2 and Pages for delivery (§10).

**2026-07-21 (design pass):** Canonical frame locked; dawn and dusk stay in the day set; print upscale on demand; JSON sidecar only; weather silence holds, GPU failure is signal lost; selfie excluded; one live frame, full private archive. §5, §7, §8, §11.

**2026-07-22 (exhibition):** Physical presentation contract moved to [DREAMBERRY-EXHIBITION.md](DREAMBERRY-EXHIBITION.md).

**2026-07-23 (hour-derived seeds):** Dial-0 first-attempt seed = blake2 of `open_meteo_hour_utc` (+ `base_seed` salt). Same hour replayable; successive hours can micro-vary under identity lock. Absolute override via `seed_base` / `--seed-base` only.

**2026-07-23 (Modal cost cut):** Hourly path publishes SDXL-native on A10; SUPIR (~4000×3000) on demand only (`upscale_archive`). Gate exhaustion or publish failure is `signal_lost` for that hour. Target ~$2 to 4/day. §10.

**2026-07-25 (night lighting):** At dial 0, `solar_elevation < −6°` applies a solar-driven parameter overlay (values from DREAM033 A/B). Public dial label unchanged; sidecar `dial_params` records effective scales.

**2026-09-18 (Cloudberry's end, from the files):** §8 records what the corpus shows; per-frame lists in `data/evidence/`.

**2026-10-15 (collapse-loop research):** The research trains on the Cloudberry photographs, then runs a collapse loop: dreams return to the corpus, and originals retire a few at a time. Two measures: distance to the nearest real photograph, and spread inside a batch. The public window stays the current screen until that trained model exists. Pinchard's weather stays the only live weather. Finland is not photographed into the model.

**2026-10-16 (twilight honesty, [#27](https://github.com/adamsimms/dreamberry/issues/27)):** Night-side weather-NN prefers the same USNO solar band, rejects auto-exposed bright inits above a luminance gate, and never falls back to the day canonical. Empty honest night pool → hold (`no_honest_night_anchor`). Config: `dream.yaml:anchor_honesty`.

**2026-10-16 (dual license, [#39](https://github.com/adamsimms/dreamberry/issues/39)):** Code/docs remain **MIT**. Media grant **CC BY 4.0** for public Dreamberry frames, Cloudberry stills used here, and the private hourly dream archive. Sacred/closed stays *product* language; reuse outside the piece is explicit. Weather upstreams and third-party weights unchanged. Recorded in [NOTICE](../NOTICE).

**2026-11-02 (docs pass):** Agent routing and the milestone plan moved out (AGENTS.md, GitHub milestones); log reduced to one line per change.

**2026-11-02 (counts):** §5 and §8: cite 1,955 (the public archive); 1,652 is the internal training slice.
