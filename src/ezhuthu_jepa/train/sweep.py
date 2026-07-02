"""Stage-A sweep orchestrator — {objectives} × {seeds}, one switched variable (TASK P1.003 / pilot).

Runs the pretraining loop once per (objective, seed) arm from a **single base config**, so the
architecture / compute / mask-ratio are provably identical across arms and only the objective (and the
seed) changes — the clean K1/K3 design (spec §3). Each arm gets its own provenanced run dir.

**LAUNCH-A gate (AGENTS.md §7, defense-in-depth).** The full n ≥ 3-seed sweep is the single most
expensive run and must not start before human approval. This orchestrator therefore *refuses* to
execute a ≥3-seed plan unless ``--launch-a-approved`` is passed (which the operator sets only after
``docs/GATE_LAUNCH_A_REVIEW.md`` is signed). A 1-seed **pilot** — a LAUNCH-A *precondition* — is
allowed. The default is a dry-run that prints the plan and starts nothing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .pretrain import PretrainConfig, train

# A plan with this many seeds or more is "the full sweep" and is gated by LAUNCH-A.
FULL_SWEEP_MIN_SEEDS = 3


def load_sweep(path: str | Path) -> tuple[dict, list[str], list[int], str]:
    """Parse a sweep config into (base-hyperparams, objectives, seeds, run_prefix)."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    for key in ("base", "objectives", "seeds"):
        if key not in data:
            raise ValueError(f"sweep config missing required key {key!r}")
    for reserved in ("objective", "seed"):
        if reserved in data["base"]:
            raise ValueError(f"'base' must not set {reserved!r}; it is swept per arm")
    return data["base"], list(data["objectives"]), list(data["seeds"]), data.get("run_prefix", "phase1-sweep")


def build_arms(objectives: list[str], seeds: list[int]) -> list[tuple[str, int]]:
    """Every (objective, seed) arm, objective-major order."""
    return [(obj, seed) for obj in objectives for seed in seeds]


def arm_config(base: dict, objective: str, seed: int) -> PretrainConfig:
    """Construct the arm's PretrainConfig from the shared base + the swept objective/seed."""
    return PretrainConfig(**{**base, "objective": objective, "seed": seed})


def run_sweep(
    config_path: str | Path,
    run_root: str | Path = "runs",
    *,
    execute: bool = False,
    launch_a_approved: bool = False,
    resume: bool = False,
) -> list[Path]:
    """Run (or dry-run) every arm. Returns the list of metrics.json paths (empty on dry-run)."""
    base, objectives, seeds, prefix = load_sweep(config_path)
    arms = build_arms(objectives, seeds)
    cfgs = [(obj, seed, arm_config(base, obj, seed)) for obj, seed in arms]  # fail fast on a bad base
    is_full = len(seeds) >= FULL_SWEEP_MIN_SEEDS

    kind = "FULL SWEEP (LAUNCH-A gated)" if is_full else "pilot / partial"
    print(f"[sweep] plan: {len(arms)} arms = {objectives} × seeds {seeds}; prefix={prefix}; {kind}", flush=True)
    for obj, seed, _ in cfgs:
        print(f"[sweep]   {prefix}-{obj}-seed{seed}", flush=True)
    if not execute:
        print("[sweep] dry-run — pass --execute to run. No runs started.", flush=True)
        return []
    if is_full and not launch_a_approved:
        raise SystemExit(
            "[sweep] REFUSED: the full sweep (≥3 seeds) is gated by LAUNCH-A. Sign "
            "docs/GATE_LAUNCH_A_REVIEW.md, then pass --launch-a-approved. (A 1-seed pilot is allowed.)"
        )

    results: list[Path] = []
    for i, (obj, seed, cfg) in enumerate(cfgs, start=1):
        run_dir = Path(run_root) / f"{prefix}-{obj}-seed{seed}"
        print(f"[sweep] === arm {i}/{len(cfgs)}: {obj} seed{seed} -> {run_dir} ===", flush=True)
        results.append(train(cfg, run_dir, resume=resume))
    print(f"[sweep] done: {len(results)} arm(s) -> {run_root}", flush=True)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage-A sweep orchestrator (objectives × seeds).")
    parser.add_argument("--config", type=Path, default=Path("configs/phase1/sweep.yaml"))
    parser.add_argument("--run-root", type=Path, default=Path("runs"))
    parser.add_argument("--execute", action="store_true", help="actually run (default: dry-run)")
    parser.add_argument("--launch-a-approved", action="store_true",
                        help="required to execute the full ≥3-seed sweep (only after LAUNCH-A is signed)")
    parser.add_argument("--resume", action="store_true", help="resume each arm from its resume-state.pt")
    args = parser.parse_args(argv)
    run_sweep(args.config, args.run_root, execute=args.execute,
              launch_a_approved=args.launch_a_approved, resume=args.resume)
    return 0


if __name__ == "__main__":
    sys.exit(main())
