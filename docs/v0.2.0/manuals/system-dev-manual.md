# AXIS Experimentation Framework -- System Developer Manual (v0.2.0)

## Overview

This manual explains how to build a custom system that plugs into the
AXIS experimentation framework. A **system** encapsulates all agent
logic -- sensing, decision-making, state transitions -- while the
framework owns world mutation, episode orchestration, and persistence.

The boundary is defined by a single protocol: `SystemInterface`. If
your class satisfies that protocol, the framework can run it without
any modifications to framework code.

This manual walks through the full process using a worked example:
**System B**, a "scout" agent that extends the base movement actions
with a `scan` action for detecting nearby resources without consuming
them.

---

## 1. Architecture at a glance

```
┌───────────────────────────────────────────────────┐
│  Framework (you do NOT modify this)               │
│                                                   │
│   World ─── ActionRegistry ─── Runner ─── CLI     │
│     │            │                │                │
│     │    base handlers:          │                │
│     │    up/down/left/right/stay │                │
│     │            │               │                │
│     │   ┌── custom handlers ──┐  │                │
│     │   │    (from system)    │  │                │
│     │   └─────────────────────┘  │                │
└─────┼────────────────────────────┼────────────────┘
      │  WorldView (read-only)     │  SystemInterface
      ▼                            ▼
┌───────────────────────────────────────────────────┐
│  Your System (you build this)                     │
│                                                   │
│   Sensor ─── Drive ─── Policy ─── Transition      │
│                                                   │
│   Config types     Agent state     Action handlers │
└───────────────────────────────────────────────────┘
```

Key ownership rules:

| Concern | Owner |
|---------|-------|
| World grid, cells, agent position | Framework |
| Movement actions (up/down/left/right/stay) | Framework |
| Action dispatch (ActionRegistry) | Framework |
| Episode loop, step sequencing | Framework |
| Persistence, experiment execution | Framework |
| Sensor, drives, policy, transition logic | System |
| Agent state (energy, memory, etc.) | System |
| Custom actions (consume, scan, etc.) | System |
| System-specific config parsing | System |

---

## 2. The SystemInterface protocol

Your system must satisfy the `SystemInterface` protocol defined in
`src/axis/sdk/interfaces.py`. It uses `@runtime_checkable`, so the
framework validates conformance at construction time.

Here is the complete contract:

```python
class SystemInterface(Protocol):
    def system_type(self) -> str: ...
    def action_space(self) -> tuple[str, ...]: ...
    def initialize_state(self) -> Any: ...
    def vitality(self, agent_state: Any) -> float: ...
    def decide(self, world_view: Any, agent_state: Any, rng: np.random.Generator) -> DecideResult: ...
    def transition(self, agent_state: Any, action_outcome: Any, new_observation: Any) -> TransitionResult: ...
    def observe(self, world_view: Any, position: Any) -> Any: ...
    def action_handlers(self) -> dict[str, Any]: ...
    def action_context(self) -> dict[str, Any]: ...
```

Each method is explained below with its role in the framework's
episode loop.

### 2.1 `system_type() -> str`

Returns a unique identifier string (e.g. `"system_b"`). This must
match the string used in `register_system()` and in config files
(`system_type: "system_b"`).

### 2.2 `action_space() -> tuple[str, ...]`

Returns all actions this system can produce, including the five base
actions. The order matters -- it defines the index mapping for
drive contributions and policy probabilities.

```python
# Must always include the 5 base actions:
("up", "down", "left", "right", "stay")

# Add custom actions in between (by convention, before "stay"):
("up", "down", "left", "right", "scan", "stay")
```

### 2.3 `initialize_state() -> Any`

Creates the initial agent state from configuration. The returned
value is **opaque to the framework** -- the framework never inspects
it. It passes it back to `decide()` and `transition()` unchanged.

You can use any type: a Pydantic model, a plain dict, a dataclass, or
even a tuple. The framework does not care.

```python
# Pydantic model (System A style):
return AgentState(energy=50.0, memory_state=MemoryState(...))

# Plain dict (MockSystem style):
return {"energy": 10.0, "scan_cooldown": 0}
```

