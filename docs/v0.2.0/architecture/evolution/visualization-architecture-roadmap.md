# Three-Tier Visualization -- Implementation Roadmap

**Based on**: `visualization-architecture.md` \
**Supersedes**: WP-4.1 through WP-4.4 of `modular-architecture-roadmap.md` \
**Status**: Proposed

---

## How to Read This Document

This is a **coarse roadmap** for the three-tier visualization system
described in `visualization-architecture.md`.  Each work package (WP)
describes:

- what it achieves (**goal**)
- what it touches in the codebase (**touches**)
- what its key deliverables are (**deliverable**)
- what must be true before it starts (**dependencies**)
- a short list of **key work** items -- enough to scope the effort and
  enable later refinement into a full implementation spec

Work packages are numbered **WP-V.n** (V for Visualization) to avoid
collision with the existing WP-4.x numbers from the modular-architecture
roadmap.  They are grouped into **phases** that must be executed
sequentially.  Work packages within a phase can often be parallelized,
but some have internal ordering noted in their dependencies.

**For Claude Code agents**: Each WP should become a self-contained
implementation task.  Read `visualization-architecture.md` before
starting any WP.

**For human developers**: Use this as a planning and review guide.  Each
WP is scoped for roughly one focused work session.

---

## Architectural Decisions Summary

These decisions were made in `visualization-architecture.md` and are
**binding for all work packages**.

| # | Decision | Choice |
|---|----------|--------|
| D1 | Adapters return structured data, not QPainter commands | Testable without display; future UI framework swap |
| D2 | `world_data` parallel to `system_data` in `BaseStepTrace` | Symmetric design; world adapter interprets `world_data` |
| D3 | `CellLayout` bridges world geometry and system overlays | System overlays render correctly on any world type |
| D4 | Default adapters for unknown types | Graceful degradation via `DefaultWorldVis` and `NullSystemVis` |
| D5 | Phase names are adapter-declared strings, not enum | Variable phase counts across systems |
| D6 | `OverlayItem` uses `item_type` string dispatch | Extensible without modifying the renderer |
| D7 | `world_config` stored in episode trace | Replay viewer parameterizes rendering from trace data |
| D8 | World and system adapters are independent | Neither imports the other; base layer mediates |

---

## Phase V-0 -- Replay Contract Extension

Extend the framework's replay pipeline to carry world metadata.  This
phase touches existing code and must land before any visualization work
can begin.

### WP-V.0.1: Extend SDK Trace Types

**Goal**: Add `world_data`, `world_type`, and `world_config` to the
replay contract so that the visualization layer has the information it
needs to resolve adapters and render world-specific visuals.

**Touches**:
- `src/axis/sdk/trace.py`
- `src/axis/sdk/world_types.py`

**Key work**:
- Add `world_data: dict[str, Any] = Field(default_factory=dict)` to
  `BaseStepTrace`
- Add `world_type: str = "grid_2d"` and
  `world_config: dict[str, Any] = Field(default_factory=dict)` to
  `BaseEpisodeTrace`
- Add `world_metadata() -> dict[str, Any]` to `MutableWorldProtocol`
  with default return `{}`
- Verify all existing tests still pass (backward-compatible defaults)

**Deliverable**: Extended trace types with backward-compatible defaults.

**Dependencies**: None (builds on current SDK types).

---

### WP-V.0.2: Implement World Metadata on Existing Worlds

**Goal**: Each world type returns meaningful per-step metadata so the
visualization layer can render world-specific indicators.

**Touches**:
- `src/axis/world/grid_2d/model.py`
- `src/axis/world/toroidal/model.py`
- `src/axis/world/signal_landscape/model.py`

**Key work**:
- `Grid2DWorld.world_metadata()`: return `{}` (no step-varying state)
- `ToroidalWorld.world_metadata()`: return `{"topology": "toroidal"}`
- `SignalLandscapeWorld.world_metadata()`: return current hotspot
  positions and parameters
  `{"hotspots": [{"cx": f, "cy": f, "radius": f, "intensity": f}, ...]}`
