# Seam-Masked Latent JEPA for Tamil Akshara Recognition — A Cheap-Baseline Falsification

**Ezhuthu-JEPA · negative-results report · 2026-07-02 · status: concluded (G1 = BLOCK, DEC-0019)**

## Abstract

We tested whether masking a Tamil akshara at its grapheme **seam** (the base-consonant / vowel-sign
boundary) and predicting the masked region's **latent** representation (I-JEPA style) teaches a model the
abugida's compositional rule (base × sign → akshara) better than generic masking or pixel reconstruction,
and thereby recognises rare/low-frequency compounds more accurately. On rendered multi-font Tamil at
evenings-scale (ViT-Tiny/8, ~20k augmented instances, single RTX 5090), the hypothesis is **falsified on
both of its kill criteria**. At a matched recipe: generic **block-masking JEPA (metric M = 0.335)
outperforms seam-masking JEPA (0.290)** beyond the pre-registered ε with non-overlapping CIs (K1
reversed), and **MAE-at-seam / pixel-target (0.532) far outperforms the latent target (0.290)** (K3
reversed). Both latent arms also fall below a raw-pixel linear-probe baseline (0.359), and the latent
representation *degrades* with more training. A supervised premise probe (K2) confirmed that the base→sign
signal a model could exploit is dominated by sign *location*, with only a thin base-ink compositional
component in ligatures — too weak for the latent objective to convert into a recognition advantage. The
result was reached with **~2 GPU-hours** via a 1-seed pilot, before committing the ~15 GPU-hour full
sweep. We release the benchmark, evaluation harness, rendering pipeline, and pretraining loop; the honest
negative is itself the contribution.

## 1. Hypothesis and pre-registration

**Thesis.** Masking at the base/vowel-sign seam and predicting the masked region's latent makes the model
internalise base × sign composition, yielding a recogniser that composes rare/unseen compounds from seen
parts and degrades gracefully on the long tail.

**Claims / kill criteria.**
- **K1 (primary):** seam-masked JEPA beats block-masking JEPA on bottom-quartile-frequency compounds,
  architecture/compute/mask-ratio held fixed.
- **K2 (premise):** a supervised probe predicts the vowel-sign class from the consonant-base region well
  above chance (else the seam carries no exploitable structure → kill before scaling).
- **K3 (ablation):** JEPA-at-seam beats MAE-at-seam, isolating the latent target from the seam boundary.
- **K4 (realism):** the K1 win survives manuscript-like degradation. *(Not reached.)*

**Null hypothesis (pre-registered, DEC-0009/0013).** Mechanism *seam-masked latent JEPA* is hypothesised
to beat baselines *{block-masking JEPA, MAE-at-seam}* on **M = bottom-quartile-frequency akshara top-1
accuracy**. If a baseline matches within **ε = 2.0 pp** (adjudicator: non-overlapping 95 % bootstrap CIs
across n ≥ 3 seeds; paired McNemar with Bonferroni as the primary test), the hypothesis is falsified and
the project re-scopes or concludes. ε and the bottom-quartile cutoff were fixed **before** any arm ran.

## 2. Methods

**Corpus + benchmark.** 216 uyirmei (18 consonants × 12 vowel signs) rendered at 96×96 grayscale under two
fonts — Noto Sans Tamil (OFL, reproducible) and Nirmala UI (Windows) — with HarfBuzz+FreeType shaping and
per-akshara `{base_id, sign_id, seam_bbox, seam_source}` labels. `seam_source ∈ {glyph, diff, none}`
records how cleanly the sign separates: `glyph` = a separable mark, `diff` = a ligature that reshapes the
base, `none` = the inherent-'a' form (no sign). Compound frequencies came from a 172-work **Project
Madurai** snapshot (4.85 M uyirmei counted; 207/216 seen); the bottom frequency quartile (54 aksharas)
defines metric M's stratum.

**Font-holdout augmented split.** To make a 2 pp effect adjudicable, we built ~100 train (Noto) + ~150
eval (Nirmala, **held out**) augmented instances per class (safe affine/stroke/blur/noise, with the
`seam_bbox` transformed in lockstep) — 54 k instances total, seed-frozen eval identical across arms. The
bottom-quartile eval set (n ≈ 8,100) gives a metric-M bootstrap **CI half-width ≈ 1.0 pp** (empirically
0.0102), down from ~12 pp on the tiny pre-augmentation eval.

**Metric M + harness.** An encoder-agnostic linear probe (numpy ridge on one-hot targets) fit on train,
evaluated top-1 on eval; metric M = bottom-quartile bucket accuracy, reported with 95 % bootstrap CIs and
stratified by `seam_source` and font. The harness also emits per-instance correctness for a paired
**McNemar** comparator (exact binomial < 25 discordants, else χ² with continuity; Bonferroni), the
pre-registered primary adjudicator. Frozen before any sweep.

