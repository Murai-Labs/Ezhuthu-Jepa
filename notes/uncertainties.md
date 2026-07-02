# Uncertainties (append-only)

Carry uncertainties forward each session until resolved.

## Entry format
### <YYYY-MM-DD> — <uncertainty>
- Why it matters: <...>.
- Status: <Open / Resolved YYYY-MM-DD — how>.

---

### 2026-07-01 — Corpus source for the bottom-quartile frequency cutoff
- Why it matters: metric M is defined on "bottom-quartile-frequency compounds"; the cutoff is
  undefined until a corpus provides compound counts. See RISKS Q005.
- Status: Open — resolve in TASK PA.002, cite the corpus, freeze the cutoff before P1.001.

### 2026-07-01 — RESOLVED: corpus = Project Madurai (references entry above)
- Resolution: Ramchand chose Project Madurai (DEC-0004). RISKS Q005 marked Resolved. Residual note:
  classical/literary skew vs manuscript-domain frequency is a known limitation to state in the paper;
  optional second-corpus robustness check tracked but not required for G1.

### 2026-07-01 — Ligature vowels (i/ii/u/uu) have no cleanly separable sign region
- Why it matters: for 60/216 aksharas the vowel fuses with the base into a single ligature glyph, so
  the seam ("diff") spans most of the glyph — "mask the sign, keep the base visible" is only clean for
  the 138 separate-glyph cases. This affects PA.004 masking design and how K1/K3 must be interpreted
  (does the compositional win hold on ligated vs separable signs?). Surfaced by PA.001 (DEC-0005).
- Status: Open — decide at PA.004 whether to (a) mask only the diff region, (b) stratify results by
  seam_source (glyph vs diff), or (c) treat ligature aksharas as a separate reported bucket. Likely
  report stratified by seam_source so the claim is honest about where composition is clean.

### 2026-07-01 — RESOLVED: stratify M by seam_source (references entry above)
- Resolution: Ramchand chose option (b) — report metric M stratified by seam_source (glyph vs diff),
  keeping all 216 (DEC-0006). Multi-font (Noto+Nirmala) also adopted, so ligation is reported per
  font (a vowel that ligates in one font may separate in another). Binds PA.003 (per-seam_source
  accuracy) and PA.004 (mask carries seam_source). Residual: smaller n per (bucket × seam_source ×
  font) stratum in the tail — watch CI width at PA.003/P1.001.

### 2026-07-01 — Rendered-glyph fidelity vs real paleographic forms
- Why it matters: seam labels are learned on renders; transfer to manuscript glyph shapes is the
  whole K4 question. See RISKS Q006.
- Status: Open — the small real-sample sanity eval (P2.002) is the check; v2 covers the full benchmark.

### 2026-07-01 — Provisional ε = 2.0 pp not yet formally pre-registered
- Why it matters: G1 is un-adjudicable without a pre-registered ε dated before baseline runs.
- Status: **Resolved 2026-07-01** — ε = 2.0 pp + non-overlapping 95 % CIs (n ≥ 3) pre-registered and
  approved by Ramchand before any baseline (DEC-0009; `notes/decision-gates/g1-cheap-baseline.md`).

### 2026-07-01 — Bottom-quartile CI width vs the 2pp ε (statistical power for G1)
- Why it matters: PA.003's baseline gives metric M (n=54) a 95 % CI of ~±0.12 (0.222–0.463). To
  adjudicate a 2 pp win with *non-overlapping* CIs on the bottom quartile, the CIs must be far tighter
  than that. With only 54 tail compounds and few instances per class, ε=2pp may be statistically
  unreachable unless PA.005 adds many augmented render instances per akshara (more eval n) and/or the
  JEPA encoder sharply reduces variance.
- Status: Open — quantify at PA.005/P1.003. If CIs stay ~±0.1 at the real encoder, either increase
  instances-per-akshara (augmentation) before the sweep or revisit the ε rule with Ramchand (would be
  a new pre-registration, dated before results). Flag now so it is not discovered mid-sweep.

### 2026-07-01 — Decision rule: paired McNemar may be far more powerful than non-overlapping CIs
- Why it matters: PA.005-prep research (subagent-log 19:40) indicates the pre-registered "non-overlapping
  95% CI" rule (DEC-0009) is low-power — it needs each arm's CI half-width < 1pp (~150-200 eval
  instances/class) to detect a 2pp effect. A **paired McNemar test on identical eval instances across
  arms** detects the same 2pp at ~3-5× smaller n because per-item outcomes are correlated. Our arms
  (seam/block/MAE) CAN be evaluated on identical eval instances, so paired testing is available.
- Status: OPEN — decision for Ramchand at PA.005. If we switch the adjudicator to McNemar, that is a
  CHANGE to the pre-registered ε rule and MUST be a new pre-registration dated before any sweep result
  (append to `notes/decision-gates/g1-cheap-baseline.md`, new DEC entry). Do not switch silently.
