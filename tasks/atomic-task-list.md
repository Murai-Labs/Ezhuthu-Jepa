# Ezhuthu-Jepa — Atomic Task List

Canonical task system. Update this file plus `STATUS.md`, `CHECKPOINT.md`, and affected docs on
any status change.

Gate chain: **G0** (skeleton) → **LAUNCH-A** (approve full Stage-A sweep) → **G1**
(cheap-baseline-falsification) → **G2** (K4 degradation-realism) → **G3** (paper + demo + recipe).

Metric **M** = bottom-quartile-frequency akshara top-1 accuracy (linear-probe/light-finetune),
n ≥ 3 seeds, 95 % bootstrap CIs. ε = 2.0 pp / non-overlapping CIs (pre-register in P1.001).

---

## Phase 0 — Skeleton & Comprehension (Gate G0)

#### TASK P0.001: Verify spec comprehension
- **What:** A written comprehension check capturing the thesis, claims, null hypothesis, and gates.
- **Where:** `notes/spec-comprehension-check.md`
- **Why:** spec §all · AGENTS.md §1 · prevents building the wrong thing.
- **Inputs:** `docs/spec/EZHUTHU_JEPA_Spec_v0.2.md`
- **Acceptance criteria:**
  1. Thesis, empirical claims (K1–K4), and null hypothesis are stated in ≤10 lines.
  2. Each gate G0…G3 (+ LAUNCH-A) is listed with the evidence it requires.
  3. The mandatory cheap baselines (block-JEPA, MAE-seam, base→sign probe) are enumerated.
- **Evidence of completion:** `notes/spec-comprehension-check.md`
- **Validation:** human read; cross-check against the spec.
- **Measurements / logs:** n/a
- **Dependencies:** none
- **Blocking gate:** G0
- **Estimated effort:** 1
- **Done:** [x]

#### TASK P0.002: Establish package skeleton and tests
- **What:** Installable `src/ezhuthu_jepa/` package with version, plus a layout/import smoke test.
- **Where:** `src/ezhuthu_jepa/__init__.py`, `pyproject.toml`, `tests/test_import.py`
- **Why:** spec §4 · AGENTS.md §9 · everything depends on an importable package.
- **Inputs:** none
- **Acceptance criteria:**
  1. `python -c "import ezhuthu_jepa"` succeeds and exposes `__version__`.
  2. `tests/test_import.py` passes.
- **Evidence of completion:** passing `pytest -q`.
- **Validation:** `python -m compileall src && pytest -q`
- **Measurements / logs:** n/a
- **Dependencies:** none
- **Blocking gate:** G0
- **Estimated effort:** 2
- **Done:** [x]

#### TASK P0.003: Implement run-provenance writer
- **What:** A writer that records config hash, code SHA, data hash, seed, and environment per run.
- **Where:** `src/ezhuthu_jepa/provenance.py`, `tests/test_provenance.py`
- **Why:** spec §4 (compute ledger) · AGENTS.md §2.4, §2.6 · no run is allowed without provenance.
- **Inputs:** P0.002
- **Acceptance criteria:**
  1. Writing creates one manifest per run dir containing exactly the 5 identifier categories.
  2. A run dir missing any identifier is rejected by a validator.
- **Evidence of completion:** `src/ezhuthu_jepa/provenance.py`, `tests/test_provenance.py` (9 tests pass).
- **Validation:** `pytest -k provenance`
- **Measurements / logs:** n/a
- **Dependencies:** P0.002
- **Blocking gate:** G0
- **Estimated effort:** 3
- **Done:** [x]

#### TASK P0.004: Lock the Phase-0 config contract
- **What:** A versioned config schema + locked dependency-version file.
- **Where:** `src/ezhuthu_jepa/config.py`, `configs/phase0/locked-versions.yaml`, `tests/test_config.py`
- **Why:** spec §4 · AGENTS.md §2.4 · rejects silent config drift before expensive runs.
- **Inputs:** P0.002
- **Acceptance criteria:**
  1. Loading an out-of-contract config raises a typed validation error.
  2. A schema-consumer audit is written for the new schema.
