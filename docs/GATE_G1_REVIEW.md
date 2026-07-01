# Gate G1 Review — Cheap-Baseline Falsification (MANDATORY)

## Purpose

G1 is the make-or-break gate. It blocks all of Phase 2+ until the simplest non-mechanism
explanations have been **run on metric M and failed to explain the effect**. This instantiates the
lab's Cheap-Baseline-Falsification rule and the spec's own kill criteria. Per the spec: *"the paper
lives or dies here."*

## Gate Status

Status: Not yet approved. Approval is recorded in `docs/DECISION_LOG.md`; this file preserves the
review evidence.

## Null Hypothesis Under Test

Mechanism **seam-masked JEPA (latent target)** is hypothesized to beat baselines
**{block-masking JEPA, MAE-at-seam}** on **M = bottom-quartile-frequency akshara top-1 accuracy**.
If either baseline matches seam-JEPA within **ε = 2.0 pp with overlapping 95 % bootstrap CIs
(n ≥ 3 seeds)**, the hypothesis is falsified → re-scope. The **base→sign premise probe (K2)** is a
prior kill-gate: if it cannot beat chance clearly, terminate before scaling.

## Required Evidence

| Requirement | Evidence (path) | Status |
|-------------|-----------------|--------|
| ε + cutoff pre-registered before runs | `docs/DECISION_LOG.md` (P1.001) | Missing |
| K2 premise probe result on M's split | run-id `phase1-k2probe-001`, `metrics.json` | Missing |
| seam-JEPA × n≥3 seeds on M | run-ids `phase1-sweep-seamjepa-seed*` | Missing |
| block-JEPA × n≥3 seeds on M (K1 baseline) | run-ids `phase1-sweep-blockjepa-seed*` | Missing |
| MAE-at-seam × n≥3 seeds on M (K3 baseline) | run-ids `phase1-sweep-maeseam-seed*` | Missing |
| Comparison table vs ε with CIs | `notes/decision-gates/g1-cheap-baseline.md` | Missing |

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
