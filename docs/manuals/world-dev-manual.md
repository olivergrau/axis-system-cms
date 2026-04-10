# AXIS World Developer Manual (v0.2.0)

> **Related manuals:**
> [CLI User Manual](cli-manual.md) |
> [Configuration Reference](config-manual.md) |
> [System Developer Manual](system-dev-manual.md)

## Overview

The AXIS framework supports pluggable world implementations through a
**world registry** and the **`MutableWorldProtocol`** SDK contract.
The built-in world type is `"grid_2d"` -- a 2D rectangular grid with
cell-based resources and obstacles. You can create entirely new world
types by implementing the protocol and registering a factory function.

This manual walks through the architecture, the contracts your world
must satisfy, and a complete worked example of a custom world.

---

## 1. Architecture

### 1.1 How worlds fit into the framework

```
config YAML: world: { world_type: "hex_grid", grid_width: 8, ... }
     │
     ▼
registry.get_world_factory("hex_grid")
     │
     ▼
your_factory(config, agent_position, seed)
     │
     ▼
YourWorld(...)  ← must satisfy MutableWorldProtocol
     │
     ▼
Framework episode loop:
  1. world_before = world.snapshot()  ← captures state before step
  2. system.decide(world, ...)       ← system sees WorldView (read-only)
  3. world.tick()                     ← world advances its own dynamics
  4. registry.apply(world, action)   ← moves agent, mutates cells
  5. world_after = world.snapshot()   ← captures post-action state
  6. system.transition(...)          ← receives ActionOutcome
```

A world is created once per episode. The framework interacts with it
exclusively through the `MutableWorldProtocol` interface. Systems only
see the read-only `WorldView` subset.

### 1.2 Key components

| Component | Location | Purpose |
|-----------|----------|---------|
| `WorldView` | `axis.sdk.world_types` | Read-only protocol exposed to systems |
| `MutableWorldProtocol` | `axis.sdk.world_types` | Full mutable protocol for the framework |
| `BaseWorldConfig` | `axis.sdk.world_types` | Configuration model (grid size, regen params, `world_type`) |
| `register_world()` | `axis.world.registry` | Register a factory for a world type |
| `create_world_from_config()` | `axis.world.registry` | Create a world by looking up its type in the registry |
| `apply_regeneration()` | `axis.world.grid_2d.dynamics` | Grid2D regeneration engine (works with any `MutableWorldProtocol` using compatible cells) |

### 1.3 Relationship to systems

Systems do **not** own world dynamics. Regeneration parameters
(`resource_regen_rate`, `regeneration_mode`, `regen_eligible_ratio`)
are configured in the `world:` section of the experiment config and
are properties of the world, not the system. A system selects which
world type to use via the config, and interacts with the world through
the read-only `WorldView` protocol.

---

## 2. The `MutableWorldProtocol` contract

Your custom world class must satisfy the `MutableWorldProtocol`, which
extends `WorldView`. Here is the full contract:

### 2.1 Read-only API (from `WorldView`)

Systems call these methods during `decide()`. They must never mutate
the world.

| Method / Property | Return type | Description |
|-------------------|-------------|-------------|
| `width` | `int` | Grid width |
| `height` | `int` | Grid height |
| `agent_position` | `Position` | Current agent position |
| `get_cell(position)` | `CellView` | Read-only cell view. Raises `ValueError` if out of bounds. |
| `is_within_bounds(position)` | `bool` | Bounds check |
| `is_traversable(position)` | `bool` | `True` if position is in bounds and not an obstacle. Returns `False` for out-of-bounds (safe to call). |

### 2.2 Mutation API (framework-only)

The framework and action handlers call these. Systems never see them.

| Method / Property | Return type | Description |
|-------------------|-------------|-------------|
| `agent_position` (setter) | -- | Set the agent's position. Should validate bounds. |
| `get_internal_cell(position)` | `Any` | Return the internal cell representation (not `CellView`). |
| `set_cell(position, cell)` | `None` | Replace a cell at a position. |
| `tick()` | `None` | Advance world dynamics by one step (e.g. regeneration). |
| `extract_resource(position, max_amount)` | `float` | Extract up to `max_amount` resource from the cell. Returns amount extracted. |
| `snapshot()` | `WorldSnapshot` | Create an immutable snapshot of the current world state. |

### 2.3 Notes on `get_internal_cell` and `set_cell`