### 2.4 `vitality(agent_state: Any) -> float`

Returns a normalized scalar in `[0.0, 1.0]` representing the agent's
"health". This is the only metric the framework reads from agent state.
It appears in traces, summaries, and OFAT comparisons.

Typical formulas:
- Energy system: `energy / max_energy`
- Fixed-lifetime system: `remaining_steps / max_steps`
- Boolean: `1.0` if alive, `0.0` if dead

### 2.5 `decide(world_view, agent_state, rng) -> DecideResult`

**Phase 1** of the two-phase step. Called once per timestep before the
framework applies any action.

Inputs:
- `world_view` -- a read-only `WorldView` of the world grid. You can
  query cell types, resource values, traversability, and grid
  dimensions. You **cannot** mutate the world through this view.
- `agent_state` -- whatever you returned from `initialize_state()` or
  the previous `transition()` call.
- `rng` -- a `numpy.random.Generator` seeded by the framework. Use
  this for all stochastic decisions to guarantee reproducibility.

Output: a `DecideResult` with two fields:
- `action: str` -- the chosen action name (must be in `action_space()`)
- `decision_data: dict[str, Any]` -- arbitrary trace data (logged to
  `system_data.decision_data` in the step trace). Include whatever is
  useful for analysis.

### 2.6 `transition(agent_state, action_outcome, new_observation) -> TransitionResult`

**Phase 2** of the two-phase step. Called after the framework has
applied the action and regenerated resources.

Inputs:
- `agent_state` -- the current agent state.
- `action_outcome` -- an `ActionOutcome` telling you what happened:
  ```python
  ActionOutcome(
      action="right",         # which action was applied
      moved=True,             # whether position changed
      new_position=Position(x=3, y=2),
      consumed=False,         # True only for consume-type actions
      resource_consumed=0.0,  # amount consumed
  )
  ```
- `new_observation` -- the observation from `observe()` after the
  action, reflecting the post-action world state.

Output: a `TransitionResult` with four fields:
- `new_state: Any` -- the updated agent state (opaque to framework)
- `trace_data: dict[str, Any]` -- logged to `system_data.trace_data`
- `terminated: bool` -- `True` to end the episode from the system side
- `termination_reason: str | None` -- e.g. `"energy_depleted"`

### 2.7 `observe(world_view, position) -> Any`

Produces a system-specific observation. Called by the framework runner
after action application to obtain the `new_observation` argument for
`transition()`. The return type is opaque -- the framework passes it
through without inspection.

### 2.8 `action_handlers() -> dict[str, Any]`

Returns a mapping of custom action names to handler callables. These
are registered with the `ActionRegistry` before episode execution.
Systems that only use base actions return `{}`.

Each handler must match the `ActionHandler` protocol:

```python
def my_handler(world: World, *, context: dict[str, Any]) -> ActionOutcome:
    ...
```

The handler receives the **mutable** `World` (not the read-only
`WorldView`) and a context dict. It may mutate the world (e.g. extract
resources from a cell) and must return an `ActionOutcome`.

**Important constraints:**
- You **cannot** override base actions (up/down/left/right/stay). The
  registry raises `ValueError` if you try.
- Each custom action name can only be registered once.

### 2.9 `action_context() -> dict[str, Any]`

Returns a dict of values your action handlers need. Called once at
episode setup and passed to every `registry.apply()` call. Systems
with no custom actions or no context needs return `{}`.

---

## 3. The episode loop

Understanding when each method is called helps you design your system
correctly. Here is the full step-by-step flow for one episode:

```
1. setup_episode()
   a. Framework creates the World from BaseWorldConfig
   b. Framework creates ActionRegistry with base handlers
   c. Framework calls system.action_handlers() and registers each one
   d. Framework calls system.action_context() and stores the result

2. run_episode()
   a. Framework calls system.initialize_state() → agent_state
   b. For each timestep until max_steps or termination:

      PHASE 1 -- DECIDE
      c. Framework calls system.decide(world_view, agent_state, rng) → DecideResult
      d. Framework applies resource regeneration to the world
      e. Framework calls registry.apply(world, action, context=ctx) → ActionOutcome
         - If action is "up"/"down"/"left"/"right": built-in movement handler
         - If action is "stay": built-in stay handler
         - If action is custom: YOUR registered handler

      PHASE 2 -- TRANSITION
      f. Framework calls system.observe(world, position) → new_observation
      g. Framework calls system.transition(agent_state, outcome, new_observation) → TransitionResult
      h. Framework records the step trace
      i. If terminated: episode ends

   c. Framework assembles the BaseEpisodeTrace
```

Note: regeneration happens **between** decide and action application.
Your system's `decide()` sees the pre-regeneration world; your
`transition()` sees the post-regeneration, post-action world.

---

## 4. Worked example: System B (Scout Agent)

System B is a scout agent that navigates the grid collecting resources
(like System A) but replaces the `consume` action with a `scan`
action. Scanning reveals the total resource value in a 3x3
neighborhood around the agent without consuming anything. The agent
uses scan results to bias its movement toward resource-rich areas.

### 4.1 Project layout

```
src/axis/systems/system_b/
    __init__.py
    system.py          # SystemB class
    config.py          # SystemBConfig
    actions.py         # handle_scan
    types.py           # AgentState, ScanResult
```

### 4.2 Agent state and types

```python
# src/axis/systems/system_b/types.py
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field


class ScanResult(BaseModel):
    """Result of the most recent scan action."""
    model_config = ConfigDict(frozen=True)

    total_resource: float = 0.0
    cell_count: int = 0


class AgentState(BaseModel):
    """System B agent state: energy + last scan result."""
    model_config = ConfigDict(frozen=True)

    energy: float = Field(..., ge=0)
    last_scan: ScanResult = Field(default_factory=ScanResult)
```

### 4.3 Configuration

```python
# src/axis/systems/system_b/config.py
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field


class AgentConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    initial_energy: float = Field(..., gt=0)
    max_energy: float = Field(..., gt=0)


class PolicyConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    selection_mode: str = "sample"   # "sample" or "argmax"
    temperature: float = Field(default=1.0, gt=0)
    scan_bonus: float = Field(default=2.0, ge=0)


class TransitionConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    move_cost: float = Field(default=1.0, gt=0)
    scan_cost: float = Field(default=0.5, gt=0)
    stay_cost: float = Field(default=0.5, ge=0)


class WorldDynamicsConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    resource_regen_rate: float = Field(default=0.0, ge=0, le=1)
    regeneration_mode: str = "all_traversable"
    regen_eligible_ratio: float | None = Field(default=None, gt=0, le=1)


class SystemBConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    agent: AgentConfig
    policy: PolicyConfig = Field(default_factory=PolicyConfig)
    transition: TransitionConfig = Field(default_factory=TransitionConfig)
    world_dynamics: WorldDynamicsConfig = Field(
        default_factory=WorldDynamicsConfig,
    )
```

### 4.4 The `scan` action handler

This is the key extension point. The handler receives the mutable
`World` object and a context dict.

```python
# src/axis/systems/system_b/actions.py
from __future__ import annotations
from typing import Any

from axis.sdk.position import Position
from axis.sdk.world_types import ActionOutcome
from axis.world.model import World


def handle_scan(
    world: World,
    *,
    context: dict[str, Any],
) -> ActionOutcome:
    """Scan a 3x3 neighborhood. Does NOT modify the world."""
    pos = world.agent_position
    scan_radius: int = context.get("scan_radius", 1)

    total_resource = 0.0
    cell_count = 0

    for dy in range(-scan_radius, scan_radius + 1):
        for dx in range(-scan_radius, scan_radius + 1):
            target = Position(x=pos.x + dx, y=pos.y + dy)
            if world.is_within_bounds(target):
                cell = world.get_cell(target)  # read-only CellView
                total_resource += cell.resource_value
                cell_count += 1

    # Scan never moves the agent and never consumes resources.
    # We encode the scan result in the ActionOutcome's generic fields.
    return ActionOutcome(
        action="scan",
        moved=False,
        new_position=pos,
        consumed=False,
        resource_consumed=total_resource,  # repurposed: total detected
    )
```

