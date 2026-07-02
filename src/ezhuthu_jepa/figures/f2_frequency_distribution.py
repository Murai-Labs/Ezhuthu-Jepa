"""Figure F2 — compound frequency distribution with the bottom-quartile cutoff (TASK PA.002).

Plots the 216 uyirmei sorted by Project Madurai frequency (log-scaled) with the bottom-quartile
cutoff marked — the long tail metric M is reported on. Regenerated from the committed split manifest
(``runs/pa002-split-001/split-manifest.json``); lineage inherited from that run.

    python -m ezhuthu_jepa.figures.f2_frequency_distribution
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .provenance import write_figure_provenance

FIGURE_ID = "F2"
PAPER_SECTION = "Data — frequency stratification"
_COMMAND = "python -m ezhuthu_jepa.figures.f2_frequency_distribution"
W, H = 900, 380
MARGIN_L, MARGIN_B, MARGIN_T, MARGIN_R = 60, 40, 30, 20
BG = (18, 18, 26)
BAR = (90, 150, 230)
BOTTOM_BAR = (255, 150, 0)
CUT = (0, 200, 90)


def build_figure(split_manifest: Path, out_dir: Path, repo_root: Path | None = None) -> Path:
    manifest = json.loads(split_manifest.read_text(encoding="utf-8"))
    aksharas = sorted(manifest["aksharas"], key=lambda a: a["rank"])
    freqs = np.array([a["frequency"] for a in aksharas], dtype=float)
    n = len(freqs)
    bottom_n = manifest["buckets"]["size"]  # rarest quartile occupies ranks [0, bottom_n)

    plot_w = W - MARGIN_L - MARGIN_R
    plot_h = H - MARGIN_T - MARGIN_B
    ymax = np.log10(freqs.max() + 1.0) or 1.0

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    bar_w = plot_w / n
    for i, f in enumerate(freqs):
        h = int((np.log10(f + 1.0) / ymax) * plot_h)
        x0 = MARGIN_L + i * bar_w
        color = BOTTOM_BAR if i < bottom_n else BAR
        draw.rectangle([x0, H - MARGIN_B - h, x0 + max(1, bar_w - 0.5), H - MARGIN_B], fill=color)

    cut_x = MARGIN_L + bottom_n * bar_w
    draw.line([cut_x, MARGIN_T, cut_x, H - MARGIN_B], fill=CUT, width=2)
    draw.text((cut_x + 4, MARGIN_T), f"bottom quartile = {bottom_n}", fill=CUT)
    draw.text((MARGIN_L, 6), "Uyirmei by Project Madurai frequency (log10, ascending rank)",
              fill=(180, 180, 200))
    draw.text((6, H - MARGIN_B - plot_h // 2), "freq", fill=(150, 150, 170))
    seen = manifest["corpus"]["distinct_uyirmei_seen"]
    draw.text((MARGIN_L, H - MARGIN_B + 6),
              f"total counted={manifest['corpus']['total_uyirmei']}  seen={seen}/{n}  "
              f"orange=bottom quartile (metric M)", fill=(150, 150, 170))

    out_dir.mkdir(parents=True, exist_ok=True)
    figure_path = out_dir / "f2_frequency_distribution.png"
    img.save(figure_path)

    write_figure_provenance(
        figure_path,
        figure_id=FIGURE_ID,
        paper_section=PAPER_SECTION,
        caption=(
            "The 216 uyirmei ranked by Project Madurai corpus frequency (log10). Orange = the "
            "bottom quartile (rarest 25%), the long tail on which metric M is reported; green line = "
            "the frozen cutoff. Compounds absent from the corpus have frequency 0 and fall in the "
            "bottom quartile (DEC-0004)."
        ),
        source_run_dir=split_manifest.parent,
        command=_COMMAND,
        repo_root=repo_root,
    )
    print(f"[figure F2] wrote {figure_path} + provenance sidecar", flush=True)
    return figure_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate paper Figure F2 (frequency distribution).")
    parser.add_argument("--split-manifest", type=Path,
                        default=Path("runs/pa002-split-001/split-manifest.json"))
    parser.add_argument("--out", type=Path, default=Path("docs/figures"))
    args = parser.parse_args(argv)
    build_figure(args.split_manifest, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