- **Evidence of completion:** `notes/schema-audits/ezhuthu_jepa-config.md`, `configs/phase0/locked-versions.yaml`, `tests/test_config.py` (18 tests pass).
- **Validation:** `pytest -k config`
- **Measurements / logs:** n/a
- **Dependencies:** P0.002
- **Blocking gate:** G0
- **Estimated effort:** 3
- **Done:** [x]

## Phase A — Rendered-Core Evaluation Harness & Data (feeds LAUNCH-A / G1)

> Stage A of the spec (§4): rendered clean Tamil with free exact grapheme-decomposition labels.
> The evaluation harness and metric M must be frozen here **before** any baseline runs, so the G1
> comparison is judged on a fixed metric.

#### TASK PA.001: Tamil rendering pipeline with grapheme decomposition
- **What:** A renderer that produces akshara images with exact Unicode base/vowel-sign decomposition.
- **Where:** `src/ezhuthu_jepa/data/render.py`, `configs/phase1/render.yaml`, `tests/test_render.py`
- **Why:** spec §4 Stage A · AGENTS.md §2.2 · exact seam labels are the free supervision signal.
- **Inputs:** P0.004
- **Acceptance criteria:**
  1. For a sample of aksharas, the renderer emits image + `{base_id, sign_id, seam_bbox}` and the
     recomposition base×sign matches the source codepoint sequence 100 % on the sample.
  2. Output writes to `data/rendered/` (gitignored) with a committed text-free manifest.
- **Evidence of completion:** `runs/pa001-render-001/{provenance,render-manifest}.json` (432 entries,
  2 fonts), `src/ezhuthu_jepa/data/{grapheme,render,build_uyirmei}.py`, `configs/phase1/render.yaml`,
  `tests/test_grapheme.py` (9) + `tests/test_render.py` (parametrized/font). Per-font seam counts:
  noto 18/142/56, nirmala 18/138/60 (none/glyph/diff).
- **Validation:** `pytest -k "grapheme or render"`; full suite 56 pass.
- **Measurements / logs:** 432 rendered (216×2 fonts); seam_source breakdown per font in manifest.
- **Dependencies:** P0.004
- **Blocking gate:** G1
- **Notes:** shaping via HarfBuzz+FreeType, seam via glyph/diff hybrid; multi-font + generalized
  provenance + seam_source stratification (DEC-0005, DEC-0006). Ligature vowels handled by reporting
  stratified by seam_source (not excluded).
- **Estimated effort:** 6
- **Done:** [x]

#### TASK PA.002: Frequency-stratified benchmark split with bottom-quartile cutoff
- **What:** A train/eval split stratified by compound corpus frequency, with the bottom-quartile
  long-tail bucket defined and frozen.
- **Where:** `src/ezhuthu_jepa/data/frequency_split.py`, `configs/phase1/split.yaml`, `tests/test_split.py`
- **Why:** spec §2, §4 (eval stratified by frequency) · AGENTS.md §6 · DEC-0004 · M is defined on this split.
- **Inputs:** PA.001
- **Acceptance criteria:**
  1. Compound frequencies are computed from **Project Madurai** e-texts (DEC-0004); the
     bottom-quartile cutoff is a recorded number with the corpus snapshot cited/hashed.
  2. Train and eval glyph instances are physically disjoint (no leakage); a test asserts empty overlap.
- **Evidence of completion:** `data/rendered/split-manifest.json` (text-free), passing `pytest -k split`.
- **Validation:** `pytest -k split`
- **Measurements / logs:** per-bucket compound counts.
- **Dependencies:** PA.001
- **Blocking gate:** G1
- **Estimated effort:** 4
- **Done:** [ ]

#### TASK PA.003: Akshara-recognition evaluation harness (metric M)
- **What:** A linear-probe / light-finetune evaluator reporting top-1 accuracy stratified by
  frequency bucket, with 95 % bootstrap CIs.
- **Where:** `src/ezhuthu_jepa/eval/akshara_probe.py`, `tests/test_probe.py`
- **Why:** spec §4 (Eval) · AGENTS.md §2.6, §6 · DEC-0006 · M and its CIs must be frozen before baselines run.
- **Inputs:** PA.002
- **Acceptance criteria:**
  1. Given a frozen encoder, it emits `metrics.json` with per-bucket top-1 accuracy + bootstrap CIs.
  2. The bottom-quartile bucket accuracy (metric M) is a named field.
  3. Accuracy is also reported **stratified by `seam_source` (glyph vs diff)** and by font (DEC-0006),
     so the compositional claim is honest about where base×sign composition is cleanly separable.
