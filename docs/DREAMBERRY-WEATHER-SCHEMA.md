# Dreamberry — Weather → Image Conditioning Schema (v1)

> Companion to [DREAMBERRY.md](DREAMBERRY.md). Defines the **deterministic** mapping
> from numeric weather/ocean/sky/astronomy data → conditioning (prompt string +
> feature vector) for the fixed Pinchard's Island window.
>
> **Symmetry contract (non-negotiable):** the functions in this document are the
> single source of truth. The *same* code runs (a) at **captioning time** on the
> historical weather at each archive photo's EXIF `DateTimeOriginal`, and (b) at
> **inference time** on the live packet. Training vocabulary == live vocabulary.
> If a token can appear at inference, it must have been derivable at captioning,
> and vice-versa. No token is allowed to exist on only one side.

- **Scene:** single fixed 4:3 camera view — cabin window over ocean + rocky islands.
- **Cabin coords:** `49.2026°N, −53.4859°W` (Pinchard's Island, NL).
- **Hemisphere:** Northern. **Timezone for season/solar:** local NL (`America/St_Johns`, UTC−3:30).
- **Corpus:** ~1,652 Cloudberry GoPro JPEGs, Aug 2017 – Mar 2018.

---

## 0. Design principles

1. **Coarse buckets, not raw numbers.** The model sees a small, stable vocabulary.
   Continuous values (23.4°C, 812 m visibility) are quantized to tokens so training
   and inference land in the same discrete space.
2. **Priority order is fixed.** Tokens are emitted in a fixed slot order so the model
   learns positional grammar. Empty slots are simply omitted (never `none`/`n/a`).
3. **Season and precipitation dominate; raw temperature is a weak modifier.** Prevents
   "summer-green February" failures (see [DREAMBERRY.md §4 Season ethics](DREAMBERRY.md)).
4. **Every threshold is authoritative.** Cloud→oktas (METAR/WMO), fog/mist (WMO No. 782),
   precip (WMO 4677 via Open-Meteo), sea state (WMO 3700 / Douglas), wind (Beaufort),
   light (USNO twilight + golden-hour). Sources listed at the end.
5. **Graceful degradation.** Any missing input drops its slot rather than emitting a
   guess. Enough missing high-weight inputs → **weather silence** (withhold frame).

---

## 1. Field list (final conditioning set)

### 1.1 Included — drive tokens AND the retrieval vector

| Field | Source | Unit | Role |
|---|---|---|---|
| `cloud_cover` (total) | Open-Meteo @ cabin | % | sky token (oktas / METAR) |
| `visibility` | Open-Meteo @ cabin | m | fog/mist/haze token |
| `weather_code` | Open-Meteo @ cabin | WMO 4677 | precip token |
| `relative_humidity_2m` | Open-Meteo @ cabin | % | mist vs haze (with visibility) |
| `wave_ht_sig` | SmartAtlantic buoy | m | sea-state token |
| `wind_speed_10m` | Open-Meteo @ cabin (fallback WYI) | km/h | wind token (Beaufort) |
| `solar_elevation` | computed | deg | time/light token |
| `month` (+ hemisphere) | timestamp | — | season token (hard lock) |

### 1.2 Included — modifiers / retrieval only

| Field | Source | Role |
|---|---|---|
| `temperature_2m` | WYI (primary) / Open-Meteo | Weak "frost / freezing" atmosphere modifier only; **never** overrides season or precip. |
| `wind_direction_10m` | Open-Meteo | Retrieval vector only (onshore vs offshore changes spray/haze); no token in v1. |
| `shortwave_radiation` | Open-Meteo | Retrieval tie-breaker for "bright vs flat" daylight; no token (light token comes from solar geometry + cloud). |

### 1.3 Excluded (with rationale)

| Field | Why excluded from tokens |
|---|---|
| `dew_point_2m`, `apparent_temperature` | Redundant with temp+RH; not visible in a landscape. |
| `precipitation` (mm) | `weather_code` already encodes type+intensity as a token; mm kept only as a retrieval tie-breaker. |
| `cloud_cover_low/mid/high` | v1 uses total only (one clean okta bucket). Reserve layered clouds for a later chapter. |
| `wind_gusts_10m` | Correlated with `wind_speed_10m`; adds noise to a static frame. |
| `wave_ht_max`, `wave_period`, buoy `sea_surface_temp`, `air_temp` | Not legible in the fixed frame; buoy is 59 km offshore. Kept out of tokens; `wave_period` may enter retrieval as a low weight later. |
| `wind_direction` as a token | Not reliably legible in the frame; retrieval-only. |
| ECCC WYI as a token source | Used as a **fallback/cross-check** for temp/wind only; Open-Meteo @ cabin is the token authority for spatial consistency with ERA5 archive pairing. |

**Pairing rule (symmetry):** at captioning, all "@ cabin" fields come from the
**Open-Meteo Historical/ERA5 Archive API** at the EXIF instant; at inference they come
from the **Open-Meteo Forecast API** (current hour). Same variables, same code path.
Buoy history via ERDDAP time query; WYI history via ECCC climate archive.

---

## 2. Bucketing tables

All functions are pure: `value → token | null`. `null` ⇒ omit the slot.

### 2.1 `cloud_cover` (%) → sky descriptor  — *oktas / METAR SKC–FEW–SCT–BKN–OVC*

Cloud cover in % is converted to oktas by `okta = round(cloud_cover_pct / 12.5)`
(0–8). METAR/WMO sky-cover contractions map as below. Open-Meteo's own
`weather_code` uses the same coarse split (0 clear / 1 mainly clear / 2 partly cloudy
/ 3 overcast), so we align to it.

| cloud_cover % | oktas | METAR code | **token emitted** |
|---|---|---|---|
| 0 – 6 | 0/8 | SKC / CLR | `clear sky` |
| 7 – 31 | 1–2/8 | FEW | `mostly clear sky` |
| 32 – 56 | 3–4/8 | SCT | `partly cloudy sky` |
| 57 – 93 | 5–7/8 | BKN | `mostly cloudy sky` |
| 94 – 100 | 8/8 | OVC | `overcast sky` |

Boundaries are the okta midpoints of the METAR ranges: FEW=1–2, SCT=3–4, BKN=5–7,
OVC=8 (0.5-okta cut points → 6.25 / 31.25 / 56.25 / 93.75 %). *(WMO No. 782; NWS
METAR decode.)*

### 2.2 `visibility` (m) + `relative_humidity_2m` (%) + `weather_code` → obscuration

Priority: **fog/mist (water)** beats **haze (dry)**. WMO No. 782 aviation thresholds:
fog `< 1000 m`; mist (BR) `1000–5000 m` reduced by water droplets; haze/smoke (HZ/FU)
reported only when visibility `≤ 5000 m`. WMO No. 782 uses RH `> 95%` as the mist/fog
(wet) marker; we use `RH ≥ 90%` as a robust wet/dry split (common operational value).

Apply in order; first match wins:

| # | Condition | **token emitted** |
|---|---|---|
| 1 | `weather_code ∈ {45,48}` OR `visibility < 1000` | `dense fog` if `visibility < 400` else `fog` |
| 2 | `1000 ≤ visibility < 5000` AND `RH ≥ 90` | `misty` |
| 3 | `1000 ≤ visibility < 5000` AND `RH < 90` | `hazy` |
| 4 | `5000 ≤ visibility < 10000` | `light haze on the horizon` |
| 5 | `visibility ≥ 10000` (or null → treat as clear air, see §6) | *(omit — clear air)* |

`< 400 m` split for `dense fog` follows the aviation LIFR/CAT-III boundary (heavy fog);
it is optional but improves the "islands vanish" extreme. *(WMO No. 782; metar-taf BR/HZ.)*

### 2.3 `weather_code` (WMO 4677, Open-Meteo subset) → precipitation descriptor

Full interpretation table as published by Open-Meteo (identical across Forecast/ERA5
and ICON/ECMWF endpoints). Codes 45/48 are consumed by §2.2 (obscuration), not here.

| weather_code | Open-Meteo meaning | **token emitted** |
|---|---|---|
| 0 | Clear sky | *(none — sky slot only)* |
| 1 | Mainly clear | *(none)* |
| 2 | Partly cloudy | *(none)* |
| 3 | Overcast | *(none)* |
| 45 | Fog | → §2.2 `fog` |
| 48 | Depositing rime fog | → §2.2 `fog` + atmosphere `rime frost` |
| 51 | Light drizzle | `light drizzle` |
| 53 | Moderate drizzle | `drizzle` |
| 55 | Dense drizzle | `heavy drizzle` |
| 56 | Light freezing drizzle | `freezing drizzle` |
| 57 | Dense freezing drizzle | `heavy freezing drizzle` |
| 61 | Slight rain | `light rain` |
| 63 | Moderate rain | `rain` |
| 65 | Heavy rain | `heavy rain` |
| 66 | Light freezing rain | `freezing rain` |
| 67 | Heavy freezing rain | `heavy freezing rain` |
| 71 | Slight snowfall | `light snow` |
| 73 | Moderate snowfall | `snow` |
| 75 | Heavy snowfall | `heavy snow` |
| 77 | Snow grains | `snow grains` |
| 80 | Slight rain showers | `passing rain showers` |
| 81 | Moderate rain showers | `rain showers` |
| 82 | Violent rain showers | `heavy rain showers` |
| 85 | Slight snow showers | `snow showers` |
| 86 | Heavy snow showers | `heavy snow showers` |
| 95 | Thunderstorm (slight/moderate) | `thunderstorm` |
| 96 | Thunderstorm + slight hail | `thunderstorm with hail` |
| 99 | Thunderstorm + heavy hail | `thunderstorm with hail` |

*(Open-Meteo docs, "WMO Weather interpretation codes (WW)".)* Note 95/96/99 hail is
Central-Europe-only in Open-Meteo and effectively never fires for NL; kept for symmetry.

### 2.4 `wave_ht_sig` (m) → sea-state descriptor — *WMO 3700 / Douglas sea scale*

WMO code 3700 (wind-sea, = Douglas sea scale). **Rule from source:** the exact bounding
height belongs to the *lower* category (a 4.00 m sea is "rough", not "very rough"). We
collapse the 10 official degrees into 6 scene-legible tokens.

| wave_ht_sig (m) | WMO 3700 degree(s) | official term | **token emitted** |
|---|---|---|---|
| `0` | 0 | Calm (glassy) | `glassy calm sea` |
| `> 0 – 0.10` | 1 | Calm (rippled) | `calm rippled sea` |
| `> 0.10 – 0.50` | 2 | Smooth (wavelets) | `calm sea` |
| `> 0.50 – 1.25` | 3 | Slight | `slight sea` |
| `> 1.25 – 2.50` | 4 | Moderate | `moderate sea` |
| `> 2.50 – 4.00` | 5 | Rough | `rough sea` |
| `> 4.00 – 6.00` | 6 | Very rough | `very rough sea` |
| `> 6.00` | 7–9 | High–Phenomenal | `heavy stormy sea` |

Bounds inclusive on the lower side per WMO 3700. If buoy offline → see §6 (fall back to
wind-derived proxy or omit). *(WMO 3700 / Douglas sea scale; en.wikipedia Sea state.)*

### 2.5 `wind_speed_10m` (km/h) → wind descriptor — *Beaufort force scale*

Open-Meteo default wind unit is **km/h** (request `wind_speed_unit=kmh` explicitly to lock
symmetry). Beaufort limits in km/h below; collapse 13 forces into 6 tokens.

| wind_speed_10m (km/h) | Beaufort force | Beaufort name | **token emitted** |
|---|---|---|---|
| `< 6` | 0–1 | Calm / light air | `still air` |
| `6 – 19` | 2–3 | Light–gentle breeze | `light breeze` |
| `20 – 38` | 4–5 | Moderate–fresh breeze | `breezy` |
| `39 – 61` | 6–7 | Strong breeze – near gale | `strong wind` |
| `62 – 88` | 8–9 | Gale – strong gale | `gale-force wind` |
| `≥ 89` | 10–12 | Storm – hurricane | `storm-force wind` |

Cut points are exact Beaufort km/h boundaries (2=6, 4=20, 6=39, 8=62, 10=89).
*(RMetS / Met Office Beaufort tables; WMO.)*

### 2.6 `solar_elevation` (deg) → time-of-day / light descriptor — *USNO twilight + golden hour*

Angles are the geometric center of the Sun relative to the horizon. USNO twilight
definitions: civil 0…−6°, nautical −6…−12°, astronomical −12…−18°. Golden hour is
conventionally sun `−4°…+6°`; blue hour `−6…−4°`. Emits **two** things: a `time-of-day`
token and, when relevant, a `light` token.

| solar_elevation (deg) | phase | **time token** | **light token** |
|---|---|---|---|
| `< −18` | night | `night` | *(none)* |
| `−18 … −12` | astronomical twilight | `deep twilight` | *(none)* |
| `−12 … −6` | nautical twilight | `twilight` | *(none)* |
| `−6 … −4` | civil twilight / blue hour | `dawn` or `dusk`¹ | `blue hour light` |
| `−4 … +6` | golden hour | `dawn` or `dusk`¹ | `golden hour light` |
| `+6 … +15` | low sun | `early morning` or `late afternoon`¹ | `low warm sunlight` |
| `+15 … +35` | mid daylight | `daytime` | `soft daylight` |
| `> +35` | high sun | `midday` | `bright overhead sun` |

¹ Morning vs evening chosen by sign of the sun's hour angle / whether time is before or
after solar noon (deterministic from the same ephemeris).

**NL note:** at 49.2°N the sun's *maximum* elevation is ≈ 64° at summer solstice but only
≈ 17° at winter solstice. So `> +35` ("high sun") is physically a **summer-only** token,
and in Dec–Feb the light naturally tops out at `low sun`/`mid daylight`. This is desirable:
it couples light to season for free. **Light-token suppression:** if `cloud_cover ≥ 57%`
(BKN/OVC), suppress `golden/blue/low warm/bright` light tokens and emit `flat overcast light`
instead — an overcast sky has no golden hour. *(USNO Rise/Set/Twilight defs; timeanddate.)*

### 2.7 `month` (+ hemisphere) → season token — *meteorological seasons, NL-adjusted*

Northern-hemisphere meteorological seasons by month, with an explicit NL late/harsh shift
(winter conditions bleed into spring; true summer is short). Season is a **hard lock** used
both as a token and as a retrieval gate (§4).

| months | base season | **season token** | NL note |
|---|---|---|---|
| Dec, Jan, Feb | winter | `winter` | Deep winter; snow/ice expected. |
| Mar, Apr | early spring | `late winter` | **Snow persists**; frame still wintry. Token deliberately `late winter`, not `spring`. |
| May | spring | `spring` | Ice out, bare/greening. |
| Jun, Jul, Aug | summer | `summer` | Short green season; dense archive coverage. |
| Sep, Oct | autumn | `autumn` | Storms, fog, low warm light. |
| Nov | late autumn | `late autumn` | Pre-winter; grey, windy. |

Rationale for `late winter` over `spring` in Mar–Apr: the corpus (and NL reality) shows
snow into spring; labeling those frames `spring` would teach the model green/thaw cues that
are wrong. The retrieval season-gate (§4) treats `late winter` as adjacent to both `winter`
and `spring`. *(Corpus is Aug 2017–Mar 2018; Mar frames are wintry.)*

### 2.8 `temperature_2m` (°C) → optional atmosphere token (weak modifier)

Emitted **only** as a subtle atmosphere cue, appended last, and **never** allowed to change
season or precip. Skipped entirely if a precip token already implies the state (e.g. `snow`).

| temperature_2m (°C) | condition | **atmosphere token** |
|---|---|---|
| `≤ −5` | hard freeze, no active precip | `frozen, frost-rimed` |
| `−5 … 0` | freezing, no active precip | `frost` |
| `0 … 3` AND `RH ≥ 90` | cold + damp | `raw damp cold` |
| otherwise | — | *(omit)* |

Guard: if precip token ∈ {snow*, freezing*, snow grains} → omit atmosphere token (avoid
"snow, frost, frozen" pile-ups). Season + precip carry the cold; temperature only tints it.

---

## 3. Prompt composition

### 3.1 Fixed scene prefix (trigger)

Every caption/prompt begins with the identical trigger phrase that binds the LoRA to this
one frame. Use a rare token so it doesn't collide with base-model priors:

```
cldbry window view of Pinchard's Island, Newfoundland
```

`cldbry` is the unique trigger word (deliberately not a dictionary word). It is present in
**100% of training captions** and **100% of live prompts** — this is what makes the model
draw *this* window rather than a generic seascape.

### 3.2 Slot order (fixed)

```
<TRIGGER>, <season>, <time-of-day>, <light>, <sky>, <obscuration>, <precip>, <sea state>, <wind>, <atmosphere>
```

Rules:
- Emit slots in this exact order; **omit** any slot whose function returned `null`.
- Never emit placeholder words for empty slots.
- Exactly one token per slot (the bucket functions guarantee this).
- Join with `, `. No trailing style tags in v1 (LoRA carries the photographic look).
- `<obscuration>` (fog/mist/haze) sits before `<precip>` because it dominates the whole
  frame's legibility.

### 3.3 Reference implementation (pseudocode — single source of truth)

```python
def compose_prompt(pkt):
    # pkt: normalized weather packet (same shape for archive + live)
    slots = [TRIGGER]                       # "cldbry window view of Pinchard's Island, Newfoundland"
    slots += [season_token(pkt.month)]                         # §2.7  (always present)
    tod, light = solar_tokens(pkt.solar_elevation, pkt.month, pkt.hour_angle)  # §2.6
    slots += [tod]                                             # always present
    if pkt.cloud_cover is not None and pkt.cloud_cover >= 57:  # overcast kills golden hour
        light = "flat overcast light" if tod in DAY_TOKENS else None
    slots += filt([light])                                    # optional
    slots += filt([sky_token(pkt.cloud_cover)])               # §2.1 optional if cloud null
    slots += filt([obscuration_token(pkt.visibility, pkt.rh, pkt.weather_code)])  # §2.2
    slots += filt([precip_token(pkt.weather_code)])           # §2.3 optional
    slots += filt([sea_state_token(pkt.wave_ht_sig)])         # §2.4 optional if buoy null
    slots += filt([wind_token(pkt.wind_speed_10m)])           # §2.5 optional if wind null
    slots += filt([atmosphere_token(pkt.temperature_2m, pkt.rh, precip_present)])  # §2.8
    return ", ".join(filt(slots))

def filt(xs): return [x for x in xs if x]   # drop None/empty — never emit placeholders
```

The identical `compose_prompt` runs on ERA5-archive packets (captioning) and live packets
(inference). That is the symmetry guarantee.

### 3.4 Worked examples

Each shows a realistic packet → the exact emitted string.

**A. Foggy October morning**
`month=Oct, solar_elev=+3°(am), cloud_cover=88%, visibility=600m, RH=98%, weather_code=45, wave_ht_sig=0.4m, wind=14km/h, temp=8°C`
```
cldbry window view of Pinchard's Island, Newfoundland, autumn, dawn, flat overcast light, mostly cloudy sky, fog, calm sea, light breeze
```
*(golden light suppressed by overcast; fog from code 45 + vis<1000; no precip token — 45 handled as obscuration; sea "calm" = smooth 0.1–0.5 m.)*

**B. Clear February noon, snow on ground**
`month=Feb, solar_elev=+16°, cloud_cover=3%, visibility=40000m, RH=62%, weather_code=0, wave_ht_sig=1.1m, wind=22km/h, temp=−9°C`
```
cldbry window view of Pinchard's Island, Newfoundland, winter, daytime, soft daylight, clear sky, slight sea, breezy, frozen, frost-rimed
```
*(no precip now, but winter + temp≤−5 gives the frozen atmosphere token; "high sun" impossible in Feb at 49°N — tops out ~17°, so mid daylight.)*

**C. Overcast windy November dusk**
`month=Nov, solar_elev=−5°(pm), cloud_cover=100%, visibility=15000m, RH=85%, weather_code=3, wave_ht_sig=3.2m, wind=57km/h, temp=4°C`
```
cldbry window view of Pinchard's Island, Newfoundland, late autumn, dusk, flat overcast light, overcast sky, rough sea, strong wind
```
*(civil-twilight dusk; blue-hour light suppressed by 100% cloud → flat overcast light; no obscuration, vis≥10 km; no precip, code 3.)*

**D. Golden-hour September evening, calm sea**
`month=Sep, solar_elev=+2°(pm), cloud_cover=20%, visibility=45000m, RH=70%, weather_code=1, wave_ht_sig=0.15m, wind=8km/h, temp=15°C`
```
cldbry window view of Pinchard's Island, Newfoundland, autumn, dusk, golden hour light, mostly clear sky, calm sea, light breeze
```
*(golden hour −4…+6° with mostly-clear sky keeps the golden light token; sea 0.10–0.50 m = calm.)*

**E. Stormy January afternoon, rough sea, snow**
`month=Jan, solar_elev=+9°, cloud_cover=100%, visibility=1800m, RH=95%, weather_code=75, wave_ht_sig=5.1m, wind=76km/h, temp=−3°C`
```
cldbry window view of Pinchard's Island, Newfoundland, winter, late afternoon, low warm sunlight, overcast sky, misty, heavy snow, very rough sea, gale-force wind
```
*(low-sun band +6…+15°; but note: with 100% cloud the light token would be suppressed to `flat overcast light`.* Corrected emission below.*)*
```
cldbry window view of Pinchard's Island, Newfoundland, winter, late afternoon, flat overcast light, overcast sky, misty, heavy snow, very rough sea, gale-force wind
```
*(atmosphere token omitted: precip present (heavy snow) suppresses `frost`. vis 1800 m + RH≥90 → misty; code 75 → heavy snow; wave 5.1 → very rough; wind 76 → gale-force.)*

---

## 4. Weather-nearest-neighbor retrieval

Goal: given a live packet, find the closest **real archive frame(s)** (same-season only) to
use as a structural anchor / img2img base / retrieval-augmented reference.

### 4.1 Feature vector (per archive frame and per live packet)

Built by the **same** code as prompts, from the same packet. Mixed numeric + categorical.

| # | Feature | Transform | Normalized range | Weight `w` |
|---|---|---|---|---|
| 1 | `solar_elevation` | `sin(elev)` then min-max to [0,1] over [−18°,+65°] | 0–1 | **3.0** |
| 2 | `cloud_cover` | `/100` | 0–1 | **2.0** |
| 3 | `visibility` | `clip(vis,0,20000)/20000`, then `sqrt` (compress high end) | 0–1 | **2.5** |
| 4 | `precip_class` | ordinal: none0 / drizzle1 / rain2 / freezing3 / snow4 / storm5 → `/5` | 0–1 | **2.5** |
| 5 | `wave_ht_sig` | `clip(w,0,6)/6` | 0–1 | **1.5** |
| 6 | `wind_speed_10m` | `clip(v,0,100)/100` | 0–1 | **1.0** |
| 7 | `wind_dir_onshore` | `cos(θ − θ_shore)` mapped to [0,1]; `θ_shore` = onshore bearing | 0–1 | **0.5** |
| 8 | `rh` | `/100` | 0–1 | **0.5** |
| 9 | `temperature_2m` | min-max over [−20,+25]°C | 0–1 | **0.5** |

Design choices per the brief: **cloud / visibility / precip / solar-elevation dominate**
(weights 2.0–3.0); **raw temperature is deliberately weak** (0.5). `precip_class` is the
ordinal severity family from §2.3 (not the raw code) so "light rain" and "rain" are near.
Solar elevation uses `sin` so the perceptually-flat night region compresses and the
horizon/low-sun region (where the scene changes fastest) spreads out.

### 4.2 Distance metric

Weighted Euclidean over the normalized vector:

```
d(a, b) = sqrt( Σ_i  w_i · (a_i − b_i)² )
```

- Circular features (wind direction) use the `cos` encoding above so 350° and 10° are near.
- `precip_class` distance is ordinal (family gap), intentionally treating snow↔rain as far.

### 4.3 Season gate (hard constraint)

Retrieval candidates are filtered to the **same season family** *before* distance is computed:

- Allowed set = `{same season}`. Adjacency: `late winter` ↔ {`winter`,`spring`}; otherwise
  no cross-season matching (no summer frame for a winter query — season ethics).
- If the same-season candidate pool is too thin (thin-winter problem, see corpus), widen to
  the adjacent season **only within the same thermal regime** (winter↔late winter, autumn↔late
  autumn), never into summer.

### 4.4 Missing-buoy / missing-data handling in retrieval

- **Buoy offline (`wave_ht_sig` null):** drop feature #5 from *both* vectors for that query
  and renormalize weights (`w_i / Σ w_present`) so distance stays comparable. Optionally
  synthesize a wave proxy from `wind_speed_10m` via Beaufort→probable-wave-height (Beaufort
  tables give probable wave heights) — flagged low-confidence and given half weight.
- **Visibility null:** treat as `visibility = 20000` (clear air) **only if** `weather_code`
  is non-fog and `RH < 90`; otherwise drop feature #3 and renormalize.
- **Any null feature:** dropped-and-renormalized rather than zero-filled (zero-fill would bias
  toward "calm/clear").
- Return top-`k` (k=3–5); the artist/generator can pick or blend.

---

## 5. Training caption strategy

1. **Trigger first, always.** Every caption starts with `cldbry window view of Pinchard's
   Island, Newfoundland`. This is the identity anchor; do not vary it.
2. **Weather tokens via §3.** Exactly the `compose_prompt` output — nothing hand-written, so
   captions and live prompts share vocabulary.
3. **Include time-of-day: yes.** Solar tokens (§2.6) are in every caption. Light is the
   biggest visual variable in the corpus; withholding it would make the model average over
   lighting and lose golden-hour/overcast distinctions.
4. **Avoid caption overfitting:**
   - Keep vocabulary **small and closed** (the tables above — ~50 tokens total). No free text,
     no per-image adjectives, no synonyms. A closed vocabulary is the main anti-overfit lever.
   - **No timestamps, dates, filenames, EXIF, or coordinates** in captions.
   - Do **not** add stylistic tokens ("beautiful", "4k", "GoPro"): the LoRA learns the look;
     tokens should describe only *conditions*.
   - Because slots are omitted when null, common conditions produce short captions and rare
     ones longer — this is fine and prevents forcing tokens onto frames that don't warrant them.
5. **Night frames (experimental):** frames with `solar_elevation < −6°` get `night`/`twilight`
   time tokens and **no light token**. The corpus has few true-night frames (per
   [DREAMBERRY.md §4](DREAMBERRY.md)); tag them `night` honestly and expect weak results.
   Option: exclude `< −12°` (nautical/astronomical) frames from v1 training and re-introduce in
   the night chapter, rather than teaching the model to hallucinate detail in near-black frames.
6. **Class-balance note:** the corpus is dense Aug–Oct, thin in winter. Caption code doesn't
   fix this, but the retrieval season-gate (§4.3) and optional loss weighting should compensate;
   flag thin-season frames in the dataset manifest.

---

## 6. Missing-data / failure behavior

Two layers: **per-slot omission** (graceful) and **weather silence** (withhold frame).

### 6.1 Per-slot rules

| Missing input | Behavior |
|---|---|
| `cloud_cover` null | omit sky slot; also skip overcast light-suppression (light token stands). |
| `visibility` null | omit obscuration slot (do **not** guess fog). |
| `weather_code` null | omit precip slot; obscuration falls back to visibility+RH only. |
| `wave_ht_sig` null (buoy offline) | omit sea-state slot; do not invent. Retrieval uses §4.4 proxy. |
| `wind_speed_10m` null | try WYI wind; if also null, omit wind slot. |
| `solar_elevation` | **never** null — computed from lat/lon+timestamp. Always present. |
| `month` | never null. Season always present. |
| `temperature_2m` null | omit atmosphere token. |

Minimum viable prompt = `TRIGGER + season + time-of-day` (three always-available slots). A
frame can always be captioned/generated with at least these three.

### 6.2 Weather silence (withhold a new frame)

Trigger weather silence when the **high-weight** signal is too degraded to honestly condition:

- **Staleness:** newest available Open-Meteo hour is older than the tolerance (e.g. > 3 h old),
  OR the live fetch fails entirely.
- **Core-field loss:** `cloud_cover` **and** `visibility` **and** `weather_code` all null
  (the whole sky/atmosphere channel is gone) — the scene's dominant conditioner is unknown.
- Buoy-only loss does **not** trigger silence (sea state is omittable).

On weather silence: do not generate a new frame; hold the last successful frame, keep its
timestamp visible, and surface "sensors are silent" in the details drawer, per
[DREAMBERRY.md §6 Weather silence](DREAMBERRY.md). This is a *feature* (remoteness), not an error.

### 6.3 Interaction with identity collapse

Weather silence is about **inputs**; identity collapse (blur/soften) is about **output
confidence** and lives in the generator, not this schema. This document only decides tokens,
the retrieval anchor, and when to declare inputs insufficient.

---

## 7. Closed vocabulary (complete token list)

For validation/tests — the model should only ever see these condition tokens (plus the trigger).

- **season:** `winter`, `late winter`, `spring`, `summer`, `autumn`, `late autumn`
- **time-of-day:** `night`, `deep twilight`, `twilight`, `dawn`, `dusk`, `early morning`, `late afternoon`, `daytime`, `midday`
- **light:** `blue hour light`, `golden hour light`, `low warm sunlight`, `soft daylight`, `bright overhead sun`, `flat overcast light`
- **sky:** `clear sky`, `mostly clear sky`, `partly cloudy sky`, `mostly cloudy sky`, `overcast sky`
- **obscuration:** `dense fog`, `fog`, `misty`, `hazy`, `light haze on the horizon`
- **precip:** `light drizzle`, `drizzle`, `heavy drizzle`, `freezing drizzle`, `heavy freezing drizzle`, `light rain`, `rain`, `heavy rain`, `freezing rain`, `heavy freezing rain`, `light snow`, `snow`, `heavy snow`, `snow grains`, `passing rain showers`, `rain showers`, `heavy rain showers`, `snow showers`, `heavy snow showers`, `thunderstorm`, `thunderstorm with hail`
- **sea state:** `glassy calm sea`, `calm rippled sea`, `calm sea`, `slight sea`, `moderate sea`, `rough sea`, `very rough sea`, `heavy stormy sea`
- **wind:** `still air`, `light breeze`, `breezy`, `strong wind`, `gale-force wind`, `storm-force wind`
- **atmosphere:** `frost`, `frozen, frost-rimed`, `raw damp cold`, `rime frost`

A unit test should assert every `compose_prompt` output token ∈ this set.

---

## 8. Sources

- **Open-Meteo — WMO Weather interpretation codes (WW) & variable docs:** https://open-meteo.com/en/docs
- **Open-Meteo — historical/ERA5 archive (same variables):** https://open-meteo.com/en/docs/historical-weather-api
- **Open-Meteo WeatherCode source (code→condition):** https://github.com/open-meteo/open-meteo/blob/main/Sources/App/Helper/WeatherCode.swift
- **WMO No. 782 — Aerodrome Reports and Forecasts (cloud oktas SKC/FEW/SCT/BKN/OVC; fog <1000 m, mist 1000–5000 m, haze ≤5000 m, RH marker):** https://amc.namem.gov.mn/wp-content/uploads/WMO/11.%20782_2022_edition_en.pdf
- **NWS — Decoding METARs (okta ↔ % sky cover):** https://preview.weather.gov/lzk/metar.htm
- **Pilot Institute — How to Read a METAR (oktas table):** https://pilotinstitute.com/how-to-read-metar/
- **metar-taf — fog/mist/haze & RH>80% split:** https://metar-taf.com/explanation
- **WMO Sea State code 3700 (significant wave height bands):** https://rda.ucar.edu/OS/web/datasets/d464000/docs/WMOtables.html
- **WMO Marine Services FAQ — Douglas scale sea/height terminology:** https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/marine-services/frequently-asked-questions
- **Wikipedia — Sea state (WMO/Douglas table):** https://en.wikipedia.org/wiki/Sea_state
- **Douglas sea scale:** https://en.wikipedia.org/wiki/Douglas_sea_scale
- **Royal Meteorological Society — Beaufort Wind Scale:** https://www.rmets.org/metmatters/beaufort-wind-scale
- **Met Office — Beaufort wind force scale (km/h & m/s limits):** https://weather.metoffice.gov.uk/guides/coast-and-sea/beaufort-scale
- **US Naval Observatory — Rise, Set, and Twilight Definitions (civil 6°, nautical 12°, astronomical 18°):** https://aa.usno.navy.mil/faq/RST_defs
- **timeanddate — Types of Twilight:** https://www.timeanddate.com/astronomy/different-types-twilight.html
- **Golden hour / blue hour elevation window (sun −4°…+6° / −6°…−4°):** https://en.wikipedia.org/wiki/Golden_hour_(photography)
- **SmartAtlantic Bonavista Bay buoy (ERDDAP `SMA_bonavista`):** https://www.smartatlantic.ca/erddap/
- **ECCC Pool's Island (WYI) climate/obs:** https://climate.weather.gc.ca/
