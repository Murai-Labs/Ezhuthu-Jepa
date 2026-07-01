# Ezhuthu-Jepa — Status

Last updated: 2026-07-01 13:30 CT

## Current State

- Repo state: pushed to Murai-Labs/Ezhuthu-Jepa (public). Phase-0 code landing.
- Current phase: **G0 complete + Phase-0 code in progress**. P0.001–P0.004 done; G1 not started.
- Stack decision: single RTX 5090; small I-JEPA-style ViT; PyTorch with `dtype=` policy (never
  `torch_dtype=`). Config contract locked at schema `0.1.0`; training toolchain deferred/pinned
  per `configs/phase0/locked-versions.yaml`.
- Latest run: no runs yet. Provenance writer is in place and required before the first run.

## Completed Work

- [x] Repository skeleton exists (governance, trackers, docs, notes, configs, src, tests).
- [x] Append-only audit files exist under `notes/`.
- [x] Atomic task list written (`tasks/atomic-task-list.md`).
- [x] Spec-comprehension check written (`notes/spec-comprehension-check.md`, completes TASK P0.001).
- [x] Minimal importable package + import test (`src/ezhuthu_jepa/`, `tests/test_import.py`).
- [x] Source-of-truth spec placed at `docs/spec/EZHUTHU_JEPA_Spec_v0.2.md`.
- [x] **Run-provenance writer implemented (TASK P0.003)** — `src/ezhuthu_jepa/provenance.py`,
  9 tests. Manifest carries exactly the 5 identifiers; `validate_run_dir` rejects any missing.
- [x] **Phase-0 config contract locked (TASK P0.004)** — `src/ezhuthu_jepa/config.py` (schema
  `0.1.0`), `configs/phase0/locked-versions.yaml`, schema-consumer audit, 18 tests.
- [ ] G0 review evidence signed off (`docs/GATE_G0_REVIEW.md` — drafted, awaiting human approval).

Test suite: **28 passed** (`pytest -q`). Placeholder scan clean.

## Current Blockers

- None blocking G0. Forward blocker: G1 cannot begin until the rendering + frequency-stratified
  evaluation harness is frozen and ε is pre-registered (TASKS PA.001–PA.003, P1.001).
- Claim boundary: nothing has been trained or measured. No scientific claim is supported yet; the
  repo now supports "the operating system + provenance/config contract are in place."

## Next Recommended Work

1. **TASK PA.001** — Tamil rendering pipeline with exact grapheme decomposition (seam labels).
2. **TASK PA.002** — frequency-stratified split + bottom-quartile cutoff (defines metric M's tail).
3. **TASK PA.003** — akshara-recognition eval harness (metric M with bootstrap CIs).
4. **TASK P1.001** — pre-register ε and the bottom-quartile cutoff **before** any baseline run.

---
**Tracker rule:** Update this file and `CHECKPOINT.md` before every commit that changes project
state, scripts, data manifests, gates, or run status.
