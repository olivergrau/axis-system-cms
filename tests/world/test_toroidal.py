"""Toroidal world tests -- construction, wrapping, protocol, factory, integration."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.world_types import (
    BaseWorldConfig,
    CellView,
    MutableWorldProtocol,
    WorldView,
)
from axis.world.grid_2d.model import Cell, CellType
from axis.world.registry import create_world_from_config, registered_world_types
from axis.world.toroidal import (
    ToroidalWorld,
    ToroidalWorldConfig,
    create_toroidal_world,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_empty_grid(w: int, h: int) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.EMPTY, resource_value=0.0)
         for _ in range(w)]
        for _ in range(h)
    ]


def _make_config(**overrides: object) -> BaseWorldConfig:
    defaults = {
        "world_type": "toroidal",
        "grid_width": 5,
        "grid_height": 5,
    }
    defaults.update(overrides)
    return BaseWorldConfig(**defaults)


def _make_world(
    width: int = 5,
    height: int = 5,
    agent: Position | None = None,
    seed: int = 42,
    **config_overrides: object,
) -> ToroidalWorld:
    if agent is None:
        agent = Position(x=width // 2, y=height // 2)
    config = _make_config(
        grid_width=width, grid_height=height, **config_overrides)
    return create_toroidal_world(config, agent, seed=seed)


# ---------------------------------------------------------------------------
# 1. Config validation
# ---------------------------------------------------------------------------


class TestToroidalWorldConfig:
    """Config model validation."""

    def test_defaults(self) -> None:
        c = ToroidalWorldConfig(grid_width=5, grid_height=5)
        assert c.obstacle_density == 0.0
        assert c.resource_regen_rate == 0.0

    def test_frozen(self) -> None:
        c = ToroidalWorldConfig(grid_width=5, grid_height=5)
        with pytest.raises(ValidationError):
            c.grid_width = 10  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 2. World construction
# ---------------------------------------------------------------------------


class TestWorldConstruction:
    """ToroidalWorld construction and basic properties."""

    def test_basic_construction(self) -> None:
        world = _make_world()
        assert world.width == 5
        assert world.height == 5

    def test_agent_position(self) -> None:
        agent = Position(x=1, y=1)
        world = _make_world(agent=agent)
        assert world.agent_position == agent

    def test_empty_grid_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            ToroidalWorld(grid=[], agent_position=Position(x=0, y=0))

    def test_agent_on_obstacle_raises(self) -> None:
        grid = _make_empty_grid(3, 3)
        grid[1][1] = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        with pytest.raises(ValueError, match="non-traversable"):
            ToroidalWorld(grid=grid, agent_position=Position(x=1, y=1))


# ---------------------------------------------------------------------------
# 3. Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    """ToroidalWorld satisfies SDK protocols."""

    def test_is_world_view(self) -> None:
        world = _make_world()
        assert isinstance(world, WorldView)

    def test_is_mutable_world_protocol(self) -> None:
        world = _make_world()
        assert isinstance(world, MutableWorldProtocol)


# ---------------------------------------------------------------------------
# 4. Toroidal wrapping
# ---------------------------------------------------------------------------


class TestToroidalWrapping:
    """The defining feature: edges wrap around."""

    def test_is_traversable_wraps_negative(self) -> None:
        world = _make_world(width=5, height=5)
        # x=-1 should wrap to x=4
        assert world.is_traversable(Position(x=-1, y=0))

    def test_is_traversable_wraps_overflow(self) -> None:
        world = _make_world(width=5, height=5)
        # x=5 should wrap to x=0
        assert world.is_traversable(Position(x=5, y=0))

    def test_agent_position_wraps(self) -> None:
        world = _make_world(width=5, height=5, agent=Position(x=0, y=0))
        # Set position beyond right edge
        world.agent_position = Position(x=5, y=0)
        assert world.agent_position == Position(x=0, y=0)

    def test_agent_position_wraps_negative(self) -> None:
        world = _make_world(width=5, height=5, agent=Position(x=0, y=0))
        world.agent_position = Position(x=-1, y=0)
        assert world.agent_position == Position(x=4, y=0)

    def test_agent_wraps_vertical(self) -> None:
        world = _make_world(width=5, height=5, agent=Position(x=0, y=0))
        world.agent_position = Position(x=0, y=5)
        assert world.agent_position == Position(x=0, y=0)

    def test_wrapping_respects_obstacles(self) -> None:
        grid = _make_empty_grid(5, 5)
        grid[0][4] = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        world = ToroidalWorld(grid=grid, agent_position=Position(x=0, y=0))
        # x=-1 wraps to x=4, which is an obstacle
        assert not world.is_traversable(Position(x=-1, y=0))

    def test_wrapping_obstacle_blocks_agent(self) -> None:
        grid = _make_empty_grid(5, 5)
        grid[0][4] = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        world = ToroidalWorld(grid=grid, agent_position=Position(x=0, y=0))
        with pytest.raises(ValueError, match="non-traversable"):
            world.agent_position = Position(x=-1, y=0)


# ---------------------------------------------------------------------------
# 5. WorldView API
# ---------------------------------------------------------------------------


class TestWorldViewAPI:
    """Read-only WorldView methods."""

    def test_get_cell_returns_cellview(self) -> None:
        world = _make_world()
        cell = world.get_cell(Position(x=0, y=0))
        assert isinstance(cell, CellView)

    def test_is_within_bounds(self) -> None:
        world = _make_world(width=3, height=3)
        assert world.is_within_bounds(Position(x=0, y=0))
        assert world.is_within_bounds(Position(x=2, y=2))
        # Out-of-bounds is still false for raw bounds check
        assert not world.is_within_bounds(Position(x=3, y=0))


# ---------------------------------------------------------------------------
# 6. World dynamics
# ---------------------------------------------------------------------------


class TestDynamics:
    """tick(), extract_resource(), snapshot()."""

    def test_tick_regenerates(self) -> None:
        world = _make_world(resource_regen_rate=0.1)
        # All cells start empty, tick should add resources
        world.tick()
        cell = world.get_cell(Position(x=0, y=0))
        assert cell.resource_value > 0

    def test_extract_resource(self) -> None:
        grid = _make_empty_grid(3, 3)
        grid[0][0] = Cell(
            cell_type=CellType.RESOURCE, resource_value=0.5)
        world = ToroidalWorld(
            grid=grid, agent_position=Position(x=1, y=1))
        extracted = world.extract_resource(Position(x=0, y=0), 0.3)
        assert extracted == pytest.approx(0.3)
        remaining = world.get_cell(Position(x=0, y=0)).resource_value
        assert remaining == pytest.approx(0.2)

    def test_extract_resource_full_consume(self) -> None:
        grid = _make_empty_grid(3, 3)
        grid[0][0] = Cell(
            cell_type=CellType.RESOURCE, resource_value=0.2)
        world = ToroidalWorld(
            grid=grid, agent_position=Position(x=1, y=1))
        extracted = world.extract_resource(Position(x=0, y=0), 1.0)
        assert extracted == pytest.approx(0.2)
        assert world.get_cell(Position(x=0, y=0)).cell_type == "empty"

    def test_snapshot(self) -> None:
        world = _make_world()
        snap = world.snapshot()
        assert isinstance(snap, WorldSnapshot)
        assert snap.width == world.width
        assert snap.height == world.height


# ---------------------------------------------------------------------------
# 7. Factory
# ---------------------------------------------------------------------------


class TestFactory:
    """create_toroidal_world factory function."""

    def test_creates_correct_dimensions(self) -> None:
        config = _make_config(grid_width=8, grid_height=6)
        world = create_toroidal_world(config, Position(x=0, y=0), seed=42)
        assert world.width == 8
        assert world.height == 6

    def test_obstacle_density(self) -> None:
        config = _make_config(
            grid_width=10, grid_height=10, obstacle_density=0.2)
        world = create_toroidal_world(config, Position(x=0, y=0), seed=42)
        obstacles = sum(
            1 for y in range(10) for x in range(10)
            if not world.is_traversable(Position(x=x, y=y))
        )
        assert obstacles > 0

    def test_agent_not_on_obstacle(self) -> None:
        config = _make_config(
            grid_width=5, grid_height=5, obstacle_density=0.5)
        agent = Position(x=2, y=2)
        world = create_toroidal_world(config, agent, seed=42)
        assert world.is_traversable(agent)


# ---------------------------------------------------------------------------
# 8. Registry integration
# ---------------------------------------------------------------------------


class TestRegistryIntegration:
    """Toroidal world registered in the world registry."""

    def test_registered(self) -> None:
        assert "toroidal" in registered_world_types()

    def test_create_from_config(self) -> None:
        config = _make_config()
        world = create_world_from_config(config, Position(x=2, y=2), seed=42)
        assert isinstance(world, ToroidalWorld)
        assert world.width == 5

    def test_factory_validates_config(self) -> None:
        config = BaseWorldConfig(world_type="toroidal")
        with pytest.raises(ValidationError):
            create_world_from_config(config, Position(x=0, y=0), seed=42)


# ---------------------------------------------------------------------------
# 9. Framework integration
# ---------------------------------------------------------------------------


class TestFrameworkIntegration:
    """System A runs with toroidal world through the framework."""

    def test_setup_and_run_episode(self) -> None:
        from axis.framework.runner import run_episode, setup_episode
        from axis.systems.system_a.config import SystemAConfig

        config_dict = {
            "agent": {
                "initial_energy": 50.0,
                "max_energy": 100.0,
                "memory_capacity": 5,
            },
            "policy": {
                "selection_mode": "sample",
                "temperature": 1.0,
                "stay_suppression": 0.1,
                "consume_weight": 1.5,
            },
            "transition": {
                "move_cost": 1.0,
                "consume_cost": 1.0,
                "stay_cost": 0.5,
                "max_consume": 1.0,
                "energy_gain_factor": 10.0,
            },
        }
        from axis.framework.registry import create_system

        system = create_system("system_a", config_dict)
        world_config = _make_config(resource_regen_rate=0.05)

        world, registry = setup_episode(
            system, world_config, Position(x=2, y=2), seed=42,
        )
        assert isinstance(world, ToroidalWorld)

        trace = run_episode(
            system, world, registry,
            max_steps=50, seed=42,
        )
        assert trace.system_type == "system_a"
        assert trace.total_steps > 0

    def test_deterministic_episodes(self) -> None:
        from axis.framework.registry import create_system
        from axis.framework.runner import run_episode, setup_episode

        config_dict = {
            "agent": {"initial_energy": 20.0, "max_energy": 20.0,
                      "memory_capacity": 3},
            "policy": {"selection_mode": "sample", "temperature": 1.0,
                       "stay_suppression": 0.1, "consume_weight": 1.5},
            "transition": {"move_cost": 1.0, "consume_cost": 1.0,
                           "stay_cost": 0.5, "max_consume": 1.0,
                           "energy_gain_factor": 5.0},
        }

        traces = []
        for _ in range(2):
            system = create_system("system_a", config_dict)
            world_config = _make_config()
            world, registry = setup_episode(
                system, world_config, Position(x=2, y=2), seed=99,
            )
            trace = run_episode(
                system, world, registry,
                max_steps=30, seed=99,
            )
            traces.append(trace)

        assert traces[0].total_steps == traces[1].total_steps
        for s1, s2 in zip(traces[0].steps, traces[1].steps):
            assert s1.action == s2.action


# ---------------------------------------------------------------------------
# 10. Import verification
# ---------------------------------------------------------------------------


class TestImports:
    """Module imports work correctly."""

    def test_import_world_class(self) -> None:
        from axis.world.toroidal import ToroidalWorld
        assert ToroidalWorld is not None

    def test_import_config(self) -> None:
        from axis.world.toroidal import ToroidalWorldConfig
        assert ToroidalWorldConfig is not None

    def test_import_factory(self) -> None:
        from axis.world.toroidal import create_toroidal_world
        assert create_toroidal_world is not None


# ---------------------------------------------------------------------------
# 11. world_metadata (WP-V.0.2)
# ---------------------------------------------------------------------------


class TestToroidalWorldMetadata:
    """Tests for ToroidalWorld.world_metadata()."""

    def test_world_metadata_returns_topology(self) -> None:
        world = _make_world()
        assert world.world_metadata() == {"topology": "toroidal"}

    def test_world_metadata_stable_across_ticks(self) -> None:
        world = _make_world()
        m1 = world.world_metadata()
        world.tick()
        m2 = world.world_metadata()
        assert m1 == m2 == {"topology": "toroidal"}
