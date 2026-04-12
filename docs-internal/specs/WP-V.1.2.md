# WP-V.1.2 Implementation Brief -- Adapter Protocols

## Context

WP-V.1.1 defined all supporting types (`CellShape`, `CellLayout`, `CellColorConfig`, `TopologyIndicator`, `AnalysisSection`, `OverlayData`, etc.). This work package defines the two adapter protocols that concrete adapters must satisfy.

The protocols are the core contracts of the three-tier visualization architecture. They define what the base layer expects from world adapters (Tier 2) and system adapters (Tier 3). Both protocols return only the structured data types from WP-V.1.1 -- no PySide6 types.

### Predecessor State (After WP-V.1.1)

```
src/axis/visualization/
    __init__.py
    types.py            # CellShape, CellLayout, CellColorConfig, TopologyIndicator,
                        # AnalysisRow, AnalysisSection, MetadataSection,
                        # OverlayTypeDeclaration, OverlayItem, OverlayData
```

### Architectural Decisions (Binding)

- **D1**: Adapters return structured data, not QPainter commands
- **D3**: `CellLayout` bridges world geometry and system overlays
- **D8**: World and system adapters are independent -- neither imports the other

### Reference Documents

- `docs/architecture/evolution/visualization-architecture.md` -- Section 4 (WorldVisualizationAdapter), Section 5 (SystemVisualizationAdapter)
- `docs/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.1.2

---

## Objective

Define two `typing.Protocol` classes:

1. `WorldVisualizationAdapter` -- the contract for world-specific rendering (cell geometry, colors, topology indicators, hit-testing)
2. `SystemVisualizationAdapter` -- the contract for system-specific analysis and overlays (phase names, vitality display, step analysis, debug overlays)

These are structural subtyping protocols -- concrete adapters satisfy them by implementing all methods with matching signatures, without inheriting from the protocol.

---

## Scope

### 1. WorldVisualizationAdapter Protocol

**File**: `src/axis/visualization/protocols.py`

```python
from __future__ import annotations

from typing import Any, Protocol

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseStepTrace
from axis.visualization.types import (
    AnalysisSection,
    CellColorConfig,
    CellLayout,
    CellShape,
    MetadataSection,
    OverlayData,
    OverlayTypeDeclaration,
    TopologyIndicator,
)


class WorldVisualizationAdapter(Protocol):
    """Contract for world-specific visualization rendering.

    Registered per world_type. The base layer calls these methods to
    obtain cell geometry, colors, topology indicators, and hit-testing
    logic. All return types are structured data -- no PySide6 types.

    The base layer caches CellLayout (recomputed only on canvas resize)
    and CellColorConfig (computed once at adapter init).
    """

    # ── Cell geometry ────────────────────────────────────────

    def cell_shape(self) -> CellShape:
        """RECTANGULAR or HEXAGONAL.
        Determines which geometry backend CellLayout uses."""
        ...

    def cell_layout(
        self,
        grid_width: int,
        grid_height: int,
        canvas_width: float,
        canvas_height: float,
    ) -> CellLayout:
        """Map every grid position to pixel polygon.
        Called once per canvas resize, cached by the base layer."""
        ...

    # ── Cell coloring ────────────────────────────────────────

    def cell_color_config(self) -> CellColorConfig:
        """Color rules for cell types. Called once at adapter init."""
        ...

    # ── Topology ─────────────────────────────────────────────

    def topology_indicators(
        self,
        world_snapshot: WorldSnapshot,
        world_data: dict[str, Any],
        cell_layout: CellLayout,
    ) -> list[TopologyIndicator]:
        """Visual cues for world topology.
        Wrap edges for toroidal, hotspot markers for signal_landscape.
        Returns empty list for bounded worlds with no indicators."""
        ...

    # ── Hit testing ──────────────────────────────────────────

    def pixel_to_grid(
        self,
        pixel_x: float,
        pixel_y: float,
        cell_layout: CellLayout,
    ) -> Position | None:
        """Convert pixel click to grid position.
        Returns None if the click is outside the grid.
        Different for rectangular vs hexagonal grids."""
        ...

    # ── Agent placement ──────────────────────────────────────

    def agent_marker_center(
        self,
        grid_position: Position,
        cell_layout: CellLayout,
    ) -> tuple[float, float]:
        """Pixel center for the agent marker in the given cell."""
        ...

    # ── World metadata display ───────────────────────────────

    def world_metadata_sections(
        self,
        world_data: dict[str, Any],
    ) -> list[MetadataSection]:
        """Optional world-specific metadata for the detail panel.
        E.g., hotspot list for signal_landscape."""
        ...

    # ── World status line ────────────────────────────────────

    def format_world_info(
        self,
        world_data: dict[str, Any],
    ) -> str | None:
        """Optional one-line world status for the status bar.
        E.g., '3 hotspots active, drift=0.5' for signal_landscape.
        Returns None if no world-specific status is needed."""
        ...
