"""WP-3 unit tests -- inherited components (sensor, observation buffer, actions)."""

from __future__ import annotations

import pytest

from axis.sdk.position import Position
from axis.sdk.world_types import ActionOutcome
from axis.systems.system_a.sensor import SystemASensor
from axis.systems.system_a.types import (
    CellObservation,
    ObservationBuffer,
    Observation,
)
from axis.systems.system_aw.actions import handle_consume
from axis.systems.system_aw.observation_buffer import update_observation_buffer
from axis.systems.system_aw.sensor import SystemAWSensor
from axis.systems.system_aw.types import AgentStateAW, WorldModelState
from axis.world.grid_2d.model import Cell, CellType, World


def _make_grid(width: int = 5, height: int = 5) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.EMPTY, resource_value=0.0)
         for _ in range(width)]
        for _ in range(height)
    ]


def _make_observation() -> Observation:
    cell = CellObservation(traversability=1.0, resource=0.0)
    return Observation(current=cell, up=cell, down=cell, left=cell, right=cell)


class TestSensor:
    """SystemAWSensor tests in System A+W context."""

    def test_sensor_produces_observation(self) -> None:
        grid = _make_grid()
        grid[2][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.7)
        world = World(grid, Position(x=2, y=2))
        sensor = SystemAWSensor()
        obs = sensor.observe(world, world.agent_position)
        assert isinstance(obs, Observation)
        assert obs.current.resource == 0.7
        assert len(obs.to_vector()) == 10

    def test_sensor_out_of_bounds(self) -> None:
        grid = _make_grid()
        world = World(grid, Position(x=0, y=0))
        sensor = SystemAWSensor()
        obs = sensor.observe(world, world.agent_position)
        assert obs.up.traversability == 0.0
        assert obs.left.traversability == 0.0

    def test_sensor_is_system_a_sensor(self) -> None:
        assert SystemAWSensor is SystemASensor


class TestObservationBuffer:
    """update_observation_buffer tests in System A+W context."""

    def test_buffer_update_appends(self) -> None:
        mem = ObservationBuffer(entries=(), capacity=5)
        new_buffer = update_observation_buffer(mem, _make_observation(), timestep=0)
        assert len(new_buffer.entries) == 1
        assert new_buffer.entries[0].timestep == 0

    def test_buffer_update_fifo_overflow(self) -> None:
        mem = ObservationBuffer(entries=(), capacity=2)
        for t in range(3):
            mem = update_observation_buffer(mem, _make_observation(), timestep=t)
        assert len(mem.entries) == 2
        assert mem.entries[0].timestep == 1
        assert mem.entries[1].timestep == 2

    def test_buffer_update_with_agent_state_aw(self) -> None:
        state = AgentStateAW(
            energy=50.0,
            observation_buffer=ObservationBuffer(entries=(), capacity=5),
            world_model=WorldModelState(),
        )
        new_buffer = update_observation_buffer(
            state.observation_buffer, _make_observation(), timestep=0,
        )
        assert len(new_buffer.entries) == 1
        assert len(state.observation_buffer.entries) == 0  # original unchanged


class TestConsumeAction:
    """handle_consume tests in System A+W context."""

    def test_consume_handler_extracts_resource(self) -> None:
        grid = _make_grid()
        grid[2][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.8)
        world = World(grid, Position(x=2, y=2))
        outcome = handle_consume(world, context={"max_consume": 1.0})
        assert isinstance(outcome, ActionOutcome)
        assert outcome.data["consumed"] is True
        assert outcome.data["resource_consumed"] == 0.8

    def test_consume_handler_respects_max(self) -> None:
        grid = _make_grid()
        grid[2][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.8)
        world = World(grid, Position(x=2, y=2))
        outcome = handle_consume(world, context={"max_consume": 0.3})
        assert outcome.data["resource_consumed"] == pytest.approx(0.3)

    def test_consume_handler_empty_cell(self) -> None:
        grid = _make_grid()
        world = World(grid, Position(x=2, y=2))
        outcome = handle_consume(world, context={"max_consume": 1.0})
        assert outcome.data["consumed"] is False
        assert outcome.data["resource_consumed"] == 0.0


class TestImportAccessibility:
    """Verify re-exports are importable."""

    def test_imports_accessible(self) -> None:
        from axis.systems.system_aw.sensor import SystemAWSensor  # noqa: F401

    def test_imports_accessible_observation_buffer(self) -> None:
        from axis.systems.system_aw.observation_buffer import update_observation_buffer  # noqa: F401

    def test_imports_accessible_actions(self) -> None:
        from axis.systems.system_aw.actions import handle_consume  # noqa: F401
