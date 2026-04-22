# WP-V.1.3 Implementation Brief -- Default and Null Adapters

## Context

WP-V.1.1 defined the supporting types. WP-V.1.2 defined the `WorldVisualizationAdapter` and `SystemVisualizationAdapter` protocols. This work package provides the fallback adapters that enable graceful degradation when no specific adapter is registered for a world type or system type.

These adapters are used by the visualization registry (WP-V.1.4) as fallback targets. They also serve as reference implementations showing how to satisfy the protocols with minimal code.

### Predecessor State (After WP-V.1.2)

```
src/axis/visualization/
    __init__.py
    types.py                # All supporting types
    protocols.py            # WorldVisualizationAdapter, SystemVisualizationAdapter
```

### Architectural Decisions (Binding)

- **D4**: Default adapters for unknown types -- graceful degradation via `DefaultWorldVis` and `NullSystemVis`
- **D5**: Phase names are adapter-declared strings -- the Null adapter provides the minimal 2-phase set

### Reference Documents

- `docs/architecture/evolution/visualization-architecture.md` -- Section 11.1 (DefaultWorldVis), Section 11.2 (NullSystemVis)
- `docs/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.1.3

---

## Objective

Implement two fallback adapters:

1. `DefaultWorldVisualizationAdapter` -- rectangular grid with standard colors, no topology indicators. Used when no world adapter is registered for a `world_type`.
2. `NullSystemVisualizationAdapter` -- 2-phase lifecycle, percentage vitality, empty analysis/overlays. Used when no system adapter is registered for a `system_type`.

Both must satisfy their respective protocols from WP-V.1.2.

---

## Scope

### 1. DefaultWorldVisualizationAdapter

**File**: `src/axis/visualization/adapters/default_world.py`

Create directory `src/axis/visualization/adapters/` with `__init__.py`.

```python
"""Default world visualization adapter -- fallback for unknown world types.

Provides rectangular grid rendering with standard colors.
Behaves identically to a grid_2d adapter. Used when no specific
adapter is registered for a world type.
"""

from __future__ import annotations

from typing import Any

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.visualization.types import (
    CellColorConfig,
    CellLayout,
    CellShape,
    MetadataSection,
    TopologyIndicator,
)


class DefaultWorldVisualizationAdapter:
    """Fallback world adapter for unregistered world types.

    Renders a standard rectangular grid with the same color scheme
    as the grid_2d world. No topology indicators, no world metadata.
    """

    def cell_shape(self) -> CellShape:
        return CellShape.RECTANGULAR

    def cell_layout(
        self,
        grid_width: int,
        grid_height: int,
        canvas_width: float,
        canvas_height: float,
    ) -> CellLayout:
        cell_w = canvas_width / grid_width
        cell_h = canvas_height / grid_height

        polygons: dict[tuple[int, int], tuple[tuple[float, float], ...]] = {}
        centers: dict[tuple[int, int], tuple[float, float]] = {}
        bboxes: dict[tuple[int, int], tuple[float, float, float, float]] = {}

        for y in range(grid_height):
            for x in range(grid_width):
                x0 = x * cell_w
                y0 = y * cell_h
                polygons[(x, y)] = (
                    (x0, y0),
                    (x0 + cell_w, y0),
                    (x0 + cell_w, y0 + cell_h),
                    (x0, y0 + cell_h),
                )
                centers[(x, y)] = (x0 + cell_w / 2, y0 + cell_h / 2)
                bboxes[(x, y)] = (x0, y0, cell_w, cell_h)

        return CellLayout(
            cell_shape=CellShape.RECTANGULAR,
            grid_width=grid_width,
            grid_height=grid_height,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            cell_polygons=polygons,
            cell_centers=centers,
            cell_bounding_boxes=bboxes,
        )

    def cell_color_config(self) -> CellColorConfig:
        return CellColorConfig(
            obstacle_color=(0, 0, 0),
            empty_color=(224, 224, 224),
            resource_color_min=(232, 245, 233),
            resource_color_max=(46, 125, 50),
            agent_color=(33, 150, 243),
            agent_selected_color=(33, 150, 243),
            selection_border_color=(255, 160, 0),
            grid_line_color=(158, 158, 158),
        )

    def topology_indicators(
        self,
        world_snapshot: WorldSnapshot,
        world_data: dict[str, Any],
        cell_layout: CellLayout,
    ) -> list[TopologyIndicator]:
        return []

    def pixel_to_grid(
        self,
        pixel_x: float,
        pixel_y: float,
        cell_layout: CellLayout,
    ) -> Position | None:
        if cell_layout.grid_width == 0 or cell_layout.grid_height == 0:
            return None
        cell_w = cell_layout.canvas_width / cell_layout.grid_width
        cell_h = cell_layout.canvas_height / cell_layout.grid_height
        gx = int(pixel_x / cell_w)
        gy = int(pixel_y / cell_h)
        if 0 <= gx < cell_layout.grid_width and 0 <= gy < cell_layout.grid_height:
            return Position(x=gx, y=gy)
        return None

    def agent_marker_center(
        self,
        grid_position: Position,
        cell_layout: CellLayout,
    ) -> tuple[float, float]:
        return cell_layout.cell_centers[(grid_position.x, grid_position.y)]

    def world_metadata_sections(
        self,
        world_data: dict[str, Any],
    ) -> list[MetadataSection]:
        return []

    def format_world_info(
        self,
        world_data: dict[str, Any],
    ) -> str | None:
        return None
