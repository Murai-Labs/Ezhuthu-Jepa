"""Build the 216-uyirmei rendered dataset + a committed manifest (TASK PA.001, AC2).

Renders every vowel-consonant compound to ``--out`` (gitignored image bodies) and writes a text-free
manifest with a provenance block to ``--run-dir`` (committed). Rendering is deterministic, so the
provenance records no RNG seed (``seed: "deterministic"``) rather than a fake one — see DEC-0005.
Training/eval runs use ``provenance.write_provenance`` with the full 5 identifiers instead.

Usage:
    python -m ezhuthu_jepa.data.build_uyirmei \
        --config configs/phase1/render.yaml \
        --out data/rendered/uyirmei \
        --run-dir runs/pa001-render-001
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from ..provenance import capture_code_state, capture_environment, hash_paths
from .grapheme import enumerate_uyirmei
from .render import RenderConfig, TamilRenderer, render_and_save

_PROGRESS_EVERY = 50
_PROVENANCE_PACKAGES = ["pillow", "numpy", "uharfbuzz", "freetype-py", "pyyaml"]


def build(config_path: Path, out_dir: Path, run_dir: Path) -> Path:
    config = RenderConfig.from_yaml(config_path)
    renderer = TamilRenderer(config)
    aksharas = enumerate_uyirmei()
    total = len(aksharas)

    entries = []
    started = time.monotonic()
    for i, aksh in enumerate(aksharas, start=1):
        entries.append(render_and_save(renderer, aksh, out_dir))
        if i % _PROGRESS_EVERY == 0 or i == total:
            elapsed = time.monotonic() - started
            eta = elapsed / i * (total - i)
            print(f"[build_uyirmei] {i}/{total} rendered  elapsed={elapsed:5.1f}s  eta={eta:4.1f}s",
                  flush=True)

    source_paths = [Path(config.font_path), config_path]
    manifest = {
        "run_id": run_dir.name,
        "task": "PA.001",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "provenance": {
            "config_hash": hash_paths([config_path]),
            "code_sha": capture_code_state().sha,
            "data_hash": hash_paths(source_paths),   # font + render config pin the inputs
            "seed": "deterministic",                 # rendering has no RNG (DEC-0005)
            "environment": capture_environment(_PROVENANCE_PACKAGES),
        },
        "config_snapshot": config.__dict__,
        "counts": {
            "total": total,
            "with_sign": sum(1 for e in entries if e["has_sign"]),
            "seam_glyph": sum(1 for e in entries if e["seam_source"] == "glyph"),
            "seam_diff": sum(1 for e in entries if e["seam_source"] == "diff"),
            "seam_none": sum(1 for e in entries if e["seam_source"] == "none"),
        },
        "image_dir": out_dir.as_posix(),
        "entries": entries,
    }

    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "render-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[build_uyirmei] wrote {total} images to {out_dir} and manifest {manifest_path}",
          flush=True)
    return manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the 216-uyirmei rendered dataset + manifest.")
    parser.add_argument("--config", type=Path, default=Path("configs/phase1/render.yaml"))
    parser.add_argument("--out", type=Path, default=Path("data/rendered/uyirmei"))
    parser.add_argument("--run-dir", type=Path, default=Path("runs/pa001-render-001"))
    args = parser.parse_args(argv)
    build(args.config, args.out, args.run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