**Pretraining loop.** One loop, one switched variable. ViT-Tiny/8 (96 px, patch 8 → 12×12 = 144 tokens;
~5.35 M-param encoder), context/EMA-target/predictor, bf16 autocast, single RTX 5090. Objective set by
config only:
- `seam_jepa` — mask a fixed-size token block **centred on the seam**; predict masked-token **latents**
  from the EMA target encoder (smooth-L1).
- `block_jepa` — same-size block at a **random** location; same latent target (K1 control: only location
  differs).
- `mae_seam` — same seam block; predict masked **pixels** (MSE), no target encoder (K3 control: only the
  target differs).

The masked-token count is a fixed fraction (mask_ratio 0.25 → 36/144), identical for every instance and
objective, so "compute/mask-ratio held fixed" is exact. Inherent-'a' forms (no seam) are excluded from
pretraining, uniformly across arms. Every run records config hash, code SHA, data hash, seed, and
environment before it starts; the I-JEPA downstream representation is the EMA target encoder.

## 3. Results

### 3.1 K2 premise — the base→sign signal is mostly *location*, weakly *composition*

A pixel ridge probe predicting the vowel-sign from the base region (sign masked out), augmented
font-holdout eval, inherent-'a' excluded (`phase1-k2probe-001`):

| | overall | glyph | diff (ligature) | chance |
|---|---:|---:|---:|---:|
| base-region → sign | **0.509** [.503,.515] | 0.604 | 0.291 | 0.091 |
| sign-location control (bbox on blank) | **0.623** | 0.695 | 0.457 | — |

The premise **passes the kill-gate** (base-region ≫ chance, ~5.6×), so we did not terminate on K2. But a
mask-geometry-only control **beats** the base-region probe in *every* stratum → the exploitable signal is
sign *location*, not base-ink shape. A follow-up **location-normalised** probe (mask sign → crop base ink →
letterbox centred; `phase1-baseink-001`) isolates the pure component: base-ink → sign = **0.331**
[.326,.336] ≫ chance, with a consonant-prediction control at 0.381 (chance 0.056) confirming the
normalisation preserved shape. Within it, glyph 0.306 vs diff 0.388 (non-overlapping) → the clean
compositional signal is the **diff−glyph gap ≈ 8.2 pp**, from ligature reshaping. Read together: a *real
but modest* base-ink compositional signal exists, concentrated in ligatures, but base→sign is
geometry-dominated — a thin prior for the mechanism to exploit.

### 3.2 The pilot — both cheap baselines beat the mechanism (K1 and K3 reversed)

A 1-seed LAUNCH-A pilot at full data scale. Metric M via the EMA-target encoder, augmented held-out font:

| Arm | Recipe | metric M | vs pixel 0.359 |
|-----|--------|---------:|:--------------:|
| seam-JEPA (mechanism) | 8k, constant LR | 0.239 [.230,.248] | below |
| seam-JEPA | **16k, cosine (best)** | **0.290** [.280,.300] | below |
| seam-JEPA | 50k, cosine | 0.212 [.204,.221] | **worse — degrades** |
| **block-JEPA** (K1 control) | 16k, cosine (matched) | **0.335** [.325,.345] | below |
| **MAE-at-seam** (K3 control) | 8k | **0.532** [.521,.542] | above |
| PixelEncoder baseline | — | 0.359 [.349,.369] | — |

- **K1 reversed:** block-JEPA (0.335) beats seam-JEPA (0.290) by 4.5 pp with non-overlapping CIs — the
  seam boundary earns *nothing* over a random block; it does worse.
- **K3 reversed:** MAE-at-seam (0.532) beats latent seam-JEPA (0.290) by ~24 pp — the latent target is
  decisively *worse* than pixel reconstruction, the opposite of the ablation's premise.
- Both latent arms fall **below the raw-pixel linear-probe baseline** (0.359); MAE clears it comfortably.
- **Degradation with scale:** extending seam-JEPA from 16k → 50k steps *lowered* metric M (0.290 → 0.212);
  a feature diagnostic shows the encoder's effective rank falling 39.7 → 20.2 over the same interval. (By
  contrast MAE's features are low-rank — effective rank 7.6 — yet highly discriminative.)

### 3.3 Recipe iteration did not reverse the direction