**Important design notes:**

1. The handler uses `world.get_cell()` (which returns the read-only
   `CellView`) for reading. To mutate cells, use
   `world.get_internal_cell()` and `world.set_cell()` -- but `scan`
   intentionally does not mutate.

2. The `ActionOutcome` model has fixed fields (`moved`, `consumed`,
   `resource_consumed`). You reuse these to convey your action's
   result. The framework does not interpret `resource_consumed` -- only
   your `transition()` method reads it. So you can repurpose it (here
   we store total detected resource).

3. If your action needs to communicate more data, encode it in
   `resource_consumed` or `consumed` flags. The framework passes the
   `ActionOutcome` opaquely to your `transition()`.

### 4.5 The SystemB class

```python
# src/axis/systems/system_b/system.py
from __future__ import annotations
from typing import Any

import numpy as np

from axis.sdk.actions import MOVEMENT_DELTAS
from axis.sdk.position import Position
from axis.sdk.types import DecideResult, TransitionResult
from axis.sdk.world_types import WorldView

from axis.systems.system_b.config import SystemBConfig
from axis.systems.system_b.types import AgentState, ScanResult


class SystemB:
    """System B: scout agent with scan action."""

    def __init__(self, config: SystemBConfig) -> None:
        self._config = config

    def system_type(self) -> str:
        return "system_b"

    def action_space(self) -> tuple[str, ...]:
        return ("up", "down", "left", "right", "scan", "stay")

    def initialize_state(self) -> AgentState:
        return AgentState(energy=self._config.agent.initial_energy)

    def vitality(self, agent_state: Any) -> float:
        return agent_state.energy / self._config.agent.max_energy

    def decide(
        self,
        world_view: Any,
        agent_state: Any,
        rng: np.random.Generator,
    ) -> DecideResult:
        # Simple heuristic: if last scan found resources, prefer
        # moving toward them; otherwise scan to gather intel.
        actions = self.action_space()
        n = len(actions)
        weights = [1.0] * n

        # Boost scan if we haven't scanned yet or scan is old
        scan_idx = actions.index("scan")
        if agent_state.last_scan.total_resource == 0:
            weights[scan_idx] = self._config.policy.scan_bonus

        # Boost directions based on neighbor resources
        for i, direction in enumerate(("up", "down", "left", "right")):
            delta = MOVEMENT_DELTAS[direction]
            target = Position(
                x=world_view.agent_position.x + delta[0],
                y=world_view.agent_position.y + delta[1],
            )
            if world_view.is_within_bounds(target) and world_view.is_traversable(target):
                cell = world_view.get_cell(target)
                weights[i] += cell.resource_value * 2.0
            else:
                weights[i] = 0.0  # inadmissible

        # Softmax selection
        beta = 1.0 / self._config.policy.temperature
        max_w = max(w for w in weights if w > 0)
        exp_w = [
            np.exp(beta * (w - max_w)) if w > 0 else 0.0
            for w in weights
        ]
        total = sum(exp_w)
        probs = [e / total for e in exp_w]

        if self._config.policy.selection_mode == "argmax":
            action_idx = probs.index(max(probs))
        else:
            action_idx = int(rng.choice(n, p=probs))

        return DecideResult(
            action=actions[action_idx],
            decision_data={
                "weights": weights,
                "probabilities": probs,
                "last_scan": agent_state.last_scan.model_dump(),
            },
        )

    def transition(
        self,
        agent_state: Any,
        action_outcome: Any,
        new_observation: Any,
    ) -> TransitionResult:
        action = action_outcome.action
        tc = self._config.transition

        # Determine energy cost
        if action in MOVEMENT_DELTAS:
            cost = tc.move_cost
        elif action == "scan":
            cost = tc.scan_cost
        else:
            cost = tc.stay_cost

        new_energy = max(0.0, min(
            agent_state.energy - cost,
            self._config.agent.max_energy,
        ))

        # Update scan result if this was a scan action
        if action == "scan":
            last_scan = ScanResult(
                total_resource=action_outcome.resource_consumed,
                cell_count=9,  # 3x3
            )
        else:
            last_scan = agent_state.last_scan

        new_state = AgentState(energy=new_energy, last_scan=last_scan)
        terminated = new_energy <= 0.0

        return TransitionResult(
            new_state=new_state,
            trace_data={
                "energy_before": agent_state.energy,
                "energy_after": new_energy,
                "action_cost": cost,
                "scan_total": last_scan.total_resource,
            },
            terminated=terminated,
            termination_reason="energy_depleted" if terminated else None,
        )

    def observe(self, world_view: Any, position: Any) -> dict[str, Any]:
        """Minimal observation: just the position."""
        return {"x": position.x, "y": position.y}

    def action_handlers(self) -> dict[str, Any]:
        from axis.systems.system_b.actions import handle_scan
        return {"scan": handle_scan}

    def action_context(self) -> dict[str, Any]:
        return {"scan_radius": 1}
```

