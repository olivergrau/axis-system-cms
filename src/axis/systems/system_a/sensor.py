"""System A sensor -- Von Neumann neighborhood observation builder."""

from __future__ import annotations

from axis.sdk.position import Position
from axis.sdk.world_types import WorldView
from axis.systems.system_a.types import CellObservation, Observation

# Sentinel for out-of-bounds cells: non-traversable, no resource.
_OUT_OF_BOUNDS = CellObservation(traversability=0.0, resource=0.0)


class SystemASensor:
    """Von Neumann neighborhood sensor for System A.

    Satisfies SensorInterface. Produces a 10-dimensional observation
    from the world state around the agent's position.
    """

    def observe(self, world_view: WorldView, position: Position) -> Observation:
        """Construct observation from world view and position.

        Reads the Von Neumann neighborhood (current cell + 4 cardinal
        neighbors) and converts each to a CellObservation.

        Directional mapping:
            up    = (x, y-1)
            down  = (x, y+1)
            left  = (x-1, y)
            right = (x+1, y)
        """
        x, y = position.x, position.y

        return Observation(
            current=self._observe_cell(world_view, position),
            up=self._observe_cell(world_view, Position(x=x, y=y - 1)),
            down=self._observe_cell(world_view, Position(x=x, y=y + 1)),
            left=self._observe_cell(world_view, Position(x=x - 1, y=y)),
            right=self._observe_cell(world_view, Position(x=x + 1, y=y)),
        )

    def _observe_cell(
        self, world_view: WorldView, position: Position,
    ) -> CellObservation:
        """Project a single cell to its observation representation.

        Out-of-bounds positions return (0.0, 0.0).
        """
        if not world_view.is_within_bounds(position):
            return _OUT_OF_BOUNDS

        cell = world_view.get_cell(position)
        return CellObservation(
            traversability=1.0 if cell.cell_type != "obstacle" else 0.0,
            resource=cell.resource_value,
        )
