"""Read-only data models for the Visualization Layer.

These frozen Pydantic models provide a stable access boundary between
the repository/persistence layer and later visualization components
(replay logic, viewer state, rendering). They expose validated identity,
structure, and references to the underlying typed artifacts.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from axis_system_a.experiment import ExperimentConfig
from axis_system_a.repository import ExperimentMetadata, RunMetadata
from axis_system_a.results import EpisodeResult
from axis_system_a.run import RunConfig, RunSummary


class ReplayPhaseAvailability(BaseModel):
    """Indicates which transition phases have valid world snapshots."""

    model_config = ConfigDict(frozen=True)

    before: bool
    after_regen: bool
    after_action: bool


class ReplayStepDescriptor(BaseModel):
    """Lightweight replay-readiness metadata for a single step."""

    model_config = ConfigDict(frozen=True)

    step_index: int
    phase_availability: ReplayPhaseAvailability
    has_agent_position: bool
    has_agent_energy: bool
    has_world_state: bool


class ReplayValidationResult(BaseModel):
    """Outcome of validating an episode against the replay contract."""

    model_config = ConfigDict(frozen=True)

    valid: bool
    total_steps: int
    grid_width: int | None = None
    grid_height: int | None = None
    violations: tuple[str, ...] = ()
    step_descriptors: tuple[ReplayStepDescriptor, ...] = ()


class ReplayEpisodeHandle(BaseModel):
    """Validated episode ready for replay consumption."""

    model_config = ConfigDict(frozen=True)

    experiment_id: str
    run_id: str
    episode_index: int
    episode_result: EpisodeResult
    validation: ReplayValidationResult


class ReplayRunHandle(BaseModel):
    """Run-level handle exposing config, metadata, and episode listing."""

    model_config = ConfigDict(frozen=True)

    experiment_id: str
    run_id: str
    run_config: RunConfig
    run_metadata: RunMetadata | None = None
    run_summary: RunSummary | None = None
    available_episodes: tuple[int, ...]


class ReplayExperimentHandle(BaseModel):
    """Experiment-level handle exposing config, metadata, and run listing."""

    model_config = ConfigDict(frozen=True)

    experiment_id: str
    experiment_config: ExperimentConfig
    experiment_metadata: ExperimentMetadata | None = None
    available_runs: tuple[str, ...]
