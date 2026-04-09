"""Visualization supporting types -- data containers for the visualization pipeline."""

from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Cell geometry
# ---------------------------------------------------------------------------


class CellShape(str, enum.Enum):
    """Shape of cells in the grid visualization."""

    RECTANGULAR = "rectangular"
    HEXAGONAL = "hexagonal"


class CellLayout(BaseModel):
    """Pre-computed geometry for rendering the grid.

    Contains polygon vertices, centers, and bounding boxes for every cell.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    cell_shape: CellShape
    grid_width: int
    grid_height: int
    canvas_width: float
    canvas_height: float
    cell_polygons: dict[tuple[int, int], tuple[tuple[float, float], ...]]
    cell_centers: dict[tuple[int, int], tuple[float, float]]
    cell_bounding_boxes: dict[tuple[int, int],
                              tuple[float, float, float, float]]


# ---------------------------------------------------------------------------
# Color configuration
# ---------------------------------------------------------------------------


class CellColorConfig(BaseModel):
    """RGB color palette for cell rendering."""

    model_config = ConfigDict(frozen=True)

    obstacle_color: tuple[int, int, int]
    empty_color: tuple[int, int, int]
    resource_color_min: tuple[int, int, int]
    resource_color_max: tuple[int, int, int]
    agent_color: tuple[int, int, int]
    agent_selected_color: tuple[int, int, int]
    selection_border_color: tuple[int, int, int]
    grid_line_color: tuple[int, int, int]


# ---------------------------------------------------------------------------
# Topology
# ---------------------------------------------------------------------------


class TopologyIndicator(BaseModel):
    """A visual indicator for world topology (e.g. wrap-edge markers)."""

    model_config = ConfigDict(frozen=True)

    indicator_type: str
    position: tuple[float, float]
    data: dict[str, Any]


# ---------------------------------------------------------------------------
# Analysis panel
# ---------------------------------------------------------------------------


class AnalysisRow(BaseModel):
    """A single row in an analysis panel, optionally with nested sub-rows."""

    model_config = ConfigDict(frozen=True)

    label: str
    value: str
    sub_rows: tuple[AnalysisRow, ...] | None = None


AnalysisRow.model_rebuild()


class AnalysisSection(BaseModel):
    """A titled section in the analysis panel."""

    model_config = ConfigDict(frozen=True)

    title: str
    rows: tuple[AnalysisRow, ...]


class MetadataSection(BaseModel):
    """A titled section for world-provided metadata."""

    model_config = ConfigDict(frozen=True)

    title: str
    rows: tuple[AnalysisRow, ...]


# ---------------------------------------------------------------------------
# Overlay system
# ---------------------------------------------------------------------------


class OverlayTypeDeclaration(BaseModel):
    """Declaration of an available overlay type."""

    model_config = ConfigDict(frozen=True)

    key: str
    label: str
    description: str
    legend_html: str = ""


class OverlayItem(BaseModel):
    """A single overlay element at a grid position."""

    model_config = ConfigDict(frozen=True)

    item_type: str
    grid_position: tuple[int, int]
    data: dict[str, Any]


class OverlayData(BaseModel):
    """A complete overlay layer with its items."""

    model_config = ConfigDict(frozen=True)

    overlay_type: str
    items: tuple[OverlayItem, ...]
