# EZHUTHU-JEPA: Grapheme-Compositional Self-Supervision for Recovering Undigitized Tamil Manuscripts

**Pre-registered specification, v0.2** · Murai Labs · Ramchand Kumaresan

*Reframed from v0.1: the masking prior is unchanged; the paper is now a Tamil textual-recovery contribution that uses the prior, not a masking-prior paper that uses Tamil.*

---

## 0. The contribution, stated for a Project Madurai volunteer

There are **>100,000 unpublished Tamil palm-leaf manuscripts** on medicine, literature, astronomy, Siddha, and temple history. Institutions (Tamil University, EAP/British Library, Tamil Heritage Foundation, Sri Lankan collections) have imaged hundreds of thousands of pages. But turning an *image* into searchable *Unicode Tamil* is still largely **manual key-in and proof-reading** — which is why Project Madurai, after 25+ years, has released works in the low hundreds. The bottleneck is not scanning; it is transcription.

Existing Tamil manuscript OCR fails exactly where the manual labor concentrates, for two structural reasons this paper attacks directly:

1. **The long-tail compound problem.** Tamil has 247 letters — 12 vowels, 18 consonants, 216 vowel-consonant *compounds*. Standard OCR treats each compound as an atomic shape to segment and classify. The rare compounds are starved of training examples, so accuracy collapses on precisely the characters a transcriber must slow down for.
2. **The missing-puḷḷi ambiguity.** In most manuscripts the consonant dot (puḷḷi) is not written, so a bare consonant and its compound look identical; the reading is recovered from the **vowel-sign region adjacent to the base**, plus context. The disambiguating signal lives at the base/sign seam — and that seam is often degraded.

**Our contribution:** a self-supervised model whose pretraining objective *is* the act of reading these manuscripts — predict the latent representation of the vowel-sign region from the consonant-base context. This yields a recognizer that (a) composes rare/unseen compounds from seen parts instead of memorizing 216 atomic shapes, and (b) is built around the exact base/sign inference paleographers perform. The deliverable is a transcription aid that degrades **gracefully on the long tail**, which is where human transcription time is actually spent.

---

## 1. The mechanism (unchanged from v0.1, now motivated by the domain)

Mask at the **grapheme-cluster seam**: hide the dependent vowel-sign region, keep the consonant base visible, predict the masked region's *latent* (JEPA), not its pixels (MAE). The model must internalize the script's generative rule (base × sign → akshara) to succeed.

In v0.1 this was an elegant prior. In v0.2 it is the **computational form of how Tamil manuscripts are deciphered** — the missing-puḷḷi fact above makes base→sign prediction the literal reading operation, not an analogy.

---

## 2. Why grapheme-compositional beats whole-akshara (the Tamil-specific claim)

A whole-akshara classifier learns 216 compound classes independently; the rare ones never get enough examples. A base+sign compositional model learns 18 bases × 12 signs and *composes* — so a compound seen rarely (or never) in training is still recognizable from its parts. This is the standard compositional-generalization argument, but Tamil's abugida structure makes it **exact rather than approximate**: every compound genuinely *is* base+sign, with no irregular forms to break the composition. This is the core scientific claim and it is Tamil-load-bearing — it would not even be well-defined for an alphabetic script.

---

## 3. Pre-registered kill criteria

**K1 — Primary: grapheme-seam JEPA vs. block-masking JEPA, evaluated on long-tail compounds.**
Hold architecture/compute/mask-ratio fixed; vary only the mask boundary. Win condition is stricter and more meaningful than v0.1: the seam prior must beat block masking **specifically on low-frequency compounds** (pre-register a frequency cutoff, e.g. bottom-quartile compounds by corpus count), n ≥ 3 seeds, non-overlapping CIs. A win only on common characters does **not** count — the long tail is the contribution. **The paper lives or dies here.**

**K2 — Premise check: does base predict sign?**
A supervised probe predicting vowel-sign class from the consonant-base region must beat chance clearly. If the seam carries no exploitable structure, the prior is unmotivated — kill before scaling. (This also directly tests the missing-puḷḷi reading hypothesis.)

**K3 — Ablation: JEPA vs. MAE at the same seam.**
Isolates whether the win is the *boundary* (expected) or confounded with the *latent target*. Honest pre-registered outcome: if MAE-at-seam captures the full win, reframe as "seam, not target."

