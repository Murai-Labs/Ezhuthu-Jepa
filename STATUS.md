# Ezhuthu-Jepa — Status

Last updated: 2026-07-01 17:45 CT

## Methodology Decisions (DEC-0004, DEC-0006)

- Metric **M = bottom-quartile-frequency akshara top-1 accuracy** — confirmed; **reported stratified
  by seam_source (glyph vs diff) and by font** (DEC-0006).
- Cheap-baseline set = **block-JEPA, MAE-at-seam, base→sign probe** (the three) — confirmed.
- Frequency corpus = **Project Madurai** — confirmed (resolves RISKS Q005).
- Rendering is **multi-font (Noto + Nirmala)**; provenance **unified** for seedless data-gen runs.
- **ε PRE-REGISTERED** (DEC-0009): 2.0 pp on M + non-overlapping 95 % CIs (n ≥ 3), before any baseline.
- **G0 gate APPROVED** (DEC-0008, `GATE_G0_REVIEW.md`).

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
- [x] **Tamil rendering pipeline (TASK PA.001)** — `data/{grapheme,render,build_uyirmei}.py`;
  HarfBuzz+FreeType shaping, glyph/diff seam hybrid, **multi-font (Noto+Nirmala)**. All 216 uyirmei
  rendered under both fonts → `runs/pa001-render-001/` (432 entries; noto 18/142/56, nirmala
  18/138/60 none/glyph/diff). Provenance unified for deterministic data-gen runs (DEC-0006).
- [x] **Figures convention + Figure F1** (DEC-0007) — `docs/figures/f1_seam_localization.{png,prov.json}`,
  generator `src/ezhuthu_jepa/figures/`, `docs/FIGURES.md` index. Figures regenerable + provenanced.
- [ ] G0 review evidence signed off (`docs/GATE_G0_REVIEW.md` — drafted, awaiting human approval).

Test suite: **58 passed** (`pytest -q`). Placeholder scan clean. Paper figures captured as milestones
land (F1 done; F2–F5 planned in `docs/FIGURES.md`).

## Current Blockers

- None blocking. G0 approved; ε pre-registered. Forward: G1 still needs PA.002 (frequency split) +
  PA.003 (eval harness) frozen; and the full sweep (P1.003) needs LAUNCH-A approval. No run authorized yet.
- Open uncertainty (feeds PA.004): ligature vowels (i/ii/u/uu, 60/216) have no cleanly separable
  sign region — likely report K1 stratified by seam_source.
- Claim boundary: nothing has been trained or measured. Repo supports "operating system +
  provenance/config contract + exact rendered akshara dataset with seam labels are in place."

## Next Recommended Work

1. **TASK PA.002** — frequency-stratified split from Project Madurai (DEC-0004); freeze bottom-quartile
   membership (does not reopen ε). Capture figure F2 (frequency distribution + cutoff).
2. **TASK PA.003** — akshara-recognition eval harness (metric M, per bucket × seam_source × font, CIs).
3. **TASK PA.004** — seam-masking module (mask carries seam_source; ligatures via diff region).
4. Then **P1.002** (K2 probe) → LAUNCH-A → **P1.003** (sweep) → **P1.004** (G1 decision vs ε).

---
**Tracker rule:** Update this file and `CHECKPOINT.md` before every commit that changes project
state, scripts, data manifests, gates, or run status.