- **Evidence of completion:** `metrics.json` schema + passing `pytest -k probe`.
- **Validation:** `pytest -k probe`
- **Measurements / logs:** per-bucket accuracy, CI width.
- **Dependencies:** PA.002
- **Blocking gate:** G1
- **Estimated effort:** 5
- **Done:** [ ]

#### TASK PA.004: Seam-masking module (base visible, vowel-sign region masked)
- **What:** The masking function that hides the dependent vowel-sign region and keeps the base visible.
- **Where:** `src/ezhuthu_jepa/masking/seam.py`, `tests/test_seam_mask.py`
- **Why:** spec §1 (the mechanism) · AGENTS.md §2.1 · DEC-0006 · this is the intervention under test.
- **Inputs:** PA.001
- **Acceptance criteria:**
  1. Given an image + `seam_bbox` (from the render manifest), the mask covers the vowel-sign region
     and leaves the base pixels; for `seam_source=="diff"` (ligatures) the mask covers the diff region.
  2. A block-masking variant with matched mask ratio is exposed behind the same interface (K1 baseline).
  3. Each masked sample carries its `seam_source` so downstream metrics can stratify (DEC-0006).
- **Evidence of completion:** passing `pytest -k seam_mask`.
- **Validation:** `pytest -k seam_mask`
- **Measurements / logs:** realized mask ratio (must match block variant).
- **Dependencies:** PA.001
- **Blocking gate:** G1
- **Estimated effort:** 4
- **Done:** [ ]

#### TASK PA.005: I-JEPA-style ViT pretraining loop (single-5090, seam/block/MAE switchable)
- **What:** A pretraining entry point that trains the small ViT under a selectable objective
  {seam-JEPA, block-JEPA, MAE-at-seam}, with provenance + ≤100-step progress logging.
- **Where:** `src/ezhuthu_jepa/train/pretrain.py`, `configs/phase1/pretrain.yaml`
- **Why:** spec §4 (Backbone) · AGENTS.md §2.4, §4 · one loop, one switched variable = clean K1/K3.
- **Inputs:** PA.003, PA.004, P0.003
- **Acceptance criteria:**
  1. A 1-seed smoke run completes end-to-end and writes a provenance manifest + `metrics.json`.
  2. Objective is set by config only; architecture/compute/mask-ratio are identical across variants.
- **Evidence of completion:** run-id `phaseA-smoke-001`, manifest + metrics.
- **Validation:** smoke run; `pytest -k pretrain_smoke`
- **Measurements / logs:** loss, throughput, GPU mem, step/total/ETA.
- **Dependencies:** PA.003, PA.004, P0.003
- **Blocking gate:** LAUNCH-A
- **Estimated effort:** 8
- **Done:** [ ]

#### TASK PA.006: Compute-ledger pre-commit for K1–K4
- **What:** A pre-committed GPU-hour ledger for K1–K4 vs a full-foundation-model build.
- **Where:** `docs/decisions/compute-ledger.md`, linked from `docs/DECISION_LOG.md`
- **Why:** spec §4 (Compute ledger, MARMAM-style) · AGENTS.md §1 · cheap gate, no sprawl.
- **Inputs:** PA.005
- **Acceptance criteria:**
  1. GPU-hours estimated for smoke/pilot/full-sweep/degradation, summing to a stated total.
  2. A hard ceiling is named beyond which escalation requires human approval.
- **Evidence of completion:** `docs/decisions/compute-ledger.md` + DECISION_LOG entry.
- **Validation:** human review.
- **Measurements / logs:** n/a
- **Dependencies:** PA.005
- **Blocking gate:** LAUNCH-A
- **Estimated effort:** 2
- **Done:** [ ]

## Gate LAUNCH-A — Approve the full Stage-A sweep

