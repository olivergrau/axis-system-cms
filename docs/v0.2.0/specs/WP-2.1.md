# WP-2.1 Implementation Brief -- World Extraction

## Context

We are implementing the **modular architecture evolution** of the AXIS project. Phase 1 (WP-1.1 through WP-1.4) defined the SDK interfaces, world contracts, replay contract, and framework config types.

This work package is **WP-2.1**. It extracts the world model from `axis_system_a` into the new `axis.world` package, making the `World` class satisfy the `WorldView` protocol defined in WP-1.2.

### Predecessor State (After WP-1.4)

```
src/axis/
    sdk/                                    # Complete: interfaces, types, world contracts, replay, actions
        __init__.py                         # 25 exports
        interfaces.py                       # SystemInterface, SensorInterface, DriveInterface, PolicyInterface, TransitionInterface
        types.py                            # DecideResult, TransitionResult, PolicyResult
        position.py                         # Position(x, y)
        world_types.py                      # CellView, WorldView (protocol), ActionOutcome, BaseWorldConfig
        actions.py                          # UP, DOWN, LEFT, RIGHT, STAY, BASE_ACTIONS, MOVEMENT_DELTAS
        snapshot.py                         # WorldSnapshot, snapshot_world()
        trace.py                            # BaseStepTrace, BaseEpisodeTrace
    framework/
        __init__.py                         # 10 exports
        config.py                           # GeneralConfig, ExecutionConfig, LoggingConfig, FrameworkConfig, ExperimentConfig, OFAT helpers
    world/
        __init__.py                         # Empty placeholder
    systems/system_a/
        __init__.py                         # Empty placeholder
    visualization/
        __init__.py                         # Empty placeholder
```

The world implementation currently lives in `axis_system_a/world.py` as `Cell`, `World`, and `create_world()`. These need to be extracted, adapted, and placed into `axis/world/`.

### Current v0.1.0 Implementation

| Module | Types/Functions | Destination |
|--------|----------------|-------------|
| `axis_system_a/world.py` | `Cell` (frozen Pydantic model) | `axis/world/model.py` |
| `axis_system_a/world.py` | `World` (mutable grid container) | `axis/world/model.py` |
| `axis_system_a/world.py` | `create_world()` | `axis/world/factory.py` |
| `axis_system_a/enums.py` | `CellType` (EMPTY, RESOURCE, OBSTACLE) | `axis/world/model.py` |
| `axis_system_a/enums.py` | `RegenerationMode` | `axis/world/model.py` |

### Architectural Decisions (Binding)

- **Q2**: Framework-owned world mutation -- systems receive `WorldView` (read-only), framework mutates `World` directly
- **Q12**: Framework owns world structure (grid size, obstacles); system owns dynamics (regen params)
- **Q14**: Observations are system-defined -- systems read world through `WorldView`, not internal `Cell`

### Reference Documents

- `docs/v0.2.0/architecture/evolution/architectural-vision-v0.2.0.md` -- Section 5 (World Framework)
- `docs/v0.2.0/architecture/evolution/modular-architecture-roadmap.md` -- WP-2.1 definition
- `docs/v0.2.0/specs/WP-1.2.md` -- WorldView protocol, CellView, BaseWorldConfig
- `docs/v0.2.0/specs/WP-1.3.md` -- WorldSnapshot, snapshot_world()

---

## Objective

Extract the world model into `axis/world/` and adapt it to satisfy the SDK contracts defined in Phase 1:

1. **`CellType` enum** -- internal world enum (`EMPTY`, `RESOURCE`, `OBSTACLE`)
2. **`Cell`** -- internal cell representation (with `regen_eligible`, cell invariants)
3. **`World`** -- mutable grid container that satisfies the `WorldView` protocol
4. **`create_world()`** -- world factory function accepting `BaseWorldConfig`
5. **`get_cell_view()`** -- helper to bridge internal `Cell` to SDK `CellView`

These are **direct extractions** with minimal adaptation. The goal is to decouple the world model from System A so it becomes a shared framework component.

---

## Scope

### 1. CellType Enum

**File**: `src/axis/world/model.py`

```python
import enum

class CellType(enum.Enum):
    """Internal cell type classification."""
    EMPTY = "empty"
    RESOURCE = "resource"
    OBSTACLE = "obstacle"
```

**Design notes**:

- Values are strings matching the `CellView.cell_type` contract from WP-1.2
- This is an **internal** world type, not exported through the SDK. Systems see `CellView.cell_type` strings
- Direct carry-forward from `axis_system_a.enums.CellType` but with string values instead of auto-int

### 2. RegenerationMode Enum

**File**: `src/axis/world/model.py` (same file)

```python
class RegenerationMode(enum.Enum):
    """Regeneration eligibility mode for the world grid."""
    ALL_TRAVERSABLE = "all_traversable"
    SPARSE_FIXED_RATIO = "sparse_fixed_ratio"
```

**Design notes**:

- Carry-forward from `axis_system_a.enums.RegenerationMode`
- Used by the world factory to determine how regen-eligibility is assigned

### 3. Cell Model

**File**: `src/axis/world/model.py` (same file)

```python
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Cell(BaseModel):
    """Internal cell representation.

    Invariants:
    - OBSTACLE: resource_value == 0, not traversable, regen_eligible forced False
    - RESOURCE: resource_value > 0, traversable
    - EMPTY: resource_value == 0, traversable
    """

    model_config = ConfigDict(frozen=True)

    cell_type: CellType
    resource_value: float = Field(..., ge=0, le=1)
    regen_eligible: bool = True

    @model_validator(mode="after")
    def check_cell_invariants(self) -> Cell:
        # Identical logic to axis_system_a.world.Cell
        ...

    @property
    def is_traversable(self) -> bool:
        return self.cell_type != CellType.OBSTACLE
```

**Design notes**:

- Functionally identical to `axis_system_a.world.Cell`
- Frozen Pydantic model
- `regen_eligible` is internal to the world -- not exposed through `CellView`
- The validator enforces cell-type/resource-value consistency

### 4. World Class

**File**: `src/axis/world/model.py` (same file)

```python
from axis.sdk.position import Position
from axis.sdk.world_types import CellView, WorldView

class World:
    """Mutable 2D grid world that satisfies the WorldView protocol.

    The sole mutable container in the runtime. Stores the grid
    of cells and the agent's position. Provides both the internal
    mutation API (for the framework) and the read-only WorldView
    protocol (for systems).
    """

    def __init__(self, grid: list[list[Cell]], agent_position: Position) -> None:
        # Validation: non-empty grid, uniform widths, agent on traversable cell
        ...

    # --- WorldView protocol (read-only) ---

    @property
    def width(self) -> int: ...

    @property
    def height(self) -> int: ...

    @property
    def agent_position(self) -> Position: ...

    def get_cell_view(self, position: Position) -> CellView:
        """Get SDK-facing cell view (bridges internal Cell to CellView)."""
        cell = self.get_cell(position)
        return CellView(
            cell_type=cell.cell_type.value,
            resource_value=cell.resource_value,
        )

    def get_cell(self, position: Position) -> CellView:
        """WorldView protocol implementation.

        Returns CellView (not internal Cell). This satisfies the
        WorldView.get_cell(position) -> CellView signature.
        """
        return self.get_cell_view(position)

    def is_within_bounds(self, position: Position) -> bool: ...

    def is_traversable(self, position: Position) -> bool: ...

    # --- Internal mutation API (framework-only) ---

    @agent_position.setter
    def agent_position(self, position: Position) -> None:
        """Set agent position. Validates bounds and traversability."""
        ...

    def get_internal_cell(self, position: Position) -> Cell:
        """Get the internal Cell (with regen_eligible). Framework-only."""
        ...

    def set_cell(self, position: Position, cell: Cell) -> None:
        """Replace a cell. Framework-only."""
        ...

    def is_regen_eligible(self, position: Position) -> bool:
        """Check regen eligibility. Framework-only."""
        ...
```

**Critical design decision -- `get_cell` returns `CellView`**:

The `WorldView` protocol specifies `get_cell(position: Position) -> CellView`. For `World` to satisfy this protocol, its `get_cell` method must return `CellView`, not the internal `Cell`.

This is a deliberate change from the v0.1.0 `World.get_cell()` which returns `Cell`. The new design:

- `World.get_cell(position)` -> `CellView` (satisfies `WorldView` protocol, used by systems)
- `World.get_internal_cell(position)` -> `Cell` (framework-only, used by action engine and dynamics)

Internal framework code that needs the full `Cell` (with `regen_eligible`) uses `get_internal_cell()`.

### 5. World Factory

**File**: `src/axis/world/factory.py`

