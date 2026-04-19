# AXIS System Construction Kit -- Specification

**Version**: 0.1.0 (draft)
**Status**: Proposed
**Date**: 2026-04-15
**Predecessor**: [System Construction Kit Draft](system-construction-kit-draft.md)
**Baseline**: AXIS v0.2.x (modular framework with System A, System AW, System B)

---

## 1. Purpose and Scope

This document formalizes the System Construction Kit as an architectural extension of AXIS v0.2.x. It serves as:

1. the **foundation for deriving work packages**,
2. the **specification of architectural changes and extensions** required,
3. and the **identification of first concrete component extractions** with guidance on how to perform them.

This is not an implementation plan. It defines *what* is being built and *where* it fits. Work packages will later define *how*, *when*, and in what order.

---

## 2. Motivation from Current Codebase

### 2.1 Cross-System Dependencies Today

The AXIS v0.2.x codebase already exhibits concrete cross-system dependencies:

| Consumed by System AW from System A | File |
|------|------|
| `Observation`, `CellObservation`, `ObservationBuffer`, `BufferEntry`, `HungerDriveOutput`, `clip_energy` | `system_a/types.py` |
| `SystemASensor` (aliased as `SystemAWSensor`) | `system_a/sensor.py` |
| `SystemAHungerDrive` (wrapped in `SystemAWHungerDrive`) | `system_a/drive.py` |
| `SystemAPolicy` (delegated to by `SystemAWPolicy`) | `system_a/policy.py` |
| `update_observation_buffer` | `system_a/observation_buffer.py` (re-exported via `system_aw/observation_buffer.py`) |

This means **System AW already depends on System A** for types, sensor, drive, policy, and buffer logic. These are not System A-specific mechanisms -- they are shared mechanisms that happen to live inside System A because System A was built first.

### 2.2 Duplicated Patterns Across Systems

| Pattern | System A | System AW | System B |
|---------|----------|-----------|----------|
| Energy clipping to `[0, max]` | `clip_energy()` in types.py | Imports from System A | `max(0.0, min(...))` inline |
| Action cost lookup | `_get_action_cost()` in transition.py | Identical copy | Inline if/elif chain |
| Vitality computation | `energy / max_energy` | `energy / max_energy` | `energy / max_energy` |
| Softmax with admissibility mask | `SystemAPolicy._softmax()` | Delegates to System A | Inline softmax |
| Energy-based termination check | `energy <= 0.0` in transition | Identical copy | `energy <= 0.0` in transition |
| Observation buffer FIFO update | `update_observation_buffer()` | Imports from System A | N/A |

### 2.3 Components That Are Not System-Specific

Several mechanisms currently placed inside System A are conceptually general:

- **Von Neumann neighborhood sensor**: Produces `Observation` from any `WorldView`. Not specific to hunger or System A's decision logic.
- **Softmax policy with admissibility masking**: A general action selection method. Not tied to any specific drive structure.
- **Hunger drive**: Computes activation from an `energy` attribute and action contributions from directional resource observations. Any energy-managing system could use it.
- **Drive arbitration**: The weighted score combination in System AW (`w_H * d_H * phi_H + w_C * d_C * phi_C`) is a general multi-drive pattern.
- **Observation buffer**: Bounded FIFO with immutable entries. No System A semantics.

### 2.4 Anticipated Needs (System C and Beyond)

System C is planned to introduce prediction-based behavior. Based on the draft design, it will require mechanisms that do not yet exist in code but follow identifiable patterns:

- **Predictive memory**: Context-conditioned expectation storage and retrieval
- **Prediction error processing**: Signed mismatch between expected and observed outcomes
- **Predictive trace dynamics**: Frustration, confidence, and reliability traces driven by prediction error
- **Action modulation**: Score adjustments based on learned traces

These mechanisms are candidates for the construction kit from inception, rather than being built inside System C and extracted later.

---

## 3. Core Concept

### 3.1 Definition

The System Construction Kit is a **library of reusable, system-internal building blocks** for composing agent architectures within the AXIS framework.

It is:

- a design and implementation layer for reusable cognitive and decision components
- positioned between the SDK contracts and concrete system implementations
- entirely on the **system side** of the architecture -- it does not extend or modify the framework

It is not:

- a replacement for `SystemInterface`
- a second framework or execution layer
- a plugin system
- a mandatory base for all systems

### 3.2 Architectural Position

The AXIS v0.2.x layering becomes:

```text
sdk/                              Contract interfaces, replay/base types
framework/                        Execution, persistence, experiment orchestration
world/                            World models, dynamics, action handlers, world views
systems/construction_kit/         Reusable system-internal building blocks
systems/system_a/                 Concrete system: hunger-driven baseline
systems/system_aw/                Concrete system: dual-drive with world model
systems/system_b/                 Concrete system: scout with scan
systems/system_c/                 (future) Concrete system: predictive agent
```

Dependency direction:

```text
construction_kit  -->  sdk (types only, no framework imports)
system_a          -->  sdk, construction_kit
system_aw         -->  sdk, construction_kit
system_b          -->  sdk, construction_kit (optional -- only the utilities it needs)
system_c          -->  sdk, construction_kit
```

The construction kit MUST NOT depend on:

- `axis.framework` (execution, persistence, registry, config resolution)
- `axis.world` (world model, dynamics, factories)
- any concrete system (`system_a`, `system_aw`, `system_b`)

