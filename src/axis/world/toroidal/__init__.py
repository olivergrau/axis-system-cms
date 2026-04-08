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

# --- Registration ---
from axis.world.registry import register_world  # noqa: E402


def _toroidal_factory(
    config: object,
    agent_position: object,
    seed: object,
) -> ToroidalWorld:
    # type: ignore[arg-type]
    return create_toroidal_world(config, agent_position, seed=seed)


register_world("toroidal", _toroidal_factory)  # type: ignore[arg-type]
