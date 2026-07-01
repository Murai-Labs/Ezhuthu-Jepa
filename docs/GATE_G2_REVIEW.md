# Gate G2 Review — Degradation-Realism (K4)

## Purpose

G2 blocks the paper/demo release phase until the Phase-1 win is re-tested under manuscript-like
degradation. It decides whether the manuscript-recovery framing is earned or the paper narrows to
the clean-script-only version. Only reached if G1 PASSES.

## Gate Status

Status: Not yet approved. Approval is recorded in `docs/DECISION_LOG.md`; this file preserves the
review evidence.

## Required Evidence

| Requirement | Evidence (path) | Status |
|-------------|-----------------|--------|
| Corruption suite (drop-puḷḷi, bleed, discoloration, touching) | `src/ezhuthu_jepa/data/degrade.py` (P2.001) | Missing |
| Corruption realism validated vs small real sample | `docs/decisions/degradation-realism.md` (P2.002) | Missing |
| Real sample confirmed absent from training manifests | grep check in P2.002 | Missing |
| K4 run: seam-JEPA vs block-JEPA on M under degradation | run-ids `phase2-k4-*` | Missing |
| Comparison table with CIs, esp. missing-puḷḷi condition | `docs/GATE_G2_REVIEW.md` (this file, filled) | Missing |

## Decision Rule

- **PASS** — the K1 advantage survives degradation (especially the missing-puḷḷi condition) beyond
  ε with non-overlapping CIs → the manuscript-recovery claim is earned; this is the headline result.
- **NARROW** — the advantage vanishes under degradation → the paper is honestly the clean-script
  version only; the manuscript claim moves to v2 (spec §7, locked). Recorded in `notes/negative-results/`.

## Explicit Non-Results

No claim about real-manuscript transcription accuracy is made from v1; the real sample is a
realism/sanity check, never a training or benchmark-label source.

## Approval Template (paste into docs/DECISION_LOG.md when granted)

```
## DEC-XXXX - G2 decision
Date: <YYYY-MM-DD>
Task/Gate: G2
Decision: <PASS → manuscript claim earned | NARROW → clean-script-only paper>.
Rationale: <K4 comparison vs ε under degradation, with CIs>.
Evidence / Source Docs: docs/GATE_G2_REVIEW.md, docs/decisions/degradation-realism.md, run-ids.
Human Approval: <name> on <date>.
```