The first suspect was the plain constant-LR schedule. Adding **cosine LR decay** (the standard I-JEPA
schedule) improved seam-JEPA from 0.239 → 0.290 but not past the pixel baseline, and the full training
budget made it worse. Correcting the probe to use the EMA **target** encoder (the I-JEPA downstream
representation) rather than the context encoder did not help either (seam 0.255 → 0.239). The ordering
seam < block < pixels ≪ MAE is stable across every recipe variant we ran.

## 4. Interpretation

At evenings-scale on this task, the latent-prediction objective is a weak and unstable learning signal
relative to pixel reconstruction: MAE, with identical architecture/compute, produces far more
class-discriminative features and is stable, while the latent arms underperform raw pixels and degrade
with training. Independently, the seam boundary confers no advantage over a random block — consistent with
K2, where the base→sign structure a model could use is dominated by sign *location* (available to any
position-aware masker) with only a thin ligature-specific base-ink component. In short, the two ingredients
the thesis bet on — *seam boundary* and *latent target* — both lose to their cheap baselines here.

## 5. What we did not do, and honest caveats

- **n = 1 seed.** The conclusion rests on a 1-seed pilot, not the pre-registered n ≥ 3 sweep. The formal
  G1 rule wanted three seeds with non-overlapping CIs; we concluded on the pilot because the signal is
  strong, consistent across three recipe variants, and adverse on *both* kill criteria — running the full
  sweep (~15 GPU-h) would most likely spend the budget to confirm a kill. This is a stated limitation, not
  a hidden one.
- **Scale.** ViT-Tiny/8, ~20k instances, single 5090. A materially larger model/corpus, an anti-collapse
  latent recipe (e.g. VICReg-style regularisation, faithful multi-block I-JEPA masking), or ViT-Small might
  change the latent arms' absolute numbers — but `block > seam` means even the seam *mask* is not winning,
  so the prior is against a rescue under this thesis.
- **K4 not reached.** No manuscript-degradation realism work was done; G1 blocked before G2.
- **Rendered, not manuscript.** All training/eval is on rendered glyphs; the real-manuscript sample was
  reserved for validation only and never used.

## 6. Reusable artifacts (survive the conclusion)

- **Frequency-stratified Tamil akshara-recognition benchmark** + augmented font-holdout split (Project
  Madurai frequencies; bottom-quartile cutoff; held-out font; ~1 pp CI).
- **Encoder-agnostic evaluation harness** — metric M, bootstrap CIs, seam_source/font stratification, and
  a paired **McNemar** comparator.
- **Multi-font Tamil rendering + grapheme-seam-labelling pipeline** (HarfBuzz/FreeType; glyph/diff/none
  seam typing; deterministic).
- **Provenance/config contract** — five-identifier manifests, strict versioned config, schema-consumer
  audits.
- **Switchable seam/block/MAE pretraining loop** with cosine LR, EMA target, resume-state, and a
  sweep orchestrator with a LAUNCH-A gate.
- **The honest negative** — "at evenings-scale, seam-masking did not beat block-masking, and a latent
  target lost to pixel reconstruction, for Tamil akshara composition."

## 7. Methodology note — the gate worked

This is the cheap-baseline-falsification rule doing exactly its job. The mandated baselines
(block-masking, MAE-pixel-target) were *run on the paper's own metric* and *exceeded* the mechanism,
before any expensive scaling. Cost to falsify: ~2 GPU-hours and one evening, versus a full n ≥ 3 sweep,
K4 degradation suite, and a paper built on an effect that isn't there. The lab thesis — an evolutionary
or latent outer objective must expose structure the simpler baseline cannot — held: it did not, and the
project ended at the right time.

## 8. Reproducibility

Everything below is committed (text-free repo; images/checkpoints gitignored, regenerable from seeds).

- **Runs:** `pa003b-probe-aug-001` (pixel baseline), `phase1-k2probe-001` (K2), `phase1-baseink-001`
  (base-ink composition), `phase1-pilot-{seam,block,mae}-seed0` + `phase1-pilotB/C-*` (pilot + recipe
  iteration), each with `provenance.json` + `metrics.json`.
- **Configs:** `configs/phase1/{render,split,augment,probe,probe-augmented,k2_probe,base_ink_probe,pretrain,pilot,sweep}.yaml`.
- **Decisions:** `docs/DECISION_LOG.md` DEC-0009…DEC-0019; gate record `docs/GATE_G1_REVIEW.md`.
- **Negatives:** `notes/negative-results/{pilot-latent-jepa-underperforms-pixel-baseline,k2-base-ink-signal-is-location-not-composition}.md`; `notes/stuck-log.md`.
- **Code:** `src/ezhuthu_jepa/` (data, masking, eval, train, provenance, config). Regeneration commands in
  `docs/RUNBOOK.md`.
