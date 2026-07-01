"""Build the 216-uyirmei rendered dataset + a committed manifest (TASK PA.001, AC2).

Renders every vowel-consonant compound under every available font (DEC-0006) to ``--out`` (gitignored
image bodies), writes a text-free ``render-manifest.json`` to ``--run-dir``, and writes the run's
``provenance.json`` via the unified ``write_provenance`` with ``seed=SEED_DETERMINISTIC`` (rendering
has no RNG). Fonts whose path is absent on this machine are skipped with a logged note.

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

from ..provenance import SEED_DETERMINISTIC, hash_paths, validate_run_dir, write_provenance
from .grapheme import enumerate_uyirmei
from .render import RenderConfig, TamilRenderer, render_and_save

_PROGRESS_EVERY = 50
_PROVENANCE_PACKAGES = ["pillow", "numpy", "uharfbuzz", "freetype-py", "pyyaml"]


def build(config_path: Path, out_dir: Path, run_dir: Path) -> Path:
    config = RenderConfig.from_yaml(config_path)
    aksharas = enumerate_uyirmei()

    available = [f for f in config.fonts if f.available]
    skipped = [f.id for f in config.fonts if not f.available]
    if not available:
        raise SystemExit(f"no configured font is available; checked {[f.path for f in config.fonts]}")
    if skipped:
        print(f"[build_uyirmei] skipping unavailable fonts: {skipped}", flush=True)

    entries: list[dict] = []
    started = time.monotonic()
    total = len(aksharas) * len(available)
    done = 0
    for font in available:
        renderer = TamilRenderer(font, config)
        for aksh in aksharas:
            entries.append(render_and_save(renderer, aksh, out_dir))
            done += 1
            if done % _PROGRESS_EVERY == 0 or done == total:
                elapsed = time.monotonic() - started
                eta = elapsed / done * (total - done)
                print(f"[build_uyirmei] {done}/{total} rendered ({font.id})  "
                      f"elapsed={elapsed:5.1f}s  eta={eta:4.1f}s", flush=True)

    # Provenance: pin the exact font bytes + render config; deterministic (no RNG) seed.
    source_paths = [Path(f.path) for f in available] + [config_path]
    run_dir.mkdir(parents=True, exist_ok=True)
    write_provenance(
        run_dir,
        config=config,
        data_hash=hash_paths(source_paths),
        run_id=run_dir.name,
        seed=SEED_DETERMINISTIC,
        package_names=_PROVENANCE_PACKAGES,
    )

    def _count(source: str) -> int:
        return sum(1 for e in entries if e["seam_source"] == source)

    manifest = {
        "run_id": run_dir.name,
        "task": "PA.001",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "provenance_ref": "provenance.json",
        "fonts_rendered": [f.id for f in available],
        "fonts_skipped": skipped,
        "counts": {
            "total": len(entries),
            "aksharas": len(aksharas),
            "fonts": len(available),
            "seam_glyph": _count("glyph"),
            "seam_diff": _count("diff"),
            "seam_none": _count("none"),
        },
        "image_dir": out_dir.as_posix(),
        "entries": entries,
    }
    manifest_path = run_dir / "render-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    validate_run_dir(run_dir)  # self-check: the run's provenance has all 5 identifiers
    print(f"[build_uyirmei] wrote {len(entries)} images to {out_dir}; manifest {manifest_path}",
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
