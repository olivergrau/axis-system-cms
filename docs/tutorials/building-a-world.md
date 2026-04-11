# Tutorial: Building a World from Scratch

**AXIS Experimentation Framework v0.2.0**

> **Prerequisites:** Python 3.11+, the AXIS framework installed (`pip install -e .`),
> familiarity with Pydantic v2 and Python protocols.
>
> **What we build:** A complete 2D grid world with obstacles, resources,
> and regeneration dynamics -- fully integrated with the framework,
> action engine, and visualization.
>
> **Related:** [World Developer Manual](../manuals/world-dev-manual.md) |
> [System Developer Manual](../manuals/system-dev-manual.md) |
> [Building a System Tutorial](building-a-system.md)

---

## What is a World?

A world in AXIS is the environment in which agents operate. It owns:

- A **spatial structure** (grid of cells with types and resource values)
- An **agent position** (the framework tracks where the agent is)
- **Dynamics** (resource regeneration per tick)
- **Mutation surface** (methods that action handlers call to extract
  resources or move the agent)
- **Snapshots** (immutable copies of the world state for replay)

The framework interacts with worlds exclusively through the
`MutableWorldProtocol`. If your class satisfies this protocol,
the framework can use it -- no inheritance needed.

We will build the standard rectangular Grid 2D world step by step,
starting with the simplest possible implementation and adding features
one at a time.

---

## Chapter 1: The Cell Model

Every world is made of cells. Cells have a type and a resource value.
We start here because everything else builds on top of cells.

### 1.1 Cell types

Our grid has three cell types:

| Type | Traversable? | Has resources? |
|------|-------------|----------------|
| `empty` | Yes | No (resource = 0) |
| `resource` | Yes | Yes (resource > 0) |
| `obstacle` | No | No |

```python
# src/axis/world/grid_2d/model.py
from __future__ import annotations

import enum


class CellType(str, enum.Enum):
    """Cell types for the Grid 2D world."""
    EMPTY = "empty"
    RESOURCE = "resource"
    OBSTACLE = "obstacle"
```

We use `str, enum.Enum` so the enum values serialize cleanly to JSON
(`"empty"` rather than `<CellType.EMPTY>`).

### 1.2 The Cell model

Cells are frozen Pydantic models. Once created, they cannot be
modified -- you create a new cell when something changes. This makes
the world state easy to reason about and safe to snapshot.

```python
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Cell(BaseModel):
    """A single cell in the grid."""
    model_config = ConfigDict(frozen=True)

    cell_type: CellType
    resource_value: float = Field(..., ge=0, le=1)
    regen_eligible: bool = True
```

Three fields:

- **`cell_type`** -- which kind of cell this is.
- **`resource_value`** -- how much resource is here (0.0 to 1.0).
- **`regen_eligible`** -- whether regeneration can add resources to
  this cell. This is an internal flag that systems never see.

### 1.3 Enforcing cell invariants

Cell types have constraints: obstacles can't have resources, resource
cells must have resources, and so on. We enforce these with a Pydantic
validator that runs after construction:

```python
class Cell(BaseModel):
    # ... fields as above ...

    @model_validator(mode="after")
    def _validate_cell(self) -> Cell:
        if self.cell_type == CellType.OBSTACLE:
            if self.resource_value != 0:
                raise ValueError("Obstacle cells must have resource_value=0")
            # Obstacles are never regen-eligible
            object.__setattr__(self, "regen_eligible", False)
        elif self.cell_type == CellType.RESOURCE:
            if self.resource_value <= 0:
                raise ValueError("Resource cells must have resource_value > 0")
        elif self.cell_type == CellType.EMPTY:
            if self.resource_value != 0:
                raise ValueError("Empty cells must have resource_value=0")
        return self
```

Note the `object.__setattr__` trick -- since the model is frozen,
ordinary attribute assignment raises an error. This bypass is safe
inside validators because the model isn't yet "sealed".

### 1.4 Test the cell model

```python
# tests/world/test_grid2d_cell.py
import pytest
from axis.world.grid_2d.model import Cell, CellType


def test_empty_cell():
    cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    assert cell.cell_type == CellType.EMPTY
    assert cell.resource_value == 0.0


def test_resource_cell():
    cell = Cell(cell_type=CellType.RESOURCE, resource_value=0.5)
    assert cell.resource_value == 0.5


def test_obstacle_cell_forces_not_eligible():
    cell = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
    assert cell.regen_eligible is False


def test_obstacle_with_resource_raises():
    with pytest.raises(ValueError, match="Obstacle cells"):
        Cell(cell_type=CellType.OBSTACLE, resource_value=0.5)


def test_resource_cell_with_zero_raises():
    with pytest.raises(ValueError, match="Resource cells"):
        Cell(cell_type=CellType.RESOURCE, resource_value=0.0)


def test_cell_is_frozen():
    cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    with pytest.raises(Exception):
        cell.resource_value = 0.5
```