```python
from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.world.model import Cell, CellType, RegenerationMode, World

def create_world(
    config: BaseWorldConfig,
    agent_position: Position,
    grid: list[list[Cell]] | None = None,
    *,
    seed: int | None = None,
    regeneration_mode: RegenerationMode = RegenerationMode.ALL_TRAVERSABLE,
    regen_eligible_ratio: float | None = None,
    resource_regen_rate: float = 0.0,
) -> World:
    """Create a World from configuration.

    If grid is None, creates a grid of EMPTY cells.
    If grid is provided, validates dimensions against config.

    Regeneration parameters are system-provided (not part of BaseWorldConfig)
    since systems own their dynamics (Q12).
    """
    ...
```

**Design notes**:

- Accepts `BaseWorldConfig` (the SDK type) instead of the old `WorldConfig`
- Regeneration parameters (`regeneration_mode`, `regen_eligible_ratio`, `resource_regen_rate`) are separate keyword arguments because they are **system-owned dynamics** (per Q12), not part of the framework's `BaseWorldConfig`
- `resource_regen_rate` is accepted here for initial world setup but not used during factory creation -- it's passed through to the dynamics engine at runtime. The factory only needs `regeneration_mode` and `regen_eligible_ratio` for determining initial eligibility
- Obstacle placement logic is identical to the existing implementation
- Sparse eligibility logic is identical to the existing implementation
- Both internal helpers (`_apply_obstacles`, `_apply_sparse_eligibility`) move to this file

### 6. Package Exports

**File**: `src/axis/world/__init__.py`

```python
"""World Framework -- world model, factory, action engine, dynamics."""

from axis.world.factory import create_world
from axis.world.model import Cell, CellType, RegenerationMode, World

__all__ = [
    "CellType",
    "RegenerationMode",
    "Cell",
    "World",
    "create_world",
]
```

---

## Out of Scope

Do **not** implement any of the following in WP-2.1:

- The action engine / `apply_action()` (WP-2.2)
- World dynamics / `apply_regeneration()` (WP-2.2)
- System A implementation (WP-2.3)
- Any modifications to `axis_system_a` code (left fully functional)
- Snapshot helpers (already defined in `axis.sdk.snapshot` via WP-1.3; the existing `snapshot_world()` accepts `WorldView`, which `World` now satisfies)
- Action handler registration (WP-2.2)

---

## Architectural Constraints

### 1. WorldView Protocol Conformance

The `World` class **must** satisfy `isinstance(world, WorldView)` at runtime. This means:

- `width`, `height`, `agent_position` are properties
- `get_cell(position)` returns `CellView` (not `Cell`)
- `is_within_bounds(position)` returns `bool`
- `is_traversable(position)` returns `bool`

Verify this with a runtime `isinstance` check in tests.

### 2. Internal vs External API

The `World` class has two APIs:

| API | Audience | Methods |
|-----|----------|---------|
| **WorldView** (read-only) | Systems (via SDK) | `width`, `height`, `agent_position`, `get_cell`, `is_within_bounds`, `is_traversable` |
| **Internal** (mutation) | Framework (action engine, dynamics) | `agent_position` setter, `get_internal_cell`, `set_cell`, `is_regen_eligible` |

Systems never import from `axis.world` directly -- they use the `WorldView` protocol from `axis.sdk`.

### 3. Dependency Direction

```
axis.world imports from axis.sdk  (Position, CellView, BaseWorldConfig)
axis.world does NOT import from axis.framework, axis.systems, or axis.visualization
axis.sdk does NOT import from axis.world
```

### 4. CellView Bridge

The bridge from `Cell` to `CellView` is:

```python
CellView(
    cell_type=cell.cell_type.value,  # CellType enum value -> string
    resource_value=cell.resource_value,
)
```

This conversion happens inside `World.get_cell()` and `World.get_cell_view()`.

### 5. snapshot_world() Compatibility

The `snapshot_world()` function defined in WP-1.3 (`axis.sdk.snapshot`) accepts any `WorldView` and calls `get_cell(Position(x, y))` for each coordinate. Since `World` satisfies `WorldView` and `get_cell` returns `CellView`, snapshot creation works automatically -- no additional adapter code is needed.

---

## Expected File Structure

After WP-2.1, these files are **new or modified**:

