"""G0 smoke test: the package imports and exposes a version (TASK P0.002)."""

from pathlib import Path


def test_package_imports_with_version():
    import ezhuthu_jepa

    assert isinstance(ezhuthu_jepa.__version__, str)
    assert ezhuthu_jepa.__version__ != ""


def test_repo_layout_present():
    """The governance operating system must exist at the repo root."""
    root = Path(__file__).resolve().parents[1]
    required = [
        "CLAUDE.md",
        "AGENTS.md",
        "CODEX.md",
        "STATUS.md",
        "CHECKPOINT.md",
        "tasks/atomic-task-list.md",
        "docs/DECISION_LOG.md",
        "docs/spec/EZHUTHU_JEPA_Spec_v0.2.md",
    ]
    missing = [p for p in required if not (root / p).exists()]
    assert not missing, f"missing required files: {missing}"
