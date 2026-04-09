# WP-V.3.3 Implementation Brief -- Viewer State and Playback Controller

## Context

The v0.1.0 viewer state system has three components: `ViewerState` (immutable state model), `viewer_state_transitions` (pure state transition functions), and `PlaybackController` (phase-aware navigation). All three are tightly coupled to the fixed 3-phase `ReplayPhase` IntEnum and the System A-specific `DebugOverlayConfig`.

In v0.2.0, the viewer state must adapt to variable phase counts (declared by the system adapter) and dynamic overlay types (declared by `OverlayTypeDeclaration` from the system adapter). The `ReplayPhase` enum becomes a `phase_index: int`, and `DebugOverlayConfig` (with hard-coded `action_preference_enabled`, `drive_contribution_enabled`, `consumption_opportunity_enabled` fields) is replaced by an `OverlayConfig` with a dynamic `enabled_overlays: set[str]`.

### Predecessor State (After WP-V.3.2)

```
src/axis/visualization/
    __init__.py
    types.py
    protocols.py
    registry.py
    errors.py
    replay_models.py
    replay_validation.py
    replay_access.py
    snapshot_models.py                   # ReplayCoordinate with phase_index
    snapshot_resolver.py                 # Variable phase mapping
    adapters/
        default_world.py
        null_system.py
```

### v0.1.0 Source Files Being Migrated

| v0.1.0 file | v0.2.0 destination | Changes |
|---|---|---|
| `axis_system_a/visualization/viewer_state.py` | `axis/visualization/viewer_state.py` | `DebugOverlayConfig` → `OverlayConfig`, `ReplayPhase` → `phase_index` |
| `axis_system_a/visualization/viewer_state_transitions.py` | `axis/visualization/viewer_state_transitions.py` | Phase transitions use `phase_index: int` |
| `axis_system_a/visualization/playback_controller.py` | `axis/visualization/playback_controller.py` | Variable phase count from `num_phases` parameter |
| `axis_system_a/visualization/debug_overlay_models.py` | Removed | Replaced by `OverlayConfig` with dynamic `enabled_overlays: set[str]` |

### Reference Documents

- `docs/v0.2.0/architecture/evolution/visualization-architecture.md` -- Sections 13.3 (ReplayCoordinate), 14.1 (Migration map)
- `docs/v0.2.0/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.3.3

---

## Objective

Implement generalized viewer state, pure state transitions, and playback controller that adapt to variable phase counts and dynamic overlay type sets.

---

## Scope

### 1. Overlay Config

**File**: `src/axis/visualization/viewer_state.py` (new)

The v0.1.0 `DebugOverlayConfig` has hard-coded boolean fields for each System A overlay type. The v0.2.0 replacement uses a dynamic set of overlay keys.

```python
class OverlayConfig(BaseModel):
    """Toggle state for the overlay system.

    master_enabled gates the entire overlay system. enabled_overlays
    contains the keys of individually enabled overlay types (from
    OverlayTypeDeclaration.key).
    """

    model_config = ConfigDict(frozen=True)

    master_enabled: bool = False
    enabled_overlays: frozenset[str] = frozenset()
```

**Design note**: `frozenset[str]` (not `set[str]`) because `OverlayConfig` is frozen. The keys come from `system_adapter.available_overlay_types()` -- e.g. `{"action_preference", "drive_contribution", "consumption_opportunity"}` for System A or `{"action_weights", "scan_result"}` for System B.

### 2. ViewerState

**Same file**: `src/axis/visualization/viewer_state.py`

```python
"""Viewer state model for the Visualization Layer.

Defines the centralized, immutable ViewerState and OverlayConfig.
"""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict, model_validator

from axis.visualization.replay_models import ReplayEpisodeHandle
from axis.visualization.snapshot_models import ReplayCoordinate


class PlaybackMode(str, enum.Enum):
    """Playback state of the viewer."""

    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class OverlayConfig(BaseModel):
    """Toggle state for the overlay system."""

    model_config = ConfigDict(frozen=True)

    master_enabled: bool = False
    enabled_overlays: frozenset[str] = frozenset()


