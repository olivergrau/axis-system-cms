"""Tests for Cell, World, and create_world."""

import pytest
from pydantic import ValidationError

from axis_system_a import (
    Cell,
    CellType,
    Position,
    World,
    WorldConfig,
    create_world,
)


# --- Cell Tests ---


class TestCellCreation:
    def test_empty_cell(self, empty_cell: Cell):
        assert empty_cell.cell_type == CellType.EMPTY
        assert empty_cell.resource_value == 0.0

    def test_resource_cell(self, resource_cell: Cell):
        assert resource_cell.cell_type == CellType.RESOURCE
        assert resource_cell.resource_value == 0.7

    def test_obstacle_cell(self, obstacle_cell: Cell):
        assert obstacle_cell.cell_type == CellType.OBSTACLE
        assert obstacle_cell.resource_value == 0.0

    def test_resource_cell_max_value(self):
        cell = Cell(cell_type=CellType.RESOURCE, resource_value=1.0)
        assert cell.resource_value == 1.0

    def test_resource_cell_minimal_value(self):
        cell = Cell(cell_type=CellType.RESOURCE, resource_value=0.01)
        assert cell.resource_value == 0.01


class TestCellInvariants:
    def test_obstacle_with_resource_invalid(self):
        with pytest.raises(ValidationError):
            Cell(cell_type=CellType.OBSTACLE, resource_value=0.5)

    def test_resource_with_zero_value_invalid(self):
        with pytest.raises(ValidationError):
            Cell(cell_type=CellType.RESOURCE, resource_value=0.0)

    def test_empty_with_resource_invalid(self):
        with pytest.raises(ValidationError):
            Cell(cell_type=CellType.EMPTY, resource_value=0.5)

    def test_resource_value_above_one_invalid(self):
        with pytest.raises(ValidationError):
            Cell(cell_type=CellType.RESOURCE, resource_value=1.1)

    def test_resource_value_negative_invalid(self):
        with pytest.raises(ValidationError):
            Cell(cell_type=CellType.RESOURCE, resource_value=-0.1)


class TestCellProperties:
    def test_frozen(self, empty_cell: Cell):
        with pytest.raises(ValidationError):
            empty_cell.resource_value = 0.5

    def test_is_traversable_empty(self, empty_cell: Cell):
        assert empty_cell.is_traversable is True

    def test_is_traversable_resource(self, resource_cell: Cell):
        assert resource_cell.is_traversable is True

    def test_is_traversable_obstacle(self, obstacle_cell: Cell):
        assert obstacle_cell.is_traversable is False

    def test_serialization(self, resource_cell: Cell):
        dump = resource_cell.model_dump()
        assert dump == {"cell_type": "resource", "resource_value": 0.7}
        reconstructed = Cell(**dump)
        assert reconstructed == resource_cell


# --- World Tests ---


class TestWorldCreation:
    def test_valid_creation(self, small_world: World):
        assert small_world is not None

    def test_width_and_height(self, small_world: World):
        assert small_world.width == 3
        assert small_world.height == 3

    def test_agent_position(self, small_world: World):
        assert small_world.agent_position == Position(x=1, y=1)


class TestWorldAccess:
    def test_get_cell(self, small_world: World, resource_cell: Cell):
        # Row 0, col 1 is RESOURCE
        cell = small_world.get_cell(Position(x=1, y=0))
        assert cell == resource_cell

    def test_get_cell_all_corners(self, small_world: World):
        # (0,0) = EMPTY, (2,0) = EMPTY, (0,2) = RESOURCE, (2,2) = EMPTY
        assert small_world.get_cell(
            Position(x=0, y=0)).cell_type == CellType.EMPTY
        assert small_world.get_cell(
            Position(x=2, y=0)).cell_type == CellType.EMPTY
        assert small_world.get_cell(
            Position(x=0, y=2)).cell_type == CellType.RESOURCE
        assert small_world.get_cell(
            Position(x=2, y=2)).cell_type == CellType.EMPTY

    def test_get_cell_out_of_bounds(self, small_world: World):
        with pytest.raises(ValueError):
            small_world.get_cell(Position(x=3, y=0))

    def test_set_cell(self, small_world: World):
        pos = Position(x=0, y=0)
        new_cell = Cell(cell_type=CellType.RESOURCE, resource_value=0.9)
        small_world.set_cell(pos, new_cell)
        assert small_world.get_cell(pos) == new_cell

    def test_set_cell_out_of_bounds(self, small_world: World):
        new_cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        with pytest.raises(ValueError):
            small_world.set_cell(Position(x=-1, y=0), new_cell)


