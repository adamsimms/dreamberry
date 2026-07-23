# Dreamberry — Exhibition Brief

> Companion to [DREAMBERRY.md](DREAMBERRY.md). Presentation contract for physical
> installs — decisions only. Web window UX stays in the art brief §9.
>
> **Status:** open design — bake-off before locking Room-1 medium.

---

## 1. One sentence

Dreamberry in a gallery is the dead camera’s dream **taken out of the cabin window** —
the same live island weather and remembered frame, rematerialized as a field of light
(or a quiet changing print), with honesty and the photographic archive in other rooms.

---

## 2. Lineage (Mug Up)

*Mug Up* moved a hearth ritual outdoors — same tea and dialect, wrong architecture on
purpose. Exhibition Dreamberry does the same to the **window**: not a nicer monitor in a
frame (CABIN grammar), but the dream performed outside the architecture that made it.

References that set the light language (not to copy): **Jim Campbell** (low-res LED at
the threshold of recognition); **Leo Villareal** (discrete light as atmosphere).

---

## 3. Encounter

| Lock | Decision |
|------|----------|
| Tone | Silent and slow; sit with the field |
| Telepresence vs elegy | Both held; **telepresence first** |
| Visitor dial / “push to dissolve” | **No** — feels gimmicky |
| Occupancy / door-as-dial | Shelved for now |
| Preferred soft modulator | **Tide and/or moon** — oceanic scale, subtle, slow |
| Signal split (unchanged) | Island weather owns **image content**; third-place signal owns **grip** of the display only ([DREAMBERRY.md](DREAMBERRY.md) §4–§7) |

**Grip (open mapping):** moon illumination, tide height, and/or moonrise–moonset may
modulate brightness, dissolve, node count, or (fabric track) air on the cloth — never
fake Pinchard's weather onto the dream.

---

## 4. Spatial contract (two rooms minimum)

### Room 1 — the dream

- One luminous (or paper) presence. No drawer chrome on or beside it.
- Not a single standard monitor in a window frame.
- Medium **unlocked** until bake-off (§7); shortlist below.

### Room 2 — the archive shore

- **Cloudberry originals**, printed — series of **≥10**, about **16×20 or 20×30**.
- Smaller than the dream field; memory as a body of photographs, not a competing window.
- Labeled photographs (sacred corpus; never mixed with generated frames in the prints).

### Honesty / telemetry

- **Not** tacked beside the dream ([DREAMBERRY.md](DREAMBERRY.md) §9 gallery seam).
- Separate station or with Room 2: generated label, weather packet, hold / signal_lost,
  attributions. Dream and provenance across a gap.

### Wall text / voice

- Open: wall text, Doris’s voice, and/or another station — Indigenous debt and family
  authority acknowledged, not resolved ([DREAMBERRY.md](DREAMBERRY.md) §4).
- Not on the dream surface.

### Private gen archive

- Prefer **secret but not closed** — explore before locking out exhibition of the hourly
  log. If shown later, as abundance study, never as the public “window.”

---

## 5. Two exhibition tracks

| Track | Surface | When |
|-------|---------|------|
| **A — Gallery (sublime)** | Low-res light field, flexible LED curtain, or fabric + fans + projection | White cube / dark media room |
| **B — Simple / street** | **E-ink** (or quiet paper-like panel) | Storefront, civic window, lean show — daylight OK |

Same hourly dream pointer can feed both; bodies differ.

**Shelved for Dreamberry Room 1:** civic full-bleed glass as primary (too straightforward);
media mesh (weak up close in a small room); Refik Anadol–style fine LED spectacle;
transparent OLED (gimmick risk); commercial Lite-Brite / Everbright play walls;
Janet Echelman–scale nets (wrong craft).

**Sibling project (not this brief):** electromechanical **flip-disc** as a tide-state
instrument — oceanic, slow, separate from the color dream.

---

## 6. Room-1 medium shortlist (pre–bake-off)

| Priority | Medium | Notes |
|----------|--------|-------|
| Strong | **RGB LED matrix wall** (HUB75 / tiled panels + diffusion) | Campbell language at room scale; dim + frost; prefer coarser pitch (≈P5–P10) over fine cabinets |
| Strong | **Custom sparse LED + diffusion / cell cups** | Artist-built pitch (e.g. 25–40 mm); closer to Campbell sculpture |
| Strong | **Flexible LED curtain / soft LED fabric** | Soft architecture; not a pane |
| Strong | **Projection on a simple moving sheet** | Fabric + quiet fans behind; dream rides the cloth |
| Track B | **E-ink** | Changing print; simple / street |
| Reference only | Villareal-like sparse point fields | If content gives way entirely to atmosphere |
| Contingency | Projection on fixed surface | Finance/ops fallback; not lead |

