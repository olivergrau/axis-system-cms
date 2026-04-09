# WP-V.3.4 Implementation Brief -- ViewModelBuilder and Frame ViewModel

## Context

The v0.1.0 `ViewModelBuilder` is the heaviest point of System A coupling in the visualization layer. It directly reads `step.decision_result`, `step.drive_output`, `step.observation`, and `step.transition_trace` -- all System A-specific types. It constructs `StepAnalysisViewModel` and `DebugOverlayViewModel` with hard-coded System A fields (drive activation, admissibility mask, consumption opportunity).

In v0.2.0, the builder delegates to both adapters:
- **World adapter**: cell layout, cell colors, topology indicators, world metadata, world info
- **System adapter**: vitality label/format, step analysis sections, overlay data

The builder itself becomes system-agnostic. The `ViewerFrameViewModel` carries adapter-produced structured data (`list[AnalysisSection]`, `list[OverlayData]`, `list[TopologyIndicator]`) instead of System A-specific view models.

### Predecessor State (After WP-V.3.3)

```
src/axis/visualization/
    __init__.py
    types.py                             # CellColorConfig, AnalysisSection, OverlayData, etc.
    protocols.py                         # WorldVisualizationAdapter, SystemVisualizationAdapter
    registry.py
    errors.py
    replay_models.py
    replay_validation.py
    replay_access.py
    snapshot_models.py
    snapshot_resolver.py
    viewer_state.py                      # ViewerState, OverlayConfig
    viewer_state_transitions.py
    playback_controller.py
    adapters/
        default_world.py
        null_system.py
```

### v0.1.0 Source Files Being Migrated

| v0.1.0 file | v0.2.0 destination | Changes |
|---|---|---|
| `axis_system_a/visualization/view_models.py` | `axis/visualization/view_models.py` | Remove System A types; add topology/overlay/analysis fields |
| `axis_system_a/visualization/view_model_builder.py` | `axis/visualization/view_model_builder.py` | Delegate to both adapters instead of reading System A types |

### Reference Documents

- `docs/v0.2.0/architecture/evolution/visualization-architecture.md` -- Sections 2.1, 3 (Data Flow Pipeline), 14.1 (Migration map)
- `docs/v0.2.0/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.3.4

---

## Objective

Implement the generalized `ViewModelBuilder` that delegates to both adapters and the `ViewerFrameViewModel` that carries adapter-produced structured data for rendering.

---

## Scope

### 1. View Models

**File**: `src/axis/visualization/view_models.py` (new)

```python
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
```

**Key changes from v0.1.0**:
- `GridCellViewModel`: removed `cell_type: CellType` enum (not framework-generic; obstacle/traversable booleans are sufficient for rendering)
- `AgentViewModel`: `energy: float` becomes `vitality: float` (normalized)
- `StatusBarViewModel`:
  - `phase: ReplayPhase` becomes `phase_index: int` + `phase_name: str`
  - `energy: float` replaced by `vitality_display: str` (formatted by system adapter, e.g. "3.45 / 5.00") and `vitality_label: str` (e.g. "Energy")
  - `world_info: str | None` added (from world adapter's `format_world_info()`)
- `ActionContextViewModel` removed entirely -- action context is part of step analysis sections produced by the system adapter
- `StepAnalysisViewModel` removed -- replaced by generic `tuple[AnalysisSection, ...]`
- `DebugOverlayViewModel` removed -- replaced by generic `tuple[OverlayData, ...]`
- `NeighborObservationViewModel` removed -- System A-specific, now inside `AnalysisSection` rows
- `ViewerFrameViewModel` gains `topology_indicators`, `world_metadata_sections`, `analysis_sections`, `overlay_data`

### 2. ViewModelBuilder

**File**: `src/axis/visualization/view_model_builder.py` (new)

```python
"""Generalized view-model builder for the Visualization Layer.

Delegates to both world and system adapters to produce a composite
ViewerFrameViewModel. No system-specific or world-specific code.

Coordinate mapping:
    Domain Position(x, y) uses x = column, y = row.
    The grid is stored as grid[row][col].
    View models use (row, col) consistently.
"""

from __future__ import annotations

from typing import Any

from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseStepTrace
from axis.visualization.playback_controller import is_at_final, is_at_initial
from axis.visualization.snapshot_models import ReplaySnapshot
from axis.visualization.snapshot_resolver import SnapshotResolver
from axis.visualization.types import (
    AnalysisSection,
    CellLayout,
    MetadataSection,
    OverlayData,
    TopologyIndicator,
)
from axis.visualization.view_models import (
    AgentViewModel,
    GridCellViewModel,
    GridViewModel,
    SelectionType,
    SelectionViewModel,
    StatusBarViewModel,
    ViewerFrameViewModel,
)
from axis.visualization.viewer_state import ViewerState