```

**Method summary**:

| Method | Called | Returns | Cached? |
|--------|--------|---------|---------|
| `cell_shape()` | Once at init | `CellShape` | Yes |
| `cell_layout(...)` | On canvas resize | `CellLayout` | Yes |
| `cell_color_config()` | Once at init | `CellColorConfig` | Yes |
| `topology_indicators(...)` | Every frame | `list[TopologyIndicator]` | No |
| `pixel_to_grid(...)` | On mouse click | `Position \| None` | No |
| `agent_marker_center(...)` | Every frame | `tuple[float, float]` | No |
| `world_metadata_sections(...)` | Every frame | `list[MetadataSection]` | No |
| `format_world_info(...)` | Every frame | `str \| None` | No |

### 2. SystemVisualizationAdapter Protocol

**Same file**: `src/axis/visualization/protocols.py`

```python
class SystemVisualizationAdapter(Protocol):
    """Contract for system-specific visualization analysis and overlays.

    Registered per system_type. The base layer calls these methods to
    obtain phase names, vitality formatting, step analysis sections,
    and debug overlay data. All return types are structured data.

    System adapters read system_data from BaseStepTrace to produce
    their outputs. They never access world state directly.
    """

    # ── Phase navigation ─────────────────────────────────────

    def phase_names(self) -> list[str]:
        """Ordered phase names for this system's step lifecycle.
        Must start with 'BEFORE' and end with 'AFTER_ACTION'.
        System A: ['BEFORE', 'AFTER_REGEN', 'AFTER_ACTION']
        System B: ['BEFORE', 'AFTER_ACTION']"""
        ...

    # ── Vitality display ─────────────────────────────────────

    def vitality_label(self) -> str:
        """Label for the vitality metric. E.g., 'Energy'."""
        ...

    def format_vitality(
        self,
        value: float,
        system_data: dict[str, Any],
    ) -> str:
        """Format vitality for display.
        System A: '3.45 / 5.00' (energy / max_energy)."""
        ...

    # ── Step analysis ────────────────────────────────────────

    def build_step_analysis(
        self,
        step_trace: BaseStepTrace,
    ) -> list[AnalysisSection]:
        """Build structured analysis sections from system_data.
        Displayed in StepAnalysisPanel. Always visible (not gated
        by overlay checkboxes)."""
        ...

    # ── Debug overlays ───────────────────────────────────────

    def build_overlays(
        self,
        step_trace: BaseStepTrace,
    ) -> list[OverlayData]:
        """Build structured overlay data from system_data.
        The base OverlayRenderer translates these to QPainter
        calls using the world adapter's CellLayout."""
        ...

    # ── Overlay declarations ─────────────────────────────────

    def available_overlay_types(self) -> list[OverlayTypeDeclaration]:
        """Declare available overlay types for the control panel.
        Each declaration becomes a checkbox in DebugOverlayPanel."""
        ...
```

**Method summary**:

| Method | Called | Returns | Cached? |
|--------|--------|---------|---------|
| `phase_names()` | Once at init | `list[str]` | Yes |
| `vitality_label()` | Once at init | `str` | Yes |
| `format_vitality(...)` | Every frame | `str` | No |
| `build_step_analysis(...)` | Every frame | `list[AnalysisSection]` | No |
| `build_overlays(...)` | Every frame | `list[OverlayData]` | No |
| `available_overlay_types()` | Once at init | `list[OverlayTypeDeclaration]` | Yes |

### 3. Key Design Constraints on the Protocols

**Independence**: `WorldVisualizationAdapter` does not reference `SystemVisualizationAdapter` and vice versa. Neither protocol imports the other. The base layer mediates all interaction.

**No PySide6**: Neither protocol imports or returns anything from PySide6. Colors are RGB integer tuples. Positions are float tuples or `Position` models.

**`world_data` parameter**: Several world adapter methods accept `world_data: dict[str, Any]`. This is the per-step metadata from `BaseStepTrace.world_data`, populated by WP-V.0.3.

**`system_data` access**: System adapter methods receive `BaseStepTrace` which contains `system_data`. The adapter reads what it needs from the opaque dict.

### 4. Module Docstring

```python
"""Visualization adapter protocols.

Defines the contracts for world-specific (Tier 2) and system-specific
(Tier 3) visualization adapters. Both protocols return structured data
types defined in axis.visualization.types -- no PySide6 dependencies.

Concrete adapters satisfy these protocols through structural subtyping
(duck typing). They do not inherit from the protocol classes.
"""
```

---

## Out of Scope

Do **not** implement any of the following in WP-V.1.2:

- Concrete adapter implementations (grid_2d, toroidal, signal_landscape, System A/B) -- WP-V.2.x
- Default/null fallback adapters -- WP-V.1.3
- Visualization registry -- WP-V.1.4
- Any rendering or UI code
- `@runtime_checkable` decorator -- not needed; the registry handles type resolution (WP-V.1.4). Add it only if explicitly needed for `isinstance()` checks later.

---

## Architectural Constraints

### 1. Structural Subtyping

Both protocols use `typing.Protocol`. Concrete adapters satisfy the protocol through structural subtyping -- they implement all methods with matching signatures without inheriting from the protocol class:

```python
# This class satisfies WorldVisualizationAdapter without inheriting from it:
class Grid2DWorldVisualizationAdapter:
    def cell_shape(self) -> CellShape: ...
    def cell_layout(self, ...) -> CellLayout: ...
    # ... all other methods