These methods use `Any` typing intentionally. The framework's
regeneration engine (`apply_regeneration`) expects cells compatible
with the built-in `Cell` model (`cell_type`, `resource_value`,
`regen_eligible`). If your world uses a different internal cell type,
you may need to provide a custom regeneration function or ensure
your cells expose the same attributes.

---

## 3. The `BaseWorldConfig`

All world types receive the same `BaseWorldConfig` at construction time:

```python
class BaseWorldConfig(BaseModel):
    """Framework-level world configuration.

    Only ``world_type`` is framework-owned. All other fields are
    world-type-specific and passed through to the world factory via
    ``extra="allow"``.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    world_type: str = "grid_2d"
```

Your factory receives this config with any extra fields provided in the
YAML `world:` section. Because `BaseWorldConfig` uses `extra="allow"`,
arbitrary keys are accepted and passed through.

- For the built-in `grid_2d` world, extras include `grid_width`,
  `grid_height`, `obstacle_density`, `resource_regen_rate`,
  `regeneration_mode`, `regen_eligible_ratio`.
- Your custom world type can accept different extras (e.g. `hex_radius`,
  `hex_layers`).
- The factory is responsible for parsing and validating these extras
  (e.g. via `getattr(config, 'hex_radius')` or by constructing a
  local Pydantic model from `config.model_extra`).

---

## 4. Registering a custom world

### 4.1 The factory function

A world factory has this signature:

```python
from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig, MutableWorldProtocol

def my_world_factory(
    config: BaseWorldConfig,
    agent_position: Position,
    seed: int | None,
) -> MutableWorldProtocol:
    ...
```

The factory is responsible for:
1. Building the internal grid/state from the config
2. Placing obstacles (using `config.obstacle_density` and `seed`)
3. Setting up regeneration eligibility (using `config.regeneration_mode`)
4. Returning a world instance that satisfies `MutableWorldProtocol`

### 4.2 Registration

Register your world type by calling `register_world()`:

```python
from axis.world import register_world

register_world("my_world_type", my_world_factory)
```

After registration, any experiment config with `world_type: "my_world_type"`
will use your factory.

**Registration timing:**

- **Built-in worlds**: Register at module import time (the built-in
  `"grid_2d"` does this in `axis/world/registry.py`).
- **Plugin worlds**: Register in a conftest fixture, an entry-point
  script, or your package's `__init__.py`.
- **Test worlds**: Register in test fixtures with cleanup:

```python
import pytest
from axis.world.registry import register_world, _WORLD_REGISTRY

@pytest.fixture(autouse=True)
def _register_my_world():
    register_world("my_world", my_world_factory)
    yield
    _WORLD_REGISTRY.pop("my_world", None)
```

### 4.3 Using your world in a config file

```yaml
world:
  world_type: "my_world_type"
  grid_width: 12
  grid_height: 12
  obstacle_density: 0.1
  resource_regen_rate: 0.05
```

The framework calls `create_world_from_config(config, position, seed)`,
which looks up `"my_world_type"` in the registry and delegates to your
factory.

---

## 5. Regeneration compatibility

The built-in `apply_regeneration()` function works with any
`MutableWorldProtocol` implementation, but it accesses the internal
cell representation through `get_internal_cell()` and `set_cell()`.
It expects the internal cell to have:

- A `cell_type` attribute (a `CellType` enum: `EMPTY`, `RESOURCE`,
  `OBSTACLE`)
- A `resource_value` attribute (float, 0.0 to 1.0)
- A `regen_eligible` attribute (bool)

If your world uses the built-in `Cell` model from `axis.world.grid_2d.model`,
regeneration works automatically. If you use a custom cell type,
ensure it exposes these attributes or provide your own regeneration
logic.

The world owns its own dynamics. The framework runner calls `world.tick()`
once per step, and the world's `tick()` method internally calls
`apply_regeneration()` (or whatever custom regeneration logic you
implement). The regen rate is stored in the world at construction time
via the factory. Your custom world can implement `tick()` with completely
different dynamics if desired.

---

## 6. Complete example: Toroidal Grid World

This example implements a **toroidal (wraparound) grid world** where
agents that walk off one edge appear on the opposite side, instead of
being blocked. The grid topology is the only difference from the
built-in `grid_2d` -- cell types, resources, and regeneration work
identically.

### 6.1 The world class

