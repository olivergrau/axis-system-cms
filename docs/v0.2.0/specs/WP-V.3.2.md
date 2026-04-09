# WP-V.3.2 Implementation Brief -- Generalized Snapshot Resolver

## Context

The v0.1.0 `SnapshotResolver` maps `(episode_handle, step_index, ReplayPhase)` to a `ReplaySnapshot`. It uses a fixed `ReplayPhase` IntEnum with exactly 3 values (`BEFORE=0`, `AFTER_REGEN=1`, `AFTER_ACTION=2`) and accesses System A-specific `TransitionTrace` fields (`world_before`, `world_after_regen`, `world_after_action`).

In v0.2.0, phase counts vary by system (System A has 3 phases, System B has 2). The resolver must work with `BaseStepTrace` and system-declared phase names from the adapter's `phase_names()` method and use `phase_index: int` instead of a fixed enum.

### Predecessor State (After WP-V.3.1)

```
src/axis/visualization/
    __init__.py
    types.py
    protocols.py
    registry.py
    errors.py                            # NEW in WP-V.3.1
    replay_models.py                     # NEW in WP-V.3.1
    replay_validation.py                 # NEW in WP-V.3.1
    replay_access.py                     # NEW in WP-V.3.1
    adapters/
        default_world.py
        null_system.py
```

### Phase Mapping from Architecture Spec (Section 13.2)

Given `phase_names = system_adapter.phase_names()` of length N:

| Phase index | Phase name | World snapshot | Agent position | Vitality |
|---|---|---|---|---|
| 0 | first (always "BEFORE") | `step.world_before` | `step.agent_position_before` | `step.vitality_before` |
| 1..N-2 | system-declared intermediates | `step.intermediate_snapshots[name]` | `step.agent_position_before` | `step.vitality_before` |
| N-1 | last (always "AFTER_ACTION") | `step.world_after` | `step.agent_position_after` | `step.vitality_after` |

Intermediate phases use "before" agent state because the agent has not yet acted. The world state may differ (e.g. after regeneration in System A).

### v0.1.0 Source Files Being Migrated

| v0.1.0 file | v0.2.0 destination |
|---|---|
| `axis_system_a/visualization/snapshot_models.py` | `axis/visualization/snapshot_models.py` |
| `axis_system_a/visualization/snapshot_resolver.py` | `axis/visualization/snapshot_resolver.py` |

### Reference Documents

- `docs/v0.2.0/architecture/evolution/visualization-architecture.md` -- Section 13 (SnapshotResolver Generalization)
- `docs/v0.2.0/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.3.2

---

## Objective

Implement the generalized snapshot resolver that maps `(step_index, phase_index)` to a `ReplaySnapshot` using variable phase counts declared by the system adapter.

---

## Scope

### 1. Snapshot Models

**File**: `src/axis/visualization/snapshot_models.py` (new)

```python
"""Snapshot data models for the Visualization Layer.

Defines the replay coordinate system and the resolved snapshot type.
Phase indices replace the v0.1.0 ReplayPhase IntEnum to support
variable phase counts across systems.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot


class ReplayCoordinate(BaseModel):
    """A point in the replay coordinate system: (step_index, phase_index).

    Unlike v0.1.0's ReplayPhase IntEnum, phase_index is a plain int
    that ranges from 0 to len(phase_names)-1, adapting to any system's
    phase count.
    """

    model_config = ConfigDict(frozen=True)

    step_index: int = Field(..., ge=0)
    phase_index: int = Field(..., ge=0)


class ReplaySnapshot(BaseModel):
    """Fully resolved state at a specific replay coordinate.

    Immutable. Contains all state required by downstream rendering.
    System-specific action context is NOT included -- it lives in
    system_data on the BaseStepTrace and is interpreted by the
    system adapter (WP-V.3.4).
    """

    model_config = ConfigDict(frozen=True)

    # Coordinate identification
    step_index: int = Field(..., ge=0)
    phase_index: int = Field(..., ge=0)
    phase_name: str
    timestep: int = Field(..., ge=0)

    # World state at this phase
    world_snapshot: WorldSnapshot

    # Agent state at this phase
    agent_position: Position
    vitality: float = Field(..., ge=0.0, le=1.0)

    # Step-level context (same for all phases of one step)
    action: str
    terminated: bool
    termination_reason: str | None
```

**Key changes from v0.1.0**:
- `phase: ReplayPhase` replaced by `phase_index: int` + `phase_name: str`
- `grid: tuple[tuple[Cell, ...], ...]` / `grid_width` / `grid_height` replaced by single `world_snapshot: WorldSnapshot` (no destructuring -- the world adapter reads the snapshot directly)
- `agent_energy` replaced by `vitality: float` (normalized [0, 1])
- System A-specific fields removed: `action: Action` becomes `action: str`, `consumed`, `resource_consumed`, `energy_delta` removed (these are in `system_data`), `termination_reason: TerminationReason | None` becomes `termination_reason: str | None`
- `moved` removed -- derivable from comparing positions, and available in `system_data`

**Design rationale**: The snapshot is the minimal state needed for the base layer (position, world, vitality, phase). System-specific analysis (drive output, decision pipeline) is provided by the system adapter reading `step_trace.system_data` directly; it does not flow through the snapshot.

### 2. Snapshot Resolver

**File**: `src/axis/visualization/snapshot_resolver.py` (new)

```python
"""Generalized snapshot resolver for the Visualization Layer.