class ViewModelBuilder:
    """Stateless, deterministic builder.

    Delegates to the world adapter for cell geometry and coloring,
    and to the system adapter for analysis sections and overlays.
    """

    def __init__(
        self,
        snapshot_resolver: SnapshotResolver,
        world_adapter: Any,
        system_adapter: Any,
    ) -> None:
        self._resolver = snapshot_resolver
        self._world_adapter = world_adapter
        self._system_adapter = system_adapter

    def build(self, state: ViewerState) -> ViewerFrameViewModel:
        """Build a complete frame view model from *state*."""
        phase_names = self._system_adapter.phase_names()

        snapshot = self._resolver.resolve(
            state.episode_handle.episode_trace,
            state.coordinate.step_index,
            state.coordinate.phase_index,
            phase_names,
        )

        step_trace = state.episode_handle.episode_trace.steps[
            state.coordinate.step_index
        ]

        # -- Grid projection (world adapter) --------------------------------
        grid_vm = self._build_grid(snapshot, state)

        # -- Agent projection -----------------------------------------------
        agent_row = snapshot.agent_position.y
        agent_col = snapshot.agent_position.x

        agent_vm = AgentViewModel(
            row=agent_row,
            col=agent_col,
            vitality=snapshot.vitality,
            is_selected=state.selected_agent,
        )

        # -- Status projection (both adapters) ------------------------------
        vitality_display = self._system_adapter.format_vitality(
            snapshot.vitality, step_trace.system_data,
        )
        world_info = self._world_adapter.format_world_info(
            step_trace.world_data
            if hasattr(step_trace, "world_data")
            else {},
        )

        status_vm = StatusBarViewModel(
            step_index=state.coordinate.step_index,
            total_steps=state.episode_handle.validation.total_steps,
            phase_index=state.coordinate.phase_index,
            phase_name=snapshot.phase_name,
            playback_mode=state.playback_mode,
            vitality_display=vitality_display,
            vitality_label=self._system_adapter.vitality_label(),
            world_info=world_info,
            at_start=is_at_initial(state),
            at_end=is_at_final(state),
        )

        # -- Selection projection -------------------------------------------
        if state.selected_agent:
            sel_type = SelectionType.AGENT
        elif state.selected_cell is not None:
            sel_type = SelectionType.CELL
        else:
            sel_type = SelectionType.NONE

        selection_vm = SelectionViewModel(
            selection_type=sel_type,
            selected_cell=state.selected_cell,
            agent_selected=state.selected_agent,
        )

        # -- World adapter outputs ------------------------------------------
        world_data = (
            step_trace.world_data
            if hasattr(step_trace, "world_data")
            else {}
        )

        cell_layout = self._world_adapter.cell_layout(
            snapshot.world_snapshot.width,
            snapshot.world_snapshot.height,
            800,  # default canvas width (actual set by widget resize)
            600,  # default canvas height
        )

        topology_indicators = self._world_adapter.topology_indicators(
            snapshot.world_snapshot, world_data, cell_layout,
        )

        world_metadata_sections = self._world_adapter.world_metadata_sections(
            world_data,
        )

        # -- System adapter outputs -----------------------------------------
        analysis_sections = self._system_adapter.build_step_analysis(
            step_trace,
        )

        overlay_data = self._build_overlays(step_trace, state)

        # -- Assemble frame -------------------------------------------------
        return ViewerFrameViewModel(
            coordinate=state.coordinate,
            grid=grid_vm,
            agent=agent_vm,
            status=status_vm,
            selection=selection_vm,
            topology_indicators=tuple(topology_indicators),
            world_metadata_sections=tuple(world_metadata_sections),
            analysis_sections=tuple(analysis_sections),
            overlay_data=tuple(overlay_data),
        )

    def _build_grid(
        self,
        snapshot: ReplaySnapshot,
        state: ViewerState,
    ) -> GridViewModel:
        """Project world snapshot to GridViewModel."""
        ws = snapshot.world_snapshot
        agent_row = snapshot.agent_position.y
        agent_col = snapshot.agent_position.x

        cells: list[GridCellViewModel] = []
        for row_idx, row in enumerate(ws.grid):
            for col_idx, cell in enumerate(row):
                cells.append(
                    GridCellViewModel(
                        row=row_idx,
                        col=col_idx,
                        resource_value=cell.resource_value,
                        is_obstacle=not cell.is_traversable and cell.resource_value == 0.0,
                        is_traversable=cell.is_traversable,
                        is_agent_here=(
                            row_idx == agent_row and col_idx == agent_col
                        ),
                        is_selected=(
                            state.selected_cell == (row_idx, col_idx)
                        ),
                    ),
                )

        return GridViewModel(
            width=ws.width,
            height=ws.height,
            cells=tuple(cells),
        )

    def _build_overlays(
        self,
        step_trace: BaseStepTrace,
        state: ViewerState,
    ) -> list[OverlayData]:
        """Build overlay data, filtered by overlay config."""
        cfg = state.overlay_config
        if not cfg.master_enabled:
            return []

        all_overlays = self._system_adapter.build_overlays(step_trace)

        # Filter to only enabled overlay types
        return [
            od for od in all_overlays
            if od.overlay_type in cfg.enabled_overlays
        ]
