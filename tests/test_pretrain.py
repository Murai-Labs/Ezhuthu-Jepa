"""Pretraining-loop tests (TASK PA.005).

Self-contained: a tiny synthetic augmented index is built in a tmp dir (no gitignored data needed),
then the loop is run on CPU/fp32 for a few steps. Verifies (AC1) an end-to-end run writes
provenance + metrics + a loadable encoder, (AC2) the masked-token count is identical across
objectives, and that the trained encoder plugs into the probe as `encoder: jepa`.
"""

import json

import numpy as np
import pytest

from ezhuthu_jepa.data.grapheme import enumerate_uyirmei
from ezhuthu_jepa.provenance import validate_run_dir
from ezhuthu_jepa.train import pretrain as P


def _tiny_config(tmp_path, objective, **overrides):
    return P.PretrainConfig(
        objective=objective, seed=0, mask_ratio=0.25,
        index_jsonl=str(tmp_path / "index.jsonl"), image_dir=str(tmp_path),
        limit_instances=0,
        img_size=96, patch_size=8, embed_dim=32, depth=2, num_heads=2,
        pred_dim=16, pred_depth=1, pred_heads=2,
        batch_size=8, max_steps=3, warmup_steps=1, log_every=2,
        device="cpu", amp_dtype="fp32",
        **overrides,
    )


@pytest.fixture()
def synthetic_index(tmp_path):
    """~24 train + a few eval synthetic 96x96 instances; most carry a seam_bbox, a few are no-sign."""
    from PIL import Image

    ids = [a.id for a in enumerate_uyirmei()][:8]
    rng = np.random.default_rng(0)
    lines = []
    for split, n_per in (("train", 3), ("eval", 1)):
        for aid in ids:
            for k in range(n_per):
                img = rng.integers(0, 256, (96, 96), dtype=np.uint8)
                name = f"{aid}__{split}{k}.png"
                Image.fromarray(img, mode="L").save(tmp_path / name)
                # one class per set gets no seam (inherent-'a' analogue)
                bbox = None if aid == ids[0] else [40, 40, 60, 64]
                lines.append({
                    "akshara_id": aid, "base_id": aid, "sign_id": "x",
                    "font_id": "noto", "split": split, "aug_index": k, "image": name,
                    "seam_source": "none" if bbox is None else "glyph",
                    "seam_bbox": bbox, "bucket": "q1_bottom",
                })
    (tmp_path / "index.jsonl").write_text(
        "\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8"
    )
    return tmp_path


@pytest.mark.parametrize("objective", ["seam_jepa", "block_jepa", "mae_seam"])
def test_pretrain_smoke_runs_end_to_end_per_objective(synthetic_index, tmp_path, objective):
    cfg = _tiny_config(synthetic_index, objective)
    run_dir = tmp_path / f"run_{objective}"
    metrics_path = P.train(cfg, run_dir)

    validate_run_dir(run_dir)                       # five provenance identifiers present (AC1)
    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert payload["objective"] == objective
    assert payload["steps"] == cfg.max_steps
    assert np.isfinite(payload["final_loss"])
    assert (run_dir / "encoder.pt").is_file()


def test_pretrain_smoke_excludes_no_sign_instances(synthetic_index):
    cfg = _tiny_config(synthetic_index, "seam_jepa")
    kept = P.load_train_instances(cfg)
    # 8 classes x 3 train each = 24; the 1 no-sign class (3 instances) is dropped -> 21.
    assert len(kept) == 21
    assert all(inst.seam_center is not None for inst in kept)


def test_pretrain_smoke_mask_ratio_identical_across_objectives(synthetic_index):
    """AC2: the masked-token count is fixed by config, identical for seam and block placements."""
    cfg = P.PretrainConfig(
        objective="seam_jepa", seed=0, mask_ratio=0.25,
        index_jsonl=str(synthetic_index / "index.jsonl"), image_dir=str(synthetic_index),
    )
    batch = P.load_train_instances(cfg)[:6]
    rng = np.random.default_rng(1)
    seam_mask, seam_vis = P._mask_indices_for_batch(batch, cfg, seam_centred=True, rng=rng)
    block_mask, block_vis = P._mask_indices_for_batch(batch, cfg, seam_centred=False, rng=rng)
    assert seam_mask.shape == block_mask.shape == (6, cfg.n_mask)
    assert seam_vis.shape == block_vis.shape == (6, cfg.n_tokens - cfg.n_mask)
    # every row is a valid partition of the token grid (no overlap, full cover)
    for m, v in ((seam_mask, seam_vis), (block_mask, block_vis)):
        for i in range(6):
            assert set(m[i]).isdisjoint(set(v[i]))
            assert set(m[i]) | set(v[i]) == set(range(cfg.n_tokens))


def test_pretrain_smoke_encoder_loads_into_probe(synthetic_index, tmp_path):
    cfg = _tiny_config(synthetic_index, "seam_jepa")
    run_dir = tmp_path / "run_probe"
    P.train(cfg, run_dir)
    enc = P.load_probe_encoder(str(run_dir / "encoder.pt"), device="cpu")
    feats = enc.encode(np.stack([np.zeros((96, 96), np.uint8), np.full((96, 96), 255, np.uint8)]))
    assert feats.shape == (2, cfg.embed_dim)
    assert np.isfinite(feats).all()


def test_pretrain_rejects_unknown_objective(synthetic_index):
    with pytest.raises(ValueError):
        _tiny_config(synthetic_index, "not_an_objective")