**K4 — Manuscript-realism gate (new in v0.2): does the win survive degradation?**
Re-run K1 with manuscript-like corruption (missing puḷḷi, ink bleed, leaf discoloration, touching characters — simulated on rendered data, validated against a small real manuscript sample). If the compositional advantage vanishes under realistic degradation, the Tamil-recovery claim is not yet earned and the paper is the clean-script version only (honest, narrower). If it survives — especially the missing-puḷḷi condition — that is the headline result for the manuscript community.

---

## 4. Minimal experiment (finishable on RTX 5090)

**Stage A — rendered clean script (free exact labels).** Render Tamil with full Unicode grapheme decomposition; seam labels are free and exact. Establishes K1–K3 with total control. This is the finishable core.

**Stage B — degradation suite (K4).** Programmatic manuscript-style corruptions on rendered data: drop puḷḷi, add bleed/discoloration/noise, induce touching characters. Validate the corruption realism against a *small* real manuscript sample (EAP / Tamil University / U.V. Swaminatha Iyer Library imagery is the target source — handful of pages for validation, not a training dependency).

**Backbone.** Small I-JEPA-style ViT, single-5090 evenings-scale pretraining. No H100/Lambda for the core claim.

**Eval.** Linear-probe / light-finetune akshara recognition, reported **stratified by compound frequency** (this stratification is the whole point — aggregate accuracy hides the long-tail story).

**Compute ledger (MARMAM-style).** Pre-commit GPU-hours for K1–K4 vs. a full-foundation-model build. Cheap gate, decisive answer, no sprawl.

---

## 5. What this gives the Tamil community (concrete, not aspirational)

- **A transcription aid, not a finished OCR.** Realistic framing: the model proposes base+sign readings, a human confirms — cutting the per-page manual cost that throttles Project Madurai.
- **Graceful long-tail behavior**, so the hard characters (rare compounds, missing puḷḷi) get *more* help, not less — inverting the usual OCR failure mode.
- **An open pretraining recipe** other Brahmic scripts (Grantha, which co-occurs in these very manuscripts; Devanagari; Kannada; Telugu; Sinhala) can reuse — the seam exists in all of them. Grantha is especially apt: it appears alongside Tamil in the Sri Lankan and Tamil-University collections, so a compositional recognizer that handles both is directly useful to existing digitization projects.
- **A dataset/benchmark contribution**: a frequency-stratified akshara-recognition benchmark with a degradation suite, which the current literature (whole-akshara, aggregate-accuracy) lacks.

---

## 6. Positioning against the literature

- **Tamil palm-leaf OCR line** (npj Heritage Science 2024; the segmentation/CNN papers): all whole-akshara, segmentation-first, aggregate-accuracy. Your axis of novelty: compositional base+sign recognition + frequency-stratified eval + the seam-aware SSL prior. You are not competing on their metric; you are changing the unit of recognition.
- **Linguistics-aware MIM for Scene Text (CVPR 2025):** inter-glyph, Latin-centric, pixel-target. Yours is intra-glyph, abugida, latent-target. Cite head-on (as in v0.1).
- **Structure-aware masking genre** (SemMAE, audio curriculum masking): proven that domain-structure masking beats geometric — de-risks the premise. You are first to the abugida seam.

---

## 8. Data availability — VERIFIED (the question that gated the whole idea)

The idea was nearly killed on the assumption that no untranscribed Tamil manuscript corpus exists. Research result: **the corpus exists at scale, and the existing annotated data is on the wrong (already-transcribed) texts** — which is exactly the gap this work fills.

- **Tamil Nadu Govt. Oriental Manuscripts Library:** 72,748 manuscript bundles total; only ~2,400 digitized and online as 600 dpi TIFF/PDF. The 2,400 are *images, not transcriptions*. The ~70,000 undigitized + the untranscribed digitized 2,400 are the backlog. (tnarch.gov.in)
- **EAP / British Library Tamil projects:** large imaged corpora — Sri Lankan Tamil (EAP1056/1260/1551): 200,000+ pages, 1,000+ manuscripts, ~two-thirds Tamil-script; Tamil University (EAP1217): 3,000 of 4,500 bundles; private Tamil-country collections (EAP1294). All open-access imagery (note: BL catalogue partially down since the Oct 2023 cyber-attack).
- **Existing annotated datasets are tiny and on canonical texts:** THPLMD (2024) = ~262 samples from Naladiyar / Tholkappiyam / Thirikadugam — i.e. the most-transcribed classics, captured at U.V. Swaminatha Iyer Library. Annotation effort is going to the texts that *least* need recovery.
- **Neighboring script has the benchmark Tamil lacks:** HKHPL (Historical Kannada) ships binarised + word-annotated + isolated-character-annotated ground truth with code. No Tamil equivalent at that completeness — a ready-made template and a clear gap.

