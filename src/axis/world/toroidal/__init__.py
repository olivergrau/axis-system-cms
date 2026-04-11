"""Toroidal world package -- wraparound grid world type.

A topology variant of the built-in ``grid_2d`` world where edges
wrap around instead of blocking movement. Reuses grid_2d's cell
model and regeneration since the internal representation is identical.

Registered as world type ``"toroidal"``.
"""

from axis.world.toroidal.config import ToroidalWorldConfig
from axis.world.toroidal.factory import create_toroidal_world
from axis.world.toroidal.model import ToroidalWorld

__all__ = [
    "ToroidalWorld",
    "ToroidalWorldConfig",
    "create_toroidal_world",
]


def register() -> None:
    """Register toroidal: world factory + visualization adapter."""
    from axis.world.registry import register_world, registered_world_types

    if "toroidal" not in registered_world_types():

        def _factory(config, agent_position, seed):
            return create_toroidal_world(config, agent_position, seed=seed)

        register_world("toroidal", _factory)

    from axis.visualization.registry import registered_world_visualizations

    if "toroidal" not in registered_world_visualizations():
        try:
            import axis.world.toroidal.visualization  # noqa: F401
        except ImportError:
            pass
