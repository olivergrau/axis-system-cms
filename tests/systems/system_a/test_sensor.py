"""WP-2.4 unit tests -- VonNeumannSensor."""

from __future__ import annotations

import pytest

from axis.sdk.interfaces import SensorInterface
from axis.sdk.position import Position
from axis.systems.construction_kit.observation.sensor import VonNeumannSensor
from axis.systems.construction_kit.observation.types import CellObservation, Observation
from axis.world.grid_2d.model import Cell, CellType, World


def _make_grid(width: int = 5, height: int = 5) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.EMPTY, resource_value=0.0)
         for _ in range(width)]
        for _ in range(height)
    ]


class TestSensor:
    """VonNeumannSensor unit tests."""

    def test_center_cell_observation(self) -> None:
        grid = _make_grid()
        grid[2][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.7)
        world = World(grid, Position(x=2, y=2))
        sensor = VonNeumannSensor()
        obs = sensor.observe(world, world.agent_position)
        assert obs.current.resource == 0.7
        assert obs.current.traversability == 1.0

    def test_obstacle_neighbor(self) -> None:
        grid = _make_grid()
        grid[1][2] = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        world = World(grid, Position(x=2, y=2))
        sensor = VonNeumannSensor()
        obs = sensor.observe(world, world.agent_position)
        assert obs.up.traversability == 0.0
        assert obs.up.resource == 0.0

    def test_resource_neighbor(self) -> None:
        grid = _make_grid()
        grid[2][3] = Cell(cell_type=CellType.RESOURCE, resource_value=0.6)
        world = World(grid, Position(x=2, y=2))
        sensor = VonNeumannSensor()
        obs = sensor.observe(world, world.agent_position)
        assert obs.right.resource == 0.6
        assert obs.right.traversability == 1.0

    def test_empty_neighbor(self) -> None:
        grid = _make_grid()
        world = World(grid, Position(x=2, y=2))
        sensor = VonNeumannSensor()
        obs = sensor.observe(world, world.agent_position)
        assert obs.down.traversability == 1.0
        assert obs.down.resource == 0.0

    def test_out_of_bounds_corner(self) -> None:
        grid = _make_grid()
        world = World(grid, Position(x=0, y=0))
        sensor = VonNeumannSensor()
        obs = sensor.observe(world, world.agent_position)
        assert obs.up.traversability == 0.0
        assert obs.up.resource == 0.0
        assert obs.left.traversability == 0.0
        assert obs.left.resource == 0.0

    def test_out_of_bounds_edge(self) -> None:
        grid = _make_grid()
        world = World(grid, Position(x=0, y=2))
        sensor = VonNeumannSensor()
        obs = sensor.observe(world, world.agent_position)
        assert obs.left.traversability == 0.0
        assert obs.left.resource == 0.0
        assert obs.right.traversability == 1.0

    def test_observation_dimension(self) -> None:
        grid = _make_grid()
        world = World(grid, Position(x=2, y=2))
        sensor = VonNeumannSensor()
        obs = sensor.observe(world, world.agent_position)
        assert len(obs.to_vector()) == 10
        assert obs.dimension == 10

    def test_observation_vector_values(self) -> None:
        grid = _make_grid()
        grid[2][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.5)
        world = World(grid, Position(x=2, y=2))
        sensor = VonNeumannSensor()
        obs = sensor.observe(world, world.agent_position)
        vec = obs.to_vector()
        assert vec[0] == obs.current.traversability
        assert vec[1] == obs.current.resource
        assert vec[2] == obs.up.traversability
        assert vec[3] == obs.up.resource
        assert vec[4] == obs.down.traversability
        assert vec[5] == obs.down.resource
        assert vec[6] == obs.left.traversability
        assert vec[7] == obs.left.resource
        assert vec[8] == obs.right.traversability
        assert vec[9] == obs.right.resource

    def test_sensor_interface_conformance(self) -> None:
        sensor = VonNeumannSensor()
        assert isinstance(sensor, SensorInterface)

    def test_pure_function(self) -> None:
        grid = _make_grid()
        grid[2][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.4)
        world = World(grid, Position(x=2, y=2))
        sensor = VonNeumannSensor()
        obs1 = sensor.observe(world, world.agent_position)
        obs2 = sensor.observe(world, world.agent_position)
        assert obs1 == obs2