- Unit tests for each implementation

**Deliverable**: All three worlds implement `world_metadata()`.

**Dependencies**: WP-V.0.1.

---

### WP-V.0.3: Capture World Metadata in Framework Runner

**Goal**: The framework runner captures world metadata on every step and
passes world identity to the episode trace, so persisted replays carry
the information the viewer needs.

**Touches**:
- `src/axis/framework/runner.py`

**Key work**:
- In `_run_step()`: after `world.tick()`, call `world.world_metadata()`
  and include result as `world_data` in the `BaseStepTrace`
- In `run_episode()`: include `world_type` (from world config) and
  `world_config` (as dict) in the `BaseEpisodeTrace`
- Integration test: run a short episode, verify `world_data` is
  non-empty for signal_landscape and that `world_type` is set correctly

**Deliverable**: Persisted replays contain world metadata.

**Dependencies**: WP-V.0.1, WP-V.0.2.

---

## Phase V-1 -- Visualization Types and Protocols

Define the adapter protocols, all supporting types, and the
visualization registry.  No PySide6 code yet -- pure data contracts.

### WP-V.1.1: Supporting Types

**Goal**: Define the Pydantic models and enums that both adapter
protocols depend on.

**Touches**:
- `src/axis/visualization/types.py` (new)

**Key work**:
- `CellShape` enum (`RECTANGULAR`, `HEXAGONAL`)
- `CellLayout` model (cell_polygons, cell_centers, cell_bounding_boxes)
- `CellColorConfig` model (RGB tuples for all cell types)
- `TopologyIndicator` model (indicator_type, position, data)
- `AnalysisSection` and `AnalysisRow` models
- `OverlayTypeDeclaration` model
- `OverlayData` and `OverlayItem` models
- `MetadataSection` model
- All models are frozen Pydantic `BaseModel`s, no Qt imports
- Unit tests: construction, serialization round-trip, validation

**Deliverable**: `axis/visualization/types.py` with all types from
Section 6 of the architecture spec.

**Dependencies**: WP-V.0.1 (needs `BaseStepTrace` with `world_data`).

---

### WP-V.1.2: Adapter Protocols

**Goal**: Define the `WorldVisualizationAdapter` and
`SystemVisualizationAdapter` as `typing.Protocol` classes.

**Touches**:
- `src/axis/visualization/protocols.py` (new)

**Key work**:
- `WorldVisualizationAdapter` protocol with all methods from
  Section 4 of the architecture spec: `cell_shape`, `cell_layout`,
  `cell_color_config`, `topology_indicators`, `pixel_to_grid`,
  `agent_marker_center`, `world_metadata_sections`, `format_world_info`
- `SystemVisualizationAdapter` protocol with all methods from
  Section 5: `phase_names`, `vitality_label`, `format_vitality`,
  `build_step_analysis`, `build_overlays`, `available_overlay_types`
- Protocol conformance tests using a minimal mock adapter

**Deliverable**: Protocol definitions.  Mock adapters pass
`isinstance()` checks.

**Dependencies**: WP-V.1.1.

---

### WP-V.1.3: Default and Null Adapters

**Goal**: Provide fallback adapters that enable graceful degradation for
unknown world types and system types.

**Touches**:
- `src/axis/visualization/adapters/default_world.py` (new)
- `src/axis/visualization/adapters/null_system.py` (new)

**Key work**:
- `DefaultWorldVisualizationAdapter`: rectangular cells, standard
  green-gradient colors, empty topology indicators, trivial hit-testing.
  Behavior identical to the grid_2d adapter (Section 11.1)
- `NullSystemVisualizationAdapter`: 2-phase `["BEFORE", "AFTER_ACTION"]`,
  `"Vitality"` label, percentage format, empty analysis/overlays
  (Section 11.2)
