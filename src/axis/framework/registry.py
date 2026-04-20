"""System registry: maps system type strings to factory functions."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from axis.sdk.interfaces import SystemInterface

SystemFactory = Callable[[dict[str, Any]], SystemInterface]

# Module-level registry
_SYSTEM_REGISTRY: dict[str, SystemFactory] = {}


def register_system(system_type: str, factory: SystemFactory) -> None:
    """Register a system factory for a given system type.

    Raises ValueError if the system type is already registered.
    """
    if system_type in _SYSTEM_REGISTRY:
        raise ValueError(
            f"System type '{system_type}' is already registered."
        )
    _SYSTEM_REGISTRY[system_type] = factory


def get_system_factory(system_type: str) -> SystemFactory:
    """Look up a system factory by type string.

    Raises KeyError with a descriptive message listing available types
    if the requested type is not registered.
    """
    if system_type not in _SYSTEM_REGISTRY:
        available = ", ".join(sorted(_SYSTEM_REGISTRY))
        raise KeyError(
            f"Unknown system type '{system_type}'. "
            f"Available types: {available}"
        )
    return _SYSTEM_REGISTRY[system_type]


def registered_system_types() -> tuple[str, ...]:
    """Return all registered system type strings (sorted)."""
    return tuple(sorted(_SYSTEM_REGISTRY))


def _clear_system_registry() -> None:
    """Clear the system registry. Test-only helper."""
    _SYSTEM_REGISTRY.clear()


def create_system(
    system_type: str, system_config: dict[str, Any],
    system_catalog: Any | None = None,
) -> SystemInterface:
    """Convenience: look up factory and create a system instance.

    If *system_catalog* is provided, uses catalog lookup instead of
    the global registry.
    """
    if system_catalog is not None:
        factory = system_catalog.get(system_type)
    else:
        factory = get_system_factory(system_type)
    return factory(system_config)
