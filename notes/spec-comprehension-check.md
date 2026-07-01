# Spec Comprehension Check (TASK P0.001)

Source: `docs/spec/EZHUTHU_JEPA_Spec_v0.2.md` (Murai Labs · Ramchand Kumaresan · v0.2).
Written 2026-07-01 at scaffold time.

## Thesis, claims, null hypothesis (≤10 lines)

1. **Thesis:** Masking at the Tamil grapheme base/vowel-sign *seam* and predicting the masked
   region's *latent* (JEPA, not pixels) forces the model to learn base × sign → akshara, so rare/
   unseen compounds are composed from parts, not memorized as 216 atomic shapes.
2. **K1 (primary claim):** seam-JEPA > block-masking JEPA on **bottom-quartile-frequency compounds**
   (arch/compute/mask-ratio fixed; n ≥ 3 seeds; non-overlapping CIs). Aggregate accuracy does not count.
3. **K2 (premise):** a supervised probe predicts vowel-sign class from the consonant-base region ≫ chance.
4. **K3 (ablation):** seam-JEPA > MAE-at-seam ⇒ the latent target matters, not just the boundary.
5. **K4 (realism):** the K1 win survives manuscript-like degradation (missing puḷḷi, bleed, touching chars).
6. **Null hypothesis:** seam-JEPA (latent) vs {block-JEPA, MAE-seam} on M = bottom-quartile top-1
   accuracy; if a baseline matches within **ε = 2.0 pp / overlapping 95 % CIs**, the mechanism is falsified.

## Gates and required evidence

- **G0** — repo skeleton/docs/trackers/task-list/minimal package exist.
- **LAUNCH-A** — eval frozen + ε pre-registered + 1-seed pilot smoke-passed + compute ledger ⇒
  authorize the full n≥3-seed Stage-A sweep (the single most expensive run).
- **G1** — K2 premise holds AND seam-JEPA beats block-JEPA on M beyond ε AND MAE-at-seam doesn't
  capture the win. Make-or-break. Evidence: run-ids + comparison table vs ε with CIs.
- **G2** — K4: the K1 win survives degradation validated against a small real sample. PASS = manuscript
  claim earned; NARROW = clean-script-only paper (manuscript benchmark deferred to v2).
- **G3** — paper (honest negatives) + Gradio transcription-aid demo (provenanced checkpoint) + open
  recipe + frequency-stratified benchmark released.

## Mandatory cheap baselines (the G1 kill set)

1. **Block/geometric-masking JEPA** — same arch/compute/mask-ratio, only the mask boundary differs (K1).
2. **MAE-at-seam** — same seam boundary, pixel target instead of latent (K3).
3. **Base→sign supervised probe** — premise gate; kill before scaling if it can't beat chance (K2).

## Key locked decisions carried from spec §7

- v1 = rendered-core + small-real-*validation* only; full labeled real benchmark = v2 of this paper.
- Tamil only for K1–K4; Grantha named as replication target, not run in v1.
- Deliverable includes a first-class Gradio demo. Venue deferred (likely arXiv-only).

## Compute

Single RTX 5090, evenings-scale. No H100/Lambda for K1–K4. Pre-committed GPU-hour ledger gates escalation.
