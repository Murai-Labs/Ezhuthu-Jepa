"""Run-provenance writer and validator (TASK P0.003).

Every run must record, *before it starts*, the five identifiers that make a metric citable
(AGENTS.md §2.4, §2.6):

    1. config_hash  — sha256 of the canonical config
    2. code_sha     — git commit of the working tree (+ dirty flag)
    3. data_hash    — caller-supplied hash of the exact data split/manifest used
    4. seed         — the RNG seed (taken from the config, single source of truth)
    5. environment  — python / platform / accelerator / key package versions

A run directory whose manifest is missing any of these is rejected by :func:`validate_run_dir`, so
un-provenanced results cannot silently reach the paper.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

from .config import RunConfig

MANIFEST_FILENAME = "provenance.json"
MANIFEST_VERSION = "1"

# Exactly the five identifier categories a run manifest must carry. The validator asserts set
# equality against this — no missing, no extra.
REQUIRED_IDENTIFIERS = ("config_hash", "code_sha", "data_hash", "seed", "environment")


class ProvenanceError(RuntimeError):
    """Raised when provenance cannot be captured or a run dir fails validation."""


@dataclass(frozen=True)
class CodeState:
    """The git identity of the working tree at run time."""

    sha: str
    dirty: bool


def _canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, no insignificant whitespace, UTF-8 preserved."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_config_hash(config: RunConfig) -> str:
    """sha256 of the config's canonical form. Order-independent and stable across processes."""
    payload = _canonical_json(config.to_canonical_dict())
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _find_repo_root(start: Path) -> Path:
    """Walk upward from ``start`` to the nearest directory containing ``.git``."""
    start = start.resolve()
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise ProvenanceError(f"no git repository found at or above {start}")


def capture_code_state(repo_root: Path | None = None) -> CodeState:
    """Capture the current commit SHA and whether the working tree is dirty.

    Runs git as a subprocess; a run without a resolvable commit is not allowed to proceed.
    """
    root = _find_repo_root(repo_root or Path.cwd())
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise ProvenanceError(f"could not read git state in {root}: {exc}") from exc
    if not sha:
        raise ProvenanceError(f"git returned an empty HEAD SHA in {root}")
    return CodeState(sha=sha, dirty=bool(status.strip()))


def hash_paths(paths: list[Path]) -> str:
    """sha256 over the ordered (relative-name, content) of the given files.

    Use this to hash a data manifest or split file so ``data_hash`` pins the exact bytes consumed.
    Raises if any path is missing — a data hash over absent files would be a lie.
    """
    if not paths:
        raise ProvenanceError("hash_paths requires at least one path")
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.as_posix()):
        if not path.is_file():
            raise ProvenanceError(f"cannot hash missing file: {path}")
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return "sha256:" + digest.hexdigest()


def capture_environment(package_names: list[str] | None = None) -> dict[str, Any]:
    """Capture python/platform/accelerator info and versions of the requested packages.

    Best-effort on the accelerator: torch may not be installed at Phase 0, so its absence is
    recorded rather than raised. Requested packages that are not installed are marked accordingly.
    """
    env: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
    }

    torch_info: dict[str, Any] = {"installed": False}
    try:
        import torch  # noqa: PLC0415 — optional, captured only if present

        torch_info = {
            "installed": True,
            "version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_version": torch.version.cuda,
            "device_name": (
                torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
            ),
        }
    except ImportError:
        pass
    env["torch"] = torch_info

    versions: dict[str, str] = {}
    for name in package_names or []:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = "not-installed"
    env["packages"] = versions
    return env


def build_manifest(
    *,
    config: RunConfig,
    data_hash: str,
    run_id: str,
    repo_root: Path | None = None,
    package_names: list[str] | None = None,
) -> dict[str, Any]:
    """Assemble a run manifest carrying exactly the five required identifiers."""
    if not run_id or not run_id.strip():
        raise ProvenanceError("run_id must be a non-empty string")
    if not isinstance(data_hash, str) or not data_hash.strip():
        raise ProvenanceError("data_hash must be a non-empty string")

    code = capture_code_state(repo_root)
    identifiers: dict[str, Any] = {
        "config_hash": compute_config_hash(config),
        "code_sha": code.sha,
        "data_hash": data_hash,
        "seed": config.seed,
        "environment": capture_environment(package_names),
    }
    # Fail loudly if the identifier set ever drifts from REQUIRED_IDENTIFIERS.
    if set(identifiers) != set(REQUIRED_IDENTIFIERS):
        raise ProvenanceError(
            f"identifier set {sorted(identifiers)} != required {sorted(REQUIRED_IDENTIFIERS)}"
        )
    return {
        "manifest_version": MANIFEST_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "code_dirty": code.dirty,
        "config": config.to_canonical_dict(),
        "identifiers": identifiers,
    }


def write_provenance(
    run_dir: Path,
    *,
    config: RunConfig,
    data_hash: str,
    run_id: str,
    repo_root: Path | None = None,
    package_names: list[str] | None = None,
) -> Path:
    """Write ``<run_dir>/provenance.json`` and return its path. Refuses to overwrite an existing one."""
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / MANIFEST_FILENAME
    if manifest_path.exists():
        raise ProvenanceError(
            f"manifest already exists at {manifest_path}; run IDs are never reused (AGENTS.md §8)"
        )
    manifest = build_manifest(
        config=config,
        data_hash=data_hash,
        run_id=run_id,
        repo_root=repo_root,
        package_names=package_names,
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path


def validate_run_dir(run_dir: Path) -> dict[str, Any]:
    """Validate that a run dir has a manifest with all five non-empty identifiers.

    Returns the parsed manifest on success; raises :class:`ProvenanceError` listing what is wrong.
    """
    manifest_path = run_dir / MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise ProvenanceError(f"no {MANIFEST_FILENAME} in {run_dir}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProvenanceError(f"manifest at {manifest_path} is not valid JSON: {exc}") from exc

    identifiers = manifest.get("identifiers")
    if not isinstance(identifiers, dict):
        raise ProvenanceError(f"manifest at {manifest_path} has no 'identifiers' object")

    present = set(identifiers)
    required = set(REQUIRED_IDENTIFIERS)
    missing = required - present
    extra = present - required
    if missing or extra:
        raise ProvenanceError(
            f"identifiers in {manifest_path} invalid: missing={sorted(missing)}, extra={sorted(extra)}"
        )
    empty = [k for k in REQUIRED_IDENTIFIERS if identifiers[k] in (None, "", {}, [])]
    if empty:
        raise ProvenanceError(f"identifiers in {manifest_path} are empty: {empty}")
    return manifest
