# Tutorial: Building a System from Scratch

**AXIS Experimentation Framework v0.2.0**

> **Prerequisites:** Python 3.11+, the AXIS framework installed (`pip install -e .`),
> familiarity with Pydantic v2 and Python protocols. You should already
> understand how worlds work (see [Building a World](building-a-world.md)).
>
> **What we build:** A complete energy-driven foraging agent (System A)
> with sensor, drive, policy, transition logic, a custom action, an
> observation buffer, and a visualization adapter.
>
> **Related:** [System Developer Manual](../manuals/system-dev-manual.md) |
> [World Developer Manual](../manuals/world-dev-manual.md) |
> [Building a World Tutorial](building-a-world.md)

---

## What is a System?

A system in AXIS is the agent's brain. It encapsulates everything
the agent does: perception, motivation, action selection, and state
update. The framework calls into the system at two points per step:

1. **Decide** -- the system observes the world and chooses an action.
2. **Transition** -- after the framework applies the action, the
   system updates its internal state.

The framework never inspects the agent's internal state. It only asks
one thing: `vitality()` -- a normalized health metric in [0, 1].
Everything else is opaque.

We will build System A (the energy-driven forager) step by step,
starting with the bare minimum and layering on components until we
have a complete, production-quality implementation.

> **Note: System Construction Kit.** This tutorial builds every
> component from scratch to teach the concepts. In practice, many
> of these components are available as tested, reusable building blocks
> in the **System Construction Kit** (`src/axis/systems/construction_kit/`).
> See the [Construction Kit Reference](../construction-kit/index.md)
> for a full catalog of available components.
> The actual System A implementation composes kit components
> (`VonNeumannSensor`, `HungerDrive`, `SoftmaxPolicy`,
> `ObservationBuffer`, `handle_consume`, shared config types) instead
> of implementing them inline. See the
> [System Developer Manual](../manuals/system-dev-manual.md) Section 10a
> for details on using the kit.

---

## Chapter 1: Understand the Contract

Before writing any code, let's understand what the framework expects.

### 1.1 The `SystemInterface` protocol

Your system must satisfy this protocol (from `src/axis/sdk/interfaces.py`):

```python
@runtime_checkable
class SystemInterface(Protocol):
    def system_type(self) -> str: ...
    def action_space(self) -> tuple[str, ...]: ...
    def initialize_state(self) -> Any: ...
    def vitality(self, agent_state: Any) -> float: ...
    def decide(self, world_view: Any, agent_state: Any,
               rng: np.random.Generator) -> DecideResult: ...
    def transition(self, agent_state: Any, action_outcome: Any,
                   new_observation: Any) -> TransitionResult: ...
    def observe(self, world_view: Any, position: Any) -> Any: ...
    def action_handlers(self) -> dict[str, Any]: ...
    def action_context(self) -> dict[str, Any]: ...
```

The return type `Any` for state and observation is deliberate -- the
framework passes these values through without inspection.

### 1.2 The two-phase step

Here is exactly when each method is called during one step:

```
Step begins
  |
  +--> system.decide(world_view, agent_state, rng)  --> DecideResult
  |      (system reads the world, chooses an action)
  |
  +--> world.tick()
  |      (framework runs regeneration)
  |
  +--> registry.apply(world, action, context)  --> ActionOutcome
  |      (framework applies the action: movement or custom handler)
  |
  +--> system.observe(world_view, position)  --> new_observation
  |      (system reads the post-action world)
  |
  +--> system.transition(agent_state, outcome, observation)  --> TransitionResult
         (system updates its state, checks for death)
```

Critical: `decide()` sees the **pre-regeneration** world. The action
is applied to the **post-regeneration** world. `transition()` sees
the **post-action** world.

### 1.3 SDK result types

Two frozen Pydantic models carry data between the system and framework:

```python
class DecideResult(BaseModel):
    action: str                      # the chosen action name
    decision_data: dict[str, Any]    # logged to trace for replay

class TransitionResult(BaseModel):
    new_state: Any                   # updated agent state (opaque)
    trace_data: dict[str, Any]       # logged to trace for replay
    terminated: bool                 # True to end the episode
    termination_reason: str | None   # e.g. "energy_depleted"
```

---

## Chapter 2: Project Layout

Create the package structure:

```
src/axis/systems/system_a/
    __init__.py
    types.py           # AgentState, Observation, CellObservation, etc.
    config.py          # SystemAConfig with nested sub-configs
    sensor.py          # SystemASensor -- world perception
    drive.py           # SystemAHungerDrive -- motivation
    policy.py          # SystemAPolicy -- action selection
    transition.py      # SystemATransition -- state update
    actions.py         # handle_consume -- custom action handler
    observation_buffer.py  # FIFO ring buffer update
    system.py          # SystemA -- the facade that implements SystemInterface
    visualization.py   # SystemAVisualizationAdapter -- replay overlays
```

This decomposition is entirely optional. You could put everything in
one file. But separating concerns makes each component independently
testable and swappable.

The pipeline inside the system is:
**Sensor -> Drive -> Policy -> (framework applies action) -> Transition**

---

## Chapter 3: Agent State and Domain Types

The first thing to define is what the agent remembers between steps.

### 3.1 Cell observation

When the agent senses a cell, it reads two signals:

```python
# src/axis/systems/system_a/types.py
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CellObservation(BaseModel):
    """What the agent perceives about one cell."""
    model_config = ConfigDict(frozen=True)

    traversability: float   # 1.0 = traversable, 0.0 = blocked/out-of-bounds
    resource: float         # [0.0, 1.0] -- how much resource is here
```

### 3.2 Observation

The full observation is the current cell plus four cardinal neighbors
(Von Neumann neighborhood):

```python
class Observation(BaseModel):
    """The agent's sensory input for one timestep."""
    model_config = ConfigDict(frozen=True)

    current: CellObservation
    up: CellObservation
    down: CellObservation
    left: CellObservation
    right: CellObservation

    def to_vector(self) -> tuple[float, ...]:
        """Flatten to a 10-dimensional tuple."""
        return (
            self.current.traversability, self.current.resource,
            self.up.traversability, self.up.resource,
            self.down.traversability, self.down.resource,
            self.left.traversability, self.left.resource,
            self.right.traversability, self.right.resource,
        )

    @property
    def dimension(self) -> int:
        return 10
```

The `to_vector()` method gives a flat representation for any
downstream processing that prefers arrays.

### 3.3 Drive output

The hunger drive produces an activation level and a score for each
action:

```python
class HungerDriveOutput(BaseModel):
    """Output of the hunger drive."""
    model_config = ConfigDict(frozen=True)

    activation: float   # d_H in [0, 1] -- how hungry the agent is
    action_contributions: tuple[float, float, float, float, float, float]
    # One score per action: (up, down, left, right, consume, stay)
```

The tuple has six entries matching the action space ordering. This
structured output flows into the policy for action selection.

### 3.4 Observation buffer

The agent has short-term memory: a bounded buffer of recent
observations.

