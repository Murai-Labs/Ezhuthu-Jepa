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

## Update 2 (2026-07-02) — recipe iteration (option A) did NOT reverse it; both baselines exceed the mechanism

Ramchand chose (A). Added **LR cosine decay** (`_lr_at`) and swept steps; also ran block at the matched
recipe for a fair K1 read.

| arm | recipe | metric_M |
|-----|--------|----------|
| seam_jepa | 16k cosine | **0.290** [.280,.300] (best latent) |
| seam_jepa | 50k cosine | 0.212 [.204,.221] — **worse** (eff-rank 39.7→20.2: degrades with scale) |
| **block_jepa** | **16k cosine (matched)** | **0.335** [.325,.345] |
| mae_seam | 8k | 0.532 [.521,.542] |
| pixel baseline | — | 0.359 |

- Cosine helped seam (0.239→0.290) but not past the pixel baseline; the full 50k budget made it **worse**
  (representation degrades, effective rank falls).
- **K1 is REVERSED at the matched recipe:** block-JEPA (0.335) beats seam-JEPA (0.290), non-overlapping
  CIs, beyond ε = 2 pp. The block-masking baseline wins.
- **K3 is REVERSED:** MAE-at-seam (0.532) ≫ seam-latent-JEPA (0.290). The pixel-target baseline wins.
- So **both mandated cheap baselines exceed the mechanism** — the Section 3 falsification condition (at
  1-seed pilot scale; the formal gate wants n ≥ 3, but the signal is strong and consistent).

Bottom line: option A (recipe iteration) was executed and the mechanism still loses to block-masking and
to MAE. This is a cheap-baseline kill signal (DEC-0018). Recommended last cheap datapoint before deciding:
**MAE-at-block vs MAE-at-seam** — does the seam *mask* help at all with a pixel target, or is seam not
special even there? Then re-scope/reframe or conclude (Ramchand's call). Do NOT launch the full sweep.
