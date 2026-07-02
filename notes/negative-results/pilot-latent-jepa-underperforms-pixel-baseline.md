# Negative result — pilot: latent I-JEPA underperforms the raw-pixel baseline (blocks LAUNCH-A)

Runs: `phase1-pilot-{seam,block,mae}-seed0` (pretraining) + `phase1-pilotprobe-{…}-001` (metric_M).
Date: 2026-07-02. 1 seed, 8,000 steps, ViT-Tiny/8, mask_ratio 0.25, constant LR 1e-3 after warmup.
**Not a K1/K3 result** (1 seed, no CI adjudication across seeds) — a pilot health check.

## What we expected

A pilot that smoke-passes: the loop runs at full scale, the loss converges, and the trained JEPA
encoder yields a linear-probe metric_M **above the weak PixelEncoder baseline** (0.359) — the minimum
bar for "the SSL objective learned something useful" and a precondition for LAUNCH-A.

## What we found

| arm (metric_M, held-out font) | context encoder | **target encoder (I-JEPA downstream)** |
|-------------------------------|----------------:|---------------------------------------:|
| seam_jepa (latent)  | 0.255 | **0.239** [0.230, 0.248] |
| block_jepa (latent) | 0.286 | **0.326** [0.316, 0.336] |
| mae_seam (pixel)    | — | **0.532** [0.521, 0.542] |
| PixelEncoder baseline (reference) | | 0.359 |

- **Both latent arms fall below the raw-pixel baseline (0.359).** A ViT-Tiny/8 I-JEPA at this
  scale/recipe produces representations *worse than downsampled pixels* for akshara recognition.
- **The target-encoder fix did not rescue them.** We hypothesised the probe was undervaluing the latent
  arms by exporting the CONTEXT encoder instead of the I-JEPA downstream EMA TARGET encoder; saving and
  probing the target moved block 0.286→0.326 and seam 0.255→0.239 — still below pixels. So this is a
  genuine recipe/scale deficiency, not an eval-protocol artifact.
- **MAE-at-seam (pixel target) dominates (0.532).** The dense per-pixel signal learns good features; the
  sparse latent-prediction target does not, here.
- Loss curves: latent arms dip then plateau ~0.03–0.05 by ~4–6k steps under **constant LR** (no cosine
  decay); MAE's MSE still descending at 8k.

## Why this blocks LAUNCH-A

Launching the full n≥3-seed sweep now would (a) compare two latent encoders that are worse than raw
pixels — the seam-vs-block (K1) contrast would be noise between broken encoders; and (b) hand K3 to
MAE-at-seam as an artifact of an under-baked latent recipe, not a real "pixel target beats latent"
finding. The pilot caught this for ~1 GPU-hour instead of ~15. **Do not launch the sweep until latent
JEPA is at least competitive with the pixel baseline on the pilot.**

## Leading hypothesis + next steps (DEC-0017)

My from-scratch I-JEPA is simplified vs the paper. Most likely missing:
1. **LR cosine decay** (the loss plateaued under constant LR; decay-to-zero commonly unlocks better
   representations) — the cheapest, highest-value change.
2. Recipe fidelity: multi-block context/target sampling, weight-decay schedule, target LayerNorm,
   mask-scale, predictor capacity — verify against the I-JEPA paper (the PA.005 note flagged this).
3. Simply more scale/steps (secondary; loss already plateaus, so schedule matters more than raw steps).

Decision (escalated): (A) iterate the recipe and re-pilot until latent ≥ pixels [recommended, cheap];
(B) reframe to "seam, not target" (MAE-at-seam), which the contract explicitly permits; (C) if iteration
fails, conclude honestly that the latent mechanism loses to the cheap baselines. This is precisely the
Murai-Labs thesis in action: the fancy latent outer objective must earn its keep over simpler targets —
so far, at pilot scale, it has not.
