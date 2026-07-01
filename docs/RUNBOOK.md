# Ezhuthu-Jepa — Runbook

Operational procedures. Exact, copy-pasteable commands only. Paths assume repo root
`/c/Github/Ezhuthu-Jepa`. Fill the environment-setup commands once the toolchain is chosen
(TASK P0.004 locks versions).

## Environment Setup

```bash
# Placeholder until P0.004 locks the toolchain. Expected shape:
python -m venv .venv
source .venv/Scripts/activate        # Windows Git Bash; use .venv/bin/activate on Linux/macOS
pip install -e .                     # editable install of src/ezhuthu_jepa
pip install -r requirements.txt      # created at P0.004 from configs/phase0/locked-versions.yaml
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
