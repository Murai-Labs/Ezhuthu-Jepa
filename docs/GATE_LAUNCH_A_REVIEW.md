# Gate LAUNCH-A Review — Approve the Full Stage-A Sweep

## Purpose

LAUNCH-A blocks the single most expensive run — the full n ≥ 3-seed Stage-A pretraining sweep over
{seam-JEPA, block-JEPA, MAE-at-seam} — until the evaluation is frozen, ε is pre-registered, a
1-seed pilot smoke-passes, and a compute ledger is committed. This prevents burning the RTX-5090
budget on a sweep whose result would be un-adjudicable or un-provenanced.

## Gate Status

Status: Not yet approved. Approval is recorded in `docs/DECISION_LOG.md`; this file preserves the
review evidence.

## Required Evidence

| Requirement | Evidence (path) | Status |
|-------------|-----------------|--------|
| Eval harness frozen (metric M + CIs) | `src/ezhuthu_jepa/eval/akshara_probe.py`, PA.003 | Missing |
| Frequency split frozen (bottom-quartile cutoff) | `data/rendered/split-manifest.json`, PA.002 | Missing |
| ε pre-registered **before** any sweep run | `docs/DECISION_LOG.md` (P1.001), `notes/decision-gates/g1-cheap-baseline.md` | Missing |
| 1-seed pilot smoke-passed | run-id `phaseA-smoke-001`, `metrics.json` (PA.005) | Missing |
| Objective switched by config only (identical arch/compute/mask-ratio) | `configs/phase1/pretrain.yaml`, `sweep.yaml` | Missing |
| Provenance writer operational | `src/ezhuthu_jepa/provenance.py` (P0.003) | Missing |
| Compute ledger committed | `docs/decisions/compute-ledger.md` (PA.006) | Missing |

## Explicit Non-Results

No full sweep has been launched. The pilot (when present) is a smoke check only and supports no
K1/K3 claim.

## Required Next Work Before Approval

- Complete PA.001–PA.006 and P1.001; attach each as evidence above with status flipped to Present.

## Approval Template (paste into docs/DECISION_LOG.md when granted)

```
## DEC-XXXX - LAUNCH-A approved
Date: <YYYY-MM-DD>
Task/Gate: LAUNCH-A
Decision: Full n≥3-seed Stage-A sweep authorized (seam-JEPA vs block-JEPA vs MAE-at-seam).
Rationale: Eval frozen, ε pre-registered (dated earlier), pilot smoke-passed, ledger committed.
Evidence / Source Docs: docs/GATE_LAUNCH_A_REVIEW.md, docs/decisions/compute-ledger.md.
Human Approval: <name> on <date>.
```
