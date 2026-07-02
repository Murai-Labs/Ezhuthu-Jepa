# Ezhuthu-Jepa — Decision Log

## Update Rules

Record every material research, tooling, gate, execution, blocker-resolution, or reporting
decision here unless it already has a dedicated file under `docs/decisions/` (which must be
linked from this log). Record the rationale **before** running expensive jobs. Never overwrite
an entry — correct a past entry by appending a new one that references it.

Each entry includes: date, task/gate, decision, rationale, alternatives considered, evidence,
measured result (if any), follow-up, and human-approval status.

---

## DEC-0001 - Project scaffolding established

Date: 2026-07-01
Task/Gate: G0
Decision: Initialized the Ezhuthu-Jepa repo with the standard governance/tracker/docs/notes
scaffolding and the phase→gate chain **G0 → LAUNCH-A → G1 → G2 → G3**.
Rationale: Ezhuthu-Jepa is a research project (spec `docs/spec/EZHUTHU_JEPA_Spec_v0.2.md`) whose
central risk is exactly the cheap-baseline failure mode this operating system guards against —
the spec's own kill criteria (K1 seam-vs-block, K3 JEPA-vs-MAE-at-seam, K2 premise probe) are the
mandatory cheap baselines. Installing the trackers/gates/audit trail up front makes G1 adjudicable.
Alternatives Considered:
- Plain CLAUDE.md without gates — rejected: the cheap-baseline gate is the whole point here.
- Merging LAUNCH-A into G1 — rejected: the full n≥3-seed sweep is the single most expensive run and
  warrants its own explicit launch approval per the skill's always-present launch-gate rule.
Evidence / Source Docs: `docs/spec/EZHUTHU_JEPA_Spec_v0.2.md`, `tasks/atomic-task-list.md`,
`docs/GATE_G0_REVIEW.md`, `notes/spec-comprehension-check.md`.
Measured Result: N/A (setup).
Follow-up: Implement provenance writer (P0.003) and config contract (P0.004); freeze eval harness
and pre-register ε (P1.001) before any baseline run.
Human Approval: pending (G0 review drafted; awaiting Ramchand sign-off).

---

## DEC-0002 - Metric M and ε provisionally set (to be pre-registered at P1.001)

Date: 2026-07-01
Task/Gate: G1 (pre-registration pending)
Decision: Provisionally adopt **M = bottom-quartile-frequency akshara top-1 accuracy** (n ≥ 3 seeds,
95 % bootstrap CIs) and **ε = 2.0 pp with the binding adjudicator "non-overlapping 95 % CIs"**. This
is recorded now for traceability but is **not yet the pre-registration** — TASK P1.001 formally
pre-registers ε and the exact frequency cutoff, dated before any baseline run.
Rationale: The spec (§3 K1, §4 Eval) mandates frequency-stratified evaluation and non-overlapping CIs
on the long tail; aggregate accuracy is explicitly not the contribution. Sub-2pp gaps at probe scale
are within typical seed variance, so the CI-overlap test is the real adjudicator.
Alternatives Considered:
- Aggregate top-1 accuracy — rejected: hides the long-tail story the paper is about.
- ε by a single seed — rejected: no CI ⇒ non-adjudicable gate.
Evidence / Source Docs: spec §3, §4; `tasks/atomic-task-list.md` P1.001.
Measured Result: N/A.
Follow-up: Formalize in P1.001 with the exact bottom-quartile count cutoff once PA.002 computes
corpus frequencies.
Human Approval: pending.

---

## DEC-0003 - Phase-0 config + provenance implemented with stdlib only (no pydantic/PyYAML yet)

Date: 2026-07-01
Task/Gate: G0 (TASK P0.003, P0.004)
Decision: Implemented the run-provenance writer (`src/ezhuthu_jepa/provenance.py`) and the versioned
config contract (`src/ezhuthu_jepa/config.py`, schema `0.1.0`) using **only the Python standard
library** (frozen `dataclass` + a typed `ConfigValidationError`, `hashlib`, `subprocess` git,
`importlib.metadata`). No third-party validation/serialization dependency is added at Phase 0.
Rationale: The training toolchain is not yet chosen (spec §4 keeps the core single-5090 and minimal),
and the earlier decision (DEC-0001 follow-through) kept the skeleton installable without an unlocked
toolchain. Stdlib gives a fully-controlled typed contract with zero install surface; pydantic/PyYAML
are pinned only when a real consumer needs them (`configs/phase0/locked-versions.yaml` → `deferred`,
PyYAML at PA.005 for loading `configs/phase1/*.yaml`).
Alternatives Considered:
- pydantic for config — rejected for now: heavy dep before the training stack exists; revisit if the
  config grows enough that hand-rolled validation becomes a liability.
- Hashing the raw config file bytes instead of a canonical dict — rejected: sensitive to formatting;
  `to_canonical_dict` + sorted-key JSON gives an order/format-independent, stable hash.
Evidence / Source Docs: `src/ezhuthu_jepa/config.py`, `src/ezhuthu_jepa/provenance.py`,
`notes/schema-audits/ezhuthu_jepa-config.md`, `configs/phase0/locked-versions.yaml`,
`tests/test_config.py` (18) + `tests/test_provenance.py` (9) — full suite 28 passed.
Measured Result: All P0.003/P0.004 acceptance criteria pass (manifest carries exactly the 5
identifiers; missing identifier rejected; out-of-contract config raises a typed error).
Follow-up: PA-phase data/train code must call `write_provenance(...)` before any run and load configs
via `RunConfig.from_dict(...)`. Re-audit the schema when PA.004/PA.005 add behavioral consumers.
Human Approval: pending.

---

## DEC-0004 - Metric M, cheap-baseline set, and frequency corpus confirmed by Ramchand