- Both must satisfy their respective protocol
- Unit tests verifying all methods return valid structured data

**Deliverable**: Working fallback adapters.

**Dependencies**: WP-V.1.2.

---

### WP-V.1.4: Visualization Registry

**Goal**: Registry module for resolving adapters by world_type and
system_type, parallel to the existing world and system registries.

**Touches**:
- `src/axis/visualization/registry.py` (new)

**Key work**:
- `register_world_visualization(world_type, factory)` and
  `register_system_visualization(system_type, factory)`
- `resolve_world_adapter(world_type, world_config)` with fallback to
  `DefaultWorldVisualizationAdapter`
- `resolve_system_adapter(system_type)` with fallback to
  `NullSystemVisualizationAdapter`
- Tests: registration, resolution, fallback behavior, duplicate
  registration handling

**Deliverable**: Working registry with fallback defaults.

**Dependencies**: WP-V.1.3.

---

## Phase V-2 -- Concrete Adapters

Implement the world and system visualization adapters for all existing
types.  Each adapter is a self-contained module with its own tests.
All WPs in this phase can be parallelized.

### WP-V.2.1: Grid2D World Adapter

**Goal**: Rectangular grid adapter -- the baseline for all grid-based
worlds.

**Touches**:
- `src/axis/world/grid_2d/visualization.py` (new)

**Key work**:
- `Grid2DWorldVisualizationAdapter` implementing
  `WorldVisualizationAdapter`
- `cell_shape()`: `RECTANGULAR`
- `cell_layout()`: standard rectangular grid computation
  (cell_w = canvas_w / grid_w, four-corner polygons)
- `cell_color_config()`: obstacle black, empty gray, resource
  pale-to-saturated green, agent blue, selection orange, grid gray
  (exact RGB values from Section 11.1)
- `topology_indicators()`: empty list
- `pixel_to_grid()`: simple integer division with bounds check
- `agent_marker_center()`: center of cell bounding box
- `world_metadata_sections()`: empty list
- `format_world_info()`: `None`
- Register with visualization registry
- Unit tests for layout computation, color config, hit-testing

**Deliverable**: Fully tested grid_2d world adapter.

**Dependencies**: WP-V.1.4.

---

### WP-V.2.2: Toroidal World Adapter

**Goal**: Extends the grid_2d adapter with wrap-edge topology indicators.

**Touches**:
- `src/axis/world/toroidal/visualization.py` (new)

**Key work**:
- `ToroidalWorldVisualizationAdapter` extending or delegating to the
  grid_2d adapter (same cell model, same colors)
- `topology_indicators()`: returns `TopologyIndicator("wrap_edge", ...)`
  for each of the four grid edges with dashed-line rendering data
- `format_world_info()`: `"Toroidal topology (edges wrap)"`
- All other methods inherited/delegated from grid_2d adapter
- Register with visualization registry
- Unit tests for topology indicator generation

**Deliverable**: Toroidal world adapter with wrap-edge indicators.

**Dependencies**: WP-V.1.4, WP-V.2.1 (shares base implementation).

---

### WP-V.2.3: Signal Landscape World Adapter

**Goal**: Heatmap-colored adapter with hotspot markers.

**Touches**:
- `src/axis/world/signal_landscape/visualization.py` (new)

**Key work**:
- `SignalLandscapeWorldVisualizationAdapter`
- `cell_color_config()`: dark blue-gray empty cells, dark-to-hot-orange
  resource gradient (heatmap palette, Section 11.1)
- `topology_indicators()`: reads `world_data["hotspots"]`, returns
  `TopologyIndicator("hotspot_center", ...)` for each hotspot with
  pixel radius and intensity
- `world_metadata_sections()`: `MetadataSection("Hotspots")` with rows
  for each hotspot position and intensity
