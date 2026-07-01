"""Provenance-writer tests (TASK P0.003): manifests carry exactly the 5 identifiers; missing → reject."""

import json

import pytest

import dataclasses

from ezhuthu_jepa.config import SCHEMA_VERSION, RunConfig
from ezhuthu_jepa.provenance import (
    REQUIRED_IDENTIFIERS,
    SEED_DETERMINISTIC,
    ProvenanceError,
    compute_config_hash,
    hash_paths,
    validate_run_dir,
    write_provenance,
)


def _config(seed: int = 0) -> RunConfig:
    return RunConfig.from_dict(
        {
            "schema_version": SCHEMA_VERSION,
            "objective": "seam_jepa",
            "seed": seed,
            "mask_ratio": 0.5,
        }
    )


def test_write_creates_manifest_with_exactly_five_identifiers(tmp_path):
    run_dir = tmp_path / "phaseA-smoke-001"
    manifest_path = write_provenance(
        run_dir, config=_config(seed=7), data_hash="sha256:deadbeef", run_id="phaseA-smoke-001"
    )
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert set(manifest["identifiers"]) == set(REQUIRED_IDENTIFIERS)
    # seed flows from the config, single source of truth.
    assert manifest["identifiers"]["seed"] == 7
    # code_sha is a real, non-empty git SHA (tests run inside the repo).
    assert manifest["identifiers"]["code_sha"]


def test_written_manifest_validates(tmp_path):
    run_dir = tmp_path / "run-ok"
    write_provenance(run_dir, config=_config(), data_hash="sha256:abc", run_id="run-ok")
    manifest = validate_run_dir(run_dir)
    assert manifest["run_id"] == "run-ok"


def test_validate_rejects_missing_identifier(tmp_path):
    run_dir = tmp_path / "run-tampered"
    path = write_provenance(run_dir, config=_config(), data_hash="sha256:abc", run_id="run-tampered")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    del manifest["identifiers"]["data_hash"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ProvenanceError, match="missing=.*data_hash"):
        validate_run_dir(run_dir)


def test_validate_rejects_empty_identifier(tmp_path):
    run_dir = tmp_path / "run-empty"
    path = write_provenance(run_dir, config=_config(), data_hash="sha256:abc", run_id="run-empty")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["identifiers"]["data_hash"] = ""
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ProvenanceError, match="empty"):
        validate_run_dir(run_dir)


def test_validate_rejects_absent_manifest(tmp_path):
    with pytest.raises(ProvenanceError, match="no provenance.json"):
        validate_run_dir(tmp_path / "does-not-exist")


def test_config_hash_is_order_independent_and_stable():
    assert compute_config_hash(_config()) == compute_config_hash(_config())
    assert compute_config_hash(_config(seed=1)) != compute_config_hash(_config(seed=2))


def test_write_refuses_to_overwrite(tmp_path):
    run_dir = tmp_path / "run-dup"
    write_provenance(run_dir, config=_config(), data_hash="sha256:abc", run_id="run-dup")
    with pytest.raises(ProvenanceError, match="already exists"):
        write_provenance(run_dir, config=_config(), data_hash="sha256:abc", run_id="run-dup")


def test_hash_paths_pins_content(tmp_path):
    f1 = tmp_path / "a.txt"
    f1.write_text("hello", encoding="utf-8")
    h1 = hash_paths([f1])
    f1.write_text("changed", encoding="utf-8")
    assert hash_paths([f1]) != h1


def test_hash_paths_missing_file_raises(tmp_path):
    with pytest.raises(ProvenanceError, match="missing file"):
        hash_paths([tmp_path / "nope.txt"])


# --- generalized provenance: seedless / non-RunConfig runs (DEC-0006) ---


@dataclasses.dataclass(frozen=True)
class _FakeRenderConfig:
    font: str
    px: int


def test_deterministic_seed_with_dataclass_config(tmp_path):
    run_dir = tmp_path / "render-run"
    write_provenance(
        run_dir,
        config=_FakeRenderConfig(font="Noto", px=96),
        data_hash="sha256:font",
        run_id="render-run",
        seed=SEED_DETERMINISTIC,
    )
    manifest = validate_run_dir(run_dir)  # deterministic is a non-empty, valid identifier
    assert manifest["identifiers"]["seed"] == SEED_DETERMINISTIC
    assert manifest["config"] == {"font": "Noto", "px": 96}


def test_mapping_config_is_hashable(tmp_path):
    run_dir = tmp_path / "map-run"
    write_provenance(
        run_dir,
        config={"a": 1, "b": 2},
        data_hash="sha256:x",
        run_id="map-run",
        seed=SEED_DETERMINISTIC,
    )
    # order-independent hashing over a mapping
    assert compute_config_hash({"a": 1, "b": 2}) == compute_config_hash({"b": 2, "a": 1})


def test_non_runconfig_without_seed_raises(tmp_path):
    with pytest.raises(ProvenanceError, match="seed is required"):
        write_provenance(
            tmp_path / "r", config={"a": 1}, data_hash="sha256:x", run_id="r"
        )


def test_bad_seed_type_raises(tmp_path):
    with pytest.raises(ProvenanceError, match="seed must be"):
        write_provenance(
            tmp_path / "r", config={"a": 1}, data_hash="sha256:x", run_id="r", seed=1.5
        )