```

### 2. No Abstract Methods, No Registration Logic

The protocols define the contract only. They do not contain default implementations, abstract method decorators, or registration logic. Those concerns belong to WP-V.1.3 (defaults) and WP-V.1.4 (registry).

### 3. Imports from SDK and Visualization Types Only

The protocols module imports from:
- `axis.sdk.position` -- `Position`
- `axis.sdk.snapshot` -- `WorldSnapshot`
- `axis.sdk.trace` -- `BaseStepTrace`
- `axis.visualization.types` -- all supporting types

No other imports. No framework imports. No world imports.

---

## Testing Requirements

**File**: `tests/visualization/test_protocols.py` (new)

### Protocol conformance tests using minimal mock adapters

Create minimal mock adapter classes that implement all methods of each protocol, returning trivial values. Verify that they satisfy the protocol.

1. **`test_mock_world_adapter_satisfies_protocol`**:
   - Define a `_MockWorldAdapter` class with all 8 methods returning stubs (e.g., `cell_shape()` returns `CellShape.RECTANGULAR`, `cell_layout()` returns a minimal `CellLayout`, etc.)
   - Assert the class instance has all protocol methods (use `hasattr()` or call each method)

2. **`test_mock_system_adapter_satisfies_protocol`**:
   - Define a `_MockSystemAdapter` class with all 6 methods returning stubs
   - Assert the class instance has all protocol methods

3. **`test_world_adapter_method_signatures`**:
   - Verify each method on the mock adapter returns the expected type:
     - `cell_shape()` returns `CellShape`
     - `cell_layout(...)` returns `CellLayout`
     - `cell_color_config()` returns `CellColorConfig`
     - `topology_indicators(...)` returns `list[TopologyIndicator]`
     - `pixel_to_grid(...)` returns `Position | None`
     - `agent_marker_center(...)` returns `tuple[float, float]`
     - `world_metadata_sections(...)` returns `list[MetadataSection]`
     - `format_world_info(...)` returns `str | None`

4. **`test_system_adapter_method_signatures`**:
   - Verify each method on the mock adapter returns the expected type:
     - `phase_names()` returns `list[str]`
     - `vitality_label()` returns `str`
     - `format_vitality(...)` returns `str`
     - `build_step_analysis(...)` returns `list[AnalysisSection]`
     - `build_overlays(...)` returns `list[OverlayData]`
     - `available_overlay_types()` returns `list[OverlayTypeDeclaration]`

5. **`test_world_adapter_independence_from_system`**:
   - Verify that `WorldVisualizationAdapter` can be imported without importing `SystemVisualizationAdapter` methods (both are in the same module, but the key point is no cross-references between the two protocol classes)

6. **`test_protocols_importable`**:
   - `from axis.visualization.protocols import WorldVisualizationAdapter, SystemVisualizationAdapter`
   - Assert both are accessible

### Mock adapter fixtures

The mock adapters created for these tests should be reusable by later WPs (WP-V.1.4 registry tests, WP-V.3.4 view model builder tests). Consider placing them in a shared test fixtures module `tests/visualization/conftest.py` or `tests/builders/mock_adapters.py`, but only if convenient. At minimum they must exist in the test file.

### Existing tests

All existing tests must continue to pass.

---

## Implementation Style

- Python 3.11+
- `typing.Protocol` classes with `...` method bodies
- Method signatures exactly match the architecture spec (Sections 4 and 5)
- Clear docstrings explaining each method's purpose, call timing, and return semantics
- Section comments separating method groups (matching architecture spec style)

---

## Expected Deliverable

1. `src/axis/visualization/protocols.py` with `WorldVisualizationAdapter` and `SystemVisualizationAdapter`
2. `tests/visualization/test_protocols.py` with protocol conformance tests
3. Confirmation that all existing tests still pass

---

## Expected File Structure

After WP-V.1.2:

```
src/axis/visualization/
    __init__.py                     # UNCHANGED
    types.py                        # UNCHANGED (from WP-V.1.1)
    protocols.py                    # NEW

tests/visualization/
    __init__.py                     # UNCHANGED (from WP-V.1.1)
    test_types.py                   # UNCHANGED (from WP-V.1.1)
    test_protocols.py               # NEW
```

---

## Important Final Constraint

This module defines two protocol classes totaling approximately 8 + 6 = 14 method signatures. There is no implementation logic -- only method stubs with `...` bodies. The module should be approximately 100-130 lines including docstrings and comments.

The protocols are the **stable contracts** of the visualization system. Once concrete adapters exist (WP-V.2.x), changing a protocol method signature requires updating all adapters. Design the signatures carefully; the architecture spec (Sections 4 and 5) has already been reviewed and approved by the user.
