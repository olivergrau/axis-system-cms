# WP-10: System Orchestrator + Registration

## Metadata
- Work Package: WP-10
- Title: System Orchestrator + Framework Registration
- System: System A+W
- Source Files: `src/axis/systems/system_aw/system.py`, `src/axis/systems/system_aw/__init__.py`, `src/axis/framework/registry.py`
- Test File: `tests/systems/system_aw/test_system_aw.py`, `tests/systems/system_aw/test_pipeline.py`
- Model Reference: `01_System A+W Model.md`, Sections 9 (Execution Cycle), 3 (Formal Definition)
- Dependencies: WP-1 through WP-9 (all prior work packages)

---

## 1. Objective

Wire all System A+W components into a single `SystemAW` class that implements the framework's `SystemInterface` protocol, and register it as `"system_aw"` in the system registry. After this WP, the system is runnable end-to-end via:

```bash
axis run experiments/configs/system-aw-baseline.yaml
```

---

## 2. Design

### 2.1 Execution Cycle Mapping

Model Section 9 defines the execution cycle. Here is the mapping to `SystemInterface` methods:

| Step | Model | Method | Details |
|---|---|---|---|
| 1 | Perception | `observe()` + inside `decide()` | Sensor builds observation |
| 2 | Drive evaluation | inside `decide()` | Hunger + curiosity drives computed |
| 3 | Drive arbitration | inside `decide()` | Dynamic weights computed |
| 4 | Action modulation | inside `decide()` | Score combination |
| 5 | Admissibility masking | inside `decide()` | Policy handles this |
| 6 | Action selection | inside `decide()` | Policy selects action |
| — | *Action execution* | *Framework* | Framework applies action to world |
| 7 | State transition | `transition()` | Energy + memory + world model |
| 8 | Termination check | `transition()` | Energy $\leq 0$ |

### 2.2 Component Wiring

```
SystemAW
├── _sensor: SystemAWSensor               (WP-3)
├── _hunger_drive: SystemAWHungerDrive     (WP-5)
├── _curiosity_drive: SystemAWCuriosityDrive (WP-6)
├── _policy: SystemAWPolicy                (WP-8)
├── _transition: SystemAWTransition        (WP-9)
└── _config: SystemAWConfig                (WP-1)
```

The arbitration functions (WP-7) are called as pure functions within `decide()` — they don't need to be stored as a component.

### 2.3 SystemInterface Methods

| Method | Signature | Returns |
|---|---|---|
| `system_type()` | `() -> str` | `"system_aw"` |
| `action_space()` | `() -> tuple[str, ...]` | `("up", "down", "left", "right", "consume", "stay")` |
| `initialize_state()` | `() -> AgentStateAW` | Initial state with energy, empty memory, fresh world model |
| `vitality(state)` | `(AgentStateAW) -> float` | `energy / max_energy` |
| `decide(world_view, state, rng)` | `(WorldView, AgentStateAW, Generator) -> DecideResult` | Steps 1-6 of execution cycle |
| `transition(state, outcome, obs)` | `(AgentStateAW, ActionOutcome, Observation) -> TransitionResult` | Steps 7-8 of execution cycle |
| `observe(world_view, position)` | `(WorldView, Position) -> Observation` | Sensor observation |
| `action_handlers()` | `() -> dict[str, Any]` | `{"consume": handle_consume}` |
| `action_context()` | `() -> dict[str, Any]` | `{"max_consume": ...}` |

---

## 3. Specification

### 3.1 SystemAW Class

