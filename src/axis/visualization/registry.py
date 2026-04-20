"""Visualization registry -- adapter resolution with graceful fallback."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from axis.visualization.adapters.default_world import DefaultWorldVisualizationAdapter
from axis.visualization.adapters.null_system import NullSystemVisualizationAdapter

WorldVisFactory = Callable[[dict[str, Any]], Any]
SystemVisFactory = Callable[[], Any]

_WORLD_VIS_REGISTRY: dict[str, WorldVisFactory] = {}
_SYSTEM_VIS_REGISTRY: dict[str, SystemVisFactory] = {}


def register_world_visualization(world_type: str, factory: WorldVisFactory) -> None:
    """Register a world visualization adapter factory.

    Raises ValueError if the world type is already registered.
    """
    if world_type in _WORLD_VIS_REGISTRY:
        raise ValueError(
            f"World visualization for '{world_type}' is already registered."
        )
    _WORLD_VIS_REGISTRY[world_type] = factory


def register_system_visualization(system_type: str, factory: SystemVisFactory) -> None:
    """Register a system visualization adapter factory.

    Raises ValueError if the system type is already registered.
    """
    if system_type in _SYSTEM_VIS_REGISTRY:
        raise ValueError(
            f"System visualization for '{system_type}' is already registered."
        )
    _SYSTEM_VIS_REGISTRY[system_type] = factory


def resolve_world_adapter(
    world_type: str, world_config: dict[str, Any],
    world_vis_catalog: Any | None = None,
) -> Any:
    """Resolve a world visualization adapter, falling back to default."""
    if world_vis_catalog is not None:
        factory = world_vis_catalog.get_optional(world_type)
    else:
        factory = _WORLD_VIS_REGISTRY.get(world_type)
    if factory is not None:
        return factory(world_config)
    return DefaultWorldVisualizationAdapter()


def resolve_system_adapter(
    system_type: str,
    system_vis_catalog: Any | None = None,
) -> Any:
    """Resolve a system visualization adapter, falling back to null."""
    if system_vis_catalog is not None:
        factory = system_vis_catalog.get_optional(system_type)
    else:
        factory = _SYSTEM_VIS_REGISTRY.get(system_type)
    if factory is not None:
        return factory()
    return NullSystemVisualizationAdapter()


def registered_world_visualizations() -> tuple[str, ...]:
    """Return all registered world visualization type strings (sorted)."""
    return tuple(sorted(_WORLD_VIS_REGISTRY))


def registered_system_visualizations() -> tuple[str, ...]:
    """Return all registered system visualization type strings (sorted)."""
    return tuple(sorted(_SYSTEM_VIS_REGISTRY))


def _clear_registries() -> None:
    """Clear both registries. Test-only helper."""
    _WORLD_VIS_REGISTRY.clear()
    _SYSTEM_VIS_REGISTRY.clear()
