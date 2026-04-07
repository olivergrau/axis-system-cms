# WP-1.1 Implementation Brief -- Core SDK Interfaces

## Context

We are implementing the **modular architecture evolution** of the AXIS project. Phase 0 (WP-0.1, WP-0.2) established the `axis` package scaffold and the test infrastructure.

This work package is **WP-1.1**. It defines the abstract interfaces that all systems must implement. These interfaces are the **type system** of the new architecture -- the contracts through which systems and the framework interact.

### Predecessor State (After WP-0.2)

```
src/axis/                                   # Empty package scaffold
    sdk/                                    # Empty __init__.py
    framework/, world/, systems/system_a/, visualization/

tests/v02/                                  # Test infrastructure
    builders/, fixtures/, utils/            # Config builders, assertion helpers
    test_scaffold.py, test_infrastructure.py
```

The `axis.sdk` package is empty. The existing `axis_system_a` package contains the concrete implementations that these interfaces will abstract:

| Current concrete implementation | Future interface |
|------|------|
| `runner.py:episode_step` (orchestration chain) | `SystemInterface` |
| `observation.py:build_observation` | `SensorInterface` |
| `drives.py:compute_hunger_drive` | `DriveInterface` |
| `policy.py:select_action` | `PolicyInterface` |
| `transition.py:step` (agent logic only) | `TransitionInterface` |

### Architectural Decisions (Binding)

- **Q1**: Opaque `system.step()` -- framework never orchestrates sub-components
- **Q2**: Framework-owned world mutation -- systems return action intents, framework applies them
- **Q14**: Observations are system-defined, opaque to framework
- **Q15**: Mandatory normalized vitality metric `[0, 1]` exposed by all systems
- **Q16**: Both framework (`max_steps`) and system (`vitality <= 0`, etc.) can terminate

### Design Refinement (from Roadmap)

The Q1 (opaque step) + Q2 (framework applies actions) decisions require a **two-phase step contract**:

1. `system.decide()` -- system produces action intent (needs to happen before framework can apply action to world)
2. `system.transition()` -- system processes outcome (needs to happen after framework applies action)

This splits the single `system.step()` described in Q1 into two calls per step. The system still owns all internal logic (sensor, drives, policy, energy, memory, termination). The framework only needs the action before it can modify the world, and the system needs the outcome after.

### Global System Assumptions (from Q&A)

All systems must internally implement:

1. Energy-based state (mandatory)
2. Drive-based modulation (1..N drives, mandatory)
3. Policy-driven action selection (mandatory)
4. Framework-owned world interaction
5. Explicit transition function with structured trace output
6. Step-level traceability (replay contract conformance)

### Reference Documents

- `docs/v0.2.0/architecture/evolution/architectural-vision-v0.2.0.md` -- Sections 4 (System SDK), 12 (Step Lifecycle)
- `docs/v0.2.0/architecture/evolution/modular-architecture-roadmap.md` -- WP-1.1 definition
- `docs/v0.2.0/architecture/evolution/modular-architecture-questions-answers.md` -- Q1, Q2, Q4, Q14, Q15, Q16

---

## Objective

Define the abstract interfaces and associated data types that constitute the **System SDK**. This includes:

1. `SystemInterface` -- the primary contract between systems and the framework
2. `SensorInterface` -- internal observation construction contract
3. `DriveInterface` -- internal drive computation contract
4. `PolicyInterface` -- internal action selection contract
5. `TransitionInterface` -- internal state transition contract
6. Supporting data types: `DecideResult`, `TransitionResult`, `PolicyResult`

These are **interface definitions only**. No concrete implementations are provided in this WP. System A will implement these interfaces in WP-2.3.

---

## Scope

### 1. SystemInterface

**File**: `src/axis/sdk/interfaces.py`

The primary interface between a system and the framework. Systems implement this; the framework calls it.

