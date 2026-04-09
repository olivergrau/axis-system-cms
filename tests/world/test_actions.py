"""WP-2.2 verification tests -- Action engine (registry, handlers, dispatch)."""

from __future__ import annotations

from typing import Any

import pytest

from axis.sdk.position import Position
from axis.sdk.world_types import ActionOutcome
from axis.world.actions import ActionRegistry, create_action_registry
from axis.world.grid_2d.model import Cell, CellType, World


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_open_grid(width: int = 5, height: int = 5) -> list[list[Cell]]:
    """All-empty grid."""
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    return [[empty for _ in range(width)] for _ in range(height)]


def _make_world(
    width: int = 5,
    height: int = 5,
    agent_x: int = 2,
    agent_y: int = 2,
) -> World:
    """Convenience world builder."""
    grid = _make_open_grid(width, height)
    return World(grid=grid, agent_position=Position(x=agent_x, y=agent_y))


# ---------------------------------------------------------------------------
# ActionRegistry construction
# ---------------------------------------------------------------------------


class TestRegistryConstruction:
    """ActionRegistry initializes with base action handlers."""

    def test_has_all_base_actions(self) -> None:
        registry = create_action_registry()
        for action in ("up", "down", "left", "right", "stay"):
            assert registry.has_handler(action)

    def test_registered_actions_includes_base(self) -> None:
        registry = create_action_registry()
        actions = set(registry.registered_actions)
        assert actions == {"up", "down", "left", "right", "stay"}

    def test_no_consume_by_default(self) -> None:
        registry = create_action_registry()
        assert registry.has_handler("consume") is False

    def test_factory_returns_new_instance(self) -> None:
        r1 = create_action_registry()
        r2 = create_action_registry()
        assert r1 is not r2


# ---------------------------------------------------------------------------
# Movement actions
# ---------------------------------------------------------------------------


class TestMovementActions:
    """Built-in movement handlers."""

    def test_move_up(self) -> None:
        world = _make_world()
        registry = create_action_registry()
        outcome = registry.apply(world, "up")
        assert outcome.moved is True
        assert outcome.new_position == Position(x=2, y=1)
        assert world.agent_position == Position(x=2, y=1)

    def test_move_down(self) -> None:
        world = _make_world()
        registry = create_action_registry()
        outcome = registry.apply(world, "down")
        assert outcome.moved is True
        assert outcome.new_position == Position(x=2, y=3)

    def test_move_left(self) -> None:
        world = _make_world()
        registry = create_action_registry()
        outcome = registry.apply(world, "left")
        assert outcome.moved is True
        assert outcome.new_position == Position(x=1, y=2)

    def test_move_right(self) -> None:
        world = _make_world()
        registry = create_action_registry()
        outcome = registry.apply(world, "right")
        assert outcome.moved is True
        assert outcome.new_position == Position(x=3, y=2)

    def test_move_into_obstacle(self) -> None:
        grid = _make_open_grid()
        grid[1][2] = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
        world = World(grid=grid, agent_position=Position(x=2, y=2))
        registry = create_action_registry()
        outcome = registry.apply(world, "up")
        assert outcome.moved is False
        assert outcome.new_position == Position(x=2, y=2)
        assert world.agent_position == Position(x=2, y=2)

    def test_move_out_of_bounds(self) -> None:
        world = _make_world(agent_x=0, agent_y=0)
        registry = create_action_registry()
        outcome = registry.apply(world, "up")
        assert outcome.moved is False
        assert outcome.new_position == Position(x=0, y=0)

    def test_action_name_echoed(self) -> None:
        world = _make_world()
        registry = create_action_registry()
        outcome = registry.apply(world, "left")
        assert outcome.action == "left"

    def test_movement_defaults(self) -> None:
        world = _make_world()
        registry = create_action_registry()
        outcome = registry.apply(world, "up")
        assert outcome.data == {}

    def test_returns_action_outcome(self) -> None:
        world = _make_world()
        registry = create_action_registry()
        outcome = registry.apply(world, "down")
        assert isinstance(outcome, ActionOutcome)


# ---------------------------------------------------------------------------
# Stay action
# ---------------------------------------------------------------------------