Date: 2026-07-01
Task/Gate: G0 → G1 (methodology confirmation)
Decision: Three of four G0 methodology questions resolved by Ramchand:
1. **Metric M = bottom-quartile-frequency akshara top-1 accuracy** (n ≥ 3 seeds, 95% bootstrap CIs).
   Confirmed as the single primary metric the paper lives or dies on; aggregate accuracy stays barred.
   Alternatives (unseen-compound recall as co-primary, per-compound macro, top-3) considered and rejected
   for v1 — kept as possible secondary reports, not the headline.
2. **Cheap-baseline set = the three (block-masking JEPA, MAE-at-seam, base→sign premise probe).**
   No 4th baseline added. Whole-akshara classifier foil and random-position mask control were offered
   and declined; block-masking JEPA already stands in for the "structured-but-not-seam" control.
3. **Frequency corpus = Project Madurai.** Compound frequencies (hence the bottom-quartile cutoff)
   are computed from Project Madurai e-texts: large, open, citable, and thematically adjacent to the
   manuscript domain and the literal downstream user. Skews classical/literary — acknowledged; a
   second-corpus robustness check may be reported but is not required for G1.
Rationale: Leanest defensible falsification path that stays faithful to the spec's K1/K2/K3 and keeps
the single-5090 budget. Project Madurai maximizes reproducibility + mission fit for defining "long tail".
Alternatives Considered: see the four-option decision prompt (2026-07-01); rejected options noted above.
Evidence / Source Docs: this entry supersedes the provisional metric note in DEC-0002 (metric now
confirmed, not provisional); resolves RISKS Q005; task PA.002 updated to cite Project Madurai.
Measured Result: N/A (methodology).
Follow-up: **ε (equivalence margin) remains UNSET** — the 4th question was not answered. Provisional
ε = 2.0 pp / non-overlapping CIs from DEC-0002 still stands and MUST be formally pre-registered at
TASK P1.001 before any baseline run. Do not launch a baseline until ε is pinned with a prior date.
Human Approval: Ramchand, 2026-07-01 (items 1–3). ε pending.

---

## DEC-0005 - PA.001 rendering: HarfBuzz+FreeType, hybrid seam localization, deterministic provenance

Date: 2026-07-01
Task/Gate: PA.001 (G1 phase)
Decision: Implemented the Tamil rendering pipeline with three sub-decisions:
1. **Shaping engine = HarfBuzz (`uharfbuzz`) + FreeType (`freetype-py`)**, not Pillow's text API.
   Pillow in this environment has no Raqm (`features.check('raqm') == False`), so it cannot reorder
   left vowel signs (ெ ே ை) or form u/uu ligatures — it would silently mis-render Tamil and corrupt
   seam labels (§2.1 violation). HarfBuzz is the industry-standard shaper; FreeType rasterizes shaped
   glyph IDs. Rejected: hacking libraqm DLLs into Pillow (Windows-fragile, less precise for seams).
2. **Seam localization = glyph/diff hybrid.** Nirmala clusters all glyphs of an akshara to cluster 0,
   so HB cluster IDs cannot isolate the sign. Instead: if the bare-consonant glyph survives in the
   shaped output (aa, e/ee/ai, two-part o/oo/au) the seam is the union bbox of the non-base glyphs
   ("glyph"); if the base is substituted into a ligature (i/ii/u/uu) the seam is the pixel-diff of the
   ligature vs the bare consonant ("diff"); the inherent-'a' form has no seam ("none"). Verified on
   all 216 (test_render) and by eye (montage): 138 glyph / 60 diff / 18 none.
3. **Data-gen runs use a deterministic provenance block, not `write_provenance`.** Rendering has no
   RNG, so forcing the RunConfig 5-identifier path (which requires a `seed`) would be a lie. The
   render manifest records config_hash (render.yaml), code_sha, data_hash (font + config), and
   environment, with `seed: "deterministic"`. Training/eval runs still use the full `write_provenance`.
Rationale: correctness of seam labels is load-bearing for the entire experiment; a mis-rendered
abugida would invalidate K1–K4. HarfBuzz is the only correct, reproducible path.
Alternatives Considered: Pillow-only (rejected: wrong shaping); cluster-based seam (rejected: font
merges clusters); pixel-diff for all signs (rejected: reorder breaks base alignment for left signs).
Evidence / Source Docs: `src/ezhuthu_jepa/data/{grapheme,render,build_uyirmei}.py`,
`configs/phase1/render.yaml`, `tests/test_grapheme.py` (9) + `tests/test_render.py` (9),
`runs/pa001-render-001/render-manifest.json` (216 entries). Full suite 46 passed.
Measured Result: PA.001 AC1 (216/216 exact base×sign recomposition) and AC2 (images to
data/rendered/ + committed text-free manifest) both pass.
Follow-up: **Ligature seams (i/ii/u/uu, 60 cases) span most of the glyph** — for these the vowel
fuses with the base, so "mask the sign, keep the base visible" is only cleanly separable for the 138
glyph-source cases. This shapes the PA.004 masking design and the K1 interpretation (see new
uncertainty). Move now-used deps to `pinned` in locked-versions.yaml.
Human Approval: pending.

---

## DEC-0006 - PA.001 follow-through: multi-font, generalized provenance, seam_source stratification

Date: 2026-07-01
Task/Gate: PA.001 → PA.003/PA.004 (G1 phase)
Decision: Three follow-up choices confirmed by Ramchand (multiple-choice review):
1. **Multi-font rendering (Nirmala + Noto Sans Tamil).** Every akshara is rendered under every
   configured font. Noto (OFL, fetched) is the cross-platform reproducible baseline; Nirmala
   (Windows-only) is a second style, skipped where absent. `RenderConfig` changed from a single
   `font_path`/`font_index` to a `fonts: tuple[FontSpec]` list (schema audit:
   `notes/schema-audits/render-config.md`). Fonts are gitignored; pinned per run via the provenance
   `data_hash`. Rationale: seam_source is font-dependent (கி ligates in Nirmala but is a separate
   glyph in Noto), so multi-font tests font-robustness instead of baking in one font's quirks.
