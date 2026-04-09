"""Playback and Navigation Controller.

Canonical replay traversal layer between raw ViewerState transitions
and the UI. Stateless, deterministic, UI-independent.

Adapts to variable phase counts using num_phases from ViewerState.
"""

from __future__ import annotations

from axis.visualization.replay_models import ReplayEpisodeHandle
from axis.visualization.snapshot_models import ReplayCoordinate
from axis.visualization.viewer_state import (
    PlaybackMode,
    ViewerState,
)
from axis.visualization.viewer_state_transitions import (
    seek,
    set_phase as _set_phase,
    set_playback_mode,
)


# -- Boundary helpers -----------------------------------------------------------


def get_initial_coordinate(
    episode_handle: ReplayEpisodeHandle,
) -> ReplayCoordinate:
    """Return the earliest valid replay coordinate: (0, 0)."""
    return ReplayCoordinate(step_index=0, phase_index=0)


def get_final_coordinate(
    episode_handle: ReplayEpisodeHandle,
    num_phases: int,
) -> ReplayCoordinate:
    """Return the latest valid replay coordinate: (last_step, last_phase)."""
    last = episode_handle.validation.total_steps - 1
    return ReplayCoordinate(step_index=last, phase_index=num_phases - 1)


def is_at_initial(state: ViewerState) -> bool:
    """True when *state* is at the initial replay coordinate."""
    return state.coordinate == get_initial_coordinate(state.episode_handle)


def is_at_final(state: ViewerState) -> bool:
    """True when *state* is at the final replay coordinate."""
    return state.coordinate == get_final_coordinate(
        state.episode_handle, state.num_phases,
    )


# -- PlaybackController ---------------------------------------------------------


class PlaybackController:
    """Deterministic replay control layer.

    Orchestrates transition primitives to implement phase-aware
    navigation and playback progression. Adapts to any phase count
    via state.num_phases.
    """

    def step_forward(self, state: ViewerState) -> ViewerState:
        """Advance one replay unit in phase order.

        Traversal for 3-phase system:
            (i, 0) -> (i, 1) -> (i, 2) -> (i+1, 0)

        Traversal for 2-phase system:
            (i, 0) -> (i, 1) -> (i+1, 0)

        Returns *state* unchanged at the final replay position.
        """
        if is_at_final(state):
            return state

        phase_idx = state.coordinate.phase_index

        if phase_idx < state.num_phases - 1:
            # Advance to next phase within the same step.
            return _set_phase(state, phase_idx + 1)

        # At last phase — move to next step's first phase.
        coord = ReplayCoordinate(
            step_index=state.coordinate.step_index + 1,
            phase_index=0,
        )
        return seek(state, coord)

    def step_backward(self, state: ViewerState) -> ViewerState:
        """Move back one replay unit in reverse phase order.

        Returns *state* unchanged at the initial replay position.
        """
        if is_at_initial(state):
            return state

        phase_idx = state.coordinate.phase_index

        if phase_idx > 0:
            # Move to previous phase within the same step.
            return _set_phase(state, phase_idx - 1)

        # At first phase — move to previous step's last phase.
        coord = ReplayCoordinate(
            step_index=state.coordinate.step_index - 1,
            phase_index=state.num_phases - 1,
        )
        return seek(state, coord)

    def seek_to_step(
        self, state: ViewerState, step_index: int,
    ) -> ViewerState:
        """Jump to (step_index, 0).

        Raises StepOutOfBoundsError for invalid *step_index*.
        """
        coord = ReplayCoordinate(step_index=step_index, phase_index=0)
        return seek(state, coord)

    def seek_to_coordinate(
        self, state: ViewerState, coordinate: ReplayCoordinate,
    ) -> ViewerState:
        """Jump to an arbitrary replay coordinate."""
        return seek(state, coordinate)

    def set_phase(
        self, state: ViewerState, phase_index: int,
    ) -> ViewerState:
        """Change the current phase without altering the step index."""
        return _set_phase(state, phase_index)

    def tick(self, state: ViewerState) -> ViewerState:
        """One playback tick — advance if PLAYING, no-op otherwise.

        * PLAYING: if at terminal position, transition to STOPPED;
          otherwise advance via step_forward.
        * PAUSED / STOPPED: return *state* unchanged.
        """
        if state.playback_mode is not PlaybackMode.PLAYING:
            return state

        if is_at_final(state):
            return set_playback_mode(state, PlaybackMode.STOPPED)

        return self.step_forward(state)
