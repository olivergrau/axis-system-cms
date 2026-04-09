# AXIS v0.2.0 -- Three-Tier Visualization Architecture

**Version**: v0.2.0 \
**Extends**: Section 9 of architectural-vision-v0.2.0.md \
**Supersedes**: WP-4.1 through WP-4.4 of modular-architecture-roadmap.md \
**Status**: Proposed

---

## 1. Purpose and Scope

### 1.1 Why a three-tier model

The architectural vision (Section 9) defined a two-layer visualization
model: a **generic base layer** for grid rendering, and a
**SystemVisualizationAdapter** for system-specific analysis panels and
overlays. That model assumed all worlds are rectangular grids with
identical visual semantics -- green resource gradient, rectangular
hit-testing, bounded edges.

With three world types now implemented, each has distinct visual needs:

| World type | Visual semantics |
|------------|-----------------|
| `grid_2d` | Bounded rectangular cells, green resource gradient, walls block movement |
| `toroidal` | Same cells but edges wrap -- needs visual indicators for wraparound |
| `signal_landscape` | Heatmap coloring for signal strength, drifting hotspot markers, non-extractive resources |

A hexagonal or otherwise non-rectangular world type is a foreseeable
future addition. The cell rendering, agent placement, hit-testing, and
color palette are all world-specific concerns that cannot live in a
single hard-coded `GridWidget`.

This document introduces a **WorldVisualizationAdapter** parallel to the
SystemVisualizationAdapter, creating a three-tier architecture:

```
Tier 1: Base Layer           -- independent of world AND system
Tier 2: World Adapter        -- world-specific rendering
Tier 3: System Adapter       -- system-specific analysis and overlays
```

### 1.2 What this supersedes

This document supersedes the visualization work packages WP-4.1 through
WP-4.4 as defined in `modular-architecture-roadmap.md`. Those work
packages are revised in Section 15 of this document. The SystemVisualization-
Adapter protocol from the roadmap is preserved and refined; the
WorldVisualizationAdapter is new.

### 1.3 Scope

- **Replay viewer only**: read-only, operates on persisted data.
- **PySide6 implementation**: but adapter protocols are UI-framework-
  agnostic (structured data, no `QPainter` or `QColor` in protocols).
- **Desktop application**: same launch model as v0.1.0.

---

## 2. Architecture Overview

### 2.1 Layer diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Tier 1: Base Layer                         │
│                    axis/visualization/                           │
│                                                                 │
│  Replay infrastructure:                                         │
│    ReplayAccessService, SnapshotResolver, ViewerState,          │
│    PlaybackController, SessionController                        │
│                                                                 │
│  UI components (PySide6):                                       │
│    CanvasWidget, OverlayRenderer, StatusPanel,                  │
│    StepAnalysisPanel, DetailPanel, ReplayControlsPanel,         │
│    OverlayPanel, MainWindow                                │
│                                                                 │
│  ViewModelBuilder (delegates to both adapters)                  │
│  ViewerFrameViewModel (composite output)                        │
│                                                                 │
└──────────┬──────────────────────────────────┬───────────────────┘
           │                                  │
           │  cell geometry,                  │  step analysis,
           │  cell colors,                    │  overlay data,
           │  topology indicators,            │  phase names,
           │  hit-testing                     │  vitality format
           │                                  │
┌──────────▼──────────────┐     ┌─────────────▼───────────────────┐
│ Tier 2: World           │     │ Tier 3: System                  │
│ Visualization Adapter   │     │ Visualization Adapter           │
│                         │     │                                 │
│ Registered per          │     │ Registered per                  │
│ world_type              │     │ system_type                     │
│                         │     │                                 │
│ Implementations:        │     │ Implementations:                │
│   Grid2DWorldVis        │     │   SystemAVis                    │
│   ToroidalWorldVis      │     │   SystemBVis                    │
│   SignalLandscapeVis    │     │   NullSystemVis (default)       │
│   DefaultWorldVis       │     │                                 │
└─────────────────────────┘     └─────────────────────────────────┘
```

### 2.2 Key architectural constraint

**Tier 2 and Tier 3 are independent of each other.** The base layer
mediates all interaction. System adapters produce structured overlay
DATA. World adapters produce cell GEOMETRY. The base layer renders
overlays by combining both through the `CellLayout` bridge object.

### 2.3 Dependency direction

```
SDK visualization types                  -- depends on nothing
   (AnalysisSection, OverlayData,
    CellLayout, CellColorConfig, ...)
          ↑                 ↑
World Vis Adapters    System Vis Adapters  -- depend on SDK types only
          ↑                 ↑
       Base Layer                         -- depends on SDK types,
                                             uses both adapters
```

No adapter imports the other adapter. No adapter imports PySide6.

---

## 3. Data Flow Pipeline

```
Repository (filesystem)
      │
      ▼