```python
# src/axis/world/toroidal/model.py
"""Toroidal grid world -- edges wrap around."""

from __future__ import annotations

from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.world_types import CellView
from axis.world.grid_2d.model import Cell, CellType


class ToroidalWorld:
    """A 2D grid where movement wraps around at the edges.

    Walking off the right edge places the agent on the left edge
    (and vice versa). Same for top/bottom. All other behavior
    (cells, resources, obstacles) is identical to the built-in grid.

    Satisfies MutableWorldProtocol.
    """

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

        for y, row in enumerate(grid):
            if len(row) != self._width:
                raise ValueError(
                    f"Row {y} has width {len(row)}, expected {self._width}"
                )

        self._grid = grid
        self._regen_rate = regen_rate
        wrapped = self._wrap(agent_position)
        if not self._grid[wrapped.y][wrapped.x].is_traversable:
            raise ValueError(
                f"Agent position {wrapped} is on a non-traversable cell"
            )
        self._agent_position = wrapped

    def _wrap(self, position: Position) -> Position:
        """Wrap coordinates to stay within the grid (toroidal)."""
        return Position(
            x=position.x % self._width,
            y=position.y % self._height,
        )

    # --- WorldView protocol (read-only) ---

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def agent_position(self) -> Position:
        return self._agent_position

    @agent_position.setter
    def agent_position(self, position: Position) -> None:
        wrapped = self._wrap(position)
        if not self._grid[wrapped.y][wrapped.x].is_traversable:
            raise ValueError(
                f"Position {wrapped} is on a non-traversable cell"
            )
        self._agent_position = wrapped

    def get_cell(self, position: Position) -> CellView:
        if not self.is_within_bounds(position):
            raise ValueError(
                f"Position {position} is out of bounds "
                f"for grid of size ({self._width}, {self._height})"
            )
        cell = self._grid[position.y][position.x]
        return CellView(
            cell_type=cell.cell_type.value,
            resource_value=cell.resource_value,
        )

    def is_within_bounds(self, position: Position) -> bool:
        return 0 <= position.x < self._width and 0 <= position.y < self._height

    def is_traversable(self, position: Position) -> bool:
        # Wrap first, then check -- this is the toroidal magic.
        wrapped = self._wrap(position)
        return self._grid[wrapped.y][wrapped.x].is_traversable

    # --- Internal mutation API (framework-only) ---

    def get_internal_cell(self, position: Position) -> Cell:
        if not self.is_within_bounds(position):
            raise ValueError(f"Position {position} is out of bounds")
        return self._grid[position.y][position.x]

    def set_cell(self, position: Position, cell: Cell) -> None:
        if not self.is_within_bounds(position):
            raise ValueError(f"Position {position} is out of bounds")
        self._grid[position.y][position.x] = cell

    # --- World dynamics ---

    def tick(self) -> None:
        """Advance world dynamics (regeneration)."""
        from axis.world.grid_2d.dynamics import apply_regeneration
        apply_regeneration(self, regen_rate=self._regen_rate)

    def extract_resource(self, position: Position, max_amount: float) -> float:
        """Extract resource from a cell."""
        cell = self.get_internal_cell(position)
        if cell.resource_value <= 0:
            return 0.0
        delta = min(cell.resource_value, max_amount)
        remainder = cell.resource_value - delta
        if remainder <= 0:
            new_cell = Cell(
                cell_type=CellType.EMPTY, resource_value=0.0,
                regen_eligible=cell.regen_eligible,
            )
        else:
            new_cell = Cell(
                cell_type=CellType.RESOURCE, resource_value=remainder,
                regen_eligible=cell.regen_eligible,
            )
        self.set_cell(position, new_cell)
        return delta

    def snapshot(self) -> WorldSnapshot:
        """Create an immutable snapshot."""
        grid = tuple(
            tuple(self.get_cell(Position(x=x, y=y))
                  for x in range(self._width))
            for y in range(self._height)
        )
        return WorldSnapshot(
            grid=grid, agent_position=self._agent_position,
            width=self._width, height=self._height,
        )
```

### 6.2 The factory function

