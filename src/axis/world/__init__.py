"""World Framework -- action engine, registry, and world type packages.

Generic infrastructure (actions, registry) lives at this level.
Concrete world types live in sub-packages (grid_2d, signal_landscape, toroidal).

Grid-2D types are re-exported here for backward compatibility.
"""

from axis.world.actions import ActionRegistry, create_action_registry
from axis.world.grid_2d import Cell, CellType, RegenerationMode, World, create_world
from axis.world.registry import (
    create_world_from_config,
    get_world_factory,
    register_world,
    registered_world_types,
)

# Import sub-packages to trigger world type registration
import axis.world.signal_landscape  # noqa: F401
import axis.world.toroidal  # noqa: F401

__all__ = [
    "CellType",
    "RegenerationMode",
    "Cell",
    "World",
    "create_world",
    "ActionRegistry",
    "create_action_registry",
    "register_world",
    "get_world_factory",
    "registered_world_types",
    "create_world_from_config",
]
