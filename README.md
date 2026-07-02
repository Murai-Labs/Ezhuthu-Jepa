# Ezhuthu-JEPA

**Grapheme-compositional self-supervision for Tamil akshara recognition — a cheap-baseline falsification.**

We tested whether a JEPA that masks a Tamil akshara at its base/vowel-sign **seam** and predicts the
masked region's **latent** representation learns the abugida's composition rule (base × sign → akshara)
better than generic masking or pixel reconstruction. At evenings-scale on rendered multi-font Tamil, the
hypothesis is **falsified on both of its kill criteria**. The project is **concluded** — as a first-class
negative result, not a failure to hide.

> ## ⛔ Status: concluded (G1 = BLOCK)
> The full writeup is **[`docs/REPORT.md`](docs/REPORT.md)**.

## TL;DR of the result

A 1-seed pilot (ViT-Tiny/8, ~20k augmented instances, single RTX 5090), metric **M = bottom-quartile-
frequency akshara top-1 accuracy** on a **held-out font**:

| Arm | Recipe | metric M | |
|-----|--------|---------:|---|
| **seam-JEPA** (the mechanism) | 16k, cosine (best) | 0.290 [.280,.300] | |
| **block-JEPA** (K1 baseline) | 16k, cosine (matched) | **0.335** [.325,.345] | **K1 reversed: block > seam, non-overlapping CIs** |
| **MAE-at-seam** (K3 baseline) | 8k | **0.532** [.521,.542] | **K3 reversed: pixel target ≫ latent** |
| PixelEncoder baseline | — | 0.359 [.349,.369] | both latent arms fall below raw pixels |

Both mandated cheap baselines (generic block-masking, MAE pixel-target) **exceed** the mechanism beyond the
pre-registered ε = 2.0 pp. Recipe iteration (cosine LR + longer training) did not reverse it, and the latent
representation *degraded* with more training. Cost to reach this: **~2 GPU-hours**, before committing the
~15 GPU-hour full sweep — the cheap-baseline gate working exactly as designed.

## What we tested (past tense)

- **K1 (primary):** seam-masked JEPA beats block-masking JEPA on bottom-quartile-frequency compounds,
  architecture/compute/mask-ratio fixed. → **Falsified** (block wins).
- **K2 (premise):** a supervised probe predicts the vowel-sign from the consonant-base region above chance.
  → **Held** the kill-gate (0.509 ≫ 0.091 chance), **but** the signal is dominated by sign *location*; a
  location-normalised probe finds only a thin base-ink composition signal in ligatures (diff−glyph ≈ 8.2 pp).
- **K3 (ablation):** JEPA-at-seam beats MAE-at-seam. → **Falsified** (MAE wins by ~24 pp).
- **K4 (realism):** not reached — G1 blocked before degradation work.

Pre-registered null hypothesis (before any arm ran): seam-masked latent JEPA vs {block-masking JEPA,
MAE-at-seam} on M; if a baseline matched within **ε = 2.0 pp / non-overlapping 95 % bootstrap CIs (n ≥ 3
seeds; paired McNemar primary)**, the mechanism claim is falsified. See `docs/DECISION_LOG.md`
(DEC-0009…DEC-0019) and `docs/GATE_G1_REVIEW.md`.

## Reusable artifacts (these survive the conclusion)

- **Frequency-stratified Tamil akshara-recognition benchmark** + augmented **font-holdout** split (Project
  Madurai frequencies; bottom-quartile cutoff; ~1 pp metric-M CI).
- **Encoder-agnostic evaluation harness** — metric M, bootstrap CIs, seam_source/font stratification, and a
  paired **McNemar** comparator (`src/ezhuthu_jepa/eval/`).
- **Multi-font Tamil rendering + grapheme-seam-labelling pipeline** (HarfBuzz/FreeType; glyph/diff/none seam
  typing; deterministic) (`src/ezhuthu_jepa/data/`).
- **Switchable seam/block/MAE pretraining loop** — ViT-Tiny/8, EMA target, cosine LR, resume-state, and a
  sweep orchestrator with a launch gate (`src/ezhuthu_jepa/train/`).
- **Provenance/config contract** — five-identifier run manifests, strict versioned configs, schema audits
  (`src/ezhuthu_jepa/provenance.py`, `config.py`).

## Reproduce

The repo is **text-free**: code, configs, manifests, and per-run `metrics.json` + `provenance.json` are
committed; rendered images and checkpoints are gitignored and regenerated from committed configs + seeds.
Step-by-step commands are in **[`docs/RUNBOOK.md`](docs/RUNBOOK.md)**. Sketch:

```bash
pip install numpy pillow uharfbuzz freetype-py pyyaml pytest torch   # torch 2.10.0+cu130 used
# fetch the OFL font, render, build the frequency split + augmented font-holdout dataset, then:
PYTHONPATH=src python -m ezhuthu_jepa.eval.akshara_probe --config configs/phase1/probe-augmented.yaml --run-dir runs/tmp-probe
PYTHONPATH=src python -m ezhuthu_jepa.eval.base_to_sign_probe --config configs/phase1/k2_probe.yaml --run-dir runs/tmp-k2
PYTHONPATH=src python -m ezhuthu_jepa.train.sweep --config configs/phase1/pilot.yaml --execute   # 1-seed pilot
pytest -q     # 124 tests
```

The full n ≥ 3 sweep was intentionally not run; `train/sweep.py` refuses it without `--launch-a-approved`.

## Repo guide

| Path | Purpose |
|------|---------|
| **`docs/REPORT.md`** | **The negative-results writeup (start here)** |
| `docs/DECISION_LOG.md` | Every material decision (DEC-0001…DEC-0019) |
| `docs/GATE_G1_REVIEW.md` | The G1 = BLOCK gate record + pilot comparison table |
| `docs/EXPERIMENT_LOG.md` | Per-run log (IDs, hashes, interpretation) |
| `notes/negative-results/` | The falsification notes (first-class, append-only) |
| `docs/RUNBOOK.md` | Copy-pasteable reproduction commands |
| `docs/spec/` | Source-of-truth specification (v0.2) |
| `src/ezhuthu_jepa/` | data · masking · eval · train · provenance · config |
| `configs/phase1/` | Locked, versioned run configs |
| `runs/` | Per-run `metrics.json` + `provenance.json` (bodies gitignored) |
| `AGENTS.md` ≡ `CLAUDE.md` | Operating contract (integrity, cheap-baseline gate, provenance) |

## Why this is a clean outcome

The mandated cheap baselines were *run on the paper's own metric* and *beat the mechanism* before any
expensive scaling — so the project ended for ~2 GPU-hours and one evening instead of a full sweep, a K4
degradation suite, and a paper built on an effect that isn't there. The lab thesis — a latent/evolutionary
outer objective must expose structure the simpler baseline cannot — was tested honestly and did not hold
here. The benchmark, harness, rendering pipeline, and the negative result itself remain useful.

## Compute & data posture

Single RTX 5090, evenings-scale; no H100/Lambda was used for the core claim. Raw/rendered corpora,
manuscript imagery, and checkpoints are gitignored (external drive); only manifests, configs, code, docs,
and reports are committed.
