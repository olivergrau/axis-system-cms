"""Pure state transition functions for ViewerState (VWP3).

Every function takes a ViewerState (and optional parameters) and returns
a new ViewerState.  No mutation.  No side effects.  No caching.
No resolver calls.  No async.
"""

from __future__ import annotations

from axis_system_a.visualization.errors import (
    CellOutOfBoundsError,
    StepOutOfBoundsError,
)
from axis_system_a.visualization.snapshot_models import (
    ReplayCoordinate,
    ReplayPhase,
)
from axis_system_a.visualization.viewer_state import (
    PlaybackMode,
    ViewerState,
)


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------


def next_step(state: ViewerState) -> ViewerState:
    """Advance to the next step, preserving current phase.

    Returns *state* unchanged (identity) when already at the last step.
    """
    total = state.episode_handle.validation.total_steps
    if state.coordinate.step_index >= total - 1:
        return state
    return state.model_copy(
        update={
            "coordinate": ReplayCoordinate(
                step_index=state.coordinate.step_index + 1,
                phase=state.coordinate.phase,
            ),
        },
    )


def previous_step(state: ViewerState) -> ViewerState:
    """Move to the previous step, preserving current phase.

    Returns *state* unchanged (identity) when already at step 0.
    """
    if state.coordinate.step_index <= 0:
        return state
    return state.model_copy(
        update={
            "coordinate": ReplayCoordinate(
                step_index=state.coordinate.step_index - 1,
                phase=state.coordinate.phase,
            ),
        },
    )


def set_phase(state: ViewerState, phase: ReplayPhase) -> ViewerState:
    """Change the current phase without altering the step index."""
    return state.model_copy(
        update={
            "coordinate": ReplayCoordinate(
                step_index=state.coordinate.step_index,
                phase=phase,
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


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------


def select_cell(state: ViewerState, row: int, col: int) -> ViewerState:
    """Select a grid cell, clearing any agent selection.

    Raises CellOutOfBoundsError if (row, col) is outside the grid.
    """
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


# ---------------------------------------------------------------------------
# Playback
# ---------------------------------------------------------------------------


def set_playback_mode(
    state: ViewerState, mode: PlaybackMode,
) -> ViewerState:
    """Change the playback mode."""
    return state.model_copy(update={"playback_mode": mode})


# ---------------------------------------------------------------------------
# Debug overlay
# ---------------------------------------------------------------------------


def toggle_debug_overlay(state: ViewerState) -> ViewerState:
    """Flip the master debug overlay flag."""
    cfg = state.debug_overlay_config
    return state.model_copy(
        update={
            "debug_overlay_config": cfg.model_copy(
                update={"master_enabled": not cfg.master_enabled},
            ),
        },
    )


def set_overlay_type_enabled(
    state: ViewerState, field_name: str, enabled: bool,
) -> ViewerState:
    """Enable or disable a specific overlay type by config field name.

    *field_name* must be one of the boolean per-type fields on
    DebugOverlayConfig (e.g. ``"action_preference_enabled"``).
    """
    cfg = state.debug_overlay_config
    return state.model_copy(
        update={
            "debug_overlay_config": cfg.model_copy(
                update={field_name: enabled},
            ),
        },
    )
