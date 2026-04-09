# WP-V.2.1 Implementation Brief -- Grid2D World Adapter

## Context

Phase V-1 established the supporting types, adapter protocols, fallback adapters, and the visualization registry. Phase V-2 implements the concrete adapters for all existing world types and systems. All WPs in this phase can be parallelized.

This work package implements the Grid2D world visualization adapter -- the baseline rectangular grid adapter that defines the standard cell geometry, color scheme, and hit-testing for bounded rectangular grids.

### Predecessor State (After Phase V-1)

```
src/axis/visualization/
    types.py                             # Supporting types
    protocols.py                         # Adapter protocols
    registry.py                          # Registration/resolution
    adapters/
        default_world.py                 # DefaultWorldVisualizationAdapter
        null_system.py                   # NullSystemVisualizationAdapter
```

The `DefaultWorldVisualizationAdapter` from WP-V.1.3 already implements the full rectangular grid layout. The Grid2D adapter has identical behavior -- it exists as a named, registered adapter so that `resolve_world_adapter("grid_2d", ...)` returns a purpose-specific adapter rather than the generic fallback.

### Reference Documents

- `docs/architecture/evolution/visualization-architecture.md` -- Section 11.1 (Grid2DWorldVisualizationAdapter)
- `docs/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.2.1

---

## Objective

Implement `Grid2DWorldVisualizationAdapter` and register it with the visualization registry as `"grid_2d"`.

---

## Scope

### 1. Grid2DWorldVisualizationAdapter

**File**: `src/axis/world/grid_2d/visualization.py` (new)

The Grid2D adapter is functionally identical to `DefaultWorldVisualizationAdapter`. The cleanest approach is to **inherit from it** and register under the `"grid_2d"` key:

```python
"""Grid2D world visualization adapter.

Rectangular bounded grid with standard green resource gradient.
Inherits all behavior from DefaultWorldVisualizationAdapter --
the grid_2d world is the baseline that the default was modeled on.
"""

from __future__ import annotations

from axis.visualization.adapters.default_world import DefaultWorldVisualizationAdapter


class Grid2DWorldVisualizationAdapter(DefaultWorldVisualizationAdapter):
    """Visualization adapter for the grid_2d world type.

    Identical to the default adapter -- rectangular cells, standard
    colors, no topology indicators. Exists as a named adapter so
    that grid_2d worlds are resolved through registration rather
    than fallback.
    """

    pass
```

**Design rationale**: The architecture spec (Section 11.1) states that `DefaultWorldVisualizationAdapter` "behaves identically to the grid_2d adapter with standard colors." Inheritance avoids code duplication. If the grid_2d adapter needs to diverge in the future (e.g., showing regen-eligible indicators), override individual methods.

**Alternative considered**: Composition (delegation) via a shared helper. Rejected because inheritance is simpler here -- the default adapter was explicitly designed as the grid_2d baseline.

### 2. Registration

**Same file**: `src/axis/world/grid_2d/visualization.py`

```python
from axis.visualization.registry import register_world_visualization

def _grid_2d_vis_factory(world_config: dict[str, Any]) -> Grid2DWorldVisualizationAdapter:
    return Grid2DWorldVisualizationAdapter()

register_world_visualization("grid_2d", _grid_2d_vis_factory)
```

The factory ignores `world_config` since the grid_2d adapter has no configuration-dependent behavior. The factory is a named function (not a lambda) for debuggability.

**Import**: Add `from typing import Any` for the factory signature.

### 3. Registration Trigger

The registration call executes at module import time. The visualization launch code (WP-V.4.4) must import `axis.world.grid_2d.visualization` to trigger registration. This is identical to how `axis.world.registry` auto-registers world factories.

---

## Out of Scope

- Toroidal world adapter (WP-V.2.2)
- Signal landscape world adapter (WP-V.2.3)
- System adapters (WP-V.2.4, WP-V.2.5)
- Any PySide6 or rendering code
- Modifications to `DefaultWorldVisualizationAdapter`

---

## Architectural Constraints

### 1. Placement in World Package

The adapter lives in `src/axis/world/grid_2d/visualization.py`, keeping visualization code co-located with the world type it serves. This mirrors the planned pattern for system adapters in `src/axis/systems/system_a/visualization.py`.

### 2. Satisfies WorldVisualizationAdapter Protocol

`Grid2DWorldVisualizationAdapter` satisfies `WorldVisualizationAdapter` through structural subtyping (inherited from `DefaultWorldVisualizationAdapter`).

### 3. No PySide6 Imports

The adapter returns structured data only.

---

## Testing Requirements

**File**: `tests/visualization/test_grid2d_world_adapter.py` (new)

1. **`test_grid2d_adapter_is_default_subclass`**:
   - Assert `isinstance(adapter, DefaultWorldVisualizationAdapter)`

2. **`test_grid2d_adapter_cell_shape`**:
   - Assert `adapter.cell_shape() == CellShape.RECTANGULAR`

3. **`test_grid2d_adapter_cell_layout`**:
   - Compute layout for 3x3 grid at 300x300 canvas
   - Assert all 9 positions in `cell_centers`
   - Assert `cell_centers[(1, 1)] == (150.0, 150.0)`

4. **`test_grid2d_adapter_color_config`**:
   - Assert standard color values match spec (obstacle black, resource green gradient, etc.)

5. **`test_grid2d_adapter_topology_empty`**:
   - Assert `topology_indicators(...)` returns `[]`

6. **`test_grid2d_adapter_pixel_to_grid`**:
   - Assert correct conversion for interior click
   - Assert `None` for out-of-bounds click

7. **`test_grid2d_adapter_format_world_info_none`**:
   - Assert `format_world_info({})` returns `None`

8. **`test_grid2d_adapter_metadata_sections_empty`**:
   - Assert `world_metadata_sections({})` returns `[]`

### Registration test

9. **`test_grid2d_registration`**:
   - Import `axis.world.grid_2d.visualization` (triggers registration)
   - Call `resolve_world_adapter("grid_2d", {})`
   - Assert returned adapter is a `Grid2DWorldVisualizationAdapter`

   **Note**: Use the `_clear_registries` fixture, then re-import to test cleanly. Alternatively, test in a separate test that imports the module and checks `registered_world_visualizations()`.

### Existing tests

All existing tests must continue to pass.

---

## Expected Deliverable

1. `src/axis/world/grid_2d/visualization.py` with `Grid2DWorldVisualizationAdapter` + registration
2. `tests/visualization/test_grid2d_world_adapter.py`
3. Confirmation that all existing tests still pass

---

## Expected File Structure

```
src/axis/world/grid_2d/
    __init__.py                          # UNCHANGED
    model.py                             # UNCHANGED
    dynamics.py                          # UNCHANGED
    factory.py                           # UNCHANGED
    visualization.py                     # NEW

tests/visualization/
    test_grid2d_world_adapter.py         # NEW
```

---

## Important Final Constraint

This is the simplest adapter in Phase V-2. The class body is literally `pass` -- all behavior is inherited. The value is in the explicit registration under `"grid_2d"` so the resolver returns a purpose-specific type rather than the anonymous default fallback.