ReplayAccessService
      │  loads BaseEpisodeTrace
      │  reads system_type, world_type
      │
      ├──► resolve_world_adapter(world_type, world_config)
      │        → WorldVisualizationAdapter
      │
      ├──► resolve_system_adapter(system_type)
      │        → SystemVisualizationAdapter
      │
      ▼
SnapshotResolver
      │  resolve(episode, step_index, phase_index)
      │  phase_names from system adapter
      │  maps phase_index → world_before / intermediate / world_after
      │
      ▼
ViewModelBuilder
      │
      ├── world adapter:
      │     cell_color_config()           → CellColorConfig
      │     cell_layout(grid, canvas)     → CellLayout
      │     topology_indicators(snap, wd) → list[TopologyIndicator]
      │     world_metadata_sections(wd)   → list[MetadataSection]
      │     format_world_info(wd)         → str | None
      │
      ├── system adapter:
      │     vitality_label()              → str
      │     format_vitality(val, sd)      → str
      │     build_step_analysis(step)     → list[AnalysisSection]
      │     build_overlays(step)          → list[OverlayData]
      │
      ├── base projections:
      │     grid cells (using CellColorConfig)
      │     agent position
      │     status bar (vitality label from system adapter,
      │                 world info from world adapter)
      │
      ▼
ViewerFrameViewModel (composite)
      │
      ▼
Widgets (PySide6 rendering)
      │
      ├── CanvasWidget:
      │     1. draw cell backgrounds (CellLayout polygons + CellColorConfig)
      │     2. draw grid lines along polygon edges
      │     3. draw topology indicators (wrap edges, hotspot markers)
      │     4. draw selection highlight (CellLayout polygon for selected cell)
      │     5. draw agent marker (CellLayout.cell_center for agent position)
      │     6. OverlayRenderer.render(overlay_data, cell_layout)
      │
      ├── StepAnalysisPanel: renders list[AnalysisSection] as formatted text
      ├── StatusPanel: vitality with adapter label, world info line
      ├── DetailPanel: cell info + world metadata sections
      └── OverlayPanel: checkboxes from OverlayTypeDeclaration list
```

---

## 4. WorldVisualizationAdapter Protocol

All return types are structured data (Pydantic models or plain types).
No PySide6 types appear in the protocol.

```python
class WorldVisualizationAdapter(Protocol):

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

---

## 5. SystemVisualizationAdapter Protocol

Refined from the roadmap's WP-4.2 definition. Key refinement:
`build_overlays()` returns structured `OverlayData`, not drawing
commands.

```python
class SystemVisualizationAdapter(Protocol):

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
        Each declaration becomes a checkbox in OverlayPanel."""
        ...
```

---

## 6. Supporting Types

All types are UI-framework-agnostic. No Qt imports. Frozen Pydantic
models where applicable.

### 6.1 CellShape

```python
class CellShape(str, Enum):
    RECTANGULAR = "rectangular"
    HEXAGONAL = "hexagonal"
```

### 6.2 CellLayout

The central bridge between world geometry and system overlays.
Produced by the world adapter, consumed by the canvas and overlay
renderer.

```python
class CellLayout(BaseModel):
    """Maps grid positions to pixel geometry."""

    model_config = ConfigDict(frozen=True)

    cell_shape: CellShape
    grid_width: int
    grid_height: int
    canvas_width: float
    canvas_height: float

    # position (x, y) → polygon vertices, pixel coordinates
    cell_polygons: dict[tuple[int, int], tuple[tuple[float, float], ...]]

    # position (x, y) → center point, pixel coordinates
    cell_centers: dict[tuple[int, int], tuple[float, float]]

    # position (x, y) → bounding box (x, y, width, height)
    cell_bounding_boxes: dict[tuple[int, int], tuple[float, float, float, float]]
```

For rectangular grids this is trivially computed:
```
cell_w = canvas_width / grid_width
cell_h = canvas_height / grid_height
cell_centers[(x, y)] = (x * cell_w + cell_w/2, y * cell_h + cell_h/2)
cell_polygons[(x, y)] = four rectangle corners
```

For hexagonal grids the math changes but the contract is identical.
System overlays work without modification on any geometry.

### 6.3 CellColorConfig

```python
class CellColorConfig(BaseModel):
    """Color rules for cell rendering. Colors are RGB tuples (0-255)."""

    model_config = ConfigDict(frozen=True)

    obstacle_color: tuple[int, int, int]
    empty_color: tuple[int, int, int]
    resource_color_min: tuple[int, int, int]  # resource_value = 0.0
    resource_color_max: tuple[int, int, int]  # resource_value = 1.0
    agent_color: tuple[int, int, int]
    agent_selected_color: tuple[int, int, int]
    selection_border_color: tuple[int, int, int]
    grid_line_color: tuple[int, int, int]
```

The base renderer uses linear RGB interpolation between
`resource_color_min` and `resource_color_max` based on
`CellView.resource_value`.

### 6.4 TopologyIndicator

