"""Deterministic glyph augmentation that transforms the seam_bbox in lockstep (TASK PA.4b.1).

Augmentation multiplies instances per akshara so metric M's CI shrinks enough to adjudicate a 2 pp
effect (DEC-0013). The hard requirement: a warp that moves the ink must move the recorded
``seam_bbox`` too, or the seam mask (PA.004) would hide the wrong pixels. Here the forward affine is
applied to the bbox corners and an axis-aligned box is re-fit (which provably contains the warped
region); stroke/blur/noise do not move the box.

Ranges are kept in the "safe" regime (small rotation/shear, mild stroke/blur/noise) so glyph topology
and the base-vs-sign distinction are preserved. Everything is seeded, so an instance is reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageFilter

BBox = tuple[int, int, int, int]


@dataclass(frozen=True)
class AugmentConfig:
    rotation_deg: float = 4.0        # +/- range
    translate_frac: float = 0.05     # +/- fraction of side
    shear_deg: float = 4.0           # +/- range
    scale_min: float = 0.9
    scale_max: float = 1.1
    stroke_iters: int = 1            # max dilate(+)/erode(-) iterations (3x3)
    blur_max: float = 1.0            # max Gaussian blur radius
    noise_std: float = 6.0           # gaussian pixel noise std (0-255 scale)


def _linear(rot_deg: float, shear_deg: float, scale: float) -> np.ndarray:
    t = np.radians(rot_deg)
    s = np.radians(shear_deg)
    rot = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    shear = np.array([[1.0, np.tan(s)], [0.0, 1.0]])
    return rot @ shear @ np.array([[scale, 0.0], [0.0, scale]])


def _transform_bbox(bbox: BBox, lin: np.ndarray, b_vec: np.ndarray, shape: tuple[int, int]) -> BBox:
    h, w = shape
    x0, y0, x1, y1 = bbox
    corners = np.array([[x0, y0], [x1, y0], [x0, y1], [x1, y1]], dtype=float)
    warped = corners @ lin.T + b_vec
    nx0, ny0 = warped.min(axis=0)
    nx1, ny1 = warped.max(axis=0)
    nx0 = int(np.clip(np.floor(nx0), 0, w - 1))
    ny0 = int(np.clip(np.floor(ny0), 0, h - 1))
    nx1 = int(np.clip(np.ceil(nx1), nx0 + 1, w))
    ny1 = int(np.clip(np.ceil(ny1), ny0 + 1, h))
    return (nx0, ny0, nx1, ny1)


def _stroke(img: Image.Image, iters: int) -> Image.Image:
    # ink is bright on a dark ground: MaxFilter dilates (thickens), MinFilter erodes (thins).
    flt = ImageFilter.MaxFilter(3) if iters > 0 else ImageFilter.MinFilter(3)
    for _ in range(abs(iters)):
        img = img.filter(flt)
    return img


def augment_image(
    image: np.ndarray, seam_bbox: BBox | None, config: AugmentConfig, rng: np.random.Generator
) -> tuple[np.ndarray, BBox | None]:
    """Return (augmented image, transformed seam_bbox). Deterministic given ``rng``."""
    h, w = image.shape
    rot = rng.uniform(-config.rotation_deg, config.rotation_deg)
    shear = rng.uniform(-config.shear_deg, config.shear_deg)
    scale = rng.uniform(config.scale_min, config.scale_max)
    tx = rng.uniform(-config.translate_frac, config.translate_frac) * w
    ty = rng.uniform(-config.translate_frac, config.translate_frac) * h

    lin = _linear(rot, shear, scale)
    center = np.array([w / 2.0, h / 2.0])
    b_vec = center + np.array([tx, ty]) - lin @ center  # forward: p' = lin @ p + b_vec

    inv = np.linalg.inv(lin)
    inv_b = -inv @ b_vec
    coeffs = (inv[0, 0], inv[0, 1], inv_b[0], inv[1, 0], inv[1, 1], inv_b[1])

    pil = Image.fromarray(image).transform((w, h), Image.AFFINE, coeffs, resample=Image.BILINEAR)

    stroke = int(rng.integers(-config.stroke_iters, config.stroke_iters + 1))
    if stroke != 0:
        pil = _stroke(pil, stroke)
    blur = rng.uniform(0.0, config.blur_max)
    if blur > 0.05:
        pil = pil.filter(ImageFilter.GaussianBlur(blur))

    out = np.asarray(pil, dtype=np.float32)
    if config.noise_std > 0:
        out = out + rng.normal(0.0, config.noise_std, out.shape)
    out = np.clip(out, 0, 255).astype(np.uint8)

    new_bbox = None if seam_bbox is None else _transform_bbox(seam_bbox, lin, b_vec, (h, w))
    return out, new_bbox
