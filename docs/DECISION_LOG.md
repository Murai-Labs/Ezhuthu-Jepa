# Ezhuthu-Jepa — Decision Log

## Update Rules

Record every material research, tooling, gate, execution, blocker-resolution, or reporting
decision here unless it already has a dedicated file under `docs/decisions/` (which must be
linked from this log). Record the rationale **before** running expensive jobs. Never overwrite
an entry — correct a past entry by appending a new one that references it.

Each entry includes: date, task/gate, decision, rationale, alternatives considered, evidence,
measured result (if any), follow-up, and human-approval status.

---

## DEC-0001 - Project scaffolding established

Date: 2026-07-01
Task/Gate: G0
Decision: Initialized the Ezhuthu-Jepa repo with the standard governance/tracker/docs/notes
scaffolding and the phase→gate chain **G0 → LAUNCH-A → G1 → G2 → G3**.
Rationale: Ezhuthu-Jepa is a research project (spec `docs/spec/EZHUTHU_JEPA_Spec_v0.2.md`) whose
central risk is exactly the cheap-baseline failure mode this operating system guards against —
the spec's own kill criteria (K1 seam-vs-block, K3 JEPA-vs-MAE-at-seam, K2 premise probe) are the
mandatory cheap baselines. Installing the trackers/gates/audit trail up front makes G1 adjudicable.
Alternatives Considered:
- Plain CLAUDE.md without gates — rejected: the cheap-baseline gate is the whole point here.
- Merging LAUNCH-A into G1 — rejected: the full n≥3-seed sweep is the single most expensive run and
  warrants its own explicit launch approval per the skill's always-present launch-gate rule.
Evidence / Source Docs: `docs/spec/EZHUTHU_JEPA_Spec_v0.2.md`, `tasks/atomic-task-list.md`,
`docs/GATE_G0_REVIEW.md`, `notes/spec-comprehension-check.md`.
Measured Result: N/A (setup).
Follow-up: Implement provenance writer (P0.003) and config contract (P0.004); freeze eval harness
and pre-register ε (P1.001) before any baseline run.
Human Approval: pending (G0 review drafted; awaiting Ramchand sign-off).

---

## DEC-0002 - Metric M and ε provisionally set (to be pre-registered at P1.001)

Date: 2026-07-01
Task/Gate: G1 (pre-registration pending)
Decision: Provisionally adopt **M = bottom-quartile-frequency akshara top-1 accuracy** (n ≥ 3 seeds,
95 % bootstrap CIs) and **ε = 2.0 pp with the binding adjudicator "non-overlapping 95 % CIs"**. This
is recorded now for traceability but is **not yet the pre-registration** — TASK P1.001 formally
pre-registers ε and the exact frequency cutoff, dated before any baseline run.
Rationale: The spec (§3 K1, §4 Eval) mandates frequency-stratified evaluation and non-overlapping CIs
on the long tail; aggregate accuracy is explicitly not the contribution. Sub-2pp gaps at probe scale
are within typical seed variance, so the CI-overlap test is the real adjudicator.
Alternatives Considered:
- Aggregate top-1 accuracy — rejected: hides the long-tail story the paper is about.
- ε by a single seed — rejected: no CI ⇒ non-adjudicable gate.
Evidence / Source Docs: spec §3, §4; `tasks/atomic-task-list.md` P1.001.
Measured Result: N/A.
Follow-up: Formalize in P1.001 with the exact bottom-quartile count cutoff once PA.002 computes
corpus frequencies.
Human Approval: pending.

---

## DEC-0003 - Phase-0 config + provenance implemented with stdlib only (no pydantic/PyYAML yet)

Date: 2026-07-01
Task/Gate: G0 (TASK P0.003, P0.004)
Decision: Implemented the run-provenance writer (`src/ezhuthu_jepa/provenance.py`) and the versioned
config contract (`src/ezhuthu_jepa/config.py`, schema `0.1.0`) using **only the Python standard
library** (frozen `dataclass` + a typed `ConfigValidationError`, `hashlib`, `subprocess` git,
`importlib.metadata`). No third-party validation/serialization dependency is added at Phase 0.
Rationale: The training toolchain is not yet chosen (spec §4 keeps the core single-5090 and minimal),
and the earlier decision (DEC-0001 follow-through) kept the skeleton installable without an unlocked
toolchain. Stdlib gives a fully-controlled typed contract with zero install surface; pydantic/PyYAML
are pinned only when a real consumer needs them (`configs/phase0/locked-versions.yaml` → `deferred`,
PyYAML at PA.005 for loading `configs/phase1/*.yaml`).
Alternatives Considered:
- pydantic for config — rejected for now: heavy dep before the training stack exists; revisit if the
  config grows enough that hand-rolled validation becomes a liability.
- Hashing the raw config file bytes instead of a canonical dict — rejected: sensitive to formatting;
  `to_canonical_dict` + sorted-key JSON gives an order/format-independent, stable hash.
Evidence / Source Docs: `src/ezhuthu_jepa/config.py`, `src/ezhuthu_jepa/provenance.py`,
`notes/schema-audits/ezhuthu_jepa-config.md`, `configs/phase0/locked-versions.yaml`,
`tests/test_config.py` (18) + `tests/test_provenance.py` (9) — full suite 28 passed.
Measured Result: All P0.003/P0.004 acceptance criteria pass (manifest carries exactly the 5
identifiers; missing identifier rejected; out-of-contract config raises a typed error).
Follow-up: PA-phase data/train code must call `write_provenance(...)` before any run and load configs
via `RunConfig.from_dict(...)`. Re-audit the schema when PA.004/PA.005 add behavioral consumers.
Human Approval: pending.