class TestWorldBounds:
    def test_is_within_bounds_valid(self, small_world: World):
        assert small_world.is_within_bounds(Position(x=0, y=0)) is True
        assert small_world.is_within_bounds(Position(x=2, y=2)) is True

    def test_is_within_bounds_negative(self, small_world: World):
        assert small_world.is_within_bounds(Position(x=-1, y=0)) is False

    def test_is_within_bounds_overflow(self, small_world: World):
        assert small_world.is_within_bounds(Position(x=3, y=0)) is False
        assert small_world.is_within_bounds(Position(x=0, y=3)) is False


class TestWorldTraversability:
    def test_traversable_empty(self, small_world: World):
        assert small_world.is_traversable(Position(x=0, y=0)) is True

    def test_traversable_resource(self, small_world: World):
        assert small_world.is_traversable(Position(x=1, y=0)) is True

    def test_not_traversable_obstacle(self, small_world: World):
        # (2, 1) is OBSTACLE
        assert small_world.is_traversable(Position(x=2, y=1)) is False

    def test_not_traversable_out_of_bounds(self, small_world: World):
        assert small_world.is_traversable(Position(x=5, y=5)) is False


class TestWorldConstructorValidation:
    def test_agent_out_of_bounds(self, empty_cell: Cell):
        grid = [[empty_cell, empty_cell], [empty_cell, empty_cell]]
        with pytest.raises(ValueError, match="out of bounds"):
            World(grid=grid, agent_position=Position(x=5, y=0))

    def test_agent_on_obstacle(self, empty_cell: Cell, obstacle_cell: Cell):
        grid = [[obstacle_cell, empty_cell], [empty_cell, empty_cell]]
        with pytest.raises(ValueError, match="non-traversable"):
            World(grid=grid, agent_position=Position(x=0, y=0))

    def test_empty_grid(self):
        with pytest.raises(ValueError):
            World(grid=[], agent_position=Position(x=0, y=0))

    def test_ragged_grid(self, empty_cell: Cell):
        grid = [
            [empty_cell, empty_cell, empty_cell],
            [empty_cell, empty_cell],
        ]
        with pytest.raises(ValueError, match="width"):
            World(grid=grid, agent_position=Position(x=0, y=0))


class TestWorldAgentPositionSetter:
    def test_valid_update(self, small_world: World):
        small_world.agent_position = Position(x=0, y=0)
        assert small_world.agent_position == Position(x=0, y=0)

    def test_out_of_bounds(self, small_world: World):
        with pytest.raises(ValueError, match="out of bounds"):
            small_world.agent_position = Position(x=10, y=10)

    def test_on_obstacle(self, small_world: World):
        # (2, 1) is OBSTACLE
        with pytest.raises(ValueError, match="non-traversable"):
            small_world.agent_position = Position(x=2, y=1)


# --- create_world Tests ---


class TestCreateWorld:
    def test_default_empty_grid(self, small_world_config: WorldConfig):
        world = create_world(
            small_world_config, agent_position=Position(x=0, y=0)
        )
        assert world.width == 3
        assert world.height == 3
        for y in range(3):
            for x in range(3):
                cell = world.get_cell(Position(x=x, y=y))
                assert cell.cell_type == CellType.EMPTY
                assert cell.resource_value == 0.0

    def test_with_explicit_grid(
        self,
        small_world_config: WorldConfig,
        empty_cell: Cell,
        resource_cell: Cell,
    ):
        grid = [
            [empty_cell, resource_cell, empty_cell],
            [empty_cell, empty_cell, empty_cell],
            [empty_cell, empty_cell, empty_cell],
        ]
        world = create_world(
            small_world_config,
            agent_position=Position(x=1, y=0),
            grid=grid,
        )
        assert world.get_cell(
            Position(x=1, y=0)).cell_type == CellType.RESOURCE

    def test_dimension_mismatch_height(self, empty_cell: Cell):
        config = WorldConfig(grid_width=2, grid_height=3)
        grid = [[empty_cell, empty_cell], [empty_cell, empty_cell]]
        with pytest.raises(ValueError, match="height"):
            create_world(config, Position(x=0, y=0), grid=grid)

    def test_dimension_mismatch_width(self, empty_cell: Cell):
        config = WorldConfig(grid_width=3, grid_height=2)
        grid = [[empty_cell, empty_cell], [empty_cell, empty_cell]]
        with pytest.raises(ValueError, match="width"):
            create_world(config, Position(x=0, y=0), grid=grid)