```

**Color values** (from architecture spec Section 11.1):

| Role | RGB | Visual |
|------|-----|--------|
| obstacle | `(0, 0, 0)` | Black |
| empty | `(224, 224, 224)` | Light gray |
| resource min | `(232, 245, 233)` | Pale green |
| resource max | `(46, 125, 50)` | Saturated green |
| agent | `(33, 150, 243)` | Blue |
| agent selected | `(33, 150, 243)` | Blue |
| selection border | `(255, 160, 0)` | Orange |
| grid lines | `(158, 158, 158)` | Gray |

### 2. NullSystemVisualizationAdapter

**File**: `src/axis/visualization/adapters/null_system.py`

```python
"""Null system visualization adapter -- fallback for unknown system types.

Provides the minimal 2-phase lifecycle with percentage vitality display.
No analysis sections, no overlays. Used when no specific adapter is
registered for a system type.
"""

from __future__ import annotations

from typing import Any

from axis.sdk.trace import BaseStepTrace
from axis.visualization.types import (
    AnalysisSection,
    OverlayData,
    OverlayTypeDeclaration,
)


class NullSystemVisualizationAdapter:
    """Fallback system adapter for unregistered system types.

    Renders the minimal visualization: 2-phase lifecycle,
    percentage vitality, no analysis, no overlays.
    """

    def phase_names(self) -> list[str]:
        return ["BEFORE", "AFTER_ACTION"]

    def vitality_label(self) -> str:
        return "Vitality"

    def format_vitality(
        self,
        value: float,
        system_data: dict[str, Any],
    ) -> str:
        return f"{value:.0%}"

    def build_step_analysis(
        self,
        step_trace: BaseStepTrace,
    ) -> list[AnalysisSection]:
        return []

    def build_overlays(
        self,
        step_trace: BaseStepTrace,
    ) -> list[OverlayData]:
        return []

    def available_overlay_types(self) -> list[OverlayTypeDeclaration]:
        return []
