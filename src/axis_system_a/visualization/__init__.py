"""Visualization Layer – public API.

Re-exports the primary types and entry points for VWP1 and VWP2:
artifact access, validation, replay models, snapshot resolution, and errors.
"""

from axis_system_a.visualization.errors import (
    EpisodeNotFoundError,
    ExperimentNotFoundError,
    MalformedArtifactError,
    PhaseNotAvailableError,
    ReplayContractViolation,
    ReplayError,
    RunNotFoundError,
    StepOutOfBoundsError,
)
from axis_system_a.visualization.replay_access import ReplayAccessService
from axis_system_a.visualization.replay_models import (
    ReplayEpisodeHandle,
    ReplayExperimentHandle,
    ReplayPhaseAvailability,
    ReplayRunHandle,
    ReplayStepDescriptor,
    ReplayValidationResult,
)
from axis_system_a.visualization.replay_validation import (
    validate_episode_for_replay,
)
from axis_system_a.visualization.snapshot_models import (
    ReplayCoordinate,
    ReplayPhase,
    ReplaySnapshot,
)
from axis_system_a.visualization.snapshot_resolver import SnapshotResolver

__all__ = [
    # Access service
    "ReplayAccessService",
    # Validation
    "validate_episode_for_replay",
    # VWP1 Models
    "ReplayEpisodeHandle",
    "ReplayExperimentHandle",
    "ReplayPhaseAvailability",
    "ReplayRunHandle",
    "ReplayStepDescriptor",
    "ReplayValidationResult",
    # VWP2 Snapshot models
    "ReplayCoordinate",
    "ReplayPhase",
    "ReplaySnapshot",
    # VWP2 Resolver
    "SnapshotResolver",
    # Errors
    "EpisodeNotFoundError",
    "ExperimentNotFoundError",
    "MalformedArtifactError",
    "PhaseNotAvailableError",
    "ReplayContractViolation",
    "ReplayError",
    "RunNotFoundError",
    "StepOutOfBoundsError",
]
