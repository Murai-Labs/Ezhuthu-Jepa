"""Akshara-recognition evaluation harness — metric M, bootstrap CIs, McNemar (TASK PA.003, P1.001b).

Given a **frozen encoder**, fit a linear probe (numpy ridge on one-hot targets) on the train
instances and evaluate top-1 accuracy on the eval instances, reported:
- overall,
- per frequency bucket (the bottom quartile is **metric M**),
- per `seam_source` (glyph / diff / none) and per font  (DEC-0006),
each with a 95 % bootstrap CI. Writes `metrics.json`, `predictions.jsonl` (per-instance correctness
for paired tests), and `provenance.json` to the run dir.

Two data backends (same metric machinery):
- **manifest** — the PA.002 split-manifest + PA.001 render-manifest (per-akshara-random split);
- **index** — the PA.4b.2 augmented per-instance `index.jsonl` (font-holdout, ~54k instances), whose
  larger eval set shrinks metric M's CI toward ~1 pp so a 2 pp effect is adjudicable (DEC-0013).

The comparator (`compare_arms`, TASK P1.001b) adjudicates two arms on identical eval instances with a
**paired McNemar test (primary, Bonferroni-corrected)** and a **non-overlapping-CI verdict
(secondary)** — the amended G1 decision rule (DEC-0013). ε = 2.0 pp is the pre-registered minimum
effect size (DEC-0009/0013).

The encoder is a plug-in (Protocol): a `PixelEncoder` baseline runs today; the I-JEPA encoder from
PA.005 drops in unchanged (`encoder: jepa`, `checkpoint:`). The metric machinery here is frozen
*before* the K1/K3 sweep so the comparison is judged on a fixed metric (AGENTS.md §2.6).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import zlib
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Protocol

import numpy as np
import yaml
from PIL import Image

from ..provenance import hash_paths, validate_run_dir, write_provenance
from ..data.grapheme import enumerate_uyirmei

BUCKET_LABELS = ("q1_bottom", "q2", "q3", "q4_top")
METRIC_M_BUCKET = "q1_bottom"

# Pre-registered minimum effect size on metric M (DEC-0009, retained by DEC-0013). Percentage points.
EPSILON_PP = 2.0
# McNemar switches to the exact binomial when discordant pairs are few (χ² approx unreliable).
MCNEMAR_EXACT_BELOW = 25
# Progress cadence for the image-load loop (Rule 11 / AGENTS.md §4): 54k reads exceed 30 s.
_LOAD_PROGRESS_EVERY = 4000


class Encoder(Protocol):
    name: str

    def encode(self, images: np.ndarray) -> np.ndarray:
        """(N, H, W) uint8 grayscale -> (N, D) float features."""
        ...


@dataclass(frozen=True)
class PixelEncoder:
    """Baseline frozen encoder: downsample to a square, flatten, scale to [0,1], mean-center.

    A deliberately weak reference so the harness produces a real number today; replaced by the
    JEPA encoder at PA.005. Deterministic (no RNG)."""

    downsample: int = 32
    name: str = "pixel32"

    def encode(self, images: np.ndarray) -> np.ndarray:
        feats = []
        for img in images:
            small = np.asarray(
                Image.fromarray(img).resize((self.downsample, self.downsample), Image.BILINEAR),
                dtype=np.float32,
            )
            feats.append(small.reshape(-1) / 255.0)
        x = np.stack(feats)
        return x - x.mean(axis=0, keepdims=True)


class ProbeConfigError(ValueError):
    """Raised when a probe config specifies neither a valid manifest pair nor an index backend."""


@dataclass(frozen=True)
class ProbeConfig:
    """Probe/eval configuration.

    Supply exactly one data backend:
      - ``index_jsonl`` (augmented per-instance index, PA.4b.2), or
      - ``split_manifest`` + ``render_manifest`` (PA.002 split + PA.001 render).
    ``index_jsonl`` takes precedence if both are given.
    """

    image_dir: str
    split_manifest: str = ""
    render_manifest: str = ""
    index_jsonl: str = ""
    ridge_lambda: float = 1.0
    bootstrap_n: int = 2000
    seed: int = 42
    encoder: str = "pixel32"
    downsample: int = 32
    checkpoint: str = ""  # required when encoder == "jepa" (PA.005)

    def __post_init__(self) -> None:
        if not self.index_jsonl and not (self.split_manifest and self.render_manifest):
            raise ProbeConfigError(
                "probe config needs either index_jsonl or (split_manifest and render_manifest)"
            )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ProbeConfig":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        allowed = {f.name for f in fields(cls)}
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"unknown probe-config key(s): {sorted(unknown)}")
        return cls(**data)


def fit_ridge(x: np.ndarray, y: np.ndarray, n_classes: int, lam: float) -> np.ndarray:
    """Closed-form ridge regression to one-hot targets, with a bias column. Returns W (D+1, C)."""
    xb = np.hstack([x, np.ones((x.shape[0], 1), dtype=x.dtype)])
    onehot = np.zeros((x.shape[0], n_classes), dtype=np.float64)
    onehot[np.arange(x.shape[0]), y] = 1.0
    d = xb.shape[1]
    a = xb.T @ xb + lam * np.eye(d)
    return np.linalg.solve(a, xb.T @ onehot)


def predict(x: np.ndarray, w: np.ndarray) -> np.ndarray:
    xb = np.hstack([x, np.ones((x.shape[0], 1), dtype=x.dtype)])
    return (xb @ w).argmax(axis=1)


def bootstrap_ci(correct: np.ndarray, n_boot: int, seed: int) -> dict[str, float]:
    """Mean accuracy + 95 % bootstrap CI over a boolean correctness array."""
    n = len(correct)
    if n == 0:
        return {"accuracy": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "n": 0}
    rng = np.random.default_rng(seed)
    accs = np.empty(n_boot, dtype=np.float64)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        accs[b] = correct[idx].mean()
    lo, hi = np.percentile(accs, [2.5, 97.5])
    return {"accuracy": float(correct.mean()), "ci_low": float(lo), "ci_high": float(hi), "n": int(n)}


def _stratify(records: list[dict], key: str, seed: int, n_boot: int) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for value in sorted({r[key] for r in records}):
        correct = np.array([r["correct"] for r in records if r[key] == value], dtype=bool)
        # stable (PYTHONHASHSEED-independent) per-stratum seed offset: reproducible yet independent
        offset = zlib.crc32(f"{key}:{value}".encode("utf-8")) % 10_000
        out[value] = bootstrap_ci(correct, n_boot, seed + offset)
    return out


def stratified_metrics(records: list[dict], n_boot: int, seed: int) -> dict:
    """Compute overall + per-bucket/seam_source/font accuracy with CIs; expose metric M."""
    correct = np.array([r["correct"] for r in records], dtype=bool)
    by_bucket = _stratify(records, "bucket", seed, n_boot)
    return {
        "overall": bootstrap_ci(correct, n_boot, seed),
        "metric_M": by_bucket.get(
            METRIC_M_BUCKET, {"accuracy": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "n": 0}
        ),
        "by_bucket": by_bucket,
        "by_seam_source": _stratify(records, "seam_source", seed, n_boot),
        "by_font": _stratify(records, "font", seed, n_boot),
    }


# --------------------------------------------------------------------------------------------------
# Paired comparator (TASK P1.001b) — McNemar (primary) + non-overlapping CI (secondary), DEC-0013.
# --------------------------------------------------------------------------------------------------

class ComparisonError(ValueError):
    """Raised when two arms are not compared on identical eval instances (McNemar precondition)."""


@dataclass(frozen=True)
class McNemarResult:
    """Paired McNemar test on two aligned boolean correctness vectors.

    ``b`` = arm-A correct & arm-B wrong; ``c`` = arm-A wrong & arm-B correct. Only the discordant
    pairs (b, c) carry information. Uses the exact two-sided binomial when ``b + c`` is small
    (< :data:`MCNEMAR_EXACT_BELOW`) and the χ² statistic with continuity correction otherwise.
    """

    b: int
    c: int
    n_discordant: int
    statistic: float
    p_value: float
    method: str  # "exact_binomial" | "chi2_continuity"


def _binomial_two_sided_p(b: int, c: int) -> float:
    """Exact two-sided p under Binomial(b + c, 0.5): 2 * P(X <= min(b, c)), capped at 1."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) * (0.5 ** n)
    return min(1.0, 2.0 * tail)


