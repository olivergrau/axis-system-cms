"""Application assembly and signal wiring.

Consolidates signal wiring that was duplicated between app.py
and launch.py in v0.1.0.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from axis.visualization.ui.main_window import VisualizationMainWindow
from axis.visualization.ui.session_controller import (
    VisualizationSessionController,
)


def wire_signals(
    window: VisualizationMainWindow,
    controller: VisualizationSessionController,
) -> None:
    """Wire all signals between window and controller.

    Consolidates the signal-wiring pattern that was duplicated
    in v0.1.0 between app.py and launch.py.
    """
    # Frame updates: controller -> window
    controller.frame_changed.connect(window.set_frame)

    # Replay controls -> controller
    controls = window.replay_controls
    controls.step_backward_requested.connect(controller.step_backward)
    controls.step_forward_requested.connect(controller.step_forward)
    controls.play_requested.connect(controller.play)
    controls.pause_requested.connect(controller.pause)
    controls.stop_requested.connect(controller.stop)
    controls.phase_selected.connect(controller.set_phase)

    # Canvas -> controller
    window.canvas.cell_clicked.connect(controller.select_cell)
    window.canvas.agent_clicked.connect(controller.select_agent)

    # Overlay panel -> controller
    overlay = window.overlay_panel
    overlay.master_toggled.connect(controller.set_overlay_master)
    overlay.overlay_toggled.connect(controller.set_overlay_type_enabled)


def launch_interactive_session(
    window: VisualizationMainWindow,
    controller: VisualizationSessionController,
) -> int:
    """Wire signals, show window, and run the Qt event loop."""
    app = QApplication.instance() or QApplication(sys.argv)

    wire_signals(window, controller)

    # Set initial frame
    window.set_frame(controller.current_frame)
    window.show()

    return app.exec()
