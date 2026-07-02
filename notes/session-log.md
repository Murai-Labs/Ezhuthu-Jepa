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

### 2026-07-01 18:30 CT — PA.002 frequency split + Figure F2
- Started from: PA.002 (blocked ~an hour by the Bash safety classifier being unavailable; wrote all
  code meanwhile, resumed when it recovered).
- Did: added `data/frequency.py` (uyirmei counter), `data/frequency_split.py` (quartile buckets +
  leak-free seeded train/eval split), `data/fetch_project_madurai.py` (reproducible corpus fetcher),
  `configs/phase1/split.yaml`, `tests/test_split.py` (11), `figures/f2_frequency_distribution.py`.
  Fetched 172 Project Madurai works (~40MB, gitignored), counted 4,851,420 uyirmei (207/216 seen),
  froze bottom quartile (54) → `runs/pa002-split-001/split-manifest.json` + provenance (seed 42).
  Generated F2. 69 tests pass. DEC-0010.
- Ended at: PA.002 done. Next: PA.003 eval harness (metric M per bucket×seam_source×font) + F3.
- Open uncertainties carried forward: small-n strata; PA.003 will show CI widths on the tail.

### 2026-07-01 19:15 CT — PA.003 eval harness (metric M) + Figure F3
- Started from: PA.003.
- Did: added `eval/akshara_probe.py` (encoder-agnostic ridge linear probe, bootstrap CIs, stratified
  by bucket × seam_source × font; metric_M named field), `configs/phase1/probe.yaml`,
  `tests/test_probe.py` (6), `figures/f3_probe_accuracy.py`. Fixed a reproducibility bug (used
  randomized `hash()` for per-stratum bootstrap seed → switched to stable crc32). Ran on the real
  PA.002 split: baseline PixelEncoder metric_M = 0.333 [0.222,0.463], clear freq gradient (q4=0.648).
  Generated F3. 75 tests pass. DEC-0011.
- Ended at: PA.003 done; metric M machinery frozen before the sweep. Next: PA.004 (masking) → PA.005
  (JEPA pretrain, introduces torch). LAUNCH-A still gates the full sweep.
- Open uncertainties: bottom-quartile CI width (±0.12) is wide at n=54 with the weak baseline — watch
  whether the JEPA encoder + augmented instances (PA.005) tighten it enough to adjudicate ε=2pp.

### 2026-07-01 19:45 CT — PA.004 seam masking + PA.005 research (parallel agents)
- Started from: PA.004; launched 2 background research agents (I-JEPA recipe; augmentation/CI) per
  Ramchand's "use parallel agents" directive, built masking in main context meanwhile.
- Did: added `masking/seam.py` (seam mask + matched block K1 control, carries seam_source) +
  `tests/test_seam_mask.py` (10). 85 tests pass. DEC-0012. Both agents returned (subagent-log 19:40):
  I-JEPA ViT-Tiny/8 recipe; augmentation stats flagged that paired McNemar >> non-overlapping CI for
  power (raises a re-pre-registration question) and that augmentation must transform seam_bbox.
- Ended at: PA.004 done; PA.005 PAUSED for decisions (ViT size, augmentation, decision rule).
- Open uncertainties: McNemar-vs-CI decision rule (see uncertainties 2026-07-01); seam_bbox under augmentation.

### 2026-07-01 20:15 CT — PA.005 decisions + augmentation core (PA.4b.1)
- Started from: 3 PA.005 decisions from Ramchand — ViT-Tiny/8 auto-escalate; full augmentation +
  held-out-font eval; decision rule = paired McNemar primary + CI secondary.
- Did: **amended the ε pre-registration** (g1-cheap-baseline.md, dated before any sweep result:
  McNemar α=0.05 Bonferroni primary + ε=2pp min effect + CI secondary); DEC-0013. Added task-plan
  entries PA.4b.1/PA.4b.2/P1.001b. Built `data/augment.py` (deterministic affine+stroke+blur+noise
  with **seam_bbox transformed in lockstep**) + `tests/test_augment.py` (6, incl. >95%-ink-in-bbox
  across seeds). 91 tests pass.
- Ended at: augmentation core done. Next: PA.4b.2 (augmented dataset + font-holdout split) → P1.001b
  (McNemar comparator) → PA.005 (torch pretrain).
- Open uncertainties: verify I-JEPA recipe vs paper at PA.005; confirm CI actually shrinks post-augment.

