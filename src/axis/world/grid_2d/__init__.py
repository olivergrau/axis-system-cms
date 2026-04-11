"""Grid-2D world package -- the built-in default world type."""

from axis.world.grid_2d.config import Grid2DWorldConfig
from axis.world.grid_2d.dynamics import apply_regeneration
from axis.world.grid_2d.factory import create_world
from axis.world.grid_2d.model import Cell, CellType, RegenerationMode, World

__all__ = [
    "Cell",
    "CellType",
    "RegenerationMode",
    "World",
    "Grid2DWorldConfig",
    "create_world",
    "apply_regeneration",
]


def register() -> None:
    """Register grid_2d: world factory + visualization adapter."""
    from axis.world.registry import register_world, registered_world_types

    if "grid_2d" not in registered_world_types():

        def _factory(config, agent_position, seed):
            return create_world(config, agent_position, seed=seed)

        register_world("grid_2d", _factory)

    from axis.visualization.registry import registered_world_visualizations

    if "grid_2d" not in registered_world_visualizations():
        try:
            import axis.world.grid_2d.visualization  # noqa: F401
        except ImportError:
            pass
