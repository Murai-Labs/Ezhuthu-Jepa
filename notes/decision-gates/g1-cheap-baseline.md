# G1 Cheap-Baseline-Falsification — Gate Record (append-only)

This file is the append-only record for the G1 gate. The ε pre-registration below is fixed
**before any baseline runs** so the PASS/BLOCK decision cannot be rationalized after seeing results.
The PASS/BLOCK outcome (TASK P1.004) is appended later, referencing this section — never edited over it.

---

## ε PRE-REGISTRATION — 2026-07-01 (TASK P1.001)

Pre-registered by Ramchand on 2026-07-01, before any baseline (P1.002/P1.003) has run.

- **Metric M:** bottom-quartile-frequency akshara top-1 accuracy (linear-probe / light-finetune),
  reported stratified by `seam_source` (glyph vs diff) and by font (DEC-0006).
- **Equivalence margin ε = 2.0 percentage points** on M.
- **Binding decision rule (adjudicator):** seam-masked JEPA counts as beating a baseline only if it
  exceeds it on M by **> ε AND with non-overlapping 95 % bootstrap CIs across n ≥ 3 seeds**. A gap
  ≤ ε, or overlapping CIs, is **not** a win.
- **Bottom-quartile cutoff definition:** the lowest 25 % of the 216 uyirmei by **Project Madurai**
  corpus frequency (DEC-0004). The specific compound membership is computed deterministically at
  TASK PA.002; that computation does **not** reopen ε (the margin/rule above are fixed now).
- **Seeds:** n ≥ 3.
- **Justification:** at single-5090 probe scale, sub-2pp differences on M are within typical seed
  variance, so the non-overlapping-CI test is the real adjudicator; ε guards against calling a
  statistically-detectable-but-trivial gap a mechanism win. Consistent with the spec's "non-overlapping
  CIs on the long tail" bar (spec §3 K1).

**Null hypothesis this gate must defeat:** seam-masked JEPA (latent) vs {block-masking JEPA,
MAE-at-seam} on M. If either baseline is within ε of seam-JEPA (per the rule above), the mechanism
claim is falsified → re-scope (MAE-at-seam captures it → "seam, not target"; block matches → seam
prior unearned). Premise gate (K2): if the base→sign probe cannot beat chance clearly, terminate.

Supersedes the *provisional* ε in DEC-0002; formalized in DEC-0009.

<!-- P1.004 PASS/BLOCK decision is appended below after the P1.003 sweep completes. Do not edit above. -->
