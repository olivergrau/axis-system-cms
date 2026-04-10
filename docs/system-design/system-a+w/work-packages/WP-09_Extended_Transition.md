# WP-9: Extended Transition Function

## Metadata
- Work Package: WP-9
- Title: Extended Transition Function
- System: System A+W
- Source File: `src/axis/systems/system_aw/transition.py`
- Test File: `tests/systems/system_aw/test_transition.py`
- Model Reference: `01_System A+W Model.md`, Section 8
- Worked Examples: `02_System A+W Worked Examples.md`, Examples D1, F1, F3
- Dependencies: WP-2 (types: `AgentStateAW`), WP-3 (inherited: `update_memory`), WP-4 (world model: `update_world_model`)

---

## 1. Objective

Implement the extended state transition function that adds dead reckoning and world model update to System A's energy + memory transition. This is where the world model is maintained at runtime.

**Critical constraint:** The transition reads only `action_outcome.action` and `action_outcome.moved`. It **never reads** `action_outcome.new_position`. The agent has no access to absolute coordinates.

---

## 2. Design

### 2.1 Five-Phase Transition

The transition extends System A's 3-phase transition to 5 phases (Model Section 8):

| Phase | Operation | Source | Changed? |
|---|---|---|---|
| 1 | Energy update | $e_{t+1} = \text{clip}(e_t - c(a_t) + \kappa \cdot \Delta R^{cons}, 0, E_{\max})$ | Unchanged |
| 2 | Memory update | $m_{t+1} = M(m_t, u_{t+1})$ | Unchanged |
| 3 | Dead reckoning | $\hat{p}_{t+1} = \hat{p}_t + \mu_t \cdot \Delta(a_t)$ | **New** |
| 4 | World model update | $w_{t+1}(\hat{p}_{t+1}) += 1$ | **New** |
| 5 | Termination check | $e_{t+1} \leq 0$ | Unchanged |

Phases 3 and 4 are handled in a single call to `update_world_model()` from WP-4.

### 2.2 New vs. System A's Transition

System A's `SystemATransition` returns `AgentState(energy, memory_state)`. System A+W's transition returns `AgentStateAW(energy, memory_state, world_model)`.

Rather than inheriting from `SystemATransition`, we create an independent `SystemAWTransition` that:
- Replicates the energy and memory logic (using the same helper functions)
- Adds the world model update
- Returns `AgentStateAW`

This avoids a fragile inheritance chain and keeps the transition self-contained.

### 2.3 Coordinate Frame Note

The SDK defines `MOVEMENT_DELTAS` with **world coordinates** (y increases downward): `UP: (0, -1)`, `DOWN: (0, +1)`.

The dead reckoning world model (WP-4) uses **agent-relative coordinates** where `UP: (0, +1)`, `DOWN: (0, -1)`.

These are independent coordinate frames. The transition calls `update_world_model(state, action, moved)`, which uses its own `DIRECTION_DELTAS` internally. The transition **does not** pass SDK deltas to the world model — it passes only the action string. This keeps the coordinate frames decoupled.

---

## 3. Specification

```python
"""System A+W transition -- energy, memory, dead reckoning, world model, termination."""

from __future__ import annotations

from axis.sdk.actions import MOVEMENT_DELTAS, STAY
from axis.sdk.types import TransitionResult
from axis.sdk.world_types import ActionOutcome
from axis.systems.system_a.memory import update_memory
from axis.systems.system_a.types import Observation, clip_energy
from axis.systems.system_aw.types import AgentStateAW
from axis.systems.system_aw.world_model import update_world_model


class SystemAWTransition:
    """Transition function for System A+W.

    Extends System A's transition with dead reckoning and
    world model update.

    Five phases (Model Section 8):
    1. Energy update
    2. Memory update
    3. Dead reckoning update
    4. World model update
    5. Termination check

    Critical: reads only action_outcome.action and action_outcome.moved.
    Never reads action_outcome.new_position.
    """

    def __init__(
        self,
        *,
        max_energy: float,
        move_cost: float,
        consume_cost: float,
        stay_cost: float,
        energy_gain_factor: float,
    ) -> None:
        self._max_energy = max_energy
        self._move_cost = move_cost
        self._consume_cost = consume_cost
        self._stay_cost = stay_cost
        self._energy_gain_factor = energy_gain_factor

    def transition(
        self,
        agent_state: AgentStateAW,
        action_outcome: ActionOutcome,
        observation: Observation,
        *,
        timestep: int = 0,
    ) -> TransitionResult:
        """Process action outcome: energy, memory, world model, termination."""

        # Phase 1: Energy update (unchanged from System A)
        cost = self._get_action_cost(action_outcome.action)
        energy_gain = self._energy_gain_factor * \
            action_outcome.data.get("resource_consumed", 0.0)
        new_energy = clip_energy(
            agent_state.energy - cost + energy_gain,
            self._max_energy,
        )

        # Phase 2: Memory update (unchanged from System A)
        new_memory = update_memory(
            agent_state.memory_state, observation, timestep,
        )

        # Phase 3 + 4: Dead reckoning + world model update (NEW)
        # Uses only action_outcome.action and action_outcome.moved
        new_world_model = update_world_model(
            agent_state.world_model,
            action_outcome.action,
            action_outcome.moved,
        )

        # Assemble new state
        new_state = AgentStateAW(
            energy=new_energy,
            memory_state=new_memory,
            world_model=new_world_model,
        )

        # Phase 5: Termination check (unchanged from System A)
        terminated = new_energy <= 0.0
        termination_reason = "energy_depleted" if terminated else None

        trace_data = {
            "energy_before": agent_state.energy,
            "energy_after": new_energy,
            "energy_delta": new_energy - agent_state.energy,
            "action_cost": cost,
            "energy_gain": energy_gain,
            "memory_entries_before": len(agent_state.memory_state.entries),
            "memory_entries_after": len(new_memory.entries),
            "relative_position": new_world_model.relative_position,
            "visit_count_at_current": dict(new_world_model.visit_counts).get(
                new_world_model.relative_position, 0
            ),
        }

        return TransitionResult(
            new_state=new_state,
            trace_data=trace_data,
            terminated=terminated,
            termination_reason=termination_reason,
        )

    def _get_action_cost(self, action: str) -> float:
        """Return the energy cost for a given action."""
        if action in MOVEMENT_DELTAS:
            return self._move_cost
        if action == "consume":
            return self._consume_cost
        if action == STAY:
            return self._stay_cost
        return self._stay_cost
```

