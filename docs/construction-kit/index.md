# System Construction Kit

The **System Construction Kit** provides tested, reusable building blocks
for composing agent systems within the AXIS framework. Instead of
implementing every component from scratch, system authors can select
and compose kit components -- sensors, drives, policies, arbitration
logic, energy utilities, and memory structures -- to assemble a working
agent pipeline.

The kit uses **composition, not inheritance**. Each component is a plain
Python class or function. Systems instantiate kit components in their
constructor and wire them together in `decide()` and `transition()`.
The framework never sees the kit -- it only sees `SystemInterface`.

**Import path:** `from axis.systems.construction_kit.<package>.<module> import ...`

**Source:** `src/axis/systems/construction_kit/`

---

## Component Catalog

| Package | Key Exports | Description |
|---------|------------|-------------|
| [Observation](observation.md) | `VonNeumannSensor`, `CellObservation`, `Observation` | 5-cell Von Neumann sensor and observation data types |
| [Drives](drives.md) | `HungerDrive`, `CuriosityDrive`, `HungerDriveOutput`, `CuriosityDriveOutput` | Drive implementations with activation + per-action scoring |
| [Policy](policy.md) | `SoftmaxPolicy` | Softmax action selection with admissibility masking |
| [Arbitration](arbitration.md) | `compute_maslow_weights`, `combine_drive_scores`, `DriveWeights` | Multi-drive weight computation and score combination |
| [Energy](energy.md) | `clip_energy`, `compute_vitality`, `check_energy_termination`, `get_action_cost` | Energy clamping, vitality, termination, action costs |
| [Memory](memory.md) | `ObservationBuffer`, `WorldModelState`, `update_observation_buffer`, `create_world_model`, `update_world_model` | FIFO observation buffer and spatial visit-count world model |
| [Types](types.md) | `AgentConfig`, `PolicyConfig`, `TransitionConfig`, `handle_consume` | Shared config models and consume action handler |

### Phase 2 (planned)

| Package | Purpose |
|---------|---------|
| `prediction` | Predictive memory and prediction error processing |
| `traces` | Trace dynamics and bounded accumulation |
| `modulation` | Action score modulation functions |

---

## Dependency Rules

The construction kit has strict architectural boundaries, enforced by
automated tests:

```
SDK (axis.sdk)
  ^
  |  imports from
  |
Construction Kit (axis.systems.construction_kit)
  ^
  |  imports from
  |
Concrete Systems (axis.systems.system_a, system_aw, ...)
```

- Kit components import **only** from the SDK and from other kit modules.
- Kit components **never** import from: the framework (`axis.framework`),
  the world (`axis.world`), or any concrete system (`axis.systems.system_*`).
- Concrete systems import from the kit and from the SDK, but **never
  from each other**.

These constraints are verified by 7 automated tests in
`tests/systems/construction_kit/test_dependency_constraints.py`.

---

## Which Systems Use Which Components?

| Component | System A | System A+W | System B |
|-----------|:--------:|:----------:|:--------:|
| `VonNeumannSensor` | yes | yes | -- |
| `HungerDrive` | yes | yes | -- |
| `CuriosityDrive` | -- | yes | -- |
| `SoftmaxPolicy` | yes | yes | -- |
| `compute_maslow_weights` | -- | yes | -- |
| `combine_drive_scores` | -- | yes | -- |
| `ObservationBuffer` | yes | yes | -- |
| `WorldModelState` | -- | yes | -- |
| `clip_energy` | yes | yes | -- |
| `AgentConfig` | yes | yes | -- |
| `PolicyConfig` | yes | yes | -- |
| `TransitionConfig` | yes | yes | -- |
| `handle_consume` | yes | yes | -- |

System B implements its own sensor, policy, and action handler (scan),
and does not use any kit components.

---

## See Also

- [System Developer Manual -- Section 10a](../manuals/system-dev-manual.md#10a-the-system-construction-kit)
  -- brief overview of when and how to use the kit
- [Building a System Tutorial](../tutorials/building-a-system.md)
  -- step-by-step tutorial building System A (shows what each component does)
- [System A Formal Specification](../system-design/system-a/01_System A Baseline.md)
  -- mathematical model behind the hunger drive, policy, and energy system
- [System A+W Formal Model](../system-design/system-a+w/01_System A+W Model.md)
  -- mathematical model behind curiosity, world model, and arbitration