class TestStayAction:
    """Built-in stay handler."""

    def test_position_unchanged(self) -> None:
        world = _make_world()
        registry = create_action_registry()
        pos_before = world.agent_position
        outcome = registry.apply(world, "stay")
        assert outcome.moved is False
        assert outcome.new_position == pos_before
        assert world.agent_position == pos_before

    def test_no_consumption(self) -> None:
        world = _make_world()
        registry = create_action_registry()
        outcome = registry.apply(world, "stay")
        assert outcome.data == {}

    def test_action_name(self) -> None:
        world = _make_world()
        registry = create_action_registry()
        outcome = registry.apply(world, "stay")
        assert outcome.action == "stay"


# ---------------------------------------------------------------------------
# Custom action registration
# ---------------------------------------------------------------------------


def _dummy_handler(
    world: World,
    *,
    context: dict[str, Any],
) -> ActionOutcome:
    """A simple custom handler for testing."""
    return ActionOutcome(
        action="custom",
        moved=False,
        new_position=world.agent_position,
        data={"consumed": True, "resource_consumed": 0.42},
    )


class TestCustomRegistration:
    """Custom action handler registration."""

    def test_register_custom_action(self) -> None:
        registry = create_action_registry()
        registry.register("consume", _dummy_handler)
        assert registry.has_handler("consume") is True

    def test_override_base_action_raises(self) -> None:
        registry = create_action_registry()
        with pytest.raises(ValueError, match="Cannot override base action"):
            registry.register("up", _dummy_handler)

    def test_override_stay_raises(self) -> None:
        registry = create_action_registry()
        with pytest.raises(ValueError, match="Cannot override base action"):
            registry.register("stay", _dummy_handler)

    def test_duplicate_custom_raises(self) -> None:
        registry = create_action_registry()
        registry.register("zap", _dummy_handler)
        with pytest.raises(ValueError, match="already registered"):
            registry.register("zap", _dummy_handler)

    def test_dispatch_to_custom_handler(self) -> None:
        world = _make_world()
        registry = create_action_registry()
        registry.register("custom", _dummy_handler)
        outcome = registry.apply(world, "custom")
        assert outcome.data["consumed"] is True
        assert outcome.data["resource_consumed"] == 0.42

    def test_custom_in_registered_actions(self) -> None:
        registry = create_action_registry()
        registry.register("consume", _dummy_handler)
        assert "consume" in registry.registered_actions


# ---------------------------------------------------------------------------
# Unknown action dispatch
# ---------------------------------------------------------------------------


class TestUnknownAction:
    """Dispatch to unregistered action."""

    def test_raises_key_error(self) -> None:
        world = _make_world()
        registry = create_action_registry()
        with pytest.raises(KeyError, match="No handler registered"):
            registry.apply(world, "unknown")


# ---------------------------------------------------------------------------
# Context passing
# ---------------------------------------------------------------------------


def _context_echo_handler(
    world: World,
    *,
    context: dict[str, Any],
) -> ActionOutcome:
    """Handler that echoes context values into outcome for verification."""
    return ActionOutcome(
        action="echo",
        moved=False,
        new_position=world.agent_position,
        data={
            "flag": bool(context.get("flag")),
            "value": context.get("value", 0.0),
        },
    )


class TestContextPassing:
    """Context dict is forwarded to handlers."""

    def test_context_reaches_handler(self) -> None:
        world = _make_world()
        registry = create_action_registry()
        registry.register("echo", _context_echo_handler)
        outcome = registry.apply(
            world, "echo", context={"flag": True, "value": 0.77}
        )
        assert outcome.data["flag"] is True
        assert outcome.data["value"] == 0.77

    def test_empty_context_by_default(self) -> None:
        world = _make_world()
        registry = create_action_registry()
        registry.register("echo", _context_echo_handler)
        outcome = registry.apply(world, "echo")
        assert outcome.data["flag"] is False
        assert outcome.data["value"] == 0.0


# ---------------------------------------------------------------------------
# Import verification
# ---------------------------------------------------------------------------


class TestImports:
    """Import paths work correctly."""

    def test_import_from_axis_world(self) -> None:
        from axis.world import ActionRegistry, create_action_registry  # noqa: F401

    def test_import_from_actions_module(self) -> None:
        from axis.world.actions import (  # noqa: F401
            ActionRegistry,
            create_action_registry,
        )
