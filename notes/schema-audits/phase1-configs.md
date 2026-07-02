# Schema-Consumer Audit — `ProbeConfig` (+P1.001b fields) and `PretrainConfig` (PA.005)

Per AGENTS.md §2.2. Two schemas changed/added on 2026-07-02 (Phase-1 harness + pretraining loop).

## A. `ezhuthu_jepa.eval.akshara_probe.ProbeConfig` — fields added at P1.001b

| Field | Type / constraint | Consumer(s) | Notes |
|-------|-------------------|-------------|-------|
| `index_jsonl` | str (default "") | `_load_instances` (index backend); `run_evaluation` (data_hash) | New backend: reads the PA.4b.2 per-instance `index.jsonl`. Precedence over the manifest pair. |
| `checkpoint` | str (default "") | `_build_encoder` (when `encoder == "jepa"`) | Path to a PA.005 `encoder.pt`; required iff encoder is `jepa`. |

Existing fields (`image_dir`, `split_manifest`, `render_manifest`, `ridge_lambda`, `bootstrap_n`,
`seed`, `encoder`, `downsample`) unchanged in meaning. New invariant in `__post_init__`
(`ProbeConfigError`): a config must supply **either** `index_jsonl` **or** both `split_manifest` and
`render_manifest`. Backends are mutually exclusive at read time (`index_jsonl` wins).

- Removed field check: none removed.
- `split_manifest`/`render_manifest` became optional (default ""), so the manifest path still works
  (`configs/phase1/probe.yaml` sets both). Verified: `run_evaluation` branches on `config.index_jsonl`.
- Test coverage: `tests/test_probe.py::test_probe_config_requires_a_backend`.

## B. `ezhuthu_jepa.train.pretrain.PretrainConfig` — new schema (PA.005)

Identity fields are validated by constructing a `RunConfig` (schema 0.1.0) in `__post_init__`, so the
locked contract governs them without a schema bump.

| Field | Consumer(s) | Read? |
|-------|-------------|-------|
| `objective` | `train` (latent vs pixel target; EMA on/off); passed to `RunConfig` validation | ✓ |
| `seed` | `torch.manual_seed`, `np.random.default_rng`, provenance seed; `RunConfig` | ✓ |
| `mask_ratio` | `n_mask` property → masked-token count; `RunConfig` | ✓ |
| `index_jsonl` | `load_train_instances`; `train` data_hash | ✓ |
| `image_dir` | `load_train_instances` | ✓ |
| `exclude_no_sign` | `load_train_instances` (drop no-seam forms) | ✓ |
| `limit_instances` | `load_train_instances` (smoke cap) | ✓ |
| `img_size`,`patch_size` | `grid`/`n_tokens`; `ViTEncoder.patch_embed`; `_patch_pixels`; `__post_init__` divisibility check | ✓ |
| `embed_dim`,`depth`,`num_heads`,`mlp_ratio` | `ViTEncoder` (context + EMA target) | ✓ |
| `pred_dim`,`pred_depth`,`pred_heads` | `Predictor` | ✓ |
| `batch_size`,`max_steps`,`lr`,`weight_decay`,`warmup_steps`,`grad_clip` | `train` optimiser/loop | ✓ |
| `ema_base`,`ema_final` | `train` EMA momentum schedule (latent objectives) | ✓ |
| `device`,`amp_dtype`,`log_every` | `train` runtime/autocast/progress | ✓ |
| `checkpoint_every` | `train` (writes `resume-state.pt` every N steps; 0 = none); `__post_init__` (>=0) | ✓ |

Every field has ≥1 present consumer. `amp_dtype` uses `dtype=` autocast only (AGENTS.md §6 — no
`torch_dtype=`; grep-clean across `src`).

- Config hashing: `PretrainConfig` is a frozen dataclass → `provenance.compute_config_hash` hashes
  `dataclasses.asdict`. Adding/removing a field changes the hash of PA.005 runs (but not RunConfig's).
- Resume-state (AGENTS.md §4): with `checkpoint_every > 0`, `train` writes `resume-state.pt` (weights,
  optimizer, EMA target, NumPy+torch RNG states) atomically every N steps. `--resume` loads it and
  **validates `config_hash` + `seed`** against the current config (`ResumeError` on mismatch), then
  continues from the saved step. Provenance is written **before** the loop (precondition, §2.4) and is
  **not** rewritten on resume. `resume-state.pt` is `*.pt` → gitignored.
- Test coverage: `tests/test_pretrain.py` (objective switch, no-sign exclusion, fixed mask ratio,
  end-to-end run, probe adapter, bad-objective rejection, resume reproduces uninterrupted run, resume
  refuses on config mismatch, resume with no state raises).