Maps (episode, step_index, phase_index, phase_names) to a fully
resolved ReplaySnapshot. Supports variable phase counts per system.
"""

from __future__ import annotations

from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace

from axis.visualization.errors import (
    PhaseNotAvailableError,
    StepOutOfBoundsError,
)
from axis.visualization.snapshot_models import ReplaySnapshot


class SnapshotResolver:
    """Resolves (episode, step_index, phase_index) -> ReplaySnapshot.

    Pure, stateless resolver. The phase_names list determines how
    phase_index maps to world snapshots and agent state.
    """

    def resolve(
        self,
        episode: BaseEpisodeTrace,
        step_index: int,
        phase_index: int,
        phase_names: list[str],
    ) -> ReplaySnapshot:
        """Resolve a single replay coordinate to a snapshot.

        Args:
            episode: The loaded episode trace.
            step_index: Index into episode.steps.
            phase_index: 0-based phase index (0 to len(phase_names)-1).
            phase_names: System adapter's phase name list.

        Raises:
            StepOutOfBoundsError: step_index is invalid.
            PhaseNotAvailableError: phase has no valid snapshot.
        """
        total = len(episode.steps)
        if step_index < 0 or step_index >= total:
            raise StepOutOfBoundsError(step_index, total)

        num_phases = len(phase_names)
        if phase_index < 0 or phase_index >= num_phases:
            raise PhaseNotAvailableError(step_index, phase_index)

        step = episode.steps[step_index]

        # Phase mapping (Section 13.2 of architecture spec)
        world_snapshot, position, vitality = self._resolve_phase(
            step, phase_index, num_phases, phase_names,
        )

        return ReplaySnapshot(
            step_index=step_index,
            phase_index=phase_index,
            phase_name=phase_names[phase_index],
            timestep=step.timestep,
            world_snapshot=world_snapshot,
            agent_position=position,
            vitality=vitality,
            action=step.action,
            terminated=step.terminated,
            termination_reason=step.termination_reason,
        )

    @staticmethod
    def _resolve_phase(
        step: BaseStepTrace,
        phase_index: int,
        num_phases: int,
        phase_names: list[str],
    ) -> tuple:
        """Map phase_index to (WorldSnapshot, Position, vitality).

        Phase 0 (first): world_before, position_before, vitality_before
        Phase N-1 (last): world_after, position_after, vitality_after
        Phase 1..N-2 (intermediate): intermediate_snapshots[name],
            position_before, vitality_before
        """
        if phase_index == 0:
            # First phase: BEFORE
            return (
                step.world_before,
                step.agent_position_before,
                step.vitality_before,
            )

        if phase_index == num_phases - 1:
            # Last phase: AFTER_ACTION
            return (
                step.world_after,
                step.agent_position_after,
                step.vitality_after,
            )

        # Intermediate phase: lookup by name
        name = phase_names[phase_index]
        snapshot = step.intermediate_snapshots.get(name)
        if snapshot is None:
            raise PhaseNotAvailableError(step.timestep, phase_index)

        return (
            snapshot,
            step.agent_position_before,
            step.vitality_before,
        )
```

**Key changes from v0.1.0**:
- `resolve()` takes `phase_index: int` and `phase_names: list[str]` instead of `phase: ReplayPhase`
- Internal `_select_world_snapshot()` and `_select_agent_state()` replaced by unified `_resolve_phase()` that implements the Section 13.2 mapping
- Reads `BaseStepTrace` fields directly instead of `TransitionTrace`
- Intermediate phases look up `step.intermediate_snapshots[name]` where `name` is the phase name from the adapter
- No `_is_valid_snapshot()` check in the resolver -- validation is done by WP-V.3.1's `validate_episode_for_replay()` before replay starts
- `episode_handle: ReplayEpisodeHandle` parameter simplified to `episode: BaseEpisodeTrace` -- the resolver doesn't need handle metadata, just the trace

**Design note on 2-phase systems**: For System B with `phase_names=["BEFORE", "AFTER_ACTION"]`, `phase_index=0` maps to `world_before` and `phase_index=1` (which is `num_phases-1=1`) maps to `world_after`. No intermediate phases exist. The resolver handles this naturally without special-casing.

---

## Out of Scope

- Viewer state management (WP-V.3.3)
- View model building (WP-V.3.4)
- Any PySide6 code
- Modifications to `BaseStepTrace` or `BaseEpisodeTrace`

---

## Architectural Constraints

### 1. Stateless and Pure

The resolver has no state. Same inputs always yield identical output. No caching, no mutation.

### 2. Phase Names from Adapter

The resolver does not know phase names intrinsically. They are passed in from the system adapter's `phase_names()` method. This keeps the resolver completely system-agnostic.

### 3. No system_data Access

The resolver never reads `step.system_data`. System-specific analysis is the system adapter's responsibility (WP-V.3.4).

### 4. WorldSnapshot Not Destructured

The v0.1.0 snapshot destructured the world into `grid`, `grid_width`, `grid_height`. The v0.2.0 snapshot keeps the `WorldSnapshot` intact and lets the world adapter handle interpretation via `CellLayout`.

---

## Testing Requirements

**File**: `tests/v02/visualization/test_snapshot_resolver.py` (new)

Create fixtures `_sample_episode_2phase()` and `_sample_episode_3phase()` that return `BaseEpisodeTrace` instances with realistic step data.

### Coordinate model tests

1. **`test_replay_coordinate_creation`**: Assert `ReplayCoordinate(step_index=0, phase_index=0)` works
2. **`test_replay_coordinate_frozen`**: Assert assignment raises error

### Snapshot model tests

3. **`test_replay_snapshot_fields`**: Create a `ReplaySnapshot` with all fields, assert values
4. **`test_replay_snapshot_has_phase_name`**: Assert `phase_name` field is present and correct

### 2-phase resolver tests (System B pattern)

5. **`test_resolve_2phase_before`**: phase_index=0 → `world_before`, `position_before`, `vitality_before`
6. **`test_resolve_2phase_after_action`**: phase_index=1 → `world_after`, `position_after`, `vitality_after`
7. **`test_resolve_2phase_invalid_phase`**: phase_index=2 → `PhaseNotAvailableError`

### 3-phase resolver tests (System A pattern)

8. **`test_resolve_3phase_before`**: phase_index=0 → `world_before`
9. **`test_resolve_3phase_intermediate`**: phase_index=1 → `intermediate_snapshots["AFTER_REGEN"]`, `position_before`, `vitality_before`
10. **`test_resolve_3phase_after_action`**: phase_index=2 → `world_after`
11. **`test_resolve_3phase_missing_intermediate`**: Step has no "AFTER_REGEN" in `intermediate_snapshots` → `PhaseNotAvailableError`

### Boundary tests

12. **`test_resolve_step_out_of_bounds_negative`**: step_index=-1 → `StepOutOfBoundsError`
13. **`test_resolve_step_out_of_bounds_too_large`**: step_index=total_steps → `StepOutOfBoundsError`
14. **`test_resolve_first_step`**: step_index=0 works
15. **`test_resolve_last_step`**: step_index=total_steps-1 works

### Phase name passthrough tests

16. **`test_snapshot_phase_name_before`**: Assert `snapshot.phase_name == "BEFORE"`
17. **`test_snapshot_phase_name_intermediate`**: Assert `snapshot.phase_name == "AFTER_REGEN"`
18. **`test_snapshot_phase_name_after_action`**: Assert `snapshot.phase_name == "AFTER_ACTION"`

### Action context tests

19. **`test_snapshot_action_from_step`**: Assert `snapshot.action == step.action`
20. **`test_snapshot_terminated_from_step`**: Assert `snapshot.terminated == step.terminated`
21. **`test_snapshot_termination_reason_from_step`**: Assert `snapshot.termination_reason == step.termination_reason`

---

## Expected Deliverable

1. `src/axis/visualization/snapshot_models.py`
2. `src/axis/visualization/snapshot_resolver.py`
3. `tests/v02/visualization/test_snapshot_resolver.py`
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
    snapshot_models.py                   # NEW
    snapshot_resolver.py                 # NEW
    adapters/
        default_world.py                 # UNCHANGED
        null_system.py                   # UNCHANGED

tests/v02/visualization/
    test_snapshot_resolver.py            # NEW
```
