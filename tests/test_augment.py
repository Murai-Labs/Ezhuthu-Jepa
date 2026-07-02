"""Augmentation tests (TASK PA.4b.1): deterministic; seam_bbox tracks the image warp."""

import numpy as np

from ezhuthu_jepa.data.augment import AugmentConfig, augment_image

SHAPE = (96, 96)


def _sign_image(bbox):
    """White block exactly in bbox on a black ground — stands in for the vowel-sign region."""
    img = np.zeros(SHAPE, dtype=np.uint8)
    x0, y0, x1, y1 = bbox
    img[y0:y1, x0:x1] = 255
    return img


def test_deterministic_given_seed():
    bbox = (30, 30, 60, 60)
    img = _sign_image(bbox)
    a_img, a_bb = augment_image(img, bbox, AugmentConfig(), np.random.default_rng(3))
    b_img, b_bb = augment_image(img, bbox, AugmentConfig(), np.random.default_rng(3))
    assert np.array_equal(a_img, b_img)
    assert a_bb == b_bb


def test_output_shape_and_dtype_preserved():
    bbox = (30, 30, 60, 60)
    out, _ = augment_image(_sign_image(bbox), bbox, AugmentConfig(), np.random.default_rng(0))
    assert out.shape == SHAPE and out.dtype == np.uint8


def test_transformed_bbox_contains_the_warped_sign():
    # After augmentation, virtually all of the warped white region must lie inside the new bbox —
    # this is the property that keeps the seam mask aligned.
    bbox = (28, 28, 64, 64)
    img = _sign_image(bbox)
    for seed in range(6):
        out, new_bbox = augment_image(img, bbox, AugmentConfig(), np.random.default_rng(seed))
        ink = np.argwhere(out > 128)
        assert ink.size > 0
        x0, y0, x1, y1 = new_bbox
        inside = ((ink[:, 1] >= x0) & (ink[:, 1] < x1) & (ink[:, 0] >= y0) & (ink[:, 0] < y1)).mean()
        assert inside > 0.95, f"seed {seed}: only {inside:.2%} of ink inside transformed bbox"


def test_translation_only_shifts_bbox():
    cfg = AugmentConfig(rotation_deg=0, shear_deg=0, scale_min=1.0, scale_max=1.0,
                        stroke_iters=0, blur_max=0.0, noise_std=0.0, translate_frac=0.1)
    bbox = (30, 30, 50, 50)
    _, new_bbox = augment_image(_sign_image(bbox), bbox, cfg, np.random.default_rng(1))
    # width/height preserved under pure translation (± rounding)
    assert abs((new_bbox[2] - new_bbox[0]) - 20) <= 2
    assert abs((new_bbox[3] - new_bbox[1]) - 20) <= 2


def test_identity_config_is_near_noop():
    cfg = AugmentConfig(rotation_deg=0, translate_frac=0, shear_deg=0, scale_min=1.0, scale_max=1.0,
                        stroke_iters=0, blur_max=0.0, noise_std=0.0)
    bbox = (20, 20, 70, 70)
    img = _sign_image(bbox)
    out, new_bbox = augment_image(img, bbox, cfg, np.random.default_rng(0))
    assert np.array_equal(out, img)
    assert new_bbox == bbox


def test_none_bbox_stays_none():
    out, new_bbox = augment_image(np.zeros(SHAPE, np.uint8), None, AugmentConfig(), np.random.default_rng(0))
    assert new_bbox is None and out.shape == SHAPE
