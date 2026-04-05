"""Playback and Navigation Controller (VWP4).

Canonical replay traversal layer between raw ViewerState transitions
(VWP3) and the UI (VWP5+).  Stateless, deterministic, UI-independent.

Defines:
- phase ordering constant
- boundary helpers (initial/final coordinate, position checks)
- PlaybackController with phase-aware stepping, seek, and tick
"""

from __future__ import annotations

from axis_system_a.visualization.replay_models import ReplayEpisodeHandle
from axis_system_a.visualization.snapshot_models import (
    ReplayCoordinate,
    ReplayPhase,
)
from axis_system_a.visualization.viewer_state import (
    PlaybackMode,
    ViewerState,
)
from axis_system_a.visualization.viewer_state_transitions import (
    seek,
    set_phase as _set_phase,
    set_playback_mode,
)

# ---------------------------------------------------------------------------
# Canonical phase ordering — defined once, used everywhere
# ---------------------------------------------------------------------------

_PHASE_ORDER: tuple[ReplayPhase, ...] = (
    ReplayPhase.BEFORE,
    ReplayPhase.AFTER_REGEN,
    ReplayPhase.AFTER_ACTION,
)

_PHASE_INDEX: dict[ReplayPhase, int] = {
    p: i for i, p in enumerate(_PHASE_ORDER)}


# ---------------------------------------------------------------------------
# Boundary helpers
# ---------------------------------------------------------------------------


def get_initial_coordinate(
    episode_handle: ReplayEpisodeHandle,
) -> ReplayCoordinate:
    """Return the earliest valid replay coordinate: ``(0, BEFORE)``."""
    return ReplayCoordinate(step_index=0, phase=ReplayPhase.BEFORE)


def get_final_coordinate(
    episode_handle: ReplayEpisodeHandle,
) -> ReplayCoordinate:
    """Return the latest valid replay coordinate: ``(last_step, AFTER_ACTION)``."""
    last = episode_handle.validation.total_steps - 1
    return ReplayCoordinate(step_index=last, phase=ReplayPhase.AFTER_ACTION)


def is_at_initial(state: ViewerState) -> bool:
    """True when *state* is at the initial replay coordinate."""
    return state.coordinate == get_initial_coordinate(state.episode_handle)


def is_at_final(state: ViewerState) -> bool:
    """True when *state* is at the final replay coordinate."""
    return state.coordinate == get_final_coordinate(state.episode_handle)


# ---------------------------------------------------------------------------
# PlaybackController
# ---------------------------------------------------------------------------


class PlaybackController:
    """Deterministic replay control layer.

    Orchestrates VWP3 transition primitives to implement canonical
    phase-aware navigation and playback progression.  Stateless — all
    methods are pure ``(ViewerState[, params]) -> ViewerState``.
    """

    def step_forward(self, state: ViewerState) -> ViewerState:
        """Advance one replay unit in phase order.

        Traversal::

            (i, BEFORE) -> (i, AFTER_REGEN) -> (i, AFTER_ACTION) -> (i+1, BEFORE)

        Returns *state* unchanged (identity) at the final replay position.
        """
        if is_at_final(state):
            return state

        phase_idx = _PHASE_INDEX[state.coordinate.phase]

        if phase_idx < len(_PHASE_ORDER) - 1:
            # Advance to next phase within the same step.
            return _set_phase(state, _PHASE_ORDER[phase_idx + 1])

        # At last phase (AFTER_ACTION) — move to next step's BEFORE.
        coord = ReplayCoordinate(
            step_index=state.coordinate.step_index + 1,
            phase=ReplayPhase.BEFORE,
        )
        return seek(state, coord)

    def step_backward(self, state: ViewerState) -> ViewerState:
        """Move back one replay unit in reverse phase order.

        Traversal::

            (i+1, BEFORE) -> (i, AFTER_ACTION) -> (i, AFTER_REGEN) -> (i, BEFORE)

        Returns *state* unchanged (identity) at the initial replay position.
        """
        if is_at_initial(state):
            return state

        phase_idx = _PHASE_INDEX[state.coordinate.phase]

        if phase_idx > 0:
            # Move to previous phase within the same step.
            return _set_phase(state, _PHASE_ORDER[phase_idx - 1])

        # At first phase (BEFORE) — move to previous step's AFTER_ACTION.
        coord = ReplayCoordinate(
            step_index=state.coordinate.step_index - 1,
            phase=ReplayPhase.AFTER_ACTION,
        )
        return seek(state, coord)

    def seek_to_step(
        self, state: ViewerState, step_index: int,
    ) -> ViewerState:
        """Jump to ``(step_index, BEFORE)``.

        The default phase is always BEFORE — explicit and documented.
        Raises :class:`StepOutOfBoundsError` for invalid *step_index*.
        """
        coord = ReplayCoordinate(
            step_index=step_index, phase=ReplayPhase.BEFORE,
        )
        return seek(state, coord)

    def seek_to_coordinate(
        self, state: ViewerState, coordinate: ReplayCoordinate,
    ) -> ViewerState:
        """Jump to an arbitrary replay coordinate.

        Raises :class:`StepOutOfBoundsError` if *coordinate* is invalid.
        """
        return seek(state, coordinate)

    def set_phase(
        self, state: ViewerState, phase: ReplayPhase,
    ) -> ViewerState:
        """Change the current phase without altering the step index."""
        return _set_phase(state, phase)

    def tick(self, state: ViewerState) -> ViewerState:
        """One playback tick — advance if PLAYING, no-op otherwise.

        Semantics:

        * **PLAYING**: if at terminal position, transition to STOPPED;
          otherwise advance one replay unit via :meth:`step_forward`.
        * **PAUSED** / **STOPPED**: return *state* unchanged.

        Auto-stop policy: when PLAYING at the final position the mode
        becomes STOPPED (not PAUSED) — STOPPED signals playback
        completion, PAUSED signals a user-initiated pause.
        """
        if state.playback_mode is not PlaybackMode.PLAYING:
            return state

        if is_at_final(state):
            return set_playback_mode(state, PlaybackMode.STOPPED)

        return self.step_forward(state)