### 3.1 Trace Data Extensions

System A+W's trace data includes two new fields beyond System A:

| Field | Type | Description |
|---|---|---|
| `relative_position` | `tuple[int, int]` | Agent's relative position after this step |
| `visit_count_at_current` | `int` | Visit count at the current relative position |

These are used by the logging runtime (EpisodeLogger) and visualization (WP-12).

---

## 4. What This Module Does NOT Access

Explicitly documenting the prohibition:

- `action_outcome.new_position` — **never accessed**. This is the framework's absolute position, which the agent does not own.
- `world_view` or `WorldView` — not available in `transition()`. The framework only passes `agent_state`, `action_outcome`, and `new_observation`.
- Any SDK `Position` type — not imported, not used.

---

## 5. Test Plan

### File: `tests/systems/system_aw/test_transition.py`

#### Energy Update (Phase 1)

| # | Test | Description |
|---|---|---|
| 1 | `test_move_cost_deducted` | Movement action → energy decreases by `move_cost` |
| 2 | `test_consume_cost_and_gain` | CONSUME with resource → energy = old - consume_cost + gain_factor * consumed |
| 3 | `test_stay_cost` | STAY → energy decreases by `stay_cost` |
| 4 | `test_energy_clipped_at_max` | Energy gain doesn't exceed `max_energy` |
| 5 | `test_energy_clipped_at_zero` | Energy doesn't go below 0.0 |

#### Memory Update (Phase 2)

| # | Test | Description |
|---|---|---|
| 6 | `test_memory_appended` | New observation is added to memory |
| 7 | `test_memory_fifo_overflow` | At capacity, oldest entry is dropped |

#### Dead Reckoning + World Model (Phases 3-4)

| # | Test | Description |
|---|---|---|
| 8 | `test_move_right_updates_world_model` | Action `"right"`, moved=True → relative position shifts, visit count at new position = 1 |
| 9 | `test_failed_move_increments_current` | Action `"right"`, moved=False → position unchanged, visit count at current position increases |
| 10 | `test_consume_increments_current` | CONSUME → position unchanged, visit count increases |
| 11 | `test_world_model_uses_action_and_moved_only` | Mock `action_outcome` with different `new_position` — verify the world model ignores it and uses only `action` + `moved` |

#### Termination (Phase 5)

| # | Test | Description |
|---|---|---|
| 12 | `test_termination_on_zero_energy` | Energy reaches 0 → `terminated=True`, `termination_reason="energy_depleted"` |
| 13 | `test_no_termination_above_zero` | Energy > 0 → `terminated=False` |

#### Output Structure

| # | Test | Description |
|---|---|---|
| 14 | `test_returns_transition_result` | Output is `TransitionResult` |
| 15 | `test_new_state_is_agent_state_aw` | `new_state` is `AgentStateAW` with energy, memory, and world model |
| 16 | `test_trace_data_contains_position` | `trace_data["relative_position"]` present |
| 17 | `test_trace_data_contains_visit_count` | `trace_data["visit_count_at_current"]` present |

#### Worked Example D1: Forage-Explore Cycle

| # | Test | Description |
|---|---|---|
| 18 | `test_d1_step0_consume` | Step 0: CONSUME at (5,5), $r=0.8$ → energy $40 \to 47$, world model position unchanged |
| 19 | `test_d1_step1_move_right` | Step 1: RIGHT, moved → energy $47 \to 46$, relative position moves by $(+1, 0)$ |

#### Absolute Position Prohibition

| # | Test | Description |
|---|---|---|
| 20 | `test_no_new_position_access` | Create an `ActionOutcome` with a sentinel `new_position`. Verify the transition produces correct results without accessing it. (Use a custom mock that raises if `.new_position` is read.) |

---

## 6. Acceptance Criteria

- [ ] Energy update matches System A exactly
- [ ] Memory update matches System A exactly
- [ ] Dead reckoning updates relative position from `action` + `moved`
- [ ] World model increments visit count at the (relative) current position
- [ ] Termination triggers at energy $\leq 0$
- [ ] Trace data includes `relative_position` and `visit_count_at_current`
- [ ] `action_outcome.new_position` is **never accessed**
- [ ] Output is `TransitionResult` with `AgentStateAW` as `new_state`
- [ ] All 20 tests pass
