"""End-to-end visualization startup tests (VWP8)."""

from __future__ import annotations

import inspect
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMainWindow  # noqa: E402

from axis_system_a.repository import ExperimentRepository  # noqa: E402
from axis_system_a.visualization.errors import (  # noqa: E402
    EpisodeNotFoundError,
    ExperimentNotFoundError,
    RunNotFoundError,
    StepOutOfBoundsError,
)
from axis_system_a.visualization.launch import (  # noqa: E402
    prepare_visualization_session,
)
from axis_system_a.visualization.replay_models import (  # noqa: E402
    ReplayEpisodeHandle,
)
from axis_system_a.visualization.snapshot_models import (  # noqa: E402
    ReplayCoordinate,
    ReplayPhase,
)
from axis_system_a.visualization.ui.detail_panel import DetailPanel  # noqa: E402
from axis_system_a.visualization.ui.grid_widget import GridWidget  # noqa: E402
from axis_system_a.visualization.ui.main_window import (  # noqa: E402
    VisualizationMainWindow,
)
from axis_system_a.visualization.ui.replay_controls_panel import (  # noqa: E402
    ReplayControlsPanel,
)
from axis_system_a.visualization.ui.status_panel import StatusPanel  # noqa: E402
from axis_system_a.visualization.viewer_state import PlaybackMode  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


# ---------------------------------------------------------------------------
# prepare_visualization_session
# ---------------------------------------------------------------------------


class TestPrepareSession:
    def test_default_coordinate(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
        )
        assert ctrl.current_state.coordinate.step_index == 0
        assert ctrl.current_state.coordinate.phase == ReplayPhase.BEFORE

    def test_correct_episode(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
        )
        assert ctrl.current_state.episode_handle.experiment_id == "test-exp"

    def test_stopped_mode(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
        )
        assert ctrl.current_state.playback_mode == PlaybackMode.STOPPED

    def test_frame_not_none(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
        )
        assert ctrl.current_frame is not None

    def test_custom_start_step(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
            start_step=2,
        )
        assert ctrl.current_state.coordinate.step_index == 2

    def test_custom_start_phase(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
            start_phase=ReplayPhase.AFTER_ACTION,
        )
        assert ctrl.current_state.coordinate.phase == ReplayPhase.AFTER_ACTION

    def test_custom_step_and_phase(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
            start_step=1, start_phase=ReplayPhase.AFTER_REGEN,
        )
        assert ctrl.current_state.coordinate.step_index == 1
        assert ctrl.current_state.coordinate.phase == ReplayPhase.AFTER_REGEN

    def test_invalid_step_raises(self, qapp, populated_repo):
        with pytest.raises(StepOutOfBoundsError):
            prepare_visualization_session(
                populated_repo, "test-exp", "run-0000", 1,
                start_step=999,
            )

    def test_negative_step_raises(self, qapp, populated_repo):
        with pytest.raises(StepOutOfBoundsError):
            prepare_visualization_session(
                populated_repo, "test-exp", "run-0000", 1,
                start_step=-1,
            )

    def test_experiment_not_found(self, qapp, populated_repo):
        with pytest.raises(ExperimentNotFoundError):
            prepare_visualization_session(
                populated_repo, "nonexistent", "run-0000", 1,
            )

    def test_run_not_found(self, qapp, populated_repo):
        with pytest.raises(RunNotFoundError):
            prepare_visualization_session(
                populated_repo, "test-exp", "nonexistent", 1,
            )

    def test_episode_not_found(self, qapp, populated_repo):
        with pytest.raises(EpisodeNotFoundError):
            prepare_visualization_session(
                populated_repo, "test-exp", "run-0000", 99,
            )


# ---------------------------------------------------------------------------
# End-to-end session startup
# ---------------------------------------------------------------------------


class TestSessionStartup:
    def test_window_construction(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
        )
        window = VisualizationMainWindow()
        window.set_frame(ctrl.current_frame)
        assert isinstance(window, QMainWindow)

    def test_initial_frame_matches_state(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
        )
        frame = ctrl.current_frame
        assert frame.status.step_index == ctrl.current_state.coordinate.step_index

    def test_initial_frame_has_grid(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
        )
        assert ctrl.current_frame.grid is not None

    def test_replay_controls_exist(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
        )
        window = VisualizationMainWindow()
        window.set_frame(ctrl.current_frame)
        assert window.replay_controls is not None

    def test_grid_widget_exists(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
        )
        window = VisualizationMainWindow()
        window.set_frame(ctrl.current_frame)
        assert window.grid_widget is not None

    def test_custom_start_reflected_in_frame(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
            start_step=1,
        )
        assert ctrl.current_frame.status.step_index == 1

    def test_navigation_after_prepare(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
        )
        ctrl.step_forward()
        assert ctrl.current_state.coordinate.phase == ReplayPhase.AFTER_REGEN

    def test_signal_propagation(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
        )
        window = VisualizationMainWindow()
        ctrl.frame_changed.connect(window.set_frame)
        window.set_frame(ctrl.current_frame)
        ctrl.step_forward()
        grid = window.findChild(GridWidget)
        # After step_forward, grid should have data from the new frame
        assert grid._grid is not None


# ---------------------------------------------------------------------------
# Architectural boundaries
# ---------------------------------------------------------------------------


class TestArchitecturalBoundary:
    def test_cli_no_pyside_at_module_level(self):
        """cli.py must not import PySide6 at module level."""
        import axis_system_a.cli as cli_mod
        src = inspect.getsource(cli_mod)
        # Only check top-level imports (before first function def)
        header = src.split("\ndef ")[0]
        assert "PySide" not in header

    def test_launch_uses_replay_access(self):
        """launch.py must go through ReplayAccessService."""
        import axis_system_a.visualization.launch as launch_mod
        src = inspect.getsource(launch_mod)
        assert "ReplayAccessService" in src

    def test_launch_does_not_load_files_directly(self):
        """launch.py must not open or parse files directly."""
        import axis_system_a.visualization.launch as launch_mod
        src = inspect.getsource(launch_mod)
        assert "open(" not in src
        assert "json.load" not in src
        assert "Path(" not in src


# ---------------------------------------------------------------------------
# Regression: VWP6/VWP7 still work under CLI-launched startup
# ---------------------------------------------------------------------------


class TestRegressionVWP6VWP7:
    def test_window_has_all_widgets(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
        )
        window = VisualizationMainWindow()
        window.set_frame(ctrl.current_frame)
        assert window.findChild(GridWidget) is not None
        assert window.findChild(StatusPanel) is not None
        assert window.findChild(DetailPanel) is not None
        assert window.findChild(ReplayControlsPanel) is not None

    def test_controls_exist_after_startup(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
        )
        window = VisualizationMainWindow()
        window.set_frame(ctrl.current_frame)
        controls = window.replay_controls
        assert controls._play_btn is not None
        assert controls._pause_btn is not None
        assert controls._stop_btn is not None

    def test_frame_consistent_with_custom_start(self, qapp, populated_repo):
        ctrl = prepare_visualization_session(
            populated_repo, "test-exp", "run-0000", 1,
            start_step=1, start_phase=ReplayPhase.AFTER_ACTION,
        )
        frame = ctrl.current_frame
        assert frame.status.step_index == 1
        assert frame.status.phase == ReplayPhase.AFTER_ACTION
