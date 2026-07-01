"""Versioned, validated run-configuration contract (TASK P0.004).

The config is the single source of truth for the knobs that define an experiment run. It is
deliberately small at Phase 0 — one honest field per genuinely-consumed knob — and grows only as
real consumers appear (masking at PA.004, the pretraining loop at PA.005). Every field is recorded
in the schema-consumer audit at ``notes/schema-audits/ezhuthu_jepa-config.md`` (AGENTS.md §2.2).

Loading is strict: unknown keys, missing keys, wrong types, out-of-range values, and a mismatched
schema version all raise :class:`ConfigValidationError`. This rejects silent config drift *before*
an expensive run rather than after (AGENTS.md §2.4).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any

# Bump when the RunConfig field set or semantics change; a manifest carries this so an old run's
# config can never be silently reinterpreted under a new schema.
SCHEMA_VERSION = "0.1.0"

# The self-supervised objectives compared in the G1 sweep. One switched variable, identical
# architecture/compute/mask-ratio across all three (spec §3 K1/K3; RUNBOOK --objective).
ALLOWED_OBJECTIVES = ("seam_jepa", "block_jepa", "mae_seam")


class ConfigValidationError(ValueError):
    """Raised when a config dict is out of contract (unknown/missing key, bad type or range)."""


@dataclass(frozen=True)
class RunConfig:
    """Immutable, hashable configuration for a single run.

    Fields:
        schema_version: must equal :data:`SCHEMA_VERSION`; guards against schema drift.
        objective: one of :data:`ALLOWED_OBJECTIVES`; selects the SSL objective under test.
        seed: non-negative RNG seed; also copied into the provenance manifest.
        mask_ratio: fraction of the akshara masked, strictly in ``(0, 1)``; held fixed across
            objectives so K1/K3 vary only the mask *boundary* / target, never the ratio.
    """

    schema_version: str
    objective: str
    seed: int
    mask_ratio: float

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ConfigValidationError(
                f"schema_version {self.schema_version!r} != supported {SCHEMA_VERSION!r}"
            )
        if self.objective not in ALLOWED_OBJECTIVES:
            raise ConfigValidationError(
                f"objective {self.objective!r} not in {ALLOWED_OBJECTIVES}"
            )
        # bool is a subclass of int — reject it explicitly so True/False can't pose as a seed.
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ConfigValidationError(f"seed must be an int, got {type(self.seed).__name__}")
        if self.seed < 0:
            raise ConfigValidationError(f"seed must be non-negative, got {self.seed}")
        if not isinstance(self.mask_ratio, (int, float)) or isinstance(self.mask_ratio, bool):
            raise ConfigValidationError(
                f"mask_ratio must be a number, got {type(self.mask_ratio).__name__}"
            )
        if not 0.0 < float(self.mask_ratio) < 1.0:
            raise ConfigValidationError(
                f"mask_ratio must be in the open interval (0, 1), got {self.mask_ratio}"
            )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunConfig":
        """Build a validated :class:`RunConfig` from a plain dict.

        Rejects unknown and missing keys before construction, so a typo or a stale field can never
        be silently ignored. Value-level checks run in ``__post_init__``.
        """
        if not isinstance(data, dict):
            raise ConfigValidationError(f"config must be a dict, got {type(data).__name__}")
        allowed = {f.name for f in fields(cls)}
        provided = set(data)
        unknown = provided - allowed
        if unknown:
            raise ConfigValidationError(f"unknown config key(s): {sorted(unknown)}")
        missing = allowed - provided
        if missing:
            raise ConfigValidationError(f"missing config key(s): {sorted(missing)}")
        return cls(**data)

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return the config as an ordered plain dict for stable hashing / manifest embedding."""
        return {key: asdict(self)[key] for key in (f.name for f in fields(self))}
