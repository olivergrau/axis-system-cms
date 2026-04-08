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
