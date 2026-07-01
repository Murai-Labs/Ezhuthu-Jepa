"""Renderer tests (TASK PA.001): all 216 render without clipping; seams land on the right side.

These require the configured Tamil font. Where it is absent (e.g. a Linux CI box without Nirmala),
the whole module skips rather than failing — the grapheme-model correctness (AC1) is covered font-free
in test_grapheme.py.
"""

from pathlib import Path

import numpy as np
import pytest

from ezhuthu_jepa.data.grapheme import compose, enumerate_uyirmei
from ezhuthu_jepa.data.render import (
    RenderConfig,
    RenderedAkshara,
    TamilRenderer,
    render_and_save,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
RENDER_YAML = REPO_ROOT / "configs" / "phase1" / "render.yaml"


@pytest.fixture(scope="module")
def config() -> RenderConfig:
    cfg = RenderConfig.from_yaml(RENDER_YAML)
    if not Path(cfg.font_path).is_file():
        pytest.skip(f"font not available: {cfg.font_path}")
    return cfg


@pytest.fixture(scope="module")
def renderer(config: RenderConfig) -> TamilRenderer:
    return TamilRenderer(config)


def _center_x(r: RenderedAkshara) -> float:
    assert r.seam_bbox is not None
    return (r.seam_bbox[0] + r.seam_bbox[2]) / 2


def test_config_loads_from_yaml(config: RenderConfig):
    assert config.font_index == 0
    assert config.output_px == 96


def test_all_216_render_without_clipping(renderer: TamilRenderer):
    for aksh in enumerate_uyirmei():
        r = renderer.render(aksh)
        assert r.image.shape == (renderer.config.output_px, renderer.config.output_px)
        assert r.image.dtype == np.uint8
        assert r.image.max() > renderer.config.ink_threshold  # has ink


def test_inherent_a_has_no_seam(renderer: TamilRenderer):
    r = renderer.render(compose("k", "a"))
    assert r.has_sign is False
    assert r.seam_bbox is None
    assert r.seam_source == "none"


def test_right_sign_is_a_separate_glyph(renderer: TamilRenderer):
    r = renderer.render(compose("k", "aa"))  # கா — ா on the right
    assert r.seam_source == "glyph"
    assert r.seam_bbox is not None


def test_ligature_sign_uses_diff(renderer: TamilRenderer):
    r = renderer.render(compose("k", "u"))  # கு — u fuses into a ligature
    assert r.seam_source == "diff"
    assert r.seam_bbox is not None


def test_left_sign_is_left_of_right_sign(renderer: TamilRenderer):
    # ெ (e) reorders to the LEFT; ா (aa) attaches on the RIGHT. Seam centers must reflect that.
    left = renderer.render(compose("k", "e"))
    right = renderer.render(compose("k", "aa"))
    assert _center_x(left) < _center_x(right)


def test_seam_bbox_within_image(renderer: TamilRenderer):
    out = renderer.config.output_px
    for aksh in enumerate_uyirmei():
        r = renderer.render(aksh)
        if r.seam_bbox is None:
            continue
        x0, y0, x1, y1 = r.seam_bbox
        assert 0 <= x0 < x1 <= out
        assert 0 <= y0 < y1 <= out


def test_all_three_seam_sources_appear(renderer: TamilRenderer):
    sources = {renderer.render(a).seam_source for a in enumerate_uyirmei()}
    assert {"none", "glyph", "diff"} <= sources


def test_render_and_save_writes_png_and_manifest_entry(renderer: TamilRenderer, tmp_path: Path):
    entry = render_and_save(renderer, compose("m", "ii"), tmp_path)
    assert (tmp_path / entry["image"]).is_file()
    assert entry["base_id"] == "m" and entry["sign_id"] == "ii"
    assert entry["codepoints"] == ["U+0BAE", "U+0BC0"]
    assert entry["seam_source"] in {"glyph", "diff"}
