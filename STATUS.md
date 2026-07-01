# Ezhuthu-Jepa — Status

Last updated: 2026-07-01 17:15 CT

## Methodology Decisions (DEC-0004, DEC-0006)

- Metric **M = bottom-quartile-frequency akshara top-1 accuracy** — confirmed; **reported stratified
  by seam_source (glyph vs diff) and by font** (DEC-0006).
- Cheap-baseline set = **block-JEPA, MAE-at-seam, base→sign probe** (the three) — confirmed.
- Frequency corpus = **Project Madurai** — confirmed (resolves RISKS Q005).
- Rendering is **multi-font (Noto + Nirmala)**; provenance **unified** for seedless data-gen runs.
- **ε still UNSET** — provisional 2.0 pp / non-overlapping CIs stands; pin at P1.001 before any baseline.

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

- None blocking. Forward blocker: G1 needs PA.002 (frequency split) + PA.003 (eval harness) frozen
  and ε pre-registered (P1.001) before any baseline run.
- Open uncertainty (feeds PA.004): ligature vowels (i/ii/u/uu, 60/216) have no cleanly separable
  sign region — likely report K1 stratified by seam_source.
- Claim boundary: nothing has been trained or measured. Repo supports "operating system +
  provenance/config contract + exact rendered akshara dataset with seam labels are in place."

## Next Recommended Work

1. **TASK PA.002** — frequency-stratified split from Project Madurai (DEC-0004) + bottom-quartile cutoff.
2. **TASK PA.003** — akshara-recognition eval harness (metric M with bootstrap CIs).
3. **TASK P1.001** — pre-register ε and the bottom-quartile cutoff **before** any baseline run.
4. **TASK PA.004** — seam-masking module; decide ligature-seam handling (stratify by seam_source).

---
**Tracker rule:** Update this file and `CHECKPOINT.md` before every commit that changes project
state, scripts, data manifests, gates, or run status.
