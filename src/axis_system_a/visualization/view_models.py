"""View model types for the Visualization Layer (VWP5).

Frozen, UI-oriented projections of replay state.  Widgets consume these
models without understanding replay internals.  All types are immutable
Pydantic BaseModels; none carry business logic.
"""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict

from axis_system_a.enums import Action, CellType, TerminationReason
from axis_system_a.visualization.debug_overlay_models import DebugOverlayViewModel
from axis_system_a.visualization.snapshot_models import (
    ReplayCoordinate,
    ReplayPhase,
)
from axis_system_a.visualization.viewer_state import PlaybackMode


class SelectionType(str, enum.Enum):
    """What entity, if any, is currently selected."""

    NONE = "none"
    CELL = "cell"
    AGENT = "agent"


class GridCellViewModel(BaseModel):
    """Render-ready representation of a single grid cell."""

    model_config = ConfigDict(frozen=True)

    row: int
    col: int
    cell_type: CellType
    resource_value: float
    is_obstacle: bool
    is_traversable: bool
    is_agent_here: bool
    is_selected: bool


class GridViewModel(BaseModel):
    """Render-ready grid.  ``cells`` is flat, row-major (index = row * width + col)."""

    model_config = ConfigDict(frozen=True)

    width: int
    height: int
    cells: tuple[GridCellViewModel, ...]


class AgentViewModel(BaseModel):
    """Render-ready agent state."""

    model_config = ConfigDict(frozen=True)

    row: int
    col: int
    energy: float
    is_selected: bool


class StatusBarViewModel(BaseModel):
    """Always-visible status information."""

    model_config = ConfigDict(frozen=True)

    step_index: int
    total_steps: int
    phase: ReplayPhase
    playback_mode: PlaybackMode
    energy: float
    at_start: bool
    at_end: bool


class SelectionViewModel(BaseModel):
    """Current selection context."""

    model_config = ConfigDict(frozen=True)

    selection_type: SelectionType
    selected_cell: tuple[int, int] | None
    agent_selected: bool


class ActionContextViewModel(BaseModel):
    """Action and outcome context for the current step."""

    model_config = ConfigDict(frozen=True)

    action: Action
    moved: bool
    consumed: bool
    resource_consumed: float
    energy_delta: float
    terminated: bool
    termination_reason: TerminationReason | None


class ViewerFrameViewModel(BaseModel):
    """Top-level composite view model for one renderable frame."""

    model_config = ConfigDict(frozen=True)

    coordinate: ReplayCoordinate
    grid: GridViewModel
    agent: AgentViewModel
    status: StatusBarViewModel
    selection: SelectionViewModel
    action_context: ActionContextViewModel
    debug_overlay: DebugOverlayViewModel | None = None
