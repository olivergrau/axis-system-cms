"""Tests for VWP6 UI construction, frame propagation, and architectural boundaries."""

from __future__ import annotations

import inspect
import os
import sys

import pytest

# Ensure headless Qt operation
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton  # noqa: E402

from axis_system_a.enums import Action, CellType  # noqa: E402
from axis_system_a.visualization.snapshot_models import (  # noqa: E402
    ReplayCoordinate,
    ReplayPhase,
)
from axis_system_a.visualization.view_models import (  # noqa: E402
    ActionContextViewModel,
    AgentViewModel,
    GridCellViewModel,
    GridViewModel,
    SelectionType,
    SelectionViewModel,
    StatusBarViewModel,
    ViewerFrameViewModel,
)
from axis_system_a.visualization.viewer_state import PlaybackMode  # noqa: E402

from axis_system_a.visualization.ui.app import (  # noqa: E402
    launch_visualization_app,
)
from axis_system_a.visualization.ui.detail_placeholder_panel import (  # noqa: E402
    DetailPlaceholderPanel,
)
from axis_system_a.visualization.ui.grid_widget import GridWidget  # noqa: E402
from axis_system_a.visualization.ui.main_window import (  # noqa: E402
    VisualizationMainWindow,
)
from axis_system_a.visualization.ui.status_panel import StatusPanel  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp():
    """Provide a QApplication instance for the test session."""
    app = QApplication.instance() or QApplication([])
    yield app


def _make_cells(
    agent_row: int = 0,
    agent_col: int = 0,
    selected_cell: tuple[int, int] | None = None,
) -> tuple[GridCellViewModel, ...]:
    """Build a 3x3 grid of cells."""
    cells: list[GridCellViewModel] = []
    for row in range(3):
        for col in range(3):
            if row == 1 and col == 1:
                ct, rv, obs = CellType.OBSTACLE, 0.0, True
            elif row == 0 and col == 2:
                ct, rv, obs = CellType.RESOURCE, 0.75, False
            else:
                ct, rv, obs = CellType.EMPTY, 0.0, False
            cells.append(
                GridCellViewModel(
                    row=row,
                    col=col,
                    cell_type=ct,
                    resource_value=rv,
                    is_obstacle=obs,
                    is_traversable=not obs,
                    is_agent_here=(row == agent_row and col == agent_col),
                    is_selected=(selected_cell == (row, col)),
                ),
            )
    return tuple(cells)


@pytest.fixture
def sample_frame() -> ViewerFrameViewModel:
    """Synthetic 3x3 frame — no VWP1-VWP4 fixtures needed."""
    return ViewerFrameViewModel(
        coordinate=ReplayCoordinate(
            step_index=2, phase=ReplayPhase.AFTER_ACTION,
        ),
        grid=GridViewModel(width=3, height=3, cells=_make_cells()),
        agent=AgentViewModel(row=0, col=0, energy=42.5, is_selected=False),
        status=StatusBarViewModel(
            step_index=2,
            total_steps=5,
            phase=ReplayPhase.AFTER_ACTION,
            playback_mode=PlaybackMode.STOPPED,
            energy=42.5,
            at_start=False,
            at_end=False,
        ),
        selection=SelectionViewModel(
            selection_type=SelectionType.NONE,
            selected_cell=None,
            agent_selected=False,
        ),
        action_context=ActionContextViewModel(
            action=Action.RIGHT,
            moved=True,
            consumed=False,
            resource_consumed=0.0,
            energy_delta=-1.0,
            terminated=False,
            termination_reason=None,
        ),
    )


@pytest.fixture
def alternate_frame() -> ViewerFrameViewModel:
    """A second frame with different values for re-set testing."""
    return ViewerFrameViewModel(
        coordinate=ReplayCoordinate(
            step_index=4, phase=ReplayPhase.BEFORE,
        ),
        grid=GridViewModel(
            width=3, height=3,
            cells=_make_cells(agent_row=2, agent_col=2),
        ),
        agent=AgentViewModel(row=2, col=2, energy=10.0, is_selected=True),
        status=StatusBarViewModel(
            step_index=4,
            total_steps=5,
            phase=ReplayPhase.BEFORE,
            playback_mode=PlaybackMode.PAUSED,
            energy=10.0,
            at_start=False,
            at_end=True,
        ),
        selection=SelectionViewModel(
            selection_type=SelectionType.AGENT,
            selected_cell=None,
            agent_selected=True,
        ),
        action_context=ActionContextViewModel(
            action=Action.STAY,
            moved=False,
            consumed=False,
            resource_consumed=0.0,
            energy_delta=0.0,
            terminated=False,
            termination_reason=None,
        ),
    )


@pytest.fixture
def window(qapp) -> VisualizationMainWindow:
    """Fresh main window (not shown)."""
    return VisualizationMainWindow()


# ---------------------------------------------------------------------------
# Main window construction
# ---------------------------------------------------------------------------


class TestMainWindowConstruction:
    def test_main_window_is_qmainwindow(self, window):
        assert isinstance(window, QMainWindow)

    def test_contains_grid_widget(self, window):
        assert window.findChild(GridWidget) is not None

    def test_contains_status_panel(self, window):
        assert window.findChild(StatusPanel) is not None

    def test_contains_detail_placeholder(self, window):
        assert window.findChild(DetailPlaceholderPanel) is not None

    def test_window_has_title(self, window):
        title = window.windowTitle()
        assert "AXIS" in title
        assert "Visualization" in title