```python
class TopologyIndicator(BaseModel):
    """A visual cue for world topology, rendered on the canvas."""

    model_config = ConfigDict(frozen=True)

    indicator_type: str
        # "wrap_edge" -- dashed line at grid edge indicating wraparound
        # "hotspot_center" -- marker at a hotspot position
    position: tuple[float, float]  # pixel coordinates
    data: dict[str, Any]
        # type-specific params:
        #   wrap_edge: edge ("left"|"right"|"top"|"bottom"), style
        #   hotspot_center: radius_pixels, intensity, label
```

### 6.5 AnalysisSection and AnalysisRow

```python
class AnalysisRow(BaseModel):
    """A labeled value in an analysis section."""

    model_config = ConfigDict(frozen=True)

    label: str
    value: str
    sub_rows: tuple[AnalysisRow, ...] | None = None


class AnalysisSection(BaseModel):
    """One titled section of the step analysis panel."""

    model_config = ConfigDict(frozen=True)

    title: str
    rows: tuple[AnalysisRow, ...]
```

### 6.6 OverlayTypeDeclaration

```python
class OverlayTypeDeclaration(BaseModel):
    """Declares one overlay type for the control panel."""

    model_config = ConfigDict(frozen=True)

    key: str           # unique ID, e.g. "action_preference"
    label: str         # checkbox label, e.g. "Action Preference"
    description: str   # tooltip text
```

### 6.7 OverlayData and OverlayItem

```python
class OverlayItem(BaseModel):
    """A single overlay element to render at a grid position."""

    model_config = ConfigDict(frozen=True)

    item_type: str
        # Known types (closed set rendered by OverlayRenderer):
        # "direction_arrow" -- line from cell center in a direction
        # "center_dot"      -- filled dot at cell center
        # "center_ring"     -- ring at cell center
        # "bar_chart"       -- mini bar chart within cell bounds
        # "diamond_marker"  -- rotated square at cell center
        # "neighbor_dot"    -- dot at a specific cell
        # "radius_circle"   -- circle at cell center with pixel radius
        # "x_marker"        -- X at cell center

    grid_position: tuple[int, int]  # (x, y) grid coordinates

    data: dict[str, Any]
        # type-specific rendering parameters:
        # direction_arrow: direction (str), length (float 0-1),
        #                  is_selected (bool), color (str)
        # center_dot:      radius (float 0-1), is_selected (bool)
        # bar_chart:       activation (float), values (list[float]),
        #                  labels (list[str])
        # diamond_marker:  opacity (float 0-1)
        # neighbor_dot:    resource_value (float), is_traversable (bool)
        # radius_circle:   radius_cells (int), label (str)
        # x_marker:        (no extra params)


class OverlayData(BaseModel):
    """One overlay layer. Multiple can be active simultaneously."""

    model_config = ConfigDict(frozen=True)

    overlay_type: str  # matches OverlayTypeDeclaration.key
    items: tuple[OverlayItem, ...]
```

### 6.8 MetadataSection

```python
class MetadataSection(BaseModel):
    """World-specific metadata for the detail panel."""

    model_config = ConfigDict(frozen=True)

    title: str
    rows: tuple[AnalysisRow, ...]
```

---

## 7. CellLayout as Bridge

This is the most critical architectural element. It decouples world
geometry from system overlays.

### 7.1 The problem

System A's overlays (arrows, bar charts) must render correctly on any
world type. The system adapter knows nothing about cell shapes or pixel
positions. The world adapter knows nothing about overlay types or system
internals.

### 7.2 The solution

`CellLayout` is the shared coordinate system.

```
System adapter produces:
    OverlayItem(
        item_type="direction_arrow",
        grid_position=(3, 2),
        data={"direction": "up", "length": 0.4, "is_selected": True},
    )

World adapter produces:
    CellLayout where:
        cell_centers[(3, 2)] = (157.5, 105.0)
        cell_bounding_boxes[(3, 2)] = (135.0, 90.0, 45.0, 30.0)

OverlayRenderer combines both:
    "direction_arrow" at pixel (157.5, 105.0):
    draws line upward, length = cell_height * 0.4
```

The system adapter works exclusively in grid coordinates. The world
adapter defines the mapping to pixel space. The base layer's
`OverlayRenderer` applies the mapping at render time.

### 7.3 Implications

- System overlays work identically on rectangular and non-rectangular
  grids without any system adapter changes.
- World adapters do not need to understand overlay semantics.
- Adding a new cell shape (hexagonal) requires only updating the
  `CellLayout` computation; no overlay code changes.

---

## 8. Overlay Rendering Pipeline

Three stages, with a clear boundary between structured data and
PySide6 rendering.

```
Stage 1: System adapter builds overlay data
    Input:  BaseStepTrace (with system_data)
    Output: list[OverlayData], each containing OverlayItem[]
    Owner:  SystemVisualizationAdapter.build_overlays()

Stage 2: OverlayRenderer resolves positions
    Input:  list[OverlayData] + CellLayout
    For each OverlayItem:
        center = cell_layout.cell_centers[item.grid_position]
        bbox = cell_layout.cell_bounding_boxes[item.grid_position]
    Owner:  OverlayRenderer (base layer)

Stage 3: OverlayRenderer draws with QPainter
    Input:  resolved pixel coordinates + item.data
    Dispatches on item.item_type to drawing methods
    Owner:  OverlayRenderer (base layer)
    Note:   This is the ONLY place QPainter is used for overlays
```

