# WP-2.3 Implementation Brief -- System A Conformance

> **Updated:** This spec has been updated to reflect the final implementation.
> Key changes from the original spec:
> - `WorldDynamicsConfig` and `world_dynamics` field removed from
>   `SystemAConfig`. System config keys are `{"agent", "policy", "transition"}`.
> - Regeneration parameters now live in `BaseWorldConfig` (world section).
> - `handle_consume` uses `world.extract_resource()` instead of directly
>   importing and manipulating `Cell`/`CellType` from `axis.world.model`.
> - `ActionOutcome` uses `data={"consumed": True, "resource_consumed": delta}`
>   instead of `consumed=True, resource_consumed=delta`.

## Context

We are implementing the **modular architecture evolution** of the AXIS project. WP-2.1 extracted the world model into `axis/world/` and WP-2.2 implemented the action engine and dynamics.

This work package is **WP-2.3**. It restructures System A's internal components into the new `axis/systems/system_a/` package and creates a `SystemA` class that implements the `SystemInterface` protocol from WP-1.1. This is the **heaviest refactoring** in the entire migration: breaking apart the monolithic step pipeline into the two-phase contract.

### Predecessor State (After WP-2.2)

```
src/axis/
    sdk/                                    # Complete SDK contracts
    framework/
        config.py                           # FrameworkConfig, ExperimentConfig, OFAT helpers
    world/
        model.py                            # CellType, RegenerationMode, Cell, World (satisfies WorldView)
        factory.py                          # create_world()
        actions.py                          # ActionRegistry, movement/stay handlers
        dynamics.py                         # apply_regeneration()
    systems/system_a/
        __init__.py                         # Empty placeholder
```

System A's logic currently lives entirely in `axis_system_a/`:

| Module | Functions/Classes | New Location |
|--------|-------------------|-------------|
| `observation.py` | `build_observation()` | `axis/systems/system_a/sensor.py` |
| `drives.py` | `compute_hunger_drive()`, `HungerDriveOutput` | `axis/systems/system_a/drive.py` |
| `policy.py` | `select_action()`, `DecisionTrace` | `axis/systems/system_a/policy.py` |
| `transition.py` | `step()` (agent logic only) | `axis/systems/system_a/transition.py` |
| `memory.py` | `update_memory()` | `axis/systems/system_a/memory.py` |
| `types.py` | `AgentState`, `MemoryState`, `Observation`, etc. | `axis/systems/system_a/types.py` |
| `config.py` | `AgentConfig`, `PolicyConfig`, `TransitionConfig` | `axis/systems/system_a/config.py` |
| `runner.py:episode_step` | Orchestration chain | Split: `decide()` and `transition()` in `SystemA` |

### Architectural Decisions (Binding)

- **Q1**: Opaque `system.step()` -- framework never orchestrates sub-components. The `SystemA.decide()` and `SystemA.transition()` methods encapsulate all internal logic
- **Q2**: Framework-owned world mutation -- `decide()` returns action intent; framework applies it; `transition()` processes the outcome
- **Q14**: Observations are system-defined -- `SystemA.decide()` internally calls its own sensor
- **Q15**: Mandatory normalized vitality `[0, 1]` -- `SystemA.vitality()` returns `energy / max_energy`
- **Q16**: Both framework and system can terminate -- system checks `energy <= 0` in `transition()`

### The Two-Phase Step Decomposition

The v0.1.0 `episode_step()` runs this chain:

```
observation -> drive -> policy -> transition_step()
                                  (regen -> action -> new_obs -> energy -> memory -> termination)
```

In v0.2.0, this splits into:

```
Framework calls system.decide(world_view, agent_state, rng):
    1. sensor.observe(world_view, position)     [was in runner, now inside decide]
    2. drive.compute(agent_state, observation)   [same]
    3. policy.select(drive_output, obs, rng)     [same]
    4. Return DecideResult(action, decision_data)

Framework applies action to world:
    - apply_regeneration(world, regen_rate)
    - registry.apply(world, action, context)    -> ActionOutcome
    - new_observation via sensor (for system)

Framework calls system.transition(agent_state, action_outcome, new_observation):
    5. Energy update                            [was phases 4-6 of transition.step()]
    6. Memory update
    7. Termination check
    8. Return TransitionResult(new_state, trace_data, terminated)
```

