"""Tests for Cell, World, and create_world."""

import pytest
from pydantic import ValidationError

from axis_system_a import (
    Cell,
    CellType,
    Position,
    RegenerationMode,
    World,
    WorldConfig,
    create_world,
)
from tests.fixtures.world_fixtures import empty_cell, obstacle_cell, resource_cell


# --- Cell Tests ---


class TestCellCreation:
    def test_empty_cell(self):
        cell = empty_cell()
        assert cell.cell_type == CellType.EMPTY
        assert cell.resource_value == 0.0

    def test_resource_cell(self):
        cell = resource_cell()
        assert cell.cell_type == CellType.RESOURCE
        assert cell.resource_value == 0.7

    def test_obstacle_cell(self):
        cell = obstacle_cell()
        assert cell.cell_type == CellType.OBSTACLE
        assert cell.resource_value == 0.0

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
    def test_frozen(self):
        cell = empty_cell()
        with pytest.raises(ValidationError):
            cell.resource_value = 0.5

    def test_is_traversable_empty(self):
        assert empty_cell().is_traversable is True

    def test_is_traversable_resource(self):
        assert resource_cell().is_traversable is True

    def test_is_traversable_obstacle(self):
        assert obstacle_cell().is_traversable is False

    def test_serialization(self):
        cell = resource_cell()
        dump = cell.model_dump()
        assert dump == {
            "cell_type": "resource", "resource_value": 0.7,
            "regen_eligible": True,
        }
        reconstructed = Cell(**dump)
        assert reconstructed == cell


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
    def test_get_cell(self, small_world: World):
        cell = small_world.get_cell(Position(x=1, y=0))
        assert cell == resource_cell()

    def test_get_cell_all_corners(self, small_world: World):
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
        assert small_world.is_traversable(Position(x=2, y=1)) is False

    def test_not_traversable_out_of_bounds(self, small_world: World):
        assert small_world.is_traversable(Position(x=5, y=5)) is False


