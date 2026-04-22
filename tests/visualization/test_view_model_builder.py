"""Tests for WP-V.3.4: ViewModelBuilder and Frame ViewModel."""

from __future__ import annotations

from typing import Any

import pytest

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import CellView

from axis.visualization.adapters.default_world import DefaultWorldVisualizationAdapter
from axis.visualization.adapters.null_system import NullSystemVisualizationAdapter
from axis.visualization.replay_models import (
    ReplayEpisodeHandle,
    ReplayStepDescriptor,
    ReplayValidationResult,
)
from axis.visualization.snapshot_models import ReplayCoordinate
from axis.visualization.snapshot_resolver import SnapshotResolver
from axis.visualization.types import (
    AnalysisRow,
    AnalysisSection,
    CellLayout,
    MetadataSection,
    OverlayData,
    OverlayItem,
    OverlayTypeDeclaration,
    TopologyIndicator,
)
from axis.visualization.view_model_builder import ViewModelBuilder
from axis.visualization.view_models import (
    SelectionType,
    ViewerFrameViewModel,
)
from axis.visualization.viewer_state import (
    OverlayConfig,
    PlaybackMode,
    ViewerState,
    create_initial_state,
)
from axis.visualization.viewer_state_transitions import (
    select_agent,
    select_cell,
    seek,
    set_overlay_enabled,
    toggle_overlay_master,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cell(
    resource: float = 0.0, traversable: bool = True,
) -> CellView:
    ct = "obstacle" if not traversable else (
        "resource" if resource > 0 else "empty")
    return CellView(cell_type=ct, resource_value=resource)


def _make_snapshot(
    width: int = 5, height: int = 5,
    agent_pos: Position | None = None,
    has_obstacle: bool = False,
) -> WorldSnapshot:
    pos = agent_pos or Position(x=1, y=1)
    rows = []
    for r in range(height):
        row = []
        for c in range(width):
            if has_obstacle and r == 0 and c == 0:
                row.append(_make_cell(traversable=False))
            elif r == 2 and c == 2:
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
    action: str = "right",
    system_data: dict[str, Any] | None = None,
) -> BaseStepTrace:
    pos_b = agent_pos_before or Position(x=1, y=1)
    pos_a = agent_pos_after or Position(x=2, y=1)
    return BaseStepTrace(
        timestep=timestep, action=action,
        world_before=_make_snapshot(agent_pos=pos_b),
        world_after=_make_snapshot(agent_pos=pos_a),
        agent_position_before=pos_b,
        agent_position_after=pos_a,
        vitality_before=0.8, vitality_after=0.75,
        terminated=False,
        system_data=system_data or {},
    )


def _sample_episode_handle(
    num_steps: int = 5,
    grid_width: int = 5,
    grid_height: int = 5,
    steps: tuple[BaseStepTrace, ...] | None = None,
) -> ReplayEpisodeHandle:
    steps = steps or tuple(_make_step(timestep=i) for i in range(num_steps))
    total_steps = len(steps)
    episode = BaseEpisodeTrace(
        system_type="test", steps=steps, total_steps=total_steps,
        termination_reason="max_steps", final_vitality=0.75,
        final_position=Position(x=0, y=0),
    )
    descriptors = tuple(
        ReplayStepDescriptor(
            step_index=i, has_world_before=True, has_world_after=True,
            has_intermediate_snapshots=(), has_agent_position=True,
            has_vitality=True, has_world_state=True,
        )
        for i in range(total_steps)
    )
    validation = ReplayValidationResult(
        valid=True, total_steps=total_steps,
        grid_width=grid_width, grid_height=grid_height,
        step_descriptors=descriptors,
    )
    return ReplayEpisodeHandle(
        experiment_id="exp", run_id="run", episode_index=0,
        episode_trace=episode, validation=validation,
    )


# ---------------------------------------------------------------------------
# Mock adapters
# ---------------------------------------------------------------------------