- `format_world_info()`: `f"{n} hotspots active"`
- Register with visualization registry
- Unit tests: heatmap color config, hotspot indicator generation,
  metadata section building

**Deliverable**: Signal landscape adapter with heatmap + hotspot visuals.

**Dependencies**: WP-V.1.4.

---

### WP-V.2.4: System A Visualization Adapter

**Goal**: Full-fidelity System A adapter preserving all v0.1.0
visualization detail.

**Touches**:
- `src/axis/systems/system_a/visualization.py` (new)

**Key work**:
- `SystemAVisualizationAdapter` implementing
  `SystemVisualizationAdapter`
- `phase_names()`: `["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]`
- `vitality_label()`: `"Energy"`
- `format_vitality()`: reads `max_energy` from system_data, formats
  `"3.45 / 5.00"`
- `build_step_analysis()`: produces 5 sections (Step Overview,
  Observation, Drive Output, Decision Pipeline, Outcome) from
  `system_data` -- see Section 11.2 of architecture spec
- `build_overlays()`: produces 3 overlay types
  (`action_preference`, `drive_contribution`,
  `consumption_opportunity`) -- see Section 11.2
- `available_overlay_types()`: 3 declarations matching the overlay types
- Register with visualization registry
- Unit tests with fixture `system_data` dicts verifying section
  content and overlay item generation

**Deliverable**: System A adapter reproducing all v0.1.0 analysis and
overlay content.

**Dependencies**: WP-V.1.4.

---

### WP-V.2.5: System B Visualization Adapter

**Goal**: System B adapter with its 2-phase lifecycle and scan-area
overlays.

**Touches**:
- `src/axis/systems/system_b/visualization.py` (new)

**Key work**:
- `SystemBVisualizationAdapter` implementing
  `SystemVisualizationAdapter`
- `phase_names()`: `["BEFORE", "AFTER_ACTION"]`
- `vitality_label()`: `"Energy"`
- `build_step_analysis()`: produces 5 sections (Step Overview,
  Decision Weights, Probabilities, Last Scan, Outcome) from
  `system_data`
- `build_overlays()`: produces 2 overlay types (`action_weights`,
  `scan_result` with `radius_circle` item type)
- Register with visualization registry
- Unit tests with fixture `system_data` dicts

**Deliverable**: System B adapter with scan-area visualization.

**Dependencies**: WP-V.1.4.

---

## Phase V-3 -- Base Layer Infrastructure

Extract and generalize the v0.1.0 replay infrastructure.  No PySide6
widgets yet -- this phase covers the logic layer beneath the UI.

### WP-V.3.1: Replay Access and Validation

**Goal**: Load `BaseEpisodeTrace` from the repository and validate it
for visualization readiness.

**Touches**:
- `src/axis/visualization/replay_access.py` (new)
- `src/axis/visualization/replay_validation.py` (new)
- `src/axis/visualization/replay_models.py` (new)
- `src/axis/visualization/errors.py` (new)

**Key work**:
- `ReplayAccessService`: loads episode trace from repository, reads
  `system_type` and `world_type`
- `ReplayValidation`: checks that episodes have steps, snapshots are
  present, world dimensions are positive
- Error types: `ReplayError` hierarchy (ported from v0.1.0:
  `StepOutOfBoundsError`, `PhaseNotAvailableError`, `CellOutOfBoundsError`,
  etc.)
- Migrate and generalize from v0.1.0 `replay_access.py`,
  `replay_validation.py`, `replay_models.py`
- Tests with mock repository data

**Deliverable**: Replay loading pipeline that returns validated episode
data with resolved type information.

**Dependencies**: WP-V.0.3 (runner captures world metadata),
WP-V.1.4 (registry for adapter resolution).

---

### WP-V.3.2: Generalized Snapshot Resolver

**Goal**: Map `(step_index, phase_index)` to the correct world snapshot,
agent position, and vitality -- adapting to variable phase counts per
system.

