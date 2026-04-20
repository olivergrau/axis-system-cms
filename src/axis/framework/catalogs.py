"""Infrastructure catalogs — composition-friendly lookup abstractions.

Provides a generic ``Catalog`` class that wraps the existing global
registries behind an injectable interface.  Each catalog is a typed,
dict-backed lookup that can be populated by the plugin bridge (WP-05)
or directly in tests.

This module does NOT delete the existing registry modules.  It sits
alongside them and will eventually replace direct global access.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Catalog(Generic[T]):
    """A typed lookup table for plugin-provided capabilities.

    Can be used as a constructor-injected dependency instead of
    importing global registry functions.
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._entries: dict[str, T] = {}

    @property
    def name(self) -> str:
        return self._name

    def register(self, key: str, value: T) -> None:
        """Register a capability.  Raises on duplicate."""
        if key in self._entries:
            raise ValueError(
                f"Duplicate registration in {self._name} catalog: '{key}'"
            )
        self._entries[key] = value

    def get(self, key: str) -> T:
        """Look up a capability.  Raises ``KeyError`` if missing."""
        try:
            return self._entries[key]
        except KeyError:
            available = ", ".join(sorted(self._entries)) or "(none)"
            raise KeyError(
                f"'{key}' not found in {self._name} catalog. "
                f"Available: {available}"
            ) from None

    def get_optional(self, key: str) -> T | None:
        """Look up a capability, returning ``None`` if missing."""
        return self._entries.get(key)

    def keys(self) -> list[str]:
        """Return all registered keys."""
        return list(self._entries.keys())

    def __contains__(self, key: str) -> bool:
        return key in self._entries

    def __len__(self) -> int:
        return len(self._entries)


# -----------------------------------------------------------------------
# Pre-defined catalog types for the five registry domains.
# -----------------------------------------------------------------------

SystemCatalog = Catalog[Any]        # SystemFactory values
WorldCatalog = Catalog[Any]         # WorldFactory values
WorldVisCatalog = Catalog[Any]      # WorldVisFactory values
SystemVisCatalog = Catalog[Any]     # SystemVisFactory values
ComparisonExtensionCatalog = Catalog[Any]  # ComparisonExtensionProtocol


def build_catalogs_from_registries() -> dict[str, Catalog]:
    """Populate catalogs from the existing global registries.

    This is the bridge that lets the new catalog abstraction coexist
    with the old global registries during migration.
    """
    from axis.framework.registry import _SYSTEM_REGISTRY
    from axis.world.registry import _WORLD_REGISTRY
    from axis.visualization.registry import (
        _WORLD_VIS_REGISTRY,
        _SYSTEM_VIS_REGISTRY,
    )
    from axis.framework.comparison.extensions import _EXTENSION_REGISTRY

    systems = SystemCatalog("systems")
    for k, v in _SYSTEM_REGISTRY.items():
        systems.register(k, v)

    worlds = WorldCatalog("worlds")
    for k, v in _WORLD_REGISTRY.items():
        worlds.register(k, v)

    world_vis = WorldVisCatalog("world_vis")
    for k, v in _WORLD_VIS_REGISTRY.items():
        world_vis.register(k, v)

    system_vis = SystemVisCatalog("system_vis")
    for k, v in _SYSTEM_VIS_REGISTRY.items():
        system_vis.register(k, v)

    extensions = ComparisonExtensionCatalog("comparison_extensions")
    for k, v in _EXTENSION_REGISTRY.items():
        extensions.register(k, v)

    return {
        "systems": systems,
        "worlds": worlds,
        "world_vis": world_vis,
        "system_vis": system_vis,
        "comparison_extensions": extensions,
    }
