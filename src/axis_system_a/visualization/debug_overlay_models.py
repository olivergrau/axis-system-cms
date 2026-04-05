"""Debug overlay data models for VWP9.

Defines the overlay configuration, per-type overlay data, and composite
DebugOverlayViewModel used by the grid widget for rendering.
"""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict, Field


class DebugOverlayType(str, enum.Enum):
    """Available debug overlay types."""

    ACTION_PREFERENCE = "action_preference"
    DRIVE_CONTRIBUTION = "drive_contribution"
    CONSUMPTION_OPPORTUNITY = "consumption_opportunity"


class DebugOverlayConfig(BaseModel):
    """Toggle state for the debug overlay system.

    master_enabled gates the entire overlay system. Individual type
    flags are only meaningful when master_enabled is True.
    """

    model_config = ConfigDict(frozen=True)

    master_enabled: bool = False
    action_preference_enabled: bool = False
    drive_contribution_enabled: bool = False
    consumption_opportunity_enabled: bool = False


class ActionPreferenceOverlay(BaseModel):
    """Per-action probability arrows from the agent cell.

    All 6-element tuples are indexed by Action enum order:
    (UP, DOWN, LEFT, RIGHT, CONSUME, STAY).
    """

    model_config = ConfigDict(frozen=True)

    agent_row: int = Field(ge=0)
    agent_col: int = Field(ge=0)
    probabilities: tuple[float, float, float, float, float, float]
    admissibility_mask: tuple[bool, bool, bool, bool, bool, bool]
    selected_action_index: int = Field(ge=0, le=5)


class DriveContributionOverlay(BaseModel):
    """Per-action drive contribution bars on the agent cell.

    action_contributions indexed by Action enum order.
    """

    model_config = ConfigDict(frozen=True)

    agent_row: int = Field(ge=0)
    agent_col: int = Field(ge=0)
    activation: float = Field(ge=0, le=1)
    action_contributions: tuple[float, float, float, float, float, float]


class ConsumptionOpportunityOverlay(BaseModel):
    """Resource availability on agent cell and neighbors.

    Neighbor order: (UP, DOWN, LEFT, RIGHT).
    """

    model_config = ConfigDict(frozen=True)

    agent_row: int = Field(ge=0)
    agent_col: int = Field(ge=0)
    current_resource: float = Field(ge=0, le=1)
    neighbor_resources: tuple[float, float, float, float]
    neighbor_traversable: tuple[bool, bool, bool, bool]


class DebugOverlayViewModel(BaseModel):
    """Composite overlay data passed to the grid widget.

    Only populated overlays whose type is enabled will be non-None.
    """

    model_config = ConfigDict(frozen=True)

    config: DebugOverlayConfig
    action_preference: ActionPreferenceOverlay | None = None
    drive_contribution: DriveContributionOverlay | None = None
    consumption_opportunity: ConsumptionOpportunityOverlay | None = None