### 2026-07-01 20:45 CT — PA.4b.2 augmented font-holdout dataset
- Started from: PA.4b.2. (Ramchand: torch already installed on system; no install checkpoint needed.)
- Did: `data/build_augmented.py` + `configs/phase1/augment.yaml` + build integration test. Generated
  54,000 instances (21.6k train noto / 32.4k eval nirmala HELD OUT), aug_index 0 = clean, seed-frozen
  eval. Committed compact split-manifest (recipe+summary+provenance); gitignored 54k images + index.jsonl
  (regenerable). Analytical check: bottom-quartile eval n≈8,100 → CI half-width ~1pp (was ~12pp). 92 tests pass.
- Ended at: PA.4b.2 done. Next: P1.001b (McNemar + probe on augmented index; confirm CI empirically).
- Open uncertainties: empirical CI on augmented eval (confirm ~1pp at P1.001b); held-out-font accuracy may
  be low for the pixel baseline (cross-font is hard) — the JEPA encoder is expected to close that at PA.005.

### 2026-07-02 CT — P1.001b (McNemar comparator) + PA.005 (I-JEPA pretraining loop)
- Started from: post-Windows-restart integrity check — working tree clean, HEAD 2ac86eb matches trackers,
  92 tests pass, gitignored data (font, 4 run dirs, 54k augmented images) intact. No work lost. Resumed at
  P1.001b + PA.005 (user: "proceed with 1 and 2").
- Did (P1.001b): added `mcnemar` (exact binomial <25 discordants else χ²+continuity) + `compare_arms`
  (Bonferroni primary + non-overlapping-CI secondary, ε=2pp) to `akshara_probe.py`; added an `index`
  backend (reads the PA.4b.2 `index.jsonl`) + `predictions.jsonl` output + load progress logging. Re-ran on
  the augmented index → `runs/pa003b-probe-aug-001`: PixelEncoder metric_M 0.359 [0.349,0.369], **CI
  half-width 1.02pp** — empirically confirms DEC-0013's ~1pp (uncertainty above resolved).
- Did (PA.005): `train/pretrain.py` — from-scratch ViT-Tiny/8 (torch.nn; no timm), context/EMA-target/
  predictor; objective {seam_jepa, block_jepa, mae_seam} by config only; fixed n_mask=36/144 identical
  across arms (AC2); no-sign forms excluded; ≤10-step progress logging; provenance + metrics + encoder.pt.
  GPU smokes `phaseA-smoke-001/-002/-003` (5.35M enc, 2.5–3.5k img/s, 1.7–1.9GB). JEPA encoder wired into
  the probe (`encoder: jepa`). torch 2.10.0+cu130 pinned. Recorded DEC-0014; schema audit + EXPERIMENT_LOG
  + RUNBOOK updated. Full suite **107 pass**; compileall + placeholder scan clean.
- Ended at: PA.001–PA.005 + P1.001b done. Next: PA.006 compute ledger → resume-state → LAUNCH-A → P1.003.
- Open uncertainties: verify the I-JEPA recipe (EMA schedule, predictor depth, mask scale) vs the paper
  before the full sweep; smokes are 30 steps and prove nothing about K1/K3; resume-state not yet built.

### 2026-07-02 CT — Resume-state for the pretraining loop (AGENTS.md §4)
- Started from: post-PA.005 (user: "Resume state first - clean dirty tree. Then do PA.006").
- Did: added `checkpoint_every` + `resume-state.pt` to `train/pretrain.py`. Every N steps the loop
  atomically (tmp+rename) saves weights, optimizer, EMA target, and NumPy+torch RNG states. `--resume`
  loads it, **validates config-hash + seed** (`ResumeError` on mismatch), restores everything, and
  continues from the saved step. Provenance is now written **before** the loop (precondition, §2.4) and
  is not rewritten on resume. Verified: interrupted@3 → resumed run reaches **identical** final weights
  (CPU allclose test) and identical final_loss on a GPU end-to-end run (scratch dir, not committed).
  3 new tests (10 pretrain total; 110 full suite). placeholder + torch_dtype scans clean (reworded two
  policy comments so the grep gate stays clean — no actual `torch_dtype=` usage ever existed).
- Ended at: resume-state done; tree clean after commit. Next: PA.006 compute-hour ledger.
- Open uncertainties: GPU bf16 resume was bit-identical here but that is not guaranteed across all ops;
  the §4 guarantee we rely on is "resumable + config/seed-validated", not "bit-exact on GPU".

