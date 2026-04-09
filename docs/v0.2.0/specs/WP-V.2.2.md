# WP-V.2.2 Implementation Brief -- Toroidal World Adapter

## Context

The toroidal world is a topology variant of the grid_2d world -- same cell model, same colors, but edges wrap around. The visualization adapter extends the grid_2d adapter with wrap-edge topology indicators and a world info line.

### Predecessor State

- `Grid2DWorldVisualizationAdapter` exists (WP-V.2.1), inheriting from `DefaultWorldVisualizationAdapter`
- The toroidal world returns `{"topology": "toroidal"}` from `world_metadata()` (WP-V.0.2)

### Reference Documents

- `docs/v0.2.0/architecture/evolution/visualization-architecture.md` -- Section 11.1 (ToroidalWorldVisualizationAdapter)

---

## Objective

Implement `ToroidalWorldVisualizationAdapter` that extends the grid_2d adapter with four wrap-edge topology indicators and a status line.

---

## Scope

### 1. ToroidalWorldVisualizationAdapter

**File**: `src/axis/world/toroidal/visualization.py` (new)

```python
"""Toroidal world visualization adapter.

Extends the grid_2d adapter with wrap-edge indicators on all four
grid edges, visually communicating the toroidal topology.
"""

from __future__ import annotations

from typing import Any

from axis.sdk.snapshot import WorldSnapshot
from axis.world.grid_2d.visualization import Grid2DWorldVisualizationAdapter
from axis.visualization.types import CellLayout, TopologyIndicator


class ToroidalWorldVisualizationAdapter(Grid2DWorldVisualizationAdapter):
    """Visualization adapter for the toroidal world type.

    Inherits rectangular grid layout and colors from the Grid2D adapter.
    Overrides topology_indicators() to show wrap edges and
    format_world_info() to display topology status.
    """

    def topology_indicators(
        self,
        world_snapshot: WorldSnapshot,
        world_data: dict[str, Any],
        cell_layout: CellLayout,
    ) -> list[TopologyIndicator]:
        """Return wrap-edge indicators for all four grid edges.

        Each indicator is a TopologyIndicator with type "wrap_edge"
        positioned at the midpoint of the grid edge.
        """
        cw = cell_layout.canvas_width
        ch = cell_layout.canvas_height
        indicators = [
            TopologyIndicator(
                indicator_type="wrap_edge",
                position=(0.0, ch / 2),
                data={"edge": "left", "style": "dashed"},
            ),
            TopologyIndicator(
                indicator_type="wrap_edge",
                position=(cw, ch / 2),
                data={"edge": "right", "style": "dashed"},
            ),
            TopologyIndicator(
                indicator_type="wrap_edge",
                position=(cw / 2, 0.0),
                data={"edge": "top", "style": "dashed"},
            ),
            TopologyIndicator(
                indicator_type="wrap_edge",
                position=(cw / 2, ch),
                data={"edge": "bottom", "style": "dashed"},
            ),
        ]
        return indicators

    def format_world_info(
        self,
        world_data: dict[str, Any],
    ) -> str | None:
        return "Toroidal topology (edges wrap)"
```

**Design notes**:

- Inherits from `Grid2DWorldVisualizationAdapter` (per architecture spec Section 11.1)
- Only two methods overridden: `topology_indicators()` and `format_world_info()`
- Wrap-edge indicator positions are at edge midpoints in pixel coordinates
- The `data["style"]` is `"dashed"` -- the CanvasWidget renderer (WP-V.4.1) will draw dashed lines along the grid edges
- `world_data` is not read (topology is static), but the parameter is accepted per the protocol

### 2. Registration

**Same file**:

```python
from axis.visualization.registry import register_world_visualization

def _toroidal_vis_factory(world_config: dict[str, Any]) -> ToroidalWorldVisualizationAdapter:
    return ToroidalWorldVisualizationAdapter()

register_world_visualization("toroidal", _toroidal_vis_factory)
```

---

## Out of Scope

- Canvas rendering of wrap-edge indicators (WP-V.4.1)
- Modifications to the toroidal world model
- Any PySide6 code

---

## Testing Requirements

**File**: `tests/v02/visualization/test_toroidal_world_adapter.py` (new)

1. **`test_toroidal_inherits_grid2d_behavior`**:
   - Assert `adapter.cell_shape() == CellShape.RECTANGULAR`
   - Assert `adapter.cell_color_config()` matches default colors

2. **`test_toroidal_topology_indicators_count`**:
   - Build a `CellLayout` for a 3x3 grid at 300x300
   - Assert `len(adapter.topology_indicators(snap, {}, layout)) == 4`

3. **`test_toroidal_topology_indicator_types`**:
   - Assert all 4 indicators have `indicator_type == "wrap_edge"`

4. **`test_toroidal_topology_indicator_edges`**:
   - Assert the 4 edges are `{"left", "right", "top", "bottom"}`

5. **`test_toroidal_topology_indicator_positions`**:
   - For 300x200 canvas, assert left edge position is `(0.0, 100.0)`, right is `(300.0, 100.0)`, etc.

6. **`test_toroidal_format_world_info`**:
   - Assert `adapter.format_world_info({}) == "Toroidal topology (edges wrap)"`

7. **`test_toroidal_metadata_sections_empty`**:
   - Assert `adapter.world_metadata_sections({}) == []` (inherited)

8. **`test_toroidal_registration`**:
   - Import module, resolve `"toroidal"`, assert correct type

---

## Expected Deliverable

1. `src/axis/world/toroidal/visualization.py`
2. `tests/v02/visualization/test_toroidal_world_adapter.py`
3. Confirmation that all existing tests still pass

---

## Important Final Constraint

Two method overrides. Everything else is inherited. Keep it minimal.
