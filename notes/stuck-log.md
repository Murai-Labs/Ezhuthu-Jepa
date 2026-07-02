# Stuck Log (append-only)

Append an entry whenever blocked for more than one serious attempt. Escalate after logging.

## Entry format
### <YYYY-MM-DD HH:MM TZ> — <task ID>
- Goal: <what I was trying to do>.
- Attempts: <what I tried>.
- Failures: <exact errors / why each failed>.
- Hypothesis: <current best guess>.
- Escalation: <question for the human / decision needed>.

---

### 2026-07-02 CT — LAUNCH-A pilot (blocks the full sweep)
- Goal: confirm the pipeline + convergence with a 1-seed pilot (3 objectives × 8k steps) before the
  full sweep, and produce a first metric_M per arm (runs `phase1-pilot-*`, `phase1-pilotprobe-*`).
- Attempts: (1) trained all 3 arms 8k steps (loss curves healthy; latent arms plateau ~0.04, MAE still
  descending). (2) Probed each with the JEPA context encoder → seam 0.255, block 0.286, mae 0.532
  (pixel baseline 0.359). (3) Hypothesised the latent arms were undersold because the probe used the
  CONTEXT encoder, not the I-JEPA downstream EMA TARGET encoder — saved the target and re-probed.
- Failures: the target-encoder fix did NOT rescue the latent arms — seam 0.239, block 0.326, both still
  **below the 0.359 raw-pixel baseline**; MAE (pixel target) dominates at 0.532. So the latent I-JEPA
  recipe genuinely produces worse representations than raw pixels at this scale — not an eval artifact.
- Hypothesis: my from-scratch I-JEPA is under-baked vs the paper — most likely missing **LR cosine
  decay** (loss plateaued under constant LR), and possibly proper multi-block masking, weight-decay
  schedule, mask-scale, or simply more scale/steps. MAE's dense pixel signal learns fine; the sparse
  latent target does not, here.
- Escalation: **LAUNCH-A is blocked** — running the ~15 GPU-h sweep now would compare broken latent
  encoders (and MAE would "win" K3 as an artifact). Decision needed (DEC-0017): (A) iterate the recipe
  — add LR cosine decay + verify against the I-JEPA paper, re-pilot until latent ≥ pixels; (B) reframe
  toward "seam, not target" (MAE-at-seam), which the contract permits; or (C) if recipe iteration fails,
  conclude honestly (the fancy latent mechanism loses to the cheap baselines). Recommend (A) first — it
  is cheap and the recipe is admittedly simplified. Do NOT launch the sweep until latent JEPA is
  competitive with the pixel baseline on the pilot.

### 2026-07-02 CT — PA.005b recipe iteration (option A) result: cheap-baseline kill signal
- Goal: lift latent seam-JEPA above the pixel baseline (0.359) via recipe iteration.
- Attempts: (1) LR cosine decay + 16k steps → seam 0.239→0.290 (helped, still < pixels). (2) Full 50k
  budget → seam 0.212 (WORSE; effective rank 39.7→20.2 — degrades with scale). (3) Matched block at 16k
  cosine → 0.335. (4) Collapse diagnostic (feature std / eff-rank).
- Failures: seam-latent-JEPA peaks at 0.290 < pixel 0.359; block-JEPA (0.335) BEATS seam (K1 reversed,
  non-overlapping CIs); MAE-at-seam (0.532) crushes latent (K3 reversed). Both cheap baselines exceed the
  mechanism beyond ε. Recipe iteration did not reverse the direction.
- Hypothesis: at evenings-scale on this task, the latent-target objective is a weak/unstable learning
  signal vs pixel reconstruction; the seam mask does not beat block masking. Anti-collapse surgery
  (VICReg/multi-block/ViT-Small) *might* help but the prior is now against it.
- Escalation: **Section 3 cheap-baseline-falsification triggered (DEC-0018).** Potential project
  re-scope/termination — Ramchand's call. Recommend one last cheap datapoint (MAE-at-block vs MAE-at-seam:
  does the seam mask help at all with a pixel target?), then reframe/conclude. Do NOT launch the sweep.
