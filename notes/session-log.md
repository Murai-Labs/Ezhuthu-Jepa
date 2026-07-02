# Session Log (append-only)

Per-session checkpoints. Append; never edit past entries.

## Entry format
### <YYYY-MM-DD HH:MM TZ> — <session purpose>
- Started from: <CHECKPOINT.md resume point / task ID>.
- Did: <what happened>.
- Ended at: <state; next task ID>.
- Open uncertainties carried forward: see `notes/uncertainties.md`.

---

### 2026-07-01 12:00 CT — G0 scaffolding
- Started from: empty repo (project init from spec).
- Did: ran research-project-init against `docs/spec/EZHUTHU_JEPA_Spec_v0.2.md`; created governance
  contract (CLAUDE.md ≡ AGENTS.md), CODEX pointer, trackers, docs suite, five gate reviews, atomic
  task list, append-only notes, minimal `ezhuthu_jepa` package + import test; placed the spec under
  `docs/spec/`. Derived gate chain G0 → LAUNCH-A → G1 → G2 → G3; set M and provisional ε.
- Ended at: G0 complete, pending human approval. Next: TASK P0.003 (provenance writer).
- Open uncertainties carried forward: see `notes/uncertainties.md`.

### 2026-07-01 13:30 CT — Phase-0 code: provenance + config contract
- Started from: G0 skeleton (CHECKPOINT resume point) → TASK P0.003, P0.004.
- Did: implemented `provenance.py` (5-identifier manifest writer + `validate_run_dir`, git SHA
  capture, canonical config hashing, data-file hashing, best-effort env capture) and `config.py`
  (frozen `RunConfig`, schema `0.1.0`, strict `from_dict`, typed `ConfigValidationError`); wrote
  `configs/phase0/locked-versions.yaml` and the schema-consumer audit; added `test_provenance.py`
  (9) + `test_config.py` (18). Full suite 28 passed; placeholder scan clean. Recorded DEC-0003.
- Ended at: P0.001–P0.004 done. Next: PA.001 (rendering pipeline) → PA.002/PA.003 → P1.001 (ε).
- Open uncertainties carried forward: see `notes/uncertainties.md` (unchanged; ε still provisional).

### 2026-07-01 14:00 CT — G0 methodology confirmation
- Started from: G0 review packet; four-question decision prompt to Ramchand.
- Did: recorded DEC-0004 — Metric M = bottom-quartile top-1 acc (confirmed), cheap-baseline set = the
  three (confirmed), frequency corpus = Project Madurai (resolves RISKS Q005, updates PA.002). ε was
  not answered; provisional 2.0 pp / non-overlapping CIs (DEC-0002) still stands, to be pinned at P1.001.
- Ended at: 3/4 G0 methodology decisions locked; ε open. Next: confirm ε, then G0 sign-off → PA.001.
- Open uncertainties carried forward: ε unset (see DEC-0004 follow-up); corpus skew limitation noted.

### 2026-07-01 15:30 CT — PA.001 Tamil rendering pipeline
- Started from: PA.001 (rendering pipeline). Probed env: Pillow 12.1.1 (no Raqm), numpy, Nirmala font.
- Did: added `data/grapheme.py` (18×12=216 exact base×sign model), `data/render.py` (HarfBuzz shaping
  + FreeType raster + glyph/diff seam hybrid), `data/build_uyirmei.py` (dataset+manifest builder),
  `configs/phase1/render.yaml`; installed+pinned uharfbuzz/freetype-py/pyyaml/pillow/numpy. Tests
  caught 2 real bugs (canvas clipping on 3-glyph au/o signs; ligature mislabeled as glyph) — both
  fixed. Generated all 216 → `runs/pa001-render-001/render-manifest.json` (138 glyph/60 diff/18 none),
  eyeballed via seam-overlay montage. Recorded DEC-0005; new uncertainty on ligature seams. 46 tests pass.
- Ended at: PA.001 done. Next: PA.002 (Project Madurai frequency split) → PA.003 → P1.001 (ε).
- Open uncertainties carried forward: ε unset; ligature vowels have no separable sign region (PA.004).

### 2026-07-01 16:30 CT — PA.001 follow-through: multi-font + provenance + stratify (DEC-0006)
- Started from: 3 multiple-choice decisions (multi-font / generalize provenance / stratify M).
- Did: (1) generalized `write_provenance` to accept dataclass/mapping configs + SEED_DETERMINISTIC
  (4 new tests); (2) reworked render.py to multi-font (FontSpec list), fetched Noto Sans Tamil (OFL,
  gitignored), updated render.yaml/build_uyirmei/tests + render-config schema audit; build now writes
  unified provenance.json via write_provenance; (3) bound seam_source stratification into PA.003/PA.004
  and resolved the ligature uncertainty. Regenerated 432 images (216×2). 56 tests pass. Recorded DEC-0006.
- Ended at: PA.001 finalized multi-font. Next: PA.002 (Project Madurai frequency split).
- Open uncertainties carried forward: ε unset; small n per (bucket×seam_source×font) stratum to watch.

### 2026-07-01 17:15 CT — Figures convention + Figure F1 (DEC-0007)
- Started from: question "are we capturing figures for the paper?" — gap found: the PA.001 montage had
  only gone to scratch and was lost.
- Did: added `figures/{provenance,f1_seam_localization}.py` (regenerable figures with `.prov.json`
  sidecars citing source run-id + lineage hashes), `docs/FIGURES.md` index, governance line in
  §8 (CLAUDE.md ≡ AGENTS.md re-verified identical), `tests/test_figures.py` (2). Generated and
  committed **F1** (seam-localization montage, Noto) citing run pa001-render-001. 58 tests pass. DEC-0007.
- Ended at: figures pipeline live; F1 captured. Next: PA.002; capture F2 (freq dist) there.
- Open uncertainties carried forward: ε unset; small-n strata.

### 2026-07-01 17:45 CT — G0 approved + ε pre-registered
- Started from: Ramchand sign-off ("G0 signed off and p1.001 approved").
- Did: recorded G0 approval (DEC-0008, `GATE_G0_REVIEW.md` → Approved) and pre-registered ε (DEC-0009,
  `notes/decision-gates/g1-cheap-baseline.md`): ε = 2.0 pp + non-overlapping 95 % CIs (n≥3), bottom
  quartile by Project Madurai freq (membership frozen at PA.002, no reopening). Marked P1.001 done;
  resolved the ε uncertainty; updated trackers. No baseline has run, so pre-registration precedes results.
- Ended at: G0 approved, ε locked, P1.001 done. Next: PA.002 (freq split + figure F2). LAUNCH-A still
  pending before the P1.003 sweep.
- Open uncertainties carried forward: small n per (bucket×seam_source×font) stratum in the tail.