**Matrix scale:** tiled RGB matrices scale to architectural size — **~10×12 ft (~3×3.7 m) is realistic** (Pi / LED processor + parallel chains, distributed 5 V power, wall frame). Same hourly dream → heavy downsample. Fine pitch (P2.5-class) and Anadol-style walls stay out of scope.

Legibility: need not resolve rocks across the room; vary with pitch / diffusion / cloth.
Test both “weather as light weather” and “horizon almost readable.”

---

## 7. Material bake-off (required before locking A)

Same still(s) on three bodies; score with the rubric below.

| Build | Lean $ | Solid $ | Prove |
|-------|--------|---------|------|
| **A** RGB matrix — one HUB75 panel (e.g. P4–P5 64×32/64×64) + frosted acrylic, dimmed; *or* sparse WS2812 grid ~1 m² @ 25–40 mm + cups/diffusion. ESP32/WLED or Pi + `rpi-rgb-led-matrix` | ~80–250 | ~350–600 | Campbell threshold; path to ~10×12 ft |
| **B** White sheet + 1–2 quiet fans + 1080p projector | ~250–450 | ~500–900 | Out-of-window motion |
| **C** E-ink — start small (e.g. ~13″ Affresco / Spectra-6); upsize only if medium wins | ~150–500 | ~1.7–2.4k | Street / simple print |

**Test stills:** one clear dial-0 morning; one fog/storm; one soft/collapse if available.
Optional slow dissolve (30–60 s) — piece is hourly stills, not video art.

**Rubric (1–5):** out of the window · silent & slow · telepresence · honesty of medium ·
path to room scale (~10×12 ft) · ops (power/heat/noise) · gut (prints next door, stay here).

**Build order:** A lean (HUB75 + frost first) → B lean → C lean; upgrade the winner.
If A wins language, scale with coarser tiled matrices or rebuild sparse; do not jump to fine-pitch cabinets.

---

## 8. Failure modes in the room

Unchanged semantics ([DREAMBERRY.md](DREAMBERRY.md) §7):

| Mode | Room behavior |
|------|----------------|
| Weather silence → **hold** | Field freezes on last success |
| Dream/channel → **signal lost** | Noise / static field (or e-ink equivalent of channel death) |
| Identity collapse | Honored dissolve — successful “failure”; updates the dream |

---

## 9. Open (non-blocking)

- Lock Room-1 medium after bake-off
- Target Room-1 footprint when scaling matrices (working envelope **~10×12 ft**; confirm per venue)
- Tide vs moon vs both; venue tide vs Bonavista / shared ocean
- Grip ethic if presence ever returns (tighter vs looser when watched)
- Doris remote as named authority over grip (option; not visitor UI)
- Whether private hourly archive is ever shown
- About / wall-text wording for Indigenous debt
- Permanent commission vs touring rental (changes fabricator path)

---

## 10. Decisions log

**2026-07-22 (exhibition spike):**

- Break the dream **out of the window** (Mug Up parallel); no CABIN-style framed monitor as lead.
- Encounter: silent/slow; telepresence-first; no visitor dissolve dial.
- Soft third-place modulator: **tide/moon**; occupancy shelved.
- **Two rooms:** dream field vs Cloudberry print series (≥10 @ ~16×20/20×30).
- Honesty off the dream; separate station.
- Tracks: gallery sublime (Campbell / flexible LED / fabric+fans) + **e-ink** simple/street.
- Bake-off required before locking medium; DIY LED over LiteZilla product.
- Flip-disc → separate tide project. Mesh, Anadol-fine LED, transparent OLED, Echelman nets shelved for Room 1.

**2026-07-22 (RGB matrices):** **HUB75 / tiled RGB LED matrices** named as a strong Room-1 path (dim + diffusion; prefer ≈P5–P10). Bake-off A starts with one panel + frost. Architectural scale **~10×12 ft** confirmed realistic (Pi/processor, distributed power). Fine-pitch cabinets still out.