```python
class BufferEntry(BaseModel):
    """One record in the observation buffer."""
    model_config = ConfigDict(frozen=True)

    timestep: int = Field(..., ge=0)
    observation: Observation


class ObservationBuffer(BaseModel):
    """Bounded FIFO buffer of recent observations."""
    model_config = ConfigDict(frozen=True)

    entries: tuple[BufferEntry, ...] = Field(default_factory=tuple)
    capacity: int = Field(..., gt=0)
```

Using `tuple` rather than `list` is deliberate -- it keeps the model
frozen. The buffer update function (Chapter 8) creates a new tuple
each time.

### 3.5 Agent state

Everything the agent carries between steps:

```python
class AgentState(BaseModel):
    """System A agent state."""
    model_config = ConfigDict(frozen=True)

    energy: float = Field(..., ge=0)
    observation_buffer: ObservationBuffer
```

Two fields:

- **`energy`** -- the agent's fuel. Movement costs energy, consuming
  resources gains energy. Episode ends at zero.
- **`observation_buffer`** -- recent observations for potential use
  by drives or extended systems.

Note what is **absent**: position. The agent does not know where it is.
Position belongs to the world. The agent observes its surroundings
through the sensor, but never has direct coordinates.

### 3.6 Utility

```python
def clip_energy(energy: float, max_energy: float) -> float:
    """Clamp energy to [0, max_energy]."""
    return max(0.0, min(energy, max_energy))
```

### 3.7 Test the types

```python
# tests/systems/system_a/test_types.py
import pytest
from axis.systems.system_a.types import (
    AgentState, CellObservation, Observation, ObservationBuffer,
)


def test_observation_dimension():
    obs = Observation(
        current=CellObservation(traversability=1.0, resource=0.5),
        up=CellObservation(traversability=1.0, resource=0.0),
        down=CellObservation(traversability=0.0, resource=0.0),
        left=CellObservation(traversability=1.0, resource=0.3),
        right=CellObservation(traversability=1.0, resource=0.0),
    )
    assert obs.dimension == 10
    assert len(obs.to_vector()) == 10


def test_agent_state_is_frozen():
    buf = ObservationBuffer(capacity=5)
    state = AgentState(energy=50.0, observation_buffer=buf)
    with pytest.raises(Exception):
        state.energy = 30.0


def test_empty_buffer():
    buf = ObservationBuffer(capacity=3)
    assert len(buf.entries) == 0
```

---

## Chapter 4: Configuration

The system's parameters are organized into three groups, matching the
three internal concerns.

### 4.1 Config hierarchy

```python
# src/axis/systems/system_a/config.py
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentConfig(BaseModel):
    """Agent construction parameters."""
    model_config = ConfigDict(frozen=True)

    initial_energy: float = Field(..., gt=0)
    max_energy: float = Field(..., gt=0)
    buffer_capacity: int = Field(..., gt=0)

    @model_validator(mode="after")
    def _validate_energy(self) -> AgentConfig:
        if self.initial_energy > self.max_energy:
            raise ValueError("initial_energy must be <= max_energy")
        return self


class PolicyConfig(BaseModel):
    """Action selection parameters."""
    model_config = ConfigDict(frozen=True)

    selection_mode: str = "sample"         # "sample" or "argmax"
    temperature: float = Field(..., gt=0)  # inverse temperature for softmax
    stay_suppression: float = Field(..., ge=0)  # penalty for staying
    consume_weight: float = Field(..., gt=0)    # bonus for consuming


class TransitionConfig(BaseModel):
    """Energy model parameters."""
    model_config = ConfigDict(frozen=True)

    move_cost: float = Field(..., gt=0)
    consume_cost: float = Field(..., gt=0)
    stay_cost: float = Field(..., ge=0)
    max_consume: float = Field(..., gt=0)        # max resource per consume
    energy_gain_factor: float = Field(..., ge=0)  # resource -> energy multiplier


class SystemAConfig(BaseModel):
    """Top-level System A configuration."""
    model_config = ConfigDict(frozen=True)

    agent: AgentConfig
    policy: PolicyConfig
    transition: TransitionConfig
```

### 4.2 How config flows from YAML

In the experiment config:

```yaml
system_type: "system_a"

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
```

The framework passes the `system:` dict to the factory as an opaque
`dict[str, Any]`. The factory calls `SystemAConfig(**cfg)` to parse
and validate it. Pydantic gives clear error messages when fields are
missing or invalid.

### 4.3 Test the config

```python
# tests/systems/system_a/test_config.py
import pytest
from axis.systems.system_a.config import SystemAConfig


def test_valid_config():
    cfg = SystemAConfig(
        agent={"initial_energy": 50, "max_energy": 100, "buffer_capacity": 5},
        policy={"temperature": 1.0, "stay_suppression": 0.1, "consume_weight": 3.0},
        transition={
            "move_cost": 1.0, "consume_cost": 0.5, "stay_cost": 0.5,
            "max_consume": 1.0, "energy_gain_factor": 20.0,
        },
    )
    assert cfg.agent.initial_energy == 50.0


def test_initial_exceeds_max_raises():
    with pytest.raises(ValueError, match="initial_energy"):
        SystemAConfig(
            agent={"initial_energy": 200, "max_energy": 100, "buffer_capacity": 5},
            policy={"temperature": 1.0, "stay_suppression": 0.1, "consume_weight": 3.0},
            transition={
                "move_cost": 1.0, "consume_cost": 0.5, "stay_cost": 0.5,
                "max_consume": 1.0, "energy_gain_factor": 20.0,
            },
        )
```

---

## Chapter 5: The Sensor

The sensor translates the raw world view into the agent's observation
format.

### 5.1 Reading the neighborhood

```python
# src/axis/systems/system_a/sensor.py
from __future__ import annotations

from axis.sdk.position import Position
from axis.sdk.world_types import WorldView
from axis.systems.system_a.types import CellObservation, Observation

_OUT_OF_BOUNDS = CellObservation(traversability=0.0, resource=0.0)


class SystemASensor:
    """Von Neumann neighborhood sensor."""

    def observe(self, world_view: WorldView, position: Position) -> Observation:
        x, y = position.x, position.y
        return Observation(
            current=self._observe_cell(world_view, position),
            up=self._observe_cell(world_view, Position(x=x, y=y - 1)),
            down=self._observe_cell(world_view, Position(x=x, y=y + 1)),
            left=self._observe_cell(world_view, Position(x=x - 1, y=y)),
            right=self._observe_cell(world_view, Position(x=x + 1, y=y)),
        )

    def _observe_cell(
        self, world_view: WorldView, position: Position,
    ) -> CellObservation:
        if not world_view.is_within_bounds(position):
            return _OUT_OF_BOUNDS
        cell = world_view.get_cell(position)
        return CellObservation(
            traversability=1.0 if cell.cell_type != "obstacle" else 0.0,
            resource=cell.resource_value,
        )
```

Design notes:

- **No direct world coupling.** The sensor reads from `WorldView`
  (the read-only protocol), not from the concrete `World` class.
- **Out-of-bounds cells** are treated as non-traversable with no
  resource. The agent perceives a wall.
- **String comparison** (`cell.cell_type != "obstacle"`) rather than
  enum comparison. The `CellView` uses strings to keep systems
  decoupled from the internal `CellType` enum.
- **Coordinate system:** up = y-1, down = y+1, left = x-1, right = x+1.
  Screen coordinates with y increasing downward.

