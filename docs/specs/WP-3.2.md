# WP-3.2 Implementation Brief -- Framework Episode Runner

## Context

We are implementing **Phase 3 -- Framework Alignment** of the AXIS modular architecture evolution. WP-3.1 provided the system registry. This work package implements the framework-owned episode execution loop that works with **any** `SystemInterface` implementation.

### Predecessor State (After WP-3.1)

```
src/axis/
    sdk/
        interfaces.py       # SystemInterface (decide/transition + action_handlers)
        types.py             # DecideResult, TransitionResult
        world_types.py       # WorldView, ActionOutcome, BaseWorldConfig
        trace.py             # BaseStepTrace, BaseEpisodeTrace
        snapshot.py          # WorldSnapshot, snapshot_world
        actions.py           # BASE_ACTIONS, MOVEMENT_DELTAS
    framework/
        config.py            # FrameworkConfig, ExperimentConfig, OFAT utilities
        registry.py          # register_system, create_system, get_system_factory
    world/
        model.py             # World, Cell, CellType
        factory.py           # create_world()
        actions.py           # ActionRegistry, create_action_registry()
        dynamics.py          # apply_regeneration()
    systems/system_a/
        system.py            # SystemA implements SystemInterface + action_handlers()
        ...
```

The framework has a registry but no episode runner. The only runner is the legacy `axis_system_a.runner.run_episode()` which is tightly coupled to System A's internal pipeline.

### Architectural Decisions (Binding)

- **Q1 = Two-phase step contract**: `system.decide()` returns action intent -> framework applies to world -> `system.transition()` processes outcome
- **Q2 = Framework applies actions**: Systems never mutate the world; the framework applies actions via `ActionRegistry`
- **Q3 = Framework-owned regeneration**: Regeneration runs as a framework step, configured via `FrameworkConfig`
- **Q9 = Snapshots**: 2 mandatory snapshots (`BEFORE`, `AFTER_ACTION`) + optional named intermediates
- **Q16 = Dual termination**: Framework enforces `max_steps`; systems signal via `terminated=True`

### Reference Documents

- `docs/architecture/evolution/modular-architecture-roadmap.md` -- WP-3.2 definition
- `docs/architecture/evolution/modular-architecture-questions-answers.md` -- Q1, Q2, Q3, Q9, Q16
- `src/axis_system_a/runner.py` -- Legacy runner (reference implementation)
- WP-2.4 `test_equivalence.py` -- manually orchestrates the same lifecycle; validates correctness

---

## Objective

Implement a system-agnostic episode runner that:

1. Orchestrates the step lifecycle (regen -> decide -> apply action -> observe -> transition)
2. Captures `BaseStepTrace` at each step and produces a `BaseEpisodeTrace`
3. Works with any `SystemInterface` implementation
4. Produces identical behavior to WP-2.4's equivalence test orchestration (which is validated against the legacy runner)

---

## Scope

### 1. Step Lifecycle

The framework runner owns the full step lifecycle. The ordering is derived from the legacy `transition.py` 6-phase pipeline, decomposed into framework-owned and system-owned phases:

```
Per timestep:
  1. [Framework] Capture BEFORE snapshot
  2. [System]    system.decide(world, agent_state, rng) -> DecideResult
  3. [Framework] Apply regeneration: apply_regeneration(world, regen_rate)
  4. [Framework] Apply action: registry.apply(world, action, context) -> ActionOutcome
  5. [Framework] Capture AFTER_ACTION snapshot
  6. [System]    system.transition(agent_state, action_outcome, new_observation) -> TransitionResult
  7. [Framework] Build BaseStepTrace
  8. [Framework] Check termination (system-signaled or max_steps)
```

**Critical ordering note**: The system's `decide()` sees the world **before** this step's regeneration. Regeneration happens after the decision but before action application. This matches the legacy pipeline where regeneration is phase 1 of `transition.step()`, which runs after the drive/policy have selected an action.

**Observation for transition**: After the framework applies the action (step 4), the system needs a new observation to process the outcome. The system's sensor builds this observation internally during `transition()`, OR the framework passes additional context. Since `SystemInterface.transition()` takes `new_observation: Any`, the framework is responsible for providing the post-action observation.

**Design decision**: The framework calls `system.sensor.observe()` (if available) or lets the system handle it. However, `SystemInterface` does not expose `.sensor` -- the sub-interfaces are internal to the system.

**Resolution**: The observation for `transition()` is beyond the framework's knowledge (it's system-specific). Two options:

- **(A)** Framework builds a generic observation (WorldView) and passes it. The system's `transition()` receives a `WorldView`, not a system-specific `Observation`.
- **(B)** The framework passes the world and position; the system builds its own observation inside `transition()`.

