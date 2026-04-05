"""Visualization Layer – public API.

Re-exports the primary types and entry points for VWP1:
artifact access, validation, replay models, and errors.
"""

from axis_system_a.visualization.errors import (
    EpisodeNotFoundError,
    ExperimentNotFoundError,
    MalformedArtifactError,
    ReplayContractViolation,
    ReplayError,
    RunNotFoundError,
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

__all__ = [
    # Access service
    "ReplayAccessService",
    # Validation
    "validate_episode_for_replay",
    # Models
    "ReplayEpisodeHandle",
    "ReplayExperimentHandle",
    "ReplayPhaseAvailability",
    "ReplayRunHandle",
    "ReplayStepDescriptor",
    "ReplayValidationResult",
    # Errors
    "EpisodeNotFoundError",
    "ExperimentNotFoundError",
    "MalformedArtifactError",
    "ReplayContractViolation",
    "ReplayError",
    "RunNotFoundError",
]