The construction kit MAY depend on:

- `axis.sdk.types` (DecideResult, TransitionResult, PolicyResult)
- `axis.sdk.position` (Position)
- `axis.sdk.world_types` (WorldView, ActionOutcome -- read-only protocols)
- `axis.sdk.actions` (MOVEMENT_DELTAS, STAY -- action constants)
- Standard library and `pydantic`, `numpy` (existing project dependencies)

### 3.3 Reuse Model

Systems use the construction kit by **composition**, not inheritance.

A concrete system:

1. selects the components it needs
2. wires them into its own `decide()` and `transition()` flow
3. exposes only `SystemInterface` at the framework boundary

The framework sees a system. The system internally sees a composition of reusable parts.

Systems are free to use none, some, or all of the construction kit. No component is mandatory. Systems may also implement their own versions of any mechanism if they need different semantics.

---

## 4. Package Structure

### 4.1 Top-Level Layout

```text
src/axis/systems/construction_kit/
    __init__.py
    observation/
    drives/
    policy/
    arbitration/
    energy/
    memory/
    prediction/
    traces/
    modulation/
    types/
```

### 4.2 Component Family Descriptions

#### 4.2.1 `observation/` -- Observation and Feature Extraction

Reusable observation types, sensor implementations, and feature extraction helpers.

Responsibilities:

- Shared observation data structures (`CellObservation`, `Observation`)
- Von Neumann neighborhood sensor
- Observation-to-feature projection helpers (for future feature extraction variants)

Current extraction source: `system_a/types.py` (observation types), `system_a/sensor.py`

#### 4.2.2 `drives/` -- Drive Primitives

Reusable drive implementations and drive output types.

Responsibilities:

- Hunger drive (activation from energy state, action contributions from resource observations)
- Curiosity drive (novelty-based activation, spatial and sensory novelty, action contributions)
- Drive output types (`HungerDriveOutput`, `CuriosityDriveOutput`)
- Drive activation functions usable across systems

Current extraction source: `system_a/drive.py`, `system_a/types.py` (HungerDriveOutput), `system_aw/drive_curiosity.py`, `system_aw/types.py` (CuriosityDriveOutput)

#### 4.2.3 `policy/` -- Action Selection

Reusable policy implementations and selection primitives.

Responsibilities:

- Softmax action selection with admissibility masking
- Argmax/sample selection modes
- Admissibility mask computation from observations
- Generic action scoring utilities

Current extraction source: `system_a/policy.py`

#### 4.2.4 `arbitration/` -- Multi-Drive Score Combination

Reusable mechanisms for combining action scores from multiple drives.

Responsibilities:

- Weighted drive combination
- Dynamic weight computation (e.g., Maslow-like gating)
- Score aggregation functions

Current extraction source: `system_aw/drive_arbitration.py`

#### 4.2.5 `energy/` -- Energy Management Utilities

Reusable energy computation functions shared across all energy-based systems.

Responsibilities:

- Energy clipping (`clip_energy`)
- Vitality computation (energy / max_energy)
- Action cost lookup (action -> cost mapping)
- Energy-based termination check

Current extraction source: `system_a/types.py` (`clip_energy`), pattern analysis across all three systems

#### 4.2.6 `memory/` -- Bounded Memory Structures

Reusable bounded memory containers, update functions, and spatial memory models.

Responsibilities:

- Observation buffer types (`BufferEntry`, `ObservationBuffer`)
- FIFO buffer update function
- Spatial world model (`WorldModelState`, dead reckoning, visit-count tracking)
- Spatial novelty computation (per-direction novelty from visit counts)
- Generic bounded-buffer utilities (future: exponential moving averages, finite-buffer updates)

Current extraction source: `system_a/types.py` (buffer types), `system_a/observation_buffer.py`, `system_aw/types.py` (WorldModelState), `system_aw/world_model.py`

#### 4.2.7 `prediction/` -- Predictive Memory and Error Processing

Reusable prediction mechanisms for systems that maintain expectations about outcomes. This family has no existing code -- it is specified for System C and future predictive systems.

Responsibilities:

- Context encoding for expectation storage
- Expectation storage and retrieval (context-conditioned tables)
- Signed prediction error computation (positive surprise, disappointment)
- Per-feature error aggregation
- Drive-facing error summaries

Anticipated components:

- `PredictiveMemory`: Context-action expectation table with bounded storage
- `PredictionError`: Signed mismatch computation between expected and observed feature vectors
- `ExpectationUpdateRule`: Update rule for adjusting stored expectations after outcomes

Design constraints:

- Predictive memory must be immutable (new instance on update, like all AXIS state)
- Prediction error must be decomposed into signed components (positive and negative)
- All state must be serializable for trace data

#### 4.2.8 `traces/` -- Predictive Trace Dynamics

Reusable trace accumulation mechanisms driven by prediction error or other learning signals.

Responsibilities:

- Frustration traces (accumulated negative prediction error)
- Confidence traces (accumulated positive prediction error)
- Reliability traces (error magnitude tracking)
- Bounded decay dynamics
- Saturating accumulation

Anticipated components:

- `DecayTrace`: Exponentially decaying trace with bounded accumulation
- `BoundedAccumulator`: Saturating accumulation with configurable ceiling and floor
- `TraceUpdate`: Pure function mapping (current_trace, new_signal) -> updated_trace

Design constraints:

- All trace types must be immutable frozen models
- Decay and accumulation parameters must be explicit (no hidden state)
- Trace values must be bounded to prevent unbounded growth

#### 4.2.9 `modulation/` -- Action Score Modulation

Reusable functions for modulating action scores based on learned traces or predictive summaries.

Responsibilities:

- Multiplicative confidence damping
- Additive risk penalties
- Bounded positive reinforcement
- Clipped exponential modulation

Anticipated components:

- `multiplicative_damping(score, confidence, floor)`: Scale action score by confidence trace
- `additive_penalty(score, frustration, weight)`: Penalize actions proportional to frustration
- `bounded_reinforcement(score, signal, ceiling)`: Boost score with upper bound

Design constraints:

- All modulation functions must be pure functions
- Modulation must be per-action, not global
- Output scores must remain finite (no unbounded amplification)

#### 4.2.10 `types/` -- Shared Internal Data Structures

Cross-cutting type definitions needed by multiple component families.

Responsibilities:

- Action ordering constants
- Shared type aliases
- Common base structures if needed

This is intentionally minimal. Most types belong to their component family (e.g., `HungerDriveOutput` in `drives/`, `ObservationBuffer` in `memory/`). The `types/` module exists only for definitions that span multiple families.

---

## 5. Dependency Constraints

### 5.1 Allowed Dependencies

```text
construction_kit/observation  -->  sdk.position, sdk.world_types
construction_kit/drives       -->  construction_kit/observation (observation types)
                                   construction_kit/memory (WorldModelState, ObservationBuffer for curiosity drive)
construction_kit/policy       -->  construction_kit/observation (for admissibility)
                                   sdk.types (PolicyResult)
construction_kit/arbitration  -->  construction_kit/drives (drive output types)
                                   (pure functions with raw parameters, no config types)
construction_kit/energy       -->  sdk.actions (MOVEMENT_DELTAS, STAY)
construction_kit/memory       -->  construction_kit/observation (observation types for buffer)
construction_kit/prediction   -->  (standalone, types only)
construction_kit/traces       -->  (standalone, types only)
construction_kit/modulation   -->  (standalone pure functions)
construction_kit/types        -->  (standalone)
```

### 5.2 Forbidden Dependencies

No module in `construction_kit/` may import from:

- `axis.framework.*`
- `axis.world.*` (except through `sdk.world_types` protocols)
- `axis.systems.system_a.*`
- `axis.systems.system_aw.*`
- `axis.systems.system_b.*`
- Any concrete system implementation

### 5.3 Internal Dependency Rule

Component families within the construction kit should minimize cross-dependencies. When a cross-dependency exists, it must be unidirectional and documented.

Circular dependencies between component families are forbidden.

---

## 6. Engineering Constraints

The construction kit inherits all AXIS v0.2.x architectural values:

1. **Deterministic behavior**: Given the same inputs, a component must always produce the same outputs.
2. **Immutable state models**: All data structures are frozen Pydantic models. State transitions produce new instances, never mutation.
3. **Explicit data flow**: No hidden global state, no singletons, no implicit context.
4. **Traceability**: Component outputs must be representable in trace data for debugging and replay.
5. **Local interpretability**: Each component's behavior must be understandable in isolation.

Additional construction kit constraints:

6. **No framework dependency**: Components must not import from or depend on the execution framework.
7. **No world mutation**: Components must never modify world state. They read via `WorldView` and receive results via `ActionOutcome`.
8. **No SystemInterface bypass**: Components are internal building blocks. They do not implement or replace `SystemInterface`.
9. **Pure functions preferred**: Where possible, component logic should be implemented as pure functions. Classes are acceptable when they hold configuration but should not hold mutable state.
10. **Composition over inheritance**: Systems compose components by calling them in their `decide()` and `transition()` flows. No inheritance hierarchies between components.

---

## 7. First Extraction Phase: Existing Components

This section identifies the components that can be extracted from the current codebase immediately. These are mechanisms that are already shared between systems or are clearly not system-specific.

### 7.1 Observation Types and Sensor

**What moves:**

| Current location | Target location |
|-----------------|----------------|
| `system_a/types.py :: CellObservation` | `construction_kit/observation/types.py` |
| `system_a/types.py :: Observation` | `construction_kit/observation/types.py` |
| `system_a/sensor.py :: SystemASensor` | `construction_kit/observation/sensor.py` (renamed: `VonNeumannSensor`) |

**Impact on existing systems:**

