"""World registry: maps world type strings to factory functions."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig, MutableWorldProtocol

WorldFactory = Callable[[BaseWorldConfig,
                         Position, int | None], MutableWorldProtocol]

# Module-level registry
_WORLD_REGISTRY: dict[str, WorldFactory] = {}


def register_world(world_type: str, factory: WorldFactory) -> None:
    """Register a world factory for a given world type.

    Raises ValueError if the world type is already registered.
    """
    if world_type in _WORLD_REGISTRY:
        raise ValueError(
            f"World type '{world_type}' is already registered."
        )
    _WORLD_REGISTRY[world_type] = factory


def get_world_factory(world_type: str) -> WorldFactory:
    """Look up a world factory by type string.

    Raises KeyError with a descriptive message listing available types
    if the requested type is not registered.
    """
    if world_type not in _WORLD_REGISTRY:
        available = ", ".join(sorted(_WORLD_REGISTRY))
        raise KeyError(
            f"Unknown world type '{world_type}'. "
            f"Available types: {available}"
        )
    return _WORLD_REGISTRY[world_type]


def registered_world_types() -> tuple[str, ...]:
    """Return all registered world type strings (sorted)."""
    return tuple(sorted(_WORLD_REGISTRY))


def create_world_from_config(
    config: BaseWorldConfig,
    agent_position: Position,
    seed: int | None = None,
) -> MutableWorldProtocol:
    """Convenience: look up factory by config.world_type and create a world.

    Equivalent to get_world_factory(config.world_type)(config, agent_position, seed).
    """
    factory = get_world_factory(config.world_type)
    return factory(config, agent_position, seed)


def _grid_2d_factory(
    config: BaseWorldConfig,
    agent_position: Position,
    seed: int | None,
) -> MutableWorldProtocol:
    """Factory for the built-in 2D grid world."""
    from axis.world.grid_2d.factory import create_world

    return create_world(config, agent_position, seed=seed)


# Auto-register built-in world type
register_world("grid_2d", _grid_2d_factory)