def mcnemar(correct_a: np.ndarray, correct_b: np.ndarray) -> McNemarResult:
    """McNemar test between two arms' aligned per-instance correctness (same instances, same order)."""
    a = np.asarray(correct_a, dtype=bool)
    b_arr = np.asarray(correct_b, dtype=bool)
    if a.shape != b_arr.shape:
        raise ComparisonError(f"correctness vectors differ in shape: {a.shape} vs {b_arr.shape}")
    b = int(np.sum(a & ~b_arr))
    c = int(np.sum(~a & b_arr))
    n_disc = b + c
    if n_disc < MCNEMAR_EXACT_BELOW:
        return McNemarResult(b, c, n_disc, float("nan"), _binomial_two_sided_p(b, c), "exact_binomial")
    stat = (abs(b - c) - 1) ** 2 / n_disc
    # Survival of χ² with 1 dof at ``stat`` equals erfc(sqrt(stat / 2)).
    p = math.erfc(math.sqrt(stat / 2.0))
    return McNemarResult(b, c, n_disc, float(stat), float(p), "chi2_continuity")


@dataclass(frozen=True)
class ArmComparison:
    """Verdict of comparing arm B against arm A on one metric (default metric M)."""

    metric: str
    arm_a: str
    arm_b: str
    n: int
    acc_a: float
    acc_b: float
    delta_pp: float
    mcnemar: McNemarResult
    alpha: float
    n_comparisons: int
    p_bonferroni: float
    significant_primary: bool     # McNemar (primary) verdict
    ci_a: dict
    ci_b: dict
    non_overlapping_ci: bool      # CI (secondary) verdict
    epsilon_pp: float
    meets_epsilon: bool           # |delta| >= pre-registered minimum effect size


