"""Observation builder (sensor projection) for AXIS System A."""

from __future__ import annotations

from axis_system_a.types import CellObservation, Observation, Position
from axis_system_a.world import World

# Sentinel for out-of-bounds cells: non-traversable, no resource.
_OUT_OF_BOUNDS = CellObservation(traversability=0.0, resource=0.0)


def _observe_cell(world: World, position: Position) -> CellObservation:
    """Project a single cell to its observation representation.

    Out-of-bounds positions return (0.0, 0.0).
    """
    if not world.is_within_bounds(position):
        return _OUT_OF_BOUNDS

    cell = world.get_cell(position)
    return CellObservation(
        traversability=1.0 if cell.is_traversable else 0.0,
        resource=cell.resource_value,
    )


def build_observation(world: World, position: Position) -> Observation:
    """Construct the agent's local observation from world state.

    Pure projection: reads the von Neumann neighborhood around the
    given position and returns a 10-dimensional Observation.

    Directional mapping (The_World.md Section 10.2):
        up    = (x, y-1)
        down  = (x, y+1)
        left  = (x-1, y)
        right = (x+1, y)
    """
    x, y = position.x, position.y

    return Observation(
        current=_observe_cell(world, position),
        up=_observe_cell(world, Position(x=x, y=y - 1)),
        down=_observe_cell(world, Position(x=x, y=y + 1)),
        left=_observe_cell(world, Position(x=x - 1, y=y)),
        right=_observe_cell(world, Position(x=x + 1, y=y)),
    )
