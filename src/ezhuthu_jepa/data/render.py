"""Tamil akshara renderer with exact seam localization (TASK PA.001).

Renders each akshara to a grayscale image and localizes the **dependent vowel-sign region** (the
seam the JEPA objective masks). Because Pillow lacks complex-text shaping, we shape with HarfBuzz
(``uharfbuzz``) — which reorders left marks (ெ ே ை) and forms u/uu ligatures correctly — and
rasterize specific glyph IDs with FreeType (``freetype-py``).

Seam localization is a validated hybrid (Nirmala clusters every glyph of an akshara to cluster 0,
so cluster IDs cannot isolate the sign):

* **glyph** — when the sign is a separate glyph (aa on the right; e/ee/ai reordered left; the
  two-part o/oo/au on both sides), the shaped output still contains the bare-consonant glyph, so the
  seam is the union bbox of the *non-base* glyphs.
* **diff** — when the sign fuses into a single ligature glyph (i, u, uu), there is no separate sign
  glyph, so the seam is the pixel region where the ligature differs from the bare consonant rendered
  at the same origin.
* **none** — the inherent-'a' form has no dependent sign; there is nothing to mask.

All heavy pixel work is on ``numpy`` arrays; the final image is a fixed-size square grayscale raster,
with the seam bbox reported in that final image's coordinate frame.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import freetype
import numpy as np
import uharfbuzz as hb
import yaml
from PIL import Image

from .grapheme import Akshara

# (x0, y0, x1, y1) in pixels, x1/y1 exclusive.
BBox = tuple[int, int, int, int]


class RenderError(RuntimeError):
    """Raised when an akshara cannot be rendered or its seam cannot be localized."""


@dataclass(frozen=True)
class RenderConfig:
    """Rendering knobs. Loaded from ``configs/phase1/render.yaml`` (or constructed directly)."""

    font_path: str
    font_index: int = 0
    render_px: int = 96        # FreeType pixel size and HarfBuzz scale (positions come out in px)
    output_px: int = 96        # side of the final square grayscale image
    ink_threshold: int = 32    # grayscale value above which a pixel counts as ink
    diff_threshold: int = 24   # per-pixel delta above which the ligature differs from the base
    margin_px: int = 6         # padding kept around the ink when cropping

    @classmethod
    def from_yaml(cls, path: str | Path) -> "RenderConfig":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        allowed = {f.name for f in fields(cls)}
        unknown = set(data) - allowed
        if unknown:
            raise RenderError(f"unknown render-config key(s): {sorted(unknown)}")
        if "font_path" not in data:
            raise RenderError("render config must set 'font_path'")
        return cls(**data)


@dataclass(frozen=True)
class ShapedGlyph:
    gid: int
    x_offset: int
    y_offset: int
    x_advance: int


@dataclass(frozen=True)
class RenderedAkshara:
    """A rendered akshara plus its exact decomposition and seam label."""

    akshara_id: str
    base_id: str
    sign_id: str
    codepoint_labels: list[str]
    has_sign: bool
    image: np.ndarray          # (output_px, output_px) uint8 grayscale
    seam_bbox: BBox | None     # dependent vowel-sign region, in final-image coords; None if no sign
    seam_source: str           # "glyph" | "diff" | "none"


def _union(boxes: list[BBox]) -> BBox:
    xs0 = min(b[0] for b in boxes)
    ys0 = min(b[1] for b in boxes)
    xs1 = max(b[2] for b in boxes)
    ys1 = max(b[3] for b in boxes)
    return (xs0, ys0, xs1, ys1)


class TamilRenderer:
    """Shapes and rasterizes Tamil aksharas, returning image + seam label."""

    def __init__(self, config: RenderConfig) -> None:
        self.config = config
        font_file = Path(config.font_path)
        if not font_file.is_file():
            raise RenderError(f"font not found: {font_file}")
        self._ft = freetype.Face(str(font_file), index=config.font_index)
        self._ft.set_pixel_sizes(0, config.render_px)
        blob = hb.Blob.from_file_path(str(font_file))
        self._hb_face = hb.Face(blob, config.font_index)
        # Scratch canvas geometry: wide enough for the widest aksharas (two-part o/oo/au signs shape
        # into left-mark + base + right-mark), tall enough for above/below marks. Validated against
        # the full 216 set by test_render's no-clipping check.
        s = config.render_px
        self._cw, self._ch = s * 6, s * 3
        self._baseline = int(s * 2.0)
        self._pen_x0 = s

    def _shape(self, text: str) -> list[ShapedGlyph]:
        font = hb.Font(self._hb_face)
        font.scale = (self.config.render_px, self.config.render_px)
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(font, buf)
        return [
            ShapedGlyph(info.codepoint, pos.x_offset, pos.y_offset, pos.x_advance)
            for info, pos in zip(buf.glyph_infos, buf.glyph_positions)
        ]

    def _raster(self, glyphs: list[ShapedGlyph]) -> tuple[np.ndarray, list[tuple[int, BBox]]]:
        """Composite glyphs onto the scratch canvas; return (canvas, [(gid, pixel_bbox)])."""
        canvas = np.zeros((self._ch, self._cw), dtype=np.uint8)
        boxes: list[tuple[int, BBox]] = []
        pen = self._pen_x0
        for g in glyphs:
            self._ft.load_glyph(g.gid, freetype.FT_LOAD_RENDER)
            slot = self._ft.glyph
            bmp = slot.bitmap
            w, rows, pitch = bmp.width, bmp.rows, bmp.pitch
            if w > 0 and rows > 0:
                arr = np.array(bmp.buffer, dtype=np.uint8).reshape(rows, pitch)[:, :w]
                x0 = pen + g.x_offset + slot.bitmap_left
                y0 = self._baseline - g.y_offset - slot.bitmap_top
                if x0 < 0 or y0 < 0 or x0 + w > self._cw or y0 + rows > self._ch:
                    raise RenderError(
                        f"glyph {g.gid} clipped scratch canvas at ({x0},{y0}); enlarge render geometry"
                    )
                region = canvas[y0 : y0 + rows, x0 : x0 + w]
                np.maximum(region, arr, out=region)
                boxes.append((g.gid, (x0, y0, x0 + w, y0 + rows)))
            pen += g.x_advance
        return canvas, boxes

    def _ink_bbox(self, canvas: np.ndarray) -> BBox:
        ink = np.argwhere(canvas > self.config.ink_threshold)
        if ink.size == 0:
            raise RenderError("rendered canvas is blank (no ink)")
        y0, x0 = ink.min(axis=0)
        y1, x1 = ink.max(axis=0)
        return (int(x0), int(y0), int(x1) + 1, int(y1) + 1)

    def _diff_bbox(self, full: np.ndarray, base: np.ndarray) -> BBox:
        delta = np.abs(full.astype(np.int16) - base.astype(np.int16)) > self.config.diff_threshold
        pts = np.argwhere(delta)
        if pts.size == 0:
            raise RenderError("ligature does not differ from its base consonant; cannot localize seam")
        y0, x0 = pts.min(axis=0)
        y1, x1 = pts.max(axis=0)
        return (int(x0), int(y0), int(x1) + 1, int(y1) + 1)

    def render(self, akshara: Akshara) -> RenderedAkshara:
        full_glyphs = self._shape(akshara.text)
        base_glyphs = self._shape(akshara.consonant.char)
        base_gids = {g.gid for g in base_glyphs}

        canvas, boxes = self._raster(full_glyphs)
        ink = self._ink_bbox(canvas)

        # A separate sign keeps the bare-consonant glyph in the shaped output (aa/e/ee/ai and the
        # two-part o/oo/au); a ligature (i/u/uu) substitutes the base away, so it is absent. That
        # presence — not "is there a non-base glyph" — is what distinguishes the two seam sources
        # (the ligature glyph is itself non-base, which earlier fooled the branch).
        base_present = any(gid in base_gids for gid, _ in boxes)
        nonbase = [box for gid, box in boxes if gid not in base_gids]
        seam_scratch: BBox | None
        if not akshara.has_sign:
            seam_scratch, source = None, "none"
        elif base_present and nonbase:
            seam_scratch, source = _union(nonbase), "glyph"
        else:
            base_canvas, _ = self._raster(base_glyphs)
            seam_scratch, source = self._diff_bbox(canvas, base_canvas), "diff"

        image, seam_bbox = self._crop_pad_resize(canvas, ink, seam_scratch)
        return RenderedAkshara(
            akshara_id=akshara.id,
            base_id=akshara.base_id,
            sign_id=akshara.sign_id,
            codepoint_labels=akshara.codepoint_labels(),
            has_sign=akshara.has_sign,
            image=image,
            seam_bbox=seam_bbox,
            seam_source=source,
        )

    def _crop_pad_resize(
        self, canvas: np.ndarray, ink: BBox, seam: BBox | None
    ) -> tuple[np.ndarray, BBox | None]:
        """Crop to ink+margin, pad to square, resize to output_px; map the seam into final coords."""
        m = self.config.margin_px
        cx0 = max(ink[0] - m, 0)
        cy0 = max(ink[1] - m, 0)
        cx1 = min(ink[2] + m, self._cw)
        cy1 = min(ink[3] + m, self._ch)
        crop = canvas[cy0:cy1, cx0:cx1]
        ch, cw = crop.shape
        side = max(cw, ch)
        square = np.zeros((side, side), dtype=np.uint8)
        ox, oy = (side - cw) // 2, (side - ch) // 2
        square[oy : oy + ch, ox : ox + cw] = crop

        out = self.config.output_px
        scale = out / side
        resized = np.asarray(
            Image.fromarray(square).resize((out, out), Image.BILINEAR), dtype=np.uint8
        )

        seam_out: BBox | None = None
        if seam is not None:
            sx0 = int(round((seam[0] - cx0 + ox) * scale))
            sy0 = int(round((seam[1] - cy0 + oy) * scale))
            sx1 = int(round((seam[2] - cx0 + ox) * scale))
            sy1 = int(round((seam[3] - cy0 + oy) * scale))
            seam_out = (
                max(0, min(sx0, out)),
                max(0, min(sy0, out)),
                max(0, min(sx1, out)),
                max(0, min(sy1, out)),
            )
        return resized, seam_out


def render_and_save(renderer: TamilRenderer, akshara: Akshara, image_dir: Path) -> dict[str, Any]:
    """Render one akshara, save its PNG under ``image_dir``, and return a text-free manifest entry."""
    result = renderer.render(akshara)
    image_dir.mkdir(parents=True, exist_ok=True)
    rel_name = f"{result.akshara_id}.png"
    Image.fromarray(result.image, mode="L").save(image_dir / rel_name)
    return {
        "akshara_id": result.akshara_id,
        "base_id": result.base_id,
        "sign_id": result.sign_id,
        "codepoints": result.codepoint_labels,
        "has_sign": result.has_sign,
        "seam_bbox": list(result.seam_bbox) if result.seam_bbox is not None else None,
        "seam_source": result.seam_source,
        "image": rel_name,
    }