Run:

```bash
python -m pytest tests/world/test_grid2d_cell.py -v
```

---

## Chapter 2: The SDK Contract

Before building the world class, we need to understand what the
framework expects. The contract is defined by two protocols in
`src/axis/sdk/world_types.py`.

### 2.1 What systems see: `CellView`

Systems never see the internal `Cell` model. They see `CellView`:

```python
# Already provided by the SDK -- you don't write this
class CellView(BaseModel):
    model_config = ConfigDict(frozen=True)
    cell_type: str            # "empty", "resource", "obstacle"
    resource_value: float     # [0.0, 1.0]
```

Notice: `cell_type` is a plain `str`, not a `CellType` enum. This
keeps systems decoupled from the internal enum. And `regen_eligible`
is absent -- systems don't need to know about it.

### 2.2 What systems see: `WorldView`

The read-only view that systems receive in `decide()`:

```python
@runtime_checkable
class WorldView(Protocol):
    @property
    def width(self) -> int: ...
    @property
    def height(self) -> int: ...
    @property
    def agent_position(self) -> Position: ...
    def get_cell(self, position: Position) -> CellView: ...
    def is_within_bounds(self, position: Position) -> bool: ...
    def is_traversable(self, position: Position) -> bool: ...
```

### 2.3 What the framework needs: `MutableWorldProtocol`

The full mutable contract that extends `WorldView`:

```python
@runtime_checkable
class MutableWorldProtocol(WorldView, Protocol):
    @property
    def agent_position(self) -> Position: ...
    @agent_position.setter
    def agent_position(self, position: Position) -> None: ...
    def get_internal_cell(self, position: Position) -> Any: ...
    def set_cell(self, position: Position, cell: Any) -> None: ...
    def tick(self) -> None: ...
    def extract_resource(self, position: Position, max_amount: float) -> float: ...
    def snapshot(self) -> WorldSnapshot: ...
    def world_metadata(self) -> dict[str, Any]: ...
```

Method-by-method:

| Method | Purpose |
|--------|---------|
| `agent_position` (setter) | Move the agent to a new cell |
| `get_internal_cell(pos)` | Return the raw internal cell (with `regen_eligible`) |
| `set_cell(pos, cell)` | Replace a cell in the grid |
| `tick()` | Advance world dynamics (regeneration) |
| `extract_resource(pos, max)` | Remove up to `max` resource from a cell; return amount extracted |
| `snapshot()` | Create an immutable `WorldSnapshot` of the current state |
| `world_metadata()` | Return a dict of per-step metadata (empty for simple worlds) |

Our job is to build a `World` class that satisfies
`MutableWorldProtocol`. The framework will validate this at runtime
with `isinstance(world, MutableWorldProtocol)`.

---

## Chapter 3: The World Class -- Skeleton

Let's build the world class incrementally. We start with the minimum:
a grid, an agent position, and the read-only methods.

### 3.1 Constructor and storage

```python
# src/axis/world/grid_2d/model.py  (continuing the file)
from axis.sdk.position import Position
from axis.sdk.world_types import CellView
from axis.sdk.snapshot import WorldSnapshot


class World:
    """A 2D rectangular grid world."""

    def __init__(
        self,
        grid: list[list[Cell]],
        agent_position: Position,
        *,
        regen_rate: float = 0.0,
    ) -> None:
        if not grid or not grid[0]:
            raise ValueError("Grid must be non-empty")

        self._height = len(grid)
        self._width = len(grid[0])

        for row in grid:
            if len(row) != self._width:
                raise ValueError("All grid rows must have the same width")

        if not self.is_within_bounds(agent_position):
            raise ValueError(f"Agent position {agent_position} is out of bounds")

        cell = grid[agent_position.y][agent_position.x]
        if cell.cell_type == CellType.OBSTACLE:
            raise ValueError("Agent cannot start on an obstacle")

        self._grid = grid
        self._agent_position = agent_position
        self._regen_rate = regen_rate
```

Key decisions:

- **Grid is stored as `list[list[Cell]]`** -- mutable container of
  immutable cells. When a cell changes, we replace the cell object.
- **Grid is `[row][col]`**, i.e., `grid[y][x]`. We validate that all
  rows have equal width.
- **Agent cannot start on an obstacle.** The framework always places
  agents on traversable cells.
- **`regen_rate`** is stored for `tick()` to use later.

### 3.2 Read-only properties

```python
    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def agent_position(self) -> Position:
        return self._agent_position
```

### 3.3 Bounds and traversability

