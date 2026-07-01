"""Figure F1 — seam localization across the 12 vowels (TASK PA.001 illustration).

Shows, for a few consonants × all 12 vowels, the rendered akshara with its localized seam box:
green = separable-glyph sign, orange = ligature (diff) sign, no box = inherent 'a'. This is the
mechanism figure: it makes "base visible, vowel-sign region masked" concrete and exposes the
ligature cases where the sign fuses with the base.

Regenerated deterministically from the committed render config (no dependency on gitignored image
bodies). Lineage is inherited from the render run (default: pa001-render-001).

    python -m ezhuthu_jepa.figures.f1_seam_localization
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from ..data.grapheme import VOWELS, compose
from ..data.render import RenderConfig, TamilRenderer
from .provenance import write_figure_provenance

FIGURE_ID = "F1"
PAPER_SECTION = "Method — seam localization"
CONSONANT_ROWS = ("k", "nn", "zh")  # ka, Na (retroflex), zha — varied ligature behavior
COLOR_GLYPH = (0, 200, 90)      # separable-glyph sign
COLOR_DIFF = (255, 150, 0)      # ligature (diff) sign
COLOR_BG = (18, 18, 26)
LABEL_H = 18
PAD = 4
_COMMAND = "python -m ezhuthu_jepa.figures.f1_seam_localization"
_CAPTION = (
    "Seam localization for consonants k/nn/zh across the 12 vowels (font: {font}). "
    "Green box = separable-glyph vowel sign (union of non-base glyphs); orange box = ligature sign "
    "(diff vs the bare consonant); no box = inherent 'a'. The orange cases are where the vowel fuses "
    "with the base, so the sign is not cleanly separable — results are reported stratified by "
    "seam_source (DEC-0006)."
)


def _pick_font(config: RenderConfig, preferred: str):
    for fid in (preferred, *[f.id for f in config.fonts]):
        font = next((f for f in config.fonts if f.id == fid and f.available), None)
        if font is not None:
            return font
    return None


def build_figure(
    config_path: Path,
    out_dir: Path,
    source_run_dir: Path,
    font_id: str = "noto",
    repo_root: Path | None = None,
) -> Path:
    config = RenderConfig.from_yaml(config_path)
    font = _pick_font(config, font_id)
    if font is None:
        raise SystemExit(f"no configured font available for figure F1 (checked {[f.id for f in config.fonts]})")
    renderer = TamilRenderer(font, config)

    s = config.output_px
    cell = s + PAD
    width = len(VOWELS) * cell + PAD
    height = LABEL_H + len(CONSONANT_ROWS) * (cell + LABEL_H) + PAD
    sheet = Image.new("RGB", (width, height), COLOR_BG)
    draw = ImageDraw.Draw(sheet)

    # Column headers (vowel ids) and per-cell renders with seam overlay.
    for ci, vowel in enumerate(VOWELS):
        draw.text((PAD + ci * cell + 2, 4), vowel.id, fill=(170, 170, 190))
    for ri, cid in enumerate(CONSONANT_ROWS):
        row_top = LABEL_H + ri * (cell + LABEL_H)
        draw.text((PAD, row_top + 2), cid, fill=(170, 170, 190))
        for ci, vowel in enumerate(VOWELS):
            r = renderer.render(compose(cid, vowel.id))
            glyph = Image.fromarray(r.image, "L").convert("RGB")
            x = PAD + ci * cell
            y = row_top + LABEL_H
            sheet.paste(glyph, (x, y))
            if r.seam_bbox is not None:
                color = COLOR_GLYPH if r.seam_source == "glyph" else COLOR_DIFF
                b = r.seam_bbox
                draw.rectangle([x + b[0], y + b[1], x + b[2], y + b[3]], outline=color, width=2)

    out_dir.mkdir(parents=True, exist_ok=True)
    figure_path = out_dir / "f1_seam_localization.png"
    sheet.save(figure_path)

    write_figure_provenance(
        figure_path,
        figure_id=FIGURE_ID,
        paper_section=PAPER_SECTION,
        caption=_CAPTION.format(font=font.id),
        source_run_dir=source_run_dir,
        command=f"{_COMMAND} --font {font.id}",
        repo_root=repo_root,
    )
    print(f"[figure F1] wrote {figure_path} (font={font.id}) + provenance sidecar", flush=True)
    return figure_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate paper Figure F1 (seam localization).")
    parser.add_argument("--config", type=Path, default=Path("configs/phase1/render.yaml"))
    parser.add_argument("--out", type=Path, default=Path("docs/figures"))
    parser.add_argument("--source-run", type=Path, default=Path("runs/pa001-render-001"))
    parser.add_argument("--font", default="noto")
    args = parser.parse_args(argv)
    build_figure(args.config, args.out, args.source_run, font_id=args.font)
    return 0


if __name__ == "__main__":
    sys.exit(main())
