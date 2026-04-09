# WP-V.1.1 Implementation Brief -- Supporting Types

## Context

Phase V-0 extended the replay contract to carry world metadata. Phase V-1 defines the visualization-specific data contracts that both adapter protocols (WP-V.1.2) will depend on.

This work package creates the supporting types module -- all the Pydantic models and enums that form the data language of the visualization system. These types are the structured data that flows between world adapters, system adapters, and the base layer. No PySide6 or Qt types appear here.

### Predecessor State (After Phase V-0)

```
src/axis/visualization/
    __init__.py             # Empty -- "Visualization -- replay viewer and system adapter framework."
```

The visualization package exists but contains no modules beyond the package init.

### Architectural Decisions (Binding)

- **D1**: Adapters return structured data, not QPainter commands. All types in this module are UI-framework-agnostic.
- **D3**: `CellLayout` bridges world geometry and system overlays.
- **D6**: `OverlayItem` uses `item_type` string dispatch -- extensible without modifying the renderer.

### Reference Documents

- `docs/architecture/evolution/visualization-architecture.md` -- Section 6 (Supporting Types)
- `docs/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.1.1

---

## Objective

Create `src/axis/visualization/types.py` containing all supporting types from Section 6 of the visualization architecture spec:

1. `CellShape` enum
2. `CellLayout` model (the central bridge between world geometry and system overlays)
3. `CellColorConfig` model (color rules for cell rendering)
4. `TopologyIndicator` model (world topology visual cues)
5. `AnalysisRow` and `AnalysisSection` models (step analysis panel data)
6. `OverlayTypeDeclaration` model (overlay checkbox declarations)
7. `OverlayItem` and `OverlayData` models (structured overlay rendering data)
8. `MetadataSection` model (world-specific detail panel data)

All types are frozen Pydantic models with no dependencies beyond `pydantic` and Python standard library.

---

## Scope

### 1. CellShape Enum

```python
import enum


class CellShape(str, enum.Enum):
    """Cell geometry type. Determines CellLayout computation."""

    RECTANGULAR = "rectangular"
    HEXAGONAL = "hexagonal"
```

Currently only `RECTANGULAR` is used. `HEXAGONAL` is reserved for future world types.

### 2. CellLayout Model

The central bridge between world geometry and system overlays. Produced by the world adapter, consumed by the canvas and overlay renderer.

```python
class CellLayout(BaseModel):
    """Maps grid positions to pixel geometry.

    Produced by WorldVisualizationAdapter.cell_layout().
    Consumed by CanvasWidget for cell rendering and by
    OverlayRenderer for translating grid-coordinate overlays
    to pixel-coordinate draw calls.

    For rectangular grids:
        cell_w = canvas_width / grid_width
        cell_h = canvas_height / grid_height
        cell_centers[(x, y)] = (x * cell_w + cell_w/2, y * cell_h + cell_h/2)
        cell_polygons[(x, y)] = four rectangle corners

    For hexagonal grids the math changes but the contract is identical.
    System overlays work without modification on any geometry.
    """

    model_config = ConfigDict(frozen=True)

    cell_shape: CellShape
    grid_width: int
    grid_height: int
    canvas_width: float
    canvas_height: float

    # position (x, y) -> polygon vertices, pixel coordinates
    cell_polygons: dict[tuple[int, int], tuple[tuple[float, float], ...]]

    # position (x, y) -> center point, pixel coordinates
    cell_centers: dict[tuple[int, int], tuple[float, float]]

    # position (x, y) -> bounding box (x, y, width, height)
    cell_bounding_boxes: dict[tuple[int, int], tuple[float, float, float, float]]
