# WP-1.3 Implementation Brief -- Replay Contract

## Context

We are implementing the **modular architecture evolution** of the AXIS project. WP-1.1 defined the core SDK interfaces and WP-1.2 defined the world contracts (`Position`, `CellView`, `WorldView`, `ActionOutcome`, `BaseWorldConfig`).

This work package is **WP-1.3**. It defines the **global replay contract**: the base step trace, episode trace, and snapshot types that form the persistence and visualization contract for all systems.

### Predecessor State (After WP-1.2)

```
src/axis/sdk/
    __init__.py                 # Exports interfaces, types, world contracts
    interfaces.py               # SystemInterface and sub-component interfaces
    types.py                    # DecideResult, TransitionResult, PolicyResult
    position.py                 # Position
    world_types.py              # CellView, WorldView, ActionOutcome, BaseWorldConfig
    actions.py                  # Base action constants
```

### Current v0.1.0 Trace Types

The existing system uses rich, System A-specific trace types:

| Module | Type | Fields |
|--------|------|--------|
| `snapshots.py` | `WorldSnapshot` | `grid: tuple[tuple[Cell, ...], ...]`, `agent_position`, `width`, `height` |
| `snapshots.py` | `AgentSnapshot` | `energy`, `position`, `memory_entry_count`, `memory_timestep_range` |
| `snapshots.py` | `RegenSummary` | `cells_updated`, `regen_rate` |
| `transition.py` | `TransitionTrace` | 3 world snapshots, 2 agent snapshots, 2 memory states, 2 observations, positions, energy values, action, regen summary, termination |
| `results.py` | `StepResult` | timestep, observation, action, drive output, decision trace, transition trace, energies, terminated |
| `results.py` | `EpisodeResult` | steps, total_steps, termination_reason, final agent state, final position, final observation, summary |

In the modular architecture, these split into:

- **Framework-level** (this WP): `WorldSnapshot`, `BaseStepTrace`, `BaseEpisodeTrace` -- system-agnostic, mandatory
- **System-specific**: Drive outputs, decision traces, detailed transition data -- packed into `system_data: dict[str, Any]`

### Architectural Decisions (Binding)

- **Q8**: Base trace + `system_data: dict[str, Any]` for extension
- **Q9**: 2 mandatory snapshots (`BEFORE`, `AFTER_ACTION`) + optional named intermediates
- **Q13**: Clean break -- no legacy artifact support required
- **Q15**: Mandatory normalized vitality metric `[0, 1]`
- **Q17**: Fixed minimal phase set (`BEFORE`, `AFTER_ACTION`) + optional system-declared extras

### Reference Documents

- `docs/architecture/evolution/architectural-vision-v0.2.0.md` -- Section 7 (Replay Contract)
- `docs/architecture/evolution/modular-architecture-roadmap.md` -- WP-1.3 definition

---

## Objective

Define the global replay contract types that form the serialization/persistence boundary for all episode data. This includes:

1. `WorldSnapshot` -- immutable capture of the world grid state
2. `BaseStepTrace` -- the mandatory per-step data all systems must produce
3. `BaseEpisodeTrace` -- the mandatory per-episode envelope
4. Supporting types for snapshot construction

These types are the **visualization and persistence contract**. All persisted episode data must conform to these schemas. The visualization layer reads these types to render replays.

---

## Scope

### 1. WorldSnapshot Type

**File**: `src/axis/sdk/snapshot.py`

```python
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axis.sdk.position import Position
from axis.sdk.world_types import CellView


class WorldSnapshot(BaseModel):
    """Immutable snapshot of the world grid state at a point in time.

    Used for replay visualization and audit trail. Contains the full
    grid state and agent position. This is the framework-level snapshot;
    system-specific state (agent energy, memory) is in system_data.
    """

    model_config = ConfigDict(frozen=True)

    grid: tuple[tuple[CellView, ...], ...]    # grid[row][col], nested immutable tuples
    agent_position: Position
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
```

