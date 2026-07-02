# Schema-Consumer Audit — `RunConfig` (TASK P0.004)

Schema: `ezhuthu_jepa.config.RunConfig` · schema_version `0.1.0` · created 2026-07-01.
Per AGENTS.md §2.2, every field is enumerated with its consumer(s). "≥1 consumer reads it" is the
bar; fields with only a future consumer are marked so the debt is visible, not hidden.

## Fields

| Field | Type / constraint | Consumers (present) | Consumers (planned) |
|-------|-------------------|---------------------|---------------------|
| `schema_version` | str == `SCHEMA_VERSION` | `RunConfig._validate` (rejects drift); `to_canonical_dict` → `compute_config_hash` | manifest reader when schema bumps |
| `objective` | one of `ALLOWED_OBJECTIVES` | `_validate`; `compute_config_hash` (hashed) | masking (PA.004) selects seam/block; pretrain loop (PA.005) selects JEPA vs MAE target |
| `seed` | int ≥ 0 (bool rejected) | `_validate`; `provenance.build_manifest` (copied into `identifiers.seed`); `compute_config_hash` | RNG seeding in pretrain loop (PA.005) |
| `mask_ratio` | float in (0, 1) (bool rejected) | `_validate`; `compute_config_hash` | seam/block masking (PA.004), held fixed across objectives for K1/K3 |

## Invariants asserted by tests (`tests/test_config.py`)

1. Unknown key → `ConfigValidationError` (no silent extra fields).
2. Missing key → `ConfigValidationError` (no silent defaults).
3. Wrong type / out-of-range (`seed`, `mask_ratio`) → `ConfigValidationError`, incl. `bool` rejection.
4. Bad `objective` and mismatched `schema_version` → `ConfigValidationError`.
5. `RunConfig` is frozen (immutable after construction).

## Downstream coupling

- `to_canonical_dict()` is the ordered serialization consumed by `provenance.compute_config_hash`.
  **If a field is added/removed/renamed, the config hash changes** → old run hashes no longer match.
  Bump `SCHEMA_VERSION` in the same edit and update this audit + `configs/phase0/locked-versions.yaml`
  (`config_schema_version`). The manifest embeds both the full config and its hash, so a mismatch is
  detectable.

## Open debt

- ~~`objective` and `mask_ratio` currently have only validation + hashing as present consumers.~~
  **Resolved 2026-07-02 (PA.005).** Both now have behavioral consumers:
  - `objective` → `train.pretrain.train` selects latent (seam/block JEPA) vs pixel (MAE) target;
    `masking.seam.make_mask` selects seam vs block placement.
  - `mask_ratio` → `PretrainConfig.n_mask` (= round(mask_ratio × n_tokens)) sets the fixed
    masked-token count, held identical across objectives (K1/K3). See the PA.005 config audit at
    `notes/schema-audits/phase1-configs.md`.
- `SCHEMA_VERSION` stays `0.1.0`: PA.005 did **not** add fields to `RunConfig`. The pretraining knobs
  live in a separate `PretrainConfig` (audited below), which *reuses* `RunConfig` to validate the three
  identity fields. So the locked contract and its config hash are unchanged.
