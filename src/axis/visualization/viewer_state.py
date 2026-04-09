"""Viewer state model for the Visualization Layer.

Defines the centralized, immutable ViewerState and OverlayConfig.
"""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict, model_validator

from axis.visualization.replay_models import ReplayEpisodeHandle
from axis.visualization.snapshot_models import ReplayCoordinate


class PlaybackMode(str, enum.Enum):
    """Playback state of the viewer."""

    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class OverlayConfig(BaseModel):
    """Toggle state for the overlay system.

    master_enabled gates the entire overlay system. enabled_overlays
    contains the keys of individually enabled overlay types (from
    OverlayTypeDeclaration.key).
    """

    model_config = ConfigDict(frozen=True)

    master_enabled: bool = False
    enabled_overlays: frozenset[str] = frozenset()


class ViewerState(BaseModel):
    """Centralized, immutable viewer state -- single source of truth.

    All visualization components derive their state from this model.
    State changes happen only through pure transition functions in
    viewer_state_transitions.py.

    Invariants (enforced by model_validator):
    - coordinate.step_index is in [0, total_steps - 1]
    - coordinate.phase_index is in [0, num_phases - 1]
    - selected_cell, when set, is within grid bounds
    """

    model_config = ConfigDict(frozen=True)

    episode_handle: ReplayEpisodeHandle
    coordinate: ReplayCoordinate
    playback_mode: PlaybackMode
    num_phases: int
    selected_cell: tuple[int, int] | None = None
    selected_agent: bool = False
    overlay_config: OverlayConfig = OverlayConfig()

    @model_validator(mode="after")
    def _validate_invariants(self) -> ViewerState:
        total = self.episode_handle.validation.total_steps
        si = self.coordinate.step_index
        if si < 0 or si >= total:
            raise ValueError(
                f"step_index {si} out of bounds (valid: 0..{total - 1})"
            )
        pi = self.coordinate.phase_index
        if pi < 0 or pi >= self.num_phases:
            raise ValueError(
                f"phase_index {pi} out of bounds (valid: 0..{self.num_phases - 1})"
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
    num_phases: int,
) -> ViewerState:
    """Create the initial ViewerState for a loaded episode.

    Starts at coordinate (0, 0), STOPPED, no selection.
    All overlay types start disabled.
    """
    return ViewerState(
        episode_handle=episode_handle,
        coordinate=ReplayCoordinate(step_index=0, phase_index=0),
        playback_mode=PlaybackMode.STOPPED,
        num_phases=num_phases,
        selected_cell=None,
        selected_agent=False,
        overlay_config=OverlayConfig(),
    )
