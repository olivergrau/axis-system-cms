# WP-1.2 Implementation Brief -- World Contracts

> **Updated:** This spec has been updated to reflect the final implementation.
> Key changes from the original spec:
> - `ActionOutcome` now uses a generic `data: dict[str, Any]` instead of
>   `consumed: bool` and `resource_consumed: float` fields
> - `BaseWorldConfig` now uses `extra="allow"` with only `world_type: str`
>   as a defined field. Grid-specific fields are parsed by `Grid2DWorldConfig`
>   in `axis.world.config`
> - `MutableWorldProtocol` extends `WorldView` with `tick()`,
>   `extract_resource()`, and `snapshot()` methods

## Context

We are implementing the **modular architecture evolution** of the AXIS project. WP-1.1 defined the core SDK interfaces (`SystemInterface`, `SensorInterface`, etc.).

This work package is **WP-1.2**. It defines the world-related contracts: the read-only view systems receive, the outcome returned after action application, shared position and cell types, and the base world configuration.

### Predecessor State (After WP-1.1)

```
src/axis/sdk/
    __init__.py                 # Exports interfaces and types
    interfaces.py               # SystemInterface, SensorInterface, DriveInterface, PolicyInterface, TransitionInterface
    types.py                    # DecideResult, TransitionResult, PolicyResult
```

The interfaces in WP-1.1 reference `world_view`, `action_outcome`, and `position` as `Any`. This WP replaces those with concrete, typed contracts.

### Current v0.1.0 Implementation

The existing world model lives in `axis_system_a`:

| Module | Types/Functions |
|--------|----------------|
| `types.py` | `Position(x: int, y: int)` |
| `enums.py` | `CellType(EMPTY, RESOURCE, OBSTACLE)`, `Action` (6-value IntEnum) |
| `world.py` | `Cell(cell_type, resource_value, regen_eligible)`, `World` (mutable grid container), `create_world()` |
| `config.py` | `WorldConfig(grid_width, grid_height, resource_regen_rate, obstacle_density, regeneration_mode, regen_eligible_ratio)` |

In WP-1.2, we define the **contract types** that abstract these. The actual `World` implementation will be moved in WP-2.1.

### Architectural Decisions (Binding)

- **Q2**: Framework-owned world mutation -- systems receive read-only view, framework applies actions
- **Q4**: Shared base actions (movement + stay), extensible per system (e.g., consume)
- **Q12**: Framework owns world structure (grid size, obstacles); system owns dynamics (regen params)
- **Q14**: Observations are system-defined, opaque to framework

### Reference Documents

- `docs/v0.2.0/architecture/evolution/architectural-vision-v0.2.0.md` -- Section 5 (World Framework)
- `docs/v0.2.0/architecture/evolution/modular-architecture-roadmap.md` -- WP-1.2 definition

---

## Objective

Define the world-related contracts that enable systems to interact with the world without owning or mutating it. This includes:

1. `Position` -- shared grid coordinate type
2. `CellView` -- read-only cell data visible to systems
3. `WorldView` -- read-only world interface passed to systems
4. `ActionOutcome` -- result of action application, returned to systems
5. `BaseWorldConfig` -- framework-level world configuration
6. Base action constants

These are **contract types and protocols**. The mutable `World` implementation and action engine come in Phase 2 (WP-2.1, WP-2.2).

---

## Scope

### 1. Position Type

**File**: `src/axis/sdk/position.py`

```python
from pydantic import BaseModel, ConfigDict


class Position(BaseModel):
    """Grid coordinate.

    Position belongs to the world state, not the agent state.
    The framework tracks agent position; the agent does not know
    its own position directly.
    """

    model_config = ConfigDict(frozen=True)

    x: int
    y: int
```

This is a direct carry-forward from `axis_system_a.types.Position`. It is placed in `axis.sdk` because both the framework and systems reference it.

**Design note**: `Position` is defined as a separate module (not in `types.py`) because it is a foundational type used across all layers. It avoids circular imports since `types.py` in WP-1.1 defines SDK output types, and `Position` is a world type referenced by many.

---

### 2. CellView Type

**File**: `src/axis/sdk/world_types.py`

```python
from pydantic import BaseModel, ConfigDict, Field


class CellView(BaseModel):
    """Read-only view of a single grid cell, as seen by systems.

    This is the system-facing representation of a cell.
    The framework may store additional internal cell data
    (e.g., regen_eligible) that is not exposed to systems.
    """

    model_config = ConfigDict(frozen=True)

    cell_type: str           # "empty", "resource", "obstacle"
    resource_value: float = Field(..., ge=0.0, le=1.0)
```

