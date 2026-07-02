"""Frequency-stratified benchmark split with a frozen bottom-quartile (TASK PA.002).

Turns Project Madurai compound frequencies (DEC-0004) into (a) a quartile bucket per uyirmei with the
bottom quartile — the long tail metric M lives on — frozen, and (b) a deterministic, leak-free
train/eval partition of the rendered instances. Writes ``data/rendered/split-manifest.json`` plus a
``provenance.json`` (seed = the split seed; not RNG-free, so a real integer seed is recorded).

The 216-uyirmei universe is fixed (from :mod:`grapheme`); a compound absent from the corpus gets
frequency 0 and lands in the bottom quartile — exactly the rare/unseen long tail the paper targets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import dataclass, fields
from pathlib import Path

import yaml

from ..provenance import hash_paths, validate_run_dir, write_provenance
from .frequency import count_uyirmei_in_files
from .grapheme import enumerate_uyirmei

BUCKET_LABELS = ("q1_bottom", "q2", "q3", "q4_top")


class SplitError(RuntimeError):
    """Raised on an invalid split configuration or corpus."""


@dataclass(frozen=True)
class SplitConfig:
    corpus_dir: str
    render_manifest: str
    n_buckets: int = 4
    eval_fraction: float = 0.5
    split_seed: int = 42

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SplitConfig":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        allowed = {f.name for f in fields(cls)}
        unknown = set(data) - allowed
        if unknown:
            raise SplitError(f"unknown split-config key(s): {sorted(unknown)}")
        missing = {"corpus_dir", "render_manifest"} - set(data)
        if missing:
            raise SplitError(f"split config missing required key(s): {sorted(missing)}")
        return cls(**data)


def compute_frequencies(corpus_paths: list[Path]) -> dict[str, int]:
    """Frequency of every one of the 216 uyirmei over the corpus (0-filled for unseen)."""
    counts, _ = count_uyirmei_in_files(corpus_paths)
    freqs = {a.id: 0 for a in enumerate_uyirmei()}
    for akshara_id, c in counts.items():
        if akshara_id in freqs:  # ignore any stray id not in the fixed universe
            freqs[akshara_id] += c
    return freqs


def assign_buckets(
    frequencies: dict[str, int], n_buckets: int = 4
) -> tuple[dict[str, str], list[int], list[str]]:
    """Rank uyirmei by frequency into ``n_buckets`` equal groups.

    Returns (bucket_of_akshara, per-bucket max-count boundaries, bottom-quartile id list). Ranking is
    ascending by (count, akshara_id) so it is deterministic and ties are stable. Requires the universe
    size to divide evenly by n_buckets (216 / 4 = 54).
    """
    ids = sorted(frequencies, key=lambda a: (frequencies[a], a))
    total = len(ids)
    if total % n_buckets != 0:
        raise SplitError(f"{total} aksharas not divisible by n_buckets={n_buckets}")
    size = total // n_buckets
    if n_buckets != len(BUCKET_LABELS):
        raise SplitError(f"n_buckets={n_buckets} but {len(BUCKET_LABELS)} labels defined")
    bucket_of: dict[str, str] = {}
    boundaries: list[int] = []
    for b in range(n_buckets):
        group = ids[b * size : (b + 1) * size]
        for aid in group:
            bucket_of[aid] = BUCKET_LABELS[b]
        boundaries.append(frequencies[group[-1]])  # max count in this bucket
    bottom_quartile = [aid for aid in ids if bucket_of[aid] == BUCKET_LABELS[0]]
    return bucket_of, boundaries, bottom_quartile


def _instance_key(seed: int, akshara_id: str, font_id: str) -> str:
    return hashlib.md5(f"{seed}:{akshara_id}:{font_id}".encode("utf-8")).hexdigest()


def assign_split(
    instances: list[dict], eval_fraction: float, seed: int
) -> dict[tuple[str, str], str]:
    """Assign each (akshara_id, font_id) instance to 'train' or 'eval'.

    Guarantees: instances are physically disjoint across splits; every akshara with ≥2 instances has
    at least one in each split (so all 216 classes are learnable and evaluable); a single-instance
    akshara goes to train. Deterministic given ``seed``; the per-akshara ordering mixes the font so
    the split is not a global font holdout.
    """
    if not 0.0 < eval_fraction < 1.0:
        raise SplitError(f"eval_fraction must be in (0,1), got {eval_fraction}")
    by_akshara: dict[str, list[dict]] = {}
    for inst in instances:
        by_akshara.setdefault(inst["akshara_id"], []).append(inst)

    assignment: dict[tuple[str, str], str] = {}
    for akshara_id, insts in by_akshara.items():
        ordered = sorted(insts, key=lambda x: _instance_key(seed, akshara_id, x["font_id"]))
        n = len(ordered)
        if n == 1:
            assignment[(akshara_id, ordered[0]["font_id"])] = "train"
            continue
        n_eval = max(1, min(n - 1, round(eval_fraction * n)))
        for j, inst in enumerate(ordered):
            split = "eval" if j < n_eval else "train"
            assignment[(akshara_id, inst["font_id"])] = split
    return assignment


def build_split(config_path: Path, run_dir: Path) -> Path:
    config = SplitConfig.from_yaml(config_path)
    corpus_dir = Path(config.corpus_dir)
    corpus_paths = sorted(p for p in corpus_dir.glob("**/*.txt") if p.is_file())
    if not corpus_paths:
        raise SplitError(f"no .txt corpus files under {corpus_dir}")

    render_manifest_path = Path(config.render_manifest)
    render_manifest = json.loads(render_manifest_path.read_text(encoding="utf-8"))
    instances = [
        {"akshara_id": e["akshara_id"], "font_id": e["font_id"], "image": e["image"]}
        for e in render_manifest["entries"]
    ]

    frequencies = compute_frequencies(corpus_paths)
    bucket_of, boundaries, bottom_quartile = assign_buckets(frequencies, config.n_buckets)
    assignment = assign_split(instances, config.eval_fraction, config.split_seed)

    all_aksharas = enumerate_uyirmei()
    ranked = sorted(all_aksharas, key=lambda a: (frequencies[a.id], a.id))
    rank_of = {a.id: i for i, a in enumerate(ranked)}

    total_uyirmei = sum(frequencies.values())
    corpus_files = [
        {"name": p.name, "sha256": hash_paths([p]), "uyirmei_count": sum(count_uyirmei_in_files([p])[0].values())}
        for p in corpus_paths
    ]
    inst_records = [
        {**inst, "split": assignment[(inst["akshara_id"], inst["font_id"])]} for inst in instances
    ]
    n_train = sum(1 for r in inst_records if r["split"] == "train")

    run_dir.mkdir(parents=True, exist_ok=True)
    write_provenance(
        run_dir,
        config=config,
        data_hash=hash_paths(corpus_paths + [render_manifest_path]),
        run_id=run_dir.name,
        seed=config.split_seed,
        package_names=["pyyaml"],
    )

    manifest = {
        "run_id": run_dir.name,
        "task": "PA.002",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "provenance_ref": "provenance.json",
        "corpus": {
            "dir": corpus_dir.as_posix(),
            "n_files": len(corpus_paths),
            "files": corpus_files,
            "total_uyirmei": total_uyirmei,
            "distinct_uyirmei_seen": sum(1 for v in frequencies.values() if v > 0),
        },
        "buckets": {
            "n": config.n_buckets,
            "size": len(all_aksharas) // config.n_buckets,
            "labels": list(BUCKET_LABELS),
            "count_boundaries": boundaries,
        },
        "bottom_quartile": bottom_quartile,
        "aksharas": [
            {
                "akshara_id": a.id,
                "base_id": a.base_id,
                "sign_id": a.sign_id,
                "frequency": frequencies[a.id],
                "rank": rank_of[a.id],
                "bucket": bucket_of[a.id],
            }
            for a in all_aksharas
        ],
        "split": {
            "seed": config.split_seed,
            "eval_fraction": config.eval_fraction,
            "n_train": n_train,
            "n_eval": len(inst_records) - n_train,
        },
        "instances": inst_records,
    }
    # The split-manifest freezes metric M's bottom quartile — a critical COMMITTED artifact — so it
    # lives in the committed run dir, not under gitignored data/rendered/.
    manifest_path = run_dir / "split-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    validate_run_dir(run_dir)
    print(
        f"[frequency_split] {total_uyirmei} uyirmei counted over {len(corpus_paths)} files; "
        f"bottom quartile = {len(bottom_quartile)} compounds; "
        f"split {n_train} train / {len(inst_records) - n_train} eval; manifest {manifest_path}",
        flush=True,
    )
    return manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the frequency-stratified split (PA.002).")
    parser.add_argument("--config", type=Path, default=Path("configs/phase1/split.yaml"))
    parser.add_argument("--run-dir", type=Path, default=Path("runs/pa002-split-001"))
    args = parser.parse_args(argv)
    build_split(args.config, args.run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
