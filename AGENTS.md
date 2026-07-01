# Ezhuthu-Jepa — Operating Contract

This file is identical at `AGENTS.md` and `CLAUDE.md`. Both Codex and Claude Code read it.
It inherits from the Murai Labs global CLAUDE.md and overrides where Ezhuthu-Jepa-specific
rules conflict.

**This is a contract. Not guidelines, not best practices. A contract.**

## 0. Required Entry Points

Before any substantive work, read, in this order:
- `STATUS.md` — current project state.
- `CHECKPOINT.md` — exact resume point.
- `tasks/atomic-task-list.md` — canonical tasks with IDs, dependencies, acceptance criteria.
- `docs/RUNBOOK.md` — operational procedures.
- `docs/REPRODUCIBILITY.md` — run evidence requirements.
- `docs/DECISION_LOG.md` — material decisions and their rationale.
- `docs/RISKS_AND_OPEN_QUESTIONS.md` — open blockers.
- `notes/session-log.md`, `notes/stuck-log.md`, `notes/uncertainties.md` — per-session audit trail.

The source-of-truth spec lives at `docs/spec/EZHUTHU_JEPA_Spec_v0.2.md`.

## 1. Identity and Stakes

- **Thesis:** Masking at the Tamil grapheme base/vowel-sign *seam* and predicting the masked
  region's *latent* (JEPA, not pixels) makes the model internalize the abugida's generative rule
  (base × sign → akshara), yielding a recognizer that composes rare/unseen compounds from seen
  parts and degrades gracefully on the long-tail, missing-puḷḷi regime that gates Tamil manuscript
  transcription.
- **Empirical claim(s):** (K1, primary) grapheme-seam JEPA beats block-masking JEPA **specifically
  on bottom-quartile-frequency compounds**, architecture/compute/mask-ratio held fixed, n ≥ 3 seeds,
  non-overlapping CIs. (K2, premise) a supervised probe predicts vowel-sign class from the
  consonant-base region well above chance. (K3, ablation) JEPA-at-seam beats MAE-at-seam, isolating
  boundary from latent target. (K4, realism) the K1 win survives manuscript-like degradation
  (missing puḷḷi, ink bleed, discoloration, touching characters).
- **Null hypothesis:** Mechanism **seam-masked JEPA (latent target)** is hypothesized to outperform
  baselines **{block-masking JEPA, MAE-at-seam}** on metric **M = bottom-quartile-frequency akshara
  top-1 accuracy** (with the **base→sign premise probe** as a kill-before-scale gate). If those
  baselines match seam-masked JEPA within **ε = 2.0 pp on M with overlapping 95 % bootstrap CIs
  across n ≥ 3 seeds**, the hypothesis is falsified and the project re-scopes (to "seam, not target",
  or clean-script-only) or concludes.
- **Deliverables:** (1) arXiv paper — rendered-core K1–K3 plus the K4 degradation suite, with honest
  negatives; (2) a usable transcription-aid demo (Gradio) proposing base+sign readings for human
  confirmation; (3) an open pretraining recipe; (4) a frequency-stratified akshara-recognition
  benchmark with a degradation suite.
- **Compute budget / timeline:** Single RTX 5090, evenings-scale pretraining for the core claim.
  **No H100/Lambda is used for K1–K4.** A pre-committed GPU-hour ledger (K1–K4 vs a full-foundation
  build) gates any escalation.

## 2. The Integrity Contract

These rules exist because silent failures waste weeks of compute. Each is non-negotiable.

### 2.1 Code claims must match code behavior
Never describe code as doing something it does not do. Verify by reading/running, not by memory.

### 2.2 Schema changes require a Schema-Consumer Audit
When you add, remove, or modify a field in any schema, dataclass, dict, or config, immediately
audit **every** consumer and write the checklist to `notes/schema-audits/<schema>.md`:
- Each new field has ≥1 consumer that reads it.
- Each removed field has no remaining references.
- Each modified field's semantics match every consumer.
"I checked" is insufficient — enumerate every consumer and the result.

### 2.3 Placeholders are forbidden in any code path affecting results
No `return 0.0  # TODO`. Raise `NotImplementedError("EZHUTHU-PLACEHOLDER: <what>")`.
Before any run: `grep -r "EZHUTHU-PLACEHOLDER" src tests` must be empty for reachable code.

### 2.4 Configurations are versioned, locked, and traceable
Every run records, before it starts: config hash, code SHA, data hash, seed, environment
(GPU, CUDA, library versions). The recording is a precondition for the run, not a TODO. If the
recording infrastructure is not in place, do not run experiments.

### 2.5 Negative results are first-class
Failed, refuted, and inconclusive results are recorded in `docs/EXPERIMENT_LOG.md` and, when they
refute a prediction, in `notes/negative-results/`. Never overwrite or delete them. A K3 outcome
where MAE-at-seam captures the full win is a **result**, not a failure — it reframes the paper.

### 2.6 Reproducibility is checked, not assumed
A metric is citable only with: run ID, metric file, config hash, code SHA, data hash, seed,
environment, known limitations. Results lacking these go to `notes/untrusted-results.md` and are
excluded from the paper.

## 3. Cheap-Baseline-Falsification Gate (Phase 0/1 requirement)

