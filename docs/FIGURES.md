# Ezhuthu-Jepa — Figures Index

Every paper figure is **regenerated from a committed script** under `src/ezhuthu_jepa/figures/`
(never hand-drawn) and carries a `<fig>.prov.json` sidecar citing its source run-id + code SHA. This
index maps figure → paper section → generator → source run. Add a row when a figure is created.

## Convention

- Figure files live in `docs/figures/` (committed — figures are *reports*, small and reproducible).
- Regenerate all figures after a result changes; the sidecar's `code_sha` / `source.run_id` make a
  stale figure detectable (compare against the run it claims to derive from).
- A figure may only cite a run whose `runs/<run-id>/provenance.json` is committed.

## Index

| Figure | Paper section | Generator | Source run | Shows |
|--------|---------------|-----------|------------|-------|
| **F1** | Method — seam localization | `figures.f1_seam_localization` | `pa001-render-001` | Rendered aksharas (k/nn/zh × 12 vowels, Noto) with seam boxes: green = separable-glyph sign, orange = ligature (diff), none = inherent 'a'. Makes the masked region concrete and exposes the ligature cases. |
| **F2** | Data — frequency stratification | `figures.f2_frequency_distribution` | `pa002-split-001` | The 216 uyirmei ranked by Project Madurai frequency (log10); orange = bottom quartile (metric M's long tail), green line = frozen cutoff. 4.85M counted, 207/216 seen. |
| **F3** | Results — recognition accuracy (baseline) | `figures.f3_probe_accuracy` | `pa003-probe-001` | Top-1 accuracy by frequency bucket & seam_source with 95% CIs; orange = metric M. Weak PixelEncoder baseline (metric M = 0.333); JEPA encoder replaces it at PA.005. |

## Regenerate

```bash
# F1 (seam localization)
PYTHONPATH=src python -m ezhuthu_jepa.figures.f1_seam_localization
# F2 (frequency distribution) — needs runs/pa002-split-001/split-manifest.json
PYTHONPATH=src python -m ezhuthu_jepa.figures.f2_frequency_distribution
# F3 (probe accuracy) — needs runs/pa003-probe-001/metrics.json
PYTHONPATH=src python -m ezhuthu_jepa.figures.f3_probe_accuracy
```

## Planned (capture as milestones land)

- **F4** — K1/K3 main comparison (seam-JEPA vs block-JEPA vs MAE-at-seam) on M, with CIs (P1.003).
- **F5** — K4 degradation curves (missing-puḷḷi etc.) (P2.003).
