# M3 dial-0 eval baseline (n=50)

Reproducible via `scripts/eval_dream.py --n 50` (seed 20260721). Full per-frame
table + JSON live under `data/gates/eval/` (gitignored, regenerable); this file
records the baseline and the threshold calibration decision.

## Aggregates

| metric | mean | min | max |
|---|---|---|---|
| dino_distance | 0.175 | 0.085 | 0.444 |
| horizon_displacement | 0.074 | 0.044 | 0.209 |
| clip_similarity (vs real) | 0.901 | 0.623 | 0.971 |
| lpips (vs real) | 0.434 | 0.030 | 0.946 |

**Collapse actions:** 48 `pass`, 2 `regen_or_hold`
**Season actions:** 33 `pass`, 17 `warn`, **0 `refuse`**

## What the baseline established

1. **Horizon threshold calibrated 0.06 → 0.13.** Good dial-0 frames sit at a
   ~0.044–0.09 horizon-displacement noise floor. The initial 0.06 falsely flagged
   7/8 in the smoke run; at 0.13 the full run passes 48/50 and flags only genuine
   drift.
2. **`dino_distance` threshold (0.45) is well-placed.** Real-faithful frames land
   0.085–0.33; the single frame near 0.44 is a true outlier (see below).
3. **The 2 `regen_or_hold` frames are genuine failures, not false positives.**
   Both are near-black winter afternoon frames (e.g. `2018-02-03T13:59` — dino
   0.444, horizon 0.209, clip 0.648): the window did not hold, so at dial-0 the
   gate correctly withholds/regens rather than publishing a black rectangle.
4. **Season lock never false-refused.** 0 refusals across 50 frames; warns are
   benign adjacency (summer/autumn ↔ spring). The asymmetric rule (warm-in-cold
   refused, cold-in-warm warned) held.
5. **CLIP/LPIPS vs the real frame stay report-only.** They are confounded by the
   dream reflecting the *packet's* weather via a possibly-different anchor, so low
   values (e.g. a faithful winter frame at clip 0.74) are not quality failures.

## Follow-up noted (not blocking)

Some winter "day" frames are extremely dark (low sun / dusk) and dream near-black.
The gate now withholds them at dial-0; a later pass may tighten the day/night
solar-elevation split or exclude them from the anchor pool.
