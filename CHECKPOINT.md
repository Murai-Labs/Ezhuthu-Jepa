# Ezhuthu-Jepa — Checkpoint

Last updated: 2026-07-02 CT

## Resume Point

To verify a clean state and continue:

```bash
cd /c/Github/Ezhuthu-Jepa
git status -sb
PYTHONIOENCODING=utf-8 python -m pytest -q          # expect: 124 passed
nvidia-smi                 # confirm RTX 5090 available before any GPU work
# Regenerate gitignored data if missing (deterministic): the OFL font, then the augmented index.
curl -fsSL "https://github.com/google/fonts/raw/main/ofl/notosanstamil/NotoSansTamil%5Bwdth,wght%5D.ttf" -o fonts/NotoSansTamil.ttf
PYTHONIOENCODING=utf-8 PYTHONPATH=src python -m ezhuthu_jepa.data.build_augmented \
  --config configs/phase1/augment.yaml --run-dir runs/pa4b-augment-001   # only if data/rendered/augmented absent
```

Next controlled task: see `tasks/atomic-task-list.md` → **LAUNCH-A** (assemble the gate packet — all
preconditions met incl. K2; run a longer 1-seed pilot + get Ramchand's sign-off, surfacing the K2 caveat),
then **P1.003** (full n≥3-seed sweep, clean tree). Do NOT launch the sweep before LAUNCH-A.

## Current Checkpoint

- Phase: **G0 APPROVED; PA.001–PA.006 + P1.001b + P1.002 + resume + sweep infra + pilot done.
  LAUNCH-A BLOCKED (DEC-0017): pilot → latent JEPA < pixel baseline; recipe iteration (PA.005b) needed.**
- What is done: operating system + provenance writer + config contract (P0.003/P0.004), and the Tamil
  rendering pipeline (PA.001): `data/{grapheme,render,build_uyirmei}.py`, HarfBuzz+FreeType shaping,
  glyph/diff seam hybrid, **multi-font (Noto+Nirmala)**. All 216 uyirmei rendered under both fonts →
  `runs/pa001-render-001/` (432 entries + unified `provenance.json`). Full suite 56 passed.
- PA.002 done: bottom quartile (54) frozen in `runs/pa002-split-001/split-manifest.json` from a
  172-work Project Madurai snapshot (4.85M uyirmei, 207/216 seen). Corpus gitignored, hash-pinned.
- PA.003 done: eval harness `eval/akshara_probe.py` — encoder-agnostic ridge probe, metric M with
  bootstrap CIs, stratified by bucket × seam_source × font, frozen before the sweep. Baseline
  PixelEncoder metric_M = 0.333 (reference). `runs/pa003-probe-001/metrics.json`; Figure F3.
- Decisions made (DEC-0013): ViT-Tiny/8; full augmentation + held-out font; ε amended to McNemar
  primary + CI secondary (re-pre-registered before any result in g1-cheap-baseline.md).
- Done: PA.4b.1 `data/augment.py` (transforms seam_bbox); PA.4b.2 augmented dataset — 54k instances,
  `runs/pa4b-augment-001/split-manifest.json` (committed) + gitignored `data/rendered/augmented/`.
  Regenerate via RUNBOOK "Build the Augmented Font-Holdout Dataset".
- Done: **P1.001b** — `akshara_probe.py` McNemar comparator (`mcnemar`/`compare_arms`) + `index`
  backend + `predictions.jsonl`; `runs/pa003b-probe-aug-001` confirms metric_M CI half-width 1.02 pp.
- Done: **PA.005** — `train/pretrain.py` I-JEPA ViT-Tiny/8, {seam/block/mae} by config; smoke runs
  `phaseA-smoke-001/-002/-003` (provenance + metrics + `encoder.pt`); JEPA encoder wired into the
  probe (`encoder: jepa`); torch 2.10.0+cu130 pinned. Regenerate via RUNBOOK "Pretraining Loop".
- Done: **Resume-state (§4)** — `checkpoint_every>0` writes atomic `resume-state.pt` (weights/optim/EMA/
  RNG); `--resume` validates config-hash+seed and continues from the saved step. Verified interrupt→resume
  reproduces identical final weights (CPU + GPU). Provenance now written before the loop.
- Done: **PA.006** compute ledger — `docs/decisions/compute-ledger.md` (DEC-0015): ~15 GPU-h program on
  one 5090, **hard ceiling 40 GPU-h**; unit costs measured from the smokes.
- Done: **P1.002 (K2)** — `eval/base_to_sign_probe.py`, run `phase1-k2probe-001`. **Kill-gate PASSES**
  (base 0.509 ≫ chance 0.091). **Caveat (DEC-0016, negative-results):** signal is sign-LOCATION not
  base-ink (location control beats base in every stratum) → live K1 risk (block may match seam).
- Done: **sweep orchestrator** (`train/sweep.py` + `sweep.yaml`/`pilot.yaml`, 6 tests) with a code-level
  LAUNCH-A gate (refuses ≥3-seed run without `--launch-a-approved`); target-encoder fix in `encoder.pt`.
- BLOCKER: **LAUNCH-A pilot (DEC-0017)** — `phase1-pilot-*` 1-seed 8k: metric_M seam 0.239, block 0.326
  (both < pixel 0.359), mae 0.532. Latent JEPA underperforms raw pixels; target-encoder fix did not
  rescue → recipe deficiency. See `notes/negative-results/pilot-latent-jepa-underperforms-pixel-baseline.md`.
- What is next: **AWAIT Ramchand's DEC-0017 choice (A recipe iteration / B reframe to MAE / C conclude).**
  Recommended A = PA.005b: LR cosine decay + I-JEPA recipe fidelity, re-pilot until latent ≥ pixels. Do
  NOT launch the sweep (sweep.py refuses it) and make no further recipe/compute changes without direction.
- Authorization gate status: **G0 approved** (DEC-0008); **ε pre-registered** (DEC-0009). LAUNCH-A
  **not yet approved** — do not launch the full Stage-A sweep (P1.003) until it is. No full training run authorized (smokes only).

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