**Choice: (A) -- Pass `WorldView`**. The `transition()` signature already accepts `new_observation: Any`. The framework passes the `World` (which satisfies `WorldView`). The system's `transition()` implementation then internally calls its sensor to build the system-specific observation from the `WorldView`. This keeps the framework generic while letting systems use their own observation types.

Wait -- reviewing the existing `SystemA.transition()` signature and WP-2.4 equivalence tests, the framework passes a **system-specific `Observation`** built by `system.sensor.observe()`. This means the framework currently needs access to the system's sensor.

**Revised approach**: The framework does NOT build observations. Instead:

- **(C)** The `SystemInterface` gains a method `observe(world_view, position) -> Any` that the framework calls to get the post-action observation. This delegates to the system's internal sensor. The framework passes the result to `transition()`.

This is cleanest: the framework calls three system methods per step: `decide()`, `observe()`, `transition()`.

Actually, checking the existing `SystemInterface` in `src/axis/sdk/interfaces.py`, it does NOT have an `observe()` method. The sub-interfaces (`SensorInterface`) are internal contracts. In WP-2.4's equivalence tests, the test code directly accesses `system.sensor.observe()` -- but this is a System A-specific implementation detail, not part of the SDK interface.

**Final design**: Add `observe(world_view: Any, position: Any) -> Any` to `SystemInterface`. This is the minimal method the framework needs to obtain a system-specific observation without knowing the system's internals.

### 2. Runner Module (`axis/framework/runner.py`)

```python
"""Framework-owned episode execution loop."""

from __future__ import annotations

from typing import Any

import numpy as np

from axis.sdk.interfaces import SystemInterface
from axis.sdk.snapshot import WorldSnapshot, snapshot_world
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import ActionOutcome
from axis.world.actions import ActionRegistry
from axis.world.dynamics import apply_regeneration
from axis.world.model import World


def run_episode(
    system: SystemInterface,
    world: World,
    registry: ActionRegistry,
    *,
    max_steps: int,
    regen_rate: float,
    seed: int,
    action_context_builder: Callable[[SystemInterface], dict[str, Any]] | None = None,
) -> BaseEpisodeTrace:
    """Run a complete episode from initialization to termination.

    Parameters
    ----------
    system : A SystemInterface implementation (already constructed).
    world : A mutable World (already created with correct grid layout).
    registry : ActionRegistry with all actions registered (base + system-specific).
    max_steps : Maximum step count (framework termination).
    regen_rate : Per-step resource regeneration rate.
    seed : RNG seed for this episode.
    action_context_builder : Optional callable that builds the action context dict
        from the system. If None, an empty context is used.

    Returns
    -------
    BaseEpisodeTrace with step-by-step traces.
    """
```

