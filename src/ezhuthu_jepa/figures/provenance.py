"""Figure provenance: tie every paper figure to the run that produced it.

A figure is a *report* (committed to the repo), but like every result it must be traceable. Each
generated figure gets a ``<fig>.prov.json`` sidecar recording the figure's own code SHA and the
lineage it inherits from its source run (run-id + that run's config/data hashes). This makes
"which run made Figure 3?" answerable and enforces the reproducibility rule that figures cite run IDs.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..provenance import capture_code_state


class FigureProvenanceError(RuntimeError):
    """Raised when a figure's source run lineage cannot be read."""


def _read_source_lineage(source_run_dir: Path) -> dict[str, Any]:
    prov_path = source_run_dir / "provenance.json"
    if not prov_path.is_file():
        raise FigureProvenanceError(f"source run has no provenance.json: {prov_path}")
    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    ids = prov.get("identifiers", {})
    return {
        "run_id": prov.get("run_id"),
        "config_hash": ids.get("config_hash"),
        "data_hash": ids.get("data_hash"),
    }


def write_figure_provenance(
    figure_path: Path,
    *,
    figure_id: str,
    paper_section: str,
    caption: str,
    source_run_dir: Path,
    command: str,
    repo_root: Path | None = None,
) -> Path:
    """Write ``<figure>.prov.json`` next to ``figure_path`` and return its path."""
    if not figure_path.is_file():
        raise FigureProvenanceError(f"figure not written yet: {figure_path}")
    code = capture_code_state(repo_root)
    sidecar = {
        "figure_id": figure_id,
        "figure_file": figure_path.name,
        "paper_section": paper_section,
        "caption": caption,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "code_sha": code.sha,
        "code_dirty": code.dirty,
        "source": _read_source_lineage(source_run_dir),
        "command": command,
    }
    prov_path = figure_path.with_name(figure_path.stem + ".prov.json")
    prov_path.write_text(json.dumps(sidecar, indent=2, ensure_ascii=False), encoding="utf-8")
    return prov_path