```
src/axis/world/__init__.py                  # MODIFIED (exports added)
src/axis/world/model.py                     # NEW (CellType, RegenerationMode, Cell, World)
src/axis/world/factory.py                   # NEW (create_world)
tests/v02/world/test_world_model.py         # NEW (verification tests)
tests/v02/test_scaffold.py                  # MODIFIED (axis.world no longer empty)
```

Unchanged:

```
src/axis/sdk/                               # UNCHANGED
src/axis/framework/                         # UNCHANGED
src/axis_system_a/                          # UNCHANGED
```

---

## Testing Requirements

### World model verification tests (`tests/v02/world/test_world_model.py`)

Must include:

1. **CellType enum**:
   - `CellType.EMPTY.value == "empty"`
   - `CellType.RESOURCE.value == "resource"`
   - `CellType.OBSTACLE.value == "obstacle"`

2. **Cell construction and invariants**:
   - `Cell(cell_type=CellType.EMPTY, resource_value=0.0)` constructs
   - `Cell(cell_type=CellType.RESOURCE, resource_value=0.5)` constructs
   - `Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)` constructs with `regen_eligible=False`
   - RESOURCE with `resource_value=0.0` raises
   - EMPTY with `resource_value=0.5` raises
   - OBSTACLE with `resource_value=0.5` raises
   - `is_traversable` returns True for EMPTY/RESOURCE, False for OBSTACLE
   - Frozen: setting `cell_type` raises

3. **World construction**:
   - Constructs with a valid grid and agent position
   - `width`, `height` match grid dimensions
   - `agent_position` returns the initial position
   - Empty grid raises
   - Agent on obstacle raises
   - Agent out of bounds raises

4. **WorldView protocol conformance**:
   - `isinstance(world, WorldView)` is `True`
   - `world.get_cell(pos)` returns `CellView` (not `Cell`)
   - Returned `CellView.cell_type` is a string (e.g., `"resource"`)
   - Returned `CellView.resource_value` matches the internal cell's value

5. **Internal mutation API**:
   - `world.agent_position = new_pos` updates position
   - Setting agent to obstacle position raises
   - `world.set_cell(pos, new_cell)` replaces the cell
   - `world.get_internal_cell(pos)` returns `Cell` (not `CellView`)
   - `world.is_regen_eligible(pos)` returns correct boolean

6. **create_world factory**:
   - `create_world(config, position)` creates an all-empty world
   - Grid dimensions match config
   - Agent starts at specified position
   - With `obstacle_density > 0`: obstacles are placed (agent position excluded)
   - With provided grid: validates dimensions
   - With sparse regeneration mode: eligibility is assigned
   - Deterministic: same seed produces same world

7. **snapshot_world compatibility**:
   - `snapshot_world(world, world.width, world.height)` produces a valid `WorldSnapshot`
   - Snapshot cell types match world cell types

8. **Import verification**:
   - `from axis.world import World, Cell, CellType, create_world` succeeds
   - `from axis.world.model import World, Cell, CellType, RegenerationMode` succeeds
   - `from axis.world.factory import create_world` succeeds

### Existing test suite

All existing tests must still pass. The new world package is independent of `axis_system_a`.

---

## Implementation Style

- Python 3.11+
- Frozen Pydantic `BaseModel` for `Cell`
- Plain class for `World` (sole mutable container)
- `enum.Enum` for `CellType` and `RegenerationMode`
- Clear docstrings
- Type hints throughout
- The extraction should be as mechanical as possible -- same logic, new location, adapted to SDK types

---

## Expected Deliverable

1. `src/axis/world/model.py` with `CellType`, `RegenerationMode`, `Cell`, `World`
2. `src/axis/world/factory.py` with `create_world()`
3. Updated `src/axis/world/__init__.py` with exports
4. Verification tests at `tests/v02/world/test_world_model.py`
5. Updated `tests/v02/test_scaffold.py` for `axis.world` exports
6. Confirmation that all existing tests still pass

---

## Important Final Constraint

This WP is a **structural extraction**, not a behavioral change. The world model logic is proven correct by the existing 1400+ tests against `axis_system_a`. The new `axis.world` code must be functionally identical.

The critical adaptation is making `World.get_cell()` return `CellView` instead of `Cell`, so the `WorldView` protocol is satisfied directly. Framework-internal code that needs the full `Cell` uses `get_internal_cell()` instead.

When the action engine (WP-2.2) and System A (WP-2.3) are implemented, they will import from `axis.world` instead of `axis_system_a`. The legacy `axis_system_a` code remains untouched and functional throughout.