```python
from typing import Any, Protocol

import numpy as np

from axis.sdk.types import DecideResult, TransitionResult


class SystemInterface(Protocol):
    """Primary contract between a system and the framework.

    The framework interacts with systems exclusively through this interface.
    Systems own all internal logic (sensor, drives, policy, transition).
    The framework owns world mutation and episode orchestration.
    """

    def system_type(self) -> str:
        """Return the system's unique type identifier (e.g., 'system_a')."""
        ...

    def action_space(self) -> tuple[str, ...]:
        """Return the ordered tuple of action names this system can produce.

        Must include all base actions ('up', 'down', 'left', 'right', 'stay')
        plus any system-specific actions (e.g., 'consume').
        """
        ...

    def initialize_state(self, system_config: dict[str, Any]) -> Any:
        """Create the initial agent state from the system config.

        The returned state is opaque to the framework. Only the system
        and its sub-components interpret it. The framework passes it
        back to decide() and transition() without inspection.
        """
        ...

    def vitality(self, agent_state: Any) -> float:
        """Return the agent's normalized vitality in [0.0, 1.0].

        This is the only framework-readable metric from agent state.
        For System A, this is energy / max_energy.
        """
        ...

    def decide(
        self,
        world_view: Any,  # WorldView from axis.sdk.world (WP-1.2)
        agent_state: Any,
        rng: np.random.Generator,
    ) -> DecideResult:
        """Phase 1 of the two-phase step: produce an action intent.

        The system reads the world via world_view (read-only), evaluates
        its internal pipeline (sensor -> drives -> policy), and returns
        the chosen action plus any decision trace data.

        The framework will apply this action to the world and call
        transition() with the outcome.
        """
        ...

    def transition(
        self,
        agent_state: Any,
        action_outcome: Any,  # ActionOutcome from axis.sdk.world (WP-1.2)
        new_observation: Any,
    ) -> TransitionResult:
        """Phase 2 of the two-phase step: process the action outcome.

        Receives the outcome of the applied action (what happened in the
        world) and the post-action observation. Updates internal state
        (energy, memory, etc.) and checks for system-level termination.
        """
        ...
```

**Design notes**:

- Uses `typing.Protocol` (structural subtyping), not ABC
- `agent_state` is `Any` at the SDK level -- systems define their own state types. The framework treats it as opaque, passing it in and receiving it back
- `world_view` and `action_outcome` are typed as `Any` here; they will be properly typed once WP-1.2 defines `WorldView` and `ActionOutcome`. The implementation may use `TYPE_CHECKING` imports or forward references
- `rng` is `np.random.Generator` for deterministic sampling

### 2. Sub-Component Interfaces

**File**: `src/axis/sdk/interfaces.py` (same file)

These interfaces are **mandatory internal contracts**. All systems must implement them internally. The framework does **not** call them directly -- they exist to:

- Enforce structural consistency across systems
- Enable independent unit testing of sub-components
- Document the expected internal architecture

```python
class SensorInterface(Protocol):
    """Constructs observations from the world state.

    System-specific: each system defines its own observation type.
    For System A, this produces a 10-dimensional Observation
    (Von Neumann neighborhood with traversability and resource signals).
    """

    def observe(self, world_view: Any, position: Any) -> Any:
        """Produce an observation from the current world state and position."""
        ...


class DriveInterface(Protocol):
    """Computes a drive output that modulates action selection.

    Every system must have at least one drive. Drive outputs flow
    into the policy for action selection.
    """

    def compute(self, agent_state: Any, observation: Any) -> Any:
        """Compute drive output from current state and observation."""
        ...


class PolicyInterface(Protocol):
    """Selects an action based on drive outputs and observation.

    Receives the combined drive outputs, the current observation,
    and a random number generator for stochastic selection.
    """

    def select(
        self,
        drive_outputs: Any,
        observation: Any,
        rng: np.random.Generator,
    ) -> "PolicyResult":
        """Select an action from the drive-modulated contributions."""
        ...


class TransitionInterface(Protocol):
    """Updates agent state after an action has been applied to the world.

    Handles state evolution: energy changes, memory updates,
    termination checks. Does NOT mutate the world.
    """

    def transition(
        self,
        agent_state: Any,
        action_outcome: Any,
        observation: Any,
    ) -> TransitionResult:
        """Process action outcome and produce new agent state."""
        ...
```

### 3. SDK Data Types

**File**: `src/axis/sdk/types.py`

Data types used in the interface signatures. These are the framework-visible output types.

