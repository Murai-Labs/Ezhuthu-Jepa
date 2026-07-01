# Ezhuthu-Jepa

**Grapheme-compositional self-supervision for recovering undigitized Tamil manuscripts.** A
JEPA that masks at the Tamil base/vowel-sign *seam* and predicts the masked region's latent,
so rare and unseen aksharas are composed from seen parts instead of memorized as 216 atomic shapes.

## Current Phase

G0 skeleton complete. Next: freeze the rendering + frequency-stratified evaluation harness and
pre-register ε, then LAUNCH-A → **G1 cheap-baseline-falsification** (the make-or-break gate).

## Research Thesis

- **K1 (primary):** seam-masked JEPA beats block-masking JEPA **on bottom-quartile-frequency
  compounds** (architecture/compute/mask-ratio fixed; n ≥ 3 seeds; non-overlapping CIs).
- **K2 (premise):** a supervised probe predicts vowel-sign class from the consonant-base region
  well above chance (this is the "missing-puḷḷi" reading operation, made computational).
- **K3 (ablation):** JEPA-at-seam beats MAE-at-seam — the win is the latent target, not just the
  boundary (honest reframe to "seam, not target" if MAE captures it).
- **K4 (realism):** the K1 win survives manuscript-like degradation (missing puḷḷi, ink bleed,
  discoloration, touching characters).
- **Null hypothesis the project must defeat:** seam-masked JEPA (latent) vs {block-masking JEPA,
  MAE-at-seam} on **M = bottom-quartile-frequency akshara top-1 accuracy**; if the baselines match
  it within **ε = 2.0 pp / overlapping 95 % CIs**, the mechanism claim is falsified.

## Deliverables

- arXiv paper (rendered-core K1–K3 + K4 degradation suite, honest negatives).
- A usable transcription-aid demo (Gradio) proposing base+sign readings for human confirmation.
- An open pretraining recipe reusable for other Brahmic scripts (Grantha named as replication target).
- A frequency-stratified akshara-recognition benchmark with a degradation suite.

## Repo Guide

| File | Purpose |
|------|---------|
| `AGENTS.md` / `CLAUDE.md` | Operating contract (identical) |
| `CODEX.md` | Codex pointer to AGENTS.md |
| `STATUS.md` | Current state |
| `CHECKPOINT.md` | Exact resume point |
| `tasks/atomic-task-list.md` | Canonical atomic task list |
| `docs/` | Spec, decision log, experiment log, reproducibility, gate reviews |
| `docs/spec/` | Source-of-truth specification (v0.2) |
| `notes/` | Append-only audit trail |
| `configs/` | Locked, versioned configs |
| `runs/` | Run artifacts with full provenance |

## Working Defaults

- **Compute:** single RTX 5090, evenings-scale pretraining. No H100/Lambda for the core claim.
- **Data posture:** repo is text-free; rendered corpora, manuscript imagery, and checkpoints live
  on an external drive and are gitignored. Only manifests, configs, code, docs, reports are committed.
- **Scale ladder:** smoke (1 seed, tiny) → pilot (1 seed, full glyph set) → main (n ≥ 3 seeds
  × {seam-JEPA, block-JEPA, MAE-seam}) → degradation suite.
