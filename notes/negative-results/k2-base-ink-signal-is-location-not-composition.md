# Negative result — K2's base→sign signal is sign LOCATION, not base-ink composition

Run: `phase1-k2probe-001` (TASK P1.002). Date: 2026-07-02. Metric file:
`runs/phase1-k2probe-001/metrics.json`. Encoder: pixel32 ridge probe on the augmented font-holdout
index (train noto / eval held-out nirmala), inherent-'a' forms excluded.

## What we predicted

The K2 premise (spec §3): *a supervised probe predicts the vowel-sign class from the consonant-base
region well above chance*, motivating the seam-masking prior — the idea being that the **base ink's
shape** (ligature reshaping, positional cues) tells you which sign composes with it.

## What we found

| Measurement | Overall | glyph (separable) | diff (ligature) |
|-------------|--------:|------------------:|----------------:|
| base-region probe | **0.509** [0.503, 0.515] | 0.604 | 0.291 |
| sign-location control (bbox rectangle on blank) | **0.623** | 0.695 | 0.457 |
| majority / chance | 0.091 | — | — |

Base-region beats chance ~5.6× → the **K2 kill-gate PASSES** (exploitable structure exists; do not
kill). **But the signal is sign LOCATION, not base-ink composition:** a control that sees only the seam
bounding-box rectangle (no base ink) **beats the base-region probe in every stratum** (0.695 > 0.604
glyph; 0.457 > 0.291 diff). The base-ink's independent contribution under a linear pixel probe is
negligible — and *lowest* exactly in the ligature ('diff') stratum where base×sign composition should
be strongest.

## Why (mechanism)

- For cleanly-separable ('glyph') aksharas the base consonant is essentially sign-invariant; masking the
  sign leaves a hole whose **position encodes which sign it was** (aa on the right, i top-right, e/o
  marks on the left, …). The probe reads the hole, not the base.
- For ligature ('diff') forms, masking the fused region destroys much of the glyph, leaving little base
  ink; the residual is weakly predictive, and a black hole on a dark ground is a weaker locator than the
  control's bright rectangle — hence base < location even there.

## Implication (does NOT kill K2; DOES weigh on the thesis)

- The contract's K2 gate is "beats chance" — it does, decisively — so this is **not** a kill. Sign
  location is legitimately available to the JEPA predictor (it is told which positions to reconstruct).
- **The motivating story weakens, honestly:** "the base *shape* tells you the sign" is not supported by
  a linear pixel probe; what tells you the sign is *where* it is. This raises the stakes on K1: if the
  exploitable structure is largely location, block-masking JEPA (which also encodes masked-region
  position) may match seam-masking on M. That is precisely the cheap baseline K1 must defeat.
- Caveat on the caveat: a *learned* encoder (the JEPA context encoder) may extract base-ink composition
  that a raw-pixel ridge cannot. K2 is a data-level premise floor, not the ceiling. K1/K3 remain the
  adjudicators.

## Action

- Surface prominently at LAUNCH-A / G1 (recorded in DEC-0016). Do not oversell the premise in the paper:
  report base→sign with the location-control ablation and the glyph/diff split, not a bare "51% ≫ 9%".
- Consider (future) a base-ink-only variant that removes the location cue (e.g. re-centre each masked
  region to a canonical position) to measure pure compositional signal — optional, not gating.
