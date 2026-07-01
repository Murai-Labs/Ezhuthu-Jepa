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