### 4.6 Package init

```python
# src/axis/systems/system_b/__init__.py
from axis.systems.system_b.config import SystemBConfig
from axis.systems.system_b.system import SystemB

__all__ = ["SystemB", "SystemBConfig"]
```

---

## 5. Registering your system

The framework discovers systems through a central registry. You need
one call to `register_system()` with a factory function.

### 5.1 The factory function

A factory takes a `dict[str, Any]` (the raw `system` dict from the
config file) and returns a `SystemInterface` instance:

```python
from typing import Any
from axis.sdk.interfaces import SystemInterface


def _system_b_factory(system_config: dict[str, Any]) -> SystemInterface:
    from axis.systems.system_b import SystemB, SystemBConfig
    config = SystemBConfig(**system_config)
    return SystemB(config)
```

The factory is responsible for parsing the opaque dict into your
typed config. Use Pydantic's `**system_config` unpacking -- it gives
you validation, type coercion, and clear error messages for free.

### 5.2 Registering

There are two approaches:

**Option A: Auto-register on import** (recommended for built-in
systems). Add this to your package's `__init__.py` or to
`src/axis/framework/registry.py`:

```python
from axis.framework.registry import register_system

register_system("system_b", _system_b_factory)
```

This is how System A registers itself -- see
`src/axis/framework/registry.py:67-68`.

**Option B: Register in test fixtures or entry-point scripts**
(recommended for experimental systems or external packages):

```python
import pytest
from axis.framework.registry import register_system, _SYSTEM_REGISTRY

@pytest.fixture(autouse=True)
def _register_system_b():
    register_system("system_b", _system_b_factory)
    yield
    _SYSTEM_REGISTRY.pop("system_b", None)  # cleanup
```

### 5.3 What happens at runtime

```
config YAML: system_type: "system_b"
     │
     ▼
registry.get_system_factory("system_b")
     │
     ▼
_system_b_factory({"agent": {...}, "policy": {...}, ...})
     │
     ▼
SystemBConfig(**raw_dict)  →  SystemB(config)
     │
     ▼
framework calls system.action_handlers()  →  {"scan": handle_scan}
framework calls system.action_context()   →  {"scan_radius": 1}
ActionRegistry.register("scan", handle_scan)
     │
     ▼
Episode loop: decide → apply → transition → ...
```

---

## 6. Writing a config file for your system

The experiment config format separates framework config from system
config. Your system's parameters go inside the `system:` dict.

```yaml
# experiments/configs/v02/system-b-baseline.yaml
system_type: "system_b"
experiment_type: "single_run"

general:
  seed: 42

execution:
  max_steps: 200

world:
  grid_width: 10
  grid_height: 10
  obstacle_density: 0.1

system:
  agent:
    initial_energy: 30.0
    max_energy: 50.0
  policy:
    selection_mode: "sample"
    temperature: 1.0
    scan_bonus: 2.0
  transition:
    move_cost: 1.0
    scan_cost: 0.5
    stay_cost: 0.5
  world_dynamics:
    resource_regen_rate: 0.05

num_episodes_per_run: 5
```