**Key insight**: The v0.1.0 transition engine's phases 1-3 (regen, action application, new observation) move to the framework. Phases 4-6 (energy, memory, termination) stay in the system's `transition()` method.

### Reference Documents

- `docs/v0.2.0/architecture/evolution/architectural-vision-v0.2.0.md` -- Sections 4 (System SDK), 12 (Step Lifecycle)
- `docs/v0.2.0/architecture/evolution/modular-architecture-roadmap.md` -- WP-2.3 definition
- `docs/v0.2.0/specs/WP-1.1.md` -- SystemInterface, DecideResult, TransitionResult, PolicyResult
- `docs/v0.2.0/specs/WP-2.1.md` -- World extraction
- `docs/v0.2.0/specs/WP-2.2.md` -- ActionRegistry, apply_regeneration

---

## Objective

Create the `SystemA` class implementing `SystemInterface` and restructure all System A sub-components:

1. **`SystemAConfig`** -- typed Pydantic config model for System A
2. **`SystemA`** -- main class implementing `SystemInterface`
3. **`SystemASensor`** -- sensor implementing `SensorInterface`
4. **`SystemAHungerDrive`** -- drive implementing `DriveInterface`
5. **`SystemAPolicy`** -- policy implementing `PolicyInterface`
6. **`SystemATransition`** -- transition implementing `TransitionInterface`
7. **System A types** -- `AgentState`, `MemoryState`, `Observation`, etc.
8. **Consume action handler** -- registered with the `ActionRegistry`

---

## Scope

### 1. System A Types

**File**: `src/axis/systems/system_a/types.py`

Carry forward from `axis_system_a/types.py`:

```python
class CellObservation(BaseModel):
    """Per-cell sensory vector z_j = (b_j, r_j)."""
    model_config = ConfigDict(frozen=True)
    traversability: float = Field(..., ge=0, le=1)
    resource: float = Field(..., ge=0, le=1)

class Observation(BaseModel):
    """Von Neumann neighborhood observation (R^10)."""
    model_config = ConfigDict(frozen=True)
    current: CellObservation
    up: CellObservation
    down: CellObservation
    left: CellObservation
    right: CellObservation

    def to_vector(self) -> tuple[float, ...]: ...

class MemoryEntry(BaseModel):
    model_config = ConfigDict(frozen=True)
    timestep: int = Field(..., ge=0)
    observation: Observation

class MemoryState(BaseModel):
    model_config = ConfigDict(frozen=True)
    entries: tuple[MemoryEntry, ...] = Field(default_factory=tuple)
    capacity: int = Field(..., gt=0)

class AgentState(BaseModel):
    """System A agent state: energy + memory.
    Position is NOT part of agent state (world-owned).
    """
    model_config = ConfigDict(frozen=True)
    energy: float = Field(..., ge=0)
    memory_state: MemoryState

def clip_energy(energy: float, max_energy: float) -> float:
    return max(0.0, min(energy, max_energy))
```

These are functionally identical to the v0.1.0 types. They are **system-internal** -- the framework never sees them (it treats `agent_state` as `Any`).

### 2. System A Config

**File**: `src/axis/systems/system_a/config.py`

```python
from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentConfig(BaseModel):
    """Agent initialization parameters."""
    model_config = ConfigDict(frozen=True)

    initial_energy: float = Field(..., gt=0)
    max_energy: float = Field(..., gt=0)
    memory_capacity: int = Field(..., gt=0)

    @model_validator(mode="after")
    def check_energy_bounds(self) -> AgentConfig:
        if self.initial_energy > self.max_energy:
            raise ValueError("initial_energy must be <= max_energy")
        return self


class PolicyConfig(BaseModel):
    """Policy and action selection parameters."""
    model_config = ConfigDict(frozen=True)

    selection_mode: str  # "sample" or "argmax"
    temperature: float = Field(..., gt=0)
    stay_suppression: float = Field(..., ge=0)
    consume_weight: float = Field(..., gt=0)


class TransitionConfig(BaseModel):
    """Transition engine cost and energy parameters."""
    model_config = ConfigDict(frozen=True)

    move_cost: float = Field(..., gt=0)
    consume_cost: float = Field(..., gt=0)
    stay_cost: float = Field(..., ge=0)
    max_consume: float = Field(..., gt=0)
    energy_gain_factor: float = Field(..., ge=0)


class SystemAConfig(BaseModel):
    """Complete System A configuration.
    Parsed from the opaque `system: dict[str, Any]` in ExperimentConfig.
    """
    model_config = ConfigDict(frozen=True)
    agent: AgentConfig
    policy: PolicyConfig
    transition: TransitionConfig
```

