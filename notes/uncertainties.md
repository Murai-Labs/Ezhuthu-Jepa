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

### 2026-07-01 — Rendered-glyph fidelity vs real paleographic forms
- Why it matters: seam labels are learned on renders; transfer to manuscript glyph shapes is the
  whole K4 question. See RISKS Q006.
- Status: Open — the small real-sample sanity eval (P2.002) is the check; v2 covers the full benchmark.

### 2026-07-01 — Provisional ε = 2.0 pp not yet formally pre-registered
- Why it matters: G1 is un-adjudicable without a pre-registered ε dated before baseline runs.
- Status: Open — DEC-0002 records it provisionally; TASK P1.001 formalizes it.
