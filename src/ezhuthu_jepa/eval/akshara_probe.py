"""Akshara-recognition evaluation harness — metric M with bootstrap CIs (TASK PA.003).

Given a **frozen encoder**, fit a linear probe (numpy ridge on one-hot targets) on the train
instances of the PA.002 split and evaluate top-1 accuracy on the eval instances, reported:
- overall,
- per frequency bucket (the bottom quartile is **metric M**),
- per `seam_source` (glyph / diff / none) and per font  (DEC-0006),
each with a 95 % bootstrap CI. Writes `metrics.json` + `provenance.json` to the run dir.

The encoder is a plug-in (Protocol): a `PixelEncoder` baseline runs today; the I-JEPA encoder from
PA.005 drops in unchanged. The metric machinery here is frozen *before* the K1/K3 sweep so the
comparison is judged on a fixed metric (AGENTS.md §2.6).
"""

from __future__ import annotations

import argparse
import json
import sys
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


@dataclass(frozen=True)
class ProbeConfig:
    split_manifest: str
    render_manifest: str
    image_dir: str
    ridge_lambda: float = 1.0
    bootstrap_n: int = 2000
    seed: int = 42
    encoder: str = "pixel32"
    downsample: int = 32

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


def _build_encoder(config: ProbeConfig) -> Encoder:
    if config.encoder in ("pixel32", "pixel"):
        return PixelEncoder(downsample=config.downsample)
    raise ValueError(f"unknown encoder {config.encoder!r} (PA.005 registers the JEPA encoder)")


def run_evaluation(config_path: Path, run_dir: Path) -> Path:
    config = ProbeConfig.from_yaml(config_path)
    split = json.loads(Path(config.split_manifest).read_text(encoding="utf-8"))
    render = json.loads(Path(config.render_manifest).read_text(encoding="utf-8"))
    image_dir = Path(config.image_dir)

    bucket_of = {a["akshara_id"]: a["bucket"] for a in split["aksharas"]}
    seam_of = {(e["akshara_id"], e["font_id"]): e["seam_source"] for e in render["entries"]}
    class_ids = [a.id for a in enumerate_uyirmei()]
    class_index = {aid: i for i, aid in enumerate(class_ids)}

    def load(split_name: str):
        images, labels, meta = [], [], []
        for inst in split["instances"]:
            if inst["split"] != split_name:
                continue
            img = np.asarray(Image.open(image_dir / inst["image"]).convert("L"), dtype=np.uint8)
            images.append(img)
            labels.append(class_index[inst["akshara_id"]])
            meta.append(inst)
        return np.stack(images), np.array(labels), meta

    encoder = _build_encoder(config)
    train_imgs, train_y, _ = load("train")
    eval_imgs, eval_y, eval_meta = load("eval")

    w = fit_ridge(encoder.encode(train_imgs), train_y, len(class_ids), config.ridge_lambda)
    preds = predict(encoder.encode(eval_imgs), w)

    records = [
        {
            "correct": bool(preds[i] == eval_y[i]),
            "bucket": bucket_of[m["akshara_id"]],
            "seam_source": seam_of[(m["akshara_id"], m["font_id"])],
            "font": m["font_id"],
        }
        for i, m in enumerate(eval_meta)
    ]
    metrics = stratified_metrics(records, config.bootstrap_n, config.seed)

    run_dir.mkdir(parents=True, exist_ok=True)
    write_provenance(
        run_dir,
        config=config,
        data_hash=hash_paths([Path(config.split_manifest), Path(config.render_manifest)]),
        run_id=run_dir.name,
        seed=config.seed,
        package_names=["numpy", "pillow", "pyyaml"],
    )
    payload = {
        "run_id": run_dir.name,
        "task": "PA.003",
        "encoder": encoder.name,
        "n_train": int(len(train_y)),
        "n_eval": int(len(eval_y)),
        "metric_M_bucket": METRIC_M_BUCKET,
        "metrics": metrics,
    }
    metrics_path = run_dir / "metrics.json"
    metrics_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    validate_run_dir(run_dir)
    m = metrics["metric_M"]
    print(
        f"[akshara_probe] encoder={encoder.name} overall={metrics['overall']['accuracy']:.3f} "
        f"metric_M={m['accuracy']:.3f} [{m['ci_low']:.3f},{m['ci_high']:.3f}] (n={m['n']}); "
        f"metrics -> {metrics_path}",
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
