# WP-2.2 Implementation Brief -- World Action Engine

> **Updated:** This spec has been updated to reflect the final implementation.
> Key changes from the original spec:
> - `apply_regeneration()` is now called internally by `World.tick()`,
>   not directly by the framework runner.
> - The framework runner calls `world.tick()` instead of
>   `apply_regeneration(world, regen_rate=...)`.
> - `apply_regeneration()` remains as an internal implementation detail
>   in `axis.world.dynamics`.

## Context

We are implementing the **modular architecture evolution** of the AXIS project. WP-2.1 extracted the world model (`Cell`, `World`, `create_world`) into `axis/world/`.

This work package is **WP-2.2**. It implements the framework-owned action application layer and world dynamics. In the v0.1.0 architecture, action application and world regeneration are embedded inside `transition.py:step()`. In v0.2.0, these become framework-owned components in `axis/world/`, called by the framework episode runner between the system's `decide()` and `transition()` phases.

### Predecessor State (After WP-2.1)

```
src/axis/world/
    __init__.py                 # Exports: CellType, RegenerationMode, Cell, World, create_world
    model.py                    # CellType, RegenerationMode, Cell, World (satisfies WorldView)
    factory.py                  # create_world()
```

The `World` class can be created and queried, but there is no way to apply actions to it or run dynamics. That logic currently lives in:

| Function | Location | Responsible For |
|----------|----------|----------------|
| `_apply_movement()` | `axis_system_a/transition.py` | Move agent if target is traversable |
| `_apply_consume()` | `axis_system_a/transition.py` | Extract resource from current cell |
| `_apply_regeneration()` | `axis_system_a/transition.py` | Tick all eligible cells |
| `_MOVEMENT_DELTAS` | `axis_system_a/transition.py` | Direction-to-delta mapping |

### Architectural Decisions (Binding)

- **Q2**: Framework-owned world mutation -- the framework applies actions to the world, not systems
- **Q4**: Shared base actions (movement + stay) handled by framework; system-specific actions (e.g., consume) are **registered** by systems as handlers
- **Q12**: Framework owns world structure; system owns dynamics parameters (e.g., regen rate). However, the regeneration *logic* runs as a framework operation on the world -- systems supply the rate parameter

### Key Design Principle: Action Handler Registration

In v0.1.0, consume logic is hardcoded in `transition.py`. In v0.2.0, the framework provides:

1. **Built-in handlers** for base actions: movement (up/down/left/right) and stay
2. **A registration mechanism** for system-specific actions: systems register a handler function that the framework calls when that action is selected

System A will register a `"consume"` handler in WP-2.3. The action engine dispatches to the correct handler based on action name.

### Reference Documents

- `docs/v0.2.0/architecture/evolution/architectural-vision-v0.2.0.md` -- Section 5 (World Framework)
- `docs/v0.2.0/architecture/evolution/modular-architecture-roadmap.md` -- WP-2.2 definition
- `docs/v0.2.0/specs/WP-1.2.md` -- ActionOutcome, MOVEMENT_DELTAS, BASE_ACTIONS
- `docs/v0.2.0/specs/WP-2.1.md` -- World, Cell, CellType

---

## Objective

Implement the framework-owned action application layer and world dynamics:

1. **`apply_action()`** -- dispatch function that applies an action to the world and returns `ActionOutcome`
2. **Built-in movement handler** -- handles `up`, `down`, `left`, `right` using `MOVEMENT_DELTAS`
3. **Built-in stay handler** -- no-op, returns current position
4. **Action handler registry** -- mechanism for systems to register custom action handlers (e.g., consume)
5. **`apply_regeneration()`** -- framework-owned world dynamics tick

---

## Scope

### 1. Action Handler Type

**File**: `src/axis/world/actions.py`

```python
from typing import Any, Protocol

from axis.sdk.world_types import ActionOutcome


class ActionHandler(Protocol):
    """Protocol for action handlers.

    Action handlers receive the world and an optional context dict,
    mutate the world, and return an ActionOutcome.
    """

    def __call__(
        self,
        world: Any,  # World (avoid circular import at type level)
        *,
        context: dict[str, Any],
    ) -> ActionOutcome:
        ...
```

**Design notes**:

- `context` carries action-specific parameters. For movement, no context is needed. For consume, `context` carries `{"max_consume": float}`.
- The `world` parameter is typed as `Any` at the protocol level to avoid circular imports. Implementations receive `World`.

