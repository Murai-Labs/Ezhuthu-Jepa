# Compute-Hour Ledger — K1–K4 on a single RTX 5090 (TASK PA.006, spec §4, AGENTS.md §1)

**Purpose.** Pre-commit the GPU-hour budget for the K1–K4 program *before* the expensive sweep, and
name a hard ceiling beyond which continuing requires human approval. This is the MARMAM-style ledger
the global lab rule requires: it makes "evenings-scale on one 5090" a number, not a vibe, and it
contrasts K1–K4 against a full-foundation build so scope creep is visible. **No H100/Lambda is used
for K1–K4** (spec §1); crossing the ceiling means *re-scope or seek approval*, never "rent a bigger GPU".

Status: pre-committed 2026-07-02, before LAUNCH-A. Unit costs are **measured**; run lengths are a
**planned budget** (pilot-confirmed at LAUNCH-A); totals are estimates carrying an explicit buffer.

---

## 1. Measured unit costs (from the PA.005 smoke runs, RTX 5090, bf16, ViT-Tiny/8, batch 128)

| Source run | Objective | Throughput | Per-step (batch 128) |
|------------|-----------|-----------:|---------------------:|
| `phaseA-smoke-001` | seam_jepa (latent + EMA target) | 2,543 img/s | ~50 ms |
| `phaseA-smoke-002` | block_jepa (latent + EMA target) | 2,989 img/s | ~43 ms |
| `phaseA-smoke-003` | mae_seam (pixel, no EMA target) | 3,487 img/s | ~37 ms |

Derived: augmented train set = 21,600 instances → **169 steps/epoch** at batch 128. The probe eval on
the 54k augmented index is **image-load bound** at ~3–4 min/run (measured `pa003b-probe-aug-001`,
GPU encode of 54k ViT-Tiny features is <10 s; the cost is decoding 54k PNGs). Conservative planning
uses the **slowest** (seam, 50 ms/step) for latent arms.

## 2. Planned run length (provisional; the LAUNCH-A pilot confirms convergence)

**Full pretraining run = 50,000 steps (~296 epochs).** Provisional; the 1-seed pilot must show the
loss still descending / probe metric_M rising near the budget, else the sweep config raises it. The
sweep config also sets `checkpoint_every` (resume-state) since each run exceeds 30 min.

- Latent run (seam / block): 50,000 × 50 ms = **~0.70 GPU-h**.
- Pixel run (mae_seam):      50,000 × 37 ms = **~0.51 GPU-h**.

## 3. Line items

| Phase | Task | Runs | Est. GPU-h | Notes |
|-------|------|-----:|-----------:|-------|
| Smoke (done) | PA.005 | 3 × 30 steps | ~0.01 | already spent; `phaseA-smoke-001/2/3` |
| K2 premise probe | P1.002 | supervised base→sign probe(s) | ~0.3 | cheap; probe-fit only, no pretraining |
| Pilot (LAUNCH-A precondition) | PA.005/LA.001 | 1 seed × 3 objectives, short | ~1.0 | confirm convergence + smoke-pass + eval |
| **Full K1/K3 sweep** | **P1.003** | **3 objectives × 3 seeds = 9** | **~5.7** | seam+block: 6 × 0.70; mae: 3 × 0.51 |
| Probe evals of the sweep | P1.003 | 9 checkpoints × ~4 min | ~0.6 | metric M + McNemar inputs |
| K4 degradation suite | G2 | re-eval 9 ckpts × ~4 corruptions + some re-pretrain | ~4.0 | generous; corruption realism vs real sample |
| Figures / reruns / false starts | — | buffer | ×1.3 on the above | provenance-clean reruns happen |
| **Planned subtotal** | | | **~11.6** | before buffer |
| **Planned total (×1.3 buffer)** | | | **~15 GPU-h** | the K1–K4 program, one 5090 |

## 4. Hard ceiling (escalation gate)

> **Hard ceiling: 40 RTX-5090 GPU-hours, cumulative, for the entire K1–K4 program.**
> If cumulative GPU time crosses 40 h, **halt and obtain Ramchand's written approval** in
> `docs/DECISION_LOG.md` before continuing. 40 h is ~2.7× the ~15 h plan — headroom for reruns and a
> longer pilot, but far short of foundation-model scale.

Escalation does **not** mean a bigger GPU: the H100/Lambda exclusion for K1–K4 (spec §1) stands. If the
ceiling is hit, the options are (a) re-scope (fewer seeds, shorter schedule, clean-script-only), or
(b) an explicit new gate decision by Ramchand — never a silent jump to more/bigger hardware.

## 5. Contrast — a full-foundation build (explicitly OUT of scope for K1–K4)

A from-scratch Tamil-manuscript vision foundation model (ViT-L/‑H, the full rendered + real corpus,
heavy augmentation, a long multi-stage schedule) is on the order of **hundreds to thousands of
GPU-hours** — roughly **10²–10³× the K1–K4 plan**. It is not undertaken to answer K1–K4, would need its
own gate, and would require the H100 exclusion to be lifted by Ramchand. K1–K4 lives or dies on the
grapheme-seam vs block/MAE comparison at evenings-scale; that is the whole point of the cheap-baseline
gate. Recorded so the ~15 h program is never quietly rescoped into a foundation-model build.

---

Linked from `docs/DECISION_LOG.md` (DEC-0015). Evidence: runs `phaseA-smoke-001/-002/-003`,
`pa003b-probe-aug-001`; loop `src/ezhuthu_jepa/train/pretrain.py`.