The `OverlayRenderer` is the boundary between structured data and
PySide6. Everything above it is testable without a display.

### 8.1 Known item_type renderers

Initially matching v0.1.0 overlay capabilities, plus new types for
System B:

| item_type | Rendering | Origin |
|-----------|-----------|--------|
| `direction_arrow` | Line from center in direction, length proportional to value | v0.1.0 action preference |
| `center_dot` | Filled circle at center | v0.1.0 consume indicator |
| `center_ring` | Unfilled ring at center | v0.1.0 stay indicator |
| `bar_chart` | Mini horizontal bars within cell bounds | v0.1.0 drive contribution |
| `diamond_marker` | Rotated square at center, opacity by resource | v0.1.0 consumption opportunity |
| `neighbor_dot` | Circle at a cell center, opacity by resource | v0.1.0 consumption opportunity |
| `x_marker` | Red X at center | v0.1.0 non-traversable indicator |
| `radius_circle` | Circle around cell with given radius | New: System B scan area |

---

## 9. Replay Contract Extension

Two changes to existing SDK types to carry world information through
the replay pipeline.

### 9.1 BaseStepTrace -- add `world_data`

```python
class BaseStepTrace(BaseModel):
    # ... existing fields ...

    world_data: dict[str, Any] = Field(default_factory=dict)
```

This parallels `system_data`. World metadata is per-step because some
world state changes each tick (e.g. hotspot positions drift in
signal_landscape).

### 9.2 BaseEpisodeTrace -- add `world_type` and `world_config`

```python
class BaseEpisodeTrace(BaseModel):
    # ... existing fields ...

    world_type: str = "grid_2d"
    world_config: dict[str, Any] = Field(default_factory=dict)
```

`world_type` is needed for adapter resolution. `world_config` provides
the world adapter with configuration parameters (grid dimensions,
hotspot count, etc.) so it can parameterize its rendering without
re-parsing config files.

Default values ensure backward compatibility with replays saved before
these fields existed.

### 9.3 MutableWorldProtocol -- add optional `world_metadata()`

```python
class MutableWorldProtocol(Protocol):
    # ... existing methods ...

    def world_metadata(self) -> dict[str, Any]:
        """Return per-step metadata for replay visualization.
        Default: {}. Override to expose internal state like
        hotspot positions."""
        ...
```

### 9.4 Framework runner changes

In `_run_step()`:
- After `world.tick()`, call `world.world_metadata()` and include the
  result as `world_data` in the `BaseStepTrace`.

In `run_episode()`:
- Include `world_type` from the world config and `world_config` as a
  dict in `BaseEpisodeTrace`.

### 9.5 World metadata shapes per type

| World type | `world_data` per step | `world_config` snapshot |
|------------|----------------------|------------------------|
| `grid_2d` | `{}` | `{grid_width, grid_height, obstacle_density, ...}` |
| `toroidal` | `{"topology": "toroidal"}` | `{grid_width, grid_height, ...}` |
| `signal_landscape` | `{"hotspots": [{"cx": f, "cy": f, "radius": f, "intensity": f}, ...]}` | `{grid_width, grid_height, num_hotspots, ...}` |

---

## 10. CanvasWidget Design

Replaces the v0.1.0 `GridWidget`. All geometry and coloring is
delegated to the world adapter via `CellLayout` and `CellColorConfig`.

```python
class CanvasWidget(QWidget):
    """World-adapter-aware canvas for rendering the world grid."""

    cell_clicked = Signal(int, int)  # (row, col)
    agent_clicked = Signal()

    def __init__(self, world_adapter, ...):
        self._world_adapter = world_adapter
        self._cell_layout: CellLayout | None = None
        self._cell_color_config = world_adapter.cell_color_config()
        self._overlay_renderer = OverlayRenderer()

    def set_frame(self, grid_vm, agent_vm, selection_vm,
                  overlay_data, topology_indicators):
        ...

    def paintEvent(self, event):
        # 1. Draw cell backgrounds using CellLayout polygons
        #    + CellColorConfig color rules
        # 2. Draw grid lines along polygon edges
        # 3. Draw topology indicators (delegated to type renderers)
        # 4. Draw selection highlight using CellLayout polygon
        # 5. Draw agent marker at CellLayout.cell_centers[agent_pos]
        # 6. OverlayRenderer.render(painter, overlay_data, cell_layout)

    def mousePressEvent(self, event):
        pos = self._world_adapter.pixel_to_grid(
            event.x(), event.y(), self._cell_layout)
        # Emit cell_clicked or agent_clicked as appropriate

    def resizeEvent(self, event):
        self._cell_layout = self._world_adapter.cell_layout(
            grid_w, grid_h, self.width(), self.height())
```

