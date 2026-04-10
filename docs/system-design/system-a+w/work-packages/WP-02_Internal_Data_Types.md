# WP-2: Internal Data Types

## Metadata
- Work Package: WP-2
- Title: Internal Data Types
- System: System A+W
- Source File: `src/axis/systems/system_aw/types.py`
- Test File: `tests/systems/system_aw/test_types.py`
- Model Reference: `01_System A+W Model.md`, Sections 3, 4, 5.2, 6.4
- Dependencies: WP-1 (config model)

---

## 1. Objective

Define the internal type vocabulary for System A+W. This includes the world model state, curiosity drive output, drive weights, and the extended agent state. All types are frozen Pydantic v2 models, consistent with System A's design.

---

## 2. Design

### 2.1 Type Reuse from System A

The following types from `axis.systems.system_a.types` are reused **without modification**:

| Type | Used by | Reason for reuse |
|---|---|---|
| `CellObservation` | Sensor, curiosity drive | Observation format unchanged (Section 1.1) |
| `Observation` | Sensor, memory, drives | Von Neumann neighborhood unchanged |
| `HungerDriveOutput` | Hunger drive | Hunger drive output format unchanged |
| `BufferEntry` | Memory | Memory entry format unchanged |
| `ObservationBuffer` | Memory, curiosity drive | FIFO buffer unchanged; capacity is configurable |
| `clip_energy` | Transition | Energy clipping utility unchanged |

These are imported into the `system_aw` package — not copied or re-exported from `types.py`. Modules that need them import directly from `axis.systems.system_a.types`.

### 2.2 New Types

| Type | Model Reference | Purpose |
|---|---|---|
| `WorldModelState` | Section 4.1 | Relative position + visit-count map |
| `CuriosityDriveOutput` | Section 5.2, 6.3 | Curiosity activation + novelty signals + per-action contributions |
| `DriveWeights` | Section 6.4 | Dynamic hunger and curiosity weights |
| `AgentStateAW` | Section 4 | Extended agent state: energy + memory + world model |

---

## 3. Specification

### 3.1 WorldModelState

Encapsulates the dead reckoning position and visit-count map (Model Section 4.1).

```python
class WorldModelState(BaseModel):
    """Spatial world model: relative position + visit counts.

    The world model uses agent-relative coordinates maintained
    through dead reckoning (path integration). No absolute position
    data is stored or consumed.

    Model reference: Section 4.1.
    """

    model_config = ConfigDict(frozen=True)

    relative_position: tuple[int, int] = Field(
        default=(0, 0),
        description="Agent's position estimate via dead reckoning, relative to start",
    )
    visit_counts: tuple[tuple[tuple[int, int], int], ...] = Field(
        default_factory=tuple,
        description="Immutable sequence of ((x, y), count) pairs",
    )
```

**Design decision: immutable visit counts.**

Visit counts are stored as a sorted tuple of `((x, y), count)` pairs rather than a dict, because Pydantic frozen models require hashable field values. The `world_model.py` module (WP-4) will provide helper functions to convert between the internal tuple representation and working dicts for efficient lookup.

**Alternative considered:** Store as `dict[tuple[int, int], int]` and disable frozen validation for this field. Rejected — inconsistent with the frozen model pattern used throughout the project.

### 3.2 CuriosityDriveOutput

Output of the curiosity drive computation (Model Sections 5.2 and 6.3).

```python
class CuriosityDriveOutput(BaseModel):
    """Output of the curiosity drive computation.

    activation: scalar curiosity level d_C(t) in [0, mu_C]
    spatial_novelty: per-direction spatial novelty (up, down, left, right)
    sensory_novelty: per-direction sensory novelty (up, down, left, right)
    composite_novelty: per-direction composite novelty (up, down, left, right)
    action_contributions: 6-element tuple indexed by action order
        (UP, DOWN, LEFT, RIGHT, CONSUME, STAY)

    Model reference: Sections 5.2, 6.3.
    """

    model_config = ConfigDict(frozen=True)

    activation: float = Field(..., ge=0, le=1)

    spatial_novelty: tuple[float, float, float, float] = Field(
        ..., description="(up, down, left, right)",
    )
    sensory_novelty: tuple[float, float, float, float] = Field(
        ..., description="(up, down, left, right)",
    )
    composite_novelty: tuple[float, float, float, float] = Field(
        ..., description="(up, down, left, right)",
    )

    action_contributions: tuple[
        float, float, float, float, float, float,
    ] = Field(..., description="(UP, DOWN, LEFT, RIGHT, CONSUME, STAY)")
```

**Notes:**
- The 4-tuples use the same directional ordering as `Observation`: (up, down, left, right)
- The 6-tuple `action_contributions` uses the same ordering as `HungerDriveOutput`: (UP, DOWN, LEFT, RIGHT, CONSUME, STAY)
- This parallel structure simplifies the arbitration layer (WP-7), which combines the two drive outputs element-wise
- `activation` is bounded by $[0, \mu_C]$, but since $\mu_C \leq 1.0$, the constraint $[0, 1]$ is sufficient

