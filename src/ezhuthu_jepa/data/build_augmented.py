"""Build the augmented, font-held-out dataset + frozen split (TASK PA.4b.2).

Generates ~n_train augmented instances per akshara from the **train font(s)** and ~n_eval from the
**held-out eval font(s)** (DEC-0013), each with its `seam_bbox` transformed in lockstep (augment.py).
Held-out font means the eval-font distribution never appears in training (pretraining or probe), so
metric M measures real generalization, not augmentation memorization. The eval set is seed-frozen, so
it is identical across every future arm/seed — the requirement for paired McNemar.

Outputs:
- images + a full per-instance index (`index.jsonl`, every seam_bbox) under the gitignored out dir —
  regenerable from the committed config + seeds, so they are not committed;
- a compact **committed** `split-manifest.json` (recipe + provenance ref + summary + per-class
  bucket/seam_source) and `provenance.json` under the run dir.

Aug index 0 is the clean (un-augmented) render; 1..n-1 are augmented with per-instance seeds.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import zlib
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import numpy as np
from PIL import Image

from ..provenance import hash_paths, validate_run_dir, write_provenance
from .augment import AugmentConfig, augment_image
from .grapheme import enumerate_uyirmei
from .render import RenderConfig, TamilRenderer

_PROGRESS_EVERY = 4000


@dataclass(frozen=True)
class AugmentedConfig:
    render_config: str
    split_manifest: str
    train_fonts: tuple[str, ...] = ("noto",)
    eval_fonts: tuple[str, ...] = ("nirmala",)
    n_train_per_class: int = 100
    n_eval_per_class: int = 150
    out_dir: str = "data/rendered/augmented"
    seed: int = 42

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AugmentedConfig":
        import yaml

        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        allowed = {f.name for f in fields(cls)}
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"unknown augment-config key(s): {sorted(unknown)}")
        for k in ("train_fonts", "eval_fonts"):
            if k in data:
                data[k] = tuple(data[k])
        return cls(**data)


def _rng(seed: int, *parts) -> np.random.Generator:
    key = ":".join([str(seed), *map(str, parts)])
    return np.random.default_rng(zlib.crc32(key.encode("utf-8")))


def build(config_path: Path, run_dir: Path) -> Path:
    return build_from_config(AugmentedConfig.from_yaml(config_path), run_dir)


def build_from_config(config: AugmentedConfig, run_dir: Path) -> Path:
    render_config = RenderConfig.from_yaml(config.render_config)
    split = json.loads(Path(config.split_manifest).read_text(encoding="utf-8"))
    bucket_of = {a["akshara_id"]: a["bucket"] for a in split["aksharas"]}

    renderers = {f.id: TamilRenderer(f, render_config) for f in render_config.fonts if f.available}
    for needed in (*config.train_fonts, *config.eval_fonts):
        if needed not in renderers:
            raise SystemExit(f"required font {needed!r} not available (have {sorted(renderers)})")

    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    aug_cfg = AugmentConfig()
    aksharas = enumerate_uyirmei()

    plan = [("train", config.train_fonts, config.n_train_per_class),
            ("eval", config.eval_fonts, config.n_eval_per_class)]
    total = sum(len(aksharas) * len(fonts) * n for _, fonts, n in plan)

    index_path = out_dir / "index.jsonl"
    per_class_seam = {}  # akshara_id -> {"train": seam_source, "eval": seam_source}
    counts = {"train": 0, "eval": 0}
    started = time.monotonic()
    done = 0
    with index_path.open("w", encoding="utf-8") as index_f:
        for split_name, fonts, n_per in plan:
            for font_id in fonts:
                renderer = renderers[font_id]
                for aksh in aksharas:
                    base = renderer.render(aksh)
                    per_class_seam.setdefault(aksh.id, {})[split_name] = base.seam_source
                    for aug_index in range(n_per):
                        if aug_index == 0:
                            img, bbox = base.image, base.seam_bbox
                        else:
                            img, bbox = augment_image(
                                base.image, base.seam_bbox, aug_cfg,
                                _rng(config.seed, aksh.id, font_id, split_name, aug_index),
                            )
                        name = f"{aksh.id}__{font_id}__{split_name}{aug_index:03d}.png"
                        Image.fromarray(img, mode="L").save(out_dir / name)
                        index_f.write(json.dumps({
                            "akshara_id": aksh.id, "base_id": aksh.base_id, "sign_id": aksh.sign_id,
                            "font_id": font_id, "split": split_name, "aug_index": aug_index,
                            "image": name, "seam_source": base.seam_source,
                            "seam_bbox": list(bbox) if bbox is not None else None,
                            "bucket": bucket_of[aksh.id],
                        }, ensure_ascii=False) + "\n")
                        counts[split_name] += 1
                        done += 1
                        if done % _PROGRESS_EVERY == 0 or done == total:
                            el = time.monotonic() - started
                            print(f"[build_augmented] {done}/{total} ({split_name}/{font_id}) "
                                  f"elapsed={el:5.1f}s eta={el/done*(total-done):5.1f}s", flush=True)

    # Held-out invariant: train and eval fonts must be disjoint.
    if set(config.train_fonts) & set(config.eval_fonts):
        raise SystemExit("train_fonts and eval_fonts overlap; held-out-font design violated")

    run_dir.mkdir(parents=True, exist_ok=True)
    write_provenance(
        run_dir,
        config=config,
        data_hash=hash_paths([Path(config.render_config), Path(config.split_manifest),
                              *[Path(f.path) for f in render_config.fonts if f.available]]),
        run_id=run_dir.name,
        seed=config.seed,
        package_names=["numpy", "pillow", "pyyaml"],
    )
    manifest = {
        "run_id": run_dir.name,
        "task": "PA.4b.2",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "provenance_ref": "provenance.json",
        "design": {
            "train_fonts": list(config.train_fonts), "eval_fonts": list(config.eval_fonts),
            "n_train_per_class": config.n_train_per_class, "n_eval_per_class": config.n_eval_per_class,
            "seed": config.seed, "aug_config": asdict(aug_cfg), "aug_index_0": "clean (un-augmented)",
        },
        "index_file": (out_dir / "index.jsonl").as_posix(),
        "counts": {**counts, "n_classes": len(aksharas)},
        "buckets": split["buckets"],
        "bottom_quartile": split["bottom_quartile"],
        "per_class": [
            {"akshara_id": a.id, "base_id": a.base_id, "sign_id": a.sign_id,
             "bucket": bucket_of[a.id],
             "seam_source_train": per_class_seam[a.id].get("train"),
             "seam_source_eval": per_class_seam[a.id].get("eval")}
            for a in aksharas
        ],
    }
    manifest_path = run_dir / "split-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    validate_run_dir(run_dir)
    print(f"[build_augmented] {counts['train']} train / {counts['eval']} eval instances; "
          f"index {index_path}; manifest {manifest_path}", flush=True)
    return manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the augmented font-holdout dataset (PA.4b.2).")
    parser.add_argument("--config", type=Path, default=Path("configs/phase1/augment.yaml"))
    parser.add_argument("--run-dir", type=Path, default=Path("runs/pa4b-augment-001"))
    args = parser.parse_args(argv)
    build(args.config, args.run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
