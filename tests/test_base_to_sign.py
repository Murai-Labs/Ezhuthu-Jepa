"""K2 premise-probe tests (TASK P1.002).

Self-contained: a synthetic index where the BASE region encodes the sign (a sign-specific ink block
outside the seam bbox) but the mask GEOMETRY does not (the seam bbox is fixed across signs). So the
base-region probe should beat both the majority baseline and the geometry control (premise holds),
while the geometry control should not — exactly the discrimination the real gate must make.
"""

import json

import numpy as np
import pytest
from PIL import Image

from ezhuthu_jepa.eval.base_to_sign_probe import (
    K2ProbeConfig,
    base_region_image,
    geometry_image,
    run_k2_probe,
)
from ezhuthu_jepa.provenance import validate_run_dir

FIXED_BBOX = [40, 40, 56, 56]        # identical for every sign → geometry carries no sign signal
SIGNS = ["aa", "i", "u"]


def _make_index(tmp_path, n_per=20, with_no_sign=True):
    rng = np.random.default_rng(0)
    lines = []
    for split in ("train", "eval"):
        for j, sign in enumerate(SIGNS):
            for k in range(n_per):
                img = rng.integers(0, 30, (96, 96), dtype=np.uint8)          # dim background
                img[70:80, 5 + j * 12 : 15 + j * 12] = 230                   # sign-specific base block
                name = f"{sign}_{split}{k}.png"
                Image.fromarray(img, mode="L").save(tmp_path / name)
                lines.append({
                    "sign_id": sign, "seam_source": "diff" if j else "glyph",
                    "font_id": "noto", "split": split, "image": name,
                    "seam_bbox": list(FIXED_BBOX),
                })
        if with_no_sign:
            for k in range(3):                                               # inherent-'a' (no sign region)
                img = rng.integers(0, 30, (96, 96), dtype=np.uint8)
                name = f"a_{split}{k}.png"
                Image.fromarray(img, mode="L").save(tmp_path / name)
                lines.append({"sign_id": "a", "seam_source": "none", "font_id": "noto",
                              "split": split, "image": name, "seam_bbox": None})
    (tmp_path / "index.jsonl").write_text("\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")
    return tmp_path


def test_base_region_image_masks_only_the_bbox():
    img = np.full((96, 96), 200, dtype=np.uint8)
    out = base_region_image(img, tuple(FIXED_BBOX))
    assert (out[40:56, 40:56] == 0).all()
    assert (out[0:40, 0:40] == 200).all()         # outside the bbox untouched
    assert base_region_image(img, None).tolist() == img.tolist()   # no sign → unchanged


def test_geometry_image_is_blank_plus_rectangle():
    g = geometry_image((96, 96), tuple(FIXED_BBOX))
    assert (g[40:56, 40:56] == 255).all()
    assert g.sum() == 255 * 16 * 16               # only the rectangle is lit
    assert geometry_image((96, 96), None).sum() == 0


def test_base_to_sign_premise_holds_when_base_encodes_sign(tmp_path):
    idx = _make_index(tmp_path)
    cfg = K2ProbeConfig(index_jsonl=str(idx / "index.jsonl"), image_dir=str(idx), bootstrap_n=300)
    metrics = json.loads(run_k2_probe(_write_cfg(tmp_path, cfg), tmp_path / "run").read_text(encoding="utf-8"))
    assert metrics["n_sign_classes"] == 3          # 'a'/no-sign excluded
    assert metrics["premise"]["holds"] is True
    assert metrics["premise"]["base_beats_chance"] is True
    assert metrics["premise"]["base_beats_majority"] is True
    base = metrics["base_region"]["overall"]["accuracy"]
    geom = metrics["signal_attribution"]["sign_location_control"]["overall"]["accuracy"]
    # here the seam bbox is fixed across signs, so geometry carries NO sign signal → base beats it
    assert base > geom
    assert metrics["signal_attribution"]["base_beats_location_control"] is True
    assert base > metrics["majority_baseline"]["accuracy"]
    validate_run_dir(tmp_path / "run")


def test_base_to_sign_excludes_no_sign_forms(tmp_path):
    idx = _make_index(tmp_path)
    cfg = K2ProbeConfig(index_jsonl=str(idx / "index.jsonl"), image_dir=str(idx),
                        bootstrap_n=100, exclude_no_sign=True)
    metrics = json.loads(run_k2_probe(_write_cfg(tmp_path, cfg), tmp_path / "run2").read_text(encoding="utf-8"))
    assert metrics["n_train"] == len(SIGNS) * 20   # 3 no-sign train instances dropped
    assert "a" not in metrics["sign_classes"]


def _write_cfg(tmp_path, cfg: K2ProbeConfig):
    import yaml

    p = tmp_path / f"cfg_{abs(hash(cfg))}.yaml"
    p.write_text(yaml.safe_dump({
        "index_jsonl": cfg.index_jsonl, "image_dir": cfg.image_dir, "ridge_lambda": cfg.ridge_lambda,
        "bootstrap_n": cfg.bootstrap_n, "seed": cfg.seed, "downsample": cfg.downsample,
        "exclude_no_sign": cfg.exclude_no_sign,
    }), encoding="utf-8")
    return p