#### TASK LA.001: LAUNCH-A authorization review
- **What:** The launch-gate review authorizing the full n ≥ 3-seed Stage-A sweep.
- **Where:** `docs/GATE_LAUNCH_A_REVIEW.md`, `docs/DECISION_LOG.md`
- **Why:** spec §4 · AGENTS.md §7 · the sweep is the single most expensive run.
- **Inputs:** PA.005, PA.006, P1.001
- **Acceptance criteria:**
  1. Eval harness frozen (PA.003), ε pre-registered (P1.001), 1-seed pilot smoke-passed (PA.005),
     compute ledger committed (PA.006) — all linked as evidence.
  2. Explicit human approval recorded before the full sweep launches.
- **Evidence of completion:** signed gate review + DECISION_LOG entry.
- **Validation:** human review.
- **Measurements / logs:** n/a
- **Dependencies:** PA.005, PA.006, P1.001
- **Blocking gate:** LAUNCH-A
- **Estimated effort:** 1
- **Done:** [ ]

## Phase 1 — Cheap-Baseline Falsification (Gate G1, MANDATORY)

> Null hypothesis: seam-masked JEPA is hypothesized to beat {block-masking JEPA, MAE-at-seam} on
> metric M (bottom-quartile-frequency accuracy). If either matches within ε (2.0 pp / overlapping
> 95 % CIs), **G2+ is blocked; the project re-scopes** (to "seam, not target", or clean-script-only).
> The base→sign probe (K2) is a premise gate: if it cannot beat chance, kill before scaling.
> These are real, executed runs — not arguments. "The paper lives or dies here."

#### TASK P1.001: Define and pre-register ε and the bottom-quartile cutoff on metric M
- **What:** A pre-registered equivalence margin ε + frequency cutoff that make G1 adjudicable.
- **Where:** `notes/decision-gates/g1-cheap-baseline.md` (ε section), `docs/DECISION_LOG.md`
- **Why:** spec §3 (kill criteria) · AGENTS.md §3 · ε must be fixed *before* baselines run.
- **Inputs:** P0.001, PA.002
- **Acceptance criteria:**
  1. ε = 2.0 pp on M with the binding adjudicator "non-overlapping 95 % bootstrap CIs, n ≥ 3 seeds",
     stated with a one-line justification.
  2. Recorded with a date **before** any P1.002+ or full-sweep run.
- **Evidence of completion:** DEC-0009 + `notes/decision-gates/g1-cheap-baseline.md` (ε section,
  dated 2026-07-01, approved by Ramchand; before any baseline run).
- **Validation:** human review; timestamp precedes all baseline runs (none have run).
- **Measurements / logs:** n/a
- **Dependencies:** P0.001 (ε margin/rule pre-registered independent of PA.002; the bottom-quartile
  compound *membership* is computed at PA.002 and does not reopen ε).
- **Blocking gate:** G1
- **Estimated effort:** 1
- **Done:** [x]

#### TASK P1.002: K2 premise probe — base→sign predictability
- **What:** A supervised probe predicting vowel-sign class from the consonant-base region only.
- **Where:** `src/ezhuthu_jepa/eval/base_to_sign_probe.py`, `configs/phase1/k2_probe.yaml`
- **Why:** spec §3 K2 · AGENTS.md §3 · if the seam carries no signal, the prior is unmotivated → kill.
- **Inputs:** PA.003, P1.001
- **Acceptance criteria:**
  1. The probe runs on the frozen split and beats the majority-class baseline clearly (report accuracy + CI).
  2. Emits a provenance manifest; progress every ≤100 steps.
- **Evidence of completion:** run-id `phase1-k2probe-001`, `metrics.json`.
- **Validation:** full run; `pytest -k base_to_sign`
- **Measurements / logs:** probe accuracy vs chance, seed.
- **Dependencies:** PA.003
- **Blocking gate:** G1
- **Estimated effort:** 3
- **Done:** [ ]