The key difference from v0.1.0's `GridWidget`: no hard-coded
`_cell_rect()` method. All geometry comes from `CellLayout`.

---

## 11. Concrete Adapters

### 11.1 World adapters

#### Grid2DWorldVisualizationAdapter

The baseline rectangular grid adapter. All fields are standard.

- `cell_shape()`: `RECTANGULAR`
- `cell_layout()`: standard rectangular grid computation
- `cell_color_config()`:
  - obstacle: `(0, 0, 0)` (black)
  - empty: `(224, 224, 224)` (light gray)
  - resource gradient: `(232, 245, 233)` to `(46, 125, 50)` (pale to saturated green)
  - agent: `(33, 150, 243)` (blue)
  - selection border: `(255, 160, 0)` (orange)
  - grid lines: `(158, 158, 158)` (gray)
- `topology_indicators()`: empty list (bounded grid)
- `pixel_to_grid()`: `Position(x=int(px/cell_w), y=int(py/cell_h))` with
  bounds check
- `world_metadata_sections()`: empty list
- `format_world_info()`: `None`

#### ToroidalWorldVisualizationAdapter

Extends Grid2DWorldVisualizationAdapter (same cell model, same colors).

- `topology_indicators()`: returns `TopologyIndicator` entries for the
  four grid edges, type `"wrap_edge"`, with dashed-line rendering data
  indicating wraparound connectivity
- `format_world_info()`: `"Toroidal topology (edges wrap)"`
- All other methods are inherited from the grid_2d adapter

#### SignalLandscapeWorldVisualizationAdapter

Distinct color palette and hotspot markers.

- `cell_shape()`: `RECTANGULAR`
- `cell_color_config()`:
  - obstacle: `(0, 0, 0)` (black)
  - empty: `(40, 40, 60)` (dark blue-gray)
  - resource (signal) gradient: `(40, 40, 60)` to `(255, 100, 0)` (dark
    to hot orange -- heatmap palette)
- `topology_indicators()`: reads `world_data["hotspots"]` and returns
  `TopologyIndicator("hotspot_center", ...)` for each hotspot, with
  pixel radius and intensity for rendering
- `world_metadata_sections()`: returns a `MetadataSection("Hotspots")`
  with rows for each hotspot position and intensity
- `format_world_info()`: `f"{n} hotspots active"`

#### DefaultWorldVisualizationAdapter

Fallback for unknown world types. Behaves identically to the grid_2d
adapter with standard colors. Used when no adapter is registered for
a world type.

### 11.2 System adapters

#### SystemAVisualizationAdapter

Reads `system_data` which has the shape:
```python
{
    "decision_data": {
        "observation": {...},    # 5-cell Von Neumann
        "drive": {"activation": float, "action_contributions": (...)},
        "policy": {"probabilities": (...), "admissibility_mask": (...),
                   "temperature": float, "selection_mode": str, ...},
    },
    "trace_data": {
        "energy_before": float, "energy_after": float,
        "energy_delta": float, "energy_gain": float, ...
    },
}
```

- `phase_names()`: `["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]`
- `vitality_label()`: `"Energy"`
- `format_vitality(value, system_data)`: `"3.45 / 5.00"` format using
  `max_energy` from config

`build_step_analysis()` produces 5 sections:

1. **Step Overview**: timestep, energy before/after with delta
2. **Observation**: current resource, 4 neighbor observations with
   resource value and traversable/blocked status
3. **Drive Output**: activation scalar, per-action contributions
4. **Decision Pipeline**: temperature, selection mode, per-action
   table (raw, admissibility, masked, probabilities), selected action
5. **Outcome**: moved, position change, action cost, energy gain,
   terminated, termination reason

`build_overlays()` produces 3 overlay types:

1. `"action_preference"`: direction arrows for movement, center dot
   for consume, center ring for stay (from v0.1.0
   `_draw_overlay_action_preference`)
2. `"drive_contribution"`: bar chart showing activation and per-action
   drive contributions (from v0.1.0 `_draw_overlay_drive_contribution`)
3. `"consumption_opportunity"`: diamond on current cell if resource > 0,
   neighbor dots for resource, X markers for non-traversable (from
   v0.1.0 `_draw_overlay_consumption_opportunity`)

`available_overlay_types()`:
- `OverlayTypeDeclaration("action_preference", "Action Preference", ...)`
- `OverlayTypeDeclaration("drive_contribution", "Drive Contribution", ...)`
- `OverlayTypeDeclaration("consumption_opportunity", "Consumption Opportunity", ...)`

#### SystemBVisualizationAdapter

- `phase_names()`: `["BEFORE", "AFTER_ACTION"]`
- `vitality_label()`: `"Energy"`

`build_step_analysis()` produces:

1. **Step Overview**: timestep, energy before/after/delta, action cost
2. **Decision Weights**: 6 weights from `decision_data["weights"]`
3. **Probabilities**: 6 probabilities from `decision_data["probabilities"]`
4. **Last Scan**: total_resource, cell_count from
   `decision_data["last_scan"]`
5. **Outcome**: action taken, energy_delta, scan_total

`build_overlays()` produces:

1. `"action_weights"`: direction arrows sized by probability,
   highlighting the selected action
2. `"scan_result"`: radius circle showing the scan area around the
   agent with a total resource label

#### NullSystemVisualizationAdapter

Default fallback when no system adapter is registered.

- `phase_names()`: `["BEFORE", "AFTER_ACTION"]`
- `vitality_label()`: `"Vitality"`
- `format_vitality(value, _)`: `f"{value:.0%}"`
- `build_step_analysis()`: empty list
- `build_overlays()`: empty list
- `available_overlay_types()`: empty list

---

## 12. Adapter Resolution and Registration

### 12.1 Visualization registry

New module: `axis/visualization/registry.py`

```python
_WORLD_VIS_REGISTRY: dict[str, WorldVisFactory] = {}
_SYSTEM_VIS_REGISTRY: dict[str, SystemVisFactory] = {}

def register_world_visualization(
    world_type: str,
    factory: Callable[[dict[str, Any]], WorldVisualizationAdapter],
) -> None: ...

def register_system_visualization(
    system_type: str,
    factory: Callable[[], SystemVisualizationAdapter],
) -> None: ...

def resolve_world_adapter(
    world_type: str,
    world_config: dict[str, Any],
) -> WorldVisualizationAdapter:
    """Look up factory, call with world_config.
    Falls back to DefaultWorldVisualizationAdapter."""

def resolve_system_adapter(
    system_type: str,
) -> SystemVisualizationAdapter:
    """Look up factory, call it.
    Falls back to NullSystemVisualizationAdapter."""
```

### 12.2 Registration pattern

Registration follows the same pattern as the world and system
registries -- at module import time in each package:

```python
# In axis/world/grid_2d/visualization.py
from axis.visualization.registry import register_world_visualization

register_world_visualization("grid_2d", Grid2DWorldVisualizationAdapter)
```

```python
# In axis/systems/system_a/visualization.py
from axis.visualization.registry import register_system_visualization

register_system_visualization(
    "system_a", lambda: SystemAVisualizationAdapter(...))
```

### 12.3 Resolution flow during launch

1. `ReplayAccessService` loads `BaseEpisodeTrace`
2. Read `episode.world_type` and `episode.system_type`
3. `world_adapter = resolve_world_adapter(world_type, world_config)`
4. `system_adapter = resolve_system_adapter(system_type)`
5. Both adapters injected into `ViewModelBuilder(world_adapter, system_adapter)`

---

## 13. SnapshotResolver Generalization

### 13.1 Variable phase counts

The v0.1.0 `ReplayPhase` is a fixed `IntEnum` with 3 values. In v0.2.0,
phase counts vary by system (System A has 3, System B has 2). The
resolver must work with `BaseStepTrace` and system-declared phase names.

### 13.2 Phase mapping

Given `phase_names = system_adapter.phase_names()`:

| Phase index | Phase name | World snapshot | Agent position | Vitality |
|-------------|------------|---------------|----------------|----------|
| 0 | `"BEFORE"` (always first) | `step.world_before` | `step.agent_position_before` | `step.vitality_before` |
| 1..N-2 | system-declared intermediates | `step.intermediate_snapshots[name]` | `step.agent_position_before` | `step.vitality_before` |
| N-1 | `"AFTER_ACTION"` (always last) | `step.world_after` | `step.agent_position_after` | `step.vitality_after` |

Intermediate phases use "before" agent state because the agent has not
yet acted. The world state may differ (e.g. after regeneration).

### 13.3 ReplayCoordinate

```python
class ReplayCoordinate(BaseModel):
    model_config = ConfigDict(frozen=True)

    step_index: int
    phase_index: int  # was: phase: ReplayPhase(IntEnum)
```

The `PlaybackController` traverses phase indices `0` through
`len(phase_names) - 1` before advancing to the next step. This
naturally adapts to any system's phase count.

---

## 14. Migration from v0.1.0

### 14.1 Component extraction map

