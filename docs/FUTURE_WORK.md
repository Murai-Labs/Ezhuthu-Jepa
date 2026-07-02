# Future Work — Two Parallel Tracks for Tamil Recognition + JEPA

**Status: planning (not started). Written 2026-07-02, after the Ezhuthu-JEPA thesis concluded (G1 = BLOCK,
`docs/REPORT.md`).** This doc scopes the next directions so a future session can pick up cold. Both tracks
inherit the Murai-Labs Phase-0 discipline: **each defines its cheap baselines up front, and neither
advances past Phase 0 until those baselines are run on the metric and fail to explain the effect** (the
rule that killed the last thesis for ~2 GPU-h instead of months).

## Why these two tracks

What the concluded project actually taught us (hard data, not speculation):

1. **MAE (pixel target) beat latent JEPA decisively** at evenings-scale (M = 0.532 vs 0.290). For
   *recognition performance*, don't marry JEPA; for *learning JEPA*, our regime (ViT-Tiny, linear-probe
   eval, small rendered data) was structurally unfavorable — a fixable mismatch, not a verdict.
2. **Block masking ≥ seam masking** (0.335 vs 0.290) — the "seam boundary is special" bet did not help
   recognition; the base-ink compositional signal is real but thin (~8 pp, ligatures only), geometry-dominated.
3. **But base→sign is genuinely learnable** (K2: 0.509; location-normalised base-ink: 0.331 ≫ 0.091 chance).
   That is the strongest *positive* signal we produced — and it points at a **supervised compositional
   decoder**, not SSL. → **Track T1.**
4. **Rendered glyphs ≠ the real problem.** Where SSL/JEPA would earn its keep is **unlabeled manuscript /
   historical page images** (label-scarce, image-rich), which we never touched. → **Track T2 + J1.**

T1 is the high-probability "ships something useful" track; T2+J1 is the high-variance "does JEPA earn its
keep, done right" track. They **share** the benchmark, eval harness, and rendering pipeline, so running
both in parallel is cheap.

## Shared, build-once assets (reused from this repo)

- Frequency-stratified akshara benchmark + augmented **font-holdout** split (`runs/pa002-split-001`,
  `runs/pa4b-augment-001`; metric-M CI ≈ 1 pp).
- Encoder-agnostic eval harness — metric M, bootstrap CIs, `seam_source`/font stratification, paired
  **McNemar** comparator (`src/ezhuthu_jepa/eval/`).
- Multi-font Tamil rendering + grapheme-seam labelling (`src/ezhuthu_jepa/data/`).
- Switchable seam/block/MAE pretraining loop with EMA target, cosine LR, resume-state, and a sweep
  orchestrator with a launch gate (`src/ezhuthu_jepa/train/`).
- Provenance/config contract (`src/ezhuthu_jepa/provenance.py`, `config.py`).

**New shared asset to build first (~half a day): the unseen-compound split.** Compounds whose base *and*
sign were each seen (in other combinations) but whose *combination* never appears in training. This is the
actual test of compositionality; both tracks report on it.

---

## Track T1 — Supervised compositional `(base, sign)` decoder

**Pitch:** Recognize each akshara as a *structured* `(base, sign)` prediction instead of one of ~216 flat
classes, so the model composes rare and **unseen** compounds from parts it has seen — the original dream,
via the mechanism K2 already proved learnable.

**Metric:** metric M (bottom-quartile-frequency top-1) **+ accuracy on the new unseen-compound split**.

**Phase-0 cheap baselines (run + fail before scaling):**
- **Flat N-way classifier**, same backbone/compute. If it matches the compositional decoder on
  bottom-quartile *seen* compounds within ε, composition is not earning its keep.
- **Two independent heads** (base-head + sign-head, no joint modeling). If this matches a joint/structured
  decoder, the "composition" is just two classifiers.
- **Kill-or-live test:** on the *unseen-compound* split the flat classifier structurally cannot score
  (no output for unseen classes) → the compositional decoder must beat chance there decisively. If not,
  the premise is dead — cheaply.

**Null hypothesis:** compositional decoder beats {flat, two-independent-heads} on bottom-quartile seen M by
> ε **and** beats chance on unseen compounds. If the cheap baselines match it → re-scope or conclude.