### 5.2 Test the sensor

```python
# tests/systems/system_a/test_sensor.py
from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.systems.system_a.sensor import SystemASensor
from axis.world.grid_2d.factory import create_world


def _make_world():
    config = BaseWorldConfig(grid_width=5, grid_height=5)
    return create_world(config, Position(x=2, y=2), seed=42)


def test_sensor_observes_five_cells():
    world = _make_world()
    sensor = SystemASensor()
    obs = sensor.observe(world, Position(x=2, y=2))
    assert obs.dimension == 10
    assert obs.current.traversability == 1.0


def test_sensor_at_corner():
    world = _make_world()
    sensor = SystemASensor()
    obs = sensor.observe(world, Position(x=0, y=0))
    # up and left are out of bounds
    assert obs.up.traversability == 0.0
    assert obs.left.traversability == 0.0
    # down and right are in bounds
    assert obs.down.traversability == 1.0
    assert obs.right.traversability == 1.0
```

---

## Chapter 6: The Hunger Drive

The drive translates the agent's needs into per-action scores. It is
the motivational core of the system.

### 6.1 How it works

The hunger drive has one activation signal:

- **Activation** `d_H = clamp(1 - energy/max_energy, 0, 1)`.
  At full energy, `d_H = 0` (no hunger). At zero energy, `d_H = 1`
  (maximum hunger).

It produces one score per action:

| Action | Score formula |
|--------|---------------|
| up / down / left / right | `d_H * neighbor_resource` |
| consume | `d_H * consume_weight * current_resource` |
| stay | `-stay_suppression * d_H` |

Movement toward resource-rich cells scores higher. Consuming is
boosted by `consume_weight`. Staying is always penalized.

### 6.2 Implementation

```python
# src/axis/systems/system_a/drive.py
from __future__ import annotations

from axis.systems.system_a.types import HungerDriveOutput, Observation


class SystemAHungerDrive:
    """Hunger drive: scores actions based on energy need and resource availability."""

    def __init__(
        self,
        *,
        consume_weight: float,
        stay_suppression: float,
        max_energy: float,
    ) -> None:
        self._consume_weight = consume_weight
        self._stay_suppression = stay_suppression
        self._max_energy = max_energy

    def compute(self, agent_state, observation: Observation) -> HungerDriveOutput:
        energy = agent_state.energy
        d_h = max(0.0, min(1.0, 1.0 - energy / self._max_energy))

        s_up = d_h * observation.up.resource
        s_down = d_h * observation.down.resource
        s_left = d_h * observation.left.resource
        s_right = d_h * observation.right.resource
        s_consume = d_h * self._consume_weight * observation.current.resource
        s_stay = -self._stay_suppression * d_h

        return HungerDriveOutput(
            activation=d_h,
            action_contributions=(s_up, s_down, s_left, s_right, s_consume, s_stay),
        )
```

### 6.3 Test the drive

```python
# tests/systems/system_a/test_drive.py
import pytest
from axis.systems.system_a.drive import SystemAHungerDrive
from axis.systems.system_a.types import (
    AgentState, CellObservation, Observation, ObservationBuffer,
)


def _make_drive():
    return SystemAHungerDrive(
        consume_weight=3.0, stay_suppression=0.1, max_energy=100.0,
    )


def _make_state(energy: float):
    return AgentState(
        energy=energy,
        observation_buffer=ObservationBuffer(capacity=5),
    )


def _make_obs(current_resource=0.0, up_resource=0.0):
    zero = CellObservation(traversability=1.0, resource=0.0)
    return Observation(
        current=CellObservation(traversability=1.0, resource=current_resource),
        up=CellObservation(traversability=1.0, resource=up_resource),
        down=zero, left=zero, right=zero,
    )


def test_full_energy_no_hunger():
    drive = _make_drive()
    state = _make_state(energy=100.0)
    result = drive.compute(state, _make_obs(current_resource=1.0))
    assert result.activation == pytest.approx(0.0)
    # All contributions should be zero (d_H = 0)
    assert all(c == pytest.approx(0.0) for c in result.action_contributions)


def test_zero_energy_max_hunger():
    drive = _make_drive()
    state = _make_state(energy=0.0)
    result = drive.compute(state, _make_obs(current_resource=0.5))
    assert result.activation == pytest.approx(1.0)
    # consume = 1.0 * 3.0 * 0.5 = 1.5
    assert result.action_contributions[4] == pytest.approx(1.5)


def test_half_energy_half_hunger():
    drive = _make_drive()
    state = _make_state(energy=50.0)
    result = drive.compute(state, _make_obs(up_resource=0.8))
    assert result.activation == pytest.approx(0.5)
    # up score = 0.5 * 0.8 = 0.4
    assert result.action_contributions[0] == pytest.approx(0.4)


def test_stay_always_penalized():
    drive = _make_drive()
    state = _make_state(energy=50.0)
    result = drive.compute(state, _make_obs())
    # stay = -0.1 * 0.5 = -0.05
    assert result.action_contributions[5] < 0.0
```

---

## Chapter 7: The Policy

The policy converts drive scores into an action choice using softmax
selection with admissibility masking.

### 7.1 The pipeline

```
drive contributions  -->  admissibility mask  -->  softmax  -->  action
```

1. **Admissibility mask**: movement into non-traversable cells is
   blocked. Consume and stay are always admissible.
2. **Softmax**: numerically stable exponential weighting with
   configurable temperature.
3. **Selection**: either sample from the distribution or take argmax.

### 7.2 Implementation

```python
# src/axis/systems/system_a/policy.py
from __future__ import annotations

import math

import numpy as np

from axis.sdk.types import PolicyResult
from axis.systems.system_a.types import HungerDriveOutput, Observation

_ACTION_NAMES = ("up", "down", "left", "right", "consume", "stay")


class SystemAPolicy:
    """Softmax action selection with admissibility masking."""

    def __init__(self, *, temperature: float, selection_mode: str) -> None:
        self._temperature = temperature
        self._selection_mode = selection_mode

    def select(
        self,
        drive_outputs: HungerDriveOutput,
        observation: Observation,
        rng: np.random.Generator,
    ) -> PolicyResult:
        contributions = drive_outputs.action_contributions
        mask = self._compute_admissibility_mask(observation)
        masked = self._apply_mask(contributions, mask)
        probs = self._softmax(contributions, self._temperature, mask)
        action_idx = self._select_from_distribution(probs, rng)
        action = _ACTION_NAMES[action_idx]

        policy_data = {
            "raw_contributions": contributions,
            "admissibility_mask": mask,
            "masked_contributions": masked,
            "probabilities": probs,
            "selected_action": action,
            "temperature": self._temperature,
            "selection_mode": self._selection_mode,
        }
        return PolicyResult(action=action, policy_data=policy_data)

    @staticmethod
    def _compute_admissibility_mask(
        observation: Observation,
    ) -> tuple[bool, ...]:
        return (
            observation.up.traversability > 0,
            observation.down.traversability > 0,
            observation.left.traversability > 0,
            observation.right.traversability > 0,
            True,   # consume is always admissible
            True,   # stay is always admissible
        )

    @staticmethod
    def _apply_mask(
        contributions: tuple[float, ...],
        mask: tuple[bool, ...],
    ) -> tuple[float, ...]:
        return tuple(
            c if m else float("-inf")
            for c, m in zip(contributions, mask)
        )

    @staticmethod
    def _softmax(
        contributions: tuple[float, ...],
        temperature: float,
        mask: tuple[bool, ...],
    ) -> tuple[float, ...]:
        beta = 1.0 / temperature
        admissible = [c for c, m in zip(contributions, mask) if m]
        if not admissible:
            # Fallback: uniform over all actions
            n = len(contributions)
            return tuple(1.0 / n for _ in range(n))

        max_c = max(admissible)
        exp_values = []
        for c, m in zip(contributions, mask):
            if m:
                exp_values.append(math.exp(beta * (c - max_c)))
            else:
                exp_values.append(0.0)

        total = sum(exp_values)
        return tuple(e / total for e in exp_values)

    def _select_from_distribution(
        self,
        probs: tuple[float, ...],
        rng: np.random.Generator,
    ) -> int:
        if self._selection_mode == "argmax":
            return probs.index(max(probs))
        return int(rng.choice(len(probs), p=probs))
```