# ---------------------------------------------------------------------------
# Frame propagation
# ---------------------------------------------------------------------------


class TestFramePropagation:
    def test_set_frame_updates_grid_widget(self, window, sample_frame):
        window.set_frame(sample_frame)
        grid = window.findChild(GridWidget)
        assert grid._grid is not None
        assert grid._grid.width == 3

    def test_set_frame_updates_status_step_label(self, window, sample_frame):
        window.set_frame(sample_frame)
        panel = window.findChild(StatusPanel)
        assert "2" in panel._step_label.text()

    def test_set_frame_updates_detail_panel(self, window, sample_frame):
        window.set_frame(sample_frame)
        detail = window.findChild(DetailPlaceholderPanel)
        assert "No selection" in detail._selection_label.text()

    def test_set_frame_stores_agent_in_grid(self, window, sample_frame):
        window.set_frame(sample_frame)
        grid = window.findChild(GridWidget)
        assert grid._agent is not None
        assert grid._agent.row == 0
        assert grid._agent.col == 0

    def test_set_frame_twice_uses_latest(
        self, window, sample_frame, alternate_frame,
    ):
        window.set_frame(sample_frame)
        window.set_frame(alternate_frame)
        grid = window.findChild(GridWidget)
        assert grid._agent.row == 2
        assert grid._agent.col == 2
        panel = window.findChild(StatusPanel)
        assert "4" in panel._step_label.text()


# ---------------------------------------------------------------------------
# Grid widget
# ---------------------------------------------------------------------------


class TestGridWidget:
    def test_accepts_frame_without_error(self, qapp, sample_frame):
        widget = GridWidget()
        widget.set_frame(
            sample_frame.grid, sample_frame.agent, sample_frame.selection,
        )

    def test_stores_grid_data(self, qapp, sample_frame):
        widget = GridWidget()
        widget.set_frame(
            sample_frame.grid, sample_frame.agent, sample_frame.selection,
        )
        assert widget._grid is sample_frame.grid

    def test_handles_none_gracefully_on_paint(self, qapp):
        widget = GridWidget()
        widget.resize(100, 100)
        widget.repaint()

    def test_paint_with_data_does_not_crash(self, qapp, sample_frame):
        widget = GridWidget()
        widget.resize(300, 300)
        widget.set_frame(
            sample_frame.grid, sample_frame.agent, sample_frame.selection,
        )
        widget.repaint()

    def test_agent_position_stored(self, qapp, sample_frame):
        widget = GridWidget()
        widget.set_frame(
            sample_frame.grid, sample_frame.agent, sample_frame.selection,
        )
        assert widget._agent.row == 0
        assert widget._agent.col == 0


# ---------------------------------------------------------------------------
# Status panel
# ---------------------------------------------------------------------------


class TestStatusPanel:
    def test_step_label_text(self, qapp, sample_frame):
        panel = StatusPanel()
        panel.set_frame(sample_frame.status)
        assert "2/4" in panel._step_label.text()

    def test_phase_label_text(self, qapp, sample_frame):
        panel = StatusPanel()
        panel.set_frame(sample_frame.status)
        assert "AFTER_ACTION" in panel._phase_label.text()

    def test_playback_label_text(self, qapp, sample_frame):
        panel = StatusPanel()
        panel.set_frame(sample_frame.status)
        assert "stopped" in panel._playback_label.text()

    def test_energy_label_text(self, qapp, sample_frame):
        panel = StatusPanel()
        panel.set_frame(sample_frame.status)
        assert "42.50" in panel._energy_label.text()


# ---------------------------------------------------------------------------
# Static behavior
# ---------------------------------------------------------------------------


class TestStaticBehavior:
    def test_no_push_buttons(self, window, sample_frame):
        window.set_frame(sample_frame)
        assert len(window.findChildren(QPushButton)) == 0

    def test_no_timers(self, window, sample_frame):
        window.set_frame(sample_frame)
        assert len(window.findChildren(QTimer)) == 0


# ---------------------------------------------------------------------------
# Architectural boundary
# ---------------------------------------------------------------------------


class TestArchitecturalBoundary:
    def test_ui_modules_do_not_import_replay_internals(self):
        """UI modules must not import ViewerState, SnapshotResolver, etc."""
        import axis_system_a.visualization.ui.grid_widget as m1
        import axis_system_a.visualization.ui.status_panel as m2
        import axis_system_a.visualization.ui.detail_placeholder_panel as m3
        import axis_system_a.visualization.ui.main_window as m4
        import axis_system_a.visualization.ui.app as m5

        forbidden = [
            "viewer_state",
            "snapshot_resolver",
            "replay_access",
            "playback_controller",
        ]
        for mod in [m1, m2, m3, m4, m5]:
            src = inspect.getsource(mod)
            for name in forbidden:
                assert f"from axis_system_a.visualization.{name}" not in src, (
                    f"{mod.__name__} imports {name}"
                )

    def test_non_ui_layers_do_not_import_pyside(self):
        """Non-UI visualization modules must not contain PySide imports."""
        import axis_system_a.visualization.view_models as vm
        import axis_system_a.visualization.view_model_builder as vb
        import axis_system_a.visualization.viewer_state as vs
        import axis_system_a.visualization.playback_controller as pc

        for mod in [vm, vb, vs, pc]:
            src = inspect.getsource(mod)
            assert "PySide" not in src, (
                f"{mod.__name__} contains PySide import"
            )