**No phase past G1 begins until the simplest non-mechanism explanation has been run on metric
M (bottom-quartile-frequency akshara top-1 accuracy) and failed to explain the effect.** Argument
that a baseline "isn't fair" is not sufficient — the baseline must be executed and must fail.
Mandatory baselines for this project:
- **Block/geometric-masking JEPA** — same architecture, compute, and mask ratio, only the mask
  *boundary* differs. If seam masking carries no advantage, generic masking matches it on M. (K1)
- **MAE-at-seam** — same seam boundary, pixel-reconstruction target instead of latent. If the win
  is the boundary and not the latent target, this captures it → reframe as "seam, not target." (K3)
- **Base→sign supervised probe** — premise check: predict vowel-sign class from the consonant-base
  region. If it cannot beat chance clearly, the seam carries no exploitable structure and the prior
  is unmotivated → **kill before scaling.** (K2)

**ε is pre-registered before the baselines run** (2.0 pp on M; binding adjudicator = non-overlapping
95 % bootstrap CIs across n ≥ 3 seeds). If any cheap baseline matches or exceeds the mechanism within
ε on M, **G2+ is blocked; the project re-scopes or terminates.**

## 4. Long-Running Session Discipline

- Checkpoint progress to `STATUS.md` + `CHECKPOINT.md` before every state-changing commit.
- When stuck, append to `notes/stuck-log.md` (task, attempts, failures, hypothesis) and escalate.
- Claims of completion require evidence (a run ID + metrics path), not file existence.
- Any run >30s emits progress every ≤100 steps: step/total, elapsed, ETA (better: loss,
  throughput, memory).
- Runs >30min write a resume-state file each epoch and validate config/seed on restart.

## 5. Subagent Loop Discipline

- Log every subagent invocation to `notes/subagent-log.md` (timestamp, task, prompt summary,
  output summary, action taken).
- Subagents share the parent's blindspots — do not treat agreement among them as verification.
- A subagent that cannot complete its task escalates; it does not fabricate a plausible result.

## 6. Forbidden Patterns

- Hardcoded numeric dtypes scattered across code (centralize in a config/dtype policy).
  Use `dtype=...`, never the deprecated `torch_dtype=...`.
- Evaluation data leaking into training pipelines. Rendered train glyphs and held-out eval glyphs
  are physically separate; the small real-manuscript sample is validation/sanity only — never
  training.
- Reporting **aggregate** accuracy as the headline. Metric M is stratified by compound frequency;
  the long tail is the contribution, and aggregate accuracy hides it.
- Silent fallbacks that mask failure (catch-and-continue without logging).
- Result files without the 5 provenance identifiers.

## 7. Decision Gates

Gate approval is recorded in `docs/DECISION_LOG.md`, with evidence preserved in the matching
`docs/GATE_*_REVIEW.md`.
- **G0** — Repo skeleton, docs, trackers exist (operating system ready).
- **LAUNCH-A** — Approval to commit the full n ≥ 3-seed Stage-A pretraining sweep (seam-JEPA vs
  block-JEPA vs MAE-at-seam), the single most expensive run. Requires: eval harness frozen, ε and
  the bottom-quartile cutoff pre-registered, and a 1-seed pilot that smoke-passes.
- **G1** — Cheap-baseline-falsification complete (Section 3): K2 premise holds, and seam-JEPA beats
  block-masking JEPA on M beyond ε with non-overlapping CIs, and MAE-at-seam does not capture the
  full win. **The paper lives or dies here.**
- **G2** — Degradation-realism (K4): the K1 win survives manuscript-like corruption; corruption
  realism is validated against a small real-manuscript sample. If it vanishes under degradation
  (esp. missing puḷḷi), the paper narrows to the clean-script version (honest, narrower).
- **G3** — Publication & demo release: paper (rendered-core + degradation + honest negatives), a
  working end-to-end Gradio transcription-aid demo, and the open pretraining recipe + benchmark.

## 8. File Conventions

- `notes/` files are append-only and committed to git. Past entries are never edited or deleted;
  a wrong entry is corrected by appending a new one that references it.
- Repo is **text-free**: raw/large/copyrighted data (manuscript imagery, rendered corpora) and
  checkpoints are gitignored (external drive); commit manifests, configs, code, docs, reports only.
- Run IDs are monotonic/descriptive and never reused, even for failed attempts.
- Paper figures live in `docs/figures/`, are **regenerated from a committed script** under
  `src/ezhuthu_jepa/figures/` (never hand-drawn), and each carries a `<fig>.prov.json` sidecar citing
  the source run-id + code SHA. `docs/FIGURES.md` indexes figure → paper section → generator → run. A
  figure may only cite a run whose `provenance.json` is committed.

## 9. Verification

After edits, run the most relevant check available; never report completion on file existence
alone:
- Markdown-only: re-read changed files; check links/headings.
- Code: `python -m compileall src` and focused `pytest -k <area>`.
- Training/data scripts: a short smoke run before any long job.

## 10. Conflict Resolution

Precedence: Section 2 (integrity) > Section 3 (cheap-baseline gate) > Section 7 (gates) >
Sections 4–6 > Section 8. When rules conflict, the higher-precedence rule wins and the conflict
is noted in `docs/DECISION_LOG.md`.
