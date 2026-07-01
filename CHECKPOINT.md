# Ezhuthu-Jepa — Checkpoint

Last updated: 2026-07-01 13:30 CT

## Resume Point

To verify a clean state and continue:

```bash
cd /c/Github/Ezhuthu-Jepa
git status -sb
python -m compileall src && pytest -q     # expect: 28 passed
nvidia-smi                 # confirm RTX 5090 available before any GPU work
```

Next controlled task: see `tasks/atomic-task-list.md` → **TASK PA.001** (Tamil rendering pipeline),
then **PA.002** (frequency split), **PA.003** (eval harness), and **P1.001** (pre-register ε).

## Current Checkpoint

- Phase: **G0 complete; Phase-0 code done** (P0.001–P0.004). LAUNCH-A / G1 not started.
- What is done: operating system + the run-provenance writer (`provenance.py`, 5-identifier manifest
  + validator, 9 tests) and the locked config contract (`config.py` schema `0.1.0`, schema-consumer
  audit, `locked-versions.yaml`, 18 tests). Full suite 28 passed.
- What is next: build the rendering + evaluation harness (PA.001–PA.003) that defines metric M, then
  pre-register ε (P1.001) before running any cheap baseline. New training/data code must call
  `write_provenance(...)` before any run and load configs through `RunConfig.from_dict(...)`.
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
