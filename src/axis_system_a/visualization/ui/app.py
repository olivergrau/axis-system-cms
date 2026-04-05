"""Visualization application entry point (VWP6/VWP7).

Provides :func:`launch_visualization_app` for static display (VWP6)
and :func:`launch_interactive_session` for full interactive replay (VWP7).

This is a **bridge module** — it wires controller signals to window
slots.  Excluded from the widget architectural boundary test.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from axis_system_a.visualization.replay_models import ReplayEpisodeHandle
from axis_system_a.visualization.snapshot_models import ReplayPhase
from axis_system_a.visualization.snapshot_resolver import SnapshotResolver
from axis_system_a.visualization.ui.main_window import VisualizationMainWindow
from axis_system_a.visualization.ui.session_controller import (
    VisualizationSessionController,
)
from axis_system_a.visualization.view_models import ViewerFrameViewModel


def launch_visualization_app(frame: ViewerFrameViewModel) -> int:
    """Create a ``QApplication``, show the main window, and run the event loop.

    Reuses an existing ``QApplication`` if one is already running
    (e.g. in test environments).  Returns the exit code from
    ``QApplication.exec()``.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    window = VisualizationMainWindow()
    window.set_frame(frame)
    window.show()
    return app.exec()


launch_visualization_static = launch_visualization_app


def launch_interactive_session(
    episode_handle: ReplayEpisodeHandle,
    snapshot_resolver: SnapshotResolver,
) -> int:
    """Launch the full interactive replay session (VWP7).

    Creates the controller, wires all signals, shows the window,
    and enters the event loop.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    window = VisualizationMainWindow()
    controller = VisualizationSessionController(
        episode_handle, snapshot_resolver)

    # Controller → window
    controller.frame_changed.connect(window.set_frame)

    # Replay controls → controller
    controls = window.replay_controls
    controls.step_backward_requested.connect(controller.step_backward)
    controls.step_forward_requested.connect(controller.step_forward)
    controls.play_requested.connect(controller.play)
    controls.pause_requested.connect(controller.pause)
    controls.stop_requested.connect(controller.stop)
    controls.phase_selected.connect(
        lambda idx: controller.set_phase(ReplayPhase(idx)),
    )

    # Grid → controller
    grid = window.grid_widget
    grid.cell_clicked.connect(controller.select_cell)
    grid.agent_clicked.connect(controller.select_agent)

    # Debug overlay panel → controller (VWP9)
    overlay_panel = window.debug_overlay_panel
    overlay_panel.master_toggled.connect(controller.set_debug_overlay_master)
    overlay_panel.action_preference_toggled.connect(
        lambda v: controller.set_overlay_enabled(
            "action_preference_enabled", v),
    )
    overlay_panel.drive_contribution_toggled.connect(
        lambda v: controller.set_overlay_enabled(
            "drive_contribution_enabled", v),
    )
    overlay_panel.consumption_opportunity_toggled.connect(
        lambda v: controller.set_overlay_enabled(
            "consumption_opportunity_enabled", v),
    )

    # Initial frame
    window.set_frame(controller.current_frame)
    window.show()
    return app.exec()
