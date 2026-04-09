"""Read-only data models for the Visualization Layer.

Frozen Pydantic models providing a stable access boundary between
the repository and later visualization components (replay logic,
viewer state, rendering).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from axis.framework.config import ExperimentConfig
from axis.framework.persistence import ExperimentMetadata, RunMetadata
from axis.framework.run import RunConfig, RunSummary
from axis.sdk.trace import BaseEpisodeTrace


class ReplayStepDescriptor(BaseModel):
    """Lightweight replay-readiness metadata for a single step."""

    model_config = ConfigDict(frozen=True)

    step_index: int
    has_world_before: bool
    has_world_after: bool
    has_intermediate_snapshots: tuple[str, ...]
    has_agent_position: bool
    has_vitality: bool
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
    episode_trace: BaseEpisodeTrace
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