### 2026-07-02 CT — PA.006 compute-hour ledger
- Started from: resume-state done → PA.006 (user: "Then do PA.006").
- Did: wrote `docs/decisions/compute-ledger.md` (DEC-0015). Grounded unit costs in the measured PA.005
  smokes (seam 50 ms/step, block 43, mae 37 at batch 128; 169 steps/epoch; probe eval ~4 min load-bound).
  Planned full run = 50,000 steps (~296 epochs, pilot-confirmed at LAUNCH-A). Line items smoke+K2+pilot+
  sweep(9 runs, ~5.7h)+evals+K4, ×1.3 buffer → **~15 GPU-h** program on one 5090. **Hard ceiling = 40
  RTX-5090 GPU-h cumulative** → halt for Ramchand's approval; escalation is re-scope, not a bigger GPU
  (H100/Lambda exclusion stands). Contrast: full-foundation build is 10²–10³× and out of scope. Marked
  PA.006 done; LAUNCH-A preconditions now all met (harness frozen, ε pre-reg, smoke, resume, ledger).
- Ended at: PA.001–PA.006 + P1.001b + resume-state done. Next: LAUNCH-A (needs a longer 1-seed pilot +
  human sign-off) and P1.002 (K2 premise probe, parallelizable). No full sweep until LAUNCH-A.
- Open uncertainties: the 50k-step budget is provisional — the pilot must show convergence or the ledger
  and sweep config revise upward (which also re-checks the 40 GPU-h ceiling headroom).

### 2026-07-02 CT — P1.002 K2 premise probe (base→sign) — PASS with an honest caveat
- Started from: PA.006 done → P1.002 (user: "start P1.002").
- Did: `eval/base_to_sign_probe.py` + `configs/phase1/k2_probe.yaml` + `tests/test_base_to_sign.py` (4).
  Predicts vowel-SIGN from the consonant-BASE region (sign masked) on the augmented font-holdout index,
  inherent-'a' excluded. Built a sign-LOCATION-only control and glyph/diff stratification from the start
  (senior-review instinct). Run `phase1-k2probe-001`: base 0.509 [0.503,0.515] ≫ chance/majority 0.091
  (~5.6×) → **K2 kill-gate PASSES**. BUT the location control (0.623) beats the base probe in EVERY
  stratum (glyph 0.695>0.604; diff 0.457>0.291) → the signal is sign LOCATION, not base-ink composition,
  weakest exactly in the ligature stratum. Fixed my initial over-strong verdict (base>geometry) to the
  contract's kill-gate criterion (beats chance) — location is fair game for JEPA (it knows masked
  positions). Recorded DEC-0016 + `notes/negative-results/k2-base-ink-signal-is-location-not-composition.md`.
  114 tests pass; placeholder + torch_dtype scans clean.
- Ended at: P1.002 done, gate PASSES. Next: LAUNCH-A packet (surface the K2 caveat) → P1.003 sweep.
- Open uncertainties: **live K1 risk** — if the exploitable structure is largely location, block-JEPA
  (position-aware) may match seam-JEPA on M; a learned encoder might still extract base-ink composition a
  pixel probe cannot. K1/K3 adjudicate. Weigh this heavily before spending the sweep budget.

### 2026-07-02 CT — P1.002b location-normalised base-ink probe (sharpens the K2 caveat)
- Started from: K2 done (user: "So lets do b" — prototype the location-normalised base-ink probe).
- Did: `eval/base_ink_probe.py` + config + `tests/test_base_ink.py` (3). Mask sign → crop to base ink →
  letterbox centred (removes absolute location + scale) → predict sign, with a consonant-prediction
  positive control. Two synthetic-test bugs found + fixed (both mine, not the probe): a 3×chance control
  threshold impossible at 3 classes → 2×chance; and a test template that encoded the consonant by row
  POSITION, which the normaliser correctly strips → re-encoded class by shape inside a fixed frame.
- Result (run `phase1-baseink-001`): base-ink→sign 0.331 [0.326,0.336] ≫ chance 0.091 — a REAL base-ink
  compositional signal survives location removal (partially reverses the K2 "it's all location" read).
  Consonant control 0.381 (chance 0.056) → normalisation preserved ink. glyph 0.306 vs diff 0.388
  (non-overlapping CIs): the ~8.2pp gap is genuine ligature-reshaping composition over a residual geometry
  floor. Balanced read: mechanism not empty, but geometry still dominates → K1 risk real, softened, not a
  green light. Recorded in negative-results (Update), EXPERIMENT_LOG, schema audit, task P1.002b, STATUS.
  117 tests pass; scans clean.
- Ended at: exploratory analysis done. Next: LAUNCH-A packet (fold in the balanced K1-risk read) → P1.003.
- Open uncertainties: does a learned seam-JEPA encoder amplify the ~8pp ligature signal into a
  bottom-quartile-M win? Only K1/K3 answer. The glyph 0.306 floor (residual relative-mask geometry) means
  even this probe isn't a perfectly clean composition measure; the diff−glyph gap is the robust estimate.