class MockWorldAdapter:
    """Satisfies WorldVisualizationAdapter protocol for testing."""

    def __init__(
        self, *, topology: list[TopologyIndicator] | None = None,
        metadata: list[MetadataSection] | None = None,
        world_info: str | None = None,
    ):
        self._topology = topology or []
        self._metadata = metadata or []
        self._world_info = world_info

    def cell_shape(self):
        from axis.visualization.types import CellShape
        return CellShape.RECTANGULAR

    def cell_layout(self, width, height, canvas_w, canvas_h):
        cw = canvas_w / width
        ch = canvas_h / height
        centers = {}
        polygons = {}
        bboxes = {}
        for r in range(height):
            for c in range(width):
                x0 = c * cw
                y0 = r * ch
                centers[(c, r)] = (x0 + cw / 2, y0 + ch / 2)
                polygons[(c, r)] = (
                    (x0, y0), (x0 + cw, y0),
                    (x0 + cw, y0 + ch), (x0, y0 + ch),
                )
                bboxes[(c, r)] = (x0, y0, cw, ch)
        from axis.visualization.types import CellShape
        return CellLayout(
            cell_shape=CellShape.RECTANGULAR,
            grid_width=width, grid_height=height,
            canvas_width=canvas_w, canvas_height=canvas_h,
            cell_polygons=polygons,
            cell_centers=centers,
            cell_bounding_boxes=bboxes,
        )

    def cell_color_config(self):
        from axis.visualization.adapters.default_world import DefaultWorldVisualizationAdapter
        return DefaultWorldVisualizationAdapter().cell_color_config()

    def topology_indicators(self, snapshot, world_data, layout):
        return self._topology

    def pixel_to_grid(self, px, py, layout):
        return None

    def format_world_info(self, world_data):
        return self._world_info

    def world_metadata_sections(self, world_data):
        return self._metadata


