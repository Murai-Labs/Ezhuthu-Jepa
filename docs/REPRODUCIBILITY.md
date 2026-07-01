# Ezhuthu-Jepa — Reproducibility

## Required Run Evidence

Every run records: git commit, exact command, config path + config hash, data split id + data
hash, seed, environment (GPU, CUDA, Python, package versions), checkpoint path, metrics path,
failure notes (if any), interpretation, next-step recommendation.

## Artifact Integrity

- Configs are copied into the run dir or immutably referenced; immutable after launch.
- Train/eval glyph splits are physically separate; no overlap (asserted by `test_split`). The small
  real-manuscript sample is validation/sanity only and must never appear in a training manifest.
- Metrics, figures, tables, and reports cite the run IDs that produced them, stratified by frequency
  bucket (aggregate accuracy is never the headline).
- Any result file lacking the 5 provenance identifiers → `notes/untrusted-results.md`, excluded
  from the paper.

## Deterministic Rerun Checklist

- [ ] Same git commit
- [ ] Same config hash
- [ ] Same data hash (rendered corpus + split manifest)
- [ ] Same seed
- [ ] Same command
- [ ] Same dependency versions (`configs/phase0/locked-versions.yaml`, when feasible)
- [ ] Same hardware class (RTX 5090, when feasible)

## Reporting Gate

No metric is citable unless it has: run ID, metric file path, config hash, code SHA, data hash,
seed, environment record, and stated known limitations. For every K1/K3/K4 number, the reported
value is the per-seed mean with its 95 % bootstrap CI, on metric M (bottom-quartile bucket).