```python
    def is_within_bounds(self, position: Position) -> bool:
        return 0 <= position.x < self._width and 0 <= position.y < self._height

    def is_traversable(self, position: Position) -> bool:
        if not self.is_within_bounds(position):
            return False
        return self._grid[position.y][position.x].cell_type != CellType.OBSTACLE
```

`is_traversable` returns `False` for out-of-bounds positions. This
is deliberate: it makes movement checks simpler because we don't
need a separate bounds check before checking traversability.

### 3.4 The cell bridge: internal `Cell` to public `CellView`

```python
    def get_cell(self, position: Position) -> CellView:
        """Return the system-facing view of a cell."""
        cell = self._grid[position.y][position.x]
        return CellView(
            cell_type=cell.cell_type.value,  # enum → string
            resource_value=cell.resource_value,
        )
```

This is the bridge between the internal model and the SDK contract.
Systems see `CellView` with `cell_type` as a string. The internal
`regen_eligible` flag is hidden.

### 3.5 Test the skeleton

```python
# tests/world/test_grid2d_world_basics.py
import pytest
from axis.sdk.position import Position
from axis.world.grid_2d.model import Cell, CellType, World


def _simple_grid() -> list[list[Cell]]:
    """3x3 grid: all empty except center is resource."""
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    resource = Cell(cell_type=CellType.RESOURCE, resource_value=0.7)
    return [
        [empty, empty, empty],
        [empty, resource, empty],
        [empty, empty, empty],
    ]


def test_world_dimensions():
    world = World(_simple_grid(), Position(x=0, y=0))
    assert world.width == 3
    assert world.height == 3


def test_agent_position():
    world = World(_simple_grid(), Position(x=1, y=1))
    assert world.agent_position == Position(x=1, y=1)


def test_is_within_bounds():
    world = World(_simple_grid(), Position(x=0, y=0))
    assert world.is_within_bounds(Position(x=0, y=0))
    assert world.is_within_bounds(Position(x=2, y=2))
    assert not world.is_within_bounds(Position(x=3, y=0))
    assert not world.is_within_bounds(Position(x=-1, y=0))


def test_get_cell_returns_cell_view():
    world = World(_simple_grid(), Position(x=0, y=0))
    cell = world.get_cell(Position(x=1, y=1))
    assert cell.cell_type == "resource"  # string, not enum
    assert cell.resource_value == 0.7


def test_agent_on_obstacle_raises():
    obstacle = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
    grid = [[obstacle]]
    with pytest.raises(ValueError, match="obstacle"):
        World(grid, Position(x=0, y=0))
```

---

## Chapter 4: Mutation Methods

The framework needs to mutate the world: moving the agent, extracting
resources, and replacing cells. Let's add these methods.

### 4.1 Moving the agent

```python
    @agent_position.setter
    def agent_position(self, position: Position) -> None:
        if not self.is_within_bounds(position):
            raise ValueError(f"Position {position} is out of bounds")
        if not self.is_traversable(position):
            raise ValueError(f"Position {position} is not traversable")
        self._agent_position = position
```

The setter validates both bounds and traversability. Movement handlers
in the `ActionRegistry` check these before calling the setter, but the
setter enforces them as a safety net.

### 4.2 Internal cell access

```python
    def get_internal_cell(self, position: Position) -> Cell:
        """Return the raw internal Cell (includes regen_eligible)."""
        return self._grid[position.y][position.x]

    def set_cell(self, position: Position, cell: Cell) -> None:
        """Replace a cell in the grid."""
        self._grid[position.y][position.x] = cell
```

These are low-level methods for action handlers and dynamics that need
full access. Most code should use `extract_resource()` instead.

### 4.3 Extracting resources

```python
    def extract_resource(self, position: Position, max_amount: float) -> float:
        """Extract up to max_amount from a cell. Returns actual amount."""
        cell = self._grid[position.y][position.x]
        if cell.resource_value <= 0:
            return 0.0

        extracted = min(cell.resource_value, max_amount)
        remaining = cell.resource_value - extracted

        if remaining <= 0:
            new_cell = Cell(
                cell_type=CellType.EMPTY,
                resource_value=0.0,
                regen_eligible=cell.regen_eligible,
            )
        else:
            new_cell = Cell(
                cell_type=CellType.RESOURCE,
                resource_value=remaining,
                regen_eligible=cell.regen_eligible,
            )

        self._grid[position.y][position.x] = new_cell
        return extracted
```

This is the preferred API for consuming resources. It handles the
cell type transition (RESOURCE -> EMPTY when fully consumed) and
preserves the `regen_eligible` flag.

### 4.4 Test mutations