**Touches**:
- `src/axis/visualization/snapshot_models.py` (new)
- `src/axis/visualization/snapshot_resolver.py` (new)

**Key work**:
- `ReplayCoordinate(step_index, phase_index)` replacing the v0.1.0
  `ReplayPhase` enum
- Phase mapping logic from Section 13.2 of architecture spec:
  phase 0 = BEFORE, phase N-1 = AFTER_ACTION, intermediates from
  `intermediate_snapshots`
- `SnapshotResolver.resolve(episode, step_index, phase_index)` returns
  `ReplaySnapshot` with world snapshot, agent position, vitality
- Tests with 2-phase (System B) and 3-phase (System A) episode traces

**Deliverable**: `SnapshotResolver` that works with any phase count.

**Dependencies**: WP-V.3.1.

---

### WP-V.3.3: Viewer State and Playback Controller

**Goal**: Generalized viewer state machine and playback controller that
adapt to variable phase counts.

**Touches**:
- `src/axis/visualization/viewer_state.py` (new)
- `src/axis/visualization/viewer_state_transitions.py` (new)
- `src/axis/visualization/playback_controller.py` (new)

**Key work**:
- `ViewerState`: current step, phase, play/pause, speed, selected cell,
  enabled overlays (dynamic set from `OverlayTypeDeclaration` keys)
- State transitions: step forward/backward, phase forward/backward,
  play/pause, speed change, cell selection, overlay toggle
- `PlaybackController`: traverses phase indices 0 through
  `len(phase_names) - 1` before advancing to next step, adapting
  naturally to any system's phase count
- Migrate and generalize from v0.1.0 `viewer_state.py`,
  `viewer_state_transitions.py`, `playback_controller.py`
- Tests: state transitions, playback with 2 and 3 phases, boundary
  conditions (first/last step)

**Deliverable**: Framework-generic viewer state and playback.

**Dependencies**: WP-V.3.2.

---

### WP-V.3.4: ViewModelBuilder and Frame ViewModel

**Goal**: Composite view model that delegates to both adapters and
produces the data the UI widgets need to render a single frame.

**Touches**:
- `src/axis/visualization/view_models.py` (new)
- `src/axis/visualization/view_model_builder.py` (new)

**Key work**:
- `ViewerFrameViewModel`: grid cell data (colors via `CellColorConfig`),
  agent position, topology indicators, overlay data, analysis sections,
  vitality display, world info line, world metadata sections
- `ViewModelBuilder(world_adapter, system_adapter)`:
  - Calls world adapter for cell layout, colors, topology indicators,
    world metadata, world info
  - Calls system adapter for vitality label/format, step analysis,
    overlays
  - Combines into `ViewerFrameViewModel`
- Remove all System A type references from view model layer
- Tests with mock adapters producing known structured data

**Deliverable**: `ViewModelBuilder` that produces complete frame data
from any adapter pair.

**Dependencies**: WP-V.3.2, WP-V.3.3.

---

## Phase V-4 -- UI Assembly

Build the PySide6 widgets and wire everything together.  This is the
only phase that imports PySide6.

### WP-V.4.1: CanvasWidget

**Goal**: World-adapter-aware canvas that replaces v0.1.0's `GridWidget`.
All geometry and coloring delegated to the world adapter via `CellLayout`.

**Touches**:
- `src/axis/visualization/ui/canvas_widget.py` (new)

**Key work**:
- `CanvasWidget(world_adapter)` with `set_frame()` accepting the grid
  view model, overlay data, and topology indicators
- `paintEvent()` sequence: cell backgrounds (CellLayout polygons +
  CellColorConfig), grid lines, topology indicators, selection
  highlight, agent marker, overlay rendering
- `mousePressEvent()` delegates to `world_adapter.pixel_to_grid()`
- `resizeEvent()` recomputes `CellLayout` via
  `world_adapter.cell_layout()`
