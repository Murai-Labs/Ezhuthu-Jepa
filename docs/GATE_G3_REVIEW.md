# Gate G3 Review — Publication & Demo Release

## Purpose

G3 blocks public release (arXiv + demo + open recipe) until every reported metric is provenanced,
negatives are reported honestly, and the transcription-aid demo works end-to-end. Per the spec, the
rendered-core + demo + honest-negative structure is self-justifying as an arXiv artifact regardless
of how K4 landed.

## Gate Status

Status: Not yet approved. Approval is recorded in `docs/DECISION_LOG.md`; this file preserves the
review evidence.

## Required Evidence

| Requirement | Evidence (path) | Status |
|-------------|-----------------|--------|
| Frequency-stratified benchmark + open recipe | `docs/benchmark-card.md` (P3.001) | Missing |
| Reproducibility dry-run of a reported M | `docs/RUNBOOK.md` recipe section | Missing |
| Gradio transcription-aid demo runs end-to-end | `src/ezhuthu_jepa/demo/app.py` (P3.002) | Missing |
| Demo loads a provenanced checkpoint (no placeholder) | checkpoint run-id | Missing |
| Paper draft with honest negatives | `docs/paper/` (P3.003) | Missing |
| Every metric cites run-id + 5 provenance identifiers | paper + EXPERIMENT_LOG cross-check | Missing |

## Explicit Non-Results

Venue is deliberately deferred (spec §7): the artifact is planned as arXiv-only unless the result
warrants a venue conversation. G3 approves *release*, not venue selection.

## Approval Template (paste into docs/DECISION_LOG.md when granted)

```
## DEC-XXXX - G3 approved
Date: <YYYY-MM-DD>
Task/Gate: G3
Decision: G3 (Publication & Demo Release) approved; arXiv artifact + demo + recipe released.
Rationale: All metrics provenanced, negatives reported, demo verified end-to-end.
Evidence / Source Docs: docs/GATE_G3_REVIEW.md, docs/benchmark-card.md, docs/paper/.
Human Approval: <name> on <date>.
```