```

**Design notes**:

- Dict keys are `(x, y)` integer tuples (grid coordinates)
- Polygon vertices are ordered for direct rendering (e.g., clockwise)
- Bounding boxes are `(x, y, width, height)` in pixel coordinates
- The model is frozen -- constructed once per canvas resize, cached by the base layer
- Pydantic may need `arbitrary_types_allowed` or explicit `TypeAdapter` handling for tuple-keyed dicts. If Pydantic v2 does not support `dict[tuple[int, int], ...]` natively as frozen fields, use `model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)`. **Test this during implementation and adjust if needed.**

### 3. CellColorConfig Model

```python
class CellColorConfig(BaseModel):
    """Color rules for cell rendering. Colors are RGB tuples (0-255).

    The base renderer uses linear RGB interpolation between
    resource_color_min and resource_color_max based on
    CellView.resource_value.
    """

    model_config = ConfigDict(frozen=True)

    obstacle_color: tuple[int, int, int]
    empty_color: tuple[int, int, int]
    resource_color_min: tuple[int, int, int]   # resource_value = 0.0
    resource_color_max: tuple[int, int, int]   # resource_value = 1.0
    agent_color: tuple[int, int, int]
    agent_selected_color: tuple[int, int, int]
    selection_border_color: tuple[int, int, int]
    grid_line_color: tuple[int, int, int]
```

All colors are `(R, G, B)` with each component in range `[0, 255]`. No alpha channel -- transparency is handled at the rendering level if needed.

### 4. TopologyIndicator Model

```python
class TopologyIndicator(BaseModel):
    """A visual cue for world topology, rendered on the canvas.

    Known indicator_type values:
        "wrap_edge"       -- dashed line at grid edge indicating wraparound
        "hotspot_center"  -- marker at a hotspot position
    """

    model_config = ConfigDict(frozen=True)

    indicator_type: str
    position: tuple[float, float]    # pixel coordinates
    data: dict[str, Any]
```

**`data` contents by indicator_type**:

| indicator_type | data keys |
|---------------|-----------|
| `"wrap_edge"` | `edge` (`"left"` / `"right"` / `"top"` / `"bottom"`), `style` (str) |
| `"hotspot_center"` | `radius_pixels` (float), `intensity` (float), `label` (str) |

### 5. AnalysisRow and AnalysisSection Models

```python
class AnalysisRow(BaseModel):
    """A labeled value in an analysis section."""

    model_config = ConfigDict(frozen=True)

    label: str
    value: str
    sub_rows: tuple[AnalysisRow, ...] | None = None


class AnalysisSection(BaseModel):
    """One titled section of the step analysis panel.

    Produced by SystemVisualizationAdapter.build_step_analysis().
    Rendered by StepAnalysisPanel as formatted text/tree.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    rows: tuple[AnalysisRow, ...]
```

`AnalysisRow` is self-referential -- `sub_rows` allows nested display (e.g., per-action breakdowns within a "Decision Pipeline" section). Pydantic v2 handles self-referential models natively via `model_rebuild()`.

### 6. OverlayTypeDeclaration Model

```python
class OverlayTypeDeclaration(BaseModel):
    """Declares one overlay type for the control panel.

    Each declaration becomes a checkbox in DebugOverlayPanel.
    The key must match OverlayData.overlay_type.
    """

    model_config = ConfigDict(frozen=True)

    key: str            # unique ID, e.g. "action_preference"
    label: str          # checkbox label, e.g. "Action Preference"
    description: str    # tooltip text
```

### 7. OverlayItem and OverlayData Models

```python
class OverlayItem(BaseModel):
    """A single overlay element to render at a grid position.

    The OverlayRenderer dispatches on item_type to the appropriate
    drawing method. All position data is in grid coordinates --
    the renderer translates to pixel coordinates via CellLayout.

    Known item_type values (closed set rendered by OverlayRenderer):
        "direction_arrow"  -- line from cell center in a direction
        "center_dot"       -- filled dot at cell center
        "center_ring"      -- ring at cell center
        "bar_chart"        -- mini bar chart within cell bounds
        "diamond_marker"   -- rotated square at cell center
        "neighbor_dot"     -- dot at a specific cell
        "radius_circle"    -- circle at cell center with pixel radius
        "x_marker"         -- X at cell center
    """

    model_config = ConfigDict(frozen=True)

    item_type: str
    grid_position: tuple[int, int]   # (x, y) grid coordinates
    data: dict[str, Any]


class OverlayData(BaseModel):
    """One overlay layer. Multiple can be active simultaneously.

    Produced by SystemVisualizationAdapter.build_overlays().
    overlay_type must match an OverlayTypeDeclaration.key.
    """

    model_config = ConfigDict(frozen=True)

    overlay_type: str    # matches OverlayTypeDeclaration.key
    items: tuple[OverlayItem, ...]
```

**`data` contents by item_type**:

| item_type | data keys |
|-----------|-----------|
| `direction_arrow` | `direction` (str), `length` (float 0-1), `is_selected` (bool), `color` (str) |
| `center_dot` | `radius` (float 0-1), `is_selected` (bool) |
| `center_ring` | `radius` (float 0-1), `is_selected` (bool) |
| `bar_chart` | `activation` (float), `values` (list[float]), `labels` (list[str]) |
| `diamond_marker` | `opacity` (float 0-1) |
| `neighbor_dot` | `resource_value` (float), `is_traversable` (bool) |
| `radius_circle` | `radius_cells` (int), `label` (str) |
| `x_marker` | (no extra params -- empty dict) |

### 8. MetadataSection Model

```python
class MetadataSection(BaseModel):
    """World-specific metadata for the detail panel.

    Produced by WorldVisualizationAdapter.world_metadata_sections().
    Reuses AnalysisRow for consistent display formatting.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    rows: tuple[AnalysisRow, ...]
