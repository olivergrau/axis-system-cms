"""View model types for the Visualization Layer.

Frozen, UI-oriented projections of replay state. Widgets consume
these models without understanding replay internals or system
specifics. All types are immutable Pydantic BaseModels.
"""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict

from axis.visualization.snapshot_models import ReplayCoordinate
from axis.visualization.types import (
    AnalysisSection,
    MetadataSection,
    OverlayData,
    TopologyIndicator,
)
from axis.visualization.viewer_state import PlaybackMode


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
    resource_value: float
    is_obstacle: bool
    is_traversable: bool
    is_agent_here: bool
    is_selected: bool


class GridViewModel(BaseModel):
    """Render-ready grid. cells is flat, row-major."""

    model_config = ConfigDict(frozen=True)

    width: int
    height: int
    cells: tuple[GridCellViewModel, ...]


class AgentViewModel(BaseModel):
    """Render-ready agent state."""

    model_config = ConfigDict(frozen=True)

    row: int
    col: int
    vitality: float
    is_selected: bool


class StatusBarViewModel(BaseModel):
    """Always-visible status information."""

    model_config = ConfigDict(frozen=True)

    step_index: int
    total_steps: int
    phase_index: int
    phase_name: str
    playback_mode: PlaybackMode
    vitality_display: str
    vitality_label: str
    world_info: str | None
    at_start: bool
    at_end: bool


class SelectionViewModel(BaseModel):
    """Current selection context."""

    model_config = ConfigDict(frozen=True)

    selection_type: SelectionType
    selected_cell: tuple[int, int] | None
    agent_selected: bool


class ViewerFrameViewModel(BaseModel):
    """Top-level composite view model for one renderable frame.

    Combines base-layer, world-adapter, and system-adapter outputs
    into a single structure that UI widgets consume.
    """

    model_config = ConfigDict(frozen=True)

    coordinate: ReplayCoordinate
    grid: GridViewModel
    agent: AgentViewModel
    status: StatusBarViewModel
    selection: SelectionViewModel

    # World adapter outputs
    topology_indicators: tuple[TopologyIndicator, ...]
    world_metadata_sections: tuple[MetadataSection, ...]

    # System adapter outputs
    analysis_sections: tuple[AnalysisSection, ...]
    overlay_data: tuple[OverlayData, ...]
    policy_widget_data: dict[str, object] | None = None
    system_widget_data: dict[str, object] | None = None
