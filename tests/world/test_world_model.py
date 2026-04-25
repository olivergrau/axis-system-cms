"""WP-2.1 verification tests -- World model, factory, and WorldView conformance."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis.sdk.position import Position
from axis.sdk.snapshot import snapshot_world
from axis.sdk.world_types import BaseWorldConfig, CellView, WorldView
from axis.world.grid_2d.factory import create_world
from axis.world.grid_2d.model import (
    Cell,
    CellType,
    RegenerationMode,
    TopologyMode,
    World,
)


# ---------------------------------------------------------------------------
# CellType enum
# ---------------------------------------------------------------------------


class TestCellType:
    """CellType enum values match CellView.cell_type strings."""

    def test_empty_value(self) -> None:
        assert CellType.EMPTY.value == "empty"

    def test_resource_value(self) -> None:
        assert CellType.RESOURCE.value == "resource"

    def test_obstacle_value(self) -> None:
        assert CellType.OBSTACLE.value == "obstacle"

    def test_three_members(self) -> None:
        assert len(CellType) == 3


# ---------------------------------------------------------------------------
# RegenerationMode enum
# ---------------------------------------------------------------------------


class TestRegenerationMode:
    """RegenerationMode enum values."""

    def test_all_traversable(self) -> None:
        assert RegenerationMode.ALL_TRAVERSABLE.value == "all_traversable"

    def test_sparse(self) -> None:
        assert RegenerationMode.SPARSE_FIXED_RATIO.value == "sparse_fixed_ratio"

    def test_clustered(self) -> None:
        assert RegenerationMode.CLUSTERED.value == "clustered"


class TestTopologyMode:
    """TopologyMode enum values."""

    def test_bounded(self) -> None:
        assert TopologyMode.BOUNDED.value == "bounded"

    def test_toroidal(self) -> None:
        assert TopologyMode.TOROIDAL.value == "toroidal"


# ---------------------------------------------------------------------------
# Cell
# ---------------------------------------------------------------------------


class TestCell:
    """Cell construction, invariants, and immutability."""

    def test_empty_cell(self) -> None:
        cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        assert cell.cell_type == CellType.EMPTY
        assert cell.resource_value == 0.0

    def test_resource_cell(self) -> None:
        cell = Cell(cell_type=CellType.RESOURCE, resource_value=0.5)
        assert cell.cell_type == CellType.RESOURCE
        assert cell.resource_value == 0.5

    def test_obstacle_cell(self) -> None:
        cell = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        assert cell.cell_type == CellType.OBSTACLE
        assert cell.regen_eligible is False
        assert cell.cooldown_remaining == 0

    def test_resource_with_zero_value_raises(self) -> None:
        with pytest.raises(ValidationError, match="resource_value > 0"):
            Cell(cell_type=CellType.RESOURCE, resource_value=0.0)

    def test_empty_with_nonzero_value_raises(self) -> None:
        with pytest.raises(ValidationError, match="resource_value == 0"):
            Cell(cell_type=CellType.EMPTY, resource_value=0.5)

    def test_obstacle_with_nonzero_value_raises(self) -> None:
        with pytest.raises(ValidationError, match="resource_value == 0"):
            Cell(cell_type=CellType.OBSTACLE, resource_value=0.5)

    def test_traversable_empty(self) -> None:
        cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        assert cell.is_traversable is True

    def test_traversable_resource(self) -> None:
        cell = Cell(cell_type=CellType.RESOURCE, resource_value=0.5)
        assert cell.is_traversable is True

    def test_not_traversable_obstacle(self) -> None:
        cell = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        assert cell.is_traversable is False

    def test_frozen(self) -> None:
        cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        with pytest.raises(ValidationError):
            cell.cell_type = CellType.RESOURCE  # type: ignore[misc]

    def test_obstacle_forces_regen_eligible_false(self) -> None:
        cell = Cell(
            cell_type=CellType.OBSTACLE, resource_value=0.0, regen_eligible=True,
        )
        assert cell.regen_eligible is False

    def test_regen_eligible_default_true(self) -> None:
        cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        assert cell.regen_eligible is True

    def test_regen_eligible_explicit_false(self) -> None:
        cell = Cell(
            cell_type=CellType.EMPTY, resource_value=0.0, regen_eligible=False,
        )
        assert cell.regen_eligible is False

    def test_empty_cell_with_cooldown(self) -> None:
        cell = Cell(
            cell_type=CellType.EMPTY,
            resource_value=0.0,
            cooldown_remaining=3,
        )
        assert cell.cooldown_remaining == 3

    def test_resource_cell_with_cooldown_raises(self) -> None:
        with pytest.raises(ValidationError, match="cooldown_remaining == 0"):
            Cell(
                cell_type=CellType.RESOURCE,
                resource_value=0.5,
                cooldown_remaining=1,
            )


# ---------------------------------------------------------------------------
# World construction
# ---------------------------------------------------------------------------


def _make_empty_grid(
    width: int = 5,
    height: int = 5,
) -> list[list[Cell]]:
    """Create an all-empty grid."""
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    return [[empty for _ in range(width)] for _ in range(height)]


class TestWorldConstruction:
    """World construction and validation."""

    def test_basic_construction(self) -> None:
        grid = _make_empty_grid()
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        assert world.width == 5
        assert world.height == 5
        assert world.topology == "bounded"

    def test_agent_position(self) -> None:
        grid = _make_empty_grid()
        pos = Position(x=2, y=3)
        world = World(grid=grid, agent_position=pos)
        assert world.agent_position == pos

    def test_empty_grid_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            World(grid=[], agent_position=Position(x=0, y=0))

    def test_agent_out_of_bounds_raises(self) -> None:
        grid = _make_empty_grid(3, 3)
        with pytest.raises(ValueError, match="out of bounds"):
            World(grid=grid, agent_position=Position(x=5, y=0))

    def test_agent_on_obstacle_raises(self) -> None:
        grid = _make_empty_grid(3, 3)
        grid[1][1] = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        with pytest.raises(ValueError, match="non-traversable"):
            World(grid=grid, agent_position=Position(x=1, y=1))

    def test_non_uniform_rows_raises(self) -> None:
        empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        grid = [
            [empty, empty, empty],
            [empty, empty],  # shorter row
        ]
        with pytest.raises(ValueError, match="width"):
            World(grid=grid, agent_position=Position(x=0, y=0))

    def test_toroidal_canonicalizes_agent_position(self) -> None:
        grid = _make_empty_grid(3, 3)
        world = World(
            grid=grid,
            agent_position=Position(x=3, y=-1),
            topology="toroidal",
        )
        assert world.agent_position == Position(x=0, y=2)


# ---------------------------------------------------------------------------
# WorldView protocol conformance
# ---------------------------------------------------------------------------


class TestWorldViewConformance:
    """World satisfies the WorldView protocol."""

    def test_isinstance_world_view(self) -> None:
        grid = _make_empty_grid(3, 3)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        assert isinstance(world, WorldView)

    def test_get_cell_returns_cell_view(self) -> None:
        grid = _make_empty_grid(3, 3)
        grid[1][1] = Cell(cell_type=CellType.RESOURCE, resource_value=0.75)
        world = World(grid=grid, agent_position=Position(x=0, y=0))

        cell_view = world.get_cell(Position(x=1, y=1))
        assert isinstance(cell_view, CellView)
        assert cell_view.cell_type == "resource"
        assert cell_view.resource_value == 0.75

    def test_get_cell_empty(self) -> None:
        grid = _make_empty_grid(3, 3)
        world = World(grid=grid, agent_position=Position(x=0, y=0))

        cell_view = world.get_cell(Position(x=2, y=2))
        assert cell_view.cell_type == "empty"
        assert cell_view.resource_value == 0.0

    def test_get_cell_obstacle(self) -> None:
        grid = _make_empty_grid(3, 3)
        grid[2][2] = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        world = World(grid=grid, agent_position=Position(x=0, y=0))

        cell_view = world.get_cell(Position(x=2, y=2))
        assert cell_view.cell_type == "obstacle"
        assert cell_view.resource_value == 0.0

    def test_get_cell_out_of_bounds_raises(self) -> None:
        grid = _make_empty_grid(3, 3)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        with pytest.raises(ValueError, match="out of bounds"):
            world.get_cell(Position(x=5, y=0))

    def test_is_within_bounds_true(self) -> None:
        grid = _make_empty_grid(3, 3)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        assert world.is_within_bounds(Position(x=2, y=2)) is True

    def test_is_within_bounds_false(self) -> None:
        grid = _make_empty_grid(3, 3)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        assert world.is_within_bounds(Position(x=3, y=0)) is False
        assert world.is_within_bounds(Position(x=-1, y=0)) is False

    def test_is_traversable_empty(self) -> None:
        grid = _make_empty_grid(3, 3)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        assert world.is_traversable(Position(x=1, y=1)) is True

    def test_is_traversable_obstacle(self) -> None:
        grid = _make_empty_grid(3, 3)
        grid[1][1] = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        assert world.is_traversable(Position(x=1, y=1)) is False

    def test_is_traversable_out_of_bounds(self) -> None:
        grid = _make_empty_grid(3, 3)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        assert world.is_traversable(Position(x=10, y=10)) is False

    def test_width_height_properties(self) -> None:
        grid = _make_empty_grid(4, 7)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        assert world.width == 4
        assert world.height == 7

    def test_canonicalize_position_toroidal_wraps(self) -> None:
        grid = _make_empty_grid(3, 3)
        world = World(
            grid=grid,
            agent_position=Position(x=0, y=0),
            topology="toroidal",
        )
        assert world.canonicalize_position(Position(x=-1, y=3)) == Position(x=2, y=0)


# ---------------------------------------------------------------------------
# Internal mutation API
# ---------------------------------------------------------------------------


class TestWorldInternalAPI:
    """Internal mutation methods (framework-only)."""

    def test_set_agent_position(self) -> None:
        grid = _make_empty_grid(5, 5)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        world.agent_position = Position(x=3, y=3)
        assert world.agent_position == Position(x=3, y=3)

    def test_set_agent_position_wraps_in_toroidal_mode(self) -> None:
        grid = _make_empty_grid(5, 5)
        world = World(
            grid=grid,
            agent_position=Position(x=0, y=0),
            topology="toroidal",
        )
        world.agent_position = Position(x=-1, y=5)
        assert world.agent_position == Position(x=4, y=0)

    def test_set_agent_position_obstacle_raises(self) -> None:
        grid = _make_empty_grid(5, 5)
        grid[3][3] = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        with pytest.raises(ValueError, match="non-traversable"):
            world.agent_position = Position(x=3, y=3)

    def test_set_agent_position_out_of_bounds_raises(self) -> None:
        grid = _make_empty_grid(5, 5)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        with pytest.raises(ValueError, match="out of bounds"):
            world.agent_position = Position(x=10, y=10)

    def test_get_internal_cell_returns_cell(self) -> None:
        grid = _make_empty_grid(3, 3)
        grid[1][1] = Cell(
            cell_type=CellType.RESOURCE, resource_value=0.5, regen_eligible=False,
        )
        world = World(grid=grid, agent_position=Position(x=0, y=0))

        cell = world.get_internal_cell(Position(x=1, y=1))
        assert isinstance(cell, Cell)
        assert cell.cell_type == CellType.RESOURCE
        assert cell.regen_eligible is False

    def test_get_internal_cell_out_of_bounds_raises(self) -> None:
        grid = _make_empty_grid(3, 3)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        with pytest.raises(ValueError, match="out of bounds"):
            world.get_internal_cell(Position(x=5, y=5))

    def test_set_cell(self) -> None:
        grid = _make_empty_grid(3, 3)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        new_cell = Cell(cell_type=CellType.RESOURCE, resource_value=0.8)
        world.set_cell(Position(x=2, y=2), new_cell)
        retrieved = world.get_internal_cell(Position(x=2, y=2))
        assert retrieved.cell_type == CellType.RESOURCE
        assert retrieved.resource_value == 0.8

    def test_set_cell_out_of_bounds_raises(self) -> None:
        grid = _make_empty_grid(3, 3)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        new_cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        with pytest.raises(ValueError, match="out of bounds"):
            world.set_cell(Position(x=5, y=5), new_cell)

    def test_is_regen_eligible(self) -> None:
        grid = _make_empty_grid(3, 3)
        grid[1][1] = Cell(
            cell_type=CellType.EMPTY, resource_value=0.0, regen_eligible=False,
        )
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        assert world.is_regen_eligible(Position(x=0, y=0)) is True
        assert world.is_regen_eligible(Position(x=1, y=1)) is False


# ---------------------------------------------------------------------------
# create_world factory
# ---------------------------------------------------------------------------


class TestCreateWorld:
    """World factory function."""

    def test_creates_empty_world(self) -> None:
        config = BaseWorldConfig(grid_width=5, grid_height=5)
        world = create_world(config, Position(x=0, y=0))
        assert world.width == 5
        assert world.height == 5
        assert world.topology == "bounded"

    def test_all_cells_empty(self) -> None:
        config = BaseWorldConfig(grid_width=3, grid_height=3)
        world = create_world(config, Position(x=0, y=0))
        for y in range(3):
            for x in range(3):
                cell_view = world.get_cell(Position(x=x, y=y))
                assert cell_view.cell_type == "empty"

    def test_agent_at_specified_position(self) -> None:
        config = BaseWorldConfig(grid_width=5, grid_height=5)
        pos = Position(x=2, y=3)
        world = create_world(config, pos)
        assert world.agent_position == pos

    def test_topology_and_cooldown_config_applied(self) -> None:
        config = BaseWorldConfig(
            grid_width=5,
            grid_height=5,
            topology="toroidal",
            resource_regen_cooldown_steps=3,
        )
        world = create_world(config, Position(x=5, y=-1))
        assert world.topology == "toroidal"
        assert world.agent_position == Position(x=0, y=4)

    def test_with_obstacles(self) -> None:
        config = BaseWorldConfig(
            grid_width=10, grid_height=10, obstacle_density=0.2,
        )
        world = create_world(config, Position(x=0, y=0), seed=42)
        obstacle_count = sum(
            1
            for y in range(10)
            for x in range(10)
            if world.get_cell(Position(x=x, y=y)).cell_type == "obstacle"
        )
        assert obstacle_count > 0

    def test_agent_position_never_obstacle(self) -> None:
        config = BaseWorldConfig(
            grid_width=10, grid_height=10, obstacle_density=0.5,
        )
        pos = Position(x=5, y=5)
        world = create_world(config, pos, seed=42)
        assert world.get_cell(pos).cell_type != "obstacle"

    def test_provided_grid_validated(self) -> None:
        config = BaseWorldConfig(grid_width=3, grid_height=3)
        empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        # Wrong height
        wrong_grid = [[empty] * 3, [empty] * 3]
        with pytest.raises(ValueError, match="grid_height"):
            create_world(config, Position(x=0, y=0), grid=wrong_grid)

    def test_provided_grid_wrong_width(self) -> None:
        config = BaseWorldConfig(grid_width=3, grid_height=2)
        empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
        grid = [[empty] * 3, [empty] * 2]
        with pytest.raises(ValueError, match="grid_width"):
            create_world(config, Position(x=0, y=0), grid=grid)

    def test_sparse_regeneration(self) -> None:
        config = BaseWorldConfig(
            grid_width=5, grid_height=5,
            regeneration_mode="sparse_fixed_ratio",
            regen_eligible_ratio=0.5,
        )
        world = create_world(
            config,
            Position(x=0, y=0),
            seed=42,
        )
        eligible_count = sum(
            1
            for y in range(5)
            for x in range(5)
            if world.is_regen_eligible(Position(x=x, y=y))
        )
        total = 25
        expected = round(0.5 * total)
        assert eligible_count == expected

    def test_sparse_without_ratio_raises(self) -> None:
        config = BaseWorldConfig(
            grid_width=5, grid_height=5,
            regeneration_mode="sparse_fixed_ratio",
        )
        with pytest.raises(ValueError, match="regen_eligible_ratio"):
            create_world(
                config,
                Position(x=0, y=0),
            )

    def test_clustered_regeneration(self) -> None:
        config = BaseWorldConfig(
            grid_width=9, grid_height=9,
            regeneration_mode="clustered",
            regen_eligible_ratio=0.25,
            num_clusters=3,
        )
        world = create_world(
            config,
            Position(x=0, y=0),
            seed=42,
        )
        eligible_count = sum(
            1
            for y in range(9)
            for x in range(9)
            if world.is_regen_eligible(Position(x=x, y=y))
        )
        assert eligible_count == round(0.25 * 81)

    def test_clustered_without_ratio_raises(self) -> None:
        config = BaseWorldConfig(
            grid_width=5, grid_height=5,
            regeneration_mode="clustered",
            num_clusters=2,
        )
        with pytest.raises(ValueError, match="regen_eligible_ratio"):
            create_world(
                config,
                Position(x=0, y=0),
            )

    def test_clustered_without_num_clusters_raises(self) -> None:
        config = BaseWorldConfig(
            grid_width=5, grid_height=5,
            regeneration_mode="clustered",
            regen_eligible_ratio=0.4,
        )
        with pytest.raises(ValueError, match="num_clusters"):
            create_world(
                config,
                Position(x=0, y=0),
            )

    def test_clustered_deterministic(self) -> None:
        config = BaseWorldConfig(
            grid_width=9, grid_height=9,
            regeneration_mode="clustered",
            regen_eligible_ratio=0.25,
            num_clusters=3,
        )
        w1 = create_world(config, Position(x=0, y=0), seed=42)
        w2 = create_world(config, Position(x=0, y=0), seed=42)

        for y in range(9):
            for x in range(9):
                p = Position(x=x, y=y)
                assert w1.is_regen_eligible(p) == w2.is_regen_eligible(p)

    def test_deterministic_obstacles(self) -> None:
        config = BaseWorldConfig(
            grid_width=10, grid_height=10, obstacle_density=0.2,
        )
        pos = Position(x=0, y=0)
        w1 = create_world(config, pos, seed=42)
        w2 = create_world(config, pos, seed=42)

        for y in range(10):
            for x in range(10):
                p = Position(x=x, y=y)
                assert w1.get_cell(p).cell_type == w2.get_cell(p).cell_type

    def test_different_seeds_different_layouts(self) -> None:
        config = BaseWorldConfig(
            grid_width=10, grid_height=10, obstacle_density=0.2,
        )
        pos = Position(x=0, y=0)
        w1 = create_world(config, pos, seed=42)
        w2 = create_world(config, pos, seed=99)

        any_diff = any(
            w1.get_cell(Position(x=x, y=y)).cell_type
            != w2.get_cell(Position(x=x, y=y)).cell_type
            for y in range(10)
            for x in range(10)
        )
        assert any_diff


# ---------------------------------------------------------------------------
# snapshot_world compatibility
# ---------------------------------------------------------------------------


class TestSnapshotCompatibility:
    """World works with snapshot_world() from axis.sdk.snapshot."""

    def test_snapshot_from_world(self) -> None:
        grid = _make_empty_grid(3, 3)
        grid[1][1] = Cell(cell_type=CellType.RESOURCE, resource_value=0.6)
        world = World(grid=grid, agent_position=Position(x=0, y=0))

        snap = snapshot_world(world, world.width, world.height)
        assert snap.width == 3
        assert snap.height == 3
        assert snap.agent_position == Position(x=0, y=0)

    def test_snapshot_cell_types_match(self) -> None:
        grid = _make_empty_grid(3, 3)
        grid[0][1] = Cell(cell_type=CellType.RESOURCE, resource_value=0.5)
        grid[2][2] = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        world = World(grid=grid, agent_position=Position(x=0, y=0))

        snap = snapshot_world(world, world.width, world.height)
        assert snap.grid[0][1].cell_type == "resource"
        assert snap.grid[0][1].resource_value == 0.5
        assert snap.grid[2][2].cell_type == "obstacle"
        assert snap.grid[0][0].cell_type == "empty"

    def test_snapshot_preserves_resource_value(self) -> None:
        grid = _make_empty_grid(3, 3)
        grid[1][2] = Cell(cell_type=CellType.RESOURCE, resource_value=0.99)
        world = World(grid=grid, agent_position=Position(x=0, y=0))

        snap = snapshot_world(world, world.width, world.height)
        assert snap.grid[1][2].resource_value == 0.99


# ---------------------------------------------------------------------------
# Import verification
# ---------------------------------------------------------------------------


class TestImports:
    """Import paths work correctly."""

    def test_import_from_axis_world(self) -> None:
        from axis.world import Cell, CellType, RegenerationMode, World, create_world  # noqa: F401

    def test_import_from_model(self) -> None:
        from axis.world.grid_2d.model import Cell, CellType, RegenerationMode, World  # noqa: F401

    def test_import_from_factory(self) -> None:
        from axis.world.grid_2d.factory import create_world  # noqa: F401

    def test_world_view_protocol_satisfied(self) -> None:
        """Explicitly verify the WorldView protocol is satisfied."""
        from axis.sdk.world_types import WorldView

        grid = _make_empty_grid(2, 2)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        assert isinstance(world, WorldView)


# ---------------------------------------------------------------------------
# world_metadata (WP-V.0.2)
# ---------------------------------------------------------------------------


class TestWorldMetadata:
    """Tests for grid_2d World.world_metadata()."""

    def test_world_metadata_returns_empty_dict(self) -> None:
        grid = _make_empty_grid(3, 3)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        assert world.world_metadata() == {}

    def test_world_metadata_stable_across_ticks(self) -> None:
        grid = _make_empty_grid(3, 3)
        world = World(grid=grid, agent_position=Position(x=0, y=0))
        m1 = world.world_metadata()
        world.tick()
        m2 = world.world_metadata()
        assert m1 == m2 == {}