**Conclusion:** digitized-but-untranscribed Tamil imagery exists at 5–6 figure page scale; the need (medical, astrological, land-record, regional manuscripts) is real and unmet; the annotated data that exists is on the wrong texts. The data does *not* kill the idea — it motivates it. The real risk was never data existence; it is whether v1 can use rendered-core to earn a claim that transfers to this imagery (that is what K4 tests).

## 9. Novelty after full literature check — NARROWED but intact

What is **NOT** novel (do not claim; will draw old citations):
- Compositional / component-based Indic recognition. Devanagari recognition-driven segmentation into vowel/consonant/conjunct primitives dates to ~2009 (Kompalli et al.) and recurs across Devanagari/Bangla/Telugu.
- Decompose-classify-recombine akshara pipelines in general.

The intellectual sibling to position against head-on:
- **CoLa (Shi et al., June 2025, arXiv:2506.03798):** learns *latent* compositional components of Chinese characters with no human-defined scheme, recognizes by comparing latent components, achieves **zero-shot** recognition of unseen characters, explicitly to solve the **long-tail** problem. This proves your core thesis (learned latent compositionality → long-tail/zero-shot win) — but for Chinese, with irregular radical composition, and **not** via a self-supervised masking prior.

What **IS** novel (the defensible intersection — none novel alone):
1. **Seam-masked JEPA**: a self-supervised prior that masks specifically at the grapheme base/sign boundary and predicts in latent space. (CoLa is a latent-variable model, not seam-masked SSL; scene-text linguistics-aware MIM is inter-glyph + pixel-target.)
2. **Abugida regularity**: Tamil base+sign composition is *exact and regular*, unlike Chinese radicals — so compositional generalization is clean, and the abugida is the ideal testbed for the CoLa-style thesis.
3. **Manuscript-degradation + zero-shot eval where the need is**: missing-puḷḷi disambiguation and long-tail compounds on real backlog imagery, not canonical classics.

**Honest novelty statement for the paper:** "We bring the learned-latent-compositionality thesis (demonstrated for Chinese by CoLa) to abugida script via a grapheme-seam-masked JEPA, where regular base+sign composition makes the inductive bias exact, and we evaluate it on the long-tail, missing-puḷḷi regime that actually gates Tamil manuscript transcription." That sentence survives the old Indic-OCR literature and the CoLa comparison.

## 7. Locked decisions

1. **Real-manuscript scope — LOCKED.** Paper 1 (v1): rendered-core + small-real-*validation* (real manuscript imagery used only to validate corruption realism and as a held-out sanity eval, not for training). Full labeled real-manuscript benchmark is **v2 of this same paper**, not a separate successor — i.e. the arXiv submission is expected to be revised to v2 with the real benchmark once it exists, keeping it one continuous artifact rather than spawning a new paper.
2. **Script scope — LOCKED.** Tamil only for K1–K4. Grantha named as the explicit replication target (justified by its co-occurrence in the same Sri Lankan / Tamil University collections), not run in v1.
3. **Deliverable — LOCKED.** Paper + usable transcription-aid demo (Gradio). Demo is a first-class deliverable, not a fast-follow: it is what makes the work reach Project-Madurai-type volunteers regardless of how the metrics land. Open pretraining recipe released alongside.
4. **Venue — DEFERRED, deliberately.** Prior expectation (consistent with the author's track record): this paper, like the others, likely under-delivers against the author's own bar and ends as an arXiv-only artifact. Venue choice is therefore premature and not worth optimizing now. Build the result first; let the result decide whether a venue conversation is even warranted. The rendered-core + demo + honest-negative structure is fully self-justifying as an arXiv contribution.