**Design notes**:

- The grid uses `CellView` (not the internal `Cell` type) -- this is the read-only, system-facing representation
- Grid is row-major: `grid[y][x]` or equivalently `grid[row][col]`
- Corresponds to the existing `WorldSnapshot` from `axis_system_a.snapshots`, but uses `CellView` instead of `Cell`
- The existing `WorldSnapshot` stores `Cell` objects with `regen_eligible` -- the new one stores `CellView` without it. This is intentional: replay data should expose only what systems and visualization need

### 2. BaseStepTrace Type

**File**: `src/axis/sdk/trace.py`

```python
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot


class BaseStepTrace(BaseModel):
    """The global replay contract for a single simulation step.

    Every system must produce data conforming to this schema.
    The framework assembles this from system outputs and world state.

    System-specific data (drive outputs, decision traces, detailed
    transition data) is packed into system_data as an opaque dict.
    Only the system's visualization adapter interprets it.
    """

    model_config = ConfigDict(frozen=True)

    # ── Step identification ──
    timestep: int = Field(..., ge=0)
    action: str

    # ── World snapshots (mandatory) ──
    world_before: WorldSnapshot
    world_after: WorldSnapshot

    # ── World snapshots (optional, system-declared) ──
    intermediate_snapshots: dict[str, WorldSnapshot] = Field(default_factory=dict)

    # ── Agent position ──
    agent_position_before: Position
    agent_position_after: Position

    # ── Vitality (normalized [0, 1]) ──
    vitality_before: float = Field(..., ge=0.0, le=1.0)
    vitality_after: float = Field(..., ge=0.0, le=1.0)

    # ── Termination ──
    terminated: bool
    termination_reason: str | None = None

    # ── System-specific trace data ──
    system_data: dict[str, Any] = Field(default_factory=dict)
```

**Field descriptions**:

| Field | Source | Purpose |
|-------|--------|---------|
| `timestep` | Framework step counter | Step index within episode (0-based) |
| `action` | `DecideResult.action` from system | The action name that was applied |
| `world_before` | Framework snapshot before step | World state before dynamics and action |
| `world_after` | Framework snapshot after action | World state after all mutations |
| `intermediate_snapshots` | System-declared via framework | Named snapshots (e.g., `"after_regen"` for System A) |
| `agent_position_before` | World state before action | Agent position at step start |
| `agent_position_after` | `ActionOutcome.new_position` | Agent position after action |
| `vitality_before` | `system.vitality(state)` before step | Normalized metric at step start |
| `vitality_after` | `system.vitality(new_state)` after step | Normalized metric after transition |
| `terminated` | `TransitionResult.terminated` or framework | Whether episode ends at this step |
| `termination_reason` | System or framework | `"energy_depleted"`, `"max_steps_reached"`, etc. |
| `system_data` | `DecideResult.decision_data` + `TransitionResult.trace_data` merged | All system-specific trace information |

**Design notes on `system_data`**:

The framework merges `DecideResult.decision_data` and `TransitionResult.trace_data` into a single `system_data` dict. The merge strategy is simple dict merge (decision_data first, then trace_data). If there are key collisions, trace_data wins. Systems should namespace their keys to avoid collisions (e.g., `"decision": {...}`, `"transition": {...}`).

For System A, `system_data` will contain:

```python
{
    "decision": {
        "observation": {...},          # Observation as dict
        "drive_output": {...},         # HungerDriveOutput as dict
        "decision_trace": {...},       # DecisionTrace as dict
    },
    "transition": {
        "energy_before": 45.0,
        "energy_after": 43.5,
        "energy_delta": -1.5,
        "resource_consumed": 0.0,
        "buffer_entries_before": 3,
        "buffer_entries_after": 4,
        "agent_snapshot_before": {...},
        "agent_snapshot_after": {...},
        "regen_summary": {...},
    },
}
```