def _correct_by_key(records: list[dict], bucket: str) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for r in records:
        if r["bucket"] != bucket:
            continue
        key = r["key"]
        if key in out:
            raise ComparisonError(f"duplicate instance key {key!r} within one arm")
        out[key] = bool(r["correct"])
    return out


def compare_arms(
    arm_a: list[dict],
    arm_b: list[dict],
    *,
    arm_a_name: str = "A",
    arm_b_name: str = "B",
    bucket: str = METRIC_M_BUCKET,
    alpha: float = 0.05,
    n_comparisons: int = 1,
    epsilon_pp: float = EPSILON_PP,
    n_boot: int = 2000,
    seed: int = 42,
) -> ArmComparison:
    """Adjudicate arm B vs arm A on ``bucket`` (metric M by default), DEC-0013.

    Each arm is a list of per-instance records with keys ``key``, ``correct``, ``bucket`` (the
    ``predictions.jsonl`` rows). The two arms **must** cover an identical set of instance keys in the
    bucket — McNemar is a paired test. Returns both the Bonferroni-corrected McNemar verdict
    (primary) and the non-overlapping-CI verdict (secondary).
    """
    a = _correct_by_key(arm_a, bucket)
    b = _correct_by_key(arm_b, bucket)
    if set(a) != set(b):
        only_a = sorted(set(a) - set(b))[:3]
        only_b = sorted(set(b) - set(a))[:3]
        raise ComparisonError(
            f"arms must be evaluated on identical instances in bucket {bucket!r}; "
            f"|only_A|={len(set(a) - set(b))} (e.g. {only_a}), "
            f"|only_B|={len(set(b) - set(a))} (e.g. {only_b})"
        )
    keys = sorted(a)
    ca = np.array([a[k] for k in keys], dtype=bool)
    cb = np.array([b[k] for k in keys], dtype=bool)

    mc = mcnemar(ca, cb)
    p_bonf = min(1.0, mc.p_value * n_comparisons)
    ci_a = bootstrap_ci(ca, n_boot, seed)
    ci_b = bootstrap_ci(cb, n_boot, seed + 1)
    non_overlap = ci_a["ci_high"] < ci_b["ci_low"] or ci_b["ci_high"] < ci_a["ci_low"]
    delta_pp = (cb.mean() - ca.mean()) * 100.0
    return ArmComparison(
        metric=bucket,
        arm_a=arm_a_name,
        arm_b=arm_b_name,
        n=len(keys),
        acc_a=float(ca.mean()),
        acc_b=float(cb.mean()),
        delta_pp=float(delta_pp),
        mcnemar=mc,
        alpha=alpha,
        n_comparisons=n_comparisons,
        p_bonferroni=float(p_bonf),
        significant_primary=bool(p_bonf < alpha),
        ci_a=ci_a,
        ci_b=ci_b,
        non_overlapping_ci=bool(non_overlap),
        epsilon_pp=epsilon_pp,
        meets_epsilon=bool(abs(delta_pp) >= epsilon_pp),
    )