2. **Generalized `write_provenance` for seedless runs.** The single provenance writer now accepts a
   RunConfig, any frozen dataclass, or a mapping, and a `seed` that may be an int or
   `SEED_DETERMINISTIC`. Data-gen runs (rendering) go through the same `write_provenance` /
   `validate_run_dir` path as training runs — one honest provenance system, no fake seed. Supersedes
   the separate deterministic-block approach floated in DEC-0005 item 3.
3. **Report metric M stratified by `seam_source` (glyph vs diff).** The K1/K3 comparison is reported
   separately for cleanly-separable-sign aksharas (glyph) and ligature aksharas (diff), keeping all
   data while being honest about where base×sign composition is clean. Binds PA.003 (eval harness must
   emit per-seam_source accuracy) and PA.004 (masking design). Resolves the ligature uncertainty.
Rationale: font-robustness + one provenance path + honest stratification all strengthen the
falsification while avoiding cherry-picking or a fake-seed integrity gap.
Alternatives Considered (per the review options): Pillow+libraqm (rejected: fragile/regression);
seed=0-everywhere (rejected: dishonest); exclude/secondary-bucket ligatures (rejected: drops 28% of
the compound space / risks cherry-picking).
Evidence / Source Docs: `src/ezhuthu_jepa/data/{render,build_uyirmei}.py`,
`src/ezhuthu_jepa/provenance.py`, `configs/phase1/render.yaml`,
`notes/schema-audits/render-config.md`, `runs/pa001-render-001/{provenance,render-manifest}.json`
(432 entries, 2 fonts). Full suite 56 passed.
Measured Result: 432 renders (216×2). Per-font seam split — noto 18/142/56, nirmala 18/138/60
(none/glyph/diff) — confirms font-dependent ligation.
Follow-up: PA.002 frequency split; PA.003 emits accuracy per (frequency-bucket × seam_source × font);
PA.004 masking respects seam_source. New uncertainty resolved (stratify).
Human Approval: Ramchand, 2026-07-01 (three choices). Implementation pending human review.

---

## DEC-0007 - Reproducible, provenanced figures convention (paper artifacts captured as we go)