### 3.3 DriveWeights

Dynamic drive weights from the arbitration function (Model Section 6.4).

```python
class DriveWeights(BaseModel):
    """Dynamic drive weights from the arbitration function.

    w_H(t) = w_H_base + (1 - w_H_base) * d_H(t)^gamma
    w_C(t) = w_C_base * (1 - d_H(t))^gamma

    Model reference: Section 6.4.
    """

    model_config = ConfigDict(frozen=True)

    hunger_weight: float = Field(..., ge=0, description="w_H(t)")
    curiosity_weight: float = Field(..., ge=0, description="w_C(t)")
```

### 3.4 AgentStateAW

Extended agent state including the world model (Model Section 4).

```python
class AgentStateAW(BaseModel):
    """System A+W agent state: energy + memory + world model.

    Extends System A's AgentState with the spatial world model.
    Position is explicitly NOT part of AgentStateAW in the absolute
    sense -- only the *relative* position estimate (inside WorldModelState)
    is tracked, via dead reckoning.

    Model reference: Section 4.
    """

    model_config = ConfigDict(frozen=True)

    energy: float = Field(..., ge=0)
    observation_buffer: ObservationBuffer
    world_model: WorldModelState
```

**Notes:**
- `energy` and `observation_buffer` have identical semantics to `AgentState` in System A
- `world_model` is the new component containing the relative position and visit counts
- `AgentStateAW` does **not** inherit from System A's `AgentState` — it is a new, independent model. This avoids issues with Pydantic frozen model inheritance while keeping the types explicit
- The `ObservationBuffer` type is imported from `axis.systems.system_a.types`

---

## 4. Action Ordering Convention

Both drive output types use the same 6-element action ordering:

| Index | Action | Symbol |
|---|---|---|
| 0 | UP | $a_{up}$ |
| 1 | DOWN | $a_{down}$ |
| 2 | LEFT | $a_{left}$ |
| 3 | RIGHT | $a_{right}$ |
| 4 | CONSUME | $a_{consume}$ |
| 5 | STAY | $a_{stay}$ |

This matches the existing `HungerDriveOutput.action_contributions` ordering from System A. Maintaining this convention ensures the arbitration layer can combine drive outputs by simple element-wise operations.

---

## 5. Direction Ordering Convention

The 4-element novelty tuples use the same directional ordering as `Observation`:

| Index | Direction | Delta $\Delta(dir)$ |
|---|---|---|
| 0 | UP | $(0, +1)$ |
| 1 | DOWN | $(0, -1)$ |
| 2 | LEFT | $(-1, 0)$ |
| 3 | RIGHT | $(+1, 0)$ |

---

## 6. Test Plan

### File: `tests/systems/system_aw/test_types.py`

| # | Test | Description |
|---|---|---|
| 1 | `test_world_model_state_defaults` | Default `WorldModelState` has `relative_position=(0,0)` and empty visit counts |
| 2 | `test_world_model_state_with_visits` | Construct with visits, verify stored correctly |
| 3 | `test_world_model_state_frozen` | Assignment raises error |
| 4 | `test_curiosity_drive_output_valid` | Construct with valid values, verify all fields |
| 5 | `test_curiosity_drive_output_activation_bounds` | `activation < 0` or `> 1` raises `ValidationError` |
| 6 | `test_curiosity_drive_output_tuple_lengths` | Wrong-length tuples raise errors |
| 7 | `test_drive_weights_valid` | Construct and verify |
| 8 | `test_drive_weights_nonneg` | Negative weights raise `ValidationError` |
| 9 | `test_agent_state_aw_valid` | Full construction with energy, memory, world model |
| 10 | `test_agent_state_aw_frozen` | Assignment raises error |
| 11 | `test_agent_state_aw_energy_nonneg` | Negative energy raises `ValidationError` |
| 12 | `test_action_ordering_consistency` | `HungerDriveOutput` and `CuriosityDriveOutput` use same 6-element ordering (verify by index correspondence) |
| 13 | `test_world_model_state_serializable` | `model_dump()` succeeds and round-trips through `model_validate()` |
| 14 | `test_agent_state_aw_serializable` | Full `AgentStateAW` round-trips through serialization |

---

## 7. Acceptance Criteria

- [ ] All new types are frozen Pydantic v2 models
- [ ] `AgentStateAW` composes energy + memory + world model
- [ ] `WorldModelState` contains relative position (not absolute) and visit counts
- [ ] `CuriosityDriveOutput` carries activation, all three novelty layers, and per-action contributions
- [ ] Action ordering matches `HungerDriveOutput` (6-element: UP, DOWN, LEFT, RIGHT, CONSUME, STAY)
- [ ] Direction ordering matches `Observation` (4-element: up, down, left, right)
- [ ] All types serialize and deserialize correctly (for trace logging)
- [ ] Reused types from System A are imported, not duplicated
- [ ] All 14 tests pass
