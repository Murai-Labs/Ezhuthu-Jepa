# Ezhuthu-Jepa — Checkpoint

Last updated: 2026-07-01 12:00 CT

## Resume Point

To verify a clean state and continue:

```bash
cd /c/Github/Ezhuthu-Jepa
git status -sb
python -m compileall src && pytest -q
nvidia-smi                 # confirm RTX 5090 available before any GPU work
```

Next controlled task: see `tasks/atomic-task-list.md` → **TASK P0.003** (run-provenance writer),
then **TASK P0.004** (config contract), then **TASK P1.001** (pre-register ε).

## Current Checkpoint

- Phase: **G0 complete** (skeleton scaffolded). LAUNCH-A / G1 not started.
- What is done: repository operating system installed — governance contract (CLAUDE.md ≡ AGENTS.md),
  trackers, docs, append-only notes, atomic task list, spec-comprehension check, minimal package,
  and the spec at `docs/spec/EZHUTHU_JEPA_Spec_v0.2.md`.
- What is next: implement provenance writer (P0.003) and config contract (P0.004); then freeze the
  eval harness and pre-register ε (P1.001) before running any cheap baseline.
- Authorization gate status: G0 evidence drafted in `docs/GATE_G0_REVIEW.md`, **pending human
  approval**. LAUNCH-A not requested. No run authorized.

## Do Not Do

- **Do not launch the full n ≥ 3-seed Stage-A sweep before LAUNCH-A is approved** (it is the single
  most expensive run).
- Do not run any baseline before ε and the bottom-quartile cutoff are pre-registered (P1.001) —
  the G1 gate becomes un-adjudicable if ε is set after seeing results.
- Do not report aggregate accuracy as the headline metric; M is bottom-quartile-frequency accuracy.
- Do not train on the real-manuscript sample; it is corruption-realism validation / held-out sanity only.
- Do not use `torch_dtype=`; use `dtype=`.

---
**Tracker rule:** Update this file and `STATUS.md` before every state-changing commit.