Key design notes:

- **Numerically stable softmax:** We subtract `max_c` before
  exponentiating to avoid overflow.
- **Masked actions get probability 0.** They can never be selected.
- **Temperature controls exploration.** Low temperature -> near-argmax
  (exploit). High temperature -> near-uniform (explore).
- **The RNG is framework-provided.** Using it ensures reproducibility
  across runs with the same seed.
- **`policy_data` captures the full pipeline.** This is what the
  visualization adapter reads to show the decision pipeline in replay.

### 7.3 Test the policy

```python
# tests/systems/system_a/test_policy.py
import numpy as np
import pytest
from axis.systems.system_a.policy import SystemAPolicy
from axis.systems.system_a.types import (
    CellObservation, HungerDriveOutput, Observation,
)


def _traversable_obs():
    cell = CellObservation(traversability=1.0, resource=0.0)
    return Observation(current=cell, up=cell, down=cell, left=cell, right=cell)


def _blocked_up_obs():
    cell = CellObservation(traversability=1.0, resource=0.0)
    blocked = CellObservation(traversability=0.0, resource=0.0)
    return Observation(current=cell, up=blocked, down=cell, left=cell, right=cell)


def test_argmax_selects_highest():
    policy = SystemAPolicy(temperature=1.0, selection_mode="argmax")
    drive = HungerDriveOutput(
        activation=1.0,
        action_contributions=(0.0, 0.0, 0.0, 5.0, 0.0, 0.0),
    )
    rng = np.random.default_rng(42)
    result = policy.select(drive, _traversable_obs(), rng)
    assert result.action == "right"


def test_blocked_direction_never_selected():
    policy = SystemAPolicy(temperature=1.0, selection_mode="argmax")
    # up has highest score but is blocked
    drive = HungerDriveOutput(
        activation=1.0,
        action_contributions=(10.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    )
    rng = np.random.default_rng(42)
    result = policy.select(drive, _blocked_up_obs(), rng)
    assert result.action != "up"


def test_probabilities_sum_to_one():
    policy = SystemAPolicy(temperature=1.0, selection_mode="sample")
    drive = HungerDriveOutput(
        activation=0.5,
        action_contributions=(0.1, 0.2, 0.3, 0.4, 0.5, -0.1),
    )
    rng = np.random.default_rng(42)
    result = policy.select(drive, _traversable_obs(), rng)
    total = sum(result.policy_data["probabilities"])
    assert total == pytest.approx(1.0)


def test_deterministic_with_same_seed():
    policy = SystemAPolicy(temperature=1.0, selection_mode="sample")
    drive = HungerDriveOutput(
        activation=0.5,
        action_contributions=(0.1, 0.2, 0.3, 0.4, 0.5, -0.1),
    )
    obs = _traversable_obs()

    r1 = policy.select(drive, obs, np.random.default_rng(42))
    r2 = policy.select(drive, obs, np.random.default_rng(42))
    assert r1.action == r2.action
```

---

## Chapter 8: The Observation Buffer

The observation buffer gives the agent short-term memory of recent
observations. It is a simple FIFO ring buffer.

### 8.1 The update function

```python
# src/axis/systems/system_a/observation_buffer.py
from __future__ import annotations

from axis.systems.system_a.types import BufferEntry, Observation, ObservationBuffer


def update_observation_buffer(
    buffer: ObservationBuffer,
    observation: Observation,
    timestep: int,
) -> ObservationBuffer:
    """Append an observation, dropping the oldest if over capacity."""
    new_entry = BufferEntry(timestep=timestep, observation=observation)
    entries = buffer.entries + (new_entry,)
    if len(entries) > buffer.capacity:
        entries = entries[1:]  # drop oldest
    return ObservationBuffer(entries=entries, capacity=buffer.capacity)
```

This is a pure function. It returns a new `ObservationBuffer` rather
than mutating the existing one (since the model is frozen). The
`entries[1:]` tuple slice drops the oldest entry when the buffer is
full.

### 8.2 Test the buffer

```python
# tests/systems/system_a/test_observation_buffer.py
from axis.systems.system_a.observation_buffer import update_observation_buffer
from axis.systems.system_a.types import (
    CellObservation, Observation, ObservationBuffer,
)


def _dummy_obs():
    cell = CellObservation(traversability=1.0, resource=0.0)
    return Observation(current=cell, up=cell, down=cell, left=cell, right=cell)


def test_append_to_empty():
    buf = ObservationBuffer(capacity=3)
    buf = update_observation_buffer(buf, _dummy_obs(), timestep=0)
    assert len(buf.entries) == 1


def test_fifo_drops_oldest():
    buf = ObservationBuffer(capacity=2)
    buf = update_observation_buffer(buf, _dummy_obs(), timestep=0)
    buf = update_observation_buffer(buf, _dummy_obs(), timestep=1)
    buf = update_observation_buffer(buf, _dummy_obs(), timestep=2)
    assert len(buf.entries) == 2
    assert buf.entries[0].timestep == 1  # oldest dropped
    assert buf.entries[1].timestep == 2


def test_capacity_respected():
    buf = ObservationBuffer(capacity=5)
    for t in range(10):
        buf = update_observation_buffer(buf, _dummy_obs(), timestep=t)
    assert len(buf.entries) == 5
```

---

## Chapter 9: The Custom Action -- Consume

System A extends the base actions with `consume`: extracting resources
from the current cell and converting them to energy.

### 9.1 The action handler

```python
# src/axis/systems/system_a/actions.py
from __future__ import annotations

from typing import Any

from axis.sdk.world_types import ActionOutcome, MutableWorldProtocol


def handle_consume(
    world: MutableWorldProtocol,
    *,
    context: dict[str, Any],
) -> ActionOutcome:
    """Extract resource from the agent's current cell."""
    max_consume: float = context["max_consume"]
    pos = world.agent_position
    extracted = world.extract_resource(pos, max_consume)

    return ActionOutcome(
        action="consume",
        moved=False,
        new_position=pos,
        data={"consumed": extracted > 0, "resource_consumed": extracted},
    )
```