```python
# tests/world/test_grid2d_mutations.py
import pytest
from axis.sdk.position import Position
from axis.world.grid_2d.model import Cell, CellType, World


def _grid_with_resource():
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    resource = Cell(cell_type=CellType.RESOURCE, resource_value=0.8)
    return [
        [empty, resource],
        [empty, empty],
    ]


def test_move_agent():
    world = World(_grid_with_resource(), Position(x=0, y=0))
    world.agent_position = Position(x=1, y=0)
    assert world.agent_position == Position(x=1, y=0)


def test_move_to_obstacle_raises():
    obstacle = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    grid = [[empty, obstacle]]
    world = World(grid, Position(x=0, y=0))
    with pytest.raises(ValueError, match="not traversable"):
        world.agent_position = Position(x=1, y=0)


def test_extract_resource_partial():
    world = World(_grid_with_resource(), Position(x=0, y=0))
    extracted = world.extract_resource(Position(x=1, y=0), max_amount=0.3)
    assert extracted == pytest.approx(0.3)
    cell = world.get_cell(Position(x=1, y=0))
    assert cell.cell_type == "resource"
    assert cell.resource_value == pytest.approx(0.5)


def test_extract_resource_full():
    world = World(_grid_with_resource(), Position(x=0, y=0))
    extracted = world.extract_resource(Position(x=1, y=0), max_amount=1.0)
    assert extracted == pytest.approx(0.8)
    cell = world.get_cell(Position(x=1, y=0))
    assert cell.cell_type == "empty"
    assert cell.resource_value == 0.0


def test_extract_from_empty_returns_zero():
    world = World(_grid_with_resource(), Position(x=0, y=0))
    extracted = world.extract_resource(Position(x=0, y=0), max_amount=0.5)
    assert extracted == 0.0
```

---

## Chapter 5: Snapshots

The framework captures three snapshots per step for replay. A snapshot
is a complete, immutable copy of the grid state.

### 5.1 The `WorldSnapshot` model