```python
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class DecideResult(BaseModel):
    """Output of SystemInterface.decide().

    Contains the chosen action and system-specific decision data
    that will be included in the step trace.
    """

    model_config = ConfigDict(frozen=True)

    action: str
    decision_data: dict[str, Any]


class TransitionResult(BaseModel):
    """Output of SystemInterface.transition().

    Contains the new agent state, system-specific trace data,
    and termination information.
    """

    model_config = ConfigDict(frozen=True)

    new_state: Any  # system-specific AgentState, opaque to framework
    trace_data: dict[str, Any]
    terminated: bool
    termination_reason: str | None = None


class PolicyResult(BaseModel):
    """Output of PolicyInterface.select().

    Contains the selected action and any policy trace data
    (e.g., probabilities, temperature, selection mode).
    """

    model_config = ConfigDict(frozen=True)

    action: str
    policy_data: dict[str, Any]
```

**Field descriptions**:

| Type | Field | Purpose |
|------|-------|---------|
| `DecideResult.action` | Action name string (e.g., `"consume"`, `"up"`) | Framework uses this to apply to world |
| `DecideResult.decision_data` | System-specific trace dict | Packed into `system_data` in replay trace |
| `TransitionResult.new_state` | Opaque agent state | Framework passes back to next `decide()` call |
| `TransitionResult.trace_data` | System-specific trace dict | Packed into `system_data` in replay trace |
| `TransitionResult.terminated` | System signals episode end | Framework checks this after each step |
| `TransitionResult.termination_reason` | Human-readable string | e.g., `"energy_depleted"` |
| `PolicyResult.action` | Action name string | Used by `decide()` to build `DecideResult` |
| `PolicyResult.policy_data` | Policy-level trace dict | Decision pipeline details |

### 4. SDK Package Exports

**File**: `src/axis/sdk/__init__.py`

Update the SDK `__init__.py` to export the public API:

```python
"""System SDK -- interfaces, contracts, and base types."""

from axis.sdk.interfaces import (
    DriveInterface,
    PolicyInterface,
    SensorInterface,
    SystemInterface,
    TransitionInterface,
)
from axis.sdk.types import DecideResult, PolicyResult, TransitionResult

__all__ = [
    "SystemInterface",
    "SensorInterface",
    "DriveInterface",
    "PolicyInterface",
    "TransitionInterface",
    "DecideResult",
    "TransitionResult",
    "PolicyResult",
]
```

---

## Out of Scope

Do **not** implement any of the following in WP-1.1:

- Concrete implementations of any interface (System A conformance is WP-2.3)
- `WorldView` or `ActionOutcome` types (WP-1.2)
- `BaseStepTrace` or replay contract types (WP-1.3)
- `FrameworkConfig` or `ExperimentConfig` types (WP-1.4)
- System registry (WP-3.1)
- Framework episode runner (WP-3.2)
- Any modifications to `axis_system_a` code
- Any modifications to files outside `src/axis/sdk/` and `tests/v02/`

---

## Architectural Constraints

### 1. Protocol-Based Interfaces

All interfaces use `typing.Protocol` for structural subtyping. This means:

- Systems do not need to inherit from a base class
- Any class with matching method signatures satisfies the protocol
- This is consistent with Python's duck-typing philosophy and Pydantic's approach

### 2. Opaque Agent State

`agent_state` is `Any` at the SDK level. The framework:

- Receives it from `initialize_state()`
- Passes it to `decide()` and `transition()`
- Receives new state from `TransitionResult.new_state`
- Never inspects, validates, or serializes it directly

The only framework-readable metric from agent state is `vitality()`.

### 3. Action Names are Strings

Actions are strings (e.g., `"up"`, `"consume"`), not enums. This enables system extensibility: each system can introduce new action names. The mapping from action strings to world operations happens via the action engine (WP-2.2).

Base actions that all systems can use: `"up"`, `"down"`, `"left"`, `"right"`, `"stay"`.

### 4. System-Specific Data is Dict-Based

`decision_data`, `trace_data`, and `policy_data` are all `dict[str, Any]`. This keeps the SDK boundary clean -- the framework never needs to know what's inside these dicts. System-specific visualization adapters (WP-4.2) will interpret them.

### 5. No Framework Dependencies

The `axis.sdk` package must not import from `axis.framework`, `axis.world`, `axis.systems`, or `axis.visualization`. It depends only on:

