"""Viewer state model for the Visualization Layer (VWP3).

Defines the centralized, immutable ViewerState that serves as the
single source of truth for the visualization system, plus the
PlaybackMode enum and factory function for initial state construction.
"""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict, model_validator

from axis_system_a.visualization.debug_overlay_models import DebugOverlayConfig
from axis_system_a.visualization.replay_models import ReplayEpisodeHandle
from axis_system_a.visualization.snapshot_models import (
    ReplayCoordinate,
    ReplayPhase,
)


class PlaybackMode(str, enum.Enum):
    """Playback state of the viewer. No ordering semantics."""

    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class ViewerState(BaseModel):
    """Centralized, immutable viewer state -- single source of truth.

    All visualization components derive their state from this model.
    State changes happen only through pure transition functions in
    viewer_state_transitions.py.

    Invariants (enforced by model_validator):
    - coordinate.step_index is in [0, total_steps - 1]
    - selected_cell, when set, is within grid bounds
    """

    model_config = ConfigDict(frozen=True)

    episode_handle: ReplayEpisodeHandle
    coordinate: ReplayCoordinate
    playback_mode: PlaybackMode
    selected_cell: tuple[int, int] | None = None
    selected_agent: bool = False
    debug_overlay_config: DebugOverlayConfig = DebugOverlayConfig()

    @model_validator(mode="after")
    def _validate_invariants(self) -> ViewerState:
        total = self.episode_handle.validation.total_steps
        si = self.coordinate.step_index
        if si < 0 or si >= total:
            raise ValueError(
                f"step_index {si} out of bounds (valid: 0..{total - 1})"
            )
        if self.selected_cell is not None:
            row, col = self.selected_cell
            gw = self.episode_handle.validation.grid_width
            gh = self.episode_handle.validation.grid_height
            if gw is not None and gh is not None:
                if row < 0 or row >= gh or col < 0 or col >= gw:
                    raise ValueError(
                        f"selected_cell ({row}, {col}) out of grid bounds "
                        f"({gh} rows x {gw} cols)"
                    )
        return self


def create_initial_state(
    episode_handle: ReplayEpisodeHandle,
) -> ViewerState:
    """Create the initial ViewerState for a loaded episode.

    Starts at coordinate (0, BEFORE), STOPPED, no selection.
    """
    return ViewerState(
        episode_handle=episode_handle,
        coordinate=ReplayCoordinate(
            step_index=0, phase=ReplayPhase.BEFORE,
        ),
        playback_mode=PlaybackMode.STOPPED,
        selected_cell=None,
        selected_agent=False,
    )
