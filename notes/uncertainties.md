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
- Status: Open — DEC-0002 records it provisionally; TASK P1.001 formalizes it.
