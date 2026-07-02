"""Sweep-orchestrator tests (TASK P1.003 / pilot): arm construction + the LAUNCH-A gate."""

import pytest
import yaml

from ezhuthu_jepa.train.pretrain import PretrainConfig
from ezhuthu_jepa.train import sweep as S


def test_build_arms_is_objective_major_and_complete():
    arms = S.build_arms(["seam_jepa", "block_jepa"], [0, 1, 2])
    assert arms == [
        ("seam_jepa", 0), ("seam_jepa", 1), ("seam_jepa", 2),
        ("block_jepa", 0), ("block_jepa", 1), ("block_jepa", 2),
    ]


def test_arm_config_injects_objective_and_seed_over_shared_base():
    base = {"mask_ratio": 0.25, "index_jsonl": "x", "image_dir": "y", "max_steps": 5}
    cfg = S.arm_config(base, "mae_seam", 2)
    assert isinstance(cfg, PretrainConfig)
    assert (cfg.objective, cfg.seed, cfg.mask_ratio, cfg.max_steps) == ("mae_seam", 2, 0.25, 5)


def _write_sweep(tmp_path, seeds, prefix="phase1-sweep"):
    cfg = {
        "run_prefix": prefix,
        "objectives": ["seam_jepa", "block_jepa", "mae_seam"],
        "seeds": seeds,
        "base": {"mask_ratio": 0.25, "index_jsonl": "x", "image_dir": "y", "device": "cpu"},
    }
    p = tmp_path / "sweep.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p


def test_dry_run_starts_nothing(tmp_path):
    results = S.run_sweep(_write_sweep(tmp_path, [0, 1, 2]), tmp_path / "runs", execute=False)
    assert results == []
    assert not (tmp_path / "runs").exists()          # no arm dirs created on a dry-run


def test_full_sweep_is_refused_without_launch_a_approval(tmp_path):
    with pytest.raises(SystemExit, match="LAUNCH-A"):
        S.run_sweep(_write_sweep(tmp_path, [0, 1, 2]), tmp_path / "runs", execute=True)


def test_base_may_not_set_swept_fields(tmp_path):
    cfg = {"run_prefix": "p", "objectives": ["seam_jepa"], "seeds": [0],
           "base": {"mask_ratio": 0.25, "index_jsonl": "x", "image_dir": "y", "seed": 0}}
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    with pytest.raises(ValueError, match="must not set 'seed'"):
        S.run_sweep(p, tmp_path / "runs", execute=False)


def test_missing_key_raises(tmp_path):
    p = tmp_path / "m.yaml"
    p.write_text(yaml.safe_dump({"objectives": ["seam_jepa"], "seeds": [0]}), encoding="utf-8")
    with pytest.raises(ValueError, match="missing required key 'base'"):
        S.run_sweep(p, tmp_path / "runs", execute=False)
