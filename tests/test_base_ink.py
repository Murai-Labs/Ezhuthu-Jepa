"""Location-normalised base-ink probe tests (exploratory analysis for DEC-0016).

Validates the instrument: (1) the normaliser centres ink and drops absolute location; (2) when the base
ink encodes the sign, the probe finds it AND the consonant control is high; (3) when the base ink is
sign-invariant (the sign lives only in the masked mark), sign accuracy falls to ~chance while the
consonant control stays high — i.e. a near-chance sign result means "no signal", not "broke the image".
"""

import json

import numpy as np
import pytest
from PIL import Image

from ezhuthu_jepa.eval.base_ink_probe import (
    BaseInkProbeConfig,
    location_normalised_base,
    run_base_ink_probe,
)
from ezhuthu_jepa.provenance import validate_run_dir

N_CONS, N_SIGN = 3, 3


def test_normaliser_centres_ink_and_drops_location():
    img = np.zeros((96, 96), dtype=np.uint8)
    img[5:15, 5:15] = 255                                   # a block in the top-left corner
    out = location_normalised_base(img, None, ink_threshold=32, canvas=64, margin=4)
    assert out.shape == (64, 64)
    ys, xs = np.where(out > 32)
    cy, cx = ys.mean(), xs.mean()
    assert 24 < cy < 40 and 24 < cx < 40                    # ink recentred to the middle
    assert location_normalised_base(np.zeros((96, 96), np.uint8), None, 32, 64, 4).sum() == 0


def _template(cons, sign, encode_sign):
    # A fixed border frame guarantees a constant ink bbox, so crop+letterbox is class-invariant and the
    # interior marks (which encode class by SHAPE, not location) survive normalisation.
    t = np.zeros((24, 24), dtype=np.uint8)
    t[2, 2:22] = t[21, 2:22] = t[2:22, 2] = t[2:22, 21] = 255       # frame
    t[5:9, 4 + cons * 4 : 8 + cons * 4] = 255                       # consonant block (upper interior)
    if encode_sign:
        t[14:18, 4 + sign * 4 : 8 + sign * 4] = 255                 # sign block (lower interior)
    return t


def _index(tmp_path, encode_sign_in_base, n_per=8):
    rng = np.random.default_rng(0)
    lines = []
    for split in ("train", "eval"):
        for cons in range(N_CONS):
            for sign in range(N_SIGN):
                for _ in range(n_per):
                    img = np.zeros((96, 96), dtype=np.uint8)
                    rx, ry = int(rng.integers(0, 40)), int(rng.integers(0, 40))   # random location
                    img[ry : ry + 24, rx : rx + 24] = _template(cons, sign, encode_sign_in_base)
                    if encode_sign_in_base:
                        bbox = [84, 84, 92, 92]                                    # empty → masks nothing
                    else:
                        y0 = 10 + sign * 20                                        # sign lives ONLY here
                        bbox = [80, y0, 88, y0 + 8]
                        img[y0 : y0 + 8, 80:88] = 255
                    name = f"c{cons}s{sign}_{split}{len(lines)}.png"
                    Image.fromarray(img, mode="L").save(tmp_path / name)
                    lines.append({
                        "sign_id": f"s{sign}", "base_id": f"c{cons}",
                        "seam_source": "diff" if encode_sign_in_base else "glyph",
                        "font_id": "noto", "split": split, "image": name, "seam_bbox": bbox,
                    })
    (tmp_path / "index.jsonl").write_text("\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")
    return tmp_path


def _run(tmp_path, idx, name):
    import yaml

    cfg = {"index_jsonl": str(idx / "index.jsonl"), "image_dir": str(idx), "bootstrap_n": 200,
           "downsample": 16, "canvas": 32, "margin": 2}
    p = tmp_path / f"{name}.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return json.loads(run_base_ink_probe(p, tmp_path / name).read_text(encoding="utf-8"))


def test_base_ink_finds_sign_when_base_encodes_it(tmp_path):
    m = _run(tmp_path, _index(tmp_path, encode_sign_in_base=True), "comp")
    assert m["base_ink_to_sign"]["above_chance"] is True
    assert m["base_ink_to_consonant_control"]["normalisation_preserved_ink"] is True
    validate_run_dir(tmp_path / "comp")


def test_base_ink_near_chance_when_base_is_sign_invariant(tmp_path):
    m = _run(tmp_path, _index(tmp_path, encode_sign_in_base=False), "sep")
    # base carries no sign signal → sign accuracy ~ chance, but the consonant control stays high
    assert m["base_ink_to_sign"]["above_chance"] is False
    assert m["base_ink_to_consonant_control"]["overall"]["accuracy"] > 2 * (1.0 / N_CONS)
