"""Tests for WP-V.4.4: SessionController, MainWindow, and signal wiring."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from PySide6.QtWidgets import QApplication  # noqa: E402

from axis.sdk.position import Position  # noqa: E402
from axis.sdk.snapshot import WorldSnapshot  # noqa: E402
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace  # noqa: E402
from axis.sdk.world_types import CellView  # noqa: E402

from axis.visualization.adapters.default_world import (  # noqa: E402
    DefaultWorldVisualizationAdapter,
)
from axis.visualization.adapters.null_system import (  # noqa: E402
    NullSystemVisualizationAdapter,
)
from axis.visualization.replay_models import (  # noqa: E402
    ReplayEpisodeHandle,
    ReplayStepDescriptor,
    ReplayValidationResult,
)
from axis.visualization.types import (  # noqa: E402
    AnalysisRow,
    AnalysisSection,
    OverlayData,
    OverlayItem,
    OverlayTypeDeclaration,
)
from axis.visualization.ui.app import wire_signals  # noqa: E402
from axis.visualization.ui.main_window import (  # noqa: E402
    VisualizationMainWindow,
)
from axis.visualization.ui.session_controller import (  # noqa: E402
    VisualizationSessionController,
)
from axis.visualization.viewer_state import PlaybackMode  # noqa: E402


# ---------------------------------------------------------------------------
# QApplication fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cell(resource: float = 0.0, traversable: bool = True) -> CellView:
    ct = "obstacle" if not traversable else (
        "resource" if resource > 0 else "empty")
    return CellView(cell_type=ct, resource_value=resource)


def _make_snapshot(
    width: int = 5, height: int = 5,
    agent_pos: Position | None = None,
) -> WorldSnapshot:
    pos = agent_pos or Position(x=1, y=1)
    rows = []
    for r in range(height):
        row = []
        for c in range(width):
            if r == 2 and c == 2:
                row.append(_make_cell(resource=0.5))
            else:
                row.append(_make_cell())
        rows.append(tuple(row))
    return WorldSnapshot(
        grid=tuple(rows), agent_position=pos,
        width=width, height=height,
    )


def _make_step(
    timestep: int = 0,
    agent_pos_before: Position | None = None,
    agent_pos_after: Position | None = None,
) -> BaseStepTrace:
    pos_b = agent_pos_before or Position(x=1, y=1)
    pos_a = agent_pos_after or Position(x=2, y=1)
    return BaseStepTrace(
        timestep=timestep, action="right",
        world_before=_make_snapshot(agent_pos=pos_b),
        world_after=_make_snapshot(agent_pos=pos_a),
        agent_position_before=pos_b,
        agent_position_after=pos_a,
        vitality_before=0.8, vitality_after=0.75,
        terminated=False,
    )


def _sample_episode_handle(num_steps: int = 5) -> ReplayEpisodeHandle:
    steps = tuple(_make_step(timestep=i) for i in range(num_steps))
    episode = BaseEpisodeTrace(
        system_type="test", steps=steps, total_steps=num_steps,
        termination_reason="max_steps", final_vitality=0.75,
        final_position=Position(x=0, y=0),
    )
    descriptors = tuple(
        ReplayStepDescriptor(
            step_index=i, has_world_before=True, has_world_after=True,
            has_intermediate_snapshots=(), has_agent_position=True,
            has_vitality=True, has_world_state=True,
        )
        for i in range(num_steps)
    )
    validation = ReplayValidationResult(
        valid=True, total_steps=num_steps,
        grid_width=5, grid_height=5,
        step_descriptors=descriptors,
    )
    return ReplayEpisodeHandle(
        experiment_id="exp", run_id="run", episode_index=0,
        episode_trace=episode, validation=validation,
    )


class MockSystemAdapter:
    """Satisfies SystemVisualizationAdapter protocol for testing."""

    def __init__(self, num_phases: int = 3):
        self._num_phases = num_phases

    def phase_names(self):
        names = ["BEFORE"]
        for i in range(1, self._num_phases - 1):
            names.append(f"INTERMEDIATE_{i}")
        names.append("AFTER_ACTION")
        return names

    def vitality_label(self):
        return "Energy"

    def format_vitality(self, value, system_data):
        return f"{value * 100:.2f} / 100.00"

    def build_step_analysis(self, step_trace):
        return [
            AnalysisSection(
                title="Test Section",
                rows=(AnalysisRow(label="Key", value="Val"),),
            ),
        ]

    def build_overlays(self, step_trace):
        return [
            OverlayData(
                overlay_type="test_overlay",
                items=(
                    OverlayItem(
                        item_type="direction_arrow",
                        grid_position=(1, 1),
                        data={"direction": "up"},
                    ),
                ),
            ),
        ]

    def available_overlay_types(self):
        return [
            OverlayTypeDeclaration(
                key="test_overlay", label="Test", description="Test overlay",
            ),
        ]


def _make_controller(qapp, num_phases: int = 2) -> VisualizationSessionController:
    return VisualizationSessionController(
        _sample_episode_handle(),
        DefaultWorldVisualizationAdapter(),
        MockSystemAdapter(num_phases),
    )


def _make_window(qapp) -> VisualizationMainWindow:
    adapter = DefaultWorldVisualizationAdapter()
    declarations = [
        OverlayTypeDeclaration(key="test", label="Test", description="Test"),
        OverlayTypeDeclaration(
            key="test2", label="Test2", description="Test2"),
    ]
    return VisualizationMainWindow(adapter, ["BEFORE", "INTER", "AFTER"], declarations)


# ---------------------------------------------------------------------------
# SessionController tests
# ---------------------------------------------------------------------------


class TestSessionController:

    def test_controller_construction(self, qapp) -> None:
        ctrl = _make_controller(qapp)
        assert ctrl.current_state is not None

    def test_initial_frame_built(self, qapp) -> None:
        ctrl = _make_controller(qapp)
        assert ctrl.current_frame is not None
        assert ctrl.current_frame.grid.width == 5

    def test_step_forward_emits_frame(self, qapp) -> None:
        ctrl = _make_controller(qapp)
        received = []
        ctrl.frame_changed.connect(lambda f: received.append(f))
        ctrl.step_forward()
        assert len(received) == 1

    def test_step_backward_emits_frame(self, qapp) -> None:
        ctrl = _make_controller(qapp)
        ctrl.step_forward()  # move off start
        received = []
        ctrl.frame_changed.connect(lambda f: received.append(f))
        ctrl.step_backward()
        assert len(received) == 1

    def test_play_starts_timer(self, qapp) -> None:
        ctrl = _make_controller(qapp)
        ctrl.play()
        assert ctrl.current_state.playback_mode == PlaybackMode.PLAYING
        ctrl.pause()  # cleanup

    def test_pause_stops_timer(self, qapp) -> None:
        ctrl = _make_controller(qapp)
        ctrl.play()
        ctrl.pause()
        assert ctrl.current_state.playback_mode == PlaybackMode.PAUSED

    def test_stop_resets(self, qapp) -> None:
        ctrl = _make_controller(qapp)
        ctrl.play()
        ctrl.stop()
        assert ctrl.current_state.playback_mode == PlaybackMode.STOPPED

    def test_set_phase(self, qapp) -> None:
        ctrl = _make_controller(qapp)
        ctrl.set_phase(1)
        assert ctrl.current_state.coordinate.phase_index == 1

    def test_select_cell(self, qapp) -> None:
        ctrl = _make_controller(qapp)
        ctrl.select_cell(2, 3)
        assert ctrl.current_state.selected_cell == (2, 3)

    def test_select_agent(self, qapp) -> None:
        ctrl = _make_controller(qapp)
        ctrl.select_agent()
        assert ctrl.current_state.selected_agent is True

    def test_clear_selection(self, qapp) -> None:
        ctrl = _make_controller(qapp)
        ctrl.select_cell(2, 3)
        ctrl.clear_selection()
        assert ctrl.current_state.selected_cell is None
        assert ctrl.current_state.selected_agent is False

    def test_overlay_master_toggle(self, qapp) -> None:
        ctrl = _make_controller(qapp)
        ctrl.set_overlay_master(True)
        assert ctrl.current_state.overlay_config.master_enabled is True
        ctrl.set_overlay_master(False)
        assert ctrl.current_state.overlay_config.master_enabled is False

    def test_overlay_type_toggle(self, qapp) -> None:
        ctrl = _make_controller(qapp)
        ctrl.set_overlay_type_enabled("test_overlay", True)
        assert "test_overlay" in ctrl.current_state.overlay_config.enabled_overlays

    def test_identity_transition_no_emit(self, qapp) -> None:
        ctrl = _make_controller(qapp)
        received = []
        ctrl.frame_changed.connect(lambda f: received.append(f))
        # step_backward at step 0 returns same state
        ctrl.step_backward()
        assert len(received) == 0


# ---------------------------------------------------------------------------
# MainWindow tests
# ---------------------------------------------------------------------------


class TestMainWindow:

    def test_main_window_construction(self, qapp) -> None:
        window = _make_window(qapp)
        assert window.windowTitle() == "AXIS Replay Viewer"
        assert window.width() == 1440

    def test_main_window_set_frame(self, qapp) -> None:
        window = _make_window(qapp)
        ctrl = _make_controller(qapp)
        # Should not crash
        window.set_frame(ctrl.current_frame)

    def test_main_window_properties(self, qapp) -> None:
        window = _make_window(qapp)
        from axis.visualization.ui.canvas_widget import CanvasWidget
        from axis.visualization.ui.replay_controls_panel import ReplayControlsPanel
        from axis.visualization.ui.overlay_panel import OverlayPanel
        assert isinstance(window.canvas, CanvasWidget)
        assert isinstance(window.replay_controls, ReplayControlsPanel)
        assert isinstance(window.overlay_panel, OverlayPanel)

    def test_main_window_opens_non_modal_config_viewer(self, qapp) -> None:
        window = VisualizationMainWindow(
            DefaultWorldVisualizationAdapter(),
            ["BEFORE", "INTER", "AFTER"],
            [OverlayTypeDeclaration(key="test", label="Test", description="Test")],
            experiment_config_text='{"system_type":"system_a"}',
            run_config_text='{"run_id":"run-0000"}',
        )
        window.show_config_viewer()
        assert window.config_window is not None
        assert window.config_window.isVisible()
        tabs = window.config_window.centralWidget()
        assert tabs is not None
        assert tabs.tabText(0) == "Experiment Config"
        assert tabs.tabText(1) == "Run Config"

    def test_main_window_config_button_disabled_without_configs(self, qapp) -> None:
        window = VisualizationMainWindow(
            DefaultWorldVisualizationAdapter(),
            ["BEFORE", "INTER", "AFTER"],
            [OverlayTypeDeclaration(key="test", label="Test", description="Test")],
        )
        assert window.config_button.isEnabled() is False


# ---------------------------------------------------------------------------
# Wire signals tests
# ---------------------------------------------------------------------------


class TestWireSignals:

    def test_wire_signals_no_crash(self, qapp) -> None:
        window = _make_window(qapp)
        ctrl = _make_controller(qapp)
        wire_signals(window, ctrl)

    def test_wire_signals_forward(self, qapp) -> None:
        window = _make_window(qapp)
        ctrl = _make_controller(qapp)
        wire_signals(window, ctrl)

        received = []
        ctrl.frame_changed.connect(lambda f: received.append(f))
        # Simulate clicking forward button
        window.replay_controls._btn_fwd.click()
        assert len(received) == 1
