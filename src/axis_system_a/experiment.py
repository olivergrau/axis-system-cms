"""Experiment-level configuration, resolution, and result structures.

Provides the formal data contracts for the Experimentation Framework:
- ExperimentConfig / ExperimentType
- Parameter addressing for OFAT variations
- Deterministic run-config resolution
- ExperimentResult / ExperimentSummary
"""

from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axis_system_a.config import SimulationConfig
from axis_system_a.run import RunConfig, RunResult, RunSummary
from axis_system_a.types import Position


# ---------------------------------------------------------------------------
# Experiment types
# ---------------------------------------------------------------------------


class ExperimentType(str, enum.Enum):
    """Canonical experiment types."""

    SINGLE_RUN = "single_run"
    OFAT = "ofat"


# ---------------------------------------------------------------------------
# Parameter addressing
# ---------------------------------------------------------------------------

# Sections on SimulationConfig that can be addressed via dot-path.
_ADDRESSABLE_SECTIONS = frozenset({
    "general", "world", "agent", "policy", "transition", "execution", "logging",
})


def get_config_value(config: SimulationConfig, path: str) -> Any:
    """Read a value from a SimulationConfig by dot-path.

    Example: ``get_config_value(cfg, "agent.initial_energy")``

    Raises :class:`ValueError` if the path is invalid.
    """
    section_name, field_name = _parse_path(path)
    section = getattr(config, section_name)
    if not hasattr(section, field_name):
        raise ValueError(
            f"Field '{field_name}' does not exist on '{section_name}' config"
        )
    return getattr(section, field_name)


def set_config_value(
    config: SimulationConfig, path: str, value: Any,
) -> SimulationConfig:
    """Return a copy of *config* with one field overridden at *path*.

    The original config is not mutated.

    Raises :class:`ValueError` if the path is invalid.
    """
    section_name, field_name = _parse_path(path)
    section = getattr(config, section_name)
    if not hasattr(section, field_name):
        raise ValueError(
            f"Field '{field_name}' does not exist on '{section_name}' config"
        )
    new_section = section.model_copy(update={field_name: value})
    return config.model_copy(update={section_name: new_section})


def _parse_path(path: str) -> tuple[str, str]:
    """Split a dot-path into (section, field) and validate the section."""
    parts = path.split(".")
    if len(parts) != 2:
        raise ValueError(
            f"Path must be 'section.field' (got {path!r} with {len(parts)} parts)"
        )
    section_name, field_name = parts
    if section_name not in _ADDRESSABLE_SECTIONS:
        raise ValueError(
            f"Unknown config section '{section_name}'. "
            f"Valid sections: {sorted(_ADDRESSABLE_SECTIONS)}"
        )
    return section_name, field_name


# ---------------------------------------------------------------------------
# Experiment configuration
# ---------------------------------------------------------------------------


class ExperimentConfig(BaseModel):
    """Top-level input for an experiment.

    Defines how one or more RunConfigs are derived. Does not execute anything.
    """

    model_config = ConfigDict(frozen=True)

    experiment_type: ExperimentType
    baseline: SimulationConfig
    name: str | None = None
    base_seed: int | None = None
    num_episodes_per_run: int = Field(..., gt=0)
    agent_start_position: Position = Field(
        default_factory=lambda: Position(x=0, y=0),
    )

    # OFAT-specific fields (must be None for single_run)
    parameter_path: str | None = None
    parameter_values: tuple[Any, ...] | None = None

    @model_validator(mode="after")
    def _validate_experiment_type_fields(self) -> ExperimentConfig:
        if self.experiment_type == ExperimentType.SINGLE_RUN:
            if self.parameter_path is not None:
                raise ValueError(
                    "parameter_path must be None for single_run experiments"
                )
            if self.parameter_values is not None:
                raise ValueError(
                    "parameter_values must be None for single_run experiments"
                )
        elif self.experiment_type == ExperimentType.OFAT:
            if self.parameter_path is None:
                raise ValueError(
                    "parameter_path is required for ofat experiments"
                )
            if self.parameter_values is None:
                raise ValueError(
                    "parameter_values is required for ofat experiments"
                )
            if len(self.parameter_values) == 0:
                raise ValueError(
                    "parameter_values must not be empty for ofat experiments"
                )
            # Validate path is valid against baseline
            get_config_value(self.baseline, self.parameter_path)
        return self