- Signals: `cell_clicked(int, int)`, `agent_clicked()`
- No hard-coded `_cell_rect()` -- all geometry from `CellLayout`

**Deliverable**: `CanvasWidget` rendering any world type.

**Dependencies**: WP-V.3.4 (view models), WP-V.2.1+ (at least one
world adapter for testing).

---

### WP-V.4.2: OverlayRenderer

**Goal**: Data-driven overlay renderer that translates `OverlayData` and
`CellLayout` into QPainter draw calls.  Extracted from v0.1.0's
`GridWidget._draw_overlay_*` methods.

**Touches**:
- `src/axis/visualization/ui/overlay_renderer.py` (new)

**Key work**:
- `OverlayRenderer.render(painter, overlay_data_list, cell_layout,
  enabled_overlays)`: iterates active overlays, dispatches on
  `item_type`
- Rendering methods for all 8 known `item_type` values from
  Section 8.1 of architecture spec: `direction_arrow`, `center_dot`,
  `center_ring`, `bar_chart`, `diamond_marker`, `neighbor_dot`,
  `x_marker`, `radius_circle`
- Position resolution: reads `cell_layout.cell_centers` and
  `cell_layout.cell_bounding_boxes` for each `grid_position`
- QPainter is used ONLY inside this module and `CanvasWidget`
- Tests: verify rendering calls with mock QPainter or snapshot testing

**Deliverable**: Data-driven overlay renderer supporting all item types.

**Dependencies**: WP-V.4.1 (CanvasWidget calls OverlayRenderer).

---

### WP-V.4.3: Generalized UI Panels

**Goal**: Generalize the analysis, status, detail, overlay control, and
replay control panels for multi-system/multi-world use.

**Touches**:
- `src/axis/visualization/ui/step_analysis_panel.py` (new)
- `src/axis/visualization/ui/status_panel.py` (new)
- `src/axis/visualization/ui/detail_panel.py` (new)
- `src/axis/visualization/ui/overlay_panel.py` (new)
- `src/axis/visualization/ui/replay_controls_panel.py` (new)

**Key work**:
- `StepAnalysisPanel`: renders `list[AnalysisSection]` as formatted
  text/tree -- no System A types
- `StatusPanel`: displays vitality using adapter-provided label and
  format, plus optional world info line from world adapter
- `DetailPanel`: cell info from `CellView` + world metadata sections
  from world adapter
- `OverlayPanel`: builds checkboxes dynamically from
  `OverlayTypeDeclaration` list (not hard-coded overlay names)
- `ReplayControlsPanel`: phase combo box populated from
  `system_adapter.phase_names()` (variable count)
- Migrate and generalize from v0.1.0 panel implementations

**Deliverable**: All panels working with adapter-provided structured
data.

**Dependencies**: WP-V.3.4 (view models feeding the panels).

---

### WP-V.4.4: Main Window, Session Controller, and Launch

**Goal**: Wire all components together into the running application.

**Touches**:
- `src/axis/visualization/ui/main_window.py` (new)
- `src/axis/visualization/ui/session_controller.py` (new)
- `src/axis/visualization/ui/app.py` (new)
- `src/axis/visualization/launch.py` (new)

**Key work**:
- `MainWindow`: layout with canvas, panels, controls -- same structure
  as v0.1.0 but with adapter-injected components
- `SessionController`: coordinates `ReplayAccessService`,
  `ViewModelBuilder`, `PlaybackController`, adapter resolution, signal
  wiring between components
- `launch.py`: entry point that resolves adapters from episode data,
  builds the session, starts the Qt event loop
- CLI integration: `axis visualize --experiment <eid> --run <rid>
  --episode <n>` calls `launch.py`
- Smoke test: load a persisted episode, launch viewer, verify no crashes

**Deliverable**: Working visualization application.

**Dependencies**: WP-V.4.1, WP-V.4.2, WP-V.4.3.

---