class ViewerState(BaseModel):
    """Centralized, immutable viewer state -- single source of truth.

    All visualization components derive their state from this model.
    State changes happen only through pure transition functions in
    viewer_state_transitions.py.

    Invariants (enforced by model_validator):
    - coordinate.step_index is in [0, total_steps - 1]
    - coordinate.phase_index is in [0, num_phases - 1]
    - selected_cell, when set, is within grid bounds
    """

    model_config = ConfigDict(frozen=True)

    episode_handle: ReplayEpisodeHandle
    coordinate: ReplayCoordinate
    playback_mode: PlaybackMode
    num_phases: int
    selected_cell: tuple[int, int] | None = None
    selected_agent: bool = False
    overlay_config: OverlayConfig = OverlayConfig()

    @model_validator(mode="after")
    def _validate_invariants(self) -> ViewerState:
        total = self.episode_handle.validation.total_steps
        si = self.coordinate.step_index
        if si < 0 or si >= total:
            raise ValueError(
                f"step_index {si} out of bounds (valid: 0..{total - 1})"
            )
        pi = self.coordinate.phase_index
        if pi < 0 or pi >= self.num_phases:
            raise ValueError(
                f"phase_index {pi} out of bounds (valid: 0..{self.num_phases - 1})"
            )
        if self.selected_cell is not None:
            row, col = self.selected_cell
            gw = self.episode_handle.validation.grid_width
            gh = self.episode_handle.validation.grid_height
            if gw is not None and gh is not None:
                if row < 0 or row >= gh or col < 0 or col >= gw:
                    raise ValueError(
                        f"selected_cell ({row}, {col}) out of grid bounds "
                        f"({gh} rows x {gw} cols)"
                    )
        return self


def create_initial_state(
    episode_handle: ReplayEpisodeHandle,
    num_phases: int,
    available_overlay_keys: frozenset[str] | None = None,
) -> ViewerState:
    """Create the initial ViewerState for a loaded episode.

    Starts at coordinate (0, 0), STOPPED, no selection.
    All overlay types start disabled.
    """
    return ViewerState(
        episode_handle=episode_handle,
        coordinate=ReplayCoordinate(step_index=0, phase_index=0),
        playback_mode=PlaybackMode.STOPPED,
        num_phases=num_phases,
        selected_cell=None,
        selected_agent=False,
        overlay_config=OverlayConfig(),
    )
```

**Key changes from v0.1.0**:
- `coordinate: ReplayCoordinate` now uses `phase_index: int` (not `phase: ReplayPhase`)
- `num_phases: int` added -- the ViewerState knows how many phases exist for validation
- `debug_overlay_config: DebugOverlayConfig` replaced by `overlay_config: OverlayConfig` with dynamic `enabled_overlays: frozenset[str]`
- `create_initial_state()` takes `num_phases` and optional `available_overlay_keys` (for future use when initializing with all overlays enabled)
- Phase index validation added to `_validate_invariants`

### 3. State Transitions

**File**: `src/axis/visualization/viewer_state_transitions.py` (new)

```python
"""Pure state transition functions for ViewerState.

Every function takes a ViewerState (and optional parameters) and
returns a new ViewerState. No mutation. No side effects.
"""

from __future__ import annotations

from axis.visualization.errors import (
    CellOutOfBoundsError,
    StepOutOfBoundsError,
)
from axis.visualization.snapshot_models import ReplayCoordinate
from axis.visualization.viewer_state import (
    OverlayConfig,
    PlaybackMode,
    ViewerState,
)


# -- Navigation ---------------------------------------------------------------


def next_step(state: ViewerState) -> ViewerState:
    """Advance to the next step, preserving current phase.

    Returns *state* unchanged at the last step.
    """
    total = state.episode_handle.validation.total_steps
    if state.coordinate.step_index >= total - 1:
        return state
    return state.model_copy(
        update={
            "coordinate": ReplayCoordinate(
                step_index=state.coordinate.step_index + 1,
                phase_index=state.coordinate.phase_index,
            ),
        },
    )


def previous_step(state: ViewerState) -> ViewerState:
    """Move to the previous step, preserving current phase.

    Returns *state* unchanged at step 0.
    """
    if state.coordinate.step_index <= 0:
        return state
    return state.model_copy(
        update={
            "coordinate": ReplayCoordinate(
                step_index=state.coordinate.step_index - 1,
                phase_index=state.coordinate.phase_index,
            ),
        },
    )


def set_phase(state: ViewerState, phase_index: int) -> ViewerState:
    """Change the current phase without altering the step index."""
    return state.model_copy(
        update={
            "coordinate": ReplayCoordinate(
                step_index=state.coordinate.step_index,
                phase_index=phase_index,
            ),
        },
    )


def seek(state: ViewerState, coordinate: ReplayCoordinate) -> ViewerState:
    """Jump to an arbitrary replay coordinate.

    Raises StepOutOfBoundsError if the coordinate is out of bounds.
    """
    total = state.episode_handle.validation.total_steps
    if coordinate.step_index < 0 or coordinate.step_index >= total:
        raise StepOutOfBoundsError(coordinate.step_index, total)
    return state.model_copy(update={"coordinate": coordinate})