Key design notes:

- **Handler receives `MutableWorldProtocol`**, not `WorldView`. Action
  handlers are the only system code that can mutate the world.
- **`context["max_consume"]`** comes from `action_context()`. This
  avoids hard-coding the value in the handler.
- **`world.extract_resource()`** handles the cell state transition
  (RESOURCE -> EMPTY). The handler doesn't need to know about `Cell`
  or `CellType`.
- **`ActionOutcome.data`** carries the result. The transition function
  will read `"resource_consumed"` to calculate energy gain.

### 9.2 Test the handler

```python
# tests/systems/system_a/test_consume.py
import pytest
from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.systems.system_a.actions import handle_consume
from axis.world.grid_2d.factory import create_world
from axis.world.grid_2d.model import Cell, CellType


def _world_with_resource_at_agent():
    resource = Cell(cell_type=CellType.RESOURCE, resource_value=0.8)
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    grid = [[resource, empty], [empty, empty]]
    config = BaseWorldConfig(grid_width=2, grid_height=2)
    return create_world(config, Position(x=0, y=0), grid=grid, seed=42)


def test_consume_extracts_resource():
    world = _world_with_resource_at_agent()
    outcome = handle_consume(world, context={"max_consume": 1.0})
    assert outcome.data["consumed"] is True
    assert outcome.data["resource_consumed"] == pytest.approx(0.8)
    assert outcome.moved is False


def test_consume_on_empty_cell():
    config = BaseWorldConfig(grid_width=3, grid_height=3)
    world = create_world(config, Position(x=1, y=1), seed=42)
    outcome = handle_consume(world, context={"max_consume": 1.0})
    assert outcome.data["consumed"] is False
    assert outcome.data["resource_consumed"] == 0.0


def test_consume_respects_max():
    world = _world_with_resource_at_agent()
    outcome = handle_consume(world, context={"max_consume": 0.3})
    assert outcome.data["resource_consumed"] == pytest.approx(0.3)
    # Resource still remains
    cell = world.get_cell(Position(x=0, y=0))
    assert cell.resource_value == pytest.approx(0.5)
```

---

## Chapter 10: The Transition Function

After the framework applies the action, the transition function updates
the agent's energy, observation buffer, and checks for death.

### 10.1 Implementation

```python
# src/axis/systems/system_a/transition.py
from __future__ import annotations

from typing import Any

from axis.sdk.actions import MOVEMENT_DELTAS, STAY
from axis.sdk.types import TransitionResult
from axis.systems.system_a.observation_buffer import update_observation_buffer
from axis.systems.system_a.types import AgentState, clip_energy


class SystemATransition:
    """Energy model and state update."""

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
        action_outcome: Any,
        observation: Any,
        *,
        timestep: int = 0,
    ) -> TransitionResult:
        # 1. Energy cost
        cost = self._get_action_cost(action_outcome.action)

        # 2. Energy gain from consuming
        resource_consumed = action_outcome.data.get("resource_consumed", 0.0)
        energy_gain = self._energy_gain_factor * resource_consumed

        # 3. New energy = old - cost + gain, clamped to [0, max]
        new_energy = clip_energy(
            agent_state.energy - cost + energy_gain,
            self._max_energy,
        )

        # 4. Update observation buffer
        new_buffer = update_observation_buffer(
            agent_state.observation_buffer, observation, timestep,
        )

        # 5. Build new state
        new_state = AgentState(
            energy=new_energy,
            observation_buffer=new_buffer,
        )

        # 6. Termination check
        terminated = new_energy <= 0.0
        termination_reason = "energy_depleted" if terminated else None

        trace_data = {
            "energy_before": agent_state.energy,
            "energy_after": new_energy,
            "energy_delta": new_energy - agent_state.energy,
            "action_cost": cost,
            "energy_gain": energy_gain,
            "resource_consumed": resource_consumed,
            "buffer_entries": len(new_buffer.entries),
            "buffer_capacity": new_buffer.capacity,
        }

        return TransitionResult(
            new_state=new_state,
            trace_data=trace_data,
            terminated=terminated,
            termination_reason=termination_reason,
        )

    def _get_action_cost(self, action: str) -> float:
        if action in MOVEMENT_DELTAS:
            return self._move_cost
        if action == "consume":
            return self._consume_cost
        return self._stay_cost
```

### 10.2 Energy model summary

```
E_new = clamp(E_old - cost(action) + gain_factor * resource_consumed, 0, E_max)
```

| Action | Cost |
|--------|------|
| up / down / left / right | `move_cost` |
| consume | `consume_cost` |
| stay | `stay_cost` |

Energy gain only happens on consume: `energy_gain_factor * resource_consumed`.
Episode terminates when `E_new <= 0`.

### 10.3 Test the transition

```python
# tests/systems/system_a/test_transition.py
import pytest
from unittest.mock import MagicMock
from axis.systems.system_a.transition import SystemATransition
from axis.systems.system_a.types import (
    AgentState, CellObservation, Observation, ObservationBuffer,
)


def _make_transition():
    return SystemATransition(
        max_energy=100.0, move_cost=1.0, consume_cost=0.5,
        stay_cost=0.5, energy_gain_factor=20.0,
    )


def _make_state(energy=50.0):
    return AgentState(
        energy=energy,
        observation_buffer=ObservationBuffer(capacity=5),
    )


def _dummy_obs():
    cell = CellObservation(traversability=1.0, resource=0.0)
    return Observation(current=cell, up=cell, down=cell, left=cell, right=cell)


def _make_outcome(action="up", resource_consumed=0.0):
    outcome = MagicMock()
    outcome.action = action
    outcome.data = {"resource_consumed": resource_consumed}
    return outcome


def test_movement_costs_energy():
    trans = _make_transition()
    result = trans.transition(_make_state(50.0), _make_outcome("up"), _dummy_obs())
    assert result.new_state.energy == pytest.approx(49.0)


def test_consume_gains_energy():
    trans = _make_transition()
    result = trans.transition(
        _make_state(50.0),
        _make_outcome("consume", resource_consumed=0.5),
        _dummy_obs(),
    )
    # 50 - 0.5 + 20*0.5 = 59.5
    assert result.new_state.energy == pytest.approx(59.5)


def test_energy_capped_at_max():
    trans = _make_transition()
    result = trans.transition(
        _make_state(95.0),
        _make_outcome("consume", resource_consumed=1.0),
        _dummy_obs(),
    )
    assert result.new_state.energy == pytest.approx(100.0)


def test_death_at_zero_energy():
    trans = _make_transition()
    result = trans.transition(
        _make_state(0.5),
        _make_outcome("up"),
        _dummy_obs(),
    )
    assert result.terminated is True
    assert result.termination_reason == "energy_depleted"
    assert result.new_state.energy == 0.0


def test_alive_above_zero():
    trans = _make_transition()
    result = trans.transition(
        _make_state(50.0),
        _make_outcome("stay"),
        _dummy_obs(),
    )
    assert result.terminated is False
    assert result.termination_reason is None
```

---

## Chapter 11: The System Facade

Now we compose all components into the `SystemA` class that satisfies
`SystemInterface`.

### 11.1 Implementation

