"""Figure F3 — akshara-recognition accuracy with 95% bootstrap CIs (TASK PA.003).

Bar chart of top-1 accuracy by frequency bucket (bottom quartile = metric M, highlighted) and by
seam_source, with CI whiskers. Regenerated from the committed probe metrics
(``runs/pa003-probe-001/metrics.json``); lineage inherited from that run.

    python -m ezhuthu_jepa.figures.f3_probe_accuracy
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from .provenance import write_figure_provenance

FIGURE_ID = "F3"
PAPER_SECTION = "Results — recognition accuracy (baseline encoder)"
_COMMAND = "python -m ezhuthu_jepa.figures.f3_probe_accuracy"
W, H = 820, 420
BG = (18, 18, 26)
BAR = (90, 150, 230)
M_BAR = (255, 150, 0)
WHISKER = (230, 230, 240)
BASE_Y = 340
TOP_Y = 40
LEFT_X = 70


def _bars_from_metrics(metrics: dict) -> list[tuple[str, dict, bool]]:
    bars: list[tuple[str, dict, bool]] = []
    for k in ("q1_bottom", "q2", "q3", "q4_top"):
        bars.append((k, metrics["by_bucket"][k], k == "q1_bottom"))
    for k in sorted(metrics["by_seam_source"]):
        bars.append((f"seam:{k}", metrics["by_seam_source"][k], False))
    return bars


def build_figure(metrics_json: Path, out_dir: Path, repo_root: Path | None = None) -> Path:
    payload = json.loads(metrics_json.read_text(encoding="utf-8"))
    metrics = payload["metrics"]
    bars = _bars_from_metrics(metrics)

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    plot_h = BASE_Y - TOP_Y
    # y grid 0..1
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = BASE_Y - int(frac * plot_h)
        draw.line([LEFT_X, y, W - 30, y], fill=(40, 40, 55))
        draw.text((LEFT_X - 34, y - 6), f"{frac:.2f}", fill=(150, 150, 170))

    n = len(bars)
    slot = (W - 30 - LEFT_X) / n
    bar_w = slot * 0.6
    for i, (label, d, is_m) in enumerate(bars):
        acc = d["accuracy"]
        x0 = LEFT_X + i * slot + (slot - bar_w) / 2
        y_acc = BASE_Y - int(acc * plot_h)
        draw.rectangle([x0, y_acc, x0 + bar_w, BASE_Y], fill=M_BAR if is_m else BAR)
        # CI whisker
        cx = x0 + bar_w / 2
        y_lo, y_hi = BASE_Y - int(d["ci_low"] * plot_h), BASE_Y - int(d["ci_high"] * plot_h)
        draw.line([cx, y_hi, cx, y_lo], fill=WHISKER, width=2)
        draw.line([cx - 5, y_hi, cx + 5, y_hi], fill=WHISKER, width=2)
        draw.line([cx - 5, y_lo, cx + 5, y_lo], fill=WHISKER, width=2)
        draw.text((x0, BASE_Y + 6), label, fill=(180, 180, 200))
        draw.text((x0, y_acc - 14), f"{acc:.2f}", fill=(210, 210, 225))
        draw.text((x0, BASE_Y + 20), f"n={d['n']}", fill=(130, 130, 150))

    draw.text((LEFT_X, 10),
              f"Top-1 accuracy by frequency bucket & seam_source (encoder={payload['encoder']}, "
              f"95% CI)", fill=(200, 200, 215))
    draw.text((LEFT_X, H - 26),
              f"orange = bottom quartile (metric M = {metrics['metric_M']['accuracy']:.3f}); "
              f"weak pixel baseline, replaced by JEPA encoder at PA.005", fill=(150, 150, 170))

    out_dir.mkdir(parents=True, exist_ok=True)
    figure_path = out_dir / "f3_probe_accuracy.png"
    img.save(figure_path)
    write_figure_provenance(
        figure_path,
        figure_id=FIGURE_ID,
        paper_section=PAPER_SECTION,
        caption=(
            "Akshara-recognition top-1 accuracy (baseline PixelEncoder) on the PA.002 split, by "
            "frequency bucket and seam_source, with 95% bootstrap CIs. Orange = bottom quartile "
            "(metric M). Reference numbers from a weak encoder + 1-shot cross-font data; the JEPA "
            "encoder replaces it at PA.005. The metric machinery is frozen here before the K1/K3 sweep."
        ),
        source_run_dir=metrics_json.parent,
        command=_COMMAND,
        repo_root=repo_root,
    )
    print(f"[figure F3] wrote {figure_path} + provenance sidecar", flush=True)
    return figure_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate paper Figure F3 (probe accuracy).")
    parser.add_argument("--metrics", type=Path, default=Path("runs/pa003-probe-001/metrics.json"))
    parser.add_argument("--out", type=Path, default=Path("docs/figures"))
    args = parser.parse_args(argv)
    build_figure(args.metrics, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