### 2. Built-in Movement Handler

**File**: `src/axis/world/actions.py` (same file)

```python
from axis.sdk.actions import MOVEMENT_DELTAS
from axis.sdk.position import Position
from axis.sdk.world_types import ActionOutcome


def _handle_movement(
    world: World,
    action: str,
    *,
    context: dict[str, Any],
) -> ActionOutcome:
    """Handle a movement action (up/down/left/right).

    Attempts to move the agent in the specified direction.
    Movement succeeds if the target cell is within bounds and traversable.
    """
    delta = MOVEMENT_DELTAS[action]
    pos = world.agent_position
    target = Position(x=pos.x + delta[0], y=pos.y + delta[1])

    if world.is_within_bounds(target) and world.is_traversable(target):
        world.agent_position = target
        return ActionOutcome(action=action, moved=True, new_position=target)

    return ActionOutcome(action=action, moved=False, new_position=pos)
```

**Design notes**:

- Functionally identical to `axis_system_a/transition.py:_apply_movement()`
- Now returns `ActionOutcome` instead of a bare `bool`
- Uses `MOVEMENT_DELTAS` from `axis.sdk.actions` (same data, string keys)

### 3. Built-in Stay Handler

**File**: `src/axis/world/actions.py` (same file)

```python
def _handle_stay(
    world: World,
    *,
    context: dict[str, Any],
) -> ActionOutcome:
    """Handle the stay action. No world mutation."""
    return ActionOutcome(
        action="stay",
        moved=False,
        new_position=world.agent_position,
    )
```

### 4. Action Registry and Dispatch

**File**: `src/axis/world/actions.py` (same file)

```python
class ActionRegistry:
    """Registry for action handlers.

    Base actions (movement + stay) are registered automatically.
    Systems register additional handlers for custom actions.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, ActionHandler] = {}
        # Register built-in handlers
        for action_name in MOVEMENT_DELTAS:
            self._handlers[action_name] = _make_movement_handler(action_name)
        self._handlers["stay"] = _handle_stay

    def register(self, action_name: str, handler: ActionHandler) -> None:
        """Register a handler for a custom action.

        Raises ValueError if action_name is a base action (cannot override).
        """
        if action_name in BASE_ACTIONS:
            raise ValueError(
                f"Cannot override base action handler: {action_name}"
            )
        if action_name in self._handlers:
            raise ValueError(
                f"Handler already registered for action: {action_name}"
            )
        self._handlers[action_name] = handler

    def has_handler(self, action_name: str) -> bool:
        """Check if a handler is registered for the given action."""
        return action_name in self._handlers

    @property
    def registered_actions(self) -> tuple[str, ...]:
        """Return all registered action names."""
        return tuple(self._handlers.keys())

    def apply(
        self,
        world: World,
        action: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> ActionOutcome:
        """Apply an action to the world.

        Dispatches to the registered handler for the given action name.
        Raises KeyError if no handler is registered.
        """
        if action not in self._handlers:
            raise KeyError(f"No handler registered for action: {action}")
        handler = self._handlers[action]
        return handler(world, context=context or {})


def _make_movement_handler(action_name: str) -> ActionHandler:
    """Create a movement handler bound to a specific direction."""
    def handler(world: World, *, context: dict[str, Any]) -> ActionOutcome:
        return _handle_movement(world, action_name, context=context)
    return handler


def create_action_registry() -> ActionRegistry:
    """Create a new ActionRegistry with base actions pre-registered."""
    return ActionRegistry()
```

**Design notes**:

- Base actions are auto-registered and cannot be overridden
- Custom actions (like `"consume"`) are registered by systems during initialization
- `apply()` is the single dispatch point -- the framework calls this, not individual handlers
- `create_action_registry()` is a convenience factory

### 5. World Dynamics -- Regeneration

**File**: `src/axis/world/dynamics.py`

