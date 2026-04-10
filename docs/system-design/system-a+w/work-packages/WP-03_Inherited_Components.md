# WP-3: Inherited Components

## Metadata
- Work Package: WP-3
- Title: Inherited Components (Sensor, Memory, Consume Action)
- System: System A+W
- Source Files: `src/axis/systems/system_aw/sensor.py`, `observation_buffer.py`, `actions.py`
- Test File: `tests/systems/system_aw/test_inherited.py`
- Model Reference: `01_System A+W Model.md`, Sections 1.1, 8
- Dependencies: WP-1 (config), WP-2 (types)

---

## 1. Objective

Wire the three System A components that are unchanged in System A+W into the `system_aw` package: the **sensor**, the **memory update function**, and the **consume action handler**.

The formal model (Section 1.1) explicitly states:

> - The action space is identical
> - The sensor model is identical
> - The energy dynamics and transition mechanics are identical

This WP makes these components available to System A+W without modification or duplication.

---

## 2. Design Decision: Import and Re-export

**Decision: Thin wrapper modules that import from System A and re-export.**

Each file in `src/axis/systems/system_aw/` serves as a local entry point so that all other System A+W modules import from within their own package. The actual logic lives in System A.

**Rationale:**
- **No duplication**: Logic is defined once, in System A
- **Package encapsulation**: Other `system_aw` modules import from `axis.systems.system_aw.sensor` (not `axis.systems.system_a.sensor`), making it easy to replace with a local implementation if needed
- **Test isolation**: System A+W tests verify these components work correctly in the A+W context (with `AgentStateAW`, `WorldModelState`, etc.)
- **Single-commit replacement**: If a component needs to diverge from System A in the future, only the wrapper file changes

**Alternative considered:** Direct import from System A in every consumer module. Rejected — scatters cross-package imports throughout the codebase and makes future divergence harder.

---

## 3. Specification

### 3.1 Sensor (`sensor.py`)

The Von Neumann neighborhood sensor is identical.

```python
"""System A+W sensor -- re-exports System A's Von Neumann sensor."""

from axis.systems.system_a.sensor import SystemASensor

# System A+W uses the same sensor as System A.
# The observation model is unchanged (Model Section 1.1):
#   u_t = S(world_view, position)
# producing a 10-dimensional Observation vector.

SystemAWSensor = SystemASensor

__all__ = ["SystemAWSensor"]
```

**Usage in System A+W:** The orchestrator (WP-10) instantiates `SystemAWSensor()` exactly as System A instantiates `SystemASensor()`. The sensor receives `world_view` and `position` from the framework's `observe()` call and produces an `Observation`.

**Note on position:** The sensor receives the agent's absolute position from the framework (via the `observe(world_view, position)` call). This is the framework providing the observation — the sensor is a passive transducer. The **agent** does not store or reason about this position. The sensor's output (`Observation`) contains no coordinate information. This is identical to how System A works.

### 3.2 Memory (`observation_buffer.py`)

The FIFO episodic memory update is identical.

```python
"""System A+W memory -- re-exports System A's memory update."""

from axis.systems.system_a.memory import update_observation_buffer

# System A+W uses the same memory update as System A.
# m_{t+1} = M(m_t, u_{t+1})
# FIFO bounded buffer with configurable capacity k.

__all__ = ["update_observation_buffer"]
```

**Usage in System A+W:** Called during the transition phase (WP-9) to append the new observation to the memory buffer. The memory buffer is also read by the curiosity drive (WP-6) for sensory novelty computation.

**Note on memory capacity:** Memory capacity $k$ is a configurable parameter in `AgentConfig.buffer_capacity`. There is no fixed limit — it can be set to any positive integer. For large $k$, the sensory novelty computation (averaging over all entries) becomes a longer sum, but the computational cost is negligible for typical values.

### 3.3 Consume Action (`actions.py`)

The consume action handler is identical.

```python
"""System A+W consume action -- re-exports System A's consume handler."""

from axis.systems.system_a.actions import handle_consume

# System A+W uses the same consume handler as System A.
# The energy dynamics are unchanged (Model Section 1.1).

__all__ = ["handle_consume"]
```

**Usage in System A+W:** Registered with the framework's action registry via `action_handlers()` in the orchestrator (WP-10). The handler extracts resource from the agent's current cell using `world.extract_resource()`, respecting `max_consume`.

---

## 4. What Is NOT Inherited

The following System A components are **not** re-exported because they are replaced or extended in System A+W:

| Component | System A module | System A+W status | Reason |
|---|---|---|---|
| `SystemAHungerDrive` | `drive.py` | Wrapped (WP-5) | Same logic, but must produce output compatible with the arbitration layer |
| `SystemAPolicy` | `policy.py` | Reused (WP-8) | Reused directly, but handled separately — it receives combined scores from arbitration, not single-drive contributions |
| `SystemATransition` | `transition.py` | Replaced (WP-9) | Extended with dead reckoning and world model update phases |
| `SystemA` | `system.py` | Replaced (WP-10) | New orchestrator wiring two drives + arbitration + world model |
| `SystemAVisualizationAdapter` | `visualization.py` | Replaced (WP-12) | Extended with curiosity and world model visualization panels |

---

## 5. Compatibility Verification

The inherited components must work with the new types from WP-2. Key compatibility points:

### 5.1 Sensor + Observation

`SystemASensor.observe()` returns an `Observation` (from `axis.systems.system_a.types`). This type is used unchanged in System A+W. No compatibility issue.

### 5.2 Memory + ObservationBuffer

`update_observation_buffer()` operates on `ObservationBuffer` (from `axis.systems.system_a.types`). System A+W's `AgentStateAW` contains a `observation_buffer: ObservationBuffer` field with the same type. No compatibility issue.

### 5.3 Consume + ActionOutcome

`handle_consume()` receives a `MutableWorldProtocol` and returns an `ActionOutcome`. Both are SDK types, independent of the system. No compatibility issue.

### 5.4 Consume + AgentStateAW

`handle_consume()` does not access agent state — it operates only on the world. The energy gain from consumption is applied during the transition phase (WP-9), which reads `action_outcome.data["resource_consumed"]`. No compatibility issue.

---

## 6. Test Plan

### File: `tests/systems/system_aw/test_inherited.py`

The tests verify that the inherited components work correctly **in the System A+W context** (with `AgentStateAW`, `WorldModelState`, etc.).

| # | Test | Description |
|---|---|---|
| 1 | `test_sensor_produces_observation` | `SystemAWSensor().observe(world_view, position)` returns a valid 10-dimensional `Observation` |
| 2 | `test_sensor_out_of_bounds` | Out-of-bounds neighbors return `(traversability=0.0, resource=0.0)` |
| 3 | `test_sensor_is_system_a_sensor` | `SystemAWSensor is SystemASensor` — confirms identity, not copy |
| 4 | `test_memory_update_appends` | `update_observation_buffer(state, observation, timestep)` appends entry correctly |
| 5 | `test_memory_update_fifo_overflow` | When at capacity, oldest entry is dropped |
| 6 | `test_memory_update_with_agent_state_aw` | Extract `observation_buffer` from `AgentStateAW`, update, verify new state |
| 7 | `test_consume_handler_extracts_resource` | `handle_consume(world, context={"max_consume": 1.0})` returns `ActionOutcome` with correct `resource_consumed` |
| 8 | `test_consume_handler_respects_max` | Extraction capped at `max_consume` |
| 9 | `test_consume_handler_empty_cell` | On empty cell, `resource_consumed = 0.0` |
| 10 | `test_imports_accessible` | `from axis.systems.system_aw.sensor import SystemAWSensor` succeeds |
| 11 | `test_imports_accessible_memory` | `from axis.systems.system_aw.memory import update_observation_buffer` succeeds |
| 12 | `test_imports_accessible_actions` | `from axis.systems.system_aw.actions import handle_consume` succeeds |

---

## 7. Acceptance Criteria

- [ ] `SystemAWSensor` produces observations identical to `SystemASensor`
- [ ] `update_observation_buffer` works with `ObservationBuffer` extracted from `AgentStateAW`
- [ ] `handle_consume` works unchanged as a registered action handler
- [ ] All three modules are importable from `axis.systems.system_aw.*`
- [ ] No System A source code is copied — only imported and re-exported
- [ ] All 12 tests pass

---

## 8. Notes for Implementer

1. **Create `src/axis/systems/system_aw/__init__.py`** as part of this WP (or WP-1 — whichever runs first). It should be minimal at this stage:
   ```python
   """System A+W -- dual-drive agent with curiosity and world model."""
   ```
   Exports will be added incrementally as later WPs produce the orchestrator and config.

2. **Create `tests/systems/system_aw/__init__.py`** as an empty package marker.

3. The sensor, memory, and actions modules are thin (3-5 lines each). The value of this WP is not in the code volume but in **establishing the import pattern** and **verifying compatibility** with the new type vocabulary.
