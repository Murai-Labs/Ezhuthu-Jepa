"""Seam masking and its matched block-masking control (TASK PA.004).

The mechanism under test hides the **dependent vowel-sign region** (the seam) and keeps the
consonant base visible; the model must infer the sign from the base (spec §1). The K1 baseline is a
**block mask of identical size/ratio placed elsewhere**, so the comparison varies only the mask
*location* (the seam boundary), not the mask ratio — exactly what K1 pre-registers (spec §3).

Both maskers share one interface and return a :class:`MaskSpec` (boolean pixel mask + metadata,
carrying ``seam_source`` so downstream metrics stratify — DEC-0006). The inherent-'a' form has no
sign, so its mask is empty (nothing to hide); PA.005 decides whether to exclude those from the
masked-prediction objective.

Masks are derived from the ``seam_bbox`` recorded in the render manifest (final-image coordinates).
Note for PA.005: if images are augmented (affine/elastic), the ``seam_bbox`` must be transformed with
the image before masking, or the mask will no longer align with the sign.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# (x0, y0, x1, y1), x1/y1 exclusive — matches render.BBox.
BBox = tuple[int, int, int, int]

SEAM = "seam"
BLOCK = "block"


class MaskError(ValueError):
    """Raised on an invalid mask request (unknown kind, out-of-bounds bbox)."""


@dataclass(frozen=True)
class MaskSpec:
    """A boolean pixel mask (True = hidden) plus the metadata to interpret and stratify it."""

    mask: np.ndarray      # bool (H, W); True where pixels are masked/hidden
    kind: str             # "seam" | "block"
    seam_source: str      # "glyph" | "diff" | "none" (from the render manifest)
    has_sign: bool        # False for the inherent-'a' form (empty mask)

    @property
    def mask_ratio(self) -> float:
        return float(self.mask.mean())


def _box_mask(shape: tuple[int, int], box: BBox) -> np.ndarray:
    h, w = shape
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
        raise MaskError(f"box {box} out of bounds for image {shape}")
    mask = np.zeros(shape, dtype=bool)
    mask[y0:y1, x0:x1] = True
    return mask


def seam_mask(shape: tuple[int, int], seam_bbox: BBox | None) -> np.ndarray:
    """Mask covering exactly the recorded vowel-sign region (empty if there is no sign)."""
    if seam_bbox is None:
        return np.zeros(shape, dtype=bool)
    return _box_mask(shape, seam_bbox)


def matched_block_mask(
    shape: tuple[int, int], seam_bbox: BBox | None, rng: np.random.Generator
) -> np.ndarray:
    """A block of the **same width/height as the seam box** at a random location (K1 control).

    Matching the box dimensions holds the mask ratio and shape fixed, so only the location differs
    from the seam mask. Empty when there is no sign (nothing to match)."""
    if seam_bbox is None:
        return np.zeros(shape, dtype=bool)
    h, w = shape
    x0, y0, x1, y1 = seam_bbox
    bw, bh = x1 - x0, y1 - y0
    rx = int(rng.integers(0, w - bw + 1))
    ry = int(rng.integers(0, h - bh + 1))
    return _box_mask(shape, (rx, ry, rx + bw, ry + bh))


def make_mask(
    kind: str,
    shape: tuple[int, int],
    seam_bbox: BBox | None,
    seam_source: str,
    rng: np.random.Generator,
) -> MaskSpec:
    """Build a :class:`MaskSpec` of ``kind`` ("seam" or "block") for one akshara image."""
    if kind == SEAM:
        mask = seam_mask(shape, seam_bbox)
    elif kind == BLOCK:
        mask = matched_block_mask(shape, seam_bbox, rng)
    else:
        raise MaskError(f"unknown mask kind {kind!r}; expected {SEAM!r} or {BLOCK!r}")
    return MaskSpec(mask=mask, kind=kind, seam_source=seam_source, has_sign=seam_bbox is not None)


def apply_mask(image: np.ndarray, mask: np.ndarray, fill: int = 0) -> np.ndarray:
    """Return a copy of ``image`` with masked pixels set to ``fill`` (for MAE-style pixel targets)."""
    if image.shape != mask.shape:
        raise MaskError(f"image {image.shape} and mask {mask.shape} shapes differ")
    out = image.copy()
    out[mask] = fill
    return out


def mask_for_entry(
    image: np.ndarray, entry: dict, kind: str, rng: np.random.Generator
) -> MaskSpec:
    """Build a mask for a render-manifest entry (reads its ``seam_bbox`` + ``seam_source``)."""
    bbox = entry.get("seam_bbox")
    seam_bbox: BBox | None = tuple(bbox) if bbox is not None else None  # type: ignore[assignment]
    return make_mask(kind, image.shape, seam_bbox, entry["seam_source"], rng)