Date: 2026-07-01
Task/Gate: cross-cutting (paper deliverable hygiene)
Decision: Adopt a figures convention so paper visuals are captured continuously and traceably, not
retrofitted at the end. Figures live in `docs/figures/` (committed — they are *reports*), are
regenerated from committed scripts under `src/ezhuthu_jepa/figures/` (never hand-drawn), and each
carries a `<fig>.prov.json` sidecar recording the figure's `code_sha` and the lineage inherited from
its source run (run-id + that run's config/data hashes). Indexed in `docs/FIGURES.md`. Governance line
added to §8 (CLAUDE.md ≡ AGENTS.md). Backfilled **Figure F1** (seam localization montage), which had
previously been generated only to the ephemeral scratchpad and lost.
Rationale: the earlier seam montage was discarded to scratch — a real gap for a paper deliverable in a
provenance-first project. Operationalizes the pre-existing REPRODUCIBILITY rule that figures cite run
IDs. Chosen option A (full convention + backfill F1) over B (F1 only) / C (defer to PA.003).
Alternatives Considered: hand-made figures at write-up time (rejected: not reproducible, no lineage);
gitignoring figure bytes (rejected: figures are small reports meant to be committed).
Evidence / Source Docs: `src/ezhuthu_jepa/figures/{provenance,f1_seam_localization}.py`,
`docs/figures/f1_seam_localization.{png,prov.json}`, `docs/FIGURES.md`, `tests/test_figures.py` (2).
F1 cites source run `pa001-render-001`. Full suite 58 passed.
Measured Result: F1 regenerable via `python -m ezhuthu_jepa.figures.f1_seam_localization`.
Follow-up: capture F2 (frequency dist, PA.002), F3 (accuracy per bucket×seam_source×font, PA.003),
F4 (K1/K3 main comparison, P1.003), F5 (K4 degradation, P2.003) as those runs land.
Human Approval: pending.

---

## DEC-0008 - G0 gate APPROVED

Date: 2026-07-01
Task/Gate: G0
Decision: G0 (Repo Skeleton Ready) **approved** by Ramchand. The operating system is accepted:
governance contract (CLAUDE.md ≡ AGENTS.md), trackers, docs, append-only notes, atomic task list,
provenance + config contract, and the PA.001 rendering pipeline. This approval also confirms as
reviewed-and-accepted the standing implementation decisions taken in the G0/PA.001 phase whose entries
were marked "pending": DEC-0001 (scaffold), DEC-0003 (stdlib config/provenance), DEC-0005 (HarfBuzz
rendering), DEC-0007 (figures convention). Per the append-only log rule this entry grants that approval
rather than overwriting those entries.
Rationale: skeleton + Phase-0 code + PA.001 complete and verified (58 tests pass); gate chain, metric M,
baselines, corpus, and ε all confirmed (DEC-0004, DEC-0009).
Evidence / Source Docs: `docs/GATE_G0_REVIEW.md` (Approved), full suite 58 passed.
Measured Result: N/A (gate).
Follow-up: G1-phase data/eval work (PA.002 → PA.003) proceeds. LAUNCH-A remains the next gate, before
the full Stage-A sweep; no training run is authorized yet.
Human Approval: Ramchand, 2026-07-01.

---

## DEC-0009 - ε PRE-REGISTERED (G1 falsification threshold locked)

Date: 2026-07-01
Task/Gate: G1 (TASK P1.001)
Decision: ε and the G1 decision rule are **pre-registered before any baseline run** (approved by
Ramchand 2026-07-01): **ε = 2.0 pp on metric M**, with the binding adjudicator **"> ε AND
non-overlapping 95 % bootstrap CIs across n ≥ 3 seeds."** Bottom-quartile cutoff = lowest 25 % of the
216 uyirmei by Project Madurai frequency (membership computed deterministically at PA.002, which does
not reopen ε). Reported stratified by seam_source and font (DEC-0006). Full record:
`notes/decision-gates/g1-cheap-baseline.md`.
Rationale: fixing the margin/rule before results exist is the whole point of the cheap-baseline gate —
it cannot be rationalized after seeing the sweep. Formalizes the provisional value from DEC-0002.
Alternatives Considered: CIs-only (no pp floor) / 3.0 pp / 1.0 pp — see the earlier ε decision prompt;
2.0 pp chosen as the balanced margin (sub-2pp ≈ seed noise at probe scale).
Evidence / Source Docs: `notes/decision-gates/g1-cheap-baseline.md`, `docs/GATE_G1_REVIEW.md`.
Measured Result: N/A (pre-registration; no baseline has run).
Follow-up: P1.002 (K2 probe) and P1.003 (sweep) are evaluated against this fixed ε; P1.004 appends the
PASS/BLOCK outcome. Bottom-quartile membership frozen at PA.002.
Human Approval: Ramchand, 2026-07-01.

---

## DEC-0010 - PA.002: Project Madurai frequency split; bottom quartile frozen

Date: 2026-07-01
Task/Gate: G1 (TASK PA.002)
Decision: Built the frequency-stratified split. Corpus = a **Project Madurai snapshot of 172 UTF-8
works** (fetched via `data.fetch_project_madurai`, HTML-stripped to `.txt`, gitignored, pinned by
per-file sha256 + provenance data_hash). Counted **4,851,420 uyirmei**; **207/216 compounds seen**
(9 unseen → frequency 0). Assigned all 216 to frequency quartiles; **bottom quartile = 54 compounds
frozen** in `runs/pa002-split-001/split-manifest.json` (this is metric M's long tail). Quartile count
boundaries: [711, 6367, 28330, 270681]. Train/eval split: deterministic (seed 42), per-akshara ≥1
instance in each, physically disjoint (216 train / 216 eval over the 2-font render set).
Two implementation choices:
1. **split-manifest lives in the committed run dir** (`runs/pa002-split-001/`), not the template's
   `data/rendered/` — that path is gitignored and the frozen bottom quartile must be committed.
2. Corpus ingestion is a committed, reproducible fetcher; the corpus *bytes* stay gitignored (text-free
   repo) but are hashed into the manifest, so the exact snapshot is reproducible.
Rationale: 4.85M counts over 172 works give stable quartile estimates for 216 classes; the 9 unseen +
rarest (ங velar-nasal forms) are exactly the rare/unseen long tail the paper targets. Does NOT reopen
ε (DEC-0009): membership is a deterministic function of the pinned corpus.
Evidence / Source Docs: `runs/pa002-split-001/{split-manifest,provenance}.json`,
`docs/figures/f2_frequency_distribution.{png,prov.json}`, `tests/test_split.py` (11). Full suite 69 passed.
Measured Result: bottom quartile frozen (54); most frequent k_a/t_a/v_a; rarest ங_* + 9 unseen.
Follow-up: PA.003 eval harness reports M on this split, stratified by seam_source × font.
Human Approval: pending.

---

## DEC-0011 - PA.003: akshara-recognition eval harness; metric M machinery frozen

Date: 2026-07-01
Task/Gate: G1 (TASK PA.003)
Decision: Built the evaluation harness that computes metric M. Design choices:
1. **Encoder-agnostic** (`Encoder` Protocol): the harness takes a frozen encoder and fits a numpy
   ridge linear probe (one-hot targets, closed form, bias term) — no torch/sklearn dependency. A
   built-in **PixelEncoder** (downsample 32² + flatten) is the runnable baseline today; the I-JEPA
   encoder from PA.005 plugs into the same interface and re-runs on the identical split.
2. **Metric machinery frozen before the sweep** (AGENTS.md §2.6): metrics.json reports top-1 accuracy
   overall, per frequency bucket (bottom = **metric M**, a named field), per seam_source, and per font,
   each with a **95 % bootstrap CI**. Per-stratum bootstrap seeds use a stable crc32 offset (not
   Python's randomized `hash`) so CIs are reproducible.
Rationale: freezing M + its CI protocol now means the K1/K3 sweep (P1.003) is judged on a fixed metric.
Alternatives Considered: sklearn LogisticRegression (rejected: adds a dep; ridge is sufficient for a
linear probe); nearest-centroid (rejected: weaker, less standard as a "linear probe").
Evidence / Source Docs: `src/ezhuthu_jepa/eval/akshara_probe.py`, `configs/phase1/probe.yaml`,
`tests/test_probe.py` (6), `runs/pa003-probe-001/{metrics,provenance}.json`,
`docs/figures/f3_probe_accuracy.{png,prov.json}`. Full suite 75 passed.
Measured Result (baseline PixelEncoder, 1-shot cross-font — a REFERENCE, not the science result):
overall 0.403; **metric_M 0.333 [0.222, 0.463]**; buckets q1/q2/q3/q4 = 0.333/0.241/0.389/0.648;
seam_source glyph/diff/none = 0.348/0.421/0.778.
Follow-up: PA.004 (masking) → PA.005 (JEPA pretrain loop; registers the encoder) → re-run this harness
to get the real M per objective for the K1/K3 sweep.
Human Approval: pending.

---

## DEC-0012 - PA.004: seam masking + matched block-masking control

Date: 2026-07-01
Task/Gate: G1 (TASK PA.004)
Decision: Implemented `masking/seam.py`: a boolean pixel `MaskSpec` for two maskers behind one
interface — **seam** (covers the recorded vowel-sign `seam_bbox`, keeps the base visible) and **block**
(the K1 control: a box of the SAME width/height as the seam at a RANDOM location, so only the mask
*location* differs, holding ratio/shape fixed per spec §3). Masks carry `seam_source` for downstream
stratification (DEC-0006); the inherent-'a' form yields an empty mask (nothing to hide). `apply_mask`
supports MAE-style pixel targets; `mask_for_entry` reads a render-manifest entry.
Rationale: this is the intervention under test; the same-size-box-elsewhere control is the cleanest K1
(structured mask, only the seam location varies). MAE-at-seam (K3) reuses the seam mask with a pixel
target at PA.005, so PA.004 stays objective-agnostic.
Evidence / Source Docs: `src/ezhuthu_jepa/masking/seam.py`, `tests/test_seam_mask.py` (10). Full suite 85 passed.
Measured Result: seam and block masks share mask ratio (asserted); block placement varies off the seam.
Follow-up: **PA.005 pretraining loop** consumes these masks. Two research inputs gathered in parallel
(subagent-log 19:40) shape PA.005 and raise a pre-registration question: (a) I-JEPA ViT-Tiny/8 recipe;
(b) augmentation + a **paired-McNemar vs non-overlapping-CI** decision-rule question (see uncertainties
2026-07-01). Forward constraint: augmentation must transform `seam_bbox` with the image.
Human Approval: pending.

---

## DEC-0013 - PA.005 design decisions: ViT size, augmentation + held-out font, McNemar decision rule

Date: 2026-07-01
Task/Gate: G1 (PA.005 prep; amends DEC-0009)
Decision: Three choices confirmed by Ramchand for the training + evaluation design:
1. **ViT-Tiny/8, auto-escalate.** Start with ViT-Tiny/8 (~5.5M/encoder, patch 8 → 144 tokens, narrow
   predictor); escalate to ViT-Small/8 only if the frozen linear probe is clearly capacity-bound.
   Config-swappable; keeps the core evenings-scale on the single 5090.
2. **Full augmentation + held-out-font eval.** Build an augmentation pipeline (safe affine/stroke/
   noise ranges) producing ~100 train and ~150 eval instances per class; **train on one font +
   augments, evaluate on the held-out font + augments**. This shrinks metric M's CI toward ~1 pp and
   measures real generalization, not augmentation memorization. **Augmentation must transform the
   `seam_bbox` with the image** (affine on bbox corners; re-derive for elastic) or the seam mask
   misaligns (DEC-0012 forward note). Changes the PA.002 instance split from per-akshara-random to
   font-holdout; the frequency stratification (bottom quartile) is unaffected (corpus-based).
3. **Decision rule = paired McNemar primary + non-overlapping CI secondary.** Amends the DEC-0009 ε
   rule; recorded as a fresh pre-registration in `notes/decision-gates/g1-cheap-baseline.md` dated
   before any sweep result. ε = 2.0 pp retained as the minimum effect size; McNemar (α=0.05, Bonferroni)
   on identical eval instances is the significance test. Requires a frozen shared eval set across arms/seeds.
Rationale: the three together make a 2 pp win on the long tail statistically adjudicable at feasible
compute, honestly (held-out font, frozen shared eval), while keeping the core cheap.
Alternatives Considered (per the decision prompt): ViT-Small upfront (rejected: 4× compute unproven
need); moderate/no augmentation (rejected: CI too wide to adjudicate ε); McNemar-only or CI-only
(rejected: BOTH is most defensible — power + interpretability).
Evidence / Source Docs: `notes/decision-gates/g1-cheap-baseline.md` (ε amendment), subagent-log 19:40.
Measured Result: N/A (design).
Follow-up: NEW task **PA.4b augmentation pipeline + font-holdout split** before PA.005; PA.003 harness
gains the McNemar comparator; PA.005 uses ViT-Tiny/8. Verify the I-JEPA recipe against the paper at build.
Human Approval: Ramchand, 2026-07-01 (three choices).

## DEC-0014 - PA.005 masking operationalization + P1.001b comparator (implementation decisions)

Date: 2026-07-02
Task/Gate: G1 (implements DEC-0013; P1.001b + PA.005)
Decision: Four implementation choices made while building the eval comparator and the pretraining loop:
1. **Fixed-count, seam-centred token block (not the per-instance pixel-matched box).** The masked set
   is a rectangular token block of a **fixed size** `n_mask = round(mask_ratio × 144)` (36 tokens at
   0.25), identical for every instance and every objective. `seam_jepa`/`mae_seam` place the block
   **centred on the seam bbox** (clamped to the grid); `block_jepa` places the **same-size** block at
   a **random location**. This makes "mask ratio held fixed across objectives" *exact* (AC2) and
   batchable, and keeps K1 = location-only difference, K3 = target-only difference. (The pixel-level
   `masking.seam.matched_block_mask` from PA.004 matches size *per instance*; the loop instead fixes
   size globally — a stricter form of the same invariant. Both satisfy "vary only boundary/target.")
2. **No-sign ('a') forms excluded from pretraining** (`exclude_no_sign=True`), the same exclusion for
   every arm. They have no seam to hide; masking them would inject block-like masking into the seam arm
   and confound K1. They remain fully evaluated by the probe (all 216 classes); only the SSL loss skips
   them. ~18/216 classes, mostly high-frequency (q4) — does not touch the bottom-quartile M contribution.
3. **Latent vs pixel is the only cross-objective architecture difference.** seam/block JEPA use an EMA
   target encoder + smooth-L1 in latent space; MAE-at-seam predicts normalised patch pixels (MSE, no
   target encoder). Encoder + predictor trunk are byte-identical across all three; only the predictor
   head output dim (D=192 latent vs 64 pixels) and the presence of the EMA target differ — that *is*
   the K3 variable, not an incidental asymmetry.
4. **G1 comparator = paired McNemar (exact binomial < 25 discordants, else χ² w/ continuity), Bonferroni
   on p** (primary) **+ non-overlapping bootstrap-CI verdict** (secondary), ε = 2.0 pp as the minimum
   effect size (DEC-0009/0013). Requires identical eval instances across arms → the harness now writes
   `predictions.jsonl` (per-instance key+correctness) so arms can be paired at P1.003.
Rationale: makes AC2 exact and the loop batchable; keeps K1/K3 clean; implements the DEC-0013 decision
rule as a reusable, tested function. From-scratch ViT (torch.nn only) rather than timm — needed for the
I-JEPA visible-token-only context encode + mask-token predictor, which timm's ViT does not expose.
Alternatives Considered: per-instance size-matched mask (rejected: variable count breaks batching and is
no cleaner than a global fixed count); include 'a' forms with a centre/random block (rejected: injects
block masking into the seam arm); timm backbone (rejected: I-JEPA forward needs custom token routing).
Evidence / Source Docs: `src/ezhuthu_jepa/train/pretrain.py`, `src/ezhuthu_jepa/eval/akshara_probe.py`,
`notes/schema-audits/phase1-configs.md`, runs `phaseA-smoke-001/-002/-003`, `pa003b-probe-aug-001`.
Measured Result: smoke — all three objectives run end-to-end (ViT-Tiny/8, 5.35M enc, n_mask=36);
augmented probe CI half-width 1.02 pp (confirms DEC-0013's ~1 pp). NOT a K1/K3 result.
Follow-up: PA.006 compute ledger → LAUNCH-A → P1.003 full sweep on a clean tree. Verify the I-JEPA recipe
(EMA schedule, predictor depth, mask scale) against the paper before the full run.
Human Approval: implementation decisions under the DEC-0013 mandate; flag to Ramchand at the LAUNCH-A review.

## DEC-0015 - Compute-hour ledger pre-committed for K1–K4 (TASK PA.006)

Date: 2026-07-02
Task/Gate: LAUNCH-A precondition (spec §4 compute ledger; AGENTS.md §1 cheap gate)
Decision: Pre-committed the K1–K4 GPU-hour ledger at `docs/decisions/compute-ledger.md` **before** the
sweep. Unit costs are measured from the PA.005 smokes (seam 50 ms/step, block 43, mae 37 at batch 128 on
the RTX 5090; 169 steps/epoch; probe eval ~4 min, load-bound). Planned full run = 50,000 steps (~296
epochs, pilot-confirmed at LAUNCH-A). Line items: smoke (done) + K2 probe (~0.3h) + pilot (~1.0h) + full
K1/K3 sweep (9 runs, ~5.7h) + sweep evals (~0.6h) + K4 degradation (~4.0h), ×1.3 buffer → **~15 GPU-h
total** for the whole program on one 5090. **Hard ceiling = 40 RTX-5090 GPU-hours cumulative**; crossing
it halts for Ramchand's written approval. Escalation never means a bigger GPU — the H100/Lambda exclusion
for K1–K4 stands; the option is re-scope, not more hardware. A full-foundation build (10²–10³× the plan)
is explicitly out of scope for K1–K4.
Rationale: makes "evenings-scale on one 5090" a number and gates sprawl before the expensive run, per the
MARMAM-style ledger rule. Grounding unit costs in measured smoke throughput keeps the estimate honest.
Alternatives Considered: no ceiling / soft target (rejected: the whole point is a hard gate); budget in
wall-clock not GPU-h (rejected: GPU-h is the portable, provenance-checkable unit); pilot-first then ledger
(rejected: the ledger must precede LAUNCH-A, which the pilot feeds).
Evidence / Source Docs: `docs/decisions/compute-ledger.md`; runs `phaseA-smoke-001/-002/-003`,
`pa003b-probe-aug-001`; `src/ezhuthu_jepa/train/pretrain.py`.
Measured Result: N/A (budget/plan). Run lengths are provisional pending the LAUNCH-A pilot.
Follow-up: the LAUNCH-A gate review cites this ledger as evidence; the sweep config sets 50,000 steps +
checkpoint_every and per-seed run dirs. Revisit the 50k step budget if the pilot shows non-convergence.
Human Approval: ledger pre-committed by the agent under §1; the 40-GPU-h ceiling + sweep launch require
Ramchand's sign-off at LAUNCH-A.

## DEC-0016 - K2 premise verdict criterion + honest signal-attribution finding (TASK P1.002)

Date: 2026-07-02
Task/Gate: G1 (K2 premise gate; spec §3, AGENTS.md §3)
Decision: Two decisions from building + running the K2 base→sign probe (`phase1-k2probe-001`):
1. **Verdict criterion = the contract's kill-gate, not "base beats geometry".** The K2 gate passes iff
   the base-region probe clearly beats **chance and the majority baseline** (the "can it beat chance"
   test AGENTS.md §3 specifies). It does, decisively: base = 0.509 [0.503, 0.515] vs chance/majority
   0.091 (~5.6×) on the augmented font-holdout eval. Sign LOCATION is legitimately available to the JEPA
   predictor (it is told which positions to reconstruct), so a mask-geometry control is **not** the
   pass/fail — it is reported as signal *attribution*. (An earlier draft used "base must beat the
   geometry control" as the gate; rejected as testing a stronger, different claim than K2, and using a
   flawed instrument — a bright rectangle is a stronger locator than base_only's black hole.)
2. **Record the geometry-dominance finding as a first-class caveat (§2.5), not bury it.** A
   sign-location-only control (seam bbox on a blank canvas) **beats** the base-region probe in *every*
   stratum (glyph 0.695 > 0.604; diff 0.457 > 0.291). So the base→sign signal is sign location, not
   base-ink composition, and the base-ink signal is weakest in the ligature ('diff') stratum where the
   thesis most expects it. The premise HOLDS (structure is exploitable) but the motivating story ("the
   base *shape* tells you the sign") is not supported by a linear pixel probe.
Rationale: honest gating — pass on the contract's criterion, but do not oversell. The finding raises the
stakes on K1 (if the structure is largely location, block-JEPA may match seam-JEPA on M — exactly the
cheap baseline K1 must defeat), which is the right thing to surface *before* the expensive sweep.
Alternatives Considered: (a) gate on base>geometry → rejected (wrong claim + flawed instrument); (b) drop
the geometry control and report bare "51% ≫ 9%" → rejected (dishonest — hides that it is location);
(c) call K2 a FAIL → rejected (it beats chance decisively; the contract's kill criterion is not met).
Evidence / Source Docs: `runs/phase1-k2probe-001/metrics.json`,
`notes/negative-results/k2-base-ink-signal-is-location-not-composition.md`,
`src/ezhuthu_jepa/eval/base_to_sign_probe.py`.
Measured Result: base 0.509 [0.503,0.515]; location-control 0.623; glyph 0.604 vs 0.695; diff 0.291 vs
0.457; majority/chance 0.091. premise_holds = True (kill-gate); base_beats_location_control = False.
Follow-up: cite in the LAUNCH-A packet and the G1 review as a live risk to K1; a raw-pixel probe may
understate what a learned encoder extracts (K1/K3 adjudicate). Optional future: a location-normalised
base-ink probe to isolate pure composition (non-gating).
Human Approval: agent's methodological call under the K2 mandate; the caveat is flagged for Ramchand at
LAUNCH-A (it materially affects the K1 risk assessment).

## DEC-0017 - LAUNCH-A BLOCKED: pilot shows latent I-JEPA underperforms the pixel baseline

Date: 2026-07-02
Task/Gate: LAUNCH-A (pilot precondition, spec §4)
Decision: **Block LAUNCH-A / the full sweep (P1.003).** The 1-seed pilot (`phase1-pilot-*`, 8k steps,
ViT-Tiny/8, mask 0.25, constant LR) shows both latent arms below the raw-pixel baseline on metric_M
(seam 0.239, block 0.326 with the I-JEPA target encoder; pixel baseline 0.359), while MAE-at-seam
dominates at 0.532. The target-encoder fix (save + probe the EMA target, the I-JEPA downstream
representation; commit this turn) did not rescue them, so this is a genuine recipe/scale deficiency,
not an eval-protocol artifact. Launching the ~15 GPU-h sweep now would compare broken latent encoders
(K1 = noise) and hand K3 to MAE as an artifact. **Do not launch until latent JEPA is competitive with
the pixel baseline on the pilot.**
Rationale: this is the pilot doing its job — catching an under-baked mechanism for ~1 GPU-h before the
expensive run, and the Murai-Labs thesis in action (the fancy latent objective must beat the cheap
baselines; so far it does not). Cheap-baseline gate discipline: MAE + raw pixels are the baselines, and
they currently win.
Alternatives Considered: (a) launch anyway and report — rejected (wastes ~15 GPU-h comparing broken
encoders, pollutes the K1/K3 record); (b) declare the project killed now — rejected (the recipe is
admittedly simplified vs the I-JEPA paper; one cheap iteration is owed before a kill).
Options escalated to Ramchand: (A) **recipe iteration** [recommended] — add LR cosine decay (loss
plateaued under constant LR), verify the recipe vs the I-JEPA paper (multi-block masking, WD schedule,
target LayerNorm, mask-scale), re-pilot until latent ≥ pixels; (B) **reframe to "seam, not target"**
(MAE-at-seam), which Section 1's null-hypothesis clause explicitly permits; (C) if (A) fails, conclude
honestly. Recommend (A) first.
Evidence / Source Docs: `notes/negative-results/pilot-latent-jepa-underperforms-pixel-baseline.md`,
`notes/stuck-log.md` (2026-07-02), runs `phase1-pilot-{seam,block,mae}-seed0`,
`phase1-pilotprobe-*-001`; `src/ezhuthu_jepa/train/{sweep.py,pretrain.py}`.
Measured Result: metric_M — seam 0.239 [0.230,0.248], block 0.326 [0.316,0.336], mae 0.532
[0.521,0.542]; pixel baseline 0.359. 1 seed, non-adjudicating.
Follow-up: NEW task PA.005b (recipe iteration) before any LAUNCH-A retry. LAUNCH-A gate review stays
unsigned. Sweep orchestrator (`sweep.py`) already refuses the ≥3-seed run without `--launch-a-approved`.
Human Approval: **REQUIRED** — Ramchand chooses A/B/C. The agent will not iterate the recipe or launch
anything further without direction.

## DEC-0018 - PA.005b recipe iteration (option A) — cheap baselines still exceed the mechanism (kill signal)

Date: 2026-07-02
Task/Gate: PA.005b → LAUNCH-A / Section 3 cheap-baseline gate
Decision: Ramchand chose option A (recipe iteration). Implemented **LR cosine decay** (`_lr_at`, the
standard I-JEPA schedule; the pilot's constant LR was the first suspect) and swept steps. Outcome — the
mechanism still loses to both cheap baselines on metric M (1 seed, target-encoder probe, augmented eval):

| arm | recipe | metric_M | note |
|-----|--------|----------|------|
| seam_jepa | 8k const  | 0.239 | (DEC-0017) |
| seam_jepa | 16k cosine | **0.290** [.280,.300] | best latent point |
| seam_jepa | 50k cosine | 0.212 [.204,.221] | **degrades with scale** (eff-rank 39.7→20.2) |
| block_jepa | 16k cosine | **0.335** [.325,.345] | **K1: block > seam, non-overlapping CIs** |
| mae_seam | 8k const | **0.532** [.521,.542] | **K3: MAE ≫ latent** |
| pixel baseline | — | 0.359 | both latent arms below it |

Findings: (1) cosine LR helped seam 0.239→0.290 but not above the pixel baseline; (2) the full 50k budget
made seam **worse** (0.212) with a falling effective rank — the latent representation degrades with
extended training; (3) at the **matched** 16k-cosine recipe, **block-JEPA (0.335) beats seam-JEPA (0.290)
beyond ε with non-overlapping CIs** — the K1 direction is *reversed*; (4) MAE-at-seam (pixel target)
crushes latent-JEPA (0.532 vs 0.290) — the K3 direction is *reversed*. So **both mandated cheap baselines
(block-masking JEPA, MAE-at-seam) exceed the seam-latent mechanism**, well beyond ε = 2 pp.
Rationale: this is exactly the Section 3 cheap-baseline-falsification condition ("if any cheap baseline
matches or exceeds the mechanism within ε on M → G2+ is blocked; re-scope or terminate"), and the
Murai-Labs thesis in action — the latent outer objective does not earn its keep over a simpler pixel
target here. Recipe iteration (option A) was tried and did **not** reverse the direction. Caveat: this is
n = 1 seed (a pilot), not the n ≥ 3 formal G1 adjudication; but the signal is strong, consistent across
recipes, and the pilot exists precisely to avoid spending the sweep on a falsified mechanism.
Alternatives Considered: run the full n≥3 sweep anyway — rejected (the 1-seed signal is strong on both
kill criteria; the sweep would most likely confirm a kill at ~15 GPU-h); more aggressive recipe surgery
(anti-collapse/VICReg reg, ViT-Small, multi-block masking) — possible but the prior is now against it, and
block > seam means even the seam *mask* (independent of target) is not winning.
Evidence / Source Docs: runs `phase1-pilotB-{seam,block}_jepa-seed0`, `phase1-pilotC-seam_jepa-seed0`,
`phase1-pilotB/Cprobe-*`; `notes/negative-results/pilot-latent-jepa-underperforms-pixel-baseline.md`
(Update 2), `notes/stuck-log.md`; `src/ezhuthu_jepa/train/pretrain.py` (`_lr_at`).
Measured Result: see table. block 0.335 > seam 0.290 (K1 reversed); MAE 0.532 ≫ seam 0.290 (K3 reversed).
Follow-up / options escalated to Ramchand: (i) a cheap diagnostic — **MAE-at-block vs MAE-at-seam** (~10
min) — to test whether the seam *mask* helps at all with a pixel target (does any "seam, not target"
reframe survive?); (ii) **re-scope/reframe** per Section 3; (iii) **conclude** with an honest negative
(seam-latent JEPA loses to block-masking and to MAE at evenings-scale). Agent recommendation: run (i) as
the last cheap datapoint, then decide (ii)/(iii); do NOT launch the full sweep.
Human Approval: **REQUIRED** — this is a potential project re-scope/termination (Section 3). No further
compute or direction changes without Ramchand.

## DEC-0019 - G1 = BLOCK; PROJECT CONCLUDED (Section 3 cheap-baseline falsification)

Date: 2026-07-02
Task/Gate: G1 (final)
Decision: **Conclude the Ezhuthu-JEPA project.** Ramchand's call: "Goal was to use a JEPA model to help
Tamil — we end it here." The central thesis (seam-masked **latent** JEPA beats {block-masking JEPA,
MAE-at-seam} on M = bottom-quartile-frequency akshara accuracy) is **falsified** by the LAUNCH-A pilot:
at the matched best recipe, **block-JEPA (0.335) > seam-JEPA (0.290)** beyond ε with non-overlapping CIs
(K1 reversed), and **MAE-at-seam (0.532) ≫ latent seam-JEPA (0.290)** (K3 reversed). Both mandated cheap
baselines exceed the mechanism; recipe iteration (cosine LR + scale, DEC-0018) did not reverse it, and
more training degraded the latent representation. G1 = **BLOCK**.
Rationale: this is the Section 3 gate working as designed and the Murai-Labs thesis confirmed — the
latent outer objective did not earn its keep over a simpler pixel-reconstruction target on this task at
evenings-scale. The pilot delivered the kill for ~2 GPU-hours instead of the ~15 GPU-h full sweep and
months of downstream work. Scope-integrity win: killed fast, cheaply, honestly.
Basis + honest caveat: the decision rests on a **1-seed pilot**, not the pre-registered n≥3 sweep. The
formal G1 rule wanted n≥3 with non-overlapping CIs; Ramchand elected to conclude on the pilot because the
signal is strong, consistent across three recipe variants, and adverse on **both** kill criteria — so the
full sweep would most likely spend the budget to confirm a kill. Recorded as a limitation, not hidden.
What the negative result means (for any future write-up): on rendered multi-font Tamil aksharas at
evenings-scale (ViT-Tiny/8, ~20k augmented instances), (1) masking the grapheme **seam** did not beat
generic **block** masking for compositional recognition, and (2) a **latent** JEPA target was clearly
worse than **pixel** reconstruction (MAE) — the latter both stronger and stable. The K2 premise (base→
sign) held only via sign *location*, with a modest base-ink composition signal in ligatures (DEC-0016,
P1.002b) — consistent with a weak compositional prior that the latent objective failed to exploit.
Reusable assets that survive the conclusion (open-release candidates): the frequency-stratified
akshara-recognition **benchmark** + augmented font-holdout split (PA.002/PA.4b), the encoder-agnostic
**eval harness** with metric M + bootstrap CIs + paired McNemar (PA.003/P1.001b), the multi-font Tamil
**rendering + seam-labelling pipeline** (PA.001/PA.004), the **provenance/config contract** (P0.003/4),
and the switchable seam/block/MAE **pretraining loop** with resume (PA.005). The honest negative itself
is a citable result.
Evidence / Source Docs: `docs/GATE_G1_REVIEW.md` (pilot comparison table), DEC-0016/0017/0018,
`notes/negative-results/{pilot-latent-jepa-underperforms-pixel-baseline.md,k2-base-ink-signal-is-location-not-composition.md}`,
`notes/stuck-log.md`, runs `phase1-k2probe-001`, `phase1-baseink-001`, `phase1-pilot*`.
Measured Result: seam 0.290 < block 0.335 (K1 reversed); seam 0.290 ≪ MAE 0.532 (K3 reversed); both < /
mixed vs pixel 0.359. Section 3 falsification met (pilot, n=1).
Follow-up: G2–G3 not entered. Full n≥3 sweep NOT run (budget preserved; `sweep.py` still gates it). No
further compute. Optional (future, separate decision): open-release the benchmark + harness + honest
negative as a short report; revisit only with a materially different approach (e.g. pixel-target-at-seam
as its own hypothesis, larger scale, or anti-collapse latent recipe) — not under this thesis.
Human Approval: **Ramchand, 2026-07-02 — CONCLUDE.**