# ---------------------------------------------------------------------------
# Run-config resolution
# ---------------------------------------------------------------------------


def resolve_run_configs(config: ExperimentConfig) -> tuple[RunConfig, ...]:
    """Expand an ExperimentConfig into concrete RunConfig instances.

    Resolution is deterministic: same config always produces the same RunConfigs
    in the same order.
    """
    if config.experiment_type == ExperimentType.SINGLE_RUN:
        return _resolve_single_run(config)
    elif config.experiment_type == ExperimentType.OFAT:
        return _resolve_ofat(config)
    raise ValueError(f"Unknown experiment type: {config.experiment_type}")


def _resolve_single_run(config: ExperimentConfig) -> tuple[RunConfig, ...]:
    run_seed = config.base_seed
    return (
        RunConfig(
            simulation=config.baseline,
            num_episodes=config.num_episodes_per_run,
            base_seed=run_seed,
            agent_start_position=config.agent_start_position,
            run_id="run-0000",
        ),
    )


def _resolve_ofat(config: ExperimentConfig) -> tuple[RunConfig, ...]:
    assert config.parameter_path is not None
    assert config.parameter_values is not None

    runs: list[RunConfig] = []
    for i, value in enumerate(config.parameter_values):
        varied_sim = set_config_value(config.baseline, config.parameter_path, value)
        run_seed = (config.base_seed + i * 1000) if config.base_seed is not None else None
        runs.append(
            RunConfig(
                simulation=varied_sim,
                num_episodes=config.num_episodes_per_run,
                base_seed=run_seed,
                agent_start_position=config.agent_start_position,
                run_id=f"run-{i:04d}",
            ),
        )
    return tuple(runs)


# ---------------------------------------------------------------------------
# Experiment result structures
# ---------------------------------------------------------------------------


class RunSummaryEntry(BaseModel):
    """Per-run entry within an ExperimentSummary."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    variation_description: str
    summary: RunSummary
    delta_mean_steps: float | None = None
    delta_mean_final_energy: float | None = None
    delta_death_rate: float | None = None


class ExperimentSummary(BaseModel):
    """Aggregated summary across all runs in an experiment."""

    model_config = ConfigDict(frozen=True)

    num_runs: int = Field(..., ge=0)
    run_entries: tuple[RunSummaryEntry, ...]


class ExperimentResult(BaseModel):
    """Complete result of an experiment. Passive result object only."""

    model_config = ConfigDict(frozen=True)

    experiment_config: ExperimentConfig
    run_results: tuple[RunResult, ...]
    summary: ExperimentSummary


# ---------------------------------------------------------------------------
# Experiment summary computation
# ---------------------------------------------------------------------------


def compute_experiment_summary(
    run_results: tuple[RunResult, ...],
    config: ExperimentConfig,
    baseline_summary: RunSummary | None = None,
) -> ExperimentSummary:
    """Build an ExperimentSummary from completed run results.

    For OFAT experiments, if *baseline_summary* is provided, delta fields
    are computed relative to it for each run entry.
    """
    entries: list[RunSummaryEntry] = []

    for i, rr in enumerate(run_results):
        desc = variation_description(config, i)
        delta_steps: float | None = None
        delta_energy: float | None = None
        delta_death: float | None = None

        if baseline_summary is not None:
            delta_steps = rr.summary.mean_steps - baseline_summary.mean_steps
            delta_energy = rr.summary.mean_final_energy - baseline_summary.mean_final_energy
            delta_death = rr.summary.death_rate - baseline_summary.death_rate

        entries.append(
            RunSummaryEntry(
                run_id=rr.run_id,
                variation_description=desc,
                summary=rr.summary,
                delta_mean_steps=delta_steps,
                delta_mean_final_energy=delta_energy,
                delta_death_rate=delta_death,
            ),
        )

    return ExperimentSummary(
        num_runs=len(run_results),
        run_entries=tuple(entries),
    )


def variation_description(config: ExperimentConfig, run_index: int) -> str:
    """Generate a human-readable variation descriptor for a run."""
    if config.experiment_type == ExperimentType.SINGLE_RUN:
        return "baseline"
    # OFAT
    assert config.parameter_path is not None
    assert config.parameter_values is not None
    value = config.parameter_values[run_index]
    return f"{config.parameter_path}={value}"