# --------------------------------------------------------------------------------------------------
# Evaluation driver.
# --------------------------------------------------------------------------------------------------

def _build_encoder(config: ProbeConfig) -> Encoder:
    if config.encoder in ("pixel32", "pixel"):
        return PixelEncoder(downsample=config.downsample)
    if config.encoder == "jepa":
        if not config.checkpoint:
            raise ValueError("encoder 'jepa' requires a 'checkpoint' path (PA.005)")
        from ..train.pretrain import load_probe_encoder  # lazy: keeps the numpy path torch-free

        return load_probe_encoder(config.checkpoint)
    raise ValueError(f"unknown encoder {config.encoder!r} (expected pixel32 or jepa)")


def _load_instances(config: ProbeConfig) -> dict[str, list[dict]]:
    """Return {split_name: [instance-meta, ...]} for 'train' and 'eval', from whichever backend.

    Each meta dict carries: ``image`` (path relative to image_dir), ``akshara_id``, ``bucket``,
    ``seam_source``, ``font`` and a unique ``key`` used to pair arms in McNemar.
    """
    if config.index_jsonl:
        by_split: dict[str, list[dict]] = {"train": [], "eval": []}
        with Path(config.index_jsonl).open("r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                split = rec["split"]
                if split not in by_split:
                    continue
                by_split[split].append(
                    {
                        "image": rec["image"],
                        "akshara_id": rec["akshara_id"],
                        "bucket": rec["bucket"],
                        "seam_source": rec["seam_source"],
                        "font": rec["font_id"],
                        "key": rec["image"],  # filenames are unique within the augmented dataset
                    }
                )
        return by_split

    split = json.loads(Path(config.split_manifest).read_text(encoding="utf-8"))
    render = json.loads(Path(config.render_manifest).read_text(encoding="utf-8"))
    bucket_of = {a["akshara_id"]: a["bucket"] for a in split["aksharas"]}
    seam_of = {(e["akshara_id"], e["font_id"]): e["seam_source"] for e in render["entries"]}
    by_split = {"train": [], "eval": []}
    for inst in split["instances"]:
        if inst["split"] not in by_split:
            continue
        by_split[inst["split"]].append(
            {
                "image": inst["image"],
                "akshara_id": inst["akshara_id"],
                "bucket": bucket_of[inst["akshara_id"]],
                "seam_source": seam_of[(inst["akshara_id"], inst["font_id"])],
                "font": inst["font_id"],
                "key": inst["image"],
            }
        )
    return by_split


def _load_images(metas: list[dict], image_dir: Path, class_index: dict[str, int], tag: str):
    images, labels = [], []
    started = time.monotonic()
    total = len(metas)
    for i, m in enumerate(metas, start=1):
        img = np.asarray(Image.open(image_dir / m["image"]).convert("L"), dtype=np.uint8)
        images.append(img)
        labels.append(class_index[m["akshara_id"]])
        if i % _LOAD_PROGRESS_EVERY == 0 or i == total:
            el = time.monotonic() - started
            eta = el / i * (total - i)
            print(f"[akshara_probe] load {tag} {i}/{total} elapsed={el:5.1f}s eta={eta:5.1f}s", flush=True)
    return np.stack(images), np.array(labels)


def run_evaluation(config_path: Path, run_dir: Path) -> Path:
    config = ProbeConfig.from_yaml(config_path)
    image_dir = Path(config.image_dir)
    class_ids = [a.id for a in enumerate_uyirmei()]
    class_index = {aid: i for i, aid in enumerate(class_ids)}

    instances = _load_instances(config)
    train_imgs, train_y = _load_images(instances["train"], image_dir, class_index, "train")
    eval_imgs, eval_y = _load_images(instances["eval"], image_dir, class_index, "eval")

    encoder = _build_encoder(config)
    w = fit_ridge(encoder.encode(train_imgs), train_y, len(class_ids), config.ridge_lambda)
    preds = predict(encoder.encode(eval_imgs), w)

    records = [
        {
            "key": m["key"],
            "correct": bool(preds[i] == eval_y[i]),
            "bucket": m["bucket"],
            "seam_source": m["seam_source"],
            "font": m["font"],
        }
        for i, m in enumerate(instances["eval"])
    ]
    metrics = stratified_metrics(records, config.bootstrap_n, config.seed)

    if config.index_jsonl:
        data_paths = [Path(config.index_jsonl)]
    else:
        data_paths = [Path(config.split_manifest), Path(config.render_manifest)]

    run_dir.mkdir(parents=True, exist_ok=True)
    write_provenance(
        run_dir,
        config=config,
        data_hash=hash_paths(data_paths),
        run_id=run_dir.name,
        seed=config.seed,
        package_names=["numpy", "pillow", "pyyaml"],
    )
    # Per-instance correctness enables the paired McNemar across arms/seeds later (P1.001b/P1.003).
    preds_path = run_dir / "predictions.jsonl"
    with preds_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    payload = {
        "run_id": run_dir.name,
        "task": "PA.003",
        "encoder": encoder.name,
        "backend": "index" if config.index_jsonl else "manifest",
        "n_train": int(len(train_y)),
        "n_eval": int(len(eval_y)),
        "metric_M_bucket": METRIC_M_BUCKET,
        "predictions_file": preds_path.name,
        "metrics": metrics,
    }
    metrics_path = run_dir / "metrics.json"
    metrics_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    validate_run_dir(run_dir)
    m = metrics["metric_M"]
    half_width = (m["ci_high"] - m["ci_low"]) / 2.0
    print(
        f"[akshara_probe] encoder={encoder.name} backend={payload['backend']} "
        f"overall={metrics['overall']['accuracy']:.3f} "
        f"metric_M={m['accuracy']:.3f} [{m['ci_low']:.3f},{m['ci_high']:.3f}] "
        f"(n={m['n']}, ci_half_width={half_width:.4f}); metrics -> {metrics_path}",
        flush=True,
    )
    return metrics_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Akshara-recognition eval harness (metric M).")
    parser.add_argument("--config", type=Path, default=Path("configs/phase1/probe.yaml"))
    parser.add_argument("--run-dir", type=Path, default=Path("runs/pa003-probe-001"))
    args = parser.parse_args(argv)
    run_evaluation(args.config, args.run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