**2-week pilot:** train flat, two-head, and joint-structured decoders on the existing rendered+augmented
data; evaluate all three on seen-M and the unseen-compound split. Evenings-scale, no JEPA. Low risk.

**Risk note:** on *seen* classes with enough data, a flat classifier is already strong — so the win must
come from the *unseen/rare* split. If composition doesn't beat chance on unseen compounds, T1 concludes.

---

## Track T2 + J1 — Self-supervised (JEPA vs MAE), done right

**Pitch:** Pretrain a vision encoder on **unlabeled** Tamil page images, then few-shot fine-tune for
recognition — the regime where SSL is motivated — and settle whether JEPA's latent target beats MAE's
pixel target when evaluated by *fine-tuning at adequate scale* (the three conditions stacked against JEPA
last time: linear-probe eval, ViT-Tiny, rendered-only).

**Metric:** few-shot fine-tuned metric M vs label budget (e.g. 1 / 5 / 20 labels per class).

**Phase-0 cheap baselines (run + fail before scaling):**
- **Supervised-from-scratch** at each label budget — SSL must beat "no pretraining," or pretraining is
  pointless.
- **Generic transfer** (ImageNet-pretrained ViT, fine-tuned) — Tamil-specific SSL must beat borrowing a
  generic encoder.
- **MAE** — the SSL baseline JEPA must beat to justify the latent target (the J1 question as a cheap gate).
- **Eval-protocol control (cheapest experiment in the whole plan):** linear-probe vs fine-tune on our
  *committed* pilot checkpoints (`runs/phase1-pilot*`). A few hours; tells us immediately whether "JEPA
  lost" was partly a linear-probe artifact. **This gates the rest of T2.**

**Null hypothesis:** best SSL beats {scratch, ImageNet-transfer} on few-shot M by > ε; and separately,
JEPA beats MAE under fine-tuning. If SSL ≤ scratch+transfer → SSL-for-Tamil is dead. If JEPA ≤ MAE → the
honest finding is "SSL yes, latent target no."

**2-week pilot:** (1) the eval-protocol control on existing checkpoints [day 1 — decides everything];
if it moves the ranking → (2) assemble an unlabeled Tamil page-image corpus, pretrain JEPA + MAE, few-shot
fine-tune vs the baselines. Scale up only if signal warrants.

**Recipe fixes carried over (from DEC-0018):** cosine LR (done), and for a fair JEPA attempt — multi-block
I-JEPA masking, larger model (ViT-Small/Base), anti-collapse care, and **fine-tuning** eval rather than a
frozen linear probe. Probe the EMA **target** encoder, not the context encoder.

**Candidate unlabeled data sources (images, not text):** Internet Archive scanned Tamil books (print);
IFP Pondicherry / Roja Muthiah Research Library / archive.org (palm-leaf). Verify licensing before use;
keep the repo text-free (images gitignored, manifests committed).

---

## Running them in parallel

- **Git worktrees** (lab Principle 1): `../ezhuthu-t1-compositional` and `../ezhuthu-t2-ssl`, each its own
  branch + session, both importing the shared `ezhuthu_jepa` package from a common base.
- **Sequencing that de-risks cheaply:** both Phase-0 kill-gate pilots are ~1–2 days and both are kill-or-
  live — run them **first, in parallel**:
  - T1: flat vs two-head vs joint-structured on seen-M + unseen-compound split.
  - T2: probe-vs-fine-tune on the existing pilot checkpoints.
  Only scaffold a full research repo (STATUS/CHECKPOINT/DEC/gate files, via `research-project-init`) for a
  track **after** its Phase-0 gate passes.
- **ε / adjudicator:** reuse the established convention — ε = 2.0 pp on M, paired McNemar (primary) +
  non-overlapping 95 % bootstrap CIs across n ≥ 3 seeds (secondary). Pre-register per track before results.

## Recommended first move

1. Build the shared **unseen-compound split** (~half a day).
2. Kick off the two Phase-0 kill-gate pilots in parallel worktrees.
3. Read both results, then decide which track(s) graduate to a full scaffold.

## Pointers

- Prior thesis + negative result: `docs/REPORT.md`, `README.md`.
- Decisions incl. the recipe lessons: `docs/DECISION_LOG.md` (DEC-0016…DEC-0019).
- Reproduction commands: `docs/RUNBOOK.md`. Operating contract: `AGENTS.md` ≡ `CLAUDE.md`.
