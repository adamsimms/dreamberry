# M3 — Quality gates

Implements brief [DREAMBERRY.md](DREAMBERRY.md) §Validators / §Failure modes
(issues #9–#11). Two failure modes made concrete, plus a dial-0 eval baseline.

## The two gates

### Identity collapse (#9) — `dream/gates/identity.py`, `embed.py`, `horizon.py`

The ghost cannot grip the rocks. Detected two ways:

1. **DINOv2 kNN distance** — how far the generated frame sits from the *real*
   Cloudberry-frame distribution (a reference index of archive embeddings).
2. **Horizon-edge displacement** — how far the sea/sky boundary has wandered vs
   the canonical geometry frame.

**Dial-aware** (the crux): below `enforced_below_dial` (default 3.0) the window
must hold — a collapse returns action `regen_or_hold` (regenerate with a new seed
or hold the last good frame; never a false sharp place). At or above that dial,
collapse is **expected and honored** — action `honored_dissolve`, rendered by the
seeded defocus already in `dream/dial.py`.

### Season lock (#10) — `dream/gates/season.py`

Layer 1 (hard same-season retrieval) is enforced upstream in M1. Layer 2 is a
**calibrated CLIP zero-shot** check on the rendered frame. The refusal is
**asymmetric**, matching the container ethic: warm/green in a cold season
(the forbidden "summer-green February" climate teleport) is **refused**;
dreaming *colder* than the date stays within the cold-maritime container and is
only a soft **warning**.

## Thresholds

All in `config/gates.yaml` — **defaults, to be tuned against the baseline**:

| key | default | meaning |
|---|---|---|
| `identity_collapse.dino_distance_fail` | 0.45 | DINOv2 cosine-distance collapse cutoff |
| `identity_collapse.horizon_displacement_fail` | 0.06 | horizon drift (fraction of height) |
| `identity_collapse.enforced_below_dial` | 3.0 | below this dial, collapse → regen/hold |
| `season_lock.refuse_margin` | 0.05 | CLIP margin before a warm-in-cold refusal |

## Build references (once)

Embeds archive frames (DINOv2) and estimates CLIP season-class bias:

```bash
# smoke: stratified ~120-frame sample
PYTHONPATH=. .venv/bin/python scripts/build_gates_refs.py --cap 120
# full: all curated day frames
PYTHONPATH=. .venv/bin/python scripts/build_gates_refs.py
```

Writes `data/gates/dino_index.npz` and `data/gates/season_calibration.json`
(gitignored, regenerable).

## Eval baseline (#11)

```bash
PYTHONPATH=. .venv/bin/python scripts/eval_dream.py --n 8
```

Holds out a stratified set (season × precip), generates dial-0 with
**leave-one-out** anchor + reference (the held-out frame is excluded from both
the weather-NN anchor pool and the DINOv2 reference, so scores aren't
self-matched), and scores CLIP similarity + LPIPS vs the real frame plus the two
gates. Writes per-frame stills/sidecars, `baseline.json`, and `baseline.md` under
`data/gates/eval/`.

## Tests

```bash
PYTHONPATH=. .venv/bin/python -m pytest dream/tests/test_gates.py -q
```

Pure-logic coverage (no model downloads): horizon math, dial-aware collapse
verdict, asymmetric season verdict, DINOv2 kNN + leave-one-out exclusion.