| v0.1.0 file | v0.2.0 destination | Changes |
|------------|-------------------|---------|
| `replay_access.py` | `axis/visualization/replay_access.py` | Read `BaseEpisodeTrace` instead of `EpisodeResult` |
| `replay_models.py` | `axis/visualization/replay_models.py` | Remove System A type references |
| `replay_validation.py` | `axis/visualization/replay_validation.py` | Validate `BaseStepTrace` fields |
| `snapshot_models.py` | `axis/visualization/snapshot_models.py` | `ReplayCoordinate` uses `phase_index: int`; `ReplaySnapshot` drops `consumed`/`resource_consumed` |
| `snapshot_resolver.py` | `axis/visualization/snapshot_resolver.py` | Phase mapping from adapters; reads `intermediate_snapshots` |
| `viewer_state.py` | `axis/visualization/viewer_state.py` | `DebugOverlayConfig` uses dynamic `enabled_overlays: set[str]` |
| `viewer_state_transitions.py` | `axis/visualization/viewer_state_transitions.py` | Minimal changes |
| `playback_controller.py` | `axis/visualization/playback_controller.py` | Variable phase count from adapter |
| `view_models.py` | `axis/visualization/view_models.py` | Remove `ActionContextViewModel` System A fields; add `topology_indicators`, `world_info` |
| `view_model_builder.py` | `axis/visualization/view_model_builder.py` | Delegate to both adapters |
| `debug_overlay_models.py` | Removed | Replaced by `OverlayData` / `OverlayItem` |
| `errors.py` | `axis/visualization/errors.py` | Unchanged |
| `launch.py` | `axis/visualization/launch.py` | Adapter resolution added |
| `ui/grid_widget.py` | `axis/visualization/ui/canvas_widget.py` | Delegates geometry to world adapter |
| `ui/main_window.py` | `axis/visualization/ui/main_window.py` | Minimal changes |
| `ui/status_panel.py` | `axis/visualization/ui/status_panel.py` | Uses adapter vitality label + world info |
| `ui/step_analysis_panel.py` | `axis/visualization/ui/step_analysis_panel.py` | Renders `list[AnalysisSection]` instead of `StepAnalysisViewModel` |
| `ui/detail_panel.py` | `axis/visualization/ui/detail_panel.py` | Adds world metadata sections |
| `ui/replay_controls_panel.py` | `axis/visualization/ui/replay_controls_panel.py` | Dynamic phase names in combo box |
| `ui/debug_overlay_panel.py` | `axis/visualization/ui/overlay_panel.py` | Dynamic checkboxes from `OverlayTypeDeclaration` |
| `ui/session_controller.py` | `axis/visualization/ui/session_controller.py` | Injects both adapters |
| `ui/app.py` | `axis/visualization/ui/app.py` | Updated signal wiring |

### 14.2 Files with no v0.1.0 counterpart (new)

| New file | Purpose |
|----------|---------|
| `axis/visualization/ui/overlay_renderer.py` | Extracted from `GridWidget._draw_overlay_*` methods; data-driven |
| `axis/visualization/registry.py` | World and system visualization registries |
| `axis/visualization/types.py` | Supporting types (Section 6) |
| `axis/world/grid_2d/visualization.py` | Grid2D world adapter |
| `axis/world/toroidal/visualization.py` | Toroidal world adapter |
| `axis/world/signal_landscape/visualization.py` | Signal landscape world adapter |
| `axis/systems/system_a/visualization.py` | System A adapter |
| `axis/systems/system_b/visualization.py` | System B adapter |

---

## 15. Updated Work Packages

### WP-4.1 (revised): Replay Contract Extension and Base Infrastructure

**Goal**: Extend the replay contract to carry world metadata and
generalize the viewer state infrastructure.

**Scope**:
- Extend `BaseStepTrace` with `world_data: dict[str, Any]`
- Extend `BaseEpisodeTrace` with `world_type: str`, `world_config: dict`
- Add `world_metadata() -> dict[str, Any]` to `MutableWorldProtocol`
  (optional, default `{}`)
- Implement `world_metadata()` on `SignalLandscapeWorld` (returns hotspot
  positions) and `ToroidalWorld` (returns topology info)
- Update `_run_step()` and `run_episode()` in framework runner to
  capture world metadata and pass world type info to episode trace
- Move and generalize viewer state infrastructure from v0.1.0
  (`ViewerState`, `PlaybackController`, `SnapshotResolver`,
  `ReplayAccessService`, `ReplayValidation`, `ReplayModels`)
- Generalize `ReplayCoordinate` to use `phase_index: int`
- Generalize `SnapshotResolver` for `BaseStepTrace`

**Files touched**:
- `src/axis/sdk/trace.py` (extend)
- `src/axis/sdk/world_types.py` (extend protocol)
- `src/axis/framework/runner.py` (extend)
- `src/axis/world/signal_landscape/model.py` (implement world_metadata)
- `src/axis/world/toroidal/model.py` (implement world_metadata)
- `src/axis/visualization/` (new: viewer_state, playback_controller,
  snapshot_resolver, replay_access, replay_models, replay_validation,
  snapshot_models, errors)

**Dependencies**: WP-3.4 (persistence layer).

---

### WP-4.2 (revised): Adapter Protocols, Types, and Registry

**Goal**: Define both adapter protocols, all supporting types, and the
visualization-specific registry.

**Scope**:
- `WorldVisualizationAdapter` protocol (Section 4)
- `SystemVisualizationAdapter` protocol (Section 5)
- All supporting types: `CellShape`, `CellLayout`, `CellColorConfig`,
  `TopologyIndicator`, `AnalysisSection`, `AnalysisRow`,
  `OverlayTypeDeclaration`, `OverlayData`, `OverlayItem`,
  `MetadataSection` (Section 6)
