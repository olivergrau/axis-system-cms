"""Tests for VWP5 ViewModelBuilder."""

from __future__ import annotations

import sys

import pytest

from axis_system_a.enums import Action, CellType
from axis_system_a.visualization.snapshot_models import ReplayPhase
from axis_system_a.visualization.snapshot_resolver import SnapshotResolver
from axis_system_a.visualization.view_model_builder import ViewModelBuilder
from axis_system_a.visualization.view_models import (
    SelectionType,
    ViewerFrameViewModel,
)
from axis_system_a.visualization.viewer_state import (
    PlaybackMode,
    ViewerState,
)
from axis_system_a.visualization.viewer_state_transitions import (
    select_agent,
    select_cell,
    set_playback_mode,
)


@pytest.fixture
def builder(snapshot_resolver: SnapshotResolver) -> ViewModelBuilder:
    return ViewModelBuilder(snapshot_resolver)


@pytest.fixture
def frame(
    builder: ViewModelBuilder, initial_viewer_state: ViewerState,
) -> ViewerFrameViewModel:
    return builder.build(initial_viewer_state)


# ---------------------------------------------------------------------------
# Frame construction
# ---------------------------------------------------------------------------


class TestFrameConstruction:
    def test_build_returns_viewer_frame_view_model(
        self, frame: ViewerFrameViewModel,
    ):
        assert isinstance(frame, ViewerFrameViewModel)

    def test_coordinate_matches_state(
        self, frame: ViewerFrameViewModel, initial_viewer_state: ViewerState,
    ):
        assert frame.coordinate == initial_viewer_state.coordinate

    def test_phase_matches_state(
        self, frame: ViewerFrameViewModel, initial_viewer_state: ViewerState,
    ):
        assert frame.coordinate.phase == initial_viewer_state.coordinate.phase


# ---------------------------------------------------------------------------
# Grid projection
# ---------------------------------------------------------------------------


class TestGridProjection:
    def test_cell_count_matches_grid_dimensions(
        self, frame: ViewerFrameViewModel,
    ):
        assert len(frame.grid.cells) == frame.grid.width * frame.grid.height

    def test_grid_width_matches(
        self,
        frame: ViewerFrameViewModel,
        initial_viewer_state: ViewerState,
    ):
        assert (
            frame.grid.width
            == initial_viewer_state.episode_handle.validation.grid_width
        )

    def test_grid_height_matches(
        self,
        frame: ViewerFrameViewModel,
        initial_viewer_state: ViewerState,
    ):
        assert (
            frame.grid.height
            == initial_viewer_state.episode_handle.validation.grid_height
        )

    def test_cells_are_row_major(self, frame: ViewerFrameViewModel):
        w = frame.grid.width
        for i, cell in enumerate(frame.grid.cells):
            assert cell.row == i // w
            assert cell.col == i % w

    def test_resource_values_non_negative(self, frame: ViewerFrameViewModel):
        for cell in frame.grid.cells:
            assert cell.resource_value >= 0.0

    def test_obstacle_cells_have_is_obstacle_true(
        self, frame: ViewerFrameViewModel,
    ):
        for cell in frame.grid.cells:
            if cell.cell_type == CellType.OBSTACLE:
                assert cell.is_obstacle is True
                assert cell.is_traversable is False
            else:
                assert cell.is_obstacle is False
                assert cell.is_traversable is True

    def test_exactly_one_cell_has_agent(self, frame: ViewerFrameViewModel):
        agent_cells = [c for c in frame.grid.cells if c.is_agent_here]
        assert len(agent_cells) == 1

    def test_selected_cell_projection(
        self,
        builder: ViewModelBuilder,
        initial_viewer_state: ViewerState,
    ):
        state = select_cell(initial_viewer_state, 0, 0)
        frame = builder.build(state)
        selected = [c for c in frame.grid.cells if c.is_selected]
        assert len(selected) == 1
        assert selected[0].row == 0
        assert selected[0].col == 0

    def test_no_selection_means_no_cells_selected(
        self, frame: ViewerFrameViewModel,
    ):
        selected = [c for c in frame.grid.cells if c.is_selected]
        assert len(selected) == 0


# ---------------------------------------------------------------------------
# Agent projection
# ---------------------------------------------------------------------------


class TestAgentProjection:
    def test_agent_position(
        self,
        builder: ViewModelBuilder,
        initial_viewer_state: ViewerState,
        snapshot_resolver: SnapshotResolver,
    ):
        snapshot = snapshot_resolver.resolve(
            initial_viewer_state.episode_handle,
            initial_viewer_state.coordinate.step_index,
            initial_viewer_state.coordinate.phase,
        )
        frame = builder.build(initial_viewer_state)
        assert frame.agent.row == snapshot.agent_position.y
        assert frame.agent.col == snapshot.agent_position.x

    def test_agent_energy_matches_snapshot(
        self,
        builder: ViewModelBuilder,
        initial_viewer_state: ViewerState,
        snapshot_resolver: SnapshotResolver,
    ):
        snapshot = snapshot_resolver.resolve(
            initial_viewer_state.episode_handle,
            initial_viewer_state.coordinate.step_index,
            initial_viewer_state.coordinate.phase,
        )
        frame = builder.build(initial_viewer_state)
        assert frame.agent.energy == snapshot.agent_energy

    def test_agent_not_selected_by_default(
        self, frame: ViewerFrameViewModel,
    ):
        assert frame.agent.is_selected is False

    def test_agent_selected_when_state_has_agent_selected(
        self,
        builder: ViewModelBuilder,
        initial_viewer_state: ViewerState,
    ):
        state = select_agent(initial_viewer_state)
        frame = builder.build(state)
        assert frame.agent.is_selected is True