The SDK provides this (you don't need to write it):

```python
class WorldSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    grid: tuple[tuple[CellView, ...], ...]  # grid[row][col]
    agent_position: Position
    width: int
    height: int
```

### 5.2 Implementing `snapshot()`

```python
    def snapshot(self) -> WorldSnapshot:
        """Create an immutable snapshot of the current world state."""
        grid = tuple(
            tuple(self.get_cell(Position(x=x, y=y)) for x in range(self._width))
            for y in range(self._height)
        )
        return WorldSnapshot(
            grid=grid,
            agent_position=self._agent_position,
            width=self._width,
            height=self._height,
        )
```

The snapshot converts every internal `Cell` to a `CellView` (via
`get_cell()`) and wraps everything in nested tuples for immutability.
The framework calls this three times per step:

1. **BEFORE** -- before the system decides
2. **AFTER_REGEN** -- after `tick()` runs regeneration
3. **AFTER_ACTION** -- after the action is applied

### 5.3 World metadata

```python
    def world_metadata(self) -> dict[str, Any]:
        """Return per-step metadata. Grid 2D has none."""
        return {}
```

Some world types (e.g., signal landscape with drifting hotspots) use
this to pass world-specific data to visualization. For a basic grid,
return an empty dict.

### 5.4 Test snapshots

```python
# tests/world/test_grid2d_snapshot.py
from axis.sdk.position import Position
from axis.world.grid_2d.model import Cell, CellType, World


def test_snapshot_is_immutable():
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    world = World([[empty, empty], [empty, empty]], Position(x=0, y=0))
    snap = world.snapshot()
    assert snap.width == 2
    assert snap.height == 2
    assert snap.agent_position == Position(x=0, y=0)
    assert snap.grid[0][0].cell_type == "empty"


def test_snapshot_captures_current_state():
    resource = Cell(cell_type=CellType.RESOURCE, resource_value=0.6)
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    world = World([[resource, empty]], Position(x=0, y=0))

    snap1 = world.snapshot()
    assert snap1.grid[0][0].resource_value == 0.6

    world.extract_resource(Position(x=0, y=0), max_amount=0.6)

    snap2 = world.snapshot()
    assert snap2.grid[0][0].resource_value == 0.0

    # Original snapshot unchanged
    assert snap1.grid[0][0].resource_value == 0.6
```

---

## Chapter 6: Regeneration Dynamics

Resources regrow over time. The framework calls `world.tick()` once
per step, between the system's `decide()` and the action application.

### 6.1 Regeneration modes

We support two modes:

| Mode | Behavior |
|------|----------|
| `all_traversable` | Every non-obstacle cell can regenerate |
| `sparse_fixed_ratio` | Only a fixed fraction of cells are eligible |

```python
# In model.py
class RegenerationMode(str, enum.Enum):
    ALL_TRAVERSABLE = "all_traversable"
    SPARSE_FIXED_RATIO = "sparse_fixed_ratio"
```

The mode is a world creation concern, not a per-tick concern. It
determines which cells have `regen_eligible=True` when the grid is
built. The `tick()` method just checks the flag.

### 6.2 The regeneration function

We put dynamics in a separate file to keep the model clean:

```python
# src/axis/world/grid_2d/dynamics.py
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from axis.sdk.world_types import MutableWorldProtocol

from axis.sdk.position import Position
from axis.world.grid_2d.model import Cell, CellType


def apply_regeneration(
    world: MutableWorldProtocol,
    *,
    regen_rate: float,
) -> int:
    """Add regen_rate to every eligible cell. Returns count of cells updated."""
    if regen_rate == 0.0:
        return 0

    updated = 0
    for y in range(world.height):
        for x in range(world.width):
            pos = Position(x=x, y=y)
            cell = world.get_internal_cell(pos)

            if cell.cell_type == CellType.OBSTACLE:
                continue
            if not cell.regen_eligible:
                continue

            new_value = min(1.0, cell.resource_value + regen_rate)
            if new_value == cell.resource_value:
                continue  # already at max

            new_cell = Cell(
                cell_type=CellType.RESOURCE,
                resource_value=new_value,
                regen_eligible=True,
            )
            world.set_cell(pos, new_cell)
            updated += 1

    return updated
```

Design notes:

- **Typed against `MutableWorldProtocol`**, not the concrete `World`
  class. This means the same function could work with a toroidal world
  or any other world that satisfies the protocol.
- **Short-circuits** on `regen_rate == 0.0`.
- **Skips** obstacles and ineligible cells.
- **Caps** at 1.0 (maximum resource value).
- **Returns** the number of cells updated (useful for debugging and
  testing, though the framework doesn't use the return value).

### 6.3 Wiring `tick()` to dynamics

```python
# In the World class
    def tick(self) -> None:
        """Advance world dynamics by one step."""
        from axis.world.grid_2d.dynamics import apply_regeneration
        apply_regeneration(self, regen_rate=self._regen_rate)
```

The lazy import avoids circular dependencies between the model and
dynamics modules.

### 6.4 Test regeneration

```python
# tests/world/test_grid2d_regen.py
from axis.sdk.position import Position
from axis.world.grid_2d.model import Cell, CellType, World


def test_tick_adds_resource():
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    world = World([[empty]], Position(x=0, y=0), regen_rate=0.1)

    world.tick()
    cell = world.get_cell(Position(x=0, y=0))
    assert cell.cell_type == "resource"
    assert cell.resource_value == pytest.approx(0.1)


def test_tick_caps_at_one():
    resource = Cell(cell_type=CellType.RESOURCE, resource_value=0.95)
    world = World([[resource]], Position(x=0, y=0), regen_rate=0.1)

    world.tick()
    cell = world.get_cell(Position(x=0, y=0))
    assert cell.resource_value == pytest.approx(1.0)


def test_tick_skips_obstacles():
    obstacle = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    world = World([[obstacle, empty]], Position(x=1, y=0), regen_rate=0.1)

    world.tick()
    assert world.get_cell(Position(x=0, y=0)).resource_value == 0.0  # obstacle unchanged
    assert world.get_cell(Position(x=1, y=0)).resource_value == pytest.approx(0.1)


def test_tick_skips_ineligible():
    cell = Cell(cell_type=CellType.EMPTY, resource_value=0.0, regen_eligible=False)
    world = World([[cell]], Position(x=0, y=0), regen_rate=0.1)

    world.tick()
    assert world.get_cell(Position(x=0, y=0)).resource_value == 0.0


def test_zero_regen_rate_is_noop():
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    world = World([[empty]], Position(x=0, y=0), regen_rate=0.0)

    world.tick()
    assert world.get_cell(Position(x=0, y=0)).resource_value == 0.0
```

---

## Chapter 7: World Configuration

Worlds are configured through experiment YAML files. The framework
owns the outer config; each world type owns its own interpretation.

### 7.1 The config model

```python
# src/axis/world/grid_2d/config.py
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Grid2DWorldConfig(BaseModel):
    """Configuration specific to the Grid 2D world type."""
    model_config = ConfigDict(frozen=True)

    grid_width: int = Field(..., gt=0)
    grid_height: int = Field(..., gt=0)
    obstacle_density: float = Field(default=0.0, ge=0.0, lt=1.0)
    resource_regen_rate: float = Field(default=0.0, ge=0, le=1)
    regeneration_mode: str = "all_traversable"
    regen_eligible_ratio: float | None = Field(default=None, gt=0, le=1)
```

### 7.2 How config flows from YAML to the world

The experiment config YAML has a `world:` section:

```yaml
world:
  world_type: grid_2d
  grid_width: 10
  grid_height: 10
  obstacle_density: 0.1
  resource_regen_rate: 0.05
```

The framework parses this into `BaseWorldConfig`. Because
`BaseWorldConfig` uses `extra="allow"`, the grid-specific fields
(`grid_width`, etc.) are stored as extras in
`config.__pydantic_extra__`. The factory extracts them:

```python
def _parse_grid_config(config: BaseWorldConfig) -> Grid2DWorldConfig:
    """Extract Grid 2D-specific config from the framework config."""
    extra = config.__pydantic_extra__ or {}
    return Grid2DWorldConfig(**extra)
```

This way, the framework stays generic -- it just passes the config
through. The world factory is responsible for parsing and validation.

---

## Chapter 8: The World Factory

The factory is the entry point that creates a fully initialized world
from a configuration.

### 8.1 The factory function

```python
# src/axis/world/grid_2d/factory.py
from __future__ import annotations

import numpy as np

from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.world.grid_2d.config import Grid2DWorldConfig
from axis.world.grid_2d.model import Cell, CellType, RegenerationMode, World


def create_world(
    config: BaseWorldConfig,
    agent_position: Position,
    grid: list[list[Cell]] | None = None,
    *,
    seed: int | None = None,
) -> World:
    """Create a Grid 2D world from configuration."""
    gc = _parse_grid_config(config)

    if grid is None:
        # Build a default grid: all empty cells
        grid = [
            [Cell(cell_type=CellType.EMPTY, resource_value=0.0)
             for _ in range(gc.grid_width)]
            for _ in range(gc.grid_height)
        ]

    # Place obstacles
    if gc.obstacle_density > 0:
        _apply_obstacles(grid, gc.obstacle_density, agent_position, seed=seed)

    # Mark sparse eligibility
    if gc.regeneration_mode == RegenerationMode.SPARSE_FIXED_RATIO.value:
        _apply_sparse_eligibility(grid, gc.regen_eligible_ratio, seed=seed)

    return World(
        grid=grid,
        agent_position=agent_position,
        regen_rate=gc.resource_regen_rate,
    )
```

### 8.2 Obstacle placement

```python
def _apply_obstacles(
    grid: list[list[Cell]],
    density: float,
    agent_position: Position,
    *,
    seed: int | None = None,
) -> None:
    """Place obstacle cells randomly, avoiding the agent start position."""
    rng = np.random.default_rng(seed)
    height = len(grid)
    width = len(grid[0])

    candidates = [
        (x, y)
        for y in range(height)
        for x in range(width)
        if (x, y) != (agent_position.x, agent_position.y)
        and grid[y][x].cell_type != CellType.OBSTACLE
    ]

    num_obstacles = round(density * len(candidates))
    chosen = rng.choice(len(candidates), size=num_obstacles, replace=False)

    for idx in chosen:
        x, y = candidates[idx]
        grid[y][x] = Cell(cell_type=CellType.OBSTACLE, resource_value=0.0)
```

Critical detail: the agent's starting position is **excluded** from
candidates. The agent must always start on a traversable cell.

### 8.3 Sparse regeneration eligibility

```python
def _apply_sparse_eligibility(
    grid: list[list[Cell]],
    ratio: float | None,
    *,
    seed: int | None = None,
) -> None:
    """Mark only a subset of traversable cells as regen-eligible."""
    if ratio is None:
        return

    rng = np.random.default_rng(seed)
    height = len(grid)
    width = len(grid[0])

    traversable = [
        (x, y)
        for y in range(height)
        for x in range(width)
        if grid[y][x].cell_type != CellType.OBSTACLE
    ]

    num_eligible = round(ratio * len(traversable))
    chosen = set(rng.choice(len(traversable), size=num_eligible, replace=False))

    for i, (x, y) in enumerate(traversable):
        cell = grid[y][x]
        eligible = i in chosen
        grid[y][x] = cell.model_copy(update={"regen_eligible": eligible})
```

### 8.4 Test the factory

```python
# tests/world/test_grid2d_factory.py
from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.world.grid_2d.factory import create_world


def test_create_basic_world():
    config = BaseWorldConfig(grid_width=5, grid_height=5)
    world = create_world(config, Position(x=2, y=2), seed=42)
    assert world.width == 5
    assert world.height == 5
    assert world.agent_position == Position(x=2, y=2)


def test_create_with_obstacles():
    config = BaseWorldConfig(grid_width=10, grid_height=10, obstacle_density=0.2)
    world = create_world(config, Position(x=0, y=0), seed=42)

    obstacle_count = sum(
        1
        for y in range(world.height)
        for x in range(world.width)
        if world.get_cell(Position(x=x, y=y)).cell_type == "obstacle"
    )
    assert obstacle_count > 0
    # Agent start position is never an obstacle
    assert world.is_traversable(Position(x=0, y=0))


def test_create_is_deterministic():
    config = BaseWorldConfig(grid_width=10, grid_height=10, obstacle_density=0.2)
    world1 = create_world(config, Position(x=0, y=0), seed=42)
    world2 = create_world(config, Position(x=0, y=0), seed=42)

    snap1 = world1.snapshot()
    snap2 = world2.snapshot()
    assert snap1 == snap2
```

---

## Chapter 9: Registering with the Framework

The framework discovers worlds through the plugin system. We need a
`register()` function and an entry in `axis-plugins.yaml` or
`pyproject.toml`.

### 9.1 The `register()` function

```python
# src/axis/world/grid_2d/__init__.py
"""Grid 2D -- standard rectangular grid world."""

from axis.world.grid_2d.config import Grid2DWorldConfig
from axis.world.grid_2d.dynamics import apply_regeneration
from axis.world.grid_2d.factory import create_world
from axis.world.grid_2d.model import Cell, CellType, RegenerationMode, World

__all__ = [
    "Cell",
    "CellType",
    "Grid2DWorldConfig",
    "RegenerationMode",
    "World",
    "apply_regeneration",
    "create_world",
]


def register() -> None:
    """Register grid_2d: world factory + visualization adapter."""
    from axis.world.registry import register_world, registered_world_types

    if "grid_2d" not in registered_world_types():

        def _factory(config, agent_position, seed):
            return create_world(config, agent_position, seed=seed)

        register_world("grid_2d", _factory)

    from axis.visualization.registry import registered_world_visualizations

    if "grid_2d" not in registered_world_visualizations():
        try:
            import axis.world.grid_2d.visualization  # noqa: F401
        except ImportError:
            pass
```

Two registrations:

1. **World factory** -- wraps `create_world()` and registers it as
   `"grid_2d"` in the world registry. The framework calls it via
   `create_world_from_config()` when `world_type: "grid_2d"`.

2. **Visualization adapter** -- imports the visualization module (which
   has a module-level registration side effect). Guarded by
   `try/except ImportError` so the world works without PySide6.

Both are **idempotent** -- the `not in` checks prevent double
registration when both entry points and `axis-plugins.yaml` trigger
discovery.

### 9.2 Plugin declaration

For local development, add to `axis-plugins.yaml`:

```yaml
plugins:
  - axis.world.grid_2d
```

For installable packages, add to `pyproject.toml`:

```toml
[project.entry-points."axis.plugins"]
grid_2d = "axis.world.grid_2d"
```

### 9.3 Test registration

```python
# tests/world/test_grid2d_registration.py
from axis.world.registry import registered_world_types


def test_grid_2d_is_registered():
    assert "grid_2d" in registered_world_types()
```

---

## Chapter 10: The Visualization Adapter

The AXIS visualizer needs to know how to render your world's geometry
and colors. Each world type provides a visualization adapter.

### 10.1 The `WorldVisualizationAdapter` protocol

The adapter must satisfy this protocol (from
`src/axis/visualization/protocols.py`):

```python
class WorldVisualizationAdapter(Protocol):
    def cell_shape(self) -> CellShape: ...
    def cell_layout(self, grid_width, grid_height,
                    canvas_width, canvas_height) -> CellLayout: ...
    def cell_color_config(self) -> CellColorConfig: ...
    def topology_indicators(self, ...) -> list[TopologyIndicator]: ...
    def pixel_to_grid(self, pixel_x, pixel_y, cell_layout) -> Position | None: ...
    def agent_marker_center(self, grid_position, cell_layout) -> tuple[float, float]: ...
    def world_metadata_sections(self, world_data) -> list[MetadataSection]: ...
    def format_world_info(self, world_data) -> str | None: ...
```

### 10.2 Using the default adapter

For rectangular grids, the framework provides
`DefaultWorldVisualizationAdapter` in
`src/axis/visualization/adapters/default_world.py`. It computes
rectangular cell geometry, color gradients, and pixel-to-grid mapping.

For most grid worlds, you simply subclass it (or even use it directly):

```python
# src/axis/world/grid_2d/visualization.py
from __future__ import annotations

from typing import Any

from axis.visualization.adapters.default_world import (
    DefaultWorldVisualizationAdapter,
)
from axis.visualization.registry import register_world_visualization


class Grid2DWorldVisualizationAdapter(DefaultWorldVisualizationAdapter):
    """Visualization adapter for Grid 2D worlds.

    Inherits all behavior from the default rectangular adapter.
    Override methods here if you need custom colors or geometry.
    """
    pass


def _grid_2d_vis_factory(
    world_config: dict[str, Any],
) -> Grid2DWorldVisualizationAdapter:
    return Grid2DWorldVisualizationAdapter()


# Module-level registration: importing this file registers the adapter
register_world_visualization("grid_2d", _grid_2d_vis_factory)
```

The module-level call at the bottom means that importing this file
has the side effect of registering the adapter. The `register()`
function in `__init__.py` imports this module to trigger registration.

### 10.3 Customizing colors

If your world needs different colors, override `cell_color_config()`:

```python
class MyWorldVisualizationAdapter(DefaultWorldVisualizationAdapter):
    def cell_color_config(self) -> CellColorConfig:
        return CellColorConfig(
            obstacle_color=(40, 40, 40),         # dark gray
            empty_color=(200, 200, 220),          # light blue-gray
            resource_color_min=(220, 240, 220),   # pale green
            resource_color_max=(0, 100, 0),       # dark green
            agent_color=(255, 100, 50),           # orange
            selection_border_color=(255, 255, 0), # yellow
            grid_line_color=(180, 180, 180),      # light gray
        )
```

### 10.4 Customizing topology

Non-rectangular worlds (like toroidal grids) can override
`topology_indicators()` to show visual cues about wrapping or
connectivity.

---

## Chapter 11: Running Your World

Now everything is wired up. Your world can be used with any registered
system.

### 11.1 From an experiment config

```yaml
# experiments/configs/my-world-demo.yaml
system_type: "system_a"
experiment_type: "single_run"

general:
  seed: 42

execution:
  max_steps: 200

world:
  world_type: "grid_2d"
  grid_width: 10
  grid_height: 10
  obstacle_density: 0.1
  resource_regen_rate: 0.05
  regeneration_mode: "sparse_fixed_ratio"
  regen_eligible_ratio: 0.17

system:
  agent:
    initial_energy: 50.0
    max_energy: 100.0
    buffer_capacity: 5
  policy:
    selection_mode: "sample"
    temperature: 1.0
    stay_suppression: 0.1
    consume_weight: 3.0
  transition:
    move_cost: 1.0
    consume_cost: 0.5
    stay_cost: 0.5
    max_consume: 1.0
    energy_gain_factor: 20.0

num_episodes_per_run: 5
```

Run:

```bash
axis experiments run experiments/configs/my-world-demo.yaml
```

### 11.2 From Python code

```python
from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.world.grid_2d.factory import create_world

config = BaseWorldConfig(
    world_type="grid_2d",
    grid_width=5,
    grid_height=5,
    obstacle_density=0.1,
    resource_regen_rate=0.05,
)
world = create_world(config, Position(x=2, y=2), seed=42)

# Inspect the world
print(f"Grid: {world.width}x{world.height}")
print(f"Agent at: {world.agent_position}")
snap = world.snapshot()
for y in range(world.height):
    row = "".join(
        "A" if Position(x=x, y=y) == world.agent_position
        else "#" if snap.grid[y][x].cell_type == "obstacle"
        else "." if snap.grid[y][x].cell_type == "empty"
        else "R"
        for x in range(world.width)
    )
    print(row)
```

---

## Chapter 12: Complete File Inventory

Here is the complete set of files for a world implementation:

```
src/axis/world/grid_2d/
    __init__.py          # Package init + register() function
    config.py            # Grid2DWorldConfig (Pydantic model)
    model.py             # CellType, RegenerationMode, Cell, World
    factory.py           # create_world() + obstacle/eligibility helpers
    dynamics.py          # apply_regeneration() -- per-tick resource growth
    visualization.py     # Grid2DWorldVisualizationAdapter + registration

tests/world/
    test_grid2d_cell.py        # Cell model invariants
    test_grid2d_world_basics.py # World construction, bounds, cell access
    test_grid2d_mutations.py    # Movement, resource extraction
    test_grid2d_snapshot.py     # Snapshot immutability
    test_grid2d_regen.py        # Regeneration dynamics
    test_grid2d_factory.py      # Factory with obstacles, determinism
    test_grid2d_registration.py # Plugin registration
```

---

## Summary: Building a World, Step by Step

1. **Define cell types** -- an enum of possible cell states.
2. **Build the cell model** -- a frozen Pydantic model with validators
   enforcing invariants.
3. **Build the `World` class** -- a mutable grid container that
   satisfies `MutableWorldProtocol`.
4. **Implement read-only methods** -- `get_cell()`, `is_within_bounds()`,
   `is_traversable()` (what systems see).
5. **Implement mutation methods** -- `agent_position` setter,
   `extract_resource()`, `set_cell()` (what action handlers use).
6. **Implement snapshots** -- `snapshot()` creates an immutable copy
   for replay.
7. **Implement dynamics** -- `tick()` delegates to a regeneration
   function.
8. **Write a config model** -- world-specific parameters with Pydantic
   validation.
9. **Write a factory** -- creates the world from config, places
   obstacles, sets up regeneration eligibility.
10. **Register** -- add `register()` to `__init__.py`, declare entry
    point in `pyproject.toml`.
11. **Add a visualization adapter** -- subclass
    `DefaultWorldVisualizationAdapter` or implement the protocol.
12. **Test each layer** -- cell invariants, world methods, dynamics,
    factory, registration.
