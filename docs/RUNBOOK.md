# Ezhuthu-Jepa — Runbook

Operational procedures. Exact, copy-pasteable commands only. Paths assume repo root
`/c/Github/Ezhuthu-Jepa`. Fill the environment-setup commands once the toolchain is chosen
(TASK P0.004 locks versions).

## Environment Setup

```bash
# Rendering toolchain (PA.001): pinned in configs/phase0/locked-versions.yaml.
pip install numpy pillow uharfbuzz "freetype-py" pyyaml pytest

# Fetch the reproducible OFL font (gitignored). Nirmala UI is a Windows-only bonus and needs no fetch.
mkdir -p fonts
curl -fsSL "https://github.com/google/fonts/raw/main/ofl/notosanstamil/NotoSansTamil%5Bwdth,wght%5D.ttf" \
  -o fonts/NotoSansTamil.ttf
```

## Build the Rendered Akshara Dataset (PA.001)

```bash
# Renders all 216 uyirmei under every available font → data/rendered/ (gitignored) + committed
# manifest + provenance under runs/. Deterministic (no RNG).
PYTHONPATH=src python -m ezhuthu_jepa.data.build_uyirmei \
  --config configs/phase1/render.yaml --out data/rendered/uyirmei --run-dir runs/pa001-render-001
```

## Build the Frequency-Stratified Split (PA.002)

```bash
# 1) Fetch the Project Madurai corpus snapshot into data/raw/project-madurai/ (gitignored).
PYTHONPATH=src python -m ezhuthu_jepa.data.fetch_project_madurai --start 1 --end 200
# 2) Count uyirmei frequencies, freeze the bottom quartile, write the split + provenance to runs/.
PYTHONPATH=src python -m ezhuthu_jepa.data.frequency_split \
  --config configs/phase1/split.yaml --run-dir runs/pa002-split-001
# 3) Figure F2 (frequency distribution + cutoff).
PYTHONPATH=src python -m ezhuthu_jepa.figures.f2_frequency_distribution
```

## Run a Smoke Test

```bash
python -m compileall src && pytest -q          # code smoke
# Pipeline smoke (after PA.005 exists):
python -m ezhuthu_jepa.train.pretrain --config configs/phase1/pretrain.yaml --smoke --seed 0
```

## Launch a Full Run

```bash
# ONLY after LAUNCH-A approval (docs/GATE_LAUNCH_A_REVIEW.md signed).
# Provenance is recorded by the writer (P0.003) before the loop starts.
python -m ezhuthu_jepa.train.pretrain --config configs/phase1/sweep.yaml \
  --objective seam_jepa --seed 0 --run-id phase1-sweep-seamjepa-seed0
```

## Resume an Interrupted Run

```bash
# Runs >30min write a resume-state file each epoch; restart validates config hash + seed.
python -m ezhuthu_jepa.train.pretrain --resume runs/<run-id>/resume-state.json
```

## Pre-Run Checklist

- [ ] `grep -r "EZHUTHU-PLACEHOLDER" src tests` is empty for reachable code.
- [ ] Config hash, code SHA, data hash, seed, environment recorded (P0.003 writer).
- [ ] Run ID allocated (not reused; see `docs/EXPERIMENT_LOG.md`).
- [ ] Progress logging emits every ≤100 steps (step/total, elapsed, ETA).
- [ ] For any full sweep: LAUNCH-A approved and ε pre-registered (P1.001) with an earlier timestamp.
- [ ] Real-manuscript sample is NOT in the training manifest.
