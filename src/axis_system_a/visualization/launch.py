"""CLI-to-visualization startup orchestration (VWP8).

Thin module that converts resolved CLI arguments into a running
interactive visualization session.  Does not contain replay logic,
widget behavior, or repository search — delegates to existing layers.

This is a **bridge module** — it imports domain types, the session
controller, and Qt types for signal wiring.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from axis_system_a.repository import ExperimentRepository
from axis_system_a.visualization.errors import StepOutOfBoundsError
from axis_system_a.visualization.replay_access import ReplayAccessService
from axis_system_a.visualization.snapshot_models import ReplayCoordinate, ReplayPhase
from axis_system_a.visualization.snapshot_resolver import SnapshotResolver
from axis_system_a.visualization.ui.main_window import VisualizationMainWindow
from axis_system_a.visualization.ui.session_controller import (
    VisualizationSessionController,
)


def prepare_visualization_session(
    repository: ExperimentRepository,
    experiment_id: str,
    run_id: str,
    episode_index: int,
    *,
    start_step: int | None = None,
    start_phase: ReplayPhase | None = None,
) -> VisualizationSessionController:
    """Build a ready-to-display visualization session from CLI inputs.

    Resolves the episode through the repository-backed replay access
    layer, constructs the session controller, and optionally seeks to
    the requested startup coordinate.

    Raises the standard VWP1 errors (ExperimentNotFoundError,
    RunNotFoundError, EpisodeNotFoundError, ReplayContractViolation)
    and StepOutOfBoundsError for invalid start positions.
    """
    access = ReplayAccessService(repository)
    episode_handle = access.load_replay_episode(
        experiment_id, run_id, episode_index,
    )
    resolver = SnapshotResolver()
    controller = VisualizationSessionController(episode_handle, resolver)

    if start_step is not None or start_phase is not None:
        step = start_step if start_step is not None else 0
        phase = start_phase if start_phase is not None else ReplayPhase.BEFORE
        if step < 0:
            raise StepOutOfBoundsError(
                step, episode_handle.validation.total_steps,
            )
        coord = ReplayCoordinate(step_index=step, phase=phase)
        controller.seek_to_coordinate(coord)

    return controller


def launch_visualization_from_cli(
    repository: ExperimentRepository,
    experiment_id: str,
    run_id: str,
    episode_index: int,
    *,
    start_step: int | None = None,
    start_phase: ReplayPhase | None = None,
) -> int:
    """Full CLI launch: prepare session, wire UI, enter event loop.

    Returns the application exit code.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    controller = prepare_visualization_session(
        repository, experiment_id, run_id, episode_index,
        start_step=start_step, start_phase=start_phase,
    )
    window = VisualizationMainWindow()

    # Signal wiring (parallel to app.py:launch_interactive_session)
    controller.frame_changed.connect(window.set_frame)

    controls = window.replay_controls
    controls.step_backward_requested.connect(controller.step_backward)
    controls.step_forward_requested.connect(controller.step_forward)
    controls.play_requested.connect(controller.play)
    controls.pause_requested.connect(controller.pause)
    controls.stop_requested.connect(controller.stop)
    controls.phase_selected.connect(
        lambda idx: controller.set_phase(ReplayPhase(idx)),
    )

    grid = window.grid_widget
    grid.cell_clicked.connect(controller.select_cell)
    grid.agent_clicked.connect(controller.select_agent)

    window.set_frame(controller.current_frame)
    window.show()
    return app.exec()