**Design notes on `intermediate_snapshots`**:

- Default is an empty dict (no intermediates)
- System A will provide `{"after_regen": WorldSnapshot}` -- the world state after regeneration but before action
- This maps to the existing `world_after_regen` in `TransitionTrace`
- Visualization adapters use the phase names to look up snapshots
- The framework captures intermediates at system-declared points (the system declares phase names, the framework captures snapshots at those points)

### 3. BaseEpisodeTrace Type

**File**: `src/axis/sdk/trace.py` (same file)

```python
class BaseEpisodeTrace(BaseModel):
    """The global replay contract for a complete episode.

    Contains the sequence of step traces and episode-level metadata.
    This is the top-level type serialized to disk per episode.
    """

    model_config = ConfigDict(frozen=True)

    system_type: str
    steps: tuple[BaseStepTrace, ...]
    total_steps: int = Field(..., ge=0)
    termination_reason: str
    final_vitality: float = Field(..., ge=0.0, le=1.0)
    final_position: Position
```

**Field descriptions**:

| Field | Source | Purpose |
|-------|--------|---------|
| `system_type` | `SystemInterface.system_type()` | Identifies which system produced this trace |
| `steps` | Accumulated `BaseStepTrace` per step | The full step record |
| `total_steps` | `len(steps)` | Convenience field for quick access |
| `termination_reason` | Last step's termination reason or `"max_steps_reached"` | Why the episode ended |
| `final_vitality` | Last step's `vitality_after` | Vitality at end of episode |
| `final_position` | Last step's `agent_position_after` | Position at end of episode |

**Design notes**:

- No `final_agent_state` at the framework level -- agent state is opaque. Only `final_vitality` and `final_position` are framework-readable.
- No `EpisodeSummary` equivalent here -- that's a derived artifact computed during run aggregation (WP-3.3).
- `termination_reason` is required (not optional) because every episode must end for a reason.

### 4. Snapshot Helper Function Signature

**File**: `src/axis/sdk/snapshot.py` (same file as WorldSnapshot)

Define the signature for the snapshot construction function. The implementation will come in WP-2.1 when the `World` class moves to `axis.world`.

```python
def snapshot_world(world_view: "WorldView", width: int, height: int) -> WorldSnapshot:
    """Create an immutable snapshot of the current world state.

    Iterates over all cells via WorldView.get_cell() and captures
    them as CellView instances in a nested tuple structure.

    Args:
        world_view: Read-only view of the world.
        width: Grid width.
        height: Grid height.

    Returns:
        A frozen WorldSnapshot capturing the complete grid state.
    """
    grid = tuple(
        tuple(
            world_view.get_cell(Position(x=x, y=y))
            for x in range(width)
        )
        for y in range(height)
    )
    return WorldSnapshot(
        grid=grid,
        agent_position=world_view.agent_position,
        width=width,
        height=height,
    )
```

**Design note**: This function is implemented here (not deferred) because it only depends on `WorldView` (a protocol) and SDK types. It does not depend on the mutable `World` class.

### 5. SDK Package Exports Update

**File**: `src/axis/sdk/__init__.py`

Add the replay contract types to the SDK exports:

```python
from axis.sdk.snapshot import WorldSnapshot, snapshot_world
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
```

Added to `__all__`:

```python
"WorldSnapshot",
"snapshot_world",
"BaseStepTrace",
"BaseEpisodeTrace",
```

---

## Out of Scope

Do **not** implement any of the following in WP-1.3:

- `AgentSnapshot` equivalent -- agent state is system-specific, goes in `system_data`
- `RegenSummary` equivalent -- regeneration details go in `system_data`
- `EpisodeSummary` / run-level summary types (WP-3.3)
- Serialization/deserialization logic for persistence (WP-3.4)
- Visualization snapshot resolver (WP-4.1)
- System A-specific trace packing (WP-2.3)
- Any `axis_system_a` modifications
- Any modifications outside `src/axis/sdk/` and `tests/`