```python
from axis.sdk.position import Position
from axis.world.model import Cell, CellType, World


def apply_regeneration(world: MutableWorldProtocol, *, regen_rate: float) -> int:
    """Apply deterministic cell regeneration to all eligible cells.

    For each non-obstacle, regen-eligible cell:
        r_next = min(1.0, r_current + regen_rate)
    EMPTY cells that gain resource become RESOURCE cells.

    Returns the number of cells updated.

    Note: The framework runner calls world.tick() instead of calling
    apply_regeneration() directly. World.tick() delegates to this
    function internally.
    """
    if regen_rate == 0.0:
        return 0

    count = 0
    for y in range(world.height):
        for x in range(world.width):
            pos = Position(x=x, y=y)
            cell = world.get_internal_cell(pos)

            if cell.cell_type is CellType.OBSTACLE:
                continue
            if not cell.regen_eligible:
                continue

            new_resource = min(1.0, cell.resource_value + regen_rate)
            if new_resource == cell.resource_value:
                continue

            count += 1
            if new_resource > 0:
                new_cell = Cell(
                    cell_type=CellType.RESOURCE,
                    resource_value=new_resource,
                    regen_eligible=cell.regen_eligible,
                )
            else:
                new_cell = Cell(
                    cell_type=CellType.EMPTY,
                    resource_value=0.0,
                    regen_eligible=cell.regen_eligible,
                )
            world.set_cell(pos, new_cell)

    return count
```

**Design notes**:

- Functionally identical to `axis_system_a/transition.py:_apply_regeneration()`
- Uses `world.get_internal_cell()` (needs full `Cell` with `regen_eligible`)
- Uses `world.set_cell()` (framework mutation API)
- Called by the framework episode runner **before** action application at each step (maintaining the v0.1.0 6-phase pipeline ordering)

### 6. Package Exports Update

**File**: `src/axis/world/__init__.py`

```python
"""World Framework -- world model, factory, action engine, dynamics."""

from axis.world.actions import ActionRegistry, create_action_registry
from axis.world.dynamics import apply_regeneration
from axis.world.factory import create_world
from axis.world.model import Cell, CellType, RegenerationMode, World

__all__ = [
    "CellType",
    "RegenerationMode",
    "Cell",
    "World",
    "create_world",
    "ActionRegistry",
    "create_action_registry",
    "apply_regeneration",
]
```

---

## Out of Scope

Do **not** implement any of the following in WP-2.2:

- The consume action handler (System A registers this in WP-2.3)
- System A implementation (WP-2.3)
- The framework episode runner that calls these components (WP-3.2)
- Any modifications to `axis_system_a` code
- Any modifications to `axis.sdk` or `axis.framework`
- Cost computation / energy updates (system-owned, WP-2.3)

---

## Architectural Constraints

### 1. Framework Ownership

The action engine and dynamics are **framework-owned**. They live in `axis.world`, not in any system package. The framework calls them on behalf of systems.

### 2. Action Registration Flow

The intended registration flow (fully realized in WP-2.3 and WP-3.2):

```
1. Framework creates an ActionRegistry (base actions pre-registered)
2. System registers custom actions: registry.register("consume", consume_handler)
3. Each step: framework calls registry.apply(world, action, context=...)
4. Registry dispatches to the correct handler
5. Handler mutates the world and returns ActionOutcome
```

### 3. Regeneration Timing

Regeneration runs **before** action application at each step, preserving the v0.1.0 pipeline ordering:

```
1. world.tick()                               # Phase 1 (world advances its own dynamics)
2. registry.apply(world, action, context=...) # Phase 2
3. system.transition(...)                      # Phases 4-6 (energy, memory, termination)
```

Phase 3 (new observation) is constructed by the episode runner between phases 2 and system.transition().

### 4. Context Dict Pattern

Action handlers receive a `context: dict[str, Any]` for action-specific parameters:

| Action | Context | Purpose |
|--------|---------|---------|
| Movement | `{}` (empty) | No extra params needed |
| Stay | `{}` (empty) | No extra params needed |
| Consume (WP-2.3) | `{"max_consume": float}` | Maximum resource extraction per action |

This avoids embedding system-specific parameters in the handler signature.

### 5. Dependency Direction

```
axis.world.actions imports from axis.sdk  (MOVEMENT_DELTAS, BASE_ACTIONS, Position, ActionOutcome)
axis.world.actions imports from axis.world.model  (World)
axis.world.dynamics imports from axis.world.model  (World, Cell, CellType)
axis.world does NOT import from axis.framework, axis.systems, or axis.visualization
```

---

## Expected File Structure

After WP-2.2, these files are **new or modified**:

```
src/axis/world/__init__.py                  # MODIFIED (new exports)
src/axis/world/actions.py                   # NEW (ActionRegistry, handlers, dispatch)
src/axis/world/dynamics.py                  # NEW (apply_regeneration)
tests/v02/world/test_actions.py             # NEW (action engine tests)
tests/v02/world/test_dynamics.py            # NEW (regeneration tests)
tests/v02/test_scaffold.py                  # MODIFIED (updated axis.world exports)
```

