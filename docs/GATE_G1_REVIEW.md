# Gate G1 Review — Cheap-Baseline Falsification (MANDATORY)

## Purpose

G1 is the make-or-break gate. It blocks all of Phase 2+ until the simplest non-mechanism
explanations have been **run on metric M and failed to explain the effect**. This instantiates the
lab's Cheap-Baseline-Falsification rule and the spec's own kill criteria. Per the spec: *"the paper
lives or dies here."*

## Gate Status

Status: **BLOCK → PROJECT CONCLUDED (2026-07-02, DEC-0019).** Decided on the **1-seed LAUNCH-A pilot**
(not the full n≥3 sweep): both cheap baselines exceed the mechanism on M, on both kill criteria. Ramchand
elected to conclude rather than spend ~15 GPU-h formalising a strongly-indicated kill. This is a
first-class negative result (§2.5), not a failure to hide.

## Null Hypothesis Under Test

Mechanism **seam-masked JEPA (latent target)** is hypothesized to beat baselines
**{block-masking JEPA, MAE-at-seam}** on **M = bottom-quartile-frequency akshara top-1 accuracy**.
If either baseline matches seam-JEPA within **ε = 2.0 pp with overlapping 95 % bootstrap CIs
(n ≥ 3 seeds)**, the hypothesis is falsified → re-scope. The **base→sign premise probe (K2)** is a
prior kill-gate: if it cannot beat chance clearly, terminate before scaling.

## Required Evidence

| Requirement | Evidence (path) | Status |
|-------------|-----------------|--------|
| ε + cutoff pre-registered before runs | `docs/DECISION_LOG.md` (DEC-0009/0013) | ✅ Done |
| K2 premise probe result on M's split | run-id `phase1-k2probe-001`, `metrics.json` | ✅ Done (PASS, caveat DEC-0016) |
| seam-JEPA on M | `phase1-pilot*-seam_jepa-*` (1 seed pilot; full sweep not run) | ⚠ Pilot only |
| block-JEPA on M (K1 baseline) | `phase1-pilot*-block_jepa-*` (1 seed pilot) | ⚠ Pilot only |
| MAE-at-seam on M (K3 baseline) | `phase1-pilot-mae_seam-*` (1 seed pilot) | ⚠ Pilot only |
| Comparison table vs ε with CIs | this file (below) + DEC-0018 | ✅ Done (pilot) |

## Pilot Comparison Table (1 seed, target-encoder probe, metric M on the augmented font-holdout eval)

| Arm | Recipe | metric_M | vs seam | vs pixel 0.359 |
|-----|--------|---------:|---------|----------------|
| seam-JEPA (mechanism) | 16k cosine | 0.290 [.280,.300] | — | below |
| block-JEPA (K1 baseline) | 16k cosine | **0.335** [.325,.345] | **+4.5 pp, non-overlapping** | below |
| MAE-at-seam (K3 baseline) | 8k | **0.532** [.521,.542] | **+24 pp** | above |
| seam-JEPA | 50k cosine | 0.212 [.204,.221] | degrades with scale | below |

**K1 verdict:** block-JEPA **exceeds** seam-JEPA beyond ε=2 pp (non-overlapping CIs) → the seam prior is
**not earned**. **K3 verdict:** MAE-at-seam **exceeds** latent seam-JEPA by ~24 pp → the latent target
**loses to the pixel target**. Both cheap baselines win. (Section 3 falsification; n=1 pilot — the full
n≥3 sweep was not run because the pilot signal is strong and consistent on both criteria, and running it
would spend ~15 GPU-h to confirm a likely kill.)

## Decision Rule

- **PASS** — K2 premise holds AND seam-JEPA beats block-JEPA on M beyond ε (non-overlapping CIs)
  AND MAE-at-seam does not capture the full win → proceed to G2.
- **BLOCK / RE-SCOPE** — any cheap baseline matches within ε. Honest reframes: MAE-at-seam captures
  it → "seam, not target"; block-JEPA matches → the seam prior is not earned; K2 fails → terminate.

## Explicit Non-Results

No degradation (K4) work begins until G1 PASSES. A BLOCK outcome is a first-class result recorded
in `notes/negative-results/`, not a failure to hide.

## Approval Template (paste into docs/DECISION_LOG.md when granted)

```
## DEC-XXXX - G1 decision
Date: <YYYY-MM-DD>
Task/Gate: G1
Decision: <PASS → G2 unblocked | BLOCK → re-scope as ...>.
Rationale: <comparison table summary vs ε, with CIs; K2 verdict>.
Evidence / Source Docs: docs/GATE_G1_REVIEW.md, notes/decision-gates/g1-cheap-baseline.md, run-ids.
Human Approval: <name> on <date>.
```
