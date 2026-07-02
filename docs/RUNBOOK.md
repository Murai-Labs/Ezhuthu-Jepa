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

## Evaluate a Frozen Encoder — Metric M (PA.003)

```bash
# Fits a linear probe on the PA.002 split's train instances, evaluates top-1 accuracy per
# frequency-bucket × seam_source × font with 95% bootstrap CIs → runs/<run>/metrics.json.
# Default encoder = PixelEncoder baseline; PA.005 swaps in the JEPA encoder via configs/phase1/probe.yaml.
PYTHONPATH=src python -m ezhuthu_jepa.eval.akshara_probe \
  --config configs/phase1/probe.yaml --run-dir runs/pa003-probe-001
PYTHONPATH=src python -m ezhuthu_jepa.figures.f3_probe_accuracy   # Figure F3
```

## Build the Augmented Font-Holdout Dataset (PA.4b.2)

```bash
# ~100 train (noto) + ~150 eval (nirmala, held out) augmented instances/class, seam_bbox transformed
# in lockstep. Images + per-instance index.jsonl → data/rendered/augmented/ (gitignored, regenerable);
# compact split-manifest + provenance → runs/. ~1 min, 54k images.
PYTHONPATH=src python -m ezhuthu_jepa.data.build_augmented \
  --config configs/phase1/augment.yaml --run-dir runs/pa4b-augment-001
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