```python
"""System A+W -- dual-drive agent with curiosity and world model."""

from __future__ import annotations

from typing import Any

import numpy as np

from axis.sdk.types import DecideResult, TransitionResult
from axis.sdk.world_types import WorldView
from axis.systems.system_aw.config import SystemAWConfig
from axis.systems.system_aw.drive_arbitration import (
    compute_action_scores,
    compute_drive_weights,
)
from axis.systems.system_aw.drive_curiosity import SystemAWCuriosityDrive
from axis.systems.system_aw.drive_hunger import SystemAWHungerDrive
from axis.systems.system_aw.policy import SystemAWPolicy
from axis.systems.system_aw.sensor import SystemAWSensor
from axis.systems.system_aw.transition import SystemAWTransition
from axis.systems.system_aw.types import AgentStateAW
from axis.systems.system_aw.world_model import create_world_model
from axis.systems.system_a.types import MemoryState


class SystemAW:
    """System A+W: dual-drive agent with curiosity and world model.

    Implements SystemInterface. Extends System A with:
    - A curiosity drive (novelty-seeking)
    - A spatial world model (visit-count map via dead reckoning)
    - Dynamic drive arbitration (hunger gates curiosity)
    """

    def __init__(self, config: SystemAWConfig) -> None:
        self._config = config
        self._sensor = SystemAWSensor()
        self._hunger_drive = SystemAWHungerDrive(
            consume_weight=config.policy.consume_weight,
            stay_suppression=config.policy.stay_suppression,
            max_energy=config.agent.max_energy,
        )
        self._curiosity_drive = SystemAWCuriosityDrive(
            base_curiosity=config.curiosity.base_curiosity,
            spatial_sensory_balance=config.curiosity.spatial_sensory_balance,
            explore_suppression=config.curiosity.explore_suppression,
        )
        self._policy = SystemAWPolicy(
            temperature=config.policy.temperature,
            selection_mode=config.policy.selection_mode,
        )
        self._transition = SystemAWTransition(
            max_energy=config.agent.max_energy,
            move_cost=config.transition.move_cost,
            consume_cost=config.transition.consume_cost,
            stay_cost=config.transition.stay_cost,
            energy_gain_factor=config.transition.energy_gain_factor,
        )

    def system_type(self) -> str:
        return "system_aw"

    def action_space(self) -> tuple[str, ...]:
        return ("up", "down", "left", "right", "consume", "stay")

    def initialize_state(self) -> AgentStateAW:
        return AgentStateAW(
            energy=self._config.agent.initial_energy,
            memory_state=MemoryState(
                entries=(),
                capacity=self._config.agent.memory_capacity,
            ),
            world_model=create_world_model(),
        )

    def vitality(self, agent_state: Any) -> float:
        return agent_state.energy / self._config.agent.max_energy

    def decide(
        self,
        world_view: Any,
        agent_state: Any,
        rng: np.random.Generator,
    ) -> DecideResult:
        """Execution cycle steps 1-6: perceive, evaluate, arbitrate, select."""

        # Step 1: Perception
        observation = self._sensor.observe(world_view, world_view.agent_position)

        # Step 2: Drive evaluation
        hunger_output = self._hunger_drive.compute(agent_state, observation)
        curiosity_output = self._curiosity_drive.compute(
            observation, agent_state.memory_state, agent_state.world_model,
        )

        # Step 3: Drive arbitration
        weights = compute_drive_weights(
            hunger_output.activation, self._config.arbitration,
        )

        # Step 4: Action modulation (score combination)
        scores = compute_action_scores(hunger_output, curiosity_output, weights)

        # Steps 5-6: Admissibility masking + action selection
        policy_result = self._policy.select(scores, observation, rng)

        # Assemble decision data for trace
        decision_data = {
            "observation": observation.model_dump(),
            "hunger_drive": {
                "activation": hunger_output.activation,
                "action_contributions": hunger_output.action_contributions,
            },
            "curiosity_drive": {
                "activation": curiosity_output.activation,
                "spatial_novelty": curiosity_output.spatial_novelty,
                "sensory_novelty": curiosity_output.sensory_novelty,
                "composite_novelty": curiosity_output.composite_novelty,
                "action_contributions": curiosity_output.action_contributions,
            },
            "arbitration": {
                "hunger_weight": weights.hunger_weight,
                "curiosity_weight": weights.curiosity_weight,
            },
            "combined_scores": scores,
            "policy": policy_result.policy_data,
        }

        return DecideResult(
            action=policy_result.action,
            decision_data=decision_data,
        )

    def transition(
        self,
        agent_state: Any,
        action_outcome: Any,
        new_observation: Any,
    ) -> TransitionResult:
        """Execution cycle steps 7-8: state transition + termination."""
        return self._transition.transition(
            agent_state, action_outcome, new_observation,
        )

    def action_handlers(self) -> dict[str, Any]:
        from axis.systems.system_aw.actions import handle_consume
        return {"consume": handle_consume}

    def observe(self, world_view: Any, position: Any) -> Any:
        return self._sensor.observe(world_view, position)

    def action_context(self) -> dict[str, Any]:
        return {"max_consume": self._config.transition.max_consume}

    @property
    def config(self) -> SystemAWConfig:
        return self._config
```

### 3.2 Package Exports (`__init__.py`)

```python
"""System A+W -- dual-drive agent with curiosity and world model."""

from axis.systems.system_aw.config import SystemAWConfig
from axis.systems.system_aw.system import SystemAW

__all__ = [
    "SystemAW",
    "SystemAWConfig",
]
```

### 3.3 Framework Registration (`registry.py`)

Add to `src/axis/framework/registry.py`, following the existing pattern:

```python
def _system_aw_factory(system_config: dict[str, Any]) -> SystemInterface:
    """Factory for System A+W."""
    from axis.systems.system_aw import SystemAW, SystemAWConfig

    config = SystemAWConfig(**system_config)
    return SystemAW(config)

# Add to auto-registration block:
register_system("system_aw", _system_aw_factory)
```

### 3.4 Decision Data Structure

The `decision_data` dict in `DecideResult` contains the full decision pipeline trace, structured for logging and visualization:

```
decision_data
├── observation: {...}              # 10-float sensor output
├── hunger_drive
│   ├── activation: float           # d_H
│   └── action_contributions: (6,)  # φ_H per action
├── curiosity_drive
│   ├── activation: float           # d_C
│   ├── spatial_novelty: (4,)       # ν^spatial per direction
│   ├── sensory_novelty: (4,)       # ν^sensory per direction
│   ├── composite_novelty: (4,)     # ν_dir per direction
│   └── action_contributions: (6,)  # φ_C per action
├── arbitration
│   ├── hunger_weight: float        # w_H
│   └── curiosity_weight: float     # w_C
├── combined_scores: (6,)           # ψ(a) per action
└── policy
    ├── raw_scores: (6,)
    ├── admissibility_mask: (6,)
    ├── masked_scores: (6,)
    ├── probabilities: (6,)
    ├── selected_action: str
    ├── temperature: float
    └── selection_mode: str
```

This structure is significantly richer than System A's decision data and enables the visualization adapter (WP-12) to render curiosity-specific panels.

---

## 4. Test Plan

### File: `tests/systems/system_aw/test_system_aw.py`

#### Construction and Interface

| # | Test | Description |
|---|---|---|
| 1 | `test_system_type` | `system.system_type() == "system_aw"` |
| 2 | `test_action_space` | Returns 6-element tuple in correct order |
| 3 | `test_initialize_state` | Returns `AgentStateAW` with correct energy, empty memory, world model at origin |
| 4 | `test_vitality` | `vitality(state)` = energy / max_energy |
| 5 | `test_action_handlers` | Returns dict with `"consume"` key |
| 6 | `test_action_context` | Returns dict with `"max_consume"` key |
| 7 | `test_observe` | Produces valid `Observation` from a world view |

#### Registration

| # | Test | Description |
|---|---|---|
| 8 | `test_registry_create_system` | `create_system("system_aw", config_dict)` returns a `SystemAW` instance |
| 9 | `test_registry_system_type_listed` | `"system_aw"` in `registered_system_types()` |
| 10 | `test_registry_default_curiosity` | Config with no curiosity/arbitration keys → system uses defaults |

#### Decide

| # | Test | Description |
|---|---|---|
| 11 | `test_decide_returns_decide_result` | Output is `DecideResult` with action and decision_data |
| 12 | `test_decide_action_in_action_space` | Selected action is one of the 6 valid actions |
| 13 | `test_decide_decision_data_structure` | `decision_data` contains all expected keys: observation, hunger_drive, curiosity_drive, arbitration, combined_scores, policy |
| 14 | `test_decide_curiosity_data_present` | `decision_data["curiosity_drive"]` has spatial_novelty, sensory_novelty, composite_novelty, activation, action_contributions |

#### Transition

| # | Test | Description |
|---|---|---|
| 15 | `test_transition_returns_transition_result` | Output is `TransitionResult` |
| 16 | `test_transition_new_state_is_aw` | `new_state` is `AgentStateAW` |
| 17 | `test_transition_updates_world_model` | After a move, world model relative position changes |
| 18 | `test_transition_updates_energy` | Energy changes according to action cost |

### File: `tests/systems/system_aw/test_pipeline.py`

End-to-end pipeline tests that run multiple steps through the full system.

| # | Test | Description |
|---|---|---|
| 19 | `test_single_step_pipeline` | `decide()` → framework applies action → `transition()` → verify state consistency |
| 20 | `test_multi_step_episode` | Run 10 steps with a simple world. Verify: energy decreases, world model grows, memory fills, no crashes. |
| 21 | `test_episode_until_termination` | Run until energy depleted → `terminated=True` eventually |
| 22 | `test_curiosity_disabled_matches_system_a` | With `base_curiosity=0`, run same scenario through System A and System A+W → verify same action probabilities (this is a preview of WP-11 reduction tests) |
| 23 | `test_well_fed_prefers_exploration` | With $e = E_{\max}$, no resources nearby, all neighbors unvisited: movement probability > consume probability |
| 24 | `test_starving_prefers_consume` | With $e \approx 0$, resource present: consume probability dominates |
| 25 | `test_world_model_consistent_across_steps` | After 5 steps, world model visit counts sum = 6 (1 initial + 5 step increments) |

#### Framework Integration

| # | Test | Description |
|---|---|---|
| 26 | `test_framework_runner_integration` | Use `RunExecutor` from `axis.framework.run` to execute a full run with `system_type="system_aw"` and a minimal config. Verify `RunResult` has expected structure. |

---

## 5. Acceptance Criteria

- [ ] `create_system("system_aw", config_dict)` returns a working `SystemAW` instance
- [ ] `"system_aw"` appears in `registered_system_types()`
- [ ] `initialize_state()` returns `AgentStateAW` with world model at origin `(0, 0)` with visit count 1
- [ ] `decide()` executes the full 6-step pipeline: sensor → hunger → curiosity → arbitration → scores → policy
- [ ] `decide()` produces `DecideResult` with rich `decision_data` (both drives, arbitration weights, novelty signals)
- [ ] `transition()` updates all three state components (energy, memory, world model)
- [ ] `transition()` never accesses absolute position (enforced by WP-9)
- [ ] Full episode runs without errors through the framework
- [ ] Well-fed agent prefers exploration; starving agent prefers consumption
- [ ] World model visit counts are consistent across steps
- [ ] All 26 tests pass