```python
# src/axis/systems/system_a/system.py
from __future__ import annotations

from typing import Any

import numpy as np

from axis.sdk.types import DecideResult, TransitionResult

from axis.systems.system_a.actions import handle_consume
from axis.systems.system_a.config import SystemAConfig
from axis.systems.system_a.drive import SystemAHungerDrive
from axis.systems.system_a.policy import SystemAPolicy
from axis.systems.system_a.sensor import SystemASensor
from axis.systems.system_a.transition import SystemATransition
from axis.systems.system_a.types import AgentState, ObservationBuffer


class SystemA:
    """System A: energy-driven foraging agent."""

    def __init__(self, config: SystemAConfig) -> None:
        self._config = config

        # Build internal components from config
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

    # ── Identity ────────────────────────────────────────

    def system_type(self) -> str:
        return "system_a"

    def action_space(self) -> tuple[str, ...]:
        return ("up", "down", "left", "right", "consume", "stay")

    # ── State lifecycle ─────────────────────────────────

    def initialize_state(self) -> AgentState:
        return AgentState(
            energy=self._config.agent.initial_energy,
            observation_buffer=ObservationBuffer(
                capacity=self._config.agent.buffer_capacity,
            ),
        )

    def vitality(self, agent_state: Any) -> float:
        return agent_state.energy / self._config.agent.max_energy

    # ── Phase 1: Decide ─────────────────────────────────

    def decide(
        self,
        world_view: Any,
        agent_state: Any,
        rng: np.random.Generator,
    ) -> DecideResult:
        # Sensor: world -> observation
        observation = self._sensor.observe(world_view, world_view.agent_position)

        # Drive: (state, observation) -> scores
        drive_output = self._drive.compute(agent_state, observation)

        # Policy: scores -> action
        policy_result = self._policy.select(drive_output, observation, rng)

        decision_data = {
            "observation": observation.to_vector(),
            "drive_activation": drive_output.activation,
            "drive_contributions": drive_output.action_contributions,
            "policy": policy_result.policy_data,
        }
        return DecideResult(
            action=policy_result.action,
            decision_data=decision_data,
        )

    # ── Phase 2: Transition ─────────────────────────────

    def transition(
        self,
        agent_state: Any,
        action_outcome: Any,
        new_observation: Any,
    ) -> TransitionResult:
        return self._transition.transition(
            agent_state, action_outcome, new_observation,
        )

    # ── Observation ─────────────────────────────────────

    def observe(self, world_view: Any, position: Any) -> Any:
        return self._sensor.observe(world_view, position)

    # ── Custom actions ──────────────────────────────────

    def action_handlers(self) -> dict[str, Any]:
        return {"consume": handle_consume}

    def action_context(self) -> dict[str, Any]:
        return {"max_consume": self._config.transition.max_consume}
```

### 11.2 What each method does

| Method | Purpose | Called by |
|--------|---------|-----------|
| `system_type()` | Returns `"system_a"` | Framework (traces, config) |
| `action_space()` | Returns all 6 actions | Framework (validation) |
| `initialize_state()` | Creates initial `AgentState` | Framework (episode start) |
| `vitality(state)` | Returns `energy / max_energy` | Framework (traces, summaries) |
| `decide(...)` | Sensor -> Drive -> Policy -> `DecideResult` | Framework (each step) |
| `transition(...)` | Energy update + buffer + death check | Framework (each step) |
| `observe(...)` | Post-action observation | Framework (each step) |
| `action_handlers()` | Returns `{"consume": handle_consume}` | Framework (episode setup) |
| `action_context()` | Returns `{"max_consume": ...}` | Framework (episode setup) |

### 11.3 Test the facade

```python
# tests/systems/system_a/test_system.py
import numpy as np
import pytest
from axis.sdk.interfaces import SystemInterface
from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.systems.system_a.config import SystemAConfig
from axis.systems.system_a.system import SystemA
from axis.world.grid_2d.factory import create_world


def _make_config():
    return SystemAConfig(
        agent={"initial_energy": 50, "max_energy": 100, "buffer_capacity": 5},
        policy={"temperature": 1.0, "stay_suppression": 0.1, "consume_weight": 3.0},
        transition={
            "move_cost": 1.0, "consume_cost": 0.5, "stay_cost": 0.5,
            "max_consume": 1.0, "energy_gain_factor": 20.0,
        },
    )


def test_system_satisfies_protocol():
    system = SystemA(_make_config())
    assert isinstance(system, SystemInterface)


def test_system_type():
    system = SystemA(_make_config())
    assert system.system_type() == "system_a"


def test_action_space_includes_consume():
    system = SystemA(_make_config())
    actions = system.action_space()
    assert "consume" in actions
    assert "up" in actions
    assert "stay" in actions


def test_initial_state():
    system = SystemA(_make_config())
    state = system.initialize_state()
    assert state.energy == 50.0
    assert state.observation_buffer.capacity == 5
    assert len(state.observation_buffer.entries) == 0


def test_vitality():
    system = SystemA(_make_config())
    state = system.initialize_state()
    assert system.vitality(state) == pytest.approx(0.5)  # 50/100


def test_decide_returns_valid_action():
    system = SystemA(_make_config())
    config = BaseWorldConfig(grid_width=5, grid_height=5)
    world = create_world(config, Position(x=2, y=2), seed=42)
    state = system.initialize_state()
    rng = np.random.default_rng(42)

    result = system.decide(world, state, rng)
    assert result.action in system.action_space()


def test_full_step_cycle():
    """Run one complete decide -> act -> transition cycle."""
    system = SystemA(_make_config())
    config = BaseWorldConfig(grid_width=5, grid_height=5, resource_regen_rate=0.5)
    world = create_world(config, Position(x=2, y=2), seed=42)
    state = system.initialize_state()
    rng = np.random.default_rng(42)

    # Decide
    decide_result = system.decide(world, state, rng)

    # Simulate framework applying the action (simplified)
    from axis.world.actions import create_action_registry
    registry = create_action_registry()
    for name, handler in system.action_handlers().items():
        registry.register(name, handler)

    world.tick()
    outcome = registry.apply(world, decide_result.action,
                             context=system.action_context())

    # Observe + transition
    obs = system.observe(world, world.agent_position)
    result = system.transition(state, outcome, obs)

    assert result.new_state.energy >= 0
    assert isinstance(result.terminated, bool)
```

---

## Chapter 12: Plugin Registration

Now we register the system with the framework so it can be used from
experiment configs and the CLI.

### 12.1 The `register()` function

```python
# src/axis/systems/system_a/__init__.py
"""System A -- hunger-driven baseline agent."""

from axis.systems.system_a.actions import handle_consume
from axis.systems.system_a.config import SystemAConfig
from axis.systems.system_a.system import SystemA

__all__ = [
    "SystemA",
    "SystemAConfig",
    "handle_consume",
]


def register() -> None:
    """Register system_a: system factory + visualization adapter."""
    from axis.framework.registry import register_system, registered_system_types

    if "system_a" not in registered_system_types():

        def _factory(cfg: dict) -> SystemA:
            return SystemA(SystemAConfig(**cfg))

        register_system("system_a", _factory)

    from axis.visualization.registry import registered_system_visualizations

    if "system_a" not in registered_system_visualizations():
        try:
            import axis.systems.system_a.visualization  # noqa: F401
        except ImportError:
            pass
```

