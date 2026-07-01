# Ezhuthu-Jepa — Experiment Log

## Update Rules

Append an entry after EVERY run — including failed, skipped, or inconclusive runs. Never
overwrite. Run IDs are descriptive and never reused.

## Entry Template

```
Run ID:            <phaseN-purpose-NNN>
Task ID:           <TASK id from atomic list>
Date:              <YYYY-MM-DD>
Git Commit:        <SHA>
Git Status:        <clean / dirty (list)>
Exact Command:     <command>
Config Path:       <configs/...>
Config Hash:       <sha256>
Data Hash:         <sha256 / split id>
Seed:              <int>
Environment:       <GPU, CUDA, Python, key package versions>
Checkpoint Path:   <path or n/a>
Metrics Path:      <runs/.../metrics.json>
Status:            <success / failed / inconclusive>
Failure Notes:     <if applicable>
Interpretation:    <what it means; claim boundary>
Next Action:       <follow-up>
```

## Run ID Allocation

Use descriptive IDs preserving phase and purpose, e.g. `phaseA-smoke-001`, `phase1-k2probe-001`,
`phase1-sweep-seamjepa-seed0`, `phase2-k4-001`. Do not reuse IDs, even for failed attempts.

---

_No runs yet. First expected run: `phaseA-smoke-001` (TASK PA.005), gated behind LAUNCH-A for the
full sweep._