---

## Architectural Constraints

### 1. Two Mandatory Snapshots

Every step produces exactly two mandatory world snapshots:

| Snapshot | Timing | Field |
|----------|--------|-------|
| `world_before` | Before any step processing (before dynamics and action) | `BaseStepTrace.world_before` |
| `world_after` | After all mutations (after dynamics and action) | `BaseStepTrace.world_after` |

Systems may request intermediate snapshots (e.g., System A wants `after_regen`). These are stored in `intermediate_snapshots` with string keys matching the system's declared phase names.

### 2. Vitality, Not Energy

The replay contract uses `vitality` (normalized `[0, 1]`), not raw energy. This is the framework-readable metric from `SystemInterface.vitality()`. For System A, vitality = energy / max_energy. System-specific raw energy values go in `system_data`.

### 3. system_data Opacity

The framework never reads, validates, or interprets `system_data`. It:

- Assembles it from `DecideResult.decision_data` and `TransitionResult.trace_data`
- Serializes it as part of `BaseStepTrace`
- Passes it through to the visualization layer

Only the system's visualization adapter (WP-4.2) interprets `system_data`.

### 4. WorldSnapshot Uses CellView

`WorldSnapshot.grid` contains `CellView` instances, not internal `Cell` types. This means:

- `regen_eligible` is not in the snapshot (system-internal)
- `cell_type` is a string
- The snapshot is framework-level data, not tied to any specific world implementation

### 5. Clean Break from v0.1.0 Traces

No backward compatibility with v0.1.0 `StepResult`, `EpisodeResult`, `TransitionTrace`, or `WorldSnapshot` types. The new types are designed from the ground up for multi-system support.

### 6. Frozen Pydantic Models

All types are frozen Pydantic models with `ConfigDict(frozen=True)`.

### 7. No Circular Dependencies

The dependency chain within `axis.sdk` is:

```
position.py          -- no sdk imports
world_types.py       -- imports position
snapshot.py          -- imports position, world_types
trace.py             -- imports position, snapshot
types.py             -- no sdk imports
interfaces.py        -- imports types (uses Any for world types)
actions.py           -- no sdk imports
```

No circular dependencies.

---

## Expected File Structure

After WP-1.3, these files are **new or modified**:

```
src/axis/sdk/__init__.py                    # MODIFIED (new exports)
src/axis/sdk/snapshot.py                    # NEW (WorldSnapshot, snapshot_world)
src/axis/sdk/trace.py                       # NEW (BaseStepTrace, BaseEpisodeTrace)
tests/sdk/test_replay_contract.py       # NEW (verification tests)
```

Unchanged:

```
src/axis/sdk/interfaces.py                  # UNCHANGED
src/axis/sdk/types.py                       # UNCHANGED
src/axis/sdk/position.py                    # UNCHANGED
src/axis/sdk/world_types.py                 # UNCHANGED
src/axis/sdk/actions.py                     # UNCHANGED
src/axis_system_a/                          # UNCHANGED
```

---

## Testing Requirements

### Replay contract verification tests (`tests/sdk/test_replay_contract.py`)

Must include:

1. **WorldSnapshot construction and immutability**:
   - A `WorldSnapshot` with a 2x2 grid constructs successfully
   - `grid[0][0]` returns a `CellView`
   - `width` and `height` match the grid dimensions
   - `agent_position` is accessible
   - Frozen: setting `grid` raises
   - `width=0` raises validation error

2. **snapshot_world function**:
   - Given a mock `WorldView` (2x3 grid), `snapshot_world` produces a `WorldSnapshot` with correct dimensions
   - Grid cells match what the mock returns from `get_cell`
   - Agent position matches the mock's `agent_position`

