"""System A+W internal types -- world model, curiosity output, agent state."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axis.systems.system_a.types import MemoryState


class WorldModelState(BaseModel):
    """Spatial world model: relative position + visit counts.

    The world model uses agent-relative coordinates maintained
    through dead reckoning (path integration). No absolute position
    data is stored or consumed.

    Model reference: Section 4.1.
    """

    model_config = ConfigDict(frozen=True)

    relative_position: tuple[int, int] = Field(
        default=(0, 0),
        description="Agent's position estimate via dead reckoning, relative to start",
    )
    visit_counts: tuple[tuple[tuple[int, int], int], ...] = Field(
        default_factory=tuple,
        description="Immutable sequence of ((x, y), count) pairs",
    )


class CuriosityDriveOutput(BaseModel):
    """Output of the curiosity drive computation.

    activation: scalar curiosity level d_C(t) in [0, mu_C]
    spatial_novelty: per-direction spatial novelty (up, down, left, right)
    sensory_novelty: per-direction sensory novelty (up, down, left, right)
    composite_novelty: per-direction composite novelty (up, down, left, right)
    action_contributions: 6-element tuple indexed by action order
        (UP, DOWN, LEFT, RIGHT, CONSUME, STAY)

    Model reference: Sections 5.2, 6.3.
    """

    model_config = ConfigDict(frozen=True)

    activation: float = Field(..., ge=0, le=1)

    spatial_novelty: tuple[float, float, float, float] = Field(
        ..., description="(up, down, left, right)",
    )
    sensory_novelty: tuple[float, float, float, float] = Field(
        ..., description="(up, down, left, right)",
    )
    composite_novelty: tuple[float, float, float, float] = Field(
        ..., description="(up, down, left, right)",
    )

    action_contributions: tuple[
        float, float, float, float, float, float,
    ] = Field(..., description="(UP, DOWN, LEFT, RIGHT, CONSUME, STAY)")


class DriveWeights(BaseModel):
    """Dynamic drive weights from the arbitration function.

    w_H(t) = w_H_base + (1 - w_H_base) * d_H(t)^gamma
    w_C(t) = w_C_base * (1 - d_H(t))^gamma

    Model reference: Section 6.4.
    """

    model_config = ConfigDict(frozen=True)

    hunger_weight: float = Field(..., ge=0)
    curiosity_weight: float = Field(..., ge=0)


class AgentStateAW(BaseModel):
    """System A+W agent state: energy + memory + world model.

    Extends System A's AgentState with the spatial world model.
    Position is explicitly NOT part of AgentStateAW in the absolute
    sense -- only the *relative* position estimate (inside WorldModelState)
    is tracked, via dead reckoning.

    Model reference: Section 4.
    """

    model_config = ConfigDict(frozen=True)

    energy: float = Field(..., ge=0)
    memory_state: MemoryState
    world_model: WorldModelState
