# Subagent Log (append-only)

Record every subagent invocation. Subagents share the parent's blindspots; agreement is not
verification.

## Entry format
### <YYYY-MM-DD HH:MM TZ> — <task ID>
- Subagent type / scope: <...>.
- Prompt summary: <...>.
- Output summary: <...>.
- Action taken on result: <accepted / rejected / verified independently by ...>.

---

### 2026-07-01 19:40 CT — PA.005 prep (research, parallel background)
- Subagent type / scope: 2× general-purpose, read-only web research, run in parallel while PA.004 was built.
- Prompt summary: (1) minimal I-JEPA recipe for a small ViT on single RTX 5090, 96×96 grayscale glyphs;
  (2) augmentation pipeline + statistics to shrink metric-M CI on the 54-compound bottom quartile.
- Output summary: (1) ViT-Tiny/8 (~5.5M each) + narrow predictor (~0.6M), patch 8 → 144 tokens, EMA
  0.998→1.0, AdamW lr 1.5e-3 cosine, bf16, target-LayerNorm to avoid collapse; MAE-at-seam shares the
  loop (pixel target + light decoder). (2) "non-overlapping 95% CI" is low-power; **paired McNemar on
  identical eval instances detects 2pp at ~3-5× smaller n**; budget ~150 eval + ~100 train aug-instances/
  class, held-out font; **any affine/elastic warp must transform seam_bbox or the mask misaligns**.
- Action taken on result: NOT auto-applied. Feeds the PA.005 decision packet (ViT size, augmentation)
  and raises a pre-registration question for Ramchand (McNemar vs non-overlapping-CI ε rule, DEC-0009).
  Findings to be verified against the I-JEPA paper before implementation, not trusted on agent say-so.