- System A: update imports, `SystemASensor` references become `VonNeumannSensor`
- System AW: update imports, remove `system_aw/sensor.py` alias file entirely (it only re-exported System A's sensor)
- System B: no impact (System B does not use these types)

**Extraction approach:**

1. Create `construction_kit/observation/types.py` with `CellObservation` and `Observation` -- exact copies, no behavioral changes.
2. Create `construction_kit/observation/sensor.py` with `VonNeumannSensor` -- exact copy of `SystemASensor`, renamed.
3. Update all imports in System A and System AW.
4. Delete `system_aw/sensor.py` (was only a re-export).
5. Remove `CellObservation` and `Observation` from `system_a/types.py`.
6. Verify all tests pass unchanged (pure move, no behavioral change).

### 7.2 Observation Buffer

**What moves:**

| Current location | Target location |
|-----------------|----------------|
| `system_a/types.py :: BufferEntry` | `construction_kit/memory/types.py` |
| `system_a/types.py :: ObservationBuffer` | `construction_kit/memory/types.py` |
| `system_a/observation_buffer.py :: update_observation_buffer` | `construction_kit/memory/observation_buffer.py` |

**Impact on existing systems:**

- System A: update imports in `types.py`, `transition.py`
- System AW: update imports in `types.py`, `transition.py`, `drive_curiosity.py`
- System B: no impact

**Extraction approach:**

1. Create `construction_kit/memory/types.py` with `BufferEntry` and `ObservationBuffer`.
2. Create `construction_kit/memory/observation_buffer.py` with `update_observation_buffer`.
3. `ObservationBuffer` depends on `BufferEntry` which depends on `Observation` -- the `Observation` import will come from `construction_kit/observation/types.py` (extraction 7.1 must happen first or concurrently).
4. Update all imports in System A and System AW.
5. Delete `system_a/observation_buffer.py`.
6. Delete `system_aw/observation_buffer.py` (was only a re-export of System A's function).
7. Remove `BufferEntry` and `ObservationBuffer` from `system_a/types.py`.

### 7.3 Energy Utilities

**What moves:**

| Current location | Target location |
|-----------------|----------------|
| `system_a/types.py :: clip_energy` | `construction_kit/energy/functions.py` |
| (new) | `construction_kit/energy/functions.py :: compute_vitality` |
| (new) | `construction_kit/energy/functions.py :: check_energy_termination` |
| (new) | `construction_kit/energy/functions.py :: get_action_cost` |

**What is new (distilled from patterns):**

```python
def compute_vitality(energy: float, max_energy: float) -> float:
    """Normalized vitality in [0.0, 1.0]."""
    return energy / max_energy

def check_energy_termination(energy: float) -> tuple[bool, str | None]:
    """Check if energy depletion terminates the episode."""
    terminated = energy <= 0.0
    return terminated, "energy_depleted" if terminated else None

def get_action_cost(
    action: str,
    *,
    move_cost: float,
    consume_cost: float,
    stay_cost: float,
    custom_costs: dict[str, float] | None = None,
) -> float:
    """Return the energy cost for a given action."""
    ...
```

**Impact on existing systems:**

- System A: use `clip_energy` from kit, optionally use `compute_vitality` and `get_action_cost`
- System AW: use `clip_energy` from kit, optionally use `compute_vitality` and `get_action_cost`
- System B: can use `compute_vitality`, `check_energy_termination`, `get_action_cost` (with `scan_cost` via custom_costs)

**Extraction approach:**

1. Create `construction_kit/energy/functions.py` with `clip_energy` (exact copy) plus new utility functions.
2. New functions (`compute_vitality`, `check_energy_termination`, `get_action_cost`) are distilled from repeated patterns -- not extracted from a single location.
3. Adoption is optional. Systems may use these or keep inline implementations.
4. Remove `clip_energy` from `system_a/types.py`, update imports.

### 7.4 Hunger Drive

**What moves:**

| Current location | Target location |
|-----------------|----------------|
| `system_a/types.py :: HungerDriveOutput` | `construction_kit/drives/types.py` |
| `system_a/drive.py :: SystemAHungerDrive` | `construction_kit/drives/hunger.py` (renamed: `HungerDrive`) |

**Impact on existing systems:**

- System A: update imports, `SystemAHungerDrive` becomes `HungerDrive`
- System AW: update imports, delete `system_aw/drive_hunger.py` entirely (it was only a delegation wrapper). Use `HungerDrive` directly.
- System B: no impact

**Extraction approach:**

1. Create `construction_kit/drives/types.py` with `HungerDriveOutput`.
2. Create `construction_kit/drives/hunger.py` with `HungerDrive` -- exact copy of `SystemAHungerDrive`, renamed.
3. `HungerDrive.compute()` reads `.energy` from agent_state via duck typing (current behavior) -- no change needed.
4. Update all imports in System A and System AW.
5. Delete `system_aw/drive_hunger.py`.
6. Remove `HungerDriveOutput` from `system_a/types.py`, delete `system_a/drive.py`.

### 7.5 Softmax Policy

**What moves:**

| Current location | Target location |
|-----------------|----------------|
| `system_a/policy.py :: SystemAPolicy` | `construction_kit/policy/softmax.py` (renamed: `SoftmaxPolicy`) |

**Design refinement:**

The current `SystemAPolicy` takes `HungerDriveOutput` as its `drive_outputs` parameter. `SystemAWPolicy` works around this by wrapping `SystemAPolicy` and passing pre-computed score tuples.

The extracted `SoftmaxPolicy` should accept a **generic action score tuple** and an `Observation` for admissibility masking. This aligns with how System AW already uses it and makes the policy truly drive-agnostic.

```python
class SoftmaxPolicy:
    def select(
        self,
        action_scores: tuple[float, ...],
        observation: Observation,
        rng: np.random.Generator,
    ) -> PolicyResult:
        ...
```

System A will need to compute its action scores from `HungerDriveOutput.action_contributions` before calling `SoftmaxPolicy.select()`. This is a minor wiring change in `SystemA.decide()`.

**Impact on existing systems:**

- System A: minor change in `decide()` to pass `drive_output.action_contributions` as `action_scores`. Delete `system_a/policy.py`.
- System AW: simplify significantly. Delete `system_aw/policy.py`, use `SoftmaxPolicy` directly. No more delegation wrapper.
- System B: can optionally adopt in the future (currently uses inline softmax)

**Extraction approach:**

1. Create `construction_kit/policy/softmax.py` with `SoftmaxPolicy` that accepts generic score tuples.
2. Admissibility masking and softmax logic are exact copies of `SystemAPolicy`.
3. Interface change: `drive_outputs: HungerDriveOutput` becomes `action_scores: tuple[float, ...]`.
4. Update System A `decide()` to extract scores before calling policy.
5. Update System AW to use `SoftmaxPolicy` directly, remove delegation wrapper.
6. Delete `system_a/policy.py` and `system_aw/policy.py`.

### 7.6 Drive Arbitration

**What moves:**

| Current location | Target location |
|-----------------|----------------|
| `system_aw/drive_arbitration.py :: compute_drive_weights` | `construction_kit/arbitration/weights.py` |
| `system_aw/drive_arbitration.py :: compute_action_scores` | `construction_kit/arbitration/scoring.py` |
| `system_aw/types.py :: DriveWeights` | `construction_kit/arbitration/types.py` |

**Design refinement:**

The current `compute_action_scores` is hardcoded for exactly two drives. The extracted version should support N drives:

```python
def combine_drive_scores(
    drive_contributions: Sequence[tuple[float, ...]],
    drive_activations: Sequence[float],
    drive_weights: Sequence[float],
) -> tuple[float, ...]:
    """Weighted combination of N drive score vectors."""
    ...
```

The current 2-drive version becomes the specific case where `len(drive_contributions) == 2`.

The current `compute_drive_weights` takes an `ArbitrationConfig` object (from `system_aw/config.py`). The extracted version must accept raw parameters instead, removing the dependency on a system-specific config type:

```python
def compute_maslow_weights(
    primary_activation: float,
    *,
    primary_weight_base: float,
    secondary_weight_base: float,
    gating_sharpness: float,
) -> DriveWeights:
    """Maslow-like hierarchy: primary drive gates secondary drive."""
    ...
```

System AW passes its `ArbitrationConfig` values as individual arguments at the call site. The construction kit function is a pure function with no config-type dependency.

**Impact on existing systems:**

- System AW: update imports, adapt `decide()` to use the generalized interface, pass config values as individual arguments
- System A: no impact (single drive, no arbitration needed)

**Extraction approach:**

1. Create `construction_kit/arbitration/types.py` with `DriveWeights`.
2. Create `construction_kit/arbitration/weights.py` with `compute_maslow_weights` (adapted from System AW's `compute_drive_weights`, raw parameters instead of config object).
3. Create `construction_kit/arbitration/scoring.py` with the generalized `combine_drive_scores`.
4. Verify the generalized version produces identical results for the 2-drive case.
5. Update System AW imports and call site. Delete `system_aw/drive_arbitration.py`.

### 7.7 Curiosity Drive and Spatial World Model

**What moves:**

| Current location | Target location |
|-----------------|----------------|
| `system_aw/types.py :: CuriosityDriveOutput` | `construction_kit/drives/types.py` |
| `system_aw/types.py :: WorldModelState` | `construction_kit/memory/types.py` |
| `system_aw/drive_curiosity.py` (full module) | `construction_kit/drives/curiosity.py` (renamed: `CuriosityDrive`) |
| `system_aw/world_model.py` (full module) | `construction_kit/memory/world_model.py` |

The `CuriosityDriveOutput` type is a general drive output structure (activation + action contributions + diagnostic novelty signals). It belongs in the kit alongside `HungerDriveOutput`.

The `WorldModelState` is a reusable spatial memory structure based on dead reckoning and visit counts. It is not specific to System AW's goals -- any system that needs spatial novelty or visit-count memory can use it. It belongs in the kit's `memory/` package alongside the observation buffer.

The curiosity drive implementation (novelty computation pipeline, spatial/sensory/composite novelty, saturation, activation) is a reusable drive mechanism. It depends on `WorldModelState`, `ObservationBuffer`, and `Observation` -- all of which are in the construction kit after earlier extractions.

The world model module (dead reckoning, visit-count tracking, spatial novelty functions) is a reusable spatial memory mechanism. The curiosity drive depends on it, and the transition function uses its update logic.

**Impact on existing systems:**

- System AW: update all imports. Delete `drive_curiosity.py` and `world_model.py`. Use kit components directly. `SystemAW.decide()` calls `CuriosityDrive` from kit. `SystemAWTransition` calls `update_world_model` and `create_world_model` from kit.
- System A: no impact
- System B: no impact

**Extraction approach:**

1. Add `WorldModelState` to `construction_kit/memory/types.py` (alongside `BufferEntry`, `ObservationBuffer`).
2. Create `construction_kit/memory/world_model.py` with all functions from `system_aw/world_model.py`: `create_world_model`, `update_world_model`, `get_visit_count`, `get_neighbor_position`, `spatial_novelty`, `all_spatial_novelties`, and direction constants.
3. Add `CuriosityDriveOutput` to `construction_kit/drives/types.py` (alongside `HungerDriveOutput`).
4. Create `construction_kit/drives/curiosity.py` with `CuriosityDrive` (renamed from `SystemAWCuriosityDrive`) and all supporting pure functions: `compute_spatial_novelty`, `compute_sensory_novelty`, `compute_composite_novelty`, `compute_novelty_saturation`, `compute_curiosity_activation`.
5. Update all internal imports to point to construction_kit locations.
6. Update System AW `system.py`, `transition.py`, `types.py`.
7. Delete `system_aw/drive_curiosity.py` and `system_aw/world_model.py`.
8. Remove `CuriosityDriveOutput` and `WorldModelState` from `system_aw/types.py`.
9. Verify all tests pass unchanged.

### 7.8 Extraction Summary

After all first-phase extractions, the construction kit will contain:

```text
construction_kit/
    __init__.py
    observation/
        __init__.py
        types.py          # CellObservation, Observation
        sensor.py         # VonNeumannSensor
    drives/
        __init__.py
        types.py          # HungerDriveOutput, CuriosityDriveOutput
        hunger.py         # HungerDrive
        curiosity.py      # CuriosityDrive, novelty computation functions
    policy/
        __init__.py
        softmax.py        # SoftmaxPolicy
    arbitration/
        __init__.py
        types.py          # DriveWeights
        weights.py        # compute_drive_weights
        scoring.py        # combine_drive_scores
    energy/
        __init__.py
        functions.py      # clip_energy, compute_vitality,
                          # check_energy_termination, get_action_cost
    memory/
        __init__.py
        types.py          # BufferEntry, ObservationBuffer, WorldModelState
        observation_buffer.py  # update_observation_buffer
        world_model.py    # create_world_model, update_world_model,
                          # spatial_novelty, all_spatial_novelties
    prediction/           # (empty -- prepared for System C)
        __init__.py
    traces/               # (empty -- prepared for System C)
        __init__.py
    modulation/           # (empty -- prepared for System C)
        __init__.py
    types/
        __init__.py       # Action ordering constants, shared type aliases
```

And the following files will be **deleted** from concrete systems:

- `system_a/drive.py` (moved to `construction_kit/drives/hunger.py`)
- `system_a/policy.py` (moved to `construction_kit/policy/softmax.py`)
- `system_a/observation_buffer.py` (moved to `construction_kit/memory/`)
- `system_aw/sensor.py` (was re-export, no longer needed)
- `system_aw/drive_hunger.py` (was delegation wrapper, no longer needed)
- `system_aw/drive_curiosity.py` (moved to `construction_kit/drives/curiosity.py`)
- `system_aw/policy.py` (was delegation wrapper, no longer needed)
- `system_aw/drive_arbitration.py` (moved to `construction_kit/arbitration/`)
- `system_aw/world_model.py` (moved to `construction_kit/memory/world_model.py`)
- `system_aw/observation_buffer.py` (was re-export, no longer needed)

---

## 8. Second Phase: Prediction Components (System C)

This section specifies the construction kit components anticipated for System C. These do not have existing code but follow the same design constraints.

### 8.1 Predictive Memory (`prediction/`)

**Purpose:** Store and retrieve context-conditioned expectations about outcomes.

**Core interface:**

```python
class PredictiveMemory:
    """Context-action expectation table with bounded storage."""

    def get_expectation(
        self,
        context: tuple,          # hashable context key
        action: str,
    ) -> tuple[float, ...] | None:
        """Retrieve expected feature vector for (context, action)."""
        ...

    def update(
        self,
        context: tuple,
        action: str,
        observed: tuple[float, ...],
        learning_rate: float,
    ) -> PredictiveMemory:
        """Update expectation toward observed features. Returns new instance."""
        ...
```

**Design constraints:**

- Context encoding is the caller's responsibility. The memory stores keyed expectations without interpreting the context semantics.
- Update returns a new immutable instance.
- Storage may be bounded (e.g., LRU eviction of stale context-action pairs).

### 8.2 Prediction Error (`prediction/`)

**Purpose:** Compute signed mismatch between expected and observed feature vectors.

**Core interface:**

```python
def compute_prediction_error(
    expected: tuple[float, ...],
    observed: tuple[float, ...],
) -> PredictionError:
    """Compute signed prediction error decomposition."""
    ...

class PredictionError:
    signed: tuple[float, ...]          # per-feature signed error (observed - expected)
    positive: tuple[float, ...]        # per-feature positive surprise (gains)
    negative: tuple[float, ...]        # per-feature disappointment (losses)
    magnitude: float                   # aggregate error magnitude
```

**Design constraints:**

- Signed decomposition: positive surprise and disappointment must be separated.
- Per-feature granularity: each feature dimension has its own error.
- Aggregate magnitude for drive-facing summaries.

### 8.3 Trace Dynamics (`traces/`)

**Purpose:** Convert prediction error signals into bounded, decaying action-history traces.

**Core interface:**

```python
class DecayTrace:
    """Exponentially decaying trace with bounded accumulation."""
    value: float
    decay_rate: float
    ceiling: float
    floor: float

def update_trace(
    trace: DecayTrace,
    signal: float,
) -> DecayTrace:
    """Apply decay, add signal, clamp to bounds. Returns new instance."""
    ...
```

**Trace families:**

- **Frustration trace**: Accumulates negative prediction error. Drives avoidance.
- **Confidence trace**: Accumulates positive prediction error. Drives exploitation.
- **Reliability trace**: Tracks prediction accuracy (low error -> high reliability).

Each family is a parameterized instance of the same `DecayTrace` mechanism with different signal sources and interpretation.

### 8.4 Action Modulation (`modulation/`)

**Purpose:** Map learned traces into per-action score adjustments.

**Core functions:**

```python
def multiplicative_damping(
    score: float, confidence: float, floor: float = 0.1,
) -> float:
    """Dampen score proportional to confidence. floor prevents zero-out."""
    ...

def additive_penalty(
    score: float, frustration: float, weight: float = 1.0,
) -> float:
    """Penalize score proportional to frustration trace."""
    ...

def bounded_reinforcement(
    score: float, signal: float, ceiling: float = 2.0,
) -> float:
    """Boost score with upper bound to prevent unbounded amplification."""
    ...
```

**Design constraints:**

- All functions are pure and per-action.
- Output scores must remain finite.
- Parameters are explicit, not hidden in class state.

---

## 9. Architectural Changes Required

### 9.1 No Framework Changes

The construction kit does not require any changes to:

- `axis.framework` (runner, experiment, persistence, registry, CLI)
- `axis.sdk` (interfaces, contracts, base types)
- `axis.world` (world models, dynamics, factories)

This is the key architectural property. The construction kit exists entirely within the `systems/` package.

### 9.2 System A Changes

System A's internal structure simplifies:

**Before:**

```text
system_a/
    system.py          # SystemA class
    config.py          # SystemAConfig
    types.py           # AgentState, Observation, HungerDriveOutput, ObservationBuffer, etc.
    sensor.py          # SystemASensor
    drive.py           # SystemAHungerDrive
    policy.py          # SystemAPolicy
    transition.py      # SystemATransition
    observation_buffer.py
    actions.py
    visualization.py
```

**After:**

```text
system_a/
    system.py          # SystemA class (updated imports, minor wiring change in decide)
    config.py          # SystemAConfig (unchanged)
    types.py           # AgentState only (Observation types, buffer types, drive types moved out)
    transition.py      # SystemATransition (updated imports; uses kit energy/memory functions)
    actions.py         # handle_consume (unchanged)
    visualization.py   # (unchanged)
```

`system_a/types.py` retains only `AgentState` (which is system-specific: it defines the particular combination of energy + observation_buffer that constitutes System A's state).

### 9.3 System AW Changes

System AW simplifies significantly:

**Before:**

```text
system_aw/
    system.py
    config.py
    types.py           # AgentStateAW, CuriosityDriveOutput, DriveWeights, WorldModelState
    sensor.py          # re-export of SystemASensor
    drive_hunger.py    # delegation wrapper
    drive_curiosity.py
    drive_arbitration.py
    policy.py          # delegation wrapper
    transition.py
    world_model.py
    actions.py
    observation_buffer.py  # re-export of system_a/observation_buffer.py
    visualization.py
```

**After:**

```text
system_aw/
    system.py          # SystemAW class (updated imports, uses kit components directly)
    config.py          # SystemAWConfig (unchanged)
    types.py           # AgentStateAW only
    transition.py      # (updated imports, uses kit energy/memory/world_model functions)
    actions.py         # (unchanged)
    visualization.py   # (unchanged)
```

Files deleted: `sensor.py`, `drive_hunger.py`, `drive_curiosity.py`, `policy.py`, `drive_arbitration.py`, `world_model.py`, `observation_buffer.py`.

### 9.4 System B Changes (Optional)

System B changes are optional. System B can remain fully self-contained. However, it may optionally adopt:

- `clip_energy` and `compute_vitality` from `energy/`
- `check_energy_termination` from `energy/`
- `get_action_cost` from `energy/` (with `scan_cost` via custom_costs)

This adoption reduces inline duplication but is not required for the construction kit to be correct.

### 9.5 Package Registration

The construction kit needs no registration. It is a library, not a system. It has no `system_type()`, no factory, no registry entry. Systems import from it directly.

### 9.6 Test Impact

- All existing behavioral tests must pass unchanged after extraction. The construction kit extraction is a pure structural refactoring -- no behavioral change.
- Construction kit components gain their own unit tests in a new test directory (e.g., `tests/unit/construction_kit/`).
- System-level integration tests remain attached to their systems.
- The construction kit test suite should include:
  - Unit tests for each component in isolation
  - Import-constraint tests verifying forbidden dependencies (no framework, no world, no concrete system imports)

---

## 10. Extraction Criteria

Not every shared pattern should be extracted into the construction kit. A mechanism is a candidate for extraction when **all** of the following are true:

1. **Conceptually stable**: The mechanism's semantics and interface are settled. It is not in active experimental flux.
2. **Multi-system utility**: It is used by (or clearly useful to) more than one concrete system.
3. **Not framework-owned**: It is a system-internal concern, not an execution or persistence concern.
4. **Clear interface boundary**: It has well-defined inputs and outputs that do not drag in a system's full internal structure.
5. **Separable identity**: It can be named and explained without referencing a specific system. "Hunger drive" is separable. "System A's special energy rebalancing hack" is not.

The prediction components (Section 8) are pre-specified because their conceptual design is stable even without existing code. However, they should still be validated against these criteria as they are implemented.

---

## 11. Non-Goals

The following are explicitly out of scope for the construction kit:

- **Framework modification**: No changes to execution, persistence, or registry.
- **SDK extension**: No new framework-level interfaces or contracts.
- **Mandatory adoption**: No system is forced to use any construction kit component.
- **Deep inheritance hierarchies**: No abstract base class trees. Composition only.
- **Dynamic component discovery**: No plugin system, no runtime component registration.
- **Performance optimization**: The construction kit prioritizes clarity and correctness.
- **Visualization components**: Visualization adapters remain system-specific. Shared visualization helpers, if needed, belong in `axis.visualization`, not in the construction kit.

---

## 12. Risks and Mitigations

### 12.1 Premature Abstraction

**Risk**: Extracting prediction/traces/modulation before they have concrete implementations may lead to interfaces that don't fit when System C is actually built.

**Mitigation**: The prediction components are specified as anticipated interfaces, not final APIs. They will be refined during System C implementation. Empty package directories are created to establish placement, but interfaces are not frozen until validated by at least one concrete system.

### 12.2 Over-Generalization

**Risk**: Making drive arbitration N-drive generic when only 2-drive exists may introduce complexity without proven benefit.

**Mitigation**: The generalized `combine_drive_scores` should remain simple (weighted sum loop). If the 2-drive case needs to stay as a separate fast-path, that is acceptable. Generalization should not add indirection.

### 12.3 Import Churn

**Risk**: Moving types and functions changes imports across the codebase, creating large diffs and potential merge conflicts.

**Mitigation**: Perform extractions as atomic work packages (one component family per WP). Each WP is a self-contained clean-break refactoring with its own test verification step. No re-export bridges.

### 12.4 Semantic Drift

**Risk**: Shared components used by multiple systems may be modified to serve one system's needs, breaking invariants for another.

**Mitigation**: Construction kit components have their own unit tests that encode their expected behavior. Systems depend on the kit's tested behavior, not on implementation details. Changes to kit components require their own tests to pass.

### 12.5 Hidden Mini-Framework

**Risk**: The construction kit could grow into a second framework with its own lifecycle, configuration, and orchestration.

**Mitigation**: The construction kit contains only pure functions, stateless classes (with configuration only), and immutable data types. It has no lifecycle, no event system, no hooks, and no configuration resolution. If any of these emerge, the design has lost its way.

---

## 13. Relationship to Existing Documents

| Document | Relationship |
|----------|-------------|
| [System Construction Kit Draft](system-construction-kit-draft.md) | Conceptual predecessor. This spec formalizes the ideas with concrete code references. |
| [Architectural Vision v0.2.0](../../architecture/evolution/architectural-vision-v0.2.0.md) | Defines the framework/system separation that the kit preserves. The kit introduces a sub-layer within the `systems/` package. |
| [Modular Architecture Evolution](../../architecture/evolution/modular-architecture-evolution.md) | Establishes the core principle: systems define behavior, frameworks define execution. The kit adds: construction kit defines reusable behavior mechanisms. |

---

## 14. Work Package Derivation Guidance

The following work packages can be derived from this spec. Ordering reflects dependency relationships.

### Phase 1: Foundation (no behavioral change, pure structural refactoring)

| WP | Content | Dependencies | Estimated scope |
|----|---------|-------------- |-----------------|
| WP-1 | Create `construction_kit/` package skeleton with `__init__.py` files | None | Small |
| WP-2 | Extract observation types and sensor (Section 7.1) | WP-1 | Medium |
| WP-3 | Extract observation buffer (Section 7.2) | WP-1, WP-2 | Small |
| WP-4 | Extract energy utilities (Section 7.3) | WP-1 | Small |
| WP-5 | Extract hunger drive (Section 7.4) | WP-1, WP-2 | Small |
| WP-6 | Extract softmax policy (Section 7.5) | WP-1, WP-2 | Medium (interface change) |
| WP-7 | Extract arbitration (Section 7.6) | WP-1 | Medium (generalization) |
| WP-8 | Extract curiosity drive and spatial world model (Section 7.7) | WP-1, WP-2, WP-3 | Medium |
| WP-9 | Dependency constraint tests | WP-1 through WP-8 | Small |

### Phase 2: Prediction foundation (new components for System C)

| WP | Content | Dependencies | Estimated scope |
|----|---------|-------------- |-----------------|
| WP-10 | Implement predictive memory (Section 8.1) | WP-1 | Medium |
| WP-11 | Implement prediction error (Section 8.2) | WP-1 | Small |
| WP-12 | Implement trace dynamics (Section 8.3) | WP-1 | Medium |
| WP-13 | Implement action modulation (Section 8.4) | WP-1 | Small |

### Phase 3: System C integration

| WP | Content | Dependencies |
|----|---------|-------------- |
| WP-14+ | System C implementation using construction kit components | Phase 2 |

Phase 1 work packages can be executed largely in parallel (WP-2 through WP-8), with the constraint that WP-2 (observation types) must complete before WP-3, WP-5, and WP-6 which depend on the extracted observation types.

Phase 2 work packages are independent of each other and can proceed in parallel.

---

## 15. Success Criteria

The construction kit is successfully implemented when:

1. **No cross-system source dependencies**: No concrete system imports directly from another concrete system. All shared mechanisms come from the construction kit.
2. **All tests pass**: Existing behavioral tests produce identical results after extraction.
3. **Framework untouched**: No changes to `axis.framework`, `axis.sdk`, or `axis.world`.
4. **Dependency constraints verified**: Automated tests confirm the construction kit imports nothing from framework, world, or concrete systems.
5. **System AW simplified**: System AW's delegation wrappers are eliminated. It uses construction kit components directly.
6. **Clean import paths**: All shared types and functions have a single canonical location in the construction kit.
7. **Future system path clear**: A developer building System C can see where prediction, traces, and modulation will live without being forced to inherit from or depend on any existing system.
