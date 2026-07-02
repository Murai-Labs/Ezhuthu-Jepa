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

## Evaluate on the Augmented Font-Holdout Index — tight CI (P1.001b)

```bash
# Same frozen metric machinery as PA.003, but the `index` backend reads the 54k-instance
# index.jsonl (train=noto / eval=held-out nirmala). Bottom-quartile eval n≈8,100 → metric M CI
# half-width ~1 pp. Writes metrics.json + predictions.jsonl (per-instance correctness, for McNemar).
PYTHONPATH=src python -m ezhuthu_jepa.eval.akshara_probe \
  --config configs/phase1/probe-augmented.yaml --run-dir runs/pa003b-probe-aug-001
# To evaluate a trained JEPA encoder instead of the PixelEncoder reference, set in the probe config:
#   encoder: jepa
#   checkpoint: runs/<pretrain-run>/encoder.pt
```

## Pretraining Loop — seam / block / MAE (PA.005)

```bash
# Objective is set by config, or overridden with --objective. Architecture / compute / mask-ratio are
# identical across the three arms — only the switched variable changes. dtype= autocast (bf16).
# SMOKE (configs/phase1/pretrain.yaml: limit_instances=1024, max_steps=30) — proves the loop runs:
PYTHONPATH=src python -m ezhuthu_jepa.train.pretrain \
  --config configs/phase1/pretrain.yaml --run-dir runs/phaseA-smoke-001                     # seam_jepa
PYTHONPATH=src python -m ezhuthu_jepa.train.pretrain \
  --config configs/phase1/pretrain.yaml --run-dir runs/phaseA-smoke-002 --objective block_jepa
PYTHONPATH=src python -m ezhuthu_jepa.train.pretrain \
  --config configs/phase1/pretrain.yaml --run-dir runs/phaseA-smoke-003 --objective mae_seam
```

## Run a Smoke Test

```bash
python -m compileall src && pytest -q                     # code smoke (107 pass)
pytest -k "pretrain or mcnemar or probe"                  # Phase-1 focused
# Pipeline smoke: the PA.005 seam/block/MAE runs above (each ~2 s on the RTX 5090).
```

## Launch a Full Run

```bash
# ONLY after LAUNCH-A approval (docs/GATE_LAUNCH_A_REVIEW.md signed) and on a CLEAN committed tree.
# Provenance (incl. code_sha + dirty flag) is recorded BEFORE the loop starts. The full sweep uses a
# dedicated sweep config (P1.003) that sets limit_instances=0, the real step budget, per-seed dirs, and
# checkpoint_every > 0 so an interrupted >30min run is resumable. Seed is a config field (one per seed).
PYTHONPATH=src python -m ezhuthu_jepa.train.pretrain \
  --config configs/phase1/sweep-seamjepa-seed0.yaml --run-dir runs/phase1-sweep-seamjepa-seed0
```

## Resume an Interrupted Run

```bash
# Runs with checkpoint_every > 0 write runs/<run-id>/resume-state.pt every N steps (weights, optimizer,
# EMA target, and NumPy+torch RNG states — atomic rename, never half-written). Restart with the SAME
# config + --resume; it validates the config hash + seed against the interrupted run and continues from
# the saved step. A changed config (or seed) is refused (ResumeError). resume-state.pt is a *.pt →
# gitignored. Provenance is not rewritten on resume (the original launch's manifest is validated).
PYTHONPATH=src python -m ezhuthu_jepa.train.pretrain \
  --config configs/phase1/sweep-seamjepa-seed0.yaml --run-dir runs/phase1-sweep-seamjepa-seed0 --resume
```

## Pre-Run Checklist

- [ ] `grep -r "EZHUTHU-PLACEHOLDER" src tests` is empty for reachable code.
- [ ] Config hash, code SHA, data hash, seed, environment recorded (P0.003 writer).
- [ ] Run ID allocated (not reused; see `docs/EXPERIMENT_LOG.md`).
- [ ] Progress logging emits every ≤100 steps (step/total, elapsed, ETA).
- [ ] For any full sweep: LAUNCH-A approved and ε pre-registered (P1.001) with an earlier timestamp.
- [ ] Real-manuscript sample is NOT in the training manifest.