- Visualization registry: `register_world_visualization()`,
  `register_system_visualization()`, `resolve_world_adapter()`,
  `resolve_system_adapter()` (Section 12)
- `DefaultWorldVisualizationAdapter` (Section 11.1)
- `NullSystemVisualizationAdapter` (Section 11.2)

**Files touched**:
- `src/axis/visualization/types.py` (new)
- `src/axis/visualization/registry.py` (new)
- `src/axis/visualization/adapters/` (new: defaults)

**Dependencies**: WP-4.1.

---

### WP-4.3 (revised): Concrete Adapters

**Goal**: Implement visualization adapters for all existing worlds and
systems.

**Scope**:
- `Grid2DWorldVisualizationAdapter` in `axis/world/grid_2d/visualization.py`
- `ToroidalWorldVisualizationAdapter` in `axis/world/toroidal/visualization.py`
- `SignalLandscapeWorldVisualizationAdapter` in
  `axis/world/signal_landscape/visualization.py`
- `SystemAVisualizationAdapter` in `axis/systems/system_a/visualization.py`
- `SystemBVisualizationAdapter` in `axis/systems/system_b/visualization.py`
- Registration of all adapters

**Files touched**:
- `src/axis/world/grid_2d/visualization.py` (new)
- `src/axis/world/toroidal/visualization.py` (new)
- `src/axis/world/signal_landscape/visualization.py` (new)
- `src/axis/systems/system_a/visualization.py` (new)
- `src/axis/systems/system_b/visualization.py` (new)

**Dependencies**: WP-4.2.

---

### WP-4.4 (revised): UI Assembly and Test Suite

**Goal**: Implement the canvas, overlay renderer, generalized panels,
and full test suite.

**Scope**:
- `CanvasWidget` (world-adapter-aware, replaces `GridWidget`)
- `OverlayRenderer` (structured data to `QPainter`, data-driven)
- Generalized `StepAnalysisPanel` (renders `list[AnalysisSection]`)
- Generalized `OverlayPanel` (uses `OverlayTypeDeclaration` list)
- Generalized `StatusPanel` (adapter vitality label + world info)
- `MainWindow`, `SessionController`, launch flow
- Test suite:
  - Base rendering with mock adapters
  - Each concrete world adapter
  - Each concrete system adapter
  - Overlay rendering with various `CellLayout` geometries
  - Snapshot resolver with variable phase counts
  - Playback controller with 2-phase and 3-phase systems

**Files touched**:
- `src/axis/visualization/overlay_renderer.py` (new)
- `src/axis/visualization/ui/canvas_widget.py` (new, replaces
  grid_widget.py)
- `src/axis/visualization/ui/` (generalized panels)
- `tests/v02/visualization/` (new test suite)

**Dependencies**: WP-4.3.

---

## 16. Design Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Adapters return structured data, not QPainter commands | Testable without display. Enables future UI framework swap. Keeps adapter contracts clean. |
| D2 | `world_data` parallel to `system_data` in `BaseStepTrace` | Symmetric design. World adapter interprets `world_data` just as system adapter interprets `system_data`. No framework coupling. |
| D3 | `CellLayout` bridges world geometry and system overlays | Decouples Tier 2 from Tier 3. System overlays render correctly on any world type without modification. |
| D4 | Default adapters for unknown types | Graceful degradation. New worlds/systems work immediately with base visualization. |
| D5 | Phase names are adapter-declared strings, not enum | Variable phase counts across systems. System A has 3, System B has 2. Future systems can declare arbitrary phases. |
| D6 | `OverlayItem` uses `item_type` string dispatch | Extensible without modifying the renderer. Closed set in base layer, open for addition. |
| D7 | `world_config` stored in episode trace | Replay viewer may need grid dimensions, hotspot parameters, etc., without re-parsing config files. |
| D8 | World and system adapters are independent | Neither adapter imports the other. The base layer mediates. This allows any world to work with any system. |

---

## 17. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| `CellLayout` dict overhead for large grids | Low | For rectangular grids, compute with a formula and cache; only precompute fully for hex |
| `OverlayItem.data` dict lacks type safety | Medium | Document expected keys per `item_type`. Adapter tests verify data shapes. |
| `world_metadata()` adds to `MutableWorldProtocol` | Medium | Method has default `{}` return. Existing worlds unaffected until they opt in. |
| Replays saved before `world_type` field cannot be loaded | Medium | Default `world_type` to `"grid_2d"` and `world_config` to `{}` if missing. |
| Signal landscape heatmap performance | Low | Same rectangular grid; only color palette differs. No extra draw passes. |
| v0.1.0 visualization behavior regression | High | System A adapter must reproduce identical analysis content. Visual diff tests. |
| Adapter protocol changes during implementation | Medium | Protocols are defined as `Protocol` classes with structural subtyping. Adding optional methods is backward-compatible. |
