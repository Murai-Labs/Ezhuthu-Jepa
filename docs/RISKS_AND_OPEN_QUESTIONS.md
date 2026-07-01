# Ezhuthu-Jepa — Risks and Open Questions

## Format

### Q<NNN> - <Title>

**Status:** <Open / Resolved YYYY-MM-DD>
**Blocking Impact:** <Low / Medium / High>
**Needed For:** <what cannot proceed until this is resolved>
**Resolution Path:** <how to resolve it>

---

### Q001 - Cheap baselines have not yet been run

**Status:** Open
**Blocking Impact:** High
**Needed For:** G1 approval; everything past Phase 1.
**Resolution Path:** Execute block-masking JEPA and MAE-at-seam on metric M, plus the base→sign
premise probe (K2), and record results against the pre-registered ε (TASKS P1.002–P1.004).

---

### Q002 - Does the base region actually predict the vowel sign? (K2 premise)

**Status:** Open
**Blocking Impact:** High
**Needed For:** Justifying the whole seam prior; kill-before-scale check.
**Resolution Path:** TASK P1.002 supervised probe. If it cannot beat majority-class clearly, the
seam carries no exploitable structure and the mechanism is unmotivated → terminate/re-scope.

---

### Q003 - Is the win the seam boundary or the latent target? (K3 confound)

**Status:** Open
**Blocking Impact:** Medium
**Needed For:** The headline claim's precision.
**Resolution Path:** MAE-at-seam arm in the P1.003 sweep. If MAE-at-seam captures the full win,
honestly reframe the paper as "seam, not target" (a valid result, per AGENTS.md §2.5).

---

### Q004 - Does the rendered-core result transfer to real degraded manuscripts? (K4)

**Status:** Open
**Blocking Impact:** Medium (narrows scope, does not kill)
**Needed For:** Earning the manuscript-recovery framing vs the clean-script-only paper.
**Resolution Path:** Phase 2 degradation suite (P2.001) + realism validation against a small real
sample (P2.002) + K4 run (P2.003). If it vanishes under missing-puḷḷi, the paper narrows honestly.

---

### Q005 - Corpus frequency source for the bottom-quartile cutoff

**Status:** Open
**Blocking Impact:** Medium
**Needed For:** Defining metric M precisely (which compounds are "long tail").
**Resolution Path:** TASK PA.002 — pick and cite a Tamil corpus for compound counts; freeze the
bottom-quartile cutoff as a recorded number before ε pre-registration (P1.001).

---

### Q006 - Rendering fidelity vs real paleographic glyph shapes

**Status:** Open
**Blocking Impact:** Low (for v1 rendered-core), Medium (for transfer)
**Needed For:** Confidence that seam labels learned on renders map to manuscript glyph forms.
**Resolution Path:** Track as an uncertainty; the real-sample sanity eval (P2.002) is the check.
Full labeled real benchmark is explicitly v2 of this same paper (spec §7, locked).