The factory function is the bridge between the framework's `dict`
and the system's typed config. `SystemAConfig(**cfg)` does all the
parsing and validation.

### 12.2 Plugin declaration

Add to `pyproject.toml` (for installable packages):

```toml
[project.entry-points."axis.plugins"]
system_a = "axis.systems.system_a"
```

Or to `axis-plugins.yaml` (for local development):

```yaml
plugins:
  - axis.systems.system_a
```

### 12.3 Test registration

```python
# tests/systems/system_a/test_registration.py
from axis.framework.registry import registered_system_types


def test_system_a_is_registered():
    assert "system_a" in registered_system_types()
```

---

## Chapter 13: The Visualization Adapter

The visualization adapter tells the replay viewer how to display
System A's decision internals. It produces analysis sections (text)
and overlays (graphics on the grid).

### 13.1 The `SystemVisualizationAdapter` protocol

The adapter must implement these methods:

```python
class SystemVisualizationAdapter(Protocol):
    def phase_names(self) -> list[str]: ...
    def vitality_label(self) -> str: ...
    def format_vitality(self, value, system_data) -> str: ...
    def build_step_analysis(self, step_trace) -> list[AnalysisSection]: ...
    def build_overlays(self, step_trace) -> list[OverlayData]: ...
    def available_overlay_types(self) -> list[OverlayTypeDeclaration]: ...
```

### 13.2 Skeleton adapter

```python
# src/axis/systems/system_a/visualization.py
from __future__ import annotations

from typing import Any

from axis.visualization.registry import register_system_visualization
from axis.visualization.types import (
    AnalysisRow,
    AnalysisSection,
    OverlayData,
    OverlayItem,
    OverlayTypeDeclaration,
)


class SystemAVisualizationAdapter:
    """Visualization adapter for System A."""

    def __init__(self, max_energy: float) -> None:
        self._max_energy = max_energy

    def phase_names(self) -> list[str]:
        return ["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]

    def vitality_label(self) -> str:
        return "Energy"

    def format_vitality(self, value: float, system_data: dict) -> str:
        actual = value * self._max_energy
        return f"{actual:.2f} / {self._max_energy:.2f}"
```

### 13.3 Analysis sections

Analysis sections appear as monospace text blocks in the step analysis
panel. Each section has a title and rows of `(label, value)` pairs:

```python
    def build_step_analysis(self, step_trace) -> list[AnalysisSection]:
        dd = step_trace.system_data.get("decision_data", {})
        td = step_trace.system_data.get("trace_data", {})

        sections = []

        # Section 1: Step overview
        sections.append(AnalysisSection(
            title="Step Overview",
            rows=[
                AnalysisRow(label="Timestep", value=str(step_trace.timestep)),
                AnalysisRow(label="Action", value=step_trace.action),
                AnalysisRow(label="Energy before", value=f"{td.get('energy_before', 0):.2f}"),
                AnalysisRow(label="Energy after", value=f"{td.get('energy_after', 0):.2f}"),
                AnalysisRow(label="Energy delta", value=f"{td.get('energy_delta', 0):+.2f}"),
            ],
        ))

        # Section 2: Observation
        obs = dd.get("observation", ())
        if len(obs) >= 10:
            sections.append(AnalysisSection(
                title="Observation",
                rows=[
                    AnalysisRow(label="Current", value=f"trav={obs[0]:.0f} res={obs[1]:.3f}"),
                    AnalysisRow(label="Up",      value=f"trav={obs[2]:.0f} res={obs[3]:.3f}"),
                    AnalysisRow(label="Down",    value=f"trav={obs[4]:.0f} res={obs[5]:.3f}"),
                    AnalysisRow(label="Left",    value=f"trav={obs[6]:.0f} res={obs[7]:.3f}"),
                    AnalysisRow(label="Right",   value=f"trav={obs[8]:.0f} res={obs[9]:.3f}"),
                ],
            ))

        # Section 3: Drive output
        sections.append(AnalysisSection(
            title="Drive Output",
            rows=[
                AnalysisRow(label="Activation", value=f"{dd.get('drive_activation', 0):.4f}"),
            ] + [
                AnalysisRow(label=name, value=f"{c:.4f}")
                for name, c in zip(
                    ["UP", "DOWN", "LEFT", "RIGHT", "CONSUME", "STAY"],
                    dd.get("drive_contributions", ()),
                )
            ],
        ))

        # More sections can be added for the policy pipeline,
        # buffer state, and outcome details.

        return sections
```

### 13.4 Debug overlays

Overlays are graphical elements drawn on the grid cells. Each overlay
contains a list of `OverlayItem` objects:

```python
    def build_overlays(self, step_trace) -> list[OverlayData]:
        dd = step_trace.system_data.get("decision_data", {})
        policy = dd.get("policy", {})
        probs = policy.get("probabilities", ())
        selected = policy.get("selected_action", "")
        pos = step_trace.agent_position_before

        overlays = []

        # Overlay 1: Action preference arrows
        if len(probs) >= 6:
            items = []
            directions = ["up", "down", "left", "right"]
            for i, d in enumerate(directions):
                items.append(OverlayItem(
                    item_type="directional_arrow",
                    position=pos,
                    data={
                        "direction": d,
                        "length": probs[i],
                        "color": (255, 193, 7) if d == selected else (100, 100, 200),
                    },
                ))
            overlays.append(OverlayData(
                overlay_type="action_preference",
                items=items,
            ))

        # Overlay 2: Drive contribution bar chart
        contribs = dd.get("drive_contributions", ())
        if contribs:
            overlays.append(OverlayData(
                overlay_type="drive_contribution",
                items=[OverlayItem(
                    item_type="bar_chart",
                    position=pos,
                    data={
                        "values": list(contribs),
                        "labels": ["U", "D", "L", "R", "C", "S"],
                    },
                )],
            ))

        return overlays

    def available_overlay_types(self) -> list[OverlayTypeDeclaration]:
        return [
            OverlayTypeDeclaration(
                key="action_preference",
                label="Action Preference",
                description="Arrows showing action probabilities",
            ),
            OverlayTypeDeclaration(
                key="drive_contribution",
                label="Drive Contribution",
                description="Per-action drive scores as bar chart",
            ),
        ]
```

### 13.5 Registration

At the bottom of `visualization.py`, register via module-level side
effect:

```python
def _system_a_vis_factory() -> SystemAVisualizationAdapter:
    return SystemAVisualizationAdapter(max_energy=100.0)


register_system_visualization("system_a", _system_a_vis_factory)
```

Importing this module triggers registration. The `register()` function
in `__init__.py` imports this module to ensure it happens.

---

## Chapter 14: Integration Test

The ultimate test runs the full system through the framework pipeline.