## Phase V-5 -- Test Suite and Validation

Comprehensive testing across all tiers.

### WP-V.5.1: Adapter Test Suite

**Goal**: Systematic tests for all concrete adapters across all
combinations of worlds and systems.

**Touches**:
- `tests/v02/visualization/` (new directory)

**Key work**:
- Test each world adapter: correct `CellLayout` computation for known
  dimensions, color config values match spec, topology indicators for
  toroidal and signal_landscape
- Test each system adapter: correct analysis section titles and row
  counts for fixture `system_data`, overlay item types and grid
  positions, overlay type declarations
- Test fallback adapters: `DefaultWorldVis` and `NullSystemVis` return
  valid data
- Test adapter registration and resolution through the registry
- Combinatorial: verify that view model builder produces valid output
  for all (world, system) pairs: (grid_2d, system_a),
  (toroidal, system_a), (signal_landscape, system_b), etc.

**Deliverable**: Adapter tests covering all 4 world adapters and 3
system adapters.

**Dependencies**: WP-V.2.1 through WP-V.2.5, WP-V.3.4.

**Note**: The dependency graph serializes V.5.1 after V.4.4 for
implementation ordering, but the adapter tests have no actual dependency
on Phase V-4 UI code.

---

### WP-V.5.2: Replay Infrastructure Test Suite

**Goal**: Tests for the replay pipeline, snapshot resolution, playback
control, and viewer state.

**Touches**:
- `tests/v02/visualization/` (continued)

**Key work**:
- Snapshot resolver with 2-phase and 3-phase step traces
- Playback controller boundary conditions: first step, last step, phase
  wrap, speed changes
- Viewer state transitions: all valid transitions, invalid transitions
  rejected
- Replay validation: missing steps, invalid snapshots, zero-dimension
  worlds
- Overlay rendering with various `CellLayout` geometries (rectangular
  only initially; future-proofed for hex)
- View model builder with mock adapters returning all supported
  structured data types

**Deliverable**: Replay infrastructure tests.

**Dependencies**: WP-V.3.1 through WP-V.3.4, WP-V.4.2.

**Note**: The dependency graph serializes V.5.2 after V.4.4 for
implementation ordering. The overlay rendering tests depend on WP-V.4.2
but the remaining infrastructure tests have no Phase V-4 dependency.

---

### WP-V.5.3: End-to-End Validation

**Goal**: Run complete experiments, persist them, and verify the
visualization pipeline renders correctly for each (world, system) pair.

**Touches**:
- `tests/v02/visualization/` (continued)
- Possibly `experiments/configs/` (test configs)

**Key work**:
- Run a short System A experiment on grid_2d, persist, load into
  viewer pipeline, verify analysis sections match expected content
- Run System A on toroidal world, verify wrap-edge indicators appear
- Run System B on signal_landscape, verify hotspot indicators and
  scan-area overlay
- Verify System A adapter reproduces identical analysis content to
  v0.1.0 for a reference episode (visual regression test)
- CLI smoke test: `axis visualize` with valid experiment data

**Deliverable**: End-to-end validation across all combinations.

**Dependencies**: WP-V.4.4, WP-V.5.1, WP-V.5.2.

---

## Phase Summary

