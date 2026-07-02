"""Location-normalised base-ink composition probe (exploratory; sharpens the K2 caveat, DEC-0016).

**Not a gate.** The K2 probe (`base_to_sign_probe`) showed that base→sign predictability is dominated by
sign *location* (where the mask is), not base-ink shape. This probe isolates the **pure compositional**
signal: does the consonant-base *ink* predict which vowel-sign composes with it, once absolute location
and scale are removed?

Normalisation: mask the sign region, find the ink bounding box of the remaining base, crop, and letterbox
it (aspect-preserving) into a centred canvas. That erases *where* the sign was and *how big* the glyph is,
leaving only the base ink's shape. Then two linear probes on that canonical image:

- **base-ink → SIGN** (the question): if the base ink carries genuine base×sign composition it beats
  chance — expected near chance for cleanly-separable ('glyph') forms (bare consonant is sign-invariant)
  and above chance only for ligature ('diff') forms if the reshaping is sign-specific.
- **base-ink → CONSONANT** (positive control): must stay high. It proves the normalisation preserved real
  ink shape, so a near-chance *sign* result means "no compositional signal", not "we destroyed the image".

Read the two together: high consonant accuracy + near-chance sign accuracy = the base ink does **not**
linearly encode the sign; the naive K2 signal was location. Above-chance sign accuracy in the 'diff'
stratum = real (if weak) compositional structure a learned encoder might amplify. Either way this is
evidence for the LAUNCH-A/G1 K1-risk read, not a gate verdict.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, fields
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

from ..provenance import hash_paths, validate_run_dir, write_provenance
from .akshara_probe import PixelEncoder, _stratify, bootstrap_ci, fit_ridge, predict

_LOAD_PROGRESS_EVERY = 4000


@dataclass(frozen=True)
class BaseInkProbeConfig:
    index_jsonl: str
    image_dir: str
    ridge_lambda: float = 1.0
    bootstrap_n: int = 2000
    seed: int = 42
    downsample: int = 32
    ink_threshold: int = 32   # grayscale cutoff for the base ink bounding box
    canvas: int = 64          # side of the centred canonical canvas
    margin: int = 4           # blank border kept inside the canvas

    @classmethod
    def from_yaml(cls, path: str | Path) -> "BaseInkProbeConfig":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        allowed = {f.name for f in fields(cls)}
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"unknown base-ink-probe-config key(s): {sorted(unknown)}")
        return cls(**data)


def location_normalised_base(
    image: np.ndarray, seam_bbox, ink_threshold: int, canvas: int, margin: int
) -> np.ndarray:
    """Mask the sign, crop to the remaining base ink, and letterbox it centred into a fixed canvas.

    Removes absolute location and scale (aspect-preserving), leaving only the base ink's shape.
    Returns an all-zero canvas if no base ink survives the mask.
    """
    base = image.copy()
    if seam_bbox is not None:
        x0, y0, x1, y1 = seam_bbox
        base[y0:y1, x0:x1] = 0

    out = np.zeros((canvas, canvas), dtype=np.uint8)
    ys, xs = np.where(base > ink_threshold)
    if xs.size == 0:
        return out
    crop = base[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    ch, cw = crop.shape
    target = canvas - 2 * margin
    scale = target / max(ch, cw)
    nh, nw = max(1, round(ch * scale)), max(1, round(cw * scale))
    resized = np.asarray(Image.fromarray(crop).resize((nw, nh), Image.BILINEAR), dtype=np.uint8)
    oy, ox = (canvas - nh) // 2, (canvas - nw) // 2
    out[oy:oy + nh, ox:ox + nw] = resized
    return out


def _load(config: BaseInkProbeConfig) -> dict[str, list[dict]]:
    image_dir = Path(config.image_dir)
    by_split: dict[str, list[dict]] = {"train": [], "eval": []}
    started = time.monotonic()
    n = 0
    with Path(config.index_jsonl).open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec["split"] not in by_split:
                continue
            bbox = rec["seam_bbox"]
            if bbox is None:      # inherent-'a' forms have no sign to compose — degenerate, excluded
                continue
            image = np.asarray(Image.open(image_dir / rec["image"]).convert("L"), dtype=np.uint8)
            norm = location_normalised_base(
                image, tuple(bbox), config.ink_threshold, config.canvas, config.margin
            )
            by_split[rec["split"]].append(
                {
                    "sign_id": rec["sign_id"],
                    "base_id": rec["base_id"],
                    "seam_source": rec["seam_source"],
                    "font": rec["font_id"],
                    "norm": norm,
                }
            )
            n += 1
            if n % _LOAD_PROGRESS_EVERY == 0:
                el = time.monotonic() - started
                print(f"[base_ink] normalised {n} instances elapsed={el:5.1f}s", flush=True)
    print(f"[base_ink] loaded {n} instances total", flush=True)
    return by_split


def _probe(train, eval_, target_key: str, cfg: BaseInkProbeConfig):
    """Fit a ridge probe from the normalised base ink to `target_key`; return (correct, majority_acc)."""
    classes = sorted({r[target_key] for r in train} | {r[target_key] for r in eval_})
    index = {c: i for i, c in enumerate(classes)}
    y_train = np.array([index[r[target_key]] for r in train])
    y_eval = np.array([index[r[target_key]] for r in eval_])
    encoder = PixelEncoder(downsample=cfg.downsample)
    x_train = encoder.encode(np.stack([r["norm"] for r in train]))
    x_eval = encoder.encode(np.stack([r["norm"] for r in eval_]))
    w = fit_ridge(x_train, y_train, len(classes), cfg.ridge_lambda)
    correct = predict(x_eval, w) == y_eval
    majority = int(np.bincount(y_train, minlength=len(classes)).argmax())
    return correct, float((y_eval == majority).mean()), len(classes)


def run_base_ink_probe(config_path: Path, run_dir: Path) -> Path:
    cfg = BaseInkProbeConfig.from_yaml(config_path)
    data = _load(cfg)
    train, eval_ = data["train"], data["eval"]
    if not train or not eval_:
        raise RuntimeError("base-ink probe: empty train or eval split")

    sign_correct, sign_majority, n_signs = _probe(train, eval_, "sign_id", cfg)
    cons_correct, cons_majority, n_cons = _probe(train, eval_, "base_id", cfg)

    sign_overall = bootstrap_ci(sign_correct, cfg.bootstrap_n, cfg.seed)
    cons_overall = bootstrap_ci(cons_correct, cfg.bootstrap_n, cfg.seed + 1)
    sign_records = [
        {"correct": bool(c), "seam_source": r["seam_source"], "font": r["font"]}
        for c, r in zip(sign_correct, eval_)
    ]
    sign_chance, cons_chance = 1.0 / n_signs, 1.0 / n_cons

    control_ok = cons_overall["ci_low"] > 2 * cons_chance     # normalisation preserved real ink shape
    sign_above_chance = sign_overall["ci_low"] > sign_chance

    run_dir.mkdir(parents=True, exist_ok=True)
    write_provenance(
        run_dir,
        config=cfg,
        data_hash=hash_paths([Path(cfg.index_jsonl)]),
        run_id=run_dir.name,
        seed=cfg.seed,
        package_names=["numpy", "pillow", "pyyaml"],
    )
    payload = {
        "run_id": run_dir.name,
        "task": "P1.002b (exploratory, non-gating)",
        "encoder": f"pixel{cfg.downsample}",
        "n_train": len(train),
        "n_eval": len(eval_),
        "normalisation": {"canvas": cfg.canvas, "margin": cfg.margin, "ink_threshold": cfg.ink_threshold,
                          "removes": "absolute location + scale; preserves base-ink shape"},
        "base_ink_to_sign": {
            "overall": sign_overall,
            "chance": sign_chance,
            "majority": sign_majority,
            "above_chance": bool(sign_above_chance),
            "by_seam_source": _stratify(sign_records, "seam_source", cfg.seed, cfg.bootstrap_n),
        },
        "base_ink_to_consonant_control": {
            "overall": cons_overall,
            "chance": cons_chance,
            "majority": cons_majority,
            "normalisation_preserved_ink": bool(control_ok),
        },
        "interpretation": (
            "High consonant accuracy + near-chance sign accuracy ⇒ the base ink does NOT linearly encode "
            "the sign; the naive K2 signal was location (DEC-0016). Above-chance sign accuracy in the "
            "'diff' (ligature) stratum ⇒ real but likely weak compositional structure a learned encoder "
            "may amplify. Exploratory — informs the K1 risk read, not a gate."
        ),
    }
    metrics_path = run_dir / "metrics.json"
    metrics_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    validate_run_dir(run_dir)
    s, c = sign_overall, cons_overall
    by = payload["base_ink_to_sign"]["by_seam_source"]
    print(
        f"[base_ink] sign={s['accuracy']:.3f} [{s['ci_low']:.3f},{s['ci_high']:.3f}] "
        f"(chance {sign_chance:.3f}) | glyph={by.get('glyph', {}).get('accuracy', float('nan')):.3f} "
        f"diff={by.get('diff', {}).get('accuracy', float('nan')):.3f} || "
        f"consonant_control={c['accuracy']:.3f} (chance {cons_chance:.3f}) -> {metrics_path}",
        flush=True,
    )
    return metrics_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Location-normalised base-ink composition probe (exploratory).")
    parser.add_argument("--config", type=Path, default=Path("configs/phase1/base_ink_probe.yaml"))
    parser.add_argument("--run-dir", type=Path, default=Path("runs/phase1-baseink-001"))
    args = parser.parse_args(argv)
    run_base_ink_probe(args.config, args.run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