class MockSystemAdapter:
    """Satisfies SystemVisualizationAdapter protocol for testing."""

    def __init__(
        self, *, num_phases: int = 3,
        analysis: list[AnalysisSection] | None = None,
        overlays: list[OverlayData] | None = None,
    ):
        self._num_phases = num_phases
        self._analysis = analysis or [
            AnalysisSection(
                title="Test Section",
                rows=(AnalysisRow(label="Key", value="Val"),),
            ),
            AnalysisSection(
                title="Test Section 2",
                rows=(AnalysisRow(label="K2", value="V2"),),
            ),
        ]
        self._overlays = overlays or [
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
        return self._analysis

    def build_overlays(self, step_trace):
        return self._overlays

    def available_overlay_types(self):
        return [
            OverlayTypeDeclaration(
                key="test_overlay",
                label="Test", description="Test overlay",
            ),
        ]


# ---------------------------------------------------------------------------
# Builder fixture
# ---------------------------------------------------------------------------


def _build_frame(
    state: ViewerState,
    world_adapter: Any = None,
    system_adapter: Any = None,
) -> ViewerFrameViewModel:
    builder = ViewModelBuilder(
        snapshot_resolver=SnapshotResolver(),
        world_adapter=world_adapter or MockWorldAdapter(),
        system_adapter=system_adapter or MockSystemAdapter(),
    )
    return builder.build(state)


def _initial_state(num_phases: int = 3) -> ViewerState:
    return create_initial_state(_sample_episode_handle(), num_phases)


# ---------------------------------------------------------------------------
# Grid projection tests
# ---------------------------------------------------------------------------


class TestGridProjection:

    def test_grid_vm_dimensions(self) -> None:
        frame = _build_frame(_initial_state())
        assert frame.grid.width == 5
        assert frame.grid.height == 5

    def test_grid_vm_cell_count(self) -> None:
        frame = _build_frame(_initial_state())
        assert len(frame.grid.cells) == 25

    def test_grid_vm_agent_position(self) -> None:
        frame = _build_frame(_initial_state())
        agent_cells = [c for c in frame.grid.cells if c.is_agent_here]
        assert len(agent_cells) == 1
        # agent position_before is (x=1, y=1) → row=1, col=1
        assert agent_cells[0].row == 1
        assert agent_cells[0].col == 1

    def test_grid_vm_selected_cell(self) -> None:
        state = select_cell(_initial_state(), 2, 3)
        frame = _build_frame(state)
        selected = [c for c in frame.grid.cells if c.is_selected]
        assert len(selected) == 1
        assert selected[0].row == 2
        assert selected[0].col == 3

    def test_grid_vm_no_selection(self) -> None:
        frame = _build_frame(_initial_state())
        selected = [c for c in frame.grid.cells if c.is_selected]
        assert len(selected) == 0

    def test_grid_vm_obstacle_detection(self) -> None:
        # Create episode with obstacle in the world
        snap = _make_snapshot(has_obstacle=True, agent_pos=Position(x=1, y=1))
        step = BaseStepTrace(
            timestep=0, action="stay",
            world_before=snap, world_after=snap,
            agent_position_before=Position(x=1, y=1),
            agent_position_after=Position(x=1, y=1),
            vitality_before=0.8, vitality_after=0.75,
            terminated=False,
        )
        episode = BaseEpisodeTrace(
            system_type="test", steps=(step,), total_steps=1,
            termination_reason="max_steps", final_vitality=0.75,
            final_position=Position(x=1, y=1),
        )
        descriptors = (ReplayStepDescriptor(
            step_index=0, has_world_before=True, has_world_after=True,
            has_intermediate_snapshots=(), has_agent_position=True,
            has_vitality=True, has_world_state=True,
        ),)
        validation = ReplayValidationResult(
            valid=True, total_steps=1, grid_width=5, grid_height=5,
            step_descriptors=descriptors,
        )
        handle = ReplayEpisodeHandle(
            experiment_id="exp", run_id="run", episode_index=0,
            episode_trace=episode, validation=validation,
        )
        state = create_initial_state(handle, 3)
        frame = _build_frame(state)
        obstacle_cells = [c for c in frame.grid.cells if c.is_obstacle]
        assert len(obstacle_cells) == 1
        assert obstacle_cells[0].row == 0
        assert obstacle_cells[0].col == 0


# ---------------------------------------------------------------------------
# Agent projection tests
# ---------------------------------------------------------------------------


class TestAgentProjection:

    def test_agent_vm_position(self) -> None:
        frame = _build_frame(_initial_state())
        # position_before is (x=1, y=1) → row=y=1, col=x=1
        assert frame.agent.row == 1
        assert frame.agent.col == 1

    def test_agent_vm_vitality(self) -> None:
        frame = _build_frame(_initial_state())
        assert frame.agent.vitality == 0.8  # vitality_before

    def test_agent_vm_selected(self) -> None:
        state = select_agent(_initial_state())
        frame = _build_frame(state)
        assert frame.agent.is_selected is True


# ---------------------------------------------------------------------------
# Status bar tests
# ---------------------------------------------------------------------------


class TestStatusBar:

    def test_status_step_and_total(self) -> None:
        frame = _build_frame(_initial_state())
        assert frame.status.step_index == 0
        assert frame.status.total_steps == 5

    def test_status_phase_info(self) -> None:
        frame = _build_frame(_initial_state())
        assert frame.status.phase_index == 0
        assert frame.status.phase_name == "BEFORE"

    def test_status_vitality_display(self) -> None:
        frame = _build_frame(_initial_state())
        assert frame.status.vitality_display == "80.00 / 100.00"

    def test_status_vitality_label(self) -> None:
        frame = _build_frame(_initial_state())
        assert frame.status.vitality_label == "Energy"

    def test_status_world_info(self) -> None:
        adapter = MockWorldAdapter(world_info="Toroidal topology")
        frame = _build_frame(_initial_state(), world_adapter=adapter)
        assert frame.status.world_info == "Toroidal topology"

    def test_status_at_start_at_end(self) -> None:
        state = _initial_state()
        frame = _build_frame(state)
        assert frame.status.at_start is True
        assert frame.status.at_end is False

        # Move to last step, last phase
        state2 = seek(state, ReplayCoordinate(step_index=4, phase_index=2))
        frame2 = _build_frame(state2)
        assert frame2.status.at_start is False
        assert frame2.status.at_end is True


# ---------------------------------------------------------------------------
# Selection tests
# ---------------------------------------------------------------------------


class TestSelection:

    def test_selection_none(self) -> None:
        frame = _build_frame(_initial_state())
        assert frame.selection.selection_type == SelectionType.NONE

    def test_selection_cell(self) -> None:
        state = select_cell(_initial_state(), 1, 2)
        frame = _build_frame(state)
        assert frame.selection.selection_type == SelectionType.CELL
        assert frame.selection.selected_cell == (1, 2)

    def test_selection_agent(self) -> None:
        state = select_agent(_initial_state())
        frame = _build_frame(state)
        assert frame.selection.selection_type == SelectionType.AGENT
        assert frame.selection.agent_selected is True


# ---------------------------------------------------------------------------
# Adapter delegation tests
# ---------------------------------------------------------------------------


class TestAdapterDelegation:

    def test_topology_indicators_from_world_adapter(self) -> None:
        indicator = TopologyIndicator(
            indicator_type="wrap_edge",
            position=(0.0, 0.0),
            data={"edge": "top"},
        )
        adapter = MockWorldAdapter(topology=[indicator])
        frame = _build_frame(_initial_state(), world_adapter=adapter)
        assert len(frame.topology_indicators) == 1
        assert frame.topology_indicators[0].indicator_type == "wrap_edge"

    def test_world_metadata_from_world_adapter(self) -> None:
        section = MetadataSection(
            title="World Info",
            rows=(AnalysisRow(label="Type", value="Toroidal"),),
        )
        adapter = MockWorldAdapter(metadata=[section])
        frame = _build_frame(_initial_state(), world_adapter=adapter)
        assert len(frame.world_metadata_sections) == 1
        assert frame.world_metadata_sections[0].title == "World Info"

    def test_analysis_sections_from_system_adapter(self) -> None:
        frame = _build_frame(_initial_state())
        assert len(frame.analysis_sections) == 2
        assert frame.analysis_sections[0].title == "Test Section"

    def test_overlay_data_from_system_adapter(self) -> None:
        state = _initial_state()
        state = toggle_overlay_master(state)
        state = set_overlay_enabled(state, "test_overlay", True)
        frame = _build_frame(state)
        assert len(frame.overlay_data) == 1
        assert frame.overlay_data[0].overlay_type == "test_overlay"

    def test_policy_widget_data_from_nested_policy_trace(self) -> None:
        step = _make_step(system_data={
            "decision_data": {
                "policy": {
                    "raw_contributions": (0.1, 0.4, 0.0, 0.0, -0.1, -0.2),
                    "masked_contributions": (0.1, 0.4, 0.0, 0.0, -0.1, -0.2),
                    "probabilities": (0.16, 0.24, 0.16, 0.16, 0.14, 0.14),
                    "selected_action": "down",
                    "temperature": 1.5,
                    "selection_mode": "sample",
                },
            },
        })
        state = create_initial_state(_sample_episode_handle(steps=(step,)), 3)
        frame = _build_frame(state)
        assert frame.policy_widget_data is not None
        assert frame.policy_widget_data["selected_action"] == "down"
        assert frame.policy_widget_data["labels"] == [
            "up", "down", "left", "right", "consume", "stay",
        ]

    def test_policy_widget_data_from_system_b_style_trace(self) -> None:
        step = _make_step(
            action="scan",
            system_data={
                "decision_data": {
                    "weights": [0.2, 0.3, 0.0, 0.5, 1.0, 0.1],
                    "probabilities": [0.10, 0.12, 0.09, 0.15, 0.44, 0.10],
                    "last_scan": {"total_resource": 1.5, "cell_count": 3},
                },
            },
        )
        state = create_initial_state(_sample_episode_handle(steps=(step,)), 3)
        frame = _build_frame(state)
        assert frame.policy_widget_data is not None
        assert frame.policy_widget_data["selected_action"] == "scan"
        assert frame.policy_widget_data["labels"] == [
            "up", "down", "left", "right", "scan", "stay",
        ]


# ---------------------------------------------------------------------------
# Overlay filtering tests
# ---------------------------------------------------------------------------


class TestOverlayFiltering:

    def test_overlays_empty_when_master_disabled(self) -> None:
        state = _initial_state()
        # master is off by default
        frame = _build_frame(state)
        assert len(frame.overlay_data) == 0

    def test_overlays_filtered_by_enabled_set(self) -> None:
        overlays = [
            OverlayData(overlay_type="type_a", items=()),
            OverlayData(overlay_type="type_b", items=()),
        ]
        adapter = MockSystemAdapter(overlays=overlays)
        state = toggle_overlay_master(_initial_state())
        state = set_overlay_enabled(state, "type_a", True)
        frame = _build_frame(state, system_adapter=adapter)
        assert len(frame.overlay_data) == 1
        assert frame.overlay_data[0].overlay_type == "type_a"

    def test_overlays_all_enabled(self) -> None:
        overlays = [
            OverlayData(overlay_type="type_a", items=()),
            OverlayData(overlay_type="type_b", items=()),
        ]
        adapter = MockSystemAdapter(overlays=overlays)
        state = toggle_overlay_master(_initial_state())
        state = set_overlay_enabled(state, "type_a", True)
        state = set_overlay_enabled(state, "type_b", True)
        frame = _build_frame(state, system_adapter=adapter)
        assert len(frame.overlay_data) == 2


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestIntegration:

    def test_build_produces_complete_frame(self) -> None:
        frame = _build_frame(_initial_state())
        assert frame.coordinate is not None
        assert frame.grid is not None
        assert frame.agent is not None
        assert frame.status is not None
        assert frame.selection is not None
        assert frame.topology_indicators is not None
        assert frame.world_metadata_sections is not None
        assert frame.analysis_sections is not None
        assert frame.overlay_data is not None

    def test_build_with_null_system_adapter(self) -> None:
        adapter = NullSystemVisualizationAdapter()
        state = create_initial_state(_sample_episode_handle(), 2)
        frame = _build_frame(state, system_adapter=adapter)
        assert len(frame.analysis_sections) == 0
        assert len(frame.overlay_data) == 0
        assert frame.status.vitality_label == "Vitality"

    def test_build_with_default_world_adapter(self) -> None:
        adapter = DefaultWorldVisualizationAdapter()
        state = _initial_state()
        frame = _build_frame(state, world_adapter=adapter)
        assert len(frame.topology_indicators) == 0
        assert len(frame.world_metadata_sections) == 0
        assert frame.status.world_info is None