#### TASK P1.003: K1 + K3 sweep — seam-JEPA vs block-JEPA vs MAE-at-seam on M
- **What:** The full n ≥ 3-seed comparison of the three objectives, evaluated on metric M.
- **Where:** `configs/phase1/sweep.yaml`, run dirs under `runs/phase1-sweep-*`
- **Why:** spec §3 K1/K3 · AGENTS.md §3 · the primary falsification + the latent-vs-pixel ablation.
- **Inputs:** LA.001, PA.005, P1.001, P1.002
- **Acceptance criteria:**
  1. Each of {seam-JEPA, block-JEPA, MAE-at-seam} × n ≥ 3 seeds produces a provenanced `metrics.json`
     on M and per-bucket accuracy.
  2. Results (including any negative/inconclusive) recorded in `docs/EXPERIMENT_LOG.md`.
- **Evidence of completion:** run-ids `phase1-sweep-{seamjepa,blockjepa,maeseam}-seed{N}`, experiment log.
- **Validation:** full runs; experiment log updated.
- **Measurements / logs:** M per variant/seed, CI, throughput, environment.
- **Dependencies:** LA.001, P1.002
- **Blocking gate:** G1
- **Estimated effort:** 10
- **Done:** [ ]

#### TASK P1.004: G1 decision — record falsification outcome
- **What:** The G1 gate decision: did any cheap baseline explain the effect on M?
- **Where:** `notes/decision-gates/g1-cheap-baseline.md`, `docs/GATE_G1_REVIEW.md`, `docs/DECISION_LOG.md`
- **Why:** spec §3 · AGENTS.md §3, §7 · gate is a hard stop.
- **Inputs:** P1.001, P1.002, P1.003
- **Acceptance criteria:**
  1. seam-JEPA vs {block-JEPA, MAE-seam} on M tabulated against the pre-registered ε, with CIs.
  2. Explicit PASS (baselines fail → proceed to G2) or BLOCK (baseline explains effect → re-scope),
     plus the K2 premise verdict.
- **Evidence of completion:** gate review + DECISION_LOG entry with human approval.
- **Validation:** human review.
- **Measurements / logs:** comparison table.
- **Dependencies:** P1.001, P1.002, P1.003
- **Blocking gate:** G1
- **Estimated effort:** 2
- **Done:** [ ]

## Phase 2 — Degradation-Realism (Gate G2, K4)

> Stage B of the spec (§4): re-run K1 under manuscript-like corruption. Only reached if G1 PASSES.

#### TASK P2.001: Manuscript-degradation corruption suite
- **What:** Programmatic corruptions on rendered data: drop puḷḷi, ink bleed, discoloration, noise,
  touching characters.
- **Where:** `src/ezhuthu_jepa/data/degrade.py`, `configs/phase1/degrade.yaml`, `tests/test_degrade.py`
- **Why:** spec §4 Stage B, §3 K4 · AGENTS.md §2.1 · realism gate for the manuscript claim.
- **Inputs:** PA.001
- **Acceptance criteria:**
  1. Each corruption is individually toggleable and parameterized; a test asserts the missing-puḷḷi
     transform removes the dot while preserving the base.
  2. Produces a corrupted eval set with a text-free manifest.
- **Evidence of completion:** manifest under `runs/`, passing `pytest -k degrade`.
- **Validation:** `pytest -k degrade`
- **Measurements / logs:** per-corruption counts.
- **Dependencies:** PA.001
- **Blocking gate:** G2
- **Estimated effort:** 5
- **Done:** [ ]

#### TASK P2.002: Validate corruption realism against a small real-manuscript sample
- **What:** A qualitative + quantitative check that the synthetic corruptions resemble real imagery.
- **Where:** `docs/decisions/degradation-realism.md`, `runs/phase2-realism-001/`
- **Why:** spec §4 Stage B, §8 · AGENTS.md §6 · real sample is validation only, never training.
- **Inputs:** P2.001
- **Acceptance criteria:**
  1. A handful of real pages (EAP / Tamil University / U.V. Swaminatha Iyer imagery) are compared to
     corrupted renders on stated statistics; agreement/divergence documented.
  2. The real sample is confirmed excluded from all training manifests.
- **Evidence of completion:** `docs/decisions/degradation-realism.md`.
- **Validation:** human review; grep training manifests for real-sample IDs (must be absent).
- **Measurements / logs:** comparison statistics.
- **Dependencies:** P2.001
- **Blocking gate:** G2
- **Estimated effort:** 4
- **Done:** [ ]