### 6.1 Framework sections vs system sections

These sections are **framework-owned** -- identical for all systems:

| Section     | Fields |
|-------------|--------|
| `general`   | `seed` |
| `execution` | `max_steps` |
| `world`     | `grid_width`, `grid_height`, `obstacle_density` |
| `logging`   | `enabled`, `console_enabled`, `verbosity`, ... |

The `system:` section is an **opaque dict** -- the framework passes it
to your factory without inspection. Its internal structure is entirely
up to you.

### 6.2 Common mistake: world vs system.world_dynamics

The top-level `world:` section configures the grid structure
(dimensions, obstacles). Parameters like resource regeneration rate
and regeneration mode are **system-owned** and belong under
`system.world_dynamics:`.

```yaml
# CORRECT:
world:
  grid_width: 10        # framework-owned
  grid_height: 10       # framework-owned
  obstacle_density: 0.1 # framework-owned

system:
  world_dynamics:
    resource_regen_rate: 0.05     # system-owned
    regeneration_mode: "sparse_fixed_ratio"  # system-owned
    regen_eligible_ratio: 0.17   # system-owned

# WRONG -- framework will reject these fields under world:
world:
  regeneration_mode: "sparse_fixed_ratio"  # ✗ not a BaseWorldConfig field
```

### 6.3 OFAT parameter paths

To sweep one of your system's parameters in an OFAT experiment, use
a 3-segment path with the `system` domain prefix:

```yaml
experiment_type: "ofat"
parameter_path: "system.policy.scan_bonus"
parameter_values: [0.5, 1.0, 2.0, 5.0]
```

Framework parameters use the `framework` prefix:

```yaml
parameter_path: "framework.execution.max_steps"
parameter_values: [100, 200, 500]
```

---

## 7. Custom action handlers in depth

### 7.1 Handler signature

Every custom action handler must conform to the `ActionHandler`
protocol:

```python
def handle_something(
    world: World,         # mutable World (not WorldView)
    *,
    context: dict[str, Any],  # from action_context()
) -> ActionOutcome:
    ...
```

### 7.2 Reading vs mutating the world

The handler receives the full mutable `World`. You have access to
two APIs:

**Read-only (safe for any action):**
- `world.agent_position` -- current Position
- `world.get_cell(pos)` -- returns `CellView(cell_type, resource_value)`
- `world.is_within_bounds(pos)` -- bounds check
- `world.is_traversable(pos)` -- traversability check
- `world.width`, `world.height` -- grid dimensions

**Mutation (use only when your action modifies the world):**
- `world.agent_position = new_pos` -- move the agent
- `world.get_internal_cell(pos)` -- returns internal `Cell` with
  `regen_eligible`
- `world.set_cell(pos, new_cell)` -- replace a cell

For non-mutating actions like `scan`, use only the read-only API.
For resource-extracting actions like `consume`, use the mutation API.

### 7.3 Returning ActionOutcome

Every handler must return an `ActionOutcome`:

```python
ActionOutcome(
    action: str,              # the action name
    moved: bool,              # whether agent position changed
    new_position: Position,   # agent position after action
    consumed: bool = False,   # whether resources were extracted
    resource_consumed: float = 0.0,  # amount extracted
)
```

The `consumed` and `resource_consumed` fields are conventions. The
framework does not interpret them -- it passes the entire
`ActionOutcome` to your `transition()`. You can repurpose
`resource_consumed` to carry custom numeric data (as System B does
with scan results).

### 7.4 The context dict

Use `action_context()` to provide configuration values that your
handlers need. This avoids hard-coding constants in the handler:

```python
# In your system class:
def action_context(self) -> dict[str, Any]:
    return {"scan_radius": 1, "scan_energy_boost": 0.5}

# In your handler:
def handle_scan(world: World, *, context: dict[str, Any]) -> ActionOutcome:
    radius = context["scan_radius"]
    ...
```

The context is created once per episode and shared across all steps.

### 7.5 Base action protection

You cannot register handlers for the five base actions. The
`ActionRegistry` raises `ValueError`:

```
ValueError: Cannot override base action handler: up
```

If you need to modify movement semantics (e.g. "movement costs double
energy"), handle it in your `transition()` method by inspecting the
`action_outcome.action` string.

---

## 8. SDK types reference

All types your system interacts with are in the `axis.sdk` package.

### 8.1 Input types (framework → system)

| Type | Module | Used in |
|------|--------|---------|
| `WorldView` | `axis.sdk.world_types` | `decide()` -- read-only world access |
| `CellView(cell_type, resource_value)` | `axis.sdk.world_types` | Returned by `world_view.get_cell()` |
| `Position(x, y)` | `axis.sdk.position` | Grid coordinates |
| `ActionOutcome(...)` | `axis.sdk.world_types` | `transition()` -- action result |

### 8.2 Output types (system → framework)

| Type | Module | Returned by |
|------|--------|-------------|
| `DecideResult(action, decision_data)` | `axis.sdk.types` | `decide()` |
| `TransitionResult(new_state, trace_data, terminated, termination_reason)` | `axis.sdk.types` | `transition()` |
| `PolicyResult(action, policy_data)` | `axis.sdk.types` | `PolicyInterface.select()` (optional) |

### 8.3 Constants

| Constant | Module | Value |
|----------|--------|-------|
| `BASE_ACTIONS` | `axis.sdk.actions` | `("up", "down", "left", "right", "stay")` |
| `MOVEMENT_DELTAS` | `axis.sdk.actions` | `{"up": (0,-1), "down": (0,1), "left": (-1,0), "right": (1,0)}` |

---

## 9. Trace data and what gets persisted

Every step produces a `BaseStepTrace`. The framework fills in:
- `timestep`, `action`
- `world_before`, `world_after` (full grid snapshots)
- `agent_position_before`, `agent_position_after`
- `vitality_before`, `vitality_after`
- `terminated`, `termination_reason`

Your system contributes through `system_data`:

```json
{
  "system_data": {
    "decision_data": { ... },   // from DecideResult.decision_data
    "trace_data": { ... }       // from TransitionResult.trace_data
  }
}
```

Design `decision_data` and `trace_data` to include whatever you need
for post-hoc analysis. Common patterns:

- **Policy diagnostics**: action probabilities, temperature, selected
  action index
- **State deltas**: energy before/after, scan results
- **Drive activations**: intermediate computations that influenced the
  action choice

These dicts are serialized to JSON via Pydantic, so use only
JSON-serializable values (strings, numbers, lists, dicts, bools,
None). Avoid numpy arrays -- convert to lists first.

---

## 10. Internal components (optional architecture)

The `SystemInterface` does not prescribe internal structure. You can
implement everything in one class. However, System A demonstrates a
clean decomposition into four internal components, each with its own
SDK protocol:

| Component | Protocol | Responsibility |
|-----------|----------|---------------|
| Sensor | `SensorInterface` | World → observation |
| Drive | `DriveInterface` | (state, observation) → drive output |
| Policy | `PolicyInterface` | (drive output, observation, rng) → action |
| Transition | `TransitionInterface` | (state, outcome, observation) → new state |

This is entirely optional. Your system can use any internal
architecture. The framework only sees `SystemInterface`.

### 10.1 When to decompose

**Keep it simple** for prototyping or small systems. A single class
with inline logic (like the MockSystem or System B above) is fine.

**Decompose** when:
- You want to swap one component (e.g. try different policies with
  the same sensor and drive)
- Components are complex enough to warrant independent unit testing
- You plan to reuse components across systems

---

## 11. Testing your system

### 11.1 Unit testing the system in isolation

Test your system methods directly without the framework:

```python
import numpy as np
from axis.systems.system_b import SystemB, SystemBConfig

def test_system_b_decide():
    config = SystemBConfig(
        agent={"initial_energy": 30, "max_energy": 50},
    )
    system = SystemB(config)
    state = system.initialize_state()
    rng = np.random.default_rng(42)

    # Create a mock world_view or use a real World
    from axis.sdk.world_types import BaseWorldConfig
    from axis.sdk.position import Position
    from axis.framework.runner import setup_episode

    world, registry = setup_episode(
        system,
        BaseWorldConfig(grid_width=5, grid_height=5),
        Position(x=2, y=2),
        seed=42,
    )

    result = system.decide(world, state, rng)
    assert result.action in system.action_space()
```

### 11.2 Testing custom action handlers

```python
from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.systems.system_b.actions import handle_scan
from axis.world.factory import create_world

def test_scan_does_not_mutate():
    config = BaseWorldConfig(grid_width=5, grid_height=5)
    world = create_world(config, Position(x=2, y=2), seed=42)

    # Record state before scan
    before = world.get_cell(Position(x=2, y=2))

    outcome = handle_scan(world, context={"scan_radius": 1})

    # Verify no mutation
    after = world.get_cell(Position(x=2, y=2))
    assert after == before
    assert outcome.action == "scan"
    assert outcome.moved is False
```

### 11.3 Integration testing through the framework

The most thorough test runs your system through the full framework
pipeline:

```python
from pathlib import Path
from axis.framework.registry import register_system, _SYSTEM_REGISTRY
from axis.framework.experiment import execute_experiment
from axis.framework.config import ExperimentConfig

def _system_b_factory(cfg):
    from axis.systems.system_b import SystemB, SystemBConfig
    return SystemB(SystemBConfig(**cfg))

def test_system_b_full_experiment(tmp_path):
    register_system("system_b", _system_b_factory)
    try:
        config = ExperimentConfig(
            system_type="system_b",
            experiment_type="single_run",
            general={"seed": 42},
            execution={"max_steps": 50},
            world={"grid_width": 5, "grid_height": 5},
            system={"agent": {"initial_energy": 30, "max_energy": 50}},
            num_episodes_per_run=3,
        )
        result = execute_experiment(config, tmp_path)
        assert result.status == "completed"
        assert len(result.run_results) == 1
        summary = result.run_results[0].summary
        assert summary.num_episodes == 3
        assert 0.0 <= summary.mean_final_vitality <= 1.0
    finally:
        _SYSTEM_REGISTRY.pop("system_b", None)
```

### 11.4 Protocol conformance check

Use `isinstance` checks to verify your system satisfies the protocol:

```python
from axis.sdk.interfaces import SystemInterface

def test_system_b_protocol():
    config = SystemBConfig(agent={"initial_energy": 30, "max_energy": 50})
    system = SystemB(config)
    assert isinstance(system, SystemInterface)
```

---

## 12. Checklist: building a new system

1. **Define your agent state type** -- what internal state does your
   agent maintain? (energy, memory, scan buffer, belief map, etc.)

2. **Define your config type** -- what parameters can be tuned?
   Use Pydantic models with validation for clean error messages.

3. **Decide on custom actions** -- what actions beyond
   up/down/left/right/stay does your agent need? Write a handler
   for each.

4. **Implement `SystemInterface`** -- fill in all 9 methods.

5. **Write a factory function** -- `dict[str, Any] → SystemInterface`.

6. **Register your system** -- call `register_system("my_system", factory)`.

7. **Create a config file** -- YAML or JSON with `system_type: "my_system"`.

8. **Test** -- unit tests for handlers, integration test through
   `execute_experiment`.

9. **Run** -- `axis experiments run my-config.yaml`.

---

## 13. Quick reference: what to import

```python
# SDK types (for your system implementation)
from axis.sdk.interfaces import SystemInterface
from axis.sdk.types import DecideResult, TransitionResult, PolicyResult
from axis.sdk.world_types import WorldView, CellView, ActionOutcome, BaseWorldConfig
from axis.sdk.position import Position
from axis.sdk.actions import BASE_ACTIONS, MOVEMENT_DELTAS

# World model (for action handlers only)
from axis.world.model import World, Cell, CellType

# Framework registration
from axis.framework.registry import register_system

# Framework execution (for integration tests)
from axis.framework.runner import setup_episode, run_episode
from axis.framework.config import ExperimentConfig
from axis.framework.experiment import execute_experiment
```