```

**Key changes from v0.1.0**:
- Constructor takes `world_adapter` and `system_adapter` in addition to `snapshot_resolver`
- `build()` calls `self._resolver.resolve()` with `phase_names` from system adapter
- Grid projection reads `CellView` from `WorldSnapshot` instead of `Cell` from System A
- `_build_debug_overlay()` replaced by `_build_overlays()` which calls `system_adapter.build_overlays(step_trace)` and filters by `overlay_config.enabled_overlays`
- `_build_step_analysis()` replaced by `system_adapter.build_step_analysis(step_trace)` -- the adapter returns `list[AnalysisSection]` directly
- Status bar includes `vitality_display` (formatted by system adapter), `vitality_label`, and `world_info` (from world adapter)
- Topology indicators obtained from world adapter via `topology_indicators()`
- World metadata sections obtained from world adapter via `world_metadata_sections()`
- No System A imports anywhere -- no `EpisodeResult`, `TransitionTrace`, `Action`, `CellType`, `TerminationReason`, `Observation`, `DecisionResult`, `DriveOutput`

**Design notes**:
- `world_adapter` and `system_adapter` are typed as `Any` in the constructor. The protocols are structural (duck-typing), so isinstance checks are not needed. The type annotations in the protocol definitions serve as documentation.
- `world_data` access uses `hasattr(step_trace, "world_data")` for backward compatibility with episodes serialized before WP-V.0.1 adds the field (defaults to `{}`).
- The `cell_layout` computed in `build()` uses hardcoded 800x600 defaults. In the real viewer (WP-V.4.1), the `CanvasWidget` computes `CellLayout` based on actual widget dimensions and passes it to rendering. The builder computes it here only for topology indicators and world metadata -- widgets will recompute on resize.

### 3. Obstacle Detection

The v0.1.0 builder checks `cell.cell_type == CellType.OBSTACLE`. In v0.2.0, `CellView` (from `axis.sdk.world_types`) has `is_traversable: bool` and `resource_value: float` but no `cell_type` enum. Obstacle detection heuristic: `not cell.is_traversable and cell.resource_value == 0.0`. This is sufficient for rendering (obstacles are drawn with `CellColorConfig.obstacle_color`).

---

## Out of Scope

- Canvas rendering (WP-V.4.1)
- Overlay rendering (WP-V.4.2)
- Analysis panel UI (WP-V.4.3)
- Any PySide6 code
- Modifications to adapter protocols or supporting types

---

## Architectural Constraints

### 1. No System-Specific Imports

The builder imports from `axis.visualization.*` and `axis.sdk.*` only. No imports from `axis.systems.*` or `axis.world.*`.

### 2. Adapter Outputs Are Passed Through

The builder does not interpret `AnalysisSection` contents or `OverlayItem` data. It passes them through from the system adapter to the `ViewerFrameViewModel`. Only the UI layer interprets them for rendering.

### 3. Overlay Filtering in Builder

The builder filters overlays by `overlay_config.enabled_overlays` before including them in the frame. This prevents the UI from receiving data it won't render, keeping the frame view model lean.

### 4. World Adapter Called for Geometry

The builder calls `world_adapter.cell_layout()` and `world_adapter.topology_indicators()`. In the full viewer, these will also be called by `CanvasWidget` on resize. The builder's call provides data for the frame view model; the widget's call provides data for rendering at the actual widget size.

---

## Testing Requirements

**File**: `tests/v02/visualization/test_view_model_builder.py` (new)

Create fixtures:
- `_mock_world_adapter()`: Returns an object satisfying `WorldVisualizationAdapter` protocol with predetermined values
- `_mock_system_adapter()`: Returns an object satisfying `SystemVisualizationAdapter` protocol with 3 phases, 2 analysis sections, 1 overlay
- `_sample_episode_handle()`: As in WP-V.3.3 tests

### Grid projection tests

1. **`test_grid_vm_dimensions`**: Assert width and height match world snapshot
2. **`test_grid_vm_cell_count`**: Assert cells count = width * height
3. **`test_grid_vm_agent_position`**: Assert `is_agent_here` true for agent cell only
4. **`test_grid_vm_selected_cell`**: Assert `is_selected` true for selected cell only
5. **`test_grid_vm_no_selection`**: Assert no cells have `is_selected` when no selection
6. **`test_grid_vm_obstacle_detection`**: Assert `is_obstacle` for non-traversable zero-resource cells

### Agent projection tests

7. **`test_agent_vm_position`**: Assert row/col match agent position (y/x)
8. **`test_agent_vm_vitality`**: Assert vitality matches snapshot
9. **`test_agent_vm_selected`**: Assert `is_selected` reflects state

### Status bar tests

10. **`test_status_step_and_total`**: Assert step_index and total_steps
11. **`test_status_phase_info`**: Assert phase_index and phase_name
12. **`test_status_vitality_display`**: Assert formatted string from system adapter
13. **`test_status_vitality_label`**: Assert label from system adapter
14. **`test_status_world_info`**: Assert world info from world adapter
15. **`test_status_at_start_at_end`**: Assert boundary flags

### Selection tests

16. **`test_selection_none`**: No selection → `SelectionType.NONE`
17. **`test_selection_cell`**: Cell selected → `SelectionType.CELL`
18. **`test_selection_agent`**: Agent selected → `SelectionType.AGENT`

### Adapter delegation tests

19. **`test_topology_indicators_from_world_adapter`**: Assert builder passes through world adapter's topology indicators
20. **`test_world_metadata_from_world_adapter`**: Assert builder passes through world metadata sections
21. **`test_analysis_sections_from_system_adapter`**: Assert builder passes through system adapter's analysis sections
22. **`test_overlay_data_from_system_adapter`**: Assert builder passes through system adapter's overlay data

### Overlay filtering tests

23. **`test_overlays_empty_when_master_disabled`**: Master off → empty overlay_data
24. **`test_overlays_filtered_by_enabled_set`**: Only enabled overlay types included
25. **`test_overlays_all_enabled`**: All overlays returned when all enabled

### Integration tests

26. **`test_build_produces_complete_frame`**: Assert all fields present and non-None on ViewerFrameViewModel
27. **`test_build_with_null_system_adapter`**: Using `NullSystemVisualizationAdapter`, assert empty sections and overlays
28. **`test_build_with_default_world_adapter`**: Using `DefaultWorldVisualizationAdapter`, assert empty topology and metadata

---

## Expected Deliverable

1. `src/axis/visualization/view_models.py`
2. `src/axis/visualization/view_model_builder.py`
3. `tests/v02/visualization/test_view_model_builder.py`
4. Confirmation that all existing tests still pass

---

## Expected File Structure

```
src/axis/visualization/
    __init__.py                          # UNCHANGED
    types.py                             # UNCHANGED
    protocols.py                         # UNCHANGED
    registry.py                          # UNCHANGED
    errors.py                            # UNCHANGED (WP-V.3.1)
    replay_models.py                     # UNCHANGED (WP-V.3.1)
    replay_validation.py                 # UNCHANGED (WP-V.3.1)
    replay_access.py                     # UNCHANGED (WP-V.3.1)
    snapshot_models.py                   # UNCHANGED (WP-V.3.2)
    snapshot_resolver.py                 # UNCHANGED (WP-V.3.2)
    viewer_state.py                      # UNCHANGED (WP-V.3.3)
    viewer_state_transitions.py          # UNCHANGED (WP-V.3.3)
    playback_controller.py               # UNCHANGED (WP-V.3.3)
    view_models.py                       # NEW
    view_model_builder.py                # NEW
    adapters/
        default_world.py                 # UNCHANGED
        null_system.py                   # UNCHANGED

tests/v02/visualization/
    test_view_model_builder.py           # NEW
```

---

## Important Final Constraint

This is the last WP in Phase V-3. After it, the entire base layer infrastructure is complete:
- **WP-V.3.1**: Replay access, validation, error types, models
- **WP-V.3.2**: Snapshot resolution with variable phases
- **WP-V.3.3**: Viewer state with dynamic overlays, playback with variable phases
- **WP-V.3.4**: View model builder delegating to both adapters

Phase V-4 (UI Assembly) can begin: all data flows from repository through adapters through the builder into `ViewerFrameViewModel`, ready for PySide6 widgets to render.
