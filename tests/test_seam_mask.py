"""Seam/block masking tests (TASK PA.004): seam covers the sign; block matches ratio elsewhere."""

import numpy as np
import pytest

from ezhuthu_jepa.masking.seam import (
    BLOCK,
    SEAM,
    MaskError,
    apply_mask,
    make_mask,
    mask_for_entry,
    matched_block_mask,
    seam_mask,
)

SHAPE = (96, 96)


def test_seam_mask_covers_bbox_and_leaves_base():
    bbox = (10, 20, 30, 50)
    m = seam_mask(SHAPE, bbox)
    assert m[20:50, 10:30].all()          # sign region masked
    assert not m[0:20, :].any()           # base above the sign is visible
    assert m.sum() == (30 - 10) * (50 - 20)


def test_no_sign_gives_empty_mask():
    spec = make_mask(SEAM, SHAPE, None, "none", np.random.default_rng(0))
    assert spec.mask.sum() == 0
    assert spec.has_sign is False
    assert spec.mask_ratio == 0.0


def test_block_matches_seam_ratio_and_shape():
    bbox = (5, 5, 25, 45)
    rng = np.random.default_rng(1)
    block = matched_block_mask(SHAPE, bbox, rng)
    assert block.sum() == (25 - 5) * (45 - 5)     # same number of masked pixels
    ys, xs = np.where(block)
    # contiguous rectangle of the seam's dimensions
    assert xs.max() - xs.min() + 1 == 25 - 5
    assert ys.max() - ys.min() + 1 == 45 - 5


def test_seam_and_block_have_matched_ratio():
    bbox = (8, 8, 40, 60)
    rng = np.random.default_rng(2)
    s = make_mask(SEAM, SHAPE, bbox, "glyph", rng)
    b = make_mask(BLOCK, SHAPE, bbox, "glyph", rng)
    assert s.mask_ratio == b.mask_ratio       # K1 holds mask ratio fixed
    assert s.kind == SEAM and b.kind == BLOCK


def test_block_location_varies_from_seam_across_seeds():
    bbox = (10, 10, 30, 30)
    seam = seam_mask(SHAPE, bbox)
    differ = any(
        not np.array_equal(matched_block_mask(SHAPE, bbox, np.random.default_rng(s)), seam)
        for s in range(5)
    )
    assert differ  # random placement moves the block off the seam


def test_block_is_deterministic_given_rng_seed():
    bbox = (10, 10, 30, 30)
    a = matched_block_mask(SHAPE, bbox, np.random.default_rng(7))
    b = matched_block_mask(SHAPE, bbox, np.random.default_rng(7))
    assert np.array_equal(a, b)


def test_apply_mask_hides_only_masked_region():
    img = np.full(SHAPE, 200, dtype=np.uint8)
    m = seam_mask(SHAPE, (0, 0, 10, 10))
    out = apply_mask(img, m, fill=0)
    assert (out[0:10, 0:10] == 0).all()
    assert (out[10:, 10:] == 200).all()
    assert img[0, 0] == 200  # original untouched (copy)


def test_mask_for_entry_reads_bbox_and_seam_source():
    img = np.zeros(SHAPE, dtype=np.uint8)
    entry = {"seam_bbox": [4, 6, 20, 30], "seam_source": "glyph"}
    spec = mask_for_entry(img, entry, SEAM, np.random.default_rng(0))
    assert spec.seam_source == "glyph"
    assert spec.has_sign is True
    assert spec.mask[6:30, 4:20].all()


def test_mask_for_entry_handles_none_bbox():
    img = np.zeros(SHAPE, dtype=np.uint8)
    entry = {"seam_bbox": None, "seam_source": "none"}
    spec = mask_for_entry(img, entry, BLOCK, np.random.default_rng(0))
    assert spec.has_sign is False and spec.mask.sum() == 0


def test_unknown_kind_and_oob_bbox_raise():
    with pytest.raises(MaskError, match="unknown mask kind"):
        make_mask("elastic", SHAPE, (0, 0, 5, 5), "glyph", np.random.default_rng(0))
    with pytest.raises(MaskError, match="out of bounds"):
        seam_mask(SHAPE, (0, 0, 200, 5))
