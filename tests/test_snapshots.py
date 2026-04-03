"""Tests for snapshot types and factory functions."""

import json

import pytest
from pydantic import ValidationError

from axis_system_a import (
    AgentSnapshot,
    AgentState,
    Cell,
    CellType,
    MemoryEntry,
    MemoryState,
    Observation,
    CellObservation,
    Position,
    RegenSummary,
    World,
    WorldSnapshot,
    snapshot_agent,
    snapshot_world,
)


def _make_observation() -> Observation:
    cell = CellObservation(traversability=1.0, resource=0.5)
    return Observation(current=cell, up=cell, down=cell, left=cell, right=cell)


class TestWorldSnapshot:
    def test_frozen(self):
        empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        ws = WorldSnapshot(
            grid=((empty,),), agent_position=Position(x=0, y=0),
            width=1, height=1,
        )
        with pytest.raises(ValidationError):
            ws.width = 2

    def test_grid_is_tuple_of_tuples(self):
        empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        ws = WorldSnapshot(
            grid=((empty, empty), (empty, empty)),
            agent_position=Position(x=0, y=0), width=2, height=2,
        )
        assert isinstance(ws.grid, tuple)
        assert isinstance(ws.grid[0], tuple)

    def test_snapshot_world_captures_all_cells(self):
        empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        res = Cell(cell_type=CellType.RESOURCE, resource_value=0.7)
        grid = [[empty, res], [res, empty]]
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        ws = snapshot_world(world)
        assert ws.grid[0][0] == empty
        assert ws.grid[0][1] == res
        assert ws.grid[1][0] == res
        assert ws.grid[1][1] == empty

    def test_snapshot_world_captures_agent_position(self):
        empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        grid = [[empty, empty], [empty, empty]]
        world = World(grid=grid, agent_position=Position(x=1, y=0))
        ws = snapshot_world(world)
        assert ws.agent_position == Position(x=1, y=0)

    def test_snapshot_world_dimensions(self):
        empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        grid = [[empty, empty, empty], [empty, empty, empty]]
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        ws = snapshot_world(world)
        assert ws.width == 3
        assert ws.height == 2

    def test_to_dict_serializable(self):
        empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        ws = WorldSnapshot(
            grid=((empty,),), agent_position=Position(x=0, y=0),
            width=1, height=1,
        )
        d = ws.model_dump(mode="python")
        assert isinstance(d, dict)
        json.dumps(d, default=str)  # should not raise


class TestAgentSnapshot:
    def test_frozen(self):
        snap = AgentSnapshot(
            energy=50.0, position=Position(x=0, y=0),
            memory_entry_count=0, memory_timestep_range=None,
        )
        with pytest.raises(ValidationError):
            snap.energy = 100.0

    def test_memory_timestep_range_none_when_empty(self):
        state = AgentState(
            energy=50.0, memory_state=MemoryState(capacity=5),
        )
        snap = snapshot_agent(state, Position(x=0, y=0))
        assert snap.memory_timestep_range is None
        assert snap.memory_entry_count == 0

    def test_memory_timestep_range_populated(self):
        obs = _make_observation()
        entries = (
            MemoryEntry(timestep=2, observation=obs),
            MemoryEntry(timestep=5, observation=obs),
        )
        state = AgentState(
            energy=50.0,
            memory_state=MemoryState(entries=entries, capacity=5),
        )
        snap = snapshot_agent(state, Position(x=1, y=1))
        assert snap.memory_timestep_range == (2, 5)
        assert snap.memory_entry_count == 2

    def test_snapshot_agent_correct_values(self):
        state = AgentState(
            energy=42.0, memory_state=MemoryState(capacity=3),
        )
        snap = snapshot_agent(state, Position(x=2, y=3))
        assert snap.energy == 42.0
        assert snap.position == Position(x=2, y=3)
        assert snap.memory_entry_count == 0


class TestRegenSummary:
    def test_frozen(self):
        rs = RegenSummary(cells_updated=5, regen_rate=0.1)
        with pytest.raises(ValidationError):
            rs.cells_updated = 10

    def test_valid_construction(self):
        rs = RegenSummary(cells_updated=3, regen_rate=0.05)
        assert rs.cells_updated == 3
        assert rs.regen_rate == 0.05
