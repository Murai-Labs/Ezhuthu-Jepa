# Ezhuthu-Jepa — Checkpoint

Last updated: 2026-07-01 16:30 CT

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

- Phase: **G0 code done; PA.001 done.** LAUNCH-A / G1 not started.
- What is done: operating system + provenance writer + config contract (P0.003/P0.004), and the Tamil
  rendering pipeline (PA.001): `data/{grapheme,render,build_uyirmei}.py`, HarfBuzz+FreeType shaping,
  glyph/diff seam hybrid, **multi-font (Noto+Nirmala)**. All 216 uyirmei rendered under both fonts →
  `runs/pa001-render-001/` (432 entries + unified `provenance.json`). Full suite 56 passed.
- What is next: PA.002 computes compound frequencies from Project Madurai and freezes the
  bottom-quartile split (defines metric M's tail); then PA.003 eval harness (report accuracy per
  frequency-bucket × seam_source × font, DEC-0006); then P1.001 pins ε. Data/train code loads configs
  via `RunConfig.from_dict(...)`; ALL runs (incl. deterministic data-gen) use `write_provenance(...)`
  with `seed=SEED_DETERMINISTIC` where there is no RNG (DEC-0006).
- Authorization gate status: G0 evidence drafted in `docs/GATE_G0_REVIEW.md`, **pending human
  approval**. LAUNCH-A not requested. No training run authorized. ε still unset (defer to P1.001).

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