3. **BaseStepTrace construction**:
   - Minimal construction with all required fields (two snapshots, positions, vitalities, terminated, action, timestep)
   - `intermediate_snapshots` defaults to empty dict
   - `system_data` defaults to empty dict
   - `termination_reason` defaults to `None`
   - Full construction with intermediate snapshots and system_data
   - `vitality_before` out of `[0, 1]` raises validation error
   - `vitality_after` out of `[0, 1]` raises validation error
   - `timestep < 0` raises validation error
   - Frozen

4. **BaseEpisodeTrace construction**:
   - Construction with a tuple of `BaseStepTrace` instances
   - `system_type` is a string
   - `total_steps` matches `len(steps)`
   - `final_vitality` is in `[0, 1]`
   - Frozen

5. **system_data extensibility**:
   - `BaseStepTrace` with nested dict in `system_data` serializes correctly via `model_dump()`
   - Round-trip: `model_dump()` -> `BaseStepTrace(**data)` reconstructs the same trace

6. **intermediate_snapshots**:
   - `BaseStepTrace` with `intermediate_snapshots={"after_regen": WorldSnapshot(...)}` stores and retrieves the snapshot correctly
   - Multiple intermediates work: `{"after_regen": snap1, "after_dynamics": snap2}`

7. **Import verification**:
   - `from axis.sdk import WorldSnapshot, snapshot_world, BaseStepTrace, BaseEpisodeTrace` succeeds

### Existing test suite

All existing tests must still pass.

---

## Implementation Style

- Python 3.11+
- Frozen Pydantic `BaseModel` for all types
- Clear docstrings with field-level documentation
- Pydantic Field validators (`ge`, `le`, `gt`) for numeric constraints
- Type hints throughout
- No dependencies beyond `pydantic`, `axis.sdk` internals

---

## Expected Deliverable

1. `src/axis/sdk/snapshot.py` with `WorldSnapshot` and `snapshot_world`
2. `src/axis/sdk/trace.py` with `BaseStepTrace` and `BaseEpisodeTrace`
3. Updated `src/axis/sdk/__init__.py` with full exports
4. Verification tests at `tests/sdk/test_replay_contract.py`
5. Confirmation that all existing tests still pass

---

## Important Final Constraint

The replay contract is the **central data bridge** between execution and visualization. It must be:

1. **System-agnostic**: No System A-specific fields in the base types
2. **Complete for base visualization**: Grid, agent position, vitality, action -- enough to render a basic replay for any system
3. **Extensible for rich visualization**: `system_data` carries everything a system adapter needs
4. **Serializable**: All types round-trip through `model_dump(mode="json")` / reconstruction

The key design tension is between richness and generality. The existing v0.1.0 traces are extremely rich (3 snapshots, 2 agent snapshots, full decision pipeline, memory states). The base contract captures the universal minimum. Everything else goes in `system_data`.

When System A is adapted (WP-2.3), the mapping should be:

| v0.1.0 trace field | v0.2.0 location |
|---------------------|-----------------|
| `world_before` | `BaseStepTrace.world_before` |
| `world_after_regen` | `BaseStepTrace.intermediate_snapshots["after_regen"]` |
| `world_after_action` | `BaseStepTrace.world_after` |
| `position_before/after` | `BaseStepTrace.agent_position_before/after` |
| `energy_before/after` | `BaseStepTrace.system_data["transition"]["energy_before/after"]` |
| `drive_output` | `BaseStepTrace.system_data["decision"]["drive_output"]` |
| `decision_result` | `BaseStepTrace.system_data["decision"]["decision_trace"]` |
| `agent_snapshot_*` | `BaseStepTrace.system_data["transition"]["agent_snapshot_*"]` |
| `memory_state_*` | `BaseStepTrace.system_data["transition"]["observation_buffer_*"]` |
| `regen_summary` | `BaseStepTrace.system_data["transition"]["regen_summary"]` |
| terminated, reason | `BaseStepTrace.terminated`, `termination_reason` |

If this mapping is awkward or lossy, the trace types need adjustment.
