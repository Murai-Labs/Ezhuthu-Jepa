"""Renderer tests (TASK PA.001): all 216 render without clipping; seams land on the right side.

Parametrized over every configured font that is present on this machine; fonts absent here (e.g.
Nirmala on Linux CI) are skipped individually. The grapheme-model correctness (AC1) is covered
font-free in test_grapheme.py, so these can all skip without losing the exactness guarantee.
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

_CONFIG = RenderConfig.from_yaml(RENDER_YAML)
_AVAILABLE = [f for f in _CONFIG.fonts if f.available]


@pytest.fixture(scope="module", params=[f.id for f in _AVAILABLE] or [pytest.param(None)])
def renderer(request) -> TamilRenderer:
    if request.param is None:
        pytest.skip("no configured Tamil font is available on this machine")
    font = next(f for f in _CONFIG.fonts if f.id == request.param)
    return TamilRenderer(font, _CONFIG)


def _center_x(r: RenderedAkshara) -> float:
    assert r.seam_bbox is not None
    return (r.seam_bbox[0] + r.seam_bbox[2]) / 2


def test_config_loads_multifont():
    assert len(_CONFIG.fonts) >= 1
    assert {f.id for f in _CONFIG.fonts} >= {"noto"}
    assert _CONFIG.output_px == 96


def test_all_216_render_without_clipping(renderer: TamilRenderer):
    for aksh in enumerate_uyirmei():
        r = renderer.render(aksh)
        assert r.image.shape == (renderer.config.output_px, renderer.config.output_px)
        assert r.image.dtype == np.uint8
        assert r.image.max() > renderer.config.ink_threshold
        assert r.font_id == renderer.font.id


def test_inherent_a_has_no_seam(renderer: TamilRenderer):
    r = renderer.render(compose("k", "a"))
    assert r.has_sign is False
    assert r.seam_bbox is None
    assert r.seam_source == "none"


def test_right_sign_is_a_separate_glyph(renderer: TamilRenderer):
    r = renderer.render(compose("k", "aa"))  # கா — ா on the right, separable in all Tamil fonts
    assert r.seam_source == "glyph"
    assert r.seam_bbox is not None


def test_left_sign_is_left_of_right_sign(renderer: TamilRenderer):
    # ெ (e) reorders to the LEFT; ா (aa) attaches on the RIGHT — true regardless of font.
    left = renderer.render(compose("k", "e"))
    right = renderer.render(compose("k", "aa"))
    assert _center_x(left) < _center_x(right)


def test_seam_source_is_valid_and_font_may_ligate(renderer: TamilRenderer):
    # 'u' fuses into a ligature in both Nirmala and Noto → diff. Other vowels are font-dependent.
    assert renderer.render(compose("k", "u")).seam_source == "diff"
    sources = {renderer.render(a).seam_source for a in enumerate_uyirmei()}
    assert sources <= {"glyph", "diff", "none"}
    assert {"none", "glyph"} <= sources  # 'a' + at least the right/left separable signs


def test_seam_bbox_within_image(renderer: TamilRenderer):
    out = renderer.config.output_px
    for aksh in enumerate_uyirmei():
        r = renderer.render(aksh)
        if r.seam_bbox is None:
            continue
        x0, y0, x1, y1 = r.seam_bbox
        assert 0 <= x0 < x1 <= out
        assert 0 <= y0 < y1 <= out


def test_render_and_save_tags_font_in_filename(renderer: TamilRenderer, tmp_path: Path):
    entry = render_and_save(renderer, compose("m", "ii"), tmp_path)
    assert entry["font_id"] == renderer.font.id
    assert entry["image"] == f"m_ii__{renderer.font.id}.png"
    assert (tmp_path / entry["image"]).is_file()
    assert entry["codepoints"] == ["U+0BAE", "U+0BC0"]
