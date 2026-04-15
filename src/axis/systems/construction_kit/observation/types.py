"""Observation types -- cell-level and neighborhood-level observation models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CellObservation(BaseModel):
    """Per-cell sensory vector z_j = (b_j, r_j).

    traversability: b_j in {0, 1} -- binary traversability signal
    resource: r_j in [0, 1] -- normalized resource intensity
    """

    model_config = ConfigDict(frozen=True)

    traversability: float = Field(..., ge=0, le=1)
    resource: float = Field(..., ge=0, le=1)


class Observation(BaseModel):
    """Baseline observation vector u_t in R^10.

    Von Neumann neighborhood: current cell + 4 cardinal neighbors.
    Fixed ordering: (b_c, r_c, b_up, r_up, b_down, r_down, b_left, r_left, b_right, r_right).
    """

    model_config = ConfigDict(frozen=True)

    current: CellObservation
    up: CellObservation
    down: CellObservation
    left: CellObservation
    right: CellObservation

    def to_vector(self) -> tuple[float, ...]:
        """Return the flat 10-element observation vector in canonical order."""
        return (
            self.current.traversability,
            self.current.resource,
            self.up.traversability,
            self.up.resource,
            self.down.traversability,
            self.down.resource,
            self.left.traversability,
            self.left.resource,
            self.right.traversability,
            self.right.resource,
        )

    @property
    def dimension(self) -> int:
        """Observation vector dimensionality."""
        return 10