```

### 3. Adapters Package Init

**File**: `src/axis/visualization/adapters/__init__.py`

```python
"""Visualization adapter implementations -- defaults and concrete adapters."""
```

No exports -- consumers import directly from the specific module.

### 4. Design Notes

**DefaultWorldVisualizationAdapter** contains actual computation logic:
- `cell_layout()` computes rectangular grid geometry (this is the same computation that `Grid2DWorldVisualizationAdapter` will use in WP-V.2.1, so the grid_2d adapter can inherit from or delegate to this class)
- `pixel_to_grid()` does integer division for hit-testing
- `agent_marker_center()` looks up the cell center from `CellLayout`

**NullSystemVisualizationAdapter** is pure stubs -- every method returns an empty collection or a trivial value. It exists so the viewer can display base grid/agent rendering for any system, even without system-specific analysis.

---

## Out of Scope

Do **not** implement any of the following in WP-V.1.3:

- Visualization registry (`register_world_visualization`, `resolve_world_adapter`) -- WP-V.1.4
- Concrete world adapters (grid_2d, toroidal, signal_landscape) -- WP-V.2.x
- Concrete system adapters (System A, System B) -- WP-V.2.x
- Any PySide6 or rendering code
- Any modifications to existing SDK, framework, or world code

---

## Architectural Constraints

### 1. Protocol Satisfaction

Both adapters must satisfy their respective protocols. This means they implement every method from the protocol with matching signatures and return types. Structural subtyping -- they do not inherit from the protocol classes.

### 2. No Protocol Import

The adapter classes do **not** import `WorldVisualizationAdapter` or `SystemVisualizationAdapter`. They satisfy the protocols through structural subtyping only. Tests verify conformance.

### 3. No PySide6

Neither adapter imports PySide6. Colors are RGB tuples. Geometry is float tuples.

### 4. Reusability of DefaultWorldVisualizationAdapter

The `DefaultWorldVisualizationAdapter.cell_layout()` computation is the canonical rectangular grid layout. The `Grid2DWorldVisualizationAdapter` (WP-V.2.1) should reuse this code, either by:
- Inheriting from `DefaultWorldVisualizationAdapter` and overriding only what differs (nothing for grid_2d, in fact), or
- Delegating to a shared helper function

This WP does **not** need to anticipate the reuse mechanism -- just implement it cleanly so it can be reused.

### 5. Minimal Dependencies

- `DefaultWorldVisualizationAdapter` imports from `axis.sdk.position`, `axis.sdk.snapshot`, `axis.visualization.types`
- `NullSystemVisualizationAdapter` imports from `axis.sdk.trace`, `axis.visualization.types`
- No cross-imports between the two adapter files

---

## Testing Requirements

**File**: `tests/visualization/test_default_adapters.py` (new)

### DefaultWorldVisualizationAdapter tests

1. **`test_default_world_cell_shape`**:
   - Assert `adapter.cell_shape() == CellShape.RECTANGULAR`

2. **`test_default_world_cell_layout_dimensions`**:
   - Call `cell_layout(grid_width=3, grid_height=2, canvas_width=300.0, canvas_height=200.0)`
   - Assert `layout.grid_width == 3`, `layout.grid_height == 2`
   - Assert `layout.canvas_width == 300.0`, `layout.canvas_height == 200.0`

3. **`test_default_world_cell_layout_all_positions_present`**:
   - For a 3x2 grid, assert all 6 positions `(0,0)` through `(2,1)` exist in `cell_polygons`, `cell_centers`, `cell_bounding_boxes`

4. **`test_default_world_cell_layout_center_values`**:
   - For a 2x2 grid at 200x200 canvas:
   - Assert `cell_centers[(0, 0)] == (50.0, 50.0)`
   - Assert `cell_centers[(1, 1)] == (150.0, 150.0)`

5. **`test_default_world_cell_layout_polygon_vertices`**:
   - For cell `(0, 0)` in a 2x2 grid at 200x200 canvas:
   - Assert 4 vertices forming the rectangle `(0,0)-(100,0)-(100,100)-(0,100)`

6. **`test_default_world_cell_layout_bounding_box`**:
   - For cell `(1, 0)` in a 2x2 grid at 200x200:
   - Assert bbox `(100.0, 0.0, 100.0, 100.0)`

7. **`test_default_world_cell_color_config_values`**:
   - Assert `config.obstacle_color == (0, 0, 0)`
   - Assert `config.resource_color_max == (46, 125, 50)`
   - (Verify all 8 fields match the architecture spec values)

8. **`test_default_world_topology_indicators_empty`**:
   - Assert returns empty list (using a mock `WorldSnapshot` and empty `world_data`)

9. **`test_default_world_pixel_to_grid_inside`**:
   - 3x2 grid at 300x200. Click at `(150, 50)` should return `Position(x=1, y=0)`

10. **`test_default_world_pixel_to_grid_outside`**:
    - Click at `(-10, 50)` or `(350, 50)` should return `None`

11. **`test_default_world_pixel_to_grid_corner`**:
    - Click at `(0, 0)` should return `Position(x=0, y=0)`

12. **`test_default_world_agent_marker_center`**:
    - For `Position(x=1, y=0)` in a 2x2 grid at 200x200:
    - Assert returns `(150.0, 50.0)` (center of cell (1,0))

13. **`test_default_world_metadata_sections_empty`**:
    - Assert returns empty list

14. **`test_default_world_format_world_info_none`**:
    - Assert returns `None`

### NullSystemVisualizationAdapter tests

15. **`test_null_system_phase_names`**:
    - Assert `adapter.phase_names() == ["BEFORE", "AFTER_ACTION"]`

16. **`test_null_system_vitality_label`**:
    - Assert `adapter.vitality_label() == "Vitality"`

17. **`test_null_system_format_vitality`**:
    - Assert `adapter.format_vitality(0.75, {}) == "75%"`
    - Assert `adapter.format_vitality(1.0, {}) == "100%"`
    - Assert `adapter.format_vitality(0.0, {}) == "0%"`

18. **`test_null_system_build_step_analysis_empty`**:
    - Construct a minimal `BaseStepTrace` fixture
    - Assert `adapter.build_step_analysis(trace) == []`

19. **`test_null_system_build_overlays_empty`**:
    - Assert `adapter.build_overlays(trace) == []`

20. **`test_null_system_available_overlay_types_empty`**:
    - Assert `adapter.available_overlay_types() == []`

### Protocol conformance tests

21. **`test_default_world_satisfies_protocol`**:
    - Verify `DefaultWorldVisualizationAdapter` has all 8 protocol methods (via `hasattr` checks)

22. **`test_null_system_satisfies_protocol`**:
    - Verify `NullSystemVisualizationAdapter` has all 6 protocol methods (via `hasattr` checks)

### Existing tests

All existing tests must continue to pass.

---

## Implementation Style

- Python 3.11+
- Plain classes (no Pydantic models for the adapters themselves -- they are stateless service objects)
- No inheritance from protocol classes
- Docstrings on class and methods
- Inline geometry computation (no helper functions for the simple rectangular case)

---

## Expected Deliverable

1. `src/axis/visualization/adapters/__init__.py`
2. `src/axis/visualization/adapters/default_world.py` with `DefaultWorldVisualizationAdapter`
3. `src/axis/visualization/adapters/null_system.py` with `NullSystemVisualizationAdapter`
4. `tests/visualization/test_default_adapters.py` with all tests
5. Confirmation that all existing tests still pass

---

## Expected File Structure

After WP-V.1.3:

```
src/axis/visualization/
    __init__.py                          # UNCHANGED
    types.py                             # UNCHANGED (from WP-V.1.1)
    protocols.py                         # UNCHANGED (from WP-V.1.2)
    adapters/
        __init__.py                      # NEW
        default_world.py                 # NEW
        null_system.py                   # NEW

tests/visualization/
    __init__.py                          # UNCHANGED
    test_types.py                        # UNCHANGED (from WP-V.1.1)
    test_protocols.py                    # UNCHANGED (from WP-V.1.2)
    test_default_adapters.py             # NEW
```

---

## Important Final Constraint

The `DefaultWorldVisualizationAdapter` is the only adapter in Phase V-1 with actual computation logic (rectangular grid layout and hit-testing). Keep this logic simple and correct -- it is the reference implementation that concrete adapters in WP-V.2.x will build upon. The `NullSystemVisualizationAdapter` is trivial: every method returns an empty list, a default label, or a simple format string.

Together, these two adapters must be sufficient for the base visualization layer to render a grid with an agent for any unknown world/system combination. No analysis panels, no overlays, no topology indicators -- just a working grid view.
