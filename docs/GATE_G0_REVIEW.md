# Gate G0 Review — Repo Skeleton Ready

## Purpose

G0 blocks all research work until the operating system exists: governance contract, trackers,
docs, append-only audit trail, atomic task list, and a minimal importable package. Without it,
no run is traceable and no gate is adjudicable.

## Gate Status

Status: **Approved 2026-07-01 by Ramchand.** Approval is recorded in `docs/DECISION_LOG.md`
(DEC-0008); this file preserves the review evidence. Phase-0 code (P0.003/P0.004) and PA.001 are
already complete; G1-phase work continues (PA.002 → PA.003 → sweep).

## Required Evidence

| Requirement | Evidence (path) | Status |
|-------------|-----------------|--------|
| Governance contract, CLAUDE.md ≡ AGENTS.md | `CLAUDE.md`, `AGENTS.md` (diff clean) | Present |
| Codex pointer (not a third rules file) | `CODEX.md` | Present |
| Trackers | `STATUS.md`, `CHECKPOINT.md`, `TASKS.md` | Present |
| Atomic task list | `tasks/atomic-task-list.md` | Present |
| Docs suite | `docs/DECISION_LOG.md`, `EXPERIMENT_LOG.md`, `REPRODUCIBILITY.md`, `RISKS_AND_OPEN_QUESTIONS.md`, `RUNBOOK.md` | Present |
| Gate reviews (one per gate) | `docs/GATE_{G0,LAUNCH_A,G1,G2,G3}_REVIEW.md` | Present |
| Append-only audit trail | `notes/*.md` + `notes/*/` subdirs | Present |
| Spec-comprehension check | `notes/spec-comprehension-check.md` | Present |
| Source-of-truth spec in repo | `docs/spec/EZHUTHU_JEPA_Spec_v0.2.md` | Present |
| Minimal importable package + test | `src/ezhuthu_jepa/__init__.py`, `tests/test_import.py` | Present |
| Text-free `.gitignore` | `.gitignore` | Present |

## Explicit Non-Results

No data has been rendered, no model trained, no metric measured. G0 asserts only that the
operating system is in place — it makes **no scientific claim** whatsoever.

## Required Next Work Before Approval

- ~~Human (Ramchand) confirms the derived gate chain, metric M, and ε values match intent.~~ Done
  (DEC-0004 metric/baselines/corpus; DEC-0009 ε pre-registered).
- ~~Confirm `pytest -q` passes on the target machine.~~ Done (58 passed).

## Approval Template (paste into docs/DECISION_LOG.md when granted)

```
## DEC-XXXX - G0 approved
Date: <YYYY-MM-DD>
Task/Gate: G0
Decision: G0 (Repo Skeleton Ready) approved; Phase 0 code tasks (P0.003, P0.004) unblocked.
Rationale: Skeleton, docs, trackers, task list, and minimal package all present and verified.
Evidence / Source Docs: docs/GATE_G0_REVIEW.md, tasks/atomic-task-list.md.
Human Approval: <name> on <date>.
```