```python
# src/axis/world/toroidal/factory.py
"""Toroidal world factory: create_toroidal_world and helpers."""

from __future__ import annotations

import numpy as np

from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.world.grid_2d.model import Cell, CellType, RegenerationMode
from axis.world.toroidal.config import ToroidalWorldConfig
from axis.world.toroidal.model import ToroidalWorld


def _parse_toroidal_config(config: BaseWorldConfig) -> ToroidalWorldConfig:
    """Extract and validate toroidal fields from BaseWorldConfig extras."""
    extra_data = (
        {k: v for k, v in config.__pydantic_extra__.items()}
        if config.__pydantic_extra__
        else {}
    )
    return ToroidalWorldConfig(**extra_data)


def create_toroidal_world(
    config: BaseWorldConfig,
    agent_position: Position,
    seed: int | None = None,
) -> ToroidalWorld:
    """Create a toroidal grid world from configuration."""
    tc = _parse_toroidal_config(config)

    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    grid: list[list[Cell]] = [
        [empty for _ in range(tc.grid_width)]
        for _ in range(tc.grid_height)
    ]

    # Place obstacles
    if tc.obstacle_density > 0:
        _apply_obstacles(grid, tc, agent_position, seed)

    # Handle sparse regeneration eligibility
    regeneration_mode = RegenerationMode(tc.regeneration_mode)
    if regeneration_mode == RegenerationMode.SPARSE_FIXED_RATIO:
        _apply_sparse_eligibility(grid, tc.regen_eligible_ratio, seed)

    return ToroidalWorld(
        grid=grid, agent_position=agent_position,
        regen_rate=tc.resource_regen_rate,
    )
```

### 6.3 Registration

```python
# src/axis/world/toroidal/__init__.py
"""Toroidal world package -- wraparound grid world type."""

from axis.world.toroidal.config import ToroidalWorldConfig
from axis.world.toroidal.factory import create_toroidal_world
from axis.world.toroidal.model import ToroidalWorld

__all__ = [
    "ToroidalWorld",
    "ToroidalWorldConfig",
    "create_toroidal_world",
]

# --- Registration ---
from axis.world.registry import register_world  # noqa: E402


def _toroidal_factory(
    config: object,
    agent_position: object,
    seed: object,
) -> ToroidalWorld:
    return create_toroidal_world(config, agent_position, seed=seed)


register_world("toroidal", _toroidal_factory)
```

Because the toroidal world is now a built-in world type, its package
is imported by `axis.world.__init__` and registration happens
automatically on framework startup.

### 6.4 Using it in a config file

```yaml
system_type: "system_a"
experiment_type: "single_run"

general:
  seed: 42
execution:
  max_steps: 200
world:
  world_type: "toroidal"
  grid_width: 10
  grid_height: 10
  obstacle_density: 0.05
  resource_regen_rate: 0.03

system:
  agent:
    initial_energy: 50.0
    max_energy: 100.0
    buffer_capacity: 5
  policy:
    selection_mode: "sample"
    temperature: 1.0
    stay_suppression: 0.1
    consume_weight: 1.5
  transition:
    move_cost: 1.0
    consume_cost: 1.0
    stay_cost: 0.5
    max_consume: 1.0
    energy_gain_factor: 10.0

num_episodes_per_run: 5
```

The only change from a standard config is `world_type: "toroidal"`.
All systems work unchanged -- they interact with the world through
the same `WorldView` protocol regardless of the underlying topology.

### 6.5 How it differs from `grid_2d`

The toroidal world overrides the movement contract at the edges. In
the built-in `grid_2d`, walking into a wall is a no-op (the agent
stays put). In the toroidal world, the `agent_position` setter wraps
coordinates, so the built-in movement handlers in `ActionRegistry`
automatically support wraparound.

Movement handlers call `world.is_traversable(target)` before moving.
In `ToroidalWorld`, `is_traversable` wraps coordinates, so a target
at `x=-1` is checked against `x=width-1`. If the wrapped cell is
traversable, the movement succeeds and `world.agent_position = target`
wraps the coordinates.

No changes to the framework, the action engine, or any system are
needed. This is the power of the protocol-based design.

---

## 7. Testing your custom world

### 7.1 Protocol conformance test

Verify your world satisfies `MutableWorldProtocol` at runtime:

```python
from axis.sdk.world_types import MutableWorldProtocol

def test_protocol_conformance():
    world = create_my_world(...)
    assert isinstance(world, MutableWorldProtocol)
```

### 7.2 WorldView contract tests

The framework and systems rely on these behaviors:

```python
def test_get_cell_returns_cellview():
    world = create_my_world(...)
    cell = world.get_cell(Position(x=0, y=0))
    assert isinstance(cell, CellView)
    assert cell.cell_type in ("empty", "resource", "obstacle")
    assert 0.0 <= cell.resource_value <= 1.0

def test_is_traversable_false_for_obstacles():
    # Place an obstacle and verify
    world = create_my_world_with_obstacle_at(Position(x=1, y=1))
    assert not world.is_traversable(Position(x=1, y=1))

def test_agent_position_setter():
    world = create_my_world(...)
    new_pos = Position(x=1, y=0)
    world.agent_position = new_pos
    assert world.agent_position == new_pos
```

