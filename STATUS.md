# Ezhuthu-Jepa — Status

Last updated: 2026-07-02 CT

## Methodology Decisions (DEC-0004, DEC-0006)

- Metric **M = bottom-quartile-frequency akshara top-1 accuracy** — confirmed; **reported stratified
  by seam_source (glyph vs diff) and by font** (DEC-0006).
- Cheap-baseline set = **block-JEPA, MAE-at-seam, base→sign probe** (the three) — confirmed.
- Frequency corpus = **Project Madurai** — confirmed (resolves RISKS Q005).
- Rendering is **multi-font (Noto + Nirmala)**; provenance **unified** for seedless data-gen runs.
- **ε PRE-REGISTERED** (DEC-0009): 2.0 pp on M + non-overlapping 95 % CIs (n ≥ 3), before any baseline.
- **G0 gate APPROVED** (DEC-0008, `GATE_G0_REVIEW.md`).

## Current State

- Repo state: pushed to Murai-Labs/Ezhuthu-Jepa (public). Phase-1 code landing.
- Current phase: **G0 complete; PA.001–PA.005 + P1.001b done; LAUNCH-A / G1 sweep not started.**
- Stack decision: single RTX 5090; from-scratch I-JEPA-style ViT-Tiny/8 (torch.nn, no timm); PyTorch
  with `dtype=` policy (never `torch_dtype=`). Config contract locked at schema `0.1.0`; torch
  2.10.0+cu130 now pinned in `configs/phase0/locked-versions.yaml`.
- Latest runs: `pa003b-probe-aug-001` (CI confirmation) + `phaseA-smoke-001/-002/-003` (pretraining
  smoke, all three objectives). All provenanced. Smoke ran on a dirty tree (acceptable for a smoke;
  the full sweep must run clean).

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
- [x] **Figures convention + Figure F1** (DEC-0007) — `docs/figures/`, generator `figures/`, `FIGURES.md`.
- [x] **G0 gate APPROVED** (DEC-0008) + **ε pre-registered** (DEC-0009, P1.001 done).
- [x] **Frequency-stratified split (TASK PA.002, DEC-0010)** — 172 Project Madurai works, 4.85M uyirmei
  counted, 207/216 seen; bottom quartile (54) frozen in `runs/pa002-split-001/split-manifest.json`;
  deterministic leak-free train/eval split; Figure F2 captured.
- [x] **Eval harness / metric M (TASK PA.003, DEC-0011)** — encoder-agnostic ridge linear probe with
  bootstrap CIs, stratified by bucket × seam_source × font. Frozen before the sweep. Baseline
  PixelEncoder metric_M = 0.333 [0.222,0.463] (reference); `runs/pa003-probe-001/metrics.json`; Figure F3.
- [x] **Seam masking + block control (TASK PA.004, DEC-0012)** — `masking/seam.py`, 10 tests. Seam mask
  covers the sign; matched block mask (same size, random location) is the clean K1 control.

- [x] **PA.005 decisions (DEC-0013)** — ViT-Tiny/8 (auto-escalate); full augmentation + held-out-font
  eval; **decision rule amended to paired McNemar primary + CI secondary** (ε=2pp retained as min effect;
  re-pre-registered before any result).
- [x] **Augmentation core (PA.4b.1)** — `data/augment.py` transforms seam_bbox in lockstep with the warp.
- [x] **Augmented font-holdout dataset (PA.4b.2)** — 54k instances (21.6k train noto / 32.4k eval nirmala,
  held out), frozen seeded eval; `runs/pa4b-augment-001/split-manifest.json`. Bottom-quartile eval n≈8,100
  → CI half-width ~1pp (was ~12pp), making the 2pp effect adjudicable.
- [x] **McNemar comparator + augmented-index probe (TASK P1.001b, DEC-0013/0014)** — `akshara_probe.py`
  gains `mcnemar`/`compare_arms` (exact binomial <25 discordants else χ²+continuity, Bonferroni; primary)
  + non-overlapping-CI verdict (secondary), and an `index` backend reading the 54k augmented index. Writes
  `predictions.jsonl` for pairing. Re-run `runs/pa003b-probe-aug-001`: PixelEncoder metric_M = 0.359
  [0.349,0.369], **CI half-width 1.02pp** — empirically confirms the ~1pp target.
- [x] **I-JEPA ViT-Tiny/8 pretraining loop (TASK PA.005, DEC-0014)** — `train/pretrain.py` +
  `configs/phase1/pretrain.yaml`. From-scratch ViT (torch.nn), context/EMA-target/predictor; objective
  {seam_jepa, block_jepa, mae_seam} by config only; fixed n_mask=36/144 identical across arms (AC2);
  ≤10-step progress logging; provenance-before-loop + metrics + `encoder.pt`; JEPA encoder registered in
  the probe (`encoder: jepa`). Smoke runs `phaseA-smoke-001/-002/-003` (5.35M enc, 2.5–3.5k img/s,
  1.7–1.9GB on the 5090). torch 2.10.0+cu130 pinned. **Smoke only — NOT a K1/K3 result.**
- [x] **Resume-state (AGENTS.md §4)** — `checkpoint_every>0` writes `resume-state.pt` (weights, optim,
  EMA target, NumPy+torch RNG) atomically each N steps; `--resume` validates config-hash+seed and
  continues from the saved step (refuses a changed config). Verified: an interrupted run resumed to the
  **identical** final weights/loss (CPU test + GPU end-to-end). Enables the >30min sweep to survive interruption.

Test suite: **110 passed** (`pytest -q`; +18 for P1.001b/PA.005/resume). Placeholder + `torch_dtype` scans
clean. `compileall src` clean. Figures: F1, F2, F3 done; F4–F5 planned.

## Current Blockers

- None blocking. G0 approved; ε pre-registered; eval harness + comparator frozen; pretraining loop
  smoke-passes. Forward: the full sweep (P1.003) needs LAUNCH-A approval, which needs PA.006 (compute
  ledger). No full training run authorized yet.
- Open uncertainty (feeds PA.004): ligature vowels (i/ii/u/uu, 60/216) have no cleanly separable
  sign region — likely report K1 stratified by seam_source.
- Claim boundary: nothing has been trained or measured. Repo supports "operating system +
  provenance/config contract + exact rendered akshara dataset with seam labels are in place."

## Next Recommended Work

1. **TASK PA.006** — pre-commit the GPU-hour ledger (smoke/pilot/full-sweep/degradation) with a hard
   ceiling → `docs/decisions/compute-ledger.md`. Uses the smoke throughput (2.5–3.5k img/s) to estimate.
2. **LAUNCH-A** — assemble the gate review (harness frozen ✓, ε pre-registered ✓, smoke passes ✓,
   resume-state ✓, ledger from PA.006) → human approval to launch the full n≥3-seed sweep.
3. **TASK P1.002** (K2 base→sign premise probe) → **P1.003** (full sweep, clean tree, checkpoint_every>0)
   → **P1.004** (G1 decision vs ε via the McNemar comparator). Do NOT launch P1.003 before LAUNCH-A.

---
**Tracker rule:** Update this file and `CHECKPOINT.md` before every commit that changes project
state, scripts, data manifests, gates, or run status.