**Design notes**:

- `cell_type` is a string (not an enum) at the SDK contract level, keeping the SDK free of world-internal enum types. The framework maps its internal `CellType` enum to these strings.
- `resource_value` preserves the existing `[0, 1]` constraint.
- `regen_eligible` is **not** exposed to systems -- it is an internal world property.

---

### 3. WorldView Protocol

**File**: `src/axis/sdk/world_types.py` (same file)

```python
from typing import Protocol, runtime_checkable

from axis.sdk.position import Position


@runtime_checkable
class WorldView(Protocol):
    """Read-only view of the world, passed to systems.

    Systems receive this in decide(). They cannot mutate the world
    through this view. The framework provides the implementation.
    """

    @property
    def width(self) -> int:
        """Grid width."""
        ...

    @property
    def height(self) -> int:
        """Grid height."""
        ...

    @property
    def agent_position(self) -> Position:
        """Current agent position."""
        ...

    def get_cell(self, position: Position) -> CellView:
        """Get the read-only view of a cell.

        Raises ValueError if position is out of bounds.
        """
        ...

    def is_within_bounds(self, position: Position) -> bool:
        """Check if a position is within the grid."""
        ...

    def is_traversable(self, position: Position) -> bool:
        """Check if a position is traversable (not obstacle, within bounds).

        Returns False for out-of-bounds positions (safe to call with any position).
        """
        ...
```

**Design notes**:

- Uses `Protocol` with `@runtime_checkable` for structural subtyping
- Matches the public read-only API of the existing `World` class
- The `World` implementation (WP-2.1) will satisfy this protocol
- No `set_cell`, no `agent_position` setter -- strictly read-only
- `get_cell` returns `CellView`, not the internal `Cell` type

---

### 4. ActionOutcome Type

**File**: `src/axis/sdk/world_types.py` (same file)

```python
class ActionOutcome(BaseModel):
    """Result of applying an action to the world.

    Returned by the framework to the system after action application.
    The system uses this to update its internal state (energy, memory, etc.).

    Universal fields (action, moved, new_position) are provided by the
    framework. The ``data`` dict carries action-specific results set by
    the action handler (e.g. consume results, scan results). Systems
    read what they need from ``data``; the framework never inspects it.
    """

    model_config = ConfigDict(frozen=True)

    action: str
    moved: bool
    new_position: Position
    data: dict[str, Any] = Field(default_factory=dict)
```

**Field descriptions**:

| Field | Source | Purpose |
|-------|--------|---------|
| `action` | Echo of the requested action | Systems can verify which action was applied |
| `moved` | Framework movement handler | True if position changed (movement actions only) |
| `new_position` | Framework, post-action | Agent's new grid position |
| `data` | Action handler | Action-specific result data (e.g. `{"consumed": True, "resource_consumed": 0.5}` for consume, `{"scan_total": 3.2}` for scan). Empty dict for base actions. |

**Design notes**:

- `data` defaults to an empty dict. For base actions (movement, stay), the dict stays empty.
- System-specific action handlers populate `data` with whatever key-value pairs the system's `transition()` method needs. The framework never inspects this dict.
- This replaces the original `consumed`/`resource_consumed` fields, which were System-A-specific. The generic `data` dict enables any system to pass custom action results without modifying the SDK type.

---

### 5. Base World Configuration

**File**: `src/axis/sdk/world_types.py` (same file)

```python
class BaseWorldConfig(BaseModel):
    """Framework-level world configuration.

    Only ``world_type`` is framework-owned. All other fields are
    world-type-specific and passed through to the world factory via
    ``extra="allow"``.  This mirrors how system config is an opaque
    dict validated by the system at instantiation.

    Custom world types add their own fields (e.g. ``hex_radius``) and
    the framework stores them transparently.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    world_type: str = "grid_2d"
```

**Design notes**:

- Contains only `world_type` as a framework-owned routing field
- Uses `extra="allow"` so grid-specific parameters (`grid_width`, `grid_height`, `obstacle_density`, `resource_regen_rate`, `regeneration_mode`, `regen_eligible_ratio`) pass through as Pydantic extras
- The world factory (e.g. the built-in `grid_2d` factory) parses extras into a `Grid2DWorldConfig` for type-safe validation
- This mirrors how `ExperimentConfig.system` is an opaque dict -- world config is similarly opaque to the framework beyond the routing key
- OFAT parameter paths like `framework.world.grid_width` work because Pydantic extras are accessible via `getattr`

---

### 6. Base Action Constants

**File**: `src/axis/sdk/actions.py`