**Design notes**:

- `PolicyConfig.selection_mode` is `str` (not enum) for simplicity. Values: `"sample"`, `"argmax"`
- `SystemAConfig` is parsed from the opaque `system: dict` in `ExperimentConfig` via `SystemAConfig(**system_dict)`
- The system config dict keys are `{"agent", "policy", "transition"}`

### 3. Sensor

**File**: `src/axis/systems/system_a/sensor.py`

```python
from axis.sdk.world_types import WorldView
from axis.sdk.position import Position
from axis.systems.system_a.types import CellObservation, Observation


class SystemASensor:
    """Von Neumann neighborhood sensor for System A.

    Satisfies SensorInterface. Produces a 10-dimensional observation
    from the world state around the agent's position.
    """

    def observe(self, world_view: WorldView, position: Position) -> Observation:
        """Construct observation from world view and position."""
        ...
```

**Design notes**:

- Functionally identical to `axis_system_a/observation.py:build_observation()`
- Wrapped in a class to satisfy `SensorInterface` protocol
- Reads `WorldView.get_cell(pos) -> CellView` to construct `CellObservation` values
- Mapping: `CellView.cell_type != "obstacle"` -> `traversability=1.0`, else `0.0`. `CellView.resource_value` -> `resource`
- Out-of-bounds positions -> `CellObservation(traversability=0.0, resource=0.0)`

### 4. Drive

**File**: `src/axis/systems/system_a/drive.py`

```python
from axis.systems.system_a.types import AgentState, HungerDriveOutput, Observation


class SystemAHungerDrive:
    """Hunger drive for System A.

    Satisfies DriveInterface. Computes drive activation and per-action
    contributions based on energy level and observation.
    """

    def __init__(self, *, consume_weight: float, stay_suppression: float, max_energy: float) -> None:
        self._consume_weight = consume_weight
        self._stay_suppression = stay_suppression
        self._max_energy = max_energy

    def compute(self, agent_state: AgentState, observation: Observation) -> HungerDriveOutput:
        """Compute hunger drive output."""
        ...
```

**Design notes**:

- `HungerDriveOutput` is defined in `types.py` (carry-forward from `axis_system_a/drives.py`)
- The constructor receives drive parameters (previously passed as function arguments each step)
- `max_energy` is needed for the activation formula `d_H = 1 - energy / max_energy`
- Functionally identical to `compute_hunger_drive()`, now as a class method

### 5. Policy

**File**: `src/axis/systems/system_a/policy.py`

```python
from axis.sdk.types import PolicyResult
from axis.systems.system_a.types import Observation

import numpy as np


class SystemAPolicy:
    """Softmax policy for System A.

    Satisfies PolicyInterface. Implements admissibility masking,
    softmax normalization, and stochastic/deterministic selection.
    """

    def __init__(self, *, temperature: float, selection_mode: str) -> None:
        self._temperature = temperature
        self._selection_mode = selection_mode

    def select(
        self,
        drive_outputs: HungerDriveOutput,
        observation: Observation,
        rng: np.random.Generator,
    ) -> PolicyResult:
        """Run the full policy pipeline: mask -> softmax -> select."""
        ...
```

**Design notes**:

- Returns `PolicyResult` (SDK type) with `action: str` and `policy_data: dict[str, Any]`
- `policy_data` carries the full decision trace: `raw_contributions`, `admissibility_mask`, `masked_contributions`, `probabilities`, `selected_action`, `temperature`, `selection_mode`
- Action names are strings (`"up"`, `"consume"`, etc.) instead of `Action` enums
- Action ordering convention for tuples: `(up, down, left, right, consume, stay)` -- same as v0.1.0 but indexed by name
- Functionally identical logic: admissibility mask -> softmax -> select