```

### 9. Module Structure

**File**: `src/axis/visualization/types.py`

Imports:

```python
from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel, ConfigDict
```

Type ordering in the file (respecting dependencies):

1. `CellShape`
2. `CellLayout`
3. `CellColorConfig`
4. `TopologyIndicator`
5. `AnalysisRow`
6. `AnalysisSection`
7. `MetadataSection`
8. `OverlayTypeDeclaration`
9. `OverlayItem`
10. `OverlayData`

`AnalysisRow` must precede `AnalysisSection` and `MetadataSection` (both reference it). All other orderings are for readability.

### 10. Package Exports

**File**: `src/axis/visualization/__init__.py`

Do **not** add exports yet. The `__init__.py` stays minimal until the full visualization package is assembled (WP-V.4.4). Consumers import directly from `axis.visualization.types`.

---

## Out of Scope

Do **not** implement any of the following in WP-V.1.1:

- Adapter protocols (`WorldVisualizationAdapter`, `SystemVisualizationAdapter`) -- WP-V.1.2
- Default/null adapter implementations -- WP-V.1.3
- Visualization registry -- WP-V.1.4
- Concrete adapters (grid_2d, toroidal, signal_landscape, System A/B) -- WP-V.2.x
- Any PySide6 or Qt imports
- Any rendering logic
- Any modifications to existing SDK or framework code

---

## Architectural Constraints

### 1. No Qt/PySide6 Imports

This module must not import anything from PySide6, Qt, or any UI framework. All color values are plain integer tuples. All positions are float tuples. The rendering layer (WP-V.4.x) translates these to Qt types.

### 2. Frozen Models

All types use `ConfigDict(frozen=True)`. They are immutable after construction.

### 3. JSON Serializable

All types must round-trip through `model_dump(mode="json")` and reconstruction. This is critical for testing and for potential future serialization of visualization state.

**Exception**: `CellLayout` contains `dict[tuple[int, int], ...]` which may not serialize to JSON natively (JSON dict keys must be strings). This is acceptable -- `CellLayout` is a runtime-only bridge object, never persisted. If `model_dump(mode="json")` is needed for testing, use `model_dump()` (Python mode) instead.

### 4. No Validation Beyond Pydantic Defaults

Do not add custom validators (e.g., range checks on RGB values, non-negative grid dimensions). Keep the types simple frozen data containers. Validation is the responsibility of the adapter implementations that construct them.

### 5. Self-Referential AnalysisRow

`AnalysisRow.sub_rows` references `AnalysisRow`. Pydantic v2 handles this natively. If `model_rebuild()` is needed, call it after the class definition:

```python
AnalysisRow.model_rebuild()
```

Test that nested construction works in the test suite.

---

## Testing Requirements

**File**: `tests/visualization/test_types.py` (new)

Create directory `tests/visualization/` with `__init__.py`.

### Construction tests

1. **`test_cell_shape_values`**:
   - Assert `CellShape.RECTANGULAR.value == "rectangular"`
   - Assert `CellShape.HEXAGONAL.value == "hexagonal"`

2. **`test_cell_layout_construction`**:
   - Construct a `CellLayout` for a 2x2 rectangular grid with known values
   - Assert `cell_shape == CellShape.RECTANGULAR`
   - Assert all 4 positions present in `cell_polygons`, `cell_centers`, `cell_bounding_boxes`
   - Assert a specific cell center value is correct

3. **`test_cell_layout_frozen`**:
   - Construct a `CellLayout`, attempt to set `grid_width` -- assert raises

4. **`test_cell_color_config_construction`**:
   - Construct with 8 RGB tuples
   - Assert each field accessible and correct

5. **`test_topology_indicator_construction`**:
   - Construct with `indicator_type="wrap_edge"`, position, and data dict
   - Assert fields correct

6. **`test_analysis_row_simple`**:
   - Construct `AnalysisRow(label="Energy", value="3.45")` with `sub_rows=None`
   - Assert fields correct

7. **`test_analysis_row_nested`**:
   - Construct `AnalysisRow` with `sub_rows` containing two child rows
   - Assert `len(row.sub_rows) == 2`
   - Assert child row values accessible

8. **`test_analysis_section_construction`**:
   - Construct `AnalysisSection` with title and 3 rows
   - Assert `len(section.rows) == 3`

9. **`test_metadata_section_construction`**:
   - Construct `MetadataSection` with title and rows
   - Assert fields correct

10. **`test_overlay_type_declaration_construction`**:
    - Construct with key, label, description
    - Assert fields correct

11. **`test_overlay_item_construction`**:
    - Construct with `item_type="direction_arrow"`, `grid_position=(3, 2)`, and data dict
    - Assert fields correct

12. **`test_overlay_data_construction`**:
    - Construct with `overlay_type` and tuple of `OverlayItem` instances
    - Assert `len(overlay.items)` matches

### Serialization tests

13. **`test_cell_color_config_round_trip`**:
    - `model_dump()` then reconstruct -- assert equal

14. **`test_analysis_section_round_trip`**:
    - Including nested `AnalysisRow` with sub_rows
    - `model_dump()` then reconstruct -- assert equal

15. **`test_overlay_data_round_trip`**:
    - `model_dump()` then reconstruct -- assert equal

16. **`test_topology_indicator_round_trip`**:
    - `model_dump()` then reconstruct -- assert equal

### Import test

17. **`test_import_from_types_module`**:
    - `from axis.visualization.types import CellShape, CellLayout, CellColorConfig, TopologyIndicator, AnalysisRow, AnalysisSection, MetadataSection, OverlayTypeDeclaration, OverlayItem, OverlayData`
    - Assert all are accessible

### Existing tests

All existing tests must continue to pass.

---

## Implementation Style

- Python 3.11+
- Frozen Pydantic v2 `BaseModel` with `ConfigDict(frozen=True)`
- `from __future__ import annotations` for forward reference support
- Clear docstrings on each type explaining its role in the visualization pipeline
- Types documented with `data` key tables in docstrings where applicable
- No custom validators -- types are simple data containers

---

## Expected Deliverable

1. `src/axis/visualization/types.py` with all 10 types
2. `tests/visualization/__init__.py` (new)
3. `tests/visualization/test_types.py` with construction, serialization, and import tests
4. Confirmation that all existing tests still pass

---

## Expected File Structure

After WP-V.1.1:

```
src/axis/visualization/
    __init__.py                     # UNCHANGED
    types.py                        # NEW (10 types)

tests/visualization/
    __init__.py                     # NEW
    test_types.py                   # NEW
```

All other files unchanged.

---

## Important Final Constraint

This module is **pure data definitions**. No logic, no computation, no I/O. Each type is a frozen Pydantic model or a string enum. The module should be short and readable -- approximately 150-200 lines of code including docstrings.

If `CellLayout`'s tuple-keyed dict fields cause Pydantic validation issues, resolve pragmatically: use `arbitrary_types_allowed=True` in that model's config, or change the key type to a string representation `"x,y"` and provide a helper to convert. Document the choice. The architecture spec allows this flexibility -- the key contract is that `CellLayout` maps grid positions to pixel geometry; the exact key encoding is an implementation detail.