#### TASK P2.003: K4 run + G2 decision — does the K1 win survive degradation?
- **What:** Re-run the K1 comparison on the corrupted eval set and record the G2 verdict.
- **Where:** `runs/phase2-k4-*`, `docs/GATE_G2_REVIEW.md`, `docs/EXPERIMENT_LOG.md`, `docs/DECISION_LOG.md`
- **Why:** spec §3 K4 · AGENTS.md §3, §7 · headline result for the manuscript community if it survives.
- **Inputs:** P1.004, P2.001, P2.002
- **Acceptance criteria:**
  1. seam-JEPA vs block-JEPA on M under degradation (esp. missing-puḷḷi) tabulated with CIs, n ≥ 3 seeds.
  2. Explicit PASS (survives → manuscript claim earned) or NARROW (vanishes → clean-script-only paper).
- **Evidence of completion:** run-ids `phase2-k4-*`, gate review + DECISION_LOG entry.
- **Validation:** full runs; human review.
- **Measurements / logs:** M under each corruption, CI.
- **Dependencies:** P1.004, P2.001, P2.002
- **Blocking gate:** G2
- **Estimated effort:** 6
- **Done:** [ ]

## Phase 3 — Paper, Demo & Release (Gate G3)

#### TASK P3.001: Frequency-stratified benchmark + open pretraining recipe release
- **What:** The packaged benchmark (splits, metric harness, degradation suite) + reproducible recipe.
- **Where:** `docs/benchmark-card.md`, `configs/` (frozen), `docs/RUNBOOK.md` (recipe section)
- **Why:** spec §5, §7 · AGENTS.md §2.6 · the dataset/benchmark contribution the literature lacks.
- **Inputs:** P2.003
- **Acceptance criteria:**
  1. A third party can reproduce a reported M from the committed configs + recipe (dry-run documented).
  2. Benchmark card states buckets, metric, provenance requirements, and known limitations.
- **Evidence of completion:** `docs/benchmark-card.md`, updated RUNBOOK.
- **Validation:** human review; recipe dry-run.
- **Measurements / logs:** n/a
- **Dependencies:** P2.003
- **Blocking gate:** G3
- **Estimated effort:** 4
- **Done:** [ ]

#### TASK P3.002: Gradio transcription-aid demo
- **What:** A demo that proposes base+sign readings for an input akshara/line for human confirmation.
- **Where:** `src/ezhuthu_jepa/demo/app.py`, `docs/RUNBOOK.md` (demo section)
- **Why:** spec §7 (demo is a first-class deliverable) · AGENTS.md §1 · reaches Project-Madurai volunteers.
- **Inputs:** P2.003
- **Acceptance criteria:**
  1. `python -m ezhuthu_jepa.demo.app` launches and returns a base+sign proposal for a sample input.
  2. The demo loads a provenanced checkpoint (run-id recorded) — no placeholder model.
- **Evidence of completion:** running demo + checkpoint run-id.
- **Validation:** manual launch; smoke assertion on one input.
- **Measurements / logs:** n/a
- **Dependencies:** P2.003
- **Blocking gate:** G3
- **Estimated effort:** 5
- **Done:** [ ]

#### TASK P3.003: arXiv paper draft with honest negatives + G3 decision
- **What:** The paper draft (rendered-core K1–K3 + K4) and the G3 release decision.
- **Where:** `docs/paper/`, `docs/GATE_G3_REVIEW.md`, `docs/DECISION_LOG.md`
- **Why:** spec §7 (deliverable) · AGENTS.md §2.5, §7 · self-justifying arXiv artifact regardless of K4.
- **Inputs:** P3.001, P3.002
- **Acceptance criteria:**
  1. Every reported metric cites its run-id + 5 provenance identifiers; negatives (e.g. K3/K4 outcomes)
     are reported, not hidden.
  2. Explicit G3 release approval recorded.
- **Evidence of completion:** paper draft + signed gate review.
- **Validation:** human review; provenance cross-check.
- **Measurements / logs:** n/a
- **Dependencies:** P3.001, P3.002
- **Blocking gate:** G3
- **Estimated effort:** 12
- **Done:** [ ]
