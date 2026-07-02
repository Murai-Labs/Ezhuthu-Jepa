# Ezhuthu-Jepa — Experiment Log

## Update Rules

Append an entry after EVERY run — including failed, skipped, or inconclusive runs. Never
overwrite. Run IDs are descriptive and never reused.

## Entry Template

```
Run ID:            <phaseN-purpose-NNN>
Task ID:           <TASK id from atomic list>
Date:              <YYYY-MM-DD>
Git Commit:        <SHA>
Git Status:        <clean / dirty (list)>
Exact Command:     <command>
Config Path:       <configs/...>
Config Hash:       <sha256>
Data Hash:         <sha256 / split id>
Seed:              <int>
Environment:       <GPU, CUDA, Python, key package versions>
Checkpoint Path:   <path or n/a>
Metrics Path:      <runs/.../metrics.json>
Status:            <success / failed / inconclusive>
Failure Notes:     <if applicable>
Interpretation:    <what it means; claim boundary>
Next Action:       <follow-up>
```

## Run ID Allocation

Use descriptive IDs preserving phase and purpose, e.g. `phaseA-smoke-001`, `phase1-k2probe-001`,
`phase1-sweep-seamjepa-seed0`, `phase2-k4-001`. Do not reuse IDs, even for failed attempts.

---

### Run: pa003b-probe-aug-001 (P1.001b — augmented-index CI confirmation)

Run ID:            pa003b-probe-aug-001
Task ID:           P1.001b
Date:              2026-07-02
Git Commit:        2ac86eb (dirty: P1.001b harness changes uncommitted at run time)
Exact Command:     PYTHONPATH=src python -m ezhuthu_jepa.eval.akshara_probe --config configs/phase1/probe-augmented.yaml --run-dir runs/pa003b-probe-aug-001
Config Path:       configs/phase1/probe-augmented.yaml
Config Hash:       sha256:4ccfaf4637f98903…
Data Hash:         sha256:4abd63f965b7acba…  (data/rendered/augmented/index.jsonl, 54k)
Seed:              42
Environment:       RTX 5090, CUDA 13.0, Python 3.x, numpy/pillow/pyyaml (see provenance.json)
Checkpoint Path:   n/a (PixelEncoder reference)
Metrics Path:      runs/pa003b-probe-aug-001/metrics.json (+ predictions.jsonl)
Status:            success
Interpretation:    On the augmented font-holdout index, PixelEncoder metric_M = 0.359 [0.349, 0.369],
                   n = 8,100, **CI half-width = 1.02 pp** — empirically confirms DEC-0013's ~1 pp target
                   (was ~12 pp on PA.003's tiny eval), so a 2 pp effect on M is now adjudicable. This is
                   the reference encoder, not a mechanism result; it validates the *measurement*, not K1.
Next Action:       Wire the JEPA encoder (encoder: jepa) once a real (non-smoke) checkpoint exists.

### Run: phaseA-smoke-001 / -002 / -003 (PA.005 — pretraining smoke, all three objectives)

Run ID:            phaseA-smoke-001 (seam_jepa), -002 (block_jepa), -003 (mae_seam)
Task ID:           PA.005
Date:              2026-07-02
Git Commit:        2ac86eb (dirty: PA.005 loop uncommitted at run time — acceptable for a smoke; the
                   full sweep P1.003 must run on a clean committed tree)
Exact Command:     PYTHONPATH=src python -m ezhuthu_jepa.train.pretrain --config configs/phase1/pretrain.yaml --run-dir runs/phaseA-smoke-001
                   (…-002 --objective block_jepa; …-003 --objective mae_seam)
Config Path:       configs/phase1/pretrain.yaml  (smoke: limit_instances=1024, max_steps=30)
Config Hash:       001 sha256:1425a9d9…  002 sha256:0a37019c…  003 sha256:ee14b401…
Data Hash:         sha256:4abd63f965b7acba…  (data/rendered/augmented/index.jsonl)
Seed:              0
Environment:       RTX 5090, CUDA 13.0, torch 2.10.0+cu130, bf16 autocast (provenance.json)
Checkpoint Path:   runs/phaseA-smoke-00{1,2,3}/encoder.pt
Metrics Path:      runs/phaseA-smoke-00{1,2,3}/metrics.json
Status:            success (AC1: end-to-end run + provenance + metrics + loadable encoder)
Interpretation:    ViT-Tiny/8 = 5.35M-param encoder; 144 tokens; n_mask=36 (0.25) identical across arms
                   (AC2). Objective set by config only. final_loss: seam 0.035, block 0.037 (latent
                   smooth-L1, EMA target), mae 0.976 (pixel MSE — different scale, expected). Throughput
                   2.5–3.5k img/s, peak mem 1.7–1.9 GB. **These are smoke runs (30 steps) — NOT a K1/K3
                   result;** they prove the loop runs, not that any objective wins.
Next Action:       PA.006 compute ledger → LAUNCH-A → P1.003 full n≥3-seed sweep (clean tree, real
                   schedule). Do NOT infer K1/K3 from smoke losses.