# -- Selection -----------------------------------------------------------------


def select_cell(state: ViewerState, row: int, col: int) -> ViewerState:
    """Select a grid cell, clearing any agent selection."""
    gw = state.episode_handle.validation.grid_width
    gh = state.episode_handle.validation.grid_height
    if gw is None or gh is None:
        raise CellOutOfBoundsError(row, col, 0, 0)
    if row < 0 or row >= gh or col < 0 or col >= gw:
        raise CellOutOfBoundsError(row, col, gw, gh)
    return state.model_copy(
        update={"selected_cell": (row, col), "selected_agent": False},
    )


def select_agent(state: ViewerState) -> ViewerState:
    """Select the agent, clearing any cell selection."""
    return state.model_copy(
        update={"selected_agent": True, "selected_cell": None},
    )


def clear_selection(state: ViewerState) -> ViewerState:
    """Clear all selection state."""
    return state.model_copy(
        update={"selected_cell": None, "selected_agent": False},
    )


# -- Playback ------------------------------------------------------------------


def set_playback_mode(
    state: ViewerState, mode: PlaybackMode,
) -> ViewerState:
    """Change the playback mode."""
    return state.model_copy(update={"playback_mode": mode})


# -- Overlay configuration -----------------------------------------------------


def toggle_overlay_master(state: ViewerState) -> ViewerState:
    """Flip the master overlay flag."""
    cfg = state.overlay_config
    return state.model_copy(
        update={
            "overlay_config": cfg.model_copy(
                update={"master_enabled": not cfg.master_enabled},
            ),
        },
    )


def set_overlay_enabled(
    state: ViewerState, overlay_key: str, enabled: bool,
) -> ViewerState:
    """Enable or disable a specific overlay type by its key.

    *overlay_key* is the key from OverlayTypeDeclaration
    (e.g. "action_preference", "scan_result").
    """
    cfg = state.overlay_config
    if enabled:
        new_set = cfg.enabled_overlays | {overlay_key}
    else:
        new_set = cfg.enabled_overlays - {overlay_key}
    return state.model_copy(
        update={
            "overlay_config": cfg.model_copy(
                update={"enabled_overlays": frozenset(new_set)},
            ),
        },
    )
```

**Key changes from v0.1.0**:
- `set_phase(state, phase: ReplayPhase)` becomes `set_phase(state, phase_index: int)` -- takes a plain int
- `toggle_debug_overlay` becomes `toggle_overlay_master` -- same semantics, renamed for generic overlay system
- `set_overlay_type_enabled(state, field_name, enabled)` becomes `set_overlay_enabled(state, overlay_key, enabled)` -- takes a string key from `OverlayTypeDeclaration` instead of a config field name
- All other transition functions are structurally identical

### 4. Playback Controller

**File**: `src/axis/visualization/playback_controller.py` (new)

```python
"""Playback and Navigation Controller.

Canonical replay traversal layer between raw ViewerState transitions
and the UI. Stateless, deterministic, UI-independent.

Adapts to variable phase counts using num_phases from ViewerState.
"""

from __future__ import annotations

from axis.visualization.replay_models import ReplayEpisodeHandle
from axis.visualization.snapshot_models import ReplayCoordinate
from axis.visualization.viewer_state import (
    PlaybackMode,
    ViewerState,
)
from axis.visualization.viewer_state_transitions import (
    seek,
    set_phase as _set_phase,
    set_playback_mode,
)


# -- Boundary helpers -----------------------------------------------------------


def get_initial_coordinate(
    episode_handle: ReplayEpisodeHandle,
) -> ReplayCoordinate:
    """Return the earliest valid replay coordinate: (0, 0)."""
    return ReplayCoordinate(step_index=0, phase_index=0)


def get_final_coordinate(
    episode_handle: ReplayEpisodeHandle,
    num_phases: int,
) -> ReplayCoordinate:
    """Return the latest valid replay coordinate: (last_step, last_phase)."""
    last = episode_handle.validation.total_steps - 1
    return ReplayCoordinate(step_index=last, phase_index=num_phases - 1)


def is_at_initial(state: ViewerState) -> bool:
    """True when *state* is at the initial replay coordinate."""
    return state.coordinate == get_initial_coordinate(state.episode_handle)


def is_at_final(state: ViewerState) -> bool:
    """True when *state* is at the final replay coordinate."""
    return state.coordinate == get_final_coordinate(
        state.episode_handle, state.num_phases,
    )


# -- PlaybackController ---------------------------------------------------------