```python
"""Base action constants shared across all systems.

These actions are handled by the framework's world action engine.
Systems may declare additional actions (e.g., 'consume') in their
action_space(). Additional actions require registered handlers.
"""

# Movement actions -- handled by framework
UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"

# Inaction -- handled by framework
STAY = "stay"

# Ordered tuple of base actions
BASE_ACTIONS: tuple[str, ...] = (UP, DOWN, LEFT, RIGHT, STAY)

# Movement direction deltas: action -> (dx, dy)
MOVEMENT_DELTAS: dict[str, tuple[int, int]] = {
    UP: (0, -1),
    DOWN: (0, +1),
    LEFT: (-1, 0),
    RIGHT: (+1, 0),
}
```

**Design notes**:

- Actions are strings, not enums -- enables system extensibility
- `MOVEMENT_DELTAS` carries forward from `transition.py:_MOVEMENT_DELTAS`, translated from `Action` enum to string keys
- Direction convention preserved: `up` = (0, -1), `down` = (0, +1) (y increases downward)
- System A will add `"consume"` to its action space via `action_space()` in WP-2.3

---

### 7. SDK Package Exports Update

**File**: `src/axis/sdk/__init__.py`

Add the new types to the SDK exports:

```python
"""System SDK -- interfaces, contracts, and base types."""

from axis.sdk.actions import BASE_ACTIONS, DOWN, LEFT, MOVEMENT_DELTAS, RIGHT, STAY, UP
from axis.sdk.interfaces import (
    DriveInterface,
    PolicyInterface,
    SensorInterface,
    SystemInterface,
    TransitionInterface,
)
from axis.sdk.position import Position
from axis.sdk.types import DecideResult, PolicyResult, TransitionResult
from axis.sdk.world_types import ActionOutcome, BaseWorldConfig, CellView, WorldView

__all__ = [
    # Interfaces
    "SystemInterface",
    "SensorInterface",
    "DriveInterface",
    "PolicyInterface",
    "TransitionInterface",
    # Data types
    "DecideResult",
    "TransitionResult",
    "PolicyResult",
    "Position",
    "CellView",
    "WorldView",
    "ActionOutcome",
    "BaseWorldConfig",
    # Action constants
    "BASE_ACTIONS",
    "UP",
    "DOWN",
    "LEFT",
    "RIGHT",
    "STAY",
    "MOVEMENT_DELTAS",
]
```

---

## Out of Scope

Do **not** implement any of the following in WP-1.2:

- The mutable `World` class (WP-2.1: World Extraction)
- The `create_world()` factory function (WP-2.1)
- The world action engine / `apply_action()` (WP-2.2)
- World dynamics / regeneration logic (WP-2.2)
- `CellType` enum (internal to world implementation, WP-2.1)
- `WorldSnapshot` (replay contract, WP-1.3)
- Action handler registration (WP-2.2)
- Any `axis_system_a` modifications
- Any modifications outside `src/axis/sdk/` and `tests/v02/`

---

## Architectural Constraints

### 1. SDK Independence

The world contract types live in `axis.sdk` because both the framework and systems reference them. The actual `World` implementation (which satisfies `WorldView`) will live in `axis.world` (WP-2.1).

### 2. String-Based Cell Types

`CellView.cell_type` is a `str`, not an enum. This keeps the SDK free of world-internal enum types. The mapping is:

| Internal `CellType` | `CellView.cell_type` string |
|---|---|
| `CellType.EMPTY` | `"empty"` |
| `CellType.RESOURCE` | `"resource"` |
| `CellType.OBSTACLE` | `"obstacle"` |

### 3. No World Mutation Through Contracts

`WorldView` is strictly read-only. `ActionOutcome` is an after-the-fact report. Systems cannot mutate the world through any contract type.

### 4. Forward Compatibility

The `data: dict[str, Any]` pattern on `ActionOutcome` provides forward compatibility by design. Each system's action handlers populate whatever keys they need, and only that system's `transition()` method reads them. No SDK changes required for new action types.

### 5. Frozen Pydantic Models

All value types (`Position`, `CellView`, `ActionOutcome`, `BaseWorldConfig`) are frozen Pydantic models.

---

## Expected File Structure

After WP-1.2, these files are **new or modified**:

```
src/axis/sdk/__init__.py                    # MODIFIED (new exports)
src/axis/sdk/position.py                    # NEW (Position)
src/axis/sdk/world_types.py                 # NEW (CellView, WorldView, ActionOutcome, BaseWorldConfig)
src/axis/sdk/actions.py                     # NEW (base action constants)
tests/v02/sdk/test_world_contracts.py       # NEW (verification tests)
```

Unchanged:

```
src/axis/sdk/interfaces.py                  # UNCHANGED (from WP-1.1)
src/axis/sdk/types.py                       # UNCHANGED (from WP-1.1)
src/axis_system_a/                          # UNCHANGED
```

---

## Testing Requirements

### World contract verification tests (`tests/v02/sdk/test_world_contracts.py`)

Must include:

1. **Position**:
   - `Position(x=0, y=0)` constructs successfully
   - `Position(x=5, y=3)` fields are accessible
   - Frozen: setting `x` raises
   - Equality: `Position(x=1, y=2) == Position(x=1, y=2)`
   - Hashable: can be used as dict key

2. **CellView**:
   - `CellView(cell_type="empty", resource_value=0.0)` constructs
   - `CellView(cell_type="resource", resource_value=0.75)` constructs
   - `resource_value` out of range `[0, 1]` raises validation error
   - Frozen: setting `cell_type` raises

3. **ActionOutcome**:
   - Default construction: `ActionOutcome(action="up", moved=True, new_position=Position(x=1, y=0))` works with `data` defaulting to `{}`
   - Construction with data: `ActionOutcome(action="consume", moved=False, new_position=..., data={"consumed": True, "resource_consumed": 0.5})` works
   - Frozen: setting `moved` raises

4. **BaseWorldConfig**:
   - `BaseWorldConfig()` works with default `world_type="grid_2d"`
   - `BaseWorldConfig(world_type="hex", hex_radius=5)` accepts custom world type and arbitrary extras
   - `BaseWorldConfig(grid_width=10, grid_height=10)` accepted via `extra="allow"`
   - Frozen: setting fields raises

5. **WorldView protocol**:
   - A mock class with `width`, `height`, `agent_position`, `get_cell`, `is_within_bounds`, `is_traversable` satisfies `isinstance(mock, WorldView)`
   - A class missing `get_cell` does not satisfy the protocol

6. **Base action constants**:
   - `BASE_ACTIONS` contains exactly 5 elements: `"up"`, `"down"`, `"left"`, `"right"`, `"stay"`
   - `MOVEMENT_DELTAS` has exactly 4 entries (no `stay`)
   - `MOVEMENT_DELTAS["up"]` equals `(0, -1)`
   - `MOVEMENT_DELTAS["down"]` equals `(0, 1)`
   - `MOVEMENT_DELTAS["left"]` equals `(-1, 0)`
   - `MOVEMENT_DELTAS["right"]` equals `(1, 0)`

7. **Import verification**:
   - `from axis.sdk import Position, CellView, WorldView, ActionOutcome, BaseWorldConfig` succeeds
   - `from axis.sdk import BASE_ACTIONS, UP, DOWN, LEFT, RIGHT, STAY, MOVEMENT_DELTAS` succeeds

### Existing test suite

All existing tests must still pass.

---

## Implementation Style

- Python 3.11+
- Frozen Pydantic `BaseModel` for value types
- `typing.Protocol` with `@runtime_checkable` for `WorldView`
- Clear, concise docstrings
- Type hints throughout
- No dependencies beyond `pydantic`, `numpy`, stdlib, and `axis.sdk` internals

---

## Expected Deliverable

1. `src/axis/sdk/position.py` with `Position`
2. `src/axis/sdk/world_types.py` with `CellView`, `WorldView`, `ActionOutcome`, `BaseWorldConfig`
3. `src/axis/sdk/actions.py` with base action constants
4. Updated `src/axis/sdk/__init__.py` with full exports
5. Verification tests at `tests/v02/sdk/test_world_contracts.py`
6. Confirmation that all existing tests still pass

---

## Important Final Constraint

This WP defines the **world boundary contracts** -- the types that cross the boundary between the framework (world owner) and systems (world users). Getting these right is critical because:

1. `WorldView` is what every system's sensor will read from
2. `ActionOutcome` is what every system's transition function will process
3. `Position` is referenced by nearly every component
4. `BaseWorldConfig` is what the framework uses to create worlds

These types must be **minimal and stable**. They should not contain fields that only one system needs. System-specific data flows through the opaque `system_data` dicts in the replay contract (WP-1.3), not through these shared types.

The mapping from existing v0.1.0 types to these contracts should be mechanical:

| v0.1.0 | WP-1.2 contract |
|--------|-----------------|
| `types.Position` | `Position` (identical) |
| `world.Cell` fields visible to agent | `CellView` |
| `World` public read methods | `WorldView` protocol |
| Data extracted in `transition.step()` after action | `ActionOutcome` |
| `config.WorldConfig` structural fields | `BaseWorldConfig` |
