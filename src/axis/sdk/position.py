"""Shared grid coordinate type."""

from pydantic import BaseModel, ConfigDict


class Position(BaseModel):
    """Grid coordinate.

    Position belongs to the world state, not the agent state.
    The framework tracks agent position; the agent does not know
    its own position directly.
    """

    model_config = ConfigDict(frozen=True)

    x: int
    y: int