class PlaybackController:
    """Deterministic replay control layer.

    Orchestrates transition primitives to implement phase-aware
    navigation and playback progression. Adapts to any phase count
    via state.num_phases.
    """

    def step_forward(self, state: ViewerState) -> ViewerState:
        """Advance one replay unit in phase order.

        Traversal for 3-phase system:
            (i, 0) -> (i, 1) -> (i, 2) -> (i+1, 0)

        Traversal for 2-phase system:
            (i, 0) -> (i, 1) -> (i+1, 0)

        Returns *state* unchanged at the final replay position.
        """
        if is_at_final(state):
            return state

        phase_idx = state.coordinate.phase_index

        if phase_idx < state.num_phases - 1:
            # Advance to next phase within the same step.
            return _set_phase(state, phase_idx + 1)

        # At last phase — move to next step's first phase.
        coord = ReplayCoordinate(
            step_index=state.coordinate.step_index + 1,
            phase_index=0,
        )
        return seek(state, coord)

    def step_backward(self, state: ViewerState) -> ViewerState:
        """Move back one replay unit in reverse phase order.

        Returns *state* unchanged at the initial replay position.
        """
        if is_at_initial(state):
            return state

        phase_idx = state.coordinate.phase_index

        if phase_idx > 0:
            # Move to previous phase within the same step.
            return _set_phase(state, phase_idx - 1)

        # At first phase — move to previous step's last phase.
        coord = ReplayCoordinate(
            step_index=state.coordinate.step_index - 1,
            phase_index=state.num_phases - 1,
        )
        return seek(state, coord)

    def seek_to_step(
        self, state: ViewerState, step_index: int,
    ) -> ViewerState:
        """Jump to (step_index, 0).

        Raises StepOutOfBoundsError for invalid *step_index*.
        """
        coord = ReplayCoordinate(step_index=step_index, phase_index=0)
        return seek(state, coord)

    def seek_to_coordinate(
        self, state: ViewerState, coordinate: ReplayCoordinate,
    ) -> ViewerState:
        """Jump to an arbitrary replay coordinate."""
        return seek(state, coordinate)

    def set_phase(
        self, state: ViewerState, phase_index: int,
    ) -> ViewerState:
        """Change the current phase without altering the step index."""
        return _set_phase(state, phase_index)

    def tick(self, state: ViewerState) -> ViewerState:
        """One playback tick — advance if PLAYING, no-op otherwise.

        * PLAYING: if at terminal position, transition to STOPPED;
          otherwise advance via step_forward.
        * PAUSED / STOPPED: return *state* unchanged.
        """
        if state.playback_mode is not PlaybackMode.PLAYING:
            return state

        if is_at_final(state):
            return set_playback_mode(state, PlaybackMode.STOPPED)

        return self.step_forward(state)