- Python stdlib
- `pydantic`
- `numpy` (for `np.random.Generator` type)
- Other `axis.sdk` modules

### 6. Frozen Pydantic Models

All data types (`DecideResult`, `TransitionResult`, `PolicyResult`) are frozen Pydantic models, consistent with the project's immutability convention.

---

## Expected File Structure

After WP-1.1, these files are **new or modified**:

```
src/axis/sdk/__init__.py                    # MODIFIED (exports added)
src/axis/sdk/interfaces.py                  # NEW (5 protocol interfaces)
src/axis/sdk/types.py                       # NEW (DecideResult, TransitionResult, PolicyResult)
tests/v02/sdk/test_sdk_types.py             # NEW (verification tests)
```

Unchanged:

```
src/axis_system_a/                          # UNCHANGED
src/axis/framework/, world/, systems/, visualization/  # UNCHANGED
tests/v02/test_scaffold.py                  # UNCHANGED (may need update for non-empty sdk)
```

---

## Testing Requirements

### SDK type verification tests (`tests/v02/sdk/test_sdk_types.py`)

Must include:

1. **DecideResult construction and immutability**:
   - `DecideResult(action="up", decision_data={})` produces a valid instance
   - `DecideResult(action="consume", decision_data={"drive": {"activation": 0.8}})` works with nested data
   - Instances are frozen (setting `action` raises)
   - `action` field is a string, `decision_data` is a dict

2. **TransitionResult construction and immutability**:
   - `TransitionResult(new_state=..., trace_data={}, terminated=False)` works
   - `TransitionResult(new_state=..., trace_data={}, terminated=True, termination_reason="energy_depleted")` works
   - `termination_reason` defaults to `None`
   - Instances are frozen

3. **PolicyResult construction and immutability**:
   - `PolicyResult(action="stay", policy_data={"temperature": 1.0})` works
   - Instances are frozen

4. **Interface protocol structural tests**:
   - A mock class implementing all `SystemInterface` methods satisfies `isinstance` check via `runtime_checkable` (if decorated) OR at minimum, type-check passes
   - Verify that the protocol methods have the expected names and argument counts

5. **Import verification**:
   - `from axis.sdk import SystemInterface, DecideResult, TransitionResult, PolicyResult` succeeds
   - `from axis.sdk import SensorInterface, DriveInterface, PolicyInterface, TransitionInterface` succeeds
   - `from axis.sdk.interfaces import SystemInterface` succeeds
   - `from axis.sdk.types import DecideResult` succeeds

### Existing test suite

All existing tests must still pass. The new files add to but do not interfere with the existing test tree.

---

## Implementation Style

- Python 3.11+
- `typing.Protocol` for interfaces (with `@runtime_checkable` where useful for testing)
- Frozen Pydantic `BaseModel` for data types
- Clear docstrings on all interfaces and their methods
- Type hints throughout
- No dependencies on `axis` domain types beyond `axis.sdk` itself
- No clever metaprogramming

---

## Expected Deliverable

1. `src/axis/sdk/interfaces.py` with 5 protocol interfaces
2. `src/axis/sdk/types.py` with 3 frozen Pydantic data types
3. Updated `src/axis/sdk/__init__.py` with exports
4. Verification tests at `tests/v02/sdk/test_sdk_types.py`
5. Confirmation that all existing tests still pass

---

## Important Final Constraint

This WP produces **type definitions only**. No behavior, no logic, no implementations. The interfaces describe what systems must do, not how they do it.

The most critical design property is the **two-phase step contract**: `decide()` produces action intent, `transition()` processes outcome. This decomposition is driven by the architectural decision that the framework owns world mutation but systems own action selection.

When System A is adapted to these interfaces in WP-2.3, the mapping should be direct:

| Interface method | System A implementation |
|---|---|
| `decide()` | `build_observation` -> `compute_hunger_drive` -> `select_action` -> return action |
| `transition()` | energy computation + memory update + termination check -> return new state |
| `vitality()` | `energy / max_energy` |
| `initialize_state()` | create `AgentState(energy=initial, memory=empty)` |
| `action_space()` | `("up", "down", "left", "right", "consume", "stay")` |

If any interface feels wrong for this mapping, reconsider the interface design before committing.