**Action context**: Some action handlers need system-specific parameters (e.g., `handle_consume` needs `max_consume` from System A's transition config). The runner cannot know about these system-specific parameters.

**Solution**: The `action_context_builder` parameter. The caller (RunExecutor in WP-3.3) provides a function that extracts the needed context from the system config. For System A, this would be:

```python
def system_a_context_builder(system):
    return {"max_consume": system.config.transition.max_consume}
```

However, this leaks system internals into the executor. A cleaner approach:

**Better solution**: Add `action_context() -> dict[str, Any]` to `SystemInterface`. The system provides the context dict that its action handlers need. The framework runner calls `system.action_context()` once at setup time and passes it to every `registry.apply()` call.

For System A:
```python
def action_context(self) -> dict[str, Any]:
    return {"max_consume": self._config.transition.max_consume}
```

For systems with no custom action context:
```python
def action_context(self) -> dict[str, Any]:
    return {}
```

This is the simplest design -- the system knows what context its handlers need.

### 3. Revised Runner Signature

```python
def run_episode(
    system: SystemInterface,
    world: World,
    registry: ActionRegistry,
    *,
    max_steps: int,
    regen_rate: float,
    seed: int,
) -> BaseEpisodeTrace:
```

The runner internally:
1. Creates `rng = np.random.default_rng(seed)`
2. Initializes agent state via `system.initialize_state(system_config)` -- but wait, the runner doesn't have the system config dict. The system is already constructed.

**State initialization**: `system.initialize_state()` needs the system config dict. The runner doesn't have this. Options:
- **(A)** The system stores its config and `initialize_state()` uses it internally (no config arg needed).
- **(B)** The runner receives the config dict and passes it.
- **(C)** `initialize_state()` takes no arguments -- it uses the config stored at construction time.

**Choice: (C)**. The system was already constructed with its config. `initialize_state()` should use the stored config to produce the initial agent state. The current signature `initialize_state(system_config: dict[str, Any])` was designed before the system stores its own config. We simplify to `initialize_state() -> Any`.

Actually, checking the existing `SystemA.initialize_state()`:
```python
def initialize_state(self, system_config: dict[str, Any]) -> AgentState:
    return AgentState(
        energy=self._config.agent.initial_energy,
        memory_state=MemoryState(entries=(), capacity=self._config.agent.memory_capacity),
    )
```

It already uses `self._config` internally -- the `system_config` parameter is unused! So changing the signature to no-arg is safe.

**Revised**: Change `SystemInterface.initialize_state()` from `(system_config: dict) -> Any` to `() -> Any`.

### 4. Step Implementation

```python
def _run_step(
    system: SystemInterface,
    world: World,
    registry: ActionRegistry,
    agent_state: Any,
    rng: np.random.Generator,
    timestep: int,
    *,
    regen_rate: float,
    action_context: dict[str, Any],
) -> tuple[Any, BaseStepTrace]:
    """Execute one step of the episode loop.

    Returns (new_agent_state, step_trace).
    """
    # 1. Capture BEFORE snapshot
    world_before = snapshot_world(world)
    position_before = world.agent_position
    vitality_before = system.vitality(agent_state)

    # 2. System decides
    decide_result = system.decide(world, agent_state, rng)

    # 3. Framework applies regeneration
    apply_regeneration(world, regen_rate=regen_rate)

    # 4. Framework applies action
    outcome = registry.apply(world, decide_result.action, context=action_context)

    # 5. Capture AFTER_ACTION snapshot
    world_after = snapshot_world(world)
    position_after = world.agent_position

    # 6. System observes post-action world
    new_observation = system.observe(world, world.agent_position)

    # 7. System transitions
    transition_result = system.transition(agent_state, outcome, new_observation)
    new_state = transition_result.new_state
    vitality_after = system.vitality(new_state)

    # 8. Build step trace
    step_trace = BaseStepTrace(
        timestep=timestep,
        action=decide_result.action,
        world_before=world_before,
        world_after=world_after,
        intermediate_snapshots={},
        agent_position_before=position_before,
        agent_position_after=position_after,
        vitality_before=vitality_before,
        vitality_after=vitality_after,
        terminated=transition_result.terminated,
        termination_reason=transition_result.termination_reason,
        system_data={
            "decision_data": decide_result.decision_data,
            "trace_data": transition_result.trace_data,
        },
    )

    return new_state, step_trace
```

### 5. Episode Loop

```python
def run_episode(...) -> BaseEpisodeTrace:
    rng = np.random.default_rng(seed)
    agent_state = system.initialize_state()
    action_context = system.action_context()
    steps: list[BaseStepTrace] = []

    for timestep in range(max_steps):
        agent_state, step_trace = _run_step(
            system, world, registry, agent_state, rng, timestep,
            regen_rate=regen_rate, action_context=action_context,
        )
        steps.append(step_trace)

        if step_trace.terminated:
            termination_reason = step_trace.termination_reason or "system_terminated"
            break
    else:
        termination_reason = "max_steps_reached"

    return BaseEpisodeTrace(
        system_type=system.system_type(),
        steps=tuple(steps),
        total_steps=len(steps),
        termination_reason=termination_reason,
        final_vitality=system.vitality(agent_state),
        final_position=world.agent_position,
    )
```

### 6. Setup Helper

A convenience function to wire up the runner from higher-level config:

```python
def setup_episode(
    system: SystemInterface,
    world_config: BaseWorldConfig,
    start_position: Position,
    *,
    seed: int,
    regen_rate: float = 0.0,
    regeneration_mode: str = "all_traversable",
    regen_eligible_ratio: float | None = None,
) -> tuple[World, ActionRegistry]:
    """Create a world and action registry for an episode.

    Returns (world, registry) ready for run_episode().
    """
    from axis.world.factory import create_world
    from axis.world.model import RegenerationMode

    world = create_world(
        world_config, start_position, seed=seed,
        regeneration_mode=RegenerationMode(regeneration_mode),
        regen_eligible_ratio=regen_eligible_ratio,
    )

    registry = create_action_registry()
    for action_name, handler in system.action_handlers().items():
        registry.register(action_name, handler)

    return world, registry
```

### 7. SystemInterface Changes Summary

Methods added or modified on `SystemInterface`:

| Method | Change | Reason |
|--------|--------|--------|
| `observe(world_view, position) -> Any` | **NEW** | Framework needs post-action observation for `transition()` |
| `action_context() -> dict[str, Any]` | **NEW** | System provides context for its custom action handlers |
| `initialize_state() -> Any` | **SIGNATURE CHANGE** | Remove unused `system_config` parameter |

These changes also require updates to `SystemA` in `axis/systems/system_a/system.py`.

---

## Out of Scope

Do **not** implement any of the following in WP-3.2:

- RunExecutor / ExperimentExecutor (WP-3.3)
- Persistence (WP-3.4)
- CLI (WP-3.5)
- Logging/observability during episodes (carry forward later)
- Run-level seeding (per-episode seed derivation is WP-3.3)
- World creation from `ExperimentConfig` (WP-3.3 orchestrates this)

---

## Architectural Constraints

### 1. System-Agnostic

The runner module must **never** import from `axis.systems.system_a` or any specific system package. It operates entirely through `SystemInterface` and the world/action infrastructure.

### 2. Deterministic

Given the same `system`, `world`, `seed`, and config, the runner must produce identical `BaseEpisodeTrace` every time.

### 3. No Logging Side Effects

Unlike the legacy `run_episode()` which creates an `AxisLogger`, the new runner produces data only. Logging is a concern for the executor layer (WP-3.3) or a future observability WP.

### 4. Snapshot Efficiency

`snapshot_world()` captures the full grid at each step (BEFORE and AFTER_ACTION -- 2 per step). For large grids or long episodes, this can be expensive. For now, always capture both mandatory snapshots per Q9. Optimization (lazy snapshots, snapshot diffing) is out of scope.

### 5. Regeneration Source

The `regen_rate` is a parameter to `run_episode()`. The caller (executor) extracts it from the system config's `world_dynamics` section or from the framework config. The runner just applies it.

---

## Expected File Structure

After WP-3.2, these files are **new**:

```
src/axis/framework/runner.py             # NEW (episode runner)
tests/framework/test_runner.py       # NEW (runner tests)
```

These files are **modified**:

```
src/axis/sdk/interfaces.py              # MODIFIED (add observe, action_context; change initialize_state)
src/axis/systems/system_a/system.py     # MODIFIED (implement observe, action_context; update initialize_state)
src/axis/framework/__init__.py          # MODIFIED (add runner exports)
tests/test_scaffold.py              # MODIFIED (update framework exports)
```

---

## Testing Requirements

### Runner Tests (`tests/framework/test_runner.py`)

Tests use System A as the concrete system (it's the only registered system), but the test design validates framework-generic behavior.

| Test | Description |
|------|-------------|
| `test_run_episode_returns_episode_trace` | Result is `BaseEpisodeTrace` |
| `test_episode_trace_system_type` | `trace.system_type == "system_a"` |
| `test_episode_trace_has_steps` | `len(trace.steps) > 0` |
| `test_step_trace_structure` | Each step has all `BaseStepTrace` fields |
| `test_step_trace_action_in_action_space` | Each step's action is valid |
| `test_step_trace_vitality_bounds` | Vitality values in [0.0, 1.0] |
| `test_step_trace_world_snapshots` | `world_before` and `world_after` are `WorldSnapshot` |
| `test_step_trace_positions` | Positions are valid `Position` objects |
| `test_termination_energy_depleted` | Low energy -> terminates early |
| `test_termination_max_steps` | High energy, low max_steps -> `"max_steps_reached"` |
| `test_deterministic_same_seed` | Same seed -> identical traces |
| `test_different_seeds_differ` | Different seeds -> different action sequences |
| `test_system_data_has_decision_data` | `step.system_data["decision_data"]` exists |
| `test_system_data_has_trace_data` | `step.system_data["trace_data"]` exists |
| `test_setup_episode_creates_world_and_registry` | `setup_episode()` returns valid `(World, ActionRegistry)` |
| `test_setup_episode_registers_system_actions` | Registry has system's custom actions |
| `test_equivalence_with_manual_orchestration` | Runner output matches WP-2.4 equivalence test orchestration |

The last test is critical: it verifies that `run_episode()` produces the same results as the manually-orchestrated loop in `test_equivalence.py`.

All existing tests (1657+) must continue to pass.

---

## Implementation Style

- Python 3.11+
- Pure functions where possible (`_run_step` as internal helper)
- No classes -- the runner is a module with functions
- `run_episode()` and `setup_episode()` are the public API
- Tests use System A via the registry (`create_system("system_a", config)`)

---

## Expected Deliverable

1. Runner module at `src/axis/framework/runner.py`
2. `observe()` and `action_context()` added to `SystemInterface`
3. `initialize_state()` signature changed (no args)
4. `SystemA` updated to implement new interface methods
5. Updated `src/axis/framework/__init__.py`
6. Updated `tests/test_scaffold.py`
7. Runner tests at `tests/framework/test_runner.py`
8. Confirmation that all tests pass