Unchanged:

```
src/axis/world/model.py                     # UNCHANGED (from WP-2.1)
src/axis/world/factory.py                   # UNCHANGED (from WP-2.1)
src/axis/sdk/                               # UNCHANGED
src/axis/framework/                         # UNCHANGED
src/axis_system_a/                          # UNCHANGED
```

---

## Testing Requirements

### Action engine tests (`tests/v02/world/test_actions.py`)

Must include:

1. **ActionRegistry construction**:
   - New registry has handlers for all 5 base actions
   - `registered_actions` includes `"up"`, `"down"`, `"left"`, `"right"`, `"stay"`
   - `has_handler("up")` is `True`
   - `has_handler("consume")` is `False`

2. **Movement actions**:
   - Move up from `(2, 2)` on open grid -> new position `(2, 1)`, `moved=True`
   - Move down -> `(2, 3)`, `moved=True`
   - Move left -> `(1, 2)`, `moved=True`
   - Move right -> `(3, 2)`, `moved=True`
   - Move into obstacle -> `moved=False`, position unchanged
   - Move out of bounds -> `moved=False`, position unchanged
   - Action name echoed in `ActionOutcome.action`

3. **Stay action**:
   - Position unchanged, `moved=False`, `data` is empty dict

4. **Custom action registration**:
   - `register("consume", handler)` succeeds
   - `has_handler("consume")` becomes `True`
   - Overriding a base action raises `ValueError`
   - Registering a duplicate custom action raises `ValueError`
   - Dispatching to registered custom handler works

5. **Dispatch to unknown action**:
   - `apply(world, "unknown")` raises `KeyError`

6. **ActionOutcome correctness**:
   - All returned outcomes are `ActionOutcome` instances
   - Movement outcomes: `consumed=False`, `resource_consumed=0.0` (defaults)
   - `new_position` reflects actual post-action position

### Dynamics tests (`tests/v02/world/test_dynamics.py`)

Must include:

1. **No-op when rate is zero**:
   - `apply_regeneration(world, regen_rate=0.0)` returns 0, world unchanged

2. **Basic regeneration**:
   - World with an empty regen-eligible cell and `regen_rate=0.1` -> cell gains resource, becomes RESOURCE
   - Returns count of updated cells

3. **Resource accumulation**:
   - RESOURCE cell with value 0.5 + rate 0.3 -> value 0.8
   - RESOURCE cell with value 0.9 + rate 0.2 -> clamped to 1.0

4. **Obstacle cells skipped**:
   - Obstacles are never regenerated

5. **Non-eligible cells skipped**:
   - Cells with `regen_eligible=False` are skipped even if traversable

6. **Full grid regeneration**:
   - Multiple cells updated in one call, count matches

### Existing test suite

All existing tests must still pass.

---

## Implementation Style

- Python 3.11+
- `typing.Protocol` for `ActionHandler`
- Clear separation: action dispatch (actions.py) vs dynamics (dynamics.py)
- Handler functions, not classes (simple callables)
- No complex metaprogramming
- Deterministic behavior: same inputs produce same outputs

---

## Expected Deliverable

1. `src/axis/world/actions.py` with `ActionRegistry`, movement/stay handlers, dispatch
2. `src/axis/world/dynamics.py` with `apply_regeneration()`
3. Updated `src/axis/world/__init__.py` with new exports
4. Action tests at `tests/v02/world/test_actions.py`
5. Dynamics tests at `tests/v02/world/test_dynamics.py`
6. Updated `tests/v02/test_scaffold.py` for updated `axis.world` exports
7. Confirmation that all existing tests still pass

---

## Important Final Constraint

This WP provides the **framework's world mutation infrastructure**. The action engine is the mechanism through which the framework applies system-chosen actions to the world, fulfilling Q2 (framework-owned mutation).

The key design property is the **registry pattern**: base actions are built-in, custom actions are pluggable. This enables multi-system support without hardcoding action handling logic. System A will register its consume handler in WP-2.3; future systems can register different custom actions.

The regeneration logic is a direct extraction from `transition.py:_apply_regeneration()`. The only change is that it uses `World.get_internal_cell()` instead of `World.get_cell()` (since `get_cell()` now returns `CellView` per WP-2.1).