```
Phase V-0 -- Replay Contract Extension          [3 WPs]
  WP-V.0.1  Extend SDK trace types
  WP-V.0.2  Implement world metadata on existing worlds
  WP-V.0.3  Capture world metadata in framework runner

Phase V-1 -- Visualization Types and Protocols   [4 WPs]
  WP-V.1.1  Supporting types
  WP-V.1.2  Adapter protocols
  WP-V.1.3  Default and null adapters
  WP-V.1.4  Visualization registry

Phase V-2 -- Concrete Adapters                   [5 WPs, parallelizable]
  WP-V.2.1  Grid2D world adapter
  WP-V.2.2  Toroidal world adapter
  WP-V.2.3  Signal landscape world adapter
  WP-V.2.4  System A visualization adapter
  WP-V.2.5  System B visualization adapter

Phase V-3 -- Base Layer Infrastructure           [4 WPs]
  WP-V.3.1  Replay access and validation
  WP-V.3.2  Generalized snapshot resolver
  WP-V.3.3  Viewer state and playback controller
  WP-V.3.4  ViewModelBuilder and frame view model

Phase V-4 -- UI Assembly                         [4 WPs]
  WP-V.4.1  CanvasWidget
  WP-V.4.2  OverlayRenderer
  WP-V.4.3  Generalized UI panels
  WP-V.4.4  Main window, session controller, and launch

Phase V-5 -- Test Suite and Validation           [3 WPs]
  WP-V.5.1  Adapter test suite
  WP-V.5.2  Replay infrastructure test suite
  WP-V.5.3  End-to-end validation
                                           Total: 23 WPs
```

---

## Dependency Graph

```
WP-V.0.1
  │
  ├── WP-V.0.2
  │     │
  │     └── WP-V.0.3
  │
  └── WP-V.1.1
        │
        └── WP-V.1.2
              │
              └── WP-V.1.3
                    │
                    └── WP-V.1.4
                          │
             ┌────────────┼─────────────────┐
             │            │                 │
          WP-V.2.1    WP-V.2.3          WP-V.2.4
             │                              │
          WP-V.2.2                      WP-V.2.5
             │
             │
             │         WP-V.0.3 + WP-V.1.4
             │               │
             │           WP-V.3.1
             │               │
             │           WP-V.3.2
             │               │
             │           WP-V.3.3
             │               │
             │           WP-V.3.4
             │               │
             └───────────────┤
                             │
                          WP-V.4.1
                             │
                          WP-V.4.2
                             │
                          WP-V.4.3
                             │
                          WP-V.4.4
                             │
              ┌──────────────┤
              │              │
          WP-V.5.1       WP-V.5.2
              │              │
              └──────┬───────┘
                     │
                 WP-V.5.3
```

---

## Mapping to Original Roadmap WPs

This roadmap replaces WP-4.1 through WP-4.4 from the modular-
architecture roadmap.  The mapping is:

| Original WP | Coverage in this roadmap |
|-------------|------------------------|
| WP-4.1 (Base layer extraction) | WP-V.0.x (contract extension), WP-V.3.x (infrastructure) |
| WP-4.2 (Adapter interface) | WP-V.1.x (types, protocols, registry) |
| WP-4.3 (System A visualization adapter) | WP-V.2.x (all concrete adapters, not just System A) |
| WP-4.4 (Visualization test suite) | WP-V.5.x (test suite and validation) |

The increase from 4 to 23 work packages reflects the additional scope
of the `WorldVisualizationAdapter` tier and the need to support three
worlds and two systems rather than one of each.

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| PySide6 availability in CI/test environments | High -- blocks all Phase V-4 work | Separate adapter/logic tests (Phases V-0 through V-3) from UI tests; UI tests use `QApplication` fixture or `pytest-qt` |
| `CellLayout` dict overhead for large grids | Low | Rectangular grids compute with formula and cache; only pre-compute fully for hex |
| `OverlayItem.data` dict lacks type safety | Medium | Document expected keys per `item_type` in architecture spec; adapter tests verify data shapes |
| v0.1.0 visualization behavior regression | High | System A adapter must reproduce identical analysis content; visual diff tests in WP-V.5.3 |
| Adapter protocol changes during implementation | Medium | Protocols use structural subtyping; adding optional methods is backward-compatible |
| Phase V-2 adapters depend on `system_data` shape | Medium | Use fixture dicts in tests; document expected shapes in adapter implementations |
| World metadata shape not yet finalized | Low | `world_data` is `dict[str, Any]` -- schema is per-world-type, documented in Section 9.5 of architecture spec |