```python
# tests/systems/system_a/test_integration.py
from pathlib import Path

import pytest

from axis.framework.experiment import execute_experiment
from axis.framework.config import ExperimentConfig


def test_system_a_full_experiment(tmp_path: Path):
    """Run a complete experiment through the framework."""
    config = ExperimentConfig(
        system_type="system_a",
        experiment_type="single_run",
        general={"seed": 42},
        execution={"max_steps": 50},
        world={
            "grid_width": 5,
            "grid_height": 5,
            "resource_regen_rate": 0.1,
        },
        system={
            "agent": {
                "initial_energy": 50,
                "max_energy": 100,
                "buffer_capacity": 5,
            },
            "policy": {
                "temperature": 1.0,
                "stay_suppression": 0.1,
                "consume_weight": 3.0,
            },
            "transition": {
                "move_cost": 1.0,
                "consume_cost": 0.5,
                "stay_cost": 0.5,
                "max_consume": 1.0,
                "energy_gain_factor": 20.0,
            },
        },
        num_episodes_per_run=3,
    )

    result = execute_experiment(config, tmp_path)

    assert result.status == "completed"
    assert len(result.run_results) == 1
    summary = result.run_results[0].summary
    assert summary.num_episodes == 3
    assert 0.0 <= summary.mean_final_vitality <= 1.0


def test_system_a_deterministic(tmp_path: Path):
    """Same seed produces identical results."""
    def _run(seed):
        config = ExperimentConfig(
            system_type="system_a",
            experiment_type="single_run",
            general={"seed": seed},
            execution={"max_steps": 20},
            world={"grid_width": 5, "grid_height": 5},
            system={
                "agent": {"initial_energy": 30, "max_energy": 50, "buffer_capacity": 3},
                "policy": {"temperature": 1.0, "stay_suppression": 0.1, "consume_weight": 3.0},
                "transition": {
                    "move_cost": 1.0, "consume_cost": 0.5, "stay_cost": 0.5,
                    "max_consume": 1.0, "energy_gain_factor": 20.0,
                },
            },
            num_episodes_per_run=1,
        )
        return execute_experiment(config, tmp_path / f"run_{seed}")

    r1 = _run(42)
    r2 = _run(42)
    s1 = r1.run_results[0].summary
    s2 = r2.run_results[0].summary
    assert s1.mean_steps == s2.mean_steps
    assert s1.mean_final_vitality == pytest.approx(s2.mean_final_vitality)
```

---

## Chapter 15: Running Your System

### 15.1 From the CLI

```bash
# Run an experiment
axis experiments run experiments/configs/system-a-baseline.yaml

# Visualize a recorded episode
axis visualize --experiment <eid> --run <rid> --episode 1
```

### 15.2 From Python

```python
import numpy as np
from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.systems.system_a import SystemA, SystemAConfig
from axis.framework.runner import setup_episode, run_episode

config = SystemAConfig(
    agent={"initial_energy": 50, "max_energy": 100, "buffer_capacity": 5},
    policy={"temperature": 1.0, "stay_suppression": 0.1, "consume_weight": 3.0},
    transition={
        "move_cost": 1.0, "consume_cost": 0.5, "stay_cost": 0.5,
        "max_consume": 1.0, "energy_gain_factor": 20.0,
    },
)
system = SystemA(config)

world_config = BaseWorldConfig(
    grid_width=10, grid_height=10,
    obstacle_density=0.1, resource_regen_rate=0.05,
)
world, registry = setup_episode(system, world_config, Position(x=5, y=5), seed=42)

trace = run_episode(system, world, registry, max_steps=200, seed=42,
                    world_config=world_config)

print(f"Survived {trace.total_steps} steps")
print(f"Final vitality: {trace.final_vitality:.3f}")
print(f"Termination: {trace.termination_reason}")
```

---

## Chapter 16: Complete File Inventory

The tutorial above builds each component from scratch for learning
purposes. The actual System A implementation uses components from
the **System Construction Kit** (`construction_kit/`), so its file
layout is leaner:

```
src/axis/systems/system_a/
    __init__.py              # Package init + register()
    types.py                 # AgentState only (kit provides observation/buffer/drive types)
    config.py                # SystemAConfig (imports AgentConfig, PolicyConfig, TransitionConfig from kit)
    transition.py            # SystemATransition -- energy model + buffer + termination
    system.py                # SystemA -- facade composing kit components
    visualization.py         # SystemAVisualizationAdapter -- analysis + overlays

src/axis/systems/construction_kit/   # Reusable components (shared with System A+W)
    observation/sensor.py    # VonNeumannSensor (was SystemASensor)
    observation/types.py     # CellObservation, Observation
    drives/hunger.py         # HungerDrive (was SystemAHungerDrive)
    drives/types.py          # HungerDriveOutput, CuriosityDriveOutput
    policy/softmax.py        # SoftmaxPolicy (was SystemAPolicy)
    memory/types.py          # BufferEntry, ObservationBuffer, WorldModelState
    memory/observation_buffer.py  # update_observation_buffer()
    energy/functions.py      # clip_energy, compute_vitality, etc.
    types/config.py          # AgentConfig, PolicyConfig, TransitionConfig
    types/actions.py         # handle_consume
```

tests/systems/system_a/
    test_types.py            # Domain type invariants
    test_config.py           # Config validation
    test_sensor.py           # Neighborhood observation
    test_drive.py            # Hunger activation + scoring
    test_policy.py           # Softmax selection + admissibility
    test_observation_buffer.py  # FIFO buffer behavior
    test_consume.py          # Custom action handler
    test_transition.py       # Energy model + death
    test_system.py           # Facade protocol conformance
    test_registration.py     # Plugin registration
    test_integration.py      # Full experiment through framework
```

---

## Summary: Building a System, Step by Step

1. **Check the Construction Kit** -- before building from scratch,
   see what reusable components are available in
   `src/axis/systems/construction_kit/`. Sensors, drives, policies,
   memory, energy utilities, and shared config types are all provided.

2. **Understand the contract** -- `SystemInterface` defines 9 methods.
   The framework calls `decide()` and `transition()` each step.

3. **Define your agent state** -- what the agent remembers between
   steps. Use frozen Pydantic models. Exclude position (it belongs
   to the world).

4. **Define your observation** -- what the agent perceives. Use
   `VonNeumannSensor` from the kit or build your own sensor.

5. **Build the sensor** -- reads cells from `WorldView`, produces
   structured observations.

6. **Build the drive** -- converts agent needs + observation into
   per-action scores. Use `HungerDrive` or `CuriosityDrive` from
   the kit, or build your own.

7. **Build the policy** -- converts scores into an action choice.
   Use `SoftmaxPolicy` from the kit or build your own.

8. **Build the observation buffer** -- short-term memory as a FIFO
   ring buffer. Use `ObservationBuffer` and `update_observation_buffer`
   from the kit.

9. **Build the custom action handler** -- receives `MutableWorldProtocol`,
   returns `ActionOutcome`. Use `handle_consume` from the kit for
   resource extraction.

10. **Build the transition function** -- updates energy, buffer, and
    checks for termination after each step.

11. **Build the facade** -- compose all components into a class that
    satisfies `SystemInterface`.

12. **Register** -- add `register()` to `__init__.py`, declare entry
    point in `pyproject.toml`.

13. **Build the visualization adapter** -- analysis sections for the
    text panel, overlay items for the grid display.

14. **Test each layer** -- unit tests for components, integration test
    through the full experiment pipeline.