class TestWorldConstructorValidation:
    def test_agent_out_of_bounds(self):
        e = empty_cell()
        grid = [[e, e], [e, e]]
        with pytest.raises(ValueError, match="out of bounds"):
            World(grid=grid, agent_position=Position(x=5, y=0))

    def test_agent_on_obstacle(self):
        e = empty_cell()
        o = obstacle_cell()
        grid = [[o, e], [e, e]]
        with pytest.raises(ValueError, match="non-traversable"):
            World(grid=grid, agent_position=Position(x=0, y=0))

    def test_empty_grid(self):
        with pytest.raises(ValueError):
            World(grid=[], agent_position=Position(x=0, y=0))

    def test_ragged_grid(self):
        e = empty_cell()
        grid = [
            [e, e, e],
            [e, e],
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

    def test_with_explicit_grid(self, small_world_config: WorldConfig):
        e = empty_cell()
        r = resource_cell()
        grid = [
            [e, r, e],
            [e, e, e],
            [e, e, e],
        ]
        world = create_world(
            small_world_config,
            agent_position=Position(x=1, y=0),
            grid=grid,
        )
        assert world.get_cell(
            Position(x=1, y=0)).cell_type == CellType.RESOURCE

    def test_dimension_mismatch_height(self):
        e = empty_cell()
        config = WorldConfig(grid_width=2, grid_height=3)
        grid = [[e, e], [e, e]]
        with pytest.raises(ValueError, match="height"):
            create_world(config, Position(x=0, y=0), grid=grid)

    def test_dimension_mismatch_width(self):
        e = empty_cell()
        config = WorldConfig(grid_width=3, grid_height=2)
        grid = [[e, e], [e, e]]
        with pytest.raises(ValueError, match="width"):
            create_world(config, Position(x=0, y=0), grid=grid)


# --- WP17: Cell Eligibility Tests ---


class TestCellRegenEligibility:
    def test_default_eligible(self):
        cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        assert cell.regen_eligible is True

    def test_explicit_eligible_false(self):
        cell = Cell(cell_type=CellType.EMPTY,
                    resource_value=0.0, regen_eligible=False)
        assert cell.regen_eligible is False

    def test_resource_cell_default_eligible(self):
        cell = Cell(cell_type=CellType.RESOURCE, resource_value=0.5)
        assert cell.regen_eligible is True

    def test_resource_cell_ineligible(self):
        cell = Cell(cell_type=CellType.RESOURCE,
                    resource_value=0.5, regen_eligible=False)
        assert cell.regen_eligible is False

    def test_obstacle_auto_corrected_to_ineligible(self):
        cell = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        assert cell.regen_eligible is False

    def test_obstacle_explicit_false(self):
        cell = Cell(cell_type=CellType.OBSTACLE,
                    resource_value=0.0, regen_eligible=False)
        assert cell.regen_eligible is False

    def test_serialization_preserves_eligibility(self):
        cell = Cell(cell_type=CellType.EMPTY,
                    resource_value=0.0, regen_eligible=False)
        dump = cell.model_dump()
        assert dump["regen_eligible"] is False
        reconstructed = Cell(**dump)
        assert reconstructed == cell


# --- WP17: World is_regen_eligible Tests ---


class TestWorldRegenEligibility:
    def test_eligible_cell(self):
        cell = Cell(cell_type=CellType.EMPTY,
                    resource_value=0.0, regen_eligible=True)
        world = World(grid=[[cell]], agent_position=Position(x=0, y=0))
        assert world.is_regen_eligible(Position(x=0, y=0)) is True

    def test_ineligible_cell(self):
        cell = Cell(cell_type=CellType.EMPTY,
                    resource_value=0.0, regen_eligible=False)
        world = World(grid=[[cell]], agent_position=Position(x=0, y=0))
        assert world.is_regen_eligible(Position(x=0, y=0)) is False


# --- Obstacle Placement Tests ---


class TestObstaclePlacement:
    def _obstacle_config(
        self, width: int = 10, height: int = 10, density: float = 0.2,
    ):
        return WorldConfig(
            grid_width=width, grid_height=height,
            obstacle_density=density,
        )

    def test_correct_obstacle_count(self):
        config = self._obstacle_config(width=10, height=10, density=0.2)
        world = create_world(config, Position(x=0, y=0), seed=42)
        obstacle_count = sum(
            1 for y in range(10) for x in range(10)
            if not world.get_cell(Position(x=x, y=y)).is_traversable
        )
        # 99 candidates (100 - agent), 0.2 * 99 = round(19.8) = 20
        assert obstacle_count == round(0.2 * 99)

    def test_agent_position_never_obstacle(self):
        config = self._obstacle_config(density=0.5)
        for seed in range(10):
            world = create_world(config, Position(x=0, y=0), seed=seed)
            assert world.get_cell(Position(x=0, y=0)).is_traversable

    def test_zero_density_no_obstacles(self):
        config = self._obstacle_config(density=0.0)
        world = create_world(config, Position(x=0, y=0), seed=42)
        for y in range(10):
            for x in range(10):
                assert world.get_cell(Position(x=x, y=y)).is_traversable

    def test_same_seed_same_layout(self):
        config = self._obstacle_config(density=0.3)
        w1 = create_world(config, Position(x=0, y=0), seed=42)
        w2 = create_world(config, Position(x=0, y=0), seed=42)
        for y in range(10):
            for x in range(10):
                pos = Position(x=x, y=y)
                assert w1.get_cell(pos).cell_type == w2.get_cell(pos).cell_type

    def test_different_seed_may_differ(self):
        config = self._obstacle_config(density=0.3)
        w1 = create_world(config, Position(x=0, y=0), seed=1)
        w2 = create_world(config, Position(x=0, y=0), seed=2)
        any_different = any(
            w1.get_cell(Position(x=x, y=y)).cell_type
            != w2.get_cell(Position(x=x, y=y)).cell_type
            for y in range(10)
            for x in range(10)
        )
        assert any_different

    def test_obstacles_are_not_traversable(self):
        config = self._obstacle_config(density=0.3)
        world = create_world(config, Position(x=0, y=0), seed=42)
        for y in range(10):
            for x in range(10):
                cell = world.get_cell(Position(x=x, y=y))
                if cell.cell_type == CellType.OBSTACLE:
                    assert not cell.is_traversable

    def test_obstacles_placed_before_sparse_eligibility(self):
        config = WorldConfig(
            grid_width=10, grid_height=10,
            obstacle_density=0.2,
            regeneration_mode="sparse_fixed_ratio",
            regen_eligible_ratio=0.5,
        )
        world = create_world(config, Position(x=0, y=0), seed=42)
        for y in range(10):
            for x in range(10):
                cell = world.get_cell(Position(x=x, y=y))
                if cell.cell_type == CellType.OBSTACLE:
                    assert not cell.regen_eligible


# --- WP17: Sparse World Initialization Tests ---


class TestSparseWorldInit:
    def _sparse_config(self, width: int = 5, height: int = 5, ratio: float = 0.17):
        return WorldConfig(
            grid_width=width, grid_height=height,
            regeneration_mode="sparse_fixed_ratio",
            regen_eligible_ratio=ratio,
        )

    def test_correct_eligible_count(self):
        config = self._sparse_config(10, 10, 0.17)
        world = create_world(config, Position(x=0, y=0), seed=42)
        eligible = sum(
            1
            for y in range(world.height)
            for x in range(world.width)
            if world.is_regen_eligible(Position(x=x, y=y))
        )
        expected = round(0.17 * 100)  # 17
        assert eligible == expected

    def test_obstacle_cells_never_eligible(self):
        config = self._sparse_config(5, 5, 0.5)
        obstacle = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        grid = [[empty] * 5 for _ in range(5)]
        grid[0][0] = obstacle
        grid[2][2] = obstacle
        world = create_world(config, Position(x=1, y=0), grid=grid, seed=42)
        assert world.is_regen_eligible(Position(x=0, y=0)) is False
        assert world.is_regen_eligible(Position(x=2, y=2)) is False

    def test_same_seed_same_layout(self):
        config = self._sparse_config(10, 10, 0.17)
        world1 = create_world(config, Position(x=0, y=0), seed=42)
        world2 = create_world(config, Position(x=0, y=0), seed=42)
        for y in range(10):
            for x in range(10):
                pos = Position(x=x, y=y)
                assert world1.is_regen_eligible(
                    pos) == world2.is_regen_eligible(pos)

    def test_different_seed_may_differ(self):
        config = self._sparse_config(10, 10, 0.17)
        world1 = create_world(config, Position(x=0, y=0), seed=1)
        world2 = create_world(config, Position(x=0, y=0), seed=999)
        layouts = []
        for w in [world1, world2]:
            layout = tuple(
                w.is_regen_eligible(Position(x=x, y=y))
                for y in range(10) for x in range(10)
            )
            layouts.append(layout)
        assert layouts[0] != layouts[1]

    def test_all_traversable_mode_all_eligible(self):
        config = WorldConfig(grid_width=5, grid_height=5)
        world = create_world(config, Position(x=0, y=0), seed=42)
        for y in range(5):
            for x in range(5):
                assert world.is_regen_eligible(Position(x=x, y=y)) is True

    def test_ratio_one_means_all_eligible(self):
        config = self._sparse_config(5, 5, 1.0)
        world = create_world(config, Position(x=0, y=0), seed=42)
        eligible = sum(
            1
            for y in range(5) for x in range(5)
            if world.is_regen_eligible(Position(x=x, y=y))
        )
        assert eligible == 25
