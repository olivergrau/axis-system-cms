"""Framework configuration types and OFAT parameter path resolution."""

from __future__ import annotations

import copy
import enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig


# ---------------------------------------------------------------------------
# Sub-configuration types
# ---------------------------------------------------------------------------


class GeneralConfig(BaseModel):
    """General experiment configuration."""

    model_config = ConfigDict(frozen=True)

    seed: int


class ExecutionConfig(BaseModel):
    """Execution control parameters."""

    model_config = ConfigDict(frozen=True)

    max_steps: int = Field(..., gt=0)
    trace_mode: str = "full"
    parallelism_mode: str = "sequential"
    max_workers: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def _validate_speedup_fields(self) -> ExecutionConfig:
        if self.trace_mode not in {"full", "light", "delta"}:
            raise ValueError("trace_mode must be 'full', 'light', or 'delta'")
        if self.parallelism_mode not in {"sequential", "episodes", "runs"}:
            raise ValueError(
                "parallelism_mode must be 'sequential', 'episodes', or 'runs'"
            )
        return self


class LoggingConfig(BaseModel):
    """Logging configuration.

    Controls console output, JSONL file logging, and verbosity.
    """

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    console_enabled: bool = True
    jsonl_enabled: bool = False
    jsonl_path: str | None = None
    include_decision_trace: bool = True
    include_transition_trace: bool = True
    verbosity: str = "compact"  # "compact" or "verbose"

    @model_validator(mode="after")
    def _validate_jsonl(self) -> LoggingConfig:
        if self.jsonl_enabled and self.jsonl_path is None:
            raise ValueError("jsonl_path must be set when jsonl_enabled is True")
        return self


# ---------------------------------------------------------------------------
# Composite framework config
# ---------------------------------------------------------------------------


class FrameworkConfig(BaseModel):
    """Complete framework configuration.

    Contains all framework-owned settings. System-specific settings
    are not included here -- they travel as an opaque dict in
    ExperimentConfig.system.
    """

    model_config = ConfigDict(frozen=True)

    general: GeneralConfig
    execution: ExecutionConfig
    world: BaseWorldConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


# ---------------------------------------------------------------------------
# Experiment types
# ---------------------------------------------------------------------------


class ExperimentType(str, enum.Enum):
    """Type of experiment."""

    SINGLE_RUN = "single_run"
    OFAT = "ofat"


class ExperimentConfig(BaseModel):
    """Top-level experiment definition.

    Per Q6=C: framework sections are flat at the top level
    (general, execution, world, logging). The system section
    is an opaque dict validated by the system at instantiation.
    """

    model_config = ConfigDict(frozen=True)

    # ── System identification ──
    system_type: str

    # ── Experiment parameters ──
    experiment_type: ExperimentType

    # ── Framework config (flat sections) ──
    general: GeneralConfig
    execution: ExecutionConfig
    world: BaseWorldConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # ── System config (opaque) ──
    system: dict[str, Any]

    # ── Run parameters ──
    num_episodes_per_run: int = Field(..., gt=0)
    agent_start_position: Position = Field(
        default_factory=lambda: Position(x=0, y=0)
    )

    # ── OFAT parameters ──
    parameter_path: str | None = None
    parameter_values: tuple[Any, ...] | None = None

    @model_validator(mode="after")
    def _validate_ofat(self) -> ExperimentConfig:
        if self.experiment_type == ExperimentType.SINGLE_RUN:
            if self.parameter_path is not None or self.parameter_values is not None:
                raise ValueError(
                    "parameter_path and parameter_values must be None for single_run"
                )
        elif self.experiment_type == ExperimentType.OFAT:
            if self.parameter_path is None or self.parameter_values is None:
                raise ValueError(
                    "parameter_path and parameter_values are required for ofat"
                )
            if len(self.parameter_values) == 0:
                raise ValueError("parameter_values must be non-empty for ofat")
        return self


# ---------------------------------------------------------------------------
# Convenience extractor
# ---------------------------------------------------------------------------


def extract_framework_config(experiment_config: ExperimentConfig) -> FrameworkConfig:
    """Extract the FrameworkConfig from an ExperimentConfig."""
    return FrameworkConfig(
        general=experiment_config.general,
        execution=experiment_config.execution,
        world=experiment_config.world,
        logging=experiment_config.logging,
    )


# ---------------------------------------------------------------------------
# OFAT parameter path resolution
# ---------------------------------------------------------------------------

# Valid framework sections for OFAT addressing
_FRAMEWORK_SECTIONS: frozenset[str] = frozenset(
    {"general", "execution", "world", "logging"}
)


def parse_parameter_path(path: str) -> tuple[str, str, str]:
    """Parse a prefixed OFAT parameter path.

    Args:
        path: Dot-separated path like 'framework.execution.max_steps'
              or 'system.policy.temperature'.

    Returns:
        Tuple of (domain, section, field).
        domain is 'framework' or 'system'.

    Raises:
        ValueError: If the path is malformed or references invalid sections.
    """
    parts = path.split(".")
    if len(parts) != 3:
        raise ValueError(
            f"Parameter path must have exactly 3 segments "
            f"(domain.section.field), got {len(parts)}: '{path}'"
        )
    domain, section, field = parts
    if domain not in ("framework", "system"):
        raise ValueError(
            f"Parameter path domain must be 'framework' or 'system', "
            f"got '{domain}' in '{path}'"
        )
    if domain == "framework" and section not in _FRAMEWORK_SECTIONS:
        raise ValueError(
            f"Invalid framework section '{section}' in '{path}'. "
            f"Valid sections: {sorted(_FRAMEWORK_SECTIONS)}"
        )
    return domain, section, field


def get_config_value(config: ExperimentConfig, path: str) -> Any:
    """Read a value from an ExperimentConfig using a prefixed dot-path.

    Args:
        config: The experiment config to read from.
        path: Prefixed dot-path (e.g., 'framework.execution.max_steps').

    Returns:
        The value at the specified path.

    Raises:
        ValueError: If the path is invalid.
        KeyError: If the field does not exist.
    """
    domain, section, field = parse_parameter_path(path)
    if domain == "framework":
        section_obj = getattr(config, section)
        if not hasattr(section_obj, field):
            raise KeyError(
                f"Framework section '{section}' has no field '{field}'"
            )
        return getattr(section_obj, field)
    else:  # system
        if section not in config.system:
            raise KeyError(f"System config has no section '{section}'")
        section_dict = config.system[section]
        if field not in section_dict:
            raise KeyError(
                f"System section '{section}' has no field '{field}'"
            )
        return section_dict[field]


def set_config_value(
    config: ExperimentConfig, path: str, value: Any
) -> ExperimentConfig:
    """Return a new ExperimentConfig with one value overridden.

    Does not mutate the original config. Uses model_copy for framework
    fields and dict copy for system fields.

    Args:
        config: The experiment config to copy and modify.
        path: Prefixed dot-path (e.g., 'system.policy.temperature').
        value: The new value.

    Returns:
        A new ExperimentConfig with the value overridden.

    Raises:
        ValueError: If the path is invalid.
    """
    domain, section, field = parse_parameter_path(path)
    if domain == "framework":
        section_obj = getattr(config, section)
        new_section = section_obj.model_copy(update={field: value})
        return config.model_copy(update={section: new_section})
    else:  # system
        new_system = copy.deepcopy(dict(config.system))
        if section not in new_system:
            new_system[section] = {}
        new_system[section][field] = value
        return config.model_copy(update={"system": new_system})
