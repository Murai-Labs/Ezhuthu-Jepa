"""Config-contract tests (TASK P0.004): loading an out-of-contract config raises a typed error."""

import pytest

from ezhuthu_jepa.config import (
    ALLOWED_OBJECTIVES,
    SCHEMA_VERSION,
    ConfigValidationError,
    RunConfig,
)


def _valid_dict() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "objective": "seam_jepa",
        "seed": 0,
        "mask_ratio": 0.5,
    }


def test_valid_config_loads():
    cfg = RunConfig.from_dict(_valid_dict())
    assert cfg.objective == "seam_jepa"
    assert cfg.seed == 0
    assert cfg.to_canonical_dict() == _valid_dict()


def test_all_allowed_objectives_load():
    for objective in ALLOWED_OBJECTIVES:
        cfg = RunConfig.from_dict({**_valid_dict(), "objective": objective})
        assert cfg.objective == objective


def test_unknown_key_rejected():
    with pytest.raises(ConfigValidationError, match="unknown config key"):
        RunConfig.from_dict({**_valid_dict(), "learning_rate": 0.1})


def test_missing_key_rejected():
    partial = _valid_dict()
    del partial["mask_ratio"]
    with pytest.raises(ConfigValidationError, match="missing config key"):
        RunConfig.from_dict(partial)


def test_bad_objective_rejected():
    with pytest.raises(ConfigValidationError, match="objective"):
        RunConfig.from_dict({**_valid_dict(), "objective": "diffusion"})


def test_schema_version_mismatch_rejected():
    with pytest.raises(ConfigValidationError, match="schema_version"):
        RunConfig.from_dict({**_valid_dict(), "schema_version": "9.9.9"})


@pytest.mark.parametrize("bad_seed", ["0", 1.5, -1, True])
def test_bad_seed_rejected(bad_seed):
    with pytest.raises(ConfigValidationError, match="seed"):
        RunConfig.from_dict({**_valid_dict(), "seed": bad_seed})


@pytest.mark.parametrize("bad_ratio", [0.0, 1.0, 1.5, -0.1, "0.5", True])
def test_out_of_range_mask_ratio_rejected(bad_ratio):
    with pytest.raises(ConfigValidationError, match="mask_ratio"):
        RunConfig.from_dict({**_valid_dict(), "mask_ratio": bad_ratio})


def test_config_is_frozen():
    cfg = RunConfig.from_dict(_valid_dict())
    with pytest.raises(Exception):
        cfg.seed = 5  # type: ignore[misc]