# ---------------------------------------------------------------------------
# Status projection
# ---------------------------------------------------------------------------


class TestStatusProjection:
    def test_step_index_matches(self, frame: ViewerFrameViewModel):
        assert frame.status.step_index == 0

    def test_total_steps_matches(
        self,
        frame: ViewerFrameViewModel,
        initial_viewer_state: ViewerState,
    ):
        assert (
            frame.status.total_steps
            == initial_viewer_state.episode_handle.validation.total_steps
        )

    def test_phase_matches(self, frame: ViewerFrameViewModel):
        assert frame.status.phase is ReplayPhase.BEFORE

    def test_playback_mode_matches(self, frame: ViewerFrameViewModel):
        assert frame.status.playback_mode is PlaybackMode.STOPPED

    def test_energy_matches_agent(self, frame: ViewerFrameViewModel):
        assert frame.status.energy == frame.agent.energy

    def test_at_start_true_for_initial(self, frame: ViewerFrameViewModel):
        assert frame.status.at_start is True

    def test_at_end_false_for_initial(self, frame: ViewerFrameViewModel):
        assert frame.status.at_end is False


# ---------------------------------------------------------------------------
# Selection projection
# ---------------------------------------------------------------------------


class TestSelectionProjection:
    def test_no_selection_gives_none_type(self, frame: ViewerFrameViewModel):
        assert frame.selection.selection_type is SelectionType.NONE
        assert frame.selection.selected_cell is None
        assert frame.selection.agent_selected is False

    def test_cell_selection_gives_cell_type(
        self,
        builder: ViewModelBuilder,
        initial_viewer_state: ViewerState,
    ):
        state = select_cell(initial_viewer_state, 1, 2)
        frame = builder.build(state)
        assert frame.selection.selection_type is SelectionType.CELL

    def test_agent_selection_gives_agent_type(
        self,
        builder: ViewModelBuilder,
        initial_viewer_state: ViewerState,
    ):
        state = select_agent(initial_viewer_state)
        frame = builder.build(state)
        assert frame.selection.selection_type is SelectionType.AGENT
        assert frame.selection.agent_selected is True

    def test_selected_cell_coordinates_match(
        self,
        builder: ViewModelBuilder,
        initial_viewer_state: ViewerState,
    ):
        state = select_cell(initial_viewer_state, 1, 2)
        frame = builder.build(state)
        assert frame.selection.selected_cell == (1, 2)


# ---------------------------------------------------------------------------
# Action context projection
# ---------------------------------------------------------------------------


class TestActionContextProjection:
    def test_action_from_snapshot(self, frame: ViewerFrameViewModel):
        assert isinstance(frame.action_context.action, Action)

    def test_moved_from_snapshot(self, frame: ViewerFrameViewModel):
        assert isinstance(frame.action_context.moved, bool)

    def test_consumed_from_snapshot(self, frame: ViewerFrameViewModel):
        assert isinstance(frame.action_context.consumed, bool)


# ---------------------------------------------------------------------------
# Purity and determinism
# ---------------------------------------------------------------------------


class TestPurity:
    def test_build_does_not_mutate_state(
        self,
        builder: ViewModelBuilder,
        initial_viewer_state: ViewerState,
    ):
        original_coord = initial_viewer_state.coordinate
        _ = builder.build(initial_viewer_state)
        assert initial_viewer_state.coordinate is original_coord

    def test_deterministic_builds(
        self,
        builder: ViewModelBuilder,
        initial_viewer_state: ViewerState,
    ):
        a = builder.build(initial_viewer_state)
        b = builder.build(initial_viewer_state)
        assert a == b

    def test_independent_builders_produce_equal_results(
        self,
        snapshot_resolver: SnapshotResolver,
        initial_viewer_state: ViewerState,
    ):
        b1 = ViewModelBuilder(snapshot_resolver)
        b2 = ViewModelBuilder(snapshot_resolver)
        assert b1.build(initial_viewer_state) == b2.build(initial_viewer_state)


# ---------------------------------------------------------------------------
# UI independence
# ---------------------------------------------------------------------------


class TestUIIndependence:
    def test_view_models_no_qt_imports(self):
        import axis_system_a.visualization.view_models  # noqa: F401

        qt_modules = [m for m in sys.modules if "PySide" in m or "PyQt" in m]
        assert qt_modules == []

    def test_view_model_builder_no_qt_imports(self):
        import axis_system_a.visualization.view_model_builder  # noqa: F401

        qt_modules = [m for m in sys.modules if "PySide" in m or "PyQt" in m]
        assert qt_modules == []
