"""Verification tests for WP-1.3: Replay Contract."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from axis.sdk import (
    BaseEpisodeTrace,
    BaseStepTrace,
    CellView,
    Position,
    WorldSnapshot,
    WorldView,
    snapshot_world,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cell(cell_type: str = "empty", resource: float = 0.0) -> CellView:
    return CellView(cell_type=cell_type, resource_value=resource)


def _make_snapshot(
    width: int = 2,
    height: int = 2,
    agent_pos: Position | None = None,
) -> WorldSnapshot:
    """Build a minimal WorldSnapshot for testing."""
    if agent_pos is None:
        agent_pos = Position(x=0, y=0)
    grid = tuple(
        tuple(_make_cell() for _ in range(width))
        for _ in range(height)
    )
    return WorldSnapshot(
        grid=grid, agent_position=agent_pos, width=width, height=height
    )


def _make_step_trace(
    *,
    timestep: int = 0,
    action: str = "stay",
    terminated: bool = False,
    termination_reason: str | None = None,
    vitality_before: float = 1.0,
    vitality_after: float = 0.9,
    intermediate_snapshots: dict[str, WorldSnapshot] | None = None,
    system_data: dict[str, Any] | None = None,
) -> BaseStepTrace:
    snap = _make_snapshot()
    return BaseStepTrace(
        timestep=timestep,
        action=action,
        world_before=snap,
        world_after=snap,
        intermediate_snapshots=intermediate_snapshots or {},
        agent_position_before=Position(x=0, y=0),
        agent_position_after=Position(x=0, y=0),
        vitality_before=vitality_before,
        vitality_after=vitality_after,
        terminated=terminated,
        termination_reason=termination_reason,
        system_data=system_data or {},
    )


# ---------------------------------------------------------------------------
# WorldSnapshot
# ---------------------------------------------------------------------------


class TestWorldSnapshot:
    """Tests for WorldSnapshot type."""

    def test_construction_2x2(self) -> None:
        snap = _make_snapshot(width=2, height=2)
        assert snap.width == 2
        assert snap.height == 2

    def test_grid_cell_type(self) -> None:
        snap = _make_snapshot()
        assert isinstance(snap.grid[0][0], CellView)

    def test_agent_position(self) -> None:
        pos = Position(x=1, y=1)
        snap = _make_snapshot(agent_pos=pos)
        assert snap.agent_position == pos

    def test_frozen(self) -> None:
        snap = _make_snapshot()
        with pytest.raises(ValidationError):
            snap.grid = ()  # type: ignore[misc]

    def test_width_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorldSnapshot(
                grid=((),),
                agent_position=Position(x=0, y=0),
                width=0,
                height=1,
            )

    def test_height_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorldSnapshot(
                grid=(),
                agent_position=Position(x=0, y=0),
                width=1,
                height=0,
            )

    def test_resource_cells_in_grid(self) -> None:
        """Snapshot can hold resource cells."""
        grid = (
            (_make_cell("resource", 0.5), _make_cell("empty", 0.0)),
            (_make_cell("obstacle", 0.0), _make_cell("resource", 1.0)),
        )
        snap = WorldSnapshot(
            grid=grid, agent_position=Position(x=0, y=0), width=2, height=2
        )
        assert snap.grid[0][0].resource_value == 0.5
        assert snap.grid[1][1].resource_value == 1.0


# ---------------------------------------------------------------------------
# snapshot_world function
# ---------------------------------------------------------------------------


class _MockWorldView:
    """Mock WorldView for testing snapshot_world."""

    def __init__(self, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self._agent_position = Position(x=1, y=0)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def agent_position(self) -> Position:
        return self._agent_position

    def get_cell(self, position: Position) -> CellView:
        # Return resource cell at (0,0), empty elsewhere
        if position.x == 0 and position.y == 0:
            return CellView(cell_type="resource", resource_value=0.8)
        return CellView(cell_type="empty", resource_value=0.0)

    def is_within_bounds(self, position: Position) -> bool:
        return 0 <= position.x < self._width and 0 <= position.y < self._height

    def is_traversable(self, position: Position) -> bool:
        return self.is_within_bounds(position)


class TestSnapshotWorld:
    """Tests for the snapshot_world helper function."""

    def test_dimensions(self) -> None:
        view = _MockWorldView(width=2, height=3)
        snap = snapshot_world(view, width=2, height=3)
        assert snap.width == 2
        assert snap.height == 3

    def test_grid_size(self) -> None:
        view = _MockWorldView(width=2, height=3)
        snap = snapshot_world(view, width=2, height=3)
        assert len(snap.grid) == 3  # rows
        assert len(snap.grid[0]) == 2  # cols

    def test_cell_values_match_view(self) -> None:
        view = _MockWorldView(width=3, height=2)
        snap = snapshot_world(view, width=3, height=2)
        assert snap.grid[0][0].cell_type == "resource"
        assert snap.grid[0][0].resource_value == 0.8
        assert snap.grid[0][1].cell_type == "empty"
        assert snap.grid[1][0].cell_type == "empty"

    def test_agent_position_matches_view(self) -> None:
        view = _MockWorldView(width=2, height=2)
        snap = snapshot_world(view, width=2, height=2)
        assert snap.agent_position == Position(x=1, y=0)

    def test_satisfies_world_view_protocol(self) -> None:
        assert isinstance(_MockWorldView(2, 2), WorldView)


# ---------------------------------------------------------------------------
# BaseStepTrace
# ---------------------------------------------------------------------------


class TestBaseStepTrace:
    """Tests for BaseStepTrace type."""

    def test_construction_minimal(self) -> None:
        trace = _make_step_trace()
        assert trace.timestep == 0
        assert trace.action == "stay"
        assert trace.terminated is False

    def test_defaults(self) -> None:
        trace = _make_step_trace()
        assert trace.intermediate_snapshots == {}
        assert trace.system_data == {}
        assert trace.termination_reason is None

    def test_construction_full(self) -> None:
        intermediate = _make_snapshot()
        trace = _make_step_trace(
            timestep=5,
            action="consume",
            terminated=True,
            termination_reason="energy_depleted",
            vitality_before=0.2,
            vitality_after=0.0,
            intermediate_snapshots={"after_regen": intermediate},
            system_data={"decision": {"temperature": 1.0}},
        )
        assert trace.timestep == 5
        assert trace.action == "consume"
        assert trace.terminated is True
        assert trace.termination_reason == "energy_depleted"
        assert "after_regen" in trace.intermediate_snapshots
        assert trace.system_data["decision"]["temperature"] == 1.0

    def test_vitality_before_above_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_step_trace(vitality_before=1.1)

    def test_vitality_before_below_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_step_trace(vitality_before=-0.1)

    def test_vitality_after_above_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_step_trace(vitality_after=1.1)

    def test_vitality_after_below_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_step_trace(vitality_after=-0.1)

    def test_timestep_negative_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_step_trace(timestep=-1)

    def test_frozen(self) -> None:
        trace = _make_step_trace()
        with pytest.raises(ValidationError):
            trace.action = "up"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# BaseStepTrace -- system_data extensibility
# ---------------------------------------------------------------------------


class TestSystemDataExtensibility:
    """Tests for system_data round-trip and nested data."""

    def test_nested_system_data(self) -> None:
        data = {
            "decision": {
                "observation": {"current": 0.5, "up": 0.3},
                "drive_output": {"activation": 0.8},
            },
            "transition": {
                "energy_before": 45.0,
                "energy_after": 43.5,
            },
        }
        trace = _make_step_trace(system_data=data)
        assert trace.system_data["decision"]["drive_output"]["activation"] == 0.8

    def test_round_trip_via_model_dump(self) -> None:
        data = {"key": [1, 2, 3], "nested": {"a": "b"}}
        trace = _make_step_trace(system_data=data)
        dumped = trace.model_dump()
        reconstructed = BaseStepTrace(**dumped)
        assert reconstructed.system_data == data
        assert reconstructed == trace

    def test_round_trip_json_mode(self) -> None:
        trace = _make_step_trace(
            system_data={"value": 42, "list": [1.0, 2.0]}
        )
        dumped = trace.model_dump(mode="json")
        reconstructed = BaseStepTrace(**dumped)
        assert reconstructed.system_data == trace.system_data


# ---------------------------------------------------------------------------
# BaseStepTrace -- intermediate_snapshots
# ---------------------------------------------------------------------------


class TestIntermediateSnapshots:
    """Tests for intermediate_snapshots in BaseStepTrace."""

    def test_single_intermediate(self) -> None:
        snap = _make_snapshot()
        trace = _make_step_trace(
            intermediate_snapshots={"after_regen": snap}
        )
        assert "after_regen" in trace.intermediate_snapshots
        assert trace.intermediate_snapshots["after_regen"] == snap

    def test_multiple_intermediates(self) -> None:
        snap1 = _make_snapshot(agent_pos=Position(x=0, y=0))
        snap2 = _make_snapshot(agent_pos=Position(x=1, y=1))
        trace = _make_step_trace(
            intermediate_snapshots={"after_regen": snap1, "after_dynamics": snap2}
        )
        assert len(trace.intermediate_snapshots) == 2
        assert trace.intermediate_snapshots["after_regen"].agent_position == Position(x=0, y=0)
        assert trace.intermediate_snapshots["after_dynamics"].agent_position == Position(x=1, y=1)


# ---------------------------------------------------------------------------
# BaseEpisodeTrace
# ---------------------------------------------------------------------------


class TestBaseEpisodeTrace:
    """Tests for BaseEpisodeTrace type."""

    def test_construction(self) -> None:
        step = _make_step_trace()
        episode = BaseEpisodeTrace(
            system_type="system_a",
            steps=(step,),
            total_steps=1,
            termination_reason="max_steps_reached",
            final_vitality=0.9,
            final_position=Position(x=0, y=0),
        )
        assert episode.system_type == "system_a"
        assert episode.total_steps == 1
        assert len(episode.steps) == 1

    def test_multiple_steps(self) -> None:
        steps = tuple(_make_step_trace(timestep=i) for i in range(5))
        episode = BaseEpisodeTrace(
            system_type="mock",
            steps=steps,
            total_steps=5,
            termination_reason="energy_depleted",
            final_vitality=0.0,
            final_position=Position(x=3, y=2),
        )
        assert episode.total_steps == 5
        assert episode.steps[4].timestep == 4

    def test_final_vitality_bounds(self) -> None:
        step = _make_step_trace()
        with pytest.raises(ValidationError):
            BaseEpisodeTrace(
                system_type="x",
                steps=(step,),
                total_steps=1,
                termination_reason="r",
                final_vitality=1.5,
                final_position=Position(x=0, y=0),
            )

    def test_frozen(self) -> None:
        step = _make_step_trace()
        episode = BaseEpisodeTrace(
            system_type="x",
            steps=(step,),
            total_steps=1,
            termination_reason="r",
            final_vitality=0.5,
            final_position=Position(x=0, y=0),
        )
        with pytest.raises(ValidationError):
            episode.system_type = "y"  # type: ignore[misc]

    def test_empty_episode(self) -> None:
        episode = BaseEpisodeTrace(
            system_type="x",
            steps=(),
            total_steps=0,
            termination_reason="immediate",
            final_vitality=1.0,
            final_position=Position(x=0, y=0),
        )
        assert episode.total_steps == 0
        assert len(episode.steps) == 0


# ---------------------------------------------------------------------------
# Import verification
# ---------------------------------------------------------------------------


class TestImports:
    """Verify that all WP-1.3 exports are importable."""

    def test_import_from_sdk(self) -> None:
        from axis.sdk import (  # noqa: F401
            BaseEpisodeTrace,
            BaseStepTrace,
            WorldSnapshot,
            snapshot_world,
        )

    def test_import_from_snapshot_module(self) -> None:
        from axis.sdk.snapshot import WorldSnapshot, snapshot_world  # noqa: F401

    def test_import_from_trace_module(self) -> None:
        from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace  # noqa: F401
