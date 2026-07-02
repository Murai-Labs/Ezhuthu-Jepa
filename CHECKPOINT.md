# Ezhuthu-Jepa — Checkpoint

Last updated: 2026-07-01 19:15 CT

## Resume Point

To verify a clean state and continue:

```bash
cd /c/Github/Ezhuthu-Jepa
git status -sb
PYTHONIOENCODING=utf-8 python -m pytest -q          # expect: 56 passed
# Fetch the OFL font (gitignored) if missing, then regenerate the multi-font dataset (deterministic):
curl -fsSL "https://github.com/google/fonts/raw/main/ofl/notosanstamil/NotoSansTamil%5Bwdth,wght%5D.ttf" -o fonts/NotoSansTamil.ttf
PYTHONIOENCODING=utf-8 PYTHONPATH=src python -m ezhuthu_jepa.data.build_uyirmei
nvidia-smi                 # confirm RTX 5090 available before any GPU work
```

Next controlled task: see `tasks/atomic-task-list.md` → **TASK PA.002** (frequency split from Project
Madurai), then **PA.003** (eval harness), **P1.001** (pre-register ε), **PA.004** (seam masking).

## Current Checkpoint

- Phase: **G0 APPROVED (DEC-0008); PA.001 + PA.002 + PA.003 done; ε PRE-REGISTERED (DEC-0009).** LAUNCH-A / G1 sweep not started.
- What is done: operating system + provenance writer + config contract (P0.003/P0.004), and the Tamil
  rendering pipeline (PA.001): `data/{grapheme,render,build_uyirmei}.py`, HarfBuzz+FreeType shaping,
  glyph/diff seam hybrid, **multi-font (Noto+Nirmala)**. All 216 uyirmei rendered under both fonts →
  `runs/pa001-render-001/` (432 entries + unified `provenance.json`). Full suite 56 passed.
- PA.002 done: bottom quartile (54) frozen in `runs/pa002-split-001/split-manifest.json` from a
  172-work Project Madurai snapshot (4.85M uyirmei, 207/216 seen). Corpus gitignored, hash-pinned.
- PA.003 done: eval harness `eval/akshara_probe.py` — encoder-agnostic ridge probe, metric M with
  bootstrap CIs, stratified by bucket × seam_source × font, frozen before the sweep. Baseline
  PixelEncoder metric_M = 0.333 (reference). `runs/pa003-probe-001/metrics.json`; Figure F3.
- What is next: **PA.004** seam-masking module, then **PA.005** I-JEPA pretraining loop (registers the
  JEPA encoder that plugs into the PA.003 harness). PA.005 introduces **torch** — use `dtype=`, never
  `torch_dtype=`; pin it in locked-versions. **Do not launch the full sweep before LAUNCH-A.**
- To rebuild PA.002/PA.003: see `docs/RUNBOOK.md` (frequency split; evaluate a frozen encoder).
- Authorization gate status: **G0 approved** (DEC-0008); **ε pre-registered** (DEC-0009). LAUNCH-A
  **not yet approved** — do not launch the full Stage-A sweep (P1.003) until it is. No training run authorized.

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
