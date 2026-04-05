"""Visualization Layer – public API.

Re-exports the primary types and entry points for VWP1–VWP5:
artifact access, validation, replay models, snapshot resolution,
viewer state, transitions, playback controller, view models, and errors.
"""

from axis_system_a.visualization.errors import (
    CellOutOfBoundsError,
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
from axis_system_a.visualization.viewer_state import (
    PlaybackMode,
    ViewerState,
    create_initial_state,
)
from axis_system_a.visualization.playback_controller import (
    PlaybackController,
    get_final_coordinate,
    get_initial_coordinate,
    is_at_final,
    is_at_initial,
)
from axis_system_a.visualization.view_model_builder import ViewModelBuilder
from axis_system_a.visualization.view_models import (
    ActionContextViewModel,
    AgentViewModel,
    GridCellViewModel,
    GridViewModel,
    SelectionType,
    SelectionViewModel,
    StatusBarViewModel,
    ViewerFrameViewModel,
)
from axis_system_a.visualization.viewer_state_transitions import (
    clear_selection,
    next_step,
    previous_step,
    seek,
    select_agent,
    select_cell,
    set_phase,
    set_playback_mode,
)

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
    # VWP3 Viewer state
    "PlaybackMode",
    "ViewerState",
    "create_initial_state",
    # VWP3 Transitions
    "clear_selection",
    "next_step",
    "previous_step",
    "seek",
    "select_agent",
    "select_cell",
    "set_phase",
    "set_playback_mode",
    # VWP4 Playback controller
    "PlaybackController",
    "get_final_coordinate",
    "get_initial_coordinate",
    "is_at_final",
    "is_at_initial",
    # VWP5 View models
    "ActionContextViewModel",
    "AgentViewModel",
    "GridCellViewModel",
    "GridViewModel",
    "SelectionType",
    "SelectionViewModel",
    "StatusBarViewModel",
    "ViewerFrameViewModel",
    # VWP5 Builder
    "ViewModelBuilder",
    # Errors
    "CellOutOfBoundsError",
    "EpisodeNotFoundError",
    "ExperimentNotFoundError",
    "MalformedArtifactError",
    "PhaseNotAvailableError",
    "ReplayContractViolation",
    "ReplayError",
    "RunNotFoundError",
    "StepOutOfBoundsError",
]