### 6. Transition

**File**: `src/axis/systems/system_a/transition.py`

```python
from axis.sdk.types import TransitionResult
from axis.sdk.world_types import ActionOutcome
from axis.systems.system_a.types import AgentState, Observation, clip_energy
from axis.systems.system_a.memory import update_memory


class SystemATransition:
    """Transition function for System A.

    Satisfies TransitionInterface. Processes the ActionOutcome from
    the framework and updates energy, memory, and termination status.

    This handles v0.1.0 phases 4-6 only:
    - Phase 4: Energy update
    - Phase 5: Memory update
    - Phase 6: Termination check
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
        agent_state: AgentState,
        action_outcome: ActionOutcome,
        observation: Observation,
    ) -> TransitionResult:
        """Process action outcome: energy, memory, termination.

        Returns:
            TransitionResult with new agent state and trace data.
        """
        # Phase 4: Energy update
        cost = self._get_action_cost(action_outcome.action)
        energy_gain = self._energy_gain_factor * action_outcome.data.get("resource_consumed", 0.0)
        new_energy = clip_energy(
            agent_state.energy - cost + energy_gain,
            self._max_energy,
        )

        # Phase 5: Memory update
        # Note: observation here is the POST-action observation
        new_memory = update_memory(agent_state.memory_state, observation, timestep=...)
        new_state = AgentState(energy=new_energy, memory_state=new_memory)

        # Phase 6: Termination check
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
        }

        return TransitionResult(
            new_state=new_state,
            trace_data=trace_data,
            terminated=terminated,
            termination_reason=termination_reason,
        )
```

**Design notes**:

- Only handles phases 4-6. Phases 1-3 (regen, action, new obs) are framework-owned
- `action_outcome.action` is a string -- use to determine cost type
- `action_outcome.data.get("resource_consumed", 0.0)` provides the delta for energy gain
- `trace_data` carries system-specific trace information (packed into `system_data` in `BaseStepTrace`)
- Returns `TransitionResult` (SDK type)
- **Timestep parameter**: The transition needs the timestep for memory entries. This is passed via the agent state or as an additional parameter. The cleanest approach is to include `timestep` as a field on `AgentState` or to have the `SystemA.transition()` method inject it. See design decision below.

**Timestep handling**: The `TransitionInterface` protocol signature is `transition(agent_state, action_outcome, observation)`. The timestep is not in the signature. Two options:

- **Option A**: Add `timestep: int` to `AgentState` (system-internal, opaque to framework)
- **Option B**: The framework passes timestep as part of a broader context

**Chosen: Option A** -- Include the `current_timestep` in `AgentState`. The framework increments it each step via the system's own `transition()` return. The system's `initialize_state()` sets `timestep=0`. This keeps the `TransitionInterface` signature clean and the timestep management system-internal.

### 7. Memory

**File**: `src/axis/systems/system_a/memory.py`

```python
from axis.systems.system_a.types import MemoryEntry, MemoryState, Observation


def update_memory(
    memory: MemoryState,
    observation: Observation,
    timestep: int,
) -> MemoryState:
    """Append observation as memory entry with FIFO overflow."""
    ...
```

Functionally identical to `axis_system_a/memory.py:update_memory()`.

### 8. Consume Action Handler

**File**: `src/axis/systems/system_a/actions.py`

```python
from typing import Any
from axis.sdk.world_types import ActionOutcome

def handle_consume(
    world: Any,
    *,
    context: dict[str, Any],
) -> ActionOutcome:
    """System A consume action handler.
    Extracts resource from the agent's current cell.
    context must contain {"max_consume": float}.
    """
    max_consume = context["max_consume"]
    pos = world.agent_position
    delta_r = world.extract_resource(pos, max_consume)

    return ActionOutcome(
        action="consume",
        moved=False,
        new_position=pos,
        data={"consumed": delta_r > 0, "resource_consumed": delta_r},
    )
```

**Design notes**:

- Uses `world.extract_resource()` protocol method instead of importing `Cell`/`CellType` from `axis.world.model`
- No longer has any import dependency on `axis.world.model`
- Returns `data` dict instead of `consumed`/`resource_consumed` fields
- Registered with the `ActionRegistry` during `SystemA` initialization

### 9. SystemA Class

**File**: `src/axis/systems/system_a/system.py`

```python
from typing import Any

import numpy as np

from axis.sdk.types import DecideResult, TransitionResult
from axis.sdk.world_types import WorldView
from axis.systems.system_a.config import SystemAConfig
from axis.systems.system_a.drive import SystemAHungerDrive
from axis.systems.system_a.policy import SystemAPolicy
from axis.systems.system_a.sensor import SystemASensor
from axis.systems.system_a.transition import SystemATransition
from axis.systems.system_a.types import AgentState, MemoryState


class SystemA:
    """System A: hunger-driven baseline agent.

    Implements SystemInterface. Encapsulates sensor, drive, policy,
    and transition as internal components.
    """

    def __init__(self, config: SystemAConfig) -> None:
        self._config = config
        self._sensor = SystemASensor()
        self._drive = SystemAHungerDrive(
            consume_weight=config.policy.consume_weight,
            stay_suppression=config.policy.stay_suppression,
            max_energy=config.agent.max_energy,
        )
        self._policy = SystemAPolicy(
            temperature=config.policy.temperature,
            selection_mode=config.policy.selection_mode,
        )
        self._transition = SystemATransition(
            max_energy=config.agent.max_energy,
            move_cost=config.transition.move_cost,
            consume_cost=config.transition.consume_cost,
            stay_cost=config.transition.stay_cost,
            energy_gain_factor=config.transition.energy_gain_factor,
        )

    def system_type(self) -> str:
        return "system_a"

    def action_space(self) -> tuple[str, ...]:
        return ("up", "down", "left", "right", "consume", "stay")

    def initialize_state(self, system_config: dict[str, Any]) -> AgentState:
        """Create initial agent state from system config dict."""
        config = SystemAConfig(**system_config)
        return AgentState(
            energy=config.agent.initial_energy,
            memory_state=MemoryState(
                entries=(),
                capacity=config.agent.memory_capacity,
            ),
        )

    def vitality(self, agent_state: Any) -> float:
        """Normalized vitality: energy / max_energy."""
        return agent_state.energy / self._config.agent.max_energy

    def decide(
        self,
        world_view: WorldView,
        agent_state: Any,
        rng: np.random.Generator,
    ) -> DecideResult:
        """Phase 1: sensor -> drive -> policy -> action intent."""
        # 1. Observe
        observation = self._sensor.observe(world_view, world_view.agent_position)

        # 2. Drive
        drive_output = self._drive.compute(agent_state, observation)

        # 3. Policy
        policy_result = self._policy.select(drive_output, observation, rng)

        # 4. Assemble decision data (for system_data in trace)
        decision_data = {
            "observation": observation.model_dump(),
            "drive": {
                "activation": drive_output.activation,
                "action_contributions": drive_output.action_contributions,
            },
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
        """Phase 2: energy update, memory update, termination check."""
        return self._transition.transition(
            agent_state, action_outcome, new_observation,
        )

    @property
    def config(self) -> SystemAConfig:
        """Access the parsed system config."""
        return self._config
```

**Design notes**:

- `decide()` encapsulates the full sensor -> drive -> policy chain
- `transition()` delegates to `SystemATransition`
- `decision_data` captures the full internal pipeline trace for visualization/debugging
- `initialize_state()` accepts the raw `system_config: dict` and parses it into `SystemAConfig`
- The constructor also accepts `SystemAConfig` directly for convenience
- `vitality()` is `energy / max_energy` -- the only metric the framework reads

### 10. Package Exports

**File**: `src/axis/systems/system_a/__init__.py`

```python
"""System A -- hunger-driven baseline agent."""

from axis.systems.system_a.actions import handle_consume
from axis.systems.system_a.config import SystemAConfig
from axis.systems.system_a.system import SystemA

__all__ = [
    "SystemA",
    "SystemAConfig",
    "handle_consume",
]
```

---

## Out of Scope

Do **not** implement any of the following in WP-2.3:

- The framework episode runner (WP-3.2) -- the `SystemA` class is tested in isolation
- Behavioral equivalence tests against `axis_system_a` (WP-2.4)
- System registry (WP-3.1)
- Any modifications to `axis_system_a` code
- Any modifications to `axis.sdk` or `axis.framework`
- Visualization adapter (WP-4.3)

---

## Architectural Constraints

### 1. SystemInterface Conformance

`SystemA` must satisfy `isinstance(system, SystemInterface)` at runtime. All method signatures must match the protocol exactly.

### 2. Sub-Interface Conformance

Each sub-component must satisfy its corresponding protocol:

| Component | Protocol |
|-----------|----------|
| `SystemASensor` | `SensorInterface` |
| `SystemAHungerDrive` | `DriveInterface` |
| `SystemAPolicy` | `PolicyInterface` |
| `SystemATransition` | `TransitionInterface` |

### 3. No Framework Dependencies

`axis.systems.system_a` imports from:
- `axis.sdk` (interfaces, types, position, world_types, actions)

It does **not** import from `axis.world` or `axis.framework`.

### 4. Opaque Agent State

The framework treats `AgentState` as `Any`. Only System A code (sensor, drive, policy, transition) knows its structure. The framework passes it between `decide()` and `transition()` without inspection.

### 5. Action String Convention

System A's action order: `("up", "down", "left", "right", "consume", "stay")`. All internal 6-tuples (contributions, masks, probabilities) use this ordering.

### 6. Consume Handler Registration

System A's `handle_consume` function is exported so the framework episode runner can register it:

```python
registry = create_action_registry()
registry.register("consume", handle_consume)
```

This registration happens in the framework layer (WP-3.2), not inside System A itself.

---

## Expected File Structure

After WP-2.3, these files are **new or modified**:

```
src/axis/systems/system_a/__init__.py       # MODIFIED (exports added)
src/axis/systems/system_a/types.py          # NEW (AgentState, Observation, MemoryState, etc.)
src/axis/systems/system_a/config.py         # NEW (SystemAConfig, AgentConfig, PolicyConfig, etc.)
src/axis/systems/system_a/sensor.py         # NEW (SystemASensor)
src/axis/systems/system_a/drive.py          # NEW (SystemAHungerDrive, HungerDriveOutput)
src/axis/systems/system_a/policy.py         # NEW (SystemAPolicy)
src/axis/systems/system_a/transition.py     # NEW (SystemATransition)
src/axis/systems/system_a/memory.py         # NEW (update_memory)
src/axis/systems/system_a/actions.py        # NEW (handle_consume)
src/axis/systems/system_a/system.py         # NEW (SystemA)
tests/v02/systems/system_a/test_system_a.py # NEW (verification tests)
tests/v02/test_scaffold.py                  # MODIFIED (axis.systems.system_a no longer empty)
```

Unchanged:

```
src/axis/sdk/                               # UNCHANGED
src/axis/framework/                         # UNCHANGED
src/axis/world/                             # UNCHANGED (from WP-2.1/2.2)
src/axis_system_a/                          # UNCHANGED
```

---

## Testing Requirements

### System A verification tests (`tests/v02/systems/system_a/test_system_a.py`)

Must include:

1. **SystemAConfig parsing**:
   - Constructs from a valid dict (matching the test builder's format)
   - Validates energy bounds (initial <= max)
   - All sub-configs accessible

2. **SystemA construction**:
   - `SystemA(config)` constructs successfully
   - `system_type()` returns `"system_a"`
   - `action_space()` returns `("up", "down", "left", "right", "consume", "stay")`

3. **SystemInterface conformance**:
   - `isinstance(system, SystemInterface)` is `True`

4. **Sub-interface conformance**:
   - `isinstance(sensor, SensorInterface)` is `True`
   - `isinstance(drive, DriveInterface)` is `True`
   - `isinstance(policy, PolicyInterface)` is `True`
   - `isinstance(transition, TransitionInterface)` is `True`

5. **initialize_state**:
   - Returns `AgentState` with correct initial energy and empty memory
   - Memory capacity matches config

6. **vitality**:
   - `vitality(state_at_full_energy) == 1.0`
   - `vitality(state_at_half_energy) == 0.5`
   - `vitality(state_at_zero_energy) == 0.0`

7. **Sensor**:
   - On a 5x5 grid, agent at center: observation has 5 `CellObservation` fields
   - Obstacle neighbor: `traversability=0.0`
   - Resource neighbor: `resource > 0`
   - Out of bounds (agent at edge): `traversability=0.0, resource=0.0`

8. **Drive**:
   - High energy (near max): low activation, low contributions
   - Low energy: high activation, contributions proportional to nearby resources
   - Stay contribution is always negative (suppressed)

9. **Policy**:
   - Returns `PolicyResult` with `action` as string
   - Admissibility masking: obstacle direction gets probability 0
   - Deterministic (`argmax` mode): same inputs produce same action
   - Stochastic (`sample` mode): uses rng, reproducible with same seed

10. **Transition**:
    - Energy decreases by move cost on movement
    - Energy increases by `energy_gain_factor * resource_consumed` on consume
    - Energy clipped to [0, max_energy]
    - Memory is updated with new observation
    - Terminates when energy <= 0

11. **Consume handler**:
    - On resource cell: extracts resource, returns `consumed=True`, `resource_consumed > 0`
    - On empty cell: `consumed=False`, `resource_consumed=0.0`
    - Cell updated in world after consume

12. **decide() integration**:
    - Given a world and agent state, returns `DecideResult` with valid action
    - `decision_data` contains observation, drive, and policy data

13. **transition() integration**:
    - Given an `ActionOutcome`, returns `TransitionResult` with new state
    - `trace_data` contains energy and memory deltas

14. **Import verification**:
    - `from axis.systems.system_a import SystemA, SystemAConfig, handle_consume` succeeds

### Test infrastructure updates

- Add a `SystemAConfigBuilder` or use the existing `SystemAConfigBuilder` from tests
- The existing `SystemAConfigBuilder` in `tests/v02/builders/system_config_builder.py` produces a dict matching the `SystemAConfig` structure -- verify this

### Existing test suite

All existing tests must still pass.

---

## Implementation Style

- Python 3.11+
- Frozen Pydantic models for all value types and configs
- Plain classes for components (sensor, drive, policy, transition, system)
- `typing.Protocol` conformance (structural, no inheritance)
- Clear docstrings
- No metaprogramming
- Direct extraction with minimal adaptation

---

## Expected Deliverable

1. System A types at `src/axis/systems/system_a/types.py`
2. System A config at `src/axis/systems/system_a/config.py`
3. Sensor at `src/axis/systems/system_a/sensor.py`
4. Drive at `src/axis/systems/system_a/drive.py`
5. Policy at `src/axis/systems/system_a/policy.py`
6. Transition at `src/axis/systems/system_a/transition.py`
7. Memory at `src/axis/systems/system_a/memory.py`
8. Consume handler at `src/axis/systems/system_a/actions.py`
9. SystemA class at `src/axis/systems/system_a/system.py`
10. Updated `src/axis/systems/system_a/__init__.py` with exports
11. Verification tests at `tests/v02/systems/system_a/test_system_a.py`
12. Updated `tests/v02/test_scaffold.py`
13. Confirmation that all existing tests still pass

---

## Important Final Constraint

This is the **most critical WP** in the migration. It transforms the monolithic `axis_system_a` pipeline into the modular two-phase contract. The implementation must be functionally identical to the legacy code -- same mathematical formulas, same conditional logic, same edge cases.

The key decomposition is:

| v0.1.0 | v0.2.0 |
|--------|--------|
| `episode_step()` orchestrates everything | Framework orchestrates; system owns `decide()` and `transition()` |
| `transition.step()` phases 1-6 | Phases 1-3 → framework; Phases 4-6 → `SystemATransition` |
| `build_observation()` called by runner | Called inside `SystemA.decide()` |
| `compute_hunger_drive()` called by runner | Called inside `SystemA.decide()` |
| `select_action()` called by runner | Called inside `SystemA.decide()` |
| `_apply_consume()` in transition.py | `handle_consume()` registered with framework |

If any sub-component doesn't map cleanly, revisit the interface design before forcing a fit.
