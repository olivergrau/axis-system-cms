"""Signal landscape world tests -- config, protocol, dynamics, factory, integration."""

from __future__ import annotations

import math

import numpy as np
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
from axis.world.signal_landscape.model import SignalCell, SignalCellType
from axis.world.registry import create_world_from_config, registered_world_types
from axis.world.signal_landscape import (
    Hotspot,
    SignalLandscapeConfig,
    SignalLandscapeWorld,
    create_signal_landscape,
)
from axis.world.signal_landscape.dynamics import recompute_signals


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_empty_grid(w: int, h: int) -> list[list[SignalCell]]:
    return [
        [SignalCell(cell_type=SignalCellType.EMPTY, resource_value=0.0)
         for _ in range(w)]
        for _ in range(h)
    ]


def _recompute(world: SignalLandscapeWorld) -> None:
    """Helper: recompute signal field on a manually-constructed world."""
    recompute_signals(
        world._grid, world._hotspots,
        world.width, world.height, world._decay_rate,
    )


def _make_config(**overrides: object) -> BaseWorldConfig:
    defaults = {
        "world_type": "signal_landscape",
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
) -> SignalLandscapeWorld:
    if agent is None:
        agent = Position(x=width // 2, y=height // 2)
    config = _make_config(
        grid_width=width, grid_height=height, **config_overrides)
    return create_signal_landscape(config, agent, seed=seed)


# ---------------------------------------------------------------------------
# 1. Config validation
# ---------------------------------------------------------------------------


class TestSignalLandscapeConfig:
    """Config model validation."""

    def test_defaults(self) -> None:
        c = SignalLandscapeConfig(grid_width=5, grid_height=5)
        assert c.num_hotspots == 3
        assert c.hotspot_radius == 3.0
        assert c.drift_speed == 0.5
        assert c.decay_rate == 0.02
        assert c.obstacle_density == 0.0
        assert c.signal_intensity == 1.0

    def test_explicit_values(self) -> None:
        c = SignalLandscapeConfig(
            grid_width=10, grid_height=8,
            num_hotspots=5, hotspot_radius=2.0,
            drift_speed=1.0, decay_rate=0.1,
            obstacle_density=0.2, signal_intensity=0.5,
        )
        assert c.grid_width == 10
        assert c.num_hotspots == 5

    def test_grid_width_positive(self) -> None:
        with pytest.raises(ValidationError):
            SignalLandscapeConfig(grid_width=0, grid_height=5)

    def test_grid_height_positive(self) -> None:
        with pytest.raises(ValidationError):
            SignalLandscapeConfig(grid_width=5, grid_height=-1)

    def test_num_hotspots_at_least_one(self) -> None:
        with pytest.raises(ValidationError):
            SignalLandscapeConfig(grid_width=5, grid_height=5, num_hotspots=0)

    def test_hotspot_radius_positive(self) -> None:
        with pytest.raises(ValidationError):
            SignalLandscapeConfig(
                grid_width=5, grid_height=5, hotspot_radius=0)

    def test_decay_rate_bounds(self) -> None:
        with pytest.raises(ValidationError):
            SignalLandscapeConfig(grid_width=5, grid_height=5, decay_rate=1.5)

    def test_frozen(self) -> None:
        c = SignalLandscapeConfig(grid_width=5, grid_height=5)
        with pytest.raises(ValidationError):
            c.grid_width = 10  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 2. World construction
# ---------------------------------------------------------------------------


class TestWorldConstruction:
    """SignalLandscapeWorld construction and basic properties."""

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
            SignalLandscapeWorld(
                grid=[],
                agent_position=Position(x=0, y=0),
                hotspots=[],
                drift_speed=0.0,
                decay_rate=0.0,
                rng=np.random.default_rng(0),
            )

    def test_agent_out_of_bounds_raises(self) -> None:
        with pytest.raises(ValueError, match="out of bounds"):
            SignalLandscapeWorld(
                grid=_make_empty_grid(3, 3),
                agent_position=Position(x=5, y=5),
                hotspots=[],
                drift_speed=0.0,
                decay_rate=0.0,
                rng=np.random.default_rng(0),
            )

    def test_agent_on_obstacle_raises(self) -> None:
        grid = _make_empty_grid(3, 3)
        grid[1][1] = SignalCell(cell_type=SignalCellType.OBSTACLE, resource_value=0.0)
        with pytest.raises(ValueError, match="non-traversable"):
            SignalLandscapeWorld(
                grid=grid,
                agent_position=Position(x=1, y=1),
                hotspots=[],
                drift_speed=0.0,
                decay_rate=0.0,
                rng=np.random.default_rng(0),
            )


# ---------------------------------------------------------------------------
# 3. Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    """SignalLandscapeWorld satisfies SDK protocols."""

    def test_is_world_view(self) -> None:
        world = _make_world()
        assert isinstance(world, WorldView)

    def test_is_mutable_world_protocol(self) -> None:
        world = _make_world()
        assert isinstance(world, MutableWorldProtocol)


# ---------------------------------------------------------------------------
# 4. WorldView API
# ---------------------------------------------------------------------------


class TestWorldViewAPI:
    """Read-only WorldView methods."""

    def test_get_cell_returns_cellview(self) -> None:
        world = _make_world()
        cell = world.get_cell(Position(x=0, y=0))
        assert isinstance(cell, CellView)
        assert cell.cell_type in ("empty", "resource", "obstacle")

    def test_get_cell_out_of_bounds_raises(self) -> None:
        world = _make_world(width=3, height=3)
        with pytest.raises(ValueError):
            world.get_cell(Position(x=10, y=10))

    def test_is_within_bounds(self) -> None:
        world = _make_world(width=3, height=3)
        assert world.is_within_bounds(Position(x=0, y=0))
        assert world.is_within_bounds(Position(x=2, y=2))
        assert not world.is_within_bounds(Position(x=3, y=0))
        assert not world.is_within_bounds(Position(x=-1, y=0))

    def test_is_traversable_obstacle(self) -> None:
        world = _make_world(width=5, height=5, obstacle_density=0.3, seed=99)
        # At least one cell should be non-traversable with 30% density
        non_traversable = sum(
            1 for y in range(5) for x in range(5)
            if not world.is_traversable(Position(x=x, y=y))
        )
        assert non_traversable > 0

    def test_is_traversable_out_of_bounds(self) -> None:
        world = _make_world(width=3, height=3)
        assert not world.is_traversable(Position(x=10, y=10))


# ---------------------------------------------------------------------------
# 5. Signal field
# ---------------------------------------------------------------------------


class TestSignalField:
    """Signal values from hotspots."""

    def test_signal_values_in_range(self) -> None:
        world = _make_world(width=10, height=10)
        for y in range(10):
            for x in range(10):
                cell = world.get_cell(Position(x=x, y=y))
                assert 0.0 <= cell.resource_value <= 1.0

    def test_cells_near_hotspot_have_signal(self) -> None:
        """A world with a single centered hotspot should have signal at center."""
        grid = _make_empty_grid(5, 5)
        hotspot = Hotspot(cx=2.0, cy=2.0, radius=2.0, intensity=1.0)
        world = SignalLandscapeWorld(
            grid=grid,
            agent_position=Position(x=0, y=0),
            hotspots=[hotspot],
            drift_speed=0.0,
            decay_rate=0.0,
            rng=np.random.default_rng(0),
        )
        _recompute(world)
        center = world.get_cell(Position(x=2, y=2))
        corner = world.get_cell(Position(x=0, y=0))
        assert center.resource_value > corner.resource_value

    def test_obstacle_cells_have_zero_signal(self) -> None:
        grid = _make_empty_grid(5, 5)
        grid[2][2] = SignalCell(cell_type=SignalCellType.OBSTACLE, resource_value=0.0)
        hotspot = Hotspot(cx=2.0, cy=2.0, radius=3.0, intensity=1.0)
        world = SignalLandscapeWorld(
            grid=grid,
            agent_position=Position(x=0, y=0),
            hotspots=[hotspot],
            drift_speed=0.0,
            decay_rate=0.0,
            rng=np.random.default_rng(0),
        )
        _recompute(world)
        assert world.get_cell(Position(x=2, y=2)).resource_value == 0.0

    def test_signal_type_matches_value(self) -> None:
        """Cells with signal > 0 should be 'resource', else 'empty'."""
        world = _make_world(width=10, height=10,
                            num_hotspots=1, hotspot_radius=1.0)
        for y in range(10):
            for x in range(10):
                cell = world.get_cell(Position(x=x, y=y))
                if cell.resource_value > 0:
                    assert cell.cell_type == "resource"
                else:
                    assert cell.cell_type == "empty"


# ---------------------------------------------------------------------------
# 6. tick() dynamics
# ---------------------------------------------------------------------------


class TestTickDynamics:
    """Signal field evolves with tick()."""

    def test_tick_changes_signals(self) -> None:
        world = _make_world(
            width=15, height=15,
            agent=Position(x=0, y=0),
            drift_speed=3.0, decay_rate=0.0,
            num_hotspots=1, hotspot_radius=2.0,
        )
        snap_before = world.snapshot()
        world.tick()
        snap_after = world.snapshot()
        # At least some cells should change as the single hotspot drifts
        changed = sum(
            1 for y in range(world.height) for x in range(world.width)
            if snap_before.grid[y][x].resource_value != snap_after.grid[y][x].resource_value
        )
        assert changed > 0

    def test_tick_deterministic_with_seed(self) -> None:
        w1 = _make_world(seed=123)
        w2 = _make_world(seed=123)
        w1.tick()
        w2.tick()
        for y in range(w1.height):
            for x in range(w1.width):
                assert (w1.get_cell(Position(x=x, y=y)).resource_value
                        == w2.get_cell(Position(x=x, y=y)).resource_value)

    def test_different_seeds_differ(self) -> None:
        w1 = _make_world(width=15, height=15, agent=Position(x=0, y=0),
                         seed=1, num_hotspots=1, hotspot_radius=2.0)
        w2 = _make_world(width=15, height=15, agent=Position(x=0, y=0),
                         seed=2, num_hotspots=1, hotspot_radius=2.0)
        w1.tick()
        w2.tick()
        values1 = [w1.get_cell(Position(x=x, y=y)).resource_value
                   for y in range(15) for x in range(15)]
        values2 = [w2.get_cell(Position(x=x, y=y)).resource_value
                   for y in range(15) for x in range(15)]
        assert values1 != values2

    def test_decay_reduces_signals(self) -> None:
        """Decay factor reduces peak signal below the no-decay value."""
        grid_no_decay = _make_empty_grid(5, 5)
        hotspot_nd = Hotspot(cx=2.0, cy=2.0, radius=3.0, intensity=1.0)
        world_no_decay = SignalLandscapeWorld(
            grid=grid_no_decay,
            agent_position=Position(x=0, y=0),
            hotspots=[hotspot_nd],
            drift_speed=0.0,
            decay_rate=0.0,
            rng=np.random.default_rng(0),
        )
        _recompute(world_no_decay)
        val_no_decay = world_no_decay.get_cell(
            Position(x=2, y=2)).resource_value

        grid_decay = _make_empty_grid(5, 5)
        hotspot_d = Hotspot(cx=2.0, cy=2.0, radius=3.0, intensity=1.0)
        world_decay = SignalLandscapeWorld(
            grid=grid_decay,
            agent_position=Position(x=0, y=0),
            hotspots=[hotspot_d],
            drift_speed=0.0,
            decay_rate=0.5,
            rng=np.random.default_rng(0),
        )
        _recompute(world_decay)
        val_with_decay = world_decay.get_cell(
            Position(x=2, y=2)).resource_value

        assert val_with_decay < val_no_decay

    def test_multiple_ticks_evolve(self) -> None:
        world = _make_world(
            width=15, height=15,
            agent=Position(x=0, y=0),
            drift_speed=2.0, num_hotspots=1, hotspot_radius=2.0,
        )
        snapshots = []
        for _ in range(5):
            snapshots.append(world.snapshot())
            world.tick()
        # Not all snapshots should be identical
        first_vals = [
            c.resource_value for row in snapshots[0].grid for c in row]
        last_vals = [
            c.resource_value for row in snapshots[-1].grid for c in row]
        assert first_vals != last_vals


# ---------------------------------------------------------------------------
# 7. extract_resource()
# ---------------------------------------------------------------------------


class TestExtractResource:
    """Signal landscape never allows extraction."""

    def test_returns_zero(self) -> None:
        world = _make_world()
        result = world.extract_resource(Position(x=2, y=2), 1.0)
        assert result == 0.0

    def test_does_not_mutate_cell(self) -> None:
        world = _make_world()
        val_before = world.get_cell(Position(x=2, y=2)).resource_value
        world.extract_resource(Position(x=2, y=2), 1.0)
        val_after = world.get_cell(Position(x=2, y=2)).resource_value
        assert val_before == val_after


# ---------------------------------------------------------------------------
# 8. Mutation API
# ---------------------------------------------------------------------------


class TestMutationAPI:
    """Internal mutation methods."""

    def test_agent_position_setter(self) -> None:
        world = _make_world(width=5, height=5, agent=Position(x=0, y=0))
        world.agent_position = Position(x=1, y=0)
        assert world.agent_position == Position(x=1, y=0)

    def test_agent_position_rejects_obstacle(self) -> None:
        grid = _make_empty_grid(3, 3)
        grid[1][1] = SignalCell(cell_type=SignalCellType.OBSTACLE, resource_value=0.0)
        world = SignalLandscapeWorld(
            grid=grid,
            agent_position=Position(x=0, y=0),
            hotspots=[],
            drift_speed=0.0,
            decay_rate=0.0,
            rng=np.random.default_rng(0),
        )
        with pytest.raises(ValueError, match="non-traversable"):
            world.agent_position = Position(x=1, y=1)

    def test_agent_position_rejects_out_of_bounds(self) -> None:
        world = _make_world(width=3, height=3)
        with pytest.raises(ValueError):
            world.agent_position = Position(x=10, y=10)

    def test_get_internal_cell(self) -> None:
        world = _make_world()
        cell = world.get_internal_cell(Position(x=0, y=0))
        assert isinstance(cell, SignalCell)

    def test_set_cell(self) -> None:
        world = _make_world()
        new_cell = SignalCell(cell_type=SignalCellType.RESOURCE,
                        resource_value=0.99)
        world.set_cell(Position(x=0, y=0), new_cell)
        assert world.get_internal_cell(
            Position(x=0, y=0)).resource_value == 0.99


# ---------------------------------------------------------------------------
# 9. Snapshot
# ---------------------------------------------------------------------------


class TestSnapshot:
    """snapshot() returns correct WorldSnapshot."""

    def test_returns_world_snapshot(self) -> None:
        world = _make_world()
        snap = world.snapshot()
        assert isinstance(snap, WorldSnapshot)

    def test_dimensions_match(self) -> None:
        world = _make_world(width=7, height=4)
        snap = world.snapshot()
        assert snap.width == 7
        assert snap.height == 4
        assert len(snap.grid) == 4
        assert len(snap.grid[0]) == 7

    def test_preserves_values(self) -> None:
        world = _make_world()
        snap = world.snapshot()
        for y in range(world.height):
            for x in range(world.width):
                cell = world.get_cell(Position(x=x, y=y))
                assert snap.grid[y][x].resource_value == cell.resource_value


# ---------------------------------------------------------------------------
# 10. Factory
# ---------------------------------------------------------------------------


class TestFactory:
    """create_signal_landscape factory function."""

    def test_creates_correct_dimensions(self) -> None:
        config = _make_config(grid_width=8, grid_height=6)
        world = create_signal_landscape(config, Position(x=0, y=0), seed=42)
        assert world.width == 8
        assert world.height == 6

    def test_deterministic_with_seed(self) -> None:
        config = _make_config()
        w1 = create_signal_landscape(config, Position(x=2, y=2), seed=42)
        w2 = create_signal_landscape(config, Position(x=2, y=2), seed=42)
        for y in range(5):
            for x in range(5):
                assert (w1.get_cell(Position(x=x, y=y)).resource_value
                        == w2.get_cell(Position(x=x, y=y)).resource_value)

    def test_obstacle_density(self) -> None:
        config = _make_config(
            grid_width=10, grid_height=10, obstacle_density=0.2)
        world = create_signal_landscape(config, Position(x=0, y=0), seed=42)
        obstacles = sum(
            1 for y in range(10) for x in range(10)
            if not world.is_traversable(Position(x=x, y=y))
        )
        assert obstacles > 0

    def test_agent_not_on_obstacle(self) -> None:
        config = _make_config(grid_width=5, grid_height=5,
                              obstacle_density=0.5)
        agent = Position(x=2, y=2)
        world = create_signal_landscape(config, agent, seed=42)
        assert world.is_traversable(agent)
        assert world.agent_position == agent


# ---------------------------------------------------------------------------
# 11. Registry integration
# ---------------------------------------------------------------------------


class TestRegistryIntegration:
    """Signal landscape registered in the world registry."""

    def test_registered(self) -> None:
        assert "signal_landscape" in registered_world_types()

    def test_create_from_config(self) -> None:
        config = _make_config()
        world = create_world_from_config(config, Position(x=2, y=2), seed=42)
        assert isinstance(world, SignalLandscapeWorld)
        assert world.width == 5

    def test_factory_validates_config(self) -> None:
        config = BaseWorldConfig(world_type="signal_landscape")
        # Missing grid_width / grid_height
        with pytest.raises(ValidationError):
            create_world_from_config(config, Position(x=0, y=0), seed=42)


# ---------------------------------------------------------------------------
# 12. Framework integration with System B
# ---------------------------------------------------------------------------


class TestFrameworkIntegration:
    """System B runs successfully with signal_landscape world."""

    def test_setup_and_run_episode(self) -> None:
        from axis.framework.runner import run_episode, setup_episode
        from axis.systems.system_b.config import AgentConfig, SystemBConfig
        from axis.systems.system_b.system import SystemB

        config = SystemBConfig(
            agent=AgentConfig(initial_energy=30.0, max_energy=50.0),
        )
        system = SystemB(config)
        world_config = _make_config()

        world, registry = setup_episode(
            system, world_config, Position(x=2, y=2), seed=42,
        )
        assert isinstance(world, SignalLandscapeWorld)
        assert registry.has_handler("scan")

        trace = run_episode(
            system, world, registry,
            max_steps=50, seed=42,
        )
        assert trace.system_type == "system_b"
        assert trace.total_steps > 0
        assert trace.termination_reason in (
            "max_steps_reached", "energy_depleted")

    def test_scan_appears_in_trace(self) -> None:
        from axis.framework.runner import run_episode, setup_episode
        from axis.systems.system_b.config import (
            AgentConfig,
            PolicyConfig,
            SystemBConfig,
        )
        from axis.systems.system_b.system import SystemB

        config = SystemBConfig(
            agent=AgentConfig(initial_energy=50.0, max_energy=50.0),
            policy=PolicyConfig(scan_bonus=10.0),
        )
        system = SystemB(config)
        world_config = _make_config()

        world, registry = setup_episode(
            system, world_config, Position(x=2, y=2), seed=42,
        )
        trace = run_episode(
            system, world, registry,
            max_steps=50, seed=42,
        )
        actions = [step.action for step in trace.steps]
        assert "scan" in actions

    def test_deterministic_episodes(self) -> None:
        from axis.framework.runner import run_episode, setup_episode
        from axis.systems.system_b.config import AgentConfig, SystemBConfig
        from axis.systems.system_b.system import SystemB

        config = SystemBConfig(
            agent=AgentConfig(initial_energy=20.0, max_energy=20.0),
        )

        traces = []
        for _ in range(2):
            system = SystemB(config)
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
# 13. Import verification
# ---------------------------------------------------------------------------


class TestImports:
    """Module imports work correctly."""

    def test_import_world_class(self) -> None:
        from axis.world.signal_landscape import SignalLandscapeWorld
        assert SignalLandscapeWorld is not None

    def test_import_config(self) -> None:
        from axis.world.signal_landscape import SignalLandscapeConfig
        assert SignalLandscapeConfig is not None

    def test_import_factory(self) -> None:
        from axis.world.signal_landscape import create_signal_landscape
        assert create_signal_landscape is not None
