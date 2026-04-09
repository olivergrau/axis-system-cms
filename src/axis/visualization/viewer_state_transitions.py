"""Pure state transition functions for ViewerState.

Every function takes a ViewerState (and optional parameters) and
returns a new ViewerState. No mutation. No side effects.
"""

from __future__ import annotations

from axis.visualization.errors import (
    CellOutOfBoundsError,
    StepOutOfBoundsError,
)
from axis.visualization.snapshot_models import ReplayCoordinate
from axis.visualization.viewer_state import (
    OverlayConfig,
    PlaybackMode,
    ViewerState,
)


# -- Navigation ---------------------------------------------------------------


def next_step(state: ViewerState) -> ViewerState:
    """Advance to the next step, preserving current phase.

    Returns *state* unchanged at the last step.
    """
    total = state.episode_handle.validation.total_steps
    if state.coordinate.step_index >= total - 1:
        return state
    return state.model_copy(
        update={
            "coordinate": ReplayCoordinate(
                step_index=state.coordinate.step_index + 1,
                phase_index=state.coordinate.phase_index,
            ),
        },
    )


def previous_step(state: ViewerState) -> ViewerState:
    """Move to the previous step, preserving current phase.

    Returns *state* unchanged at step 0.
    """
    if state.coordinate.step_index <= 0:
        return state
    return state.model_copy(
        update={
            "coordinate": ReplayCoordinate(
                step_index=state.coordinate.step_index - 1,
                phase_index=state.coordinate.phase_index,
            ),
        },
    )


def set_phase(state: ViewerState, phase_index: int) -> ViewerState:
    """Change the current phase without altering the step index."""
    return state.model_copy(
        update={
            "coordinate": ReplayCoordinate(
                step_index=state.coordinate.step_index,
                phase_index=phase_index,
            ),
        },
    )


def seek(state: ViewerState, coordinate: ReplayCoordinate) -> ViewerState:
    """Jump to an arbitrary replay coordinate.

    Raises StepOutOfBoundsError if the coordinate is out of bounds.
    """
    total = state.episode_handle.validation.total_steps
    if coordinate.step_index < 0 or coordinate.step_index >= total:
        raise StepOutOfBoundsError(coordinate.step_index, total)
    return state.model_copy(update={"coordinate": coordinate})


# -- Selection -----------------------------------------------------------------


def select_cell(state: ViewerState, row: int, col: int) -> ViewerState:
    """Select a grid cell, clearing any agent selection."""
    gw = state.episode_handle.validation.grid_width
    gh = state.episode_handle.validation.grid_height
    if gw is None or gh is None:
        raise CellOutOfBoundsError(row, col, 0, 0)
    if row < 0 or row >= gh or col < 0 or col >= gw:
        raise CellOutOfBoundsError(row, col, gw, gh)
    return state.model_copy(
        update={"selected_cell": (row, col), "selected_agent": False},
    )


def select_agent(state: ViewerState) -> ViewerState:
    """Select the agent, clearing any cell selection."""
    return state.model_copy(
        update={"selected_agent": True, "selected_cell": None},
    )


def clear_selection(state: ViewerState) -> ViewerState:
    """Clear all selection state."""
    return state.model_copy(
        update={"selected_cell": None, "selected_agent": False},
    )


# -- Playback ------------------------------------------------------------------


def set_playback_mode(
    state: ViewerState, mode: PlaybackMode,
) -> ViewerState:
    """Change the playback mode."""
    return state.model_copy(update={"playback_mode": mode})


# -- Overlay configuration -----------------------------------------------------


def toggle_overlay_master(state: ViewerState) -> ViewerState:
    """Flip the master overlay flag."""
    cfg = state.overlay_config
    return state.model_copy(
        update={
            "overlay_config": cfg.model_copy(
                update={"master_enabled": not cfg.master_enabled},
            ),
        },
    )


def set_overlay_enabled(
    state: ViewerState, overlay_key: str, enabled: bool,
) -> ViewerState:
    """Enable or disable a specific overlay type by its key.

    *overlay_key* is the key from OverlayTypeDeclaration
    (e.g. "action_preference", "scan_result").
    """
    cfg = state.overlay_config
    if enabled:
        new_set = cfg.enabled_overlays | {overlay_key}
    else:
        new_set = cfg.enabled_overlays - {overlay_key}
    return state.model_copy(
        update={
            "overlay_config": cfg.model_copy(
                update={"enabled_overlays": frozenset(new_set)},
            ),
        },
    )