### 7.3 Regeneration compatibility test

If you use the built-in `apply_regeneration()`:

```python
from axis.world.grid_2d.dynamics import apply_regeneration
from axis.world.grid_2d.model import Cell, CellType

def test_regeneration_works():
    # Create a world with a regen-eligible empty cell
    world = create_my_world(...)
    count = apply_regeneration(world, regen_rate=0.1)
    # Verify cells gained resource
    assert count >= 0
```

### 7.4 Integration test through the framework

The strongest test: run a full episode through the framework with
your world type:

```python
from axis.framework.runner import setup_episode, run_episode
from axis.framework.registry import create_system
from axis.sdk.world_types import BaseWorldConfig

def test_full_episode():
    # Ensure your world type is registered
    world_config = BaseWorldConfig(
        world_type="my_world_type",
        grid_width=5,
        grid_height=5,
    )
    system = create_system("system_a", {...})
    world, registry = setup_episode(
        system, world_config, Position(x=0, y=0), seed=42
    )
    trace = run_episode(
        system, world, registry,
        max_steps=50, seed=42,
    )
    assert trace.total_steps > 0
```

---

## 8. Design guidelines

### 8.1 Keep `WorldView` honest

Systems trust `WorldView` to be read-only. Never expose mutation
methods through the `WorldView` interface. The `MutableWorldProtocol`
extension is for the framework only.

### 8.2 Use the built-in `Cell` model when possible

The `Cell` model from `axis.world.grid_2d.model` provides validated cell state
with proper invariants (obstacle cells have `resource_value == 0`,
etc.). Using it gives you free compatibility with `apply_regeneration()`
and `snapshot_world()`.

### 8.3 Deterministic world generation

Always use the `seed` parameter for any random operations (obstacle
placement, sparse eligibility). This ensures reproducible experiments.
Use `numpy.random.default_rng(seed)` for determinism.

### 8.4 Validate at construction time

Check all invariants in your `__init__`:
- Grid dimensions match `config.grid_width` and `config.grid_height`
- Agent start position is on a traversable cell
- No contradictory cell states

Fail fast with clear error messages.

### 8.5 Keep action handlers world-agnostic

The action handlers in `ActionRegistry` (movement, stay) work with any
`MutableWorldProtocol` implementation. They call `is_traversable()`,
`is_within_bounds()`, and the `agent_position` setter. If your world
type changes the semantics of these methods (like the toroidal world
does for `is_traversable`), the same action handlers automatically
adapt. You should not need to replace the built-in movement handlers.

---

## 9. API reference summary

### Registration

```python
from axis.world import register_world, registered_world_types

# Register a new world type
register_world("my_type", my_factory)

# List all registered types
types = registered_world_types()  # ("grid_2d", "signal_landscape", "toroidal")
```

### World creation

```python
from axis.world import create_world_from_config
from axis.sdk.world_types import BaseWorldConfig
from axis.sdk.position import Position

config = BaseWorldConfig(
    world_type="my_type",
    grid_width=10,
    grid_height=10,
)
world = create_world_from_config(config, Position(x=0, y=0), seed=42)
```

### Built-in world types

| Type | Module | Description |
|------|--------|-------------|
| `"grid_2d"` | `axis.world.grid_2d` | Standard 2D rectangular grid. Walls block movement. Default world type. |
| `"signal_landscape"` | `axis.world.signal_landscape` | Dynamic signal-based world with drifting Gaussian hotspots. Signal values are non-extractive. |
| `"toroidal"` | `axis.world.toroidal` | Toroidal (wraparound) variant of grid_2d. Edges wrap instead of blocking. |

---

## 10. Checklist for a new world type

- [ ] Implement a class satisfying `MutableWorldProtocol`
- [ ] Implement `tick()` for world dynamics
- [ ] Implement `extract_resource()` for resource extraction
- [ ] Implement `snapshot()` for world state capture
- [ ] Implement a factory function with signature `(BaseWorldConfig, Position, int | None) -> MutableWorldProtocol`
- [ ] Handle `obstacle_density` and `seed` for deterministic obstacle placement
- [ ] Handle `regeneration_mode` and `regen_eligible_ratio` for sparse eligibility
- [ ] Register via `register_world("your_type", your_factory)`
- [ ] Write a protocol conformance test (`isinstance(world, MutableWorldProtocol)`)
- [ ] Write a regeneration compatibility test (if using built-in `apply_regeneration`)
- [ ] Write a framework integration test (full episode via `run_episode()`)
- [ ] Document the world type and its config in your project docs