```

**Key changes from v0.1.0**:
- `_PHASE_ORDER` tuple and `_PHASE_INDEX` dict removed -- replaced by `state.num_phases` integer arithmetic
- `get_final_coordinate()` takes `num_phases: int` parameter
- `step_forward` / `step_backward` use `state.num_phases` for phase boundary detection instead of indexing into `_PHASE_ORDER`
- `set_phase` takes `phase_index: int` instead of `phase: ReplayPhase`
- All phase references are integers, no `ReplayPhase` enum

---

## Out of Scope

- View model building (WP-V.3.4)
- Any PySide6 code
- Playback speed configuration (will be added in WP-V.4.3)
- Keyboard shortcuts or timer integration

---

## Architectural Constraints

### 1. Pure State Transitions

All transition functions are pure: `(ViewerState[, params]) -> ViewerState`. No mutation, no side effects, no async.

### 2. PlaybackController is Stateless

The controller has no instance state. All methods are pure functions of `(ViewerState[, params]) -> ViewerState`. It could be a module-level function set, but the class groups related operations.

### 3. Phase Count from ViewerState

The `num_phases` field on `ViewerState` is the single source of truth for phase count. It is set once at initialization from `len(system_adapter.phase_names())` and never changes during a session.

### 4. Overlay Keys are Strings

Overlay toggle state uses string keys from `OverlayTypeDeclaration.key`. The viewer state has no knowledge of what overlays mean -- it just stores which keys are enabled.

---

## Testing Requirements

**File**: `tests/v02/visualization/test_viewer_state.py` (new)
**File**: `tests/v02/visualization/test_playback_controller.py` (new)

Create a fixture `_sample_episode_handle()` that returns a `ReplayEpisodeHandle` with 5 steps.

### ViewerState tests (`test_viewer_state.py`)

1. **`test_create_initial_state`**: Assert coordinate is (0, 0), mode is STOPPED, no selection
2. **`test_initial_state_with_overlay_keys`**: Create with overlay keys, assert `overlay_config.enabled_overlays` is empty (all start disabled)
3. **`test_step_index_out_of_bounds`**: Assert `ValueError` when step_index >= total_steps
4. **`test_phase_index_out_of_bounds`**: Assert `ValueError` when phase_index >= num_phases
5. **`test_selected_cell_out_of_bounds`**: Assert `ValueError` for invalid cell
6. **`test_overlay_config_frozen`**: Assert `OverlayConfig` is immutable

### State transition tests

7. **`test_next_step`**: Assert step_index increments, phase preserved
8. **`test_next_step_at_last`**: Assert identity at last step
9. **`test_previous_step`**: Assert step_index decrements, phase preserved
10. **`test_previous_step_at_first`**: Assert identity at step 0
11. **`test_set_phase`**: Assert phase_index changes, step preserved
12. **`test_seek`**: Assert both step and phase change
13. **`test_seek_out_of_bounds`**: Assert `StepOutOfBoundsError`
14. **`test_select_cell`**: Assert selected_cell set, agent deselected
15. **`test_select_cell_out_of_bounds`**: Assert `CellOutOfBoundsError`
16. **`test_select_agent`**: Assert selected_agent set, cell deselected
17. **`test_clear_selection`**: Assert both cleared
18. **`test_set_playback_mode`**: Assert mode changes
19. **`test_toggle_overlay_master`**: Assert master_enabled flips
20. **`test_set_overlay_enabled`**: Enable "action_preference", assert in set
21. **`test_set_overlay_disabled`**: Disable overlay, assert removed from set

### Playback controller tests (`test_playback_controller.py`)

#### 3-phase traversal

22. **`test_step_forward_within_step`**: (0, 0) → (0, 1) → (0, 2)
23. **`test_step_forward_cross_step`**: (0, 2) → (1, 0)
24. **`test_step_forward_at_final`**: Identity at (4, 2)
25. **`test_step_backward_within_step`**: (0, 2) → (0, 1) → (0, 0)
26. **`test_step_backward_cross_step`**: (1, 0) → (0, 2)
27. **`test_step_backward_at_initial`**: Identity at (0, 0)

#### 2-phase traversal

28. **`test_step_forward_2phase`**: (0, 0) → (0, 1) → (1, 0)
29. **`test_step_backward_2phase`**: (1, 0) → (0, 1)

#### Seek and boundary

30. **`test_seek_to_step`**: Jump to (3, 0)
31. **`test_seek_to_coordinate`**: Jump to (2, 1)
32. **`test_is_at_initial`**: True only at (0, 0)
33. **`test_is_at_final_3phase`**: True only at (4, 2) for 3-phase
34. **`test_is_at_final_2phase`**: True only at (4, 1) for 2-phase

#### Tick/playback

35. **`test_tick_stopped`**: No-op when STOPPED
36. **`test_tick_paused`**: No-op when PAUSED
37. **`test_tick_playing`**: Advances when PLAYING
38. **`test_tick_playing_at_final`**: Transitions to STOPPED

---

## Expected Deliverable

1. `src/axis/visualization/viewer_state.py`
2. `src/axis/visualization/viewer_state_transitions.py`
3. `src/axis/visualization/playback_controller.py`
4. `tests/v02/visualization/test_viewer_state.py`
5. `tests/v02/visualization/test_playback_controller.py`
6. Confirmation that all existing tests still pass

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
    viewer_state.py                      # NEW
    viewer_state_transitions.py          # NEW
    playback_controller.py               # NEW
    adapters/
        default_world.py                 # UNCHANGED
        null_system.py                   # UNCHANGED

tests/v02/visualization/
    test_viewer_state.py                 # NEW
    test_playback_controller.py          # NEW
```

---

## Important Final Constraint

The v0.1.0 `debug_overlay_models.py` is **not migrated** -- it is replaced entirely by the `OverlayConfig` model in `viewer_state.py` and the `OverlayData`/`OverlayItem` types from WP-V.1.1. The System A-specific overlay types (`ActionPreferenceOverlay`, `DriveContributionOverlay`, `ConsumptionOpportunityOverlay`) were data models consumed by `GridWidget._draw_overlay_*` methods; in v0.2.0, the system adapter produces `OverlayData` with `OverlayItem` entries, and the `OverlayRenderer` (WP-V.4.2) dispatches on `item_type` strings. No fixed enum of overlay types exists in the base layer.
