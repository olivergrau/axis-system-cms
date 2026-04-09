"""Tests for WP-V.5.1: Adapter Combinations.

Wire all 12 (world × system) adapter pairs through ViewModelBuilder
and verify complete ViewerFrameViewModel construction.
"""

from __future__ import annotations

import pytest

from axis.sdk.position import Position
from axis.visualization.snapshot_models import ReplayCoordinate
from axis.visualization.snapshot_resolver import SnapshotResolver
from axis.visualization.view_model_builder import ViewModelBuilder
from axis.visualization.view_models import ViewerFrameViewModel
from axis.visualization.viewer_state import create_initial_state

from tests.visualization.adapter_fixtures import (
    ALL_SYSTEM_ADAPTERS,
    ALL_WORLD_ADAPTERS,
    make_episode_handle,
    make_episode_trace,
    make_snapshot,
    sample_signal_landscape_world_data,
    sample_system_a_data,
    sample_system_b_data,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_frame(world_adapter, system_adapter, system_data=None,
                 world_data=None, intermediate_snapshots=None,
                 obstacles=None, resources=None):
    """Build a ViewerFrameViewModel for the given adapter pair."""
    num_phases = len(system_adapter.phase_names())
    episode = make_episode_trace(
        num_steps=3,
        system_data=system_data or {},
        world_data=world_data or {},
        intermediate_snapshots=intermediate_snapshots,
        obstacles=obstacles,
        resources=resources,
    )
    handle = make_episode_handle(episode)
    state = create_initial_state(handle, num_phases)
    builder = ViewModelBuilder(
        SnapshotResolver(), world_adapter, system_adapter)
    return builder.build(state)


def _system_data_for(adapter_id: str) -> dict:
    if adapter_id == "system_a":
        return sample_system_a_data()
    elif adapter_id == "system_b":
        return sample_system_b_data()
    return {}


def _intermediate_for(adapter_id: str):
    """Build intermediate snapshots needed for 3-phase systems."""
    if adapter_id == "system_a":
        return {"AFTER_REGEN": make_snapshot()}
    return None


# ---------------------------------------------------------------------------
# All 12 combinations
# ---------------------------------------------------------------------------

_COMBOS = [
    (wid, wadapter, sid, sadapter)
    for wid, wadapter in ALL_WORLD_ADAPTERS
    for sid, sadapter in ALL_SYSTEM_ADAPTERS
]
_COMBO_IDS = [f"{wid}+{sid}" for wid, _, sid, _ in _COMBOS]


@pytest.fixture(params=_COMBOS, ids=_COMBO_IDS)
def combo(request):
    return request.param


class TestAllCombinations:

    def test_frame_produced(self, combo) -> None:
        wid, wadapter, sid, sadapter = combo
        frame = _build_frame(
            wadapter, sadapter,
            system_data=_system_data_for(sid),
            intermediate_snapshots=_intermediate_for(sid),
        )
        assert isinstance(frame, ViewerFrameViewModel)

    def test_frame_has_grid(self, combo) -> None:
        wid, wadapter, sid, sadapter = combo
        frame = _build_frame(
            wadapter, sadapter,
            system_data=_system_data_for(sid),
            intermediate_snapshots=_intermediate_for(sid),
        )
        assert frame.grid is not None
        assert frame.grid.width == 5
        assert frame.grid.height == 5

    def test_frame_has_agent(self, combo) -> None:
        wid, wadapter, sid, sadapter = combo
        frame = _build_frame(
            wadapter, sadapter,
            system_data=_system_data_for(sid),
            intermediate_snapshots=_intermediate_for(sid),
        )
        assert frame.agent is not None

    def test_frame_has_status(self, combo) -> None:
        wid, wadapter, sid, sadapter = combo
        frame = _build_frame(
            wadapter, sadapter,
            system_data=_system_data_for(sid),
            intermediate_snapshots=_intermediate_for(sid),
        )
        assert frame.status is not None
        assert isinstance(frame.status.vitality_display, str)

    def test_frame_has_selection(self, combo) -> None:
        wid, wadapter, sid, sadapter = combo
        frame = _build_frame(
            wadapter, sadapter,
            system_data=_system_data_for(sid),
            intermediate_snapshots=_intermediate_for(sid),
        )
        assert frame.selection is not None

    def test_grid_cell_count(self, combo) -> None:
        wid, wadapter, sid, sadapter = combo
        frame = _build_frame(
            wadapter, sadapter,
            system_data=_system_data_for(sid),
            intermediate_snapshots=_intermediate_for(sid),
        )
        assert len(frame.grid.cells) == 25  # 5x5

    def test_agent_position_consistent(self, combo) -> None:
        wid, wadapter, sid, sadapter = combo
        frame = _build_frame(
            wadapter, sadapter,
            system_data=_system_data_for(sid),
            intermediate_snapshots=_intermediate_for(sid),
        )
        assert frame.agent.row == 1  # y=1
        assert frame.agent.col == 1  # x=1


# ---------------------------------------------------------------------------
# Cross-adapter consistency tests
# ---------------------------------------------------------------------------


class TestCrossAdapterConsistency:

    def test_toroidal_has_topology_indicators(self) -> None:
        from axis.world.toroidal.visualization import (
            ToroidalWorldVisualizationAdapter,
        )
        from axis.visualization.adapters.null_system import (
            NullSystemVisualizationAdapter,
        )
        frame = _build_frame(
            ToroidalWorldVisualizationAdapter(),
            NullSystemVisualizationAdapter(),
        )
        assert len(frame.topology_indicators) == 4

    def test_grid2d_no_topology(self) -> None:
        from axis.world.grid_2d.visualization import (
            Grid2DWorldVisualizationAdapter,
        )
        from axis.visualization.adapters.null_system import (
            NullSystemVisualizationAdapter,
        )
        frame = _build_frame(
            Grid2DWorldVisualizationAdapter(),
            NullSystemVisualizationAdapter(),
        )
        assert len(frame.topology_indicators) == 0

    def test_vitality_format_varies_by_system(self) -> None:
        from axis.visualization.adapters.default_world import (
            DefaultWorldVisualizationAdapter,
        )
        from axis.visualization.adapters.null_system import (
            NullSystemVisualizationAdapter,
        )
        from axis.systems.system_a.visualization import (
            SystemAVisualizationAdapter,
        )
        w = DefaultWorldVisualizationAdapter()

        frame_a = _build_frame(
            w, SystemAVisualizationAdapter(max_energy=100.0),
            system_data=sample_system_a_data(),
            intermediate_snapshots={"AFTER_REGEN": make_snapshot()},
        )
        frame_null = _build_frame(w, NullSystemVisualizationAdapter())

        # System A: "X.XX / 100.00" format
        assert "/" in frame_a.status.vitality_display
        # Null: "X%" format
        assert "%" in frame_null.status.vitality_display

    def test_world_info_varies_by_world(self) -> None:
        from axis.visualization.adapters.null_system import (
            NullSystemVisualizationAdapter,
        )
        from axis.world.grid_2d.visualization import (
            Grid2DWorldVisualizationAdapter,
        )
        from axis.world.toroidal.visualization import (
            ToroidalWorldVisualizationAdapter,
        )
        sys_adapter = NullSystemVisualizationAdapter()

        frame_grid = _build_frame(
            Grid2DWorldVisualizationAdapter(), sys_adapter)
        frame_toro = _build_frame(
            ToroidalWorldVisualizationAdapter(), sys_adapter)

        assert frame_grid.status.world_info is None
        assert frame_toro.status.world_info is not None
        assert "Toroidal" in frame_toro.status.world_info
