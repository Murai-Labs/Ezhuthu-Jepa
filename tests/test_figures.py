"""Figure-pipeline tests (figures convention): F1 regenerates with a provenance sidecar.

Skips where no configured Tamil font is present (same as the render tests)."""

import json
from pathlib import Path

import pytest

from ezhuthu_jepa.data.render import RenderConfig
from ezhuthu_jepa.figures.f1_seam_localization import build_figure

REPO_ROOT = Path(__file__).resolve().parents[1]
RENDER_YAML = REPO_ROOT / "configs" / "phase1" / "render.yaml"
SOURCE_RUN = REPO_ROOT / "runs" / "pa001-render-001"

_CONFIG = RenderConfig.from_yaml(RENDER_YAML)
_HAS_FONT = any(f.available for f in _CONFIG.fonts)

pytestmark = pytest.mark.skipif(not _HAS_FONT, reason="no configured Tamil font available")


def test_f1_generates_image_and_provenance(tmp_path: Path):
    fig = build_figure(RENDER_YAML, tmp_path, SOURCE_RUN)
    assert fig.is_file()
    sidecar = fig.with_name(fig.stem + ".prov.json")
    assert sidecar.is_file()

    prov = json.loads(sidecar.read_text(encoding="utf-8"))
    assert prov["figure_id"] == "F1"
    assert prov["code_sha"]
    # The figure must cite the source render run and inherit its lineage hashes.
    assert prov["source"]["run_id"] == "pa001-render-001"
    assert prov["source"]["config_hash"].startswith("sha256:")
    assert prov["source"]["data_hash"].startswith("sha256:")


def test_f1_provenance_requires_committed_source_run(tmp_path: Path):
    from ezhuthu_jepa.figures.provenance import FigureProvenanceError

    with pytest.raises(FigureProvenanceError, match="no provenance.json"):
        build_figure(RENDER_YAML, tmp_path, tmp_path / "no-such-run")
