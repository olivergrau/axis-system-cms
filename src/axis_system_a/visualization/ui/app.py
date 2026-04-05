"""Visualization application entry point (VWP6).

Provides :func:`launch_visualization_app` — the single bootstrap
function for the PySide6 visualization window.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from axis_system_a.visualization.ui.main_window import VisualizationMainWindow
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
