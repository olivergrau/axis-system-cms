# Modular Architecture Evolution -- Kickoff Document

**Milestone**: Transition from single-system implementation to modular, extensible framework
**Status**: Pre-implementation
**Repository baseline**: AXIS System A v0.1.0 (1215+ tests, fully functional)

---

## 1. Purpose of This Kickoff Document

This document is the **starting point for the next major architectural milestone** of the AXIS project: the evolution from a monolithic System A implementation toward a modular framework that can host multiple independent system implementations.

It serves as:

- **Orientation** for any developer or Claude Code agent beginning work on this milestone
- **Architectural context** bridging the current codebase and the target direction
- **Constraint document** identifying what must change, what should remain stable, and where the risks are

This is not an implementation spec. It is a foundation for writing detailed specs.

---

## 2. Current Implemented Architecture

The repository implements a complete, functional simulation pipeline centered on **System A (Baseline)**: a hunger-driven agent navigating a 2D grid world.

### 2.1 Core Runtime

A single simulation step follows the chain:

```
observe -> drive -> decide -> act -> update
```

Key modules and their roles:

| Module | Responsibility |
|--------|---------------|
| `world.py` | Grid world model (Cell, World, create_world). World is the sole mutable container. |
| `observation.py` | Stateless sensor projection: Von Neumann neighborhood -> Observation (10-dim vector) |
| `observation_buffer.py` | Pure FIFO memory update. Populated but unused by current drive/policy. |
| `drives.py` | Hunger drive: `(energy, observation) -> HungerDriveOutput` (activation + 6 action contributions) |
| `policy.py` | Decision pipeline: admissibility mask -> softmax -> action selection -> `DecisionTrace` |
| `transition.py` | 6-phase state transition: regen -> act -> observe -> energy -> memory -> termination |
| `runner.py` | Episode loop orchestration: chains drive -> policy -> transition per step |
| `results.py` | `StepResult`, `EpisodeResult`, `EpisodeSummary` -- complete trace structures |
| `snapshots.py` | Immutable `WorldSnapshot` / `AgentSnapshot` capture (3 world + 2 agent per step) |

All domain models are frozen Pydantic `BaseModel` instances. The runtime is fully deterministic given a seed. Every step produces a complete `StepResult` trace.

### 2.2 Experimentation Framework

Three-layer orchestration:

```
ExperimentExecutor
  -> resolve_run_configs() -> tuple[RunConfig, ...]
     -> RunExecutor
        -> resolve_episode_seeds()
        -> create_world() + run_episode() -> EpisodeResult
```

- **ExperimentConfig**: defines single_run or OFAT experiment types
- **RunConfig**: per-run config with seed, episodes, start position
- **RunExecutor**: calls `create_world()` and `run_episode()` directly -- these are System A functions
- **ExperimentExecutor**: orchestrates runs, manages persistence lifecycle, supports resume

The experiment framework currently **calls System A code directly** -- there is no interface or indirection layer.

### 2.3 Persistence / Repository

`ExperimentRepository` is a filesystem-backed, JSON-only persistence layer.

```
{root}/{experiment_id}/
  experiment_config.json, experiment_metadata.json, experiment_status.json
  experiment_summary.json
  runs/{run_id}/
    run_config.json, run_metadata.json, run_status.json
    run_summary.json, run_result.json
    episodes/episode_0001.json, ...
```

Key properties:
- Purely path-based, no database
- Immutable artifacts (config, result, summary) vs mutable artifacts (status, metadata)
- Resume works by checking artifact completeness at run level
- No system-type awareness -- artifacts are System A-specific by content, not by schema

### 2.4 Resume Behavior

Run-level granularity: a run is either fully complete (skip) or fully re-executed. Resume re-resolves all run configs deterministically and checks `is_run_complete()` per run. The experiment summary is always recomputed.

No system-type metadata is persisted. Resume uses `resolve_run_configs()` which depends on `ExperimentConfig` -- currently a System A-specific type.

### 2.5 CLI

Entry point `axis` with subcommands:

```
axis experiments {list|run|resume|show}
axis runs {list|show}
axis visualize --experiment E --run R --episode N
```

All dispatch goes through `ExperimentRepository` and `ExperimentExecutor`. The CLI directly imports System A's `ExperimentConfig` and `ExperimentExecutor`. No system selection or routing exists.

### 2.6 Visualization / Replay

PySide6 desktop application with strict unidirectional data flow:

```
Repository -> ReplayAccessService -> SnapshotResolver -> ViewModelBuilder -> Widgets
```

The visualization layer:
- Operates on persisted `EpisodeResult` data only (no live execution)
- Resolves three world snapshots per step (BEFORE, AFTER_REGEN, AFTER_ACTION)
- Renders System A-specific content: hunger drive output, decision trace, transition trace
- The `SnapshotResolver` directly accesses `TransitionTrace` fields (world_before, world_after_regen, etc.)
- The `ViewModelBuilder` constructs System A-specific overlays: action preference, drive contribution, consumption opportunity
- The `StepAnalysisPanel` renders hunger drive activation, observation table, and the full decision pipeline

The visualization is deeply coupled to System A's trace structure. There is no system-agnostic replay layer.

---

## 3. Target Architectural Direction

The vision document (`Modular Architecture Evolution.md`) defines the following target:

### 3.1 Core Separation Principle

> Systems define behavior. Frameworks define execution. Contracts define integration.

### 3.2 System SDK

A set of explicit interfaces that all system implementations must conform to:

- `AgentInterface` -- agent state representation
- `PolicyInterface` -- decision pipeline
- `DriveInterface` -- motivation computation
- `TransitionInterface` -- state evolution
- `SensorInterface` -- observation construction

Systems are structured compositions of these components, not black boxes.

### 3.3 World Framework

The World is owned by the framework, not by systems. Systems interact with the world only through defined interfaces.

### 3.4 Experimentation Framework (Evolved)

Execution responsibility (episode loop, step sequencing, seed handling) moves fully into the framework. The framework interacts with systems exclusively through SDK interfaces. No direct import of system code.

### 3.5 Persistence Layer

Storage of all artifacts becomes system-agnostic. Trace data conforms to a global replay contract that works across systems.

### 3.6 Visualization Layer

Replay-based, read-only, consuming only the global replay contract. No system-specific rendering hardcoded in the framework.

### 3.7 Global Replay Contract

All systems must produce trace data compatible with a shared contract that enables:
- Cross-system visualization
- Comparable experiments
- Standardized trace analysis

---

## 4. Architectural Delta: Current State vs Target State

### 4.1 Structural Comparison

| Concern | Current State | Target State | Gap |
|---------|--------------|-------------|-----|
| **System definition** | Implicit -- spread across `drives.py`, `policy.py`, `transition.py`, `runner.py`, `observation.py` | Explicit `System` composition via SDK interfaces | No interfaces exist; system is the codebase |
| **System registration** | N/A -- only System A exists | Systems register with framework, selected by config | No registration mechanism |
| **Episode execution** | `runner.py:run_episode()` directly calls System A functions | Framework-owned loop calling system via interfaces | `run_episode` hardcodes the drive->policy->transition chain |
| **World ownership** | `world.py` is a System A module | World is a framework concern with defined interaction API | World is already partially generic but lives in System A package |
| **Observation/Sensor** | `observation.py:build_observation()` hardcodes Von Neumann sensor | Sensor is a system component via `SensorInterface` | Function is System A-specific |
| **Drive composition** | Single `compute_hunger_drive()` function | `DriveInterface` with composable drive system | No interface; no composition |
| **Config model** | `SimulationConfig` embeds System A-specific sections (policy, transition, agent) | System-agnostic experiment config + system-specific config | Config is monolithically System A |
| **Trace format** | `StepResult` contains `HungerDriveOutput`, `DecisionTrace` (System A-specific) | Global replay contract with system-agnostic base + extensible system data | Trace types are System A-only |
| **Replay/Viz** | Directly reads `TransitionTrace`, `HungerDriveOutput` | Reads generic replay contract; system-specific views are pluggable | Deep coupling to System A trace types |
| **CLI routing** | Directly imports `ExperimentConfig`, `ExperimentExecutor` | Routes to correct system based on config/metadata | No routing, no system awareness |
| **Repository** | Stores System A artifacts as-is | System-agnostic storage with system type metadata | No system type field in metadata |

### 4.2 What Is Already Generic Enough

Several components are already close to system-agnostic:

- **Repository filesystem layout**: `experiment -> runs -> episodes` is system-independent
- **Repository save/load mechanics**: JSON serialization, status lifecycle, discovery
- **Resume logic**: run-level completion detection and re-execution
- **Experiment types**: `single_run` and `ofat` are system-agnostic concepts
- **Seed resolution**: `resolve_episode_seeds()` has no System A dependency
- **Visualization state machine**: `ViewerState`, state transitions, `PlaybackController` are mostly generic
- **Visualization UI framework**: PySide6 widget hierarchy and signal wiring pattern

### 4.3 What Is Currently Mixed and Must Be Separated

- **`runner.py`**: The `episode_step()` function is the main coupling point -- it directly calls `compute_hunger_drive`, `select_action`, and `transition.step`. This is simultaneously the episode execution loop (framework concern) and the System A processing chain (system concern).
- **`config.py`**: `SimulationConfig` merges framework concerns (`GeneralConfig`, `ExecutionConfig`, `LoggingConfig`) with system-specific concerns (`PolicyConfig`, `TransitionConfig`, `AgentConfig`, `WorldConfig`).
- **`run.py`**: `RunExecutor` directly calls `create_world()` and `run_episode()` -- both System A functions.
- **`experiment.py`**: `ExperimentConfig` references `SimulationConfig` which is System A-specific. The OFAT parameter path mechanism depends on System A's config structure.
- **Visualization `ViewModelBuilder`**: Builds System A-specific overlays and analysis panels from System A trace types.
- **Visualization `SnapshotResolver`**: Directly accesses `TransitionTrace` fields that are specific to System A's 6-phase transition model.

---

## 5. Consistency Check of the Proposed Direction

### 5.1 Is the Definition of "System" Consistent?

**Mostly yes.** The vision document defines a System as:

> (current_state, observation) -> (action, next_state, trace)

This is a clean functional contract. However, there is a subtlety:

- The current System A's transition function does more than map state: it mutates the World (resource consumption, agent position). The vision says the World is a framework concern, but the transition engine currently writes to it.
- **Tension**: If systems produce actions and the framework applies them to the world, then the transition engine must be split: system-side (state update, energy computation) vs framework-side (world mutation). If systems own their transition entirely, then the world mutation contract needs explicit specification.
- **Recommendation**: The system should return an action intent (or action result). The framework should own world mutation. This aligns with the vision but requires the current `transition.py` to be decomposed.

### 5.2 Is Execution Ownership Clear?

**Partially.** The vision states execution belongs to the Experimentation Framework. Currently:

- `runner.py:run_episode()` contains the step loop -- this needs to move to the framework.
- `runner.py:episode_step()` is the per-step orchestration chain -- this mixes framework dispatch (calling components in order) with system logic (which components to call).
- The step loop itself is generic (loop, record, check termination). The per-step chain (`drive -> policy -> transition`) is system-specific.

**Clarity needed**: Does the framework call `system.step(state, observation)` as a single opaque call? Or does the framework call sub-components individually (`system.sense()`, `system.decide()`, `system.transition()`)? The vision suggests structured composition (individual interfaces), which implies the framework may orchestrate sub-components -- but this conflicts with treating systems as black boxes at the step level.

**Recommendation**: The framework should call a single `System.step()` method that internally orchestrates sub-components. The SDK interfaces define the sub-components for inspection/testing, but execution flows through the system's own orchestration. This preserves both composability and encapsulation.

### 5.3 Is World Ownership Clear Enough?

**Needs refinement.** The vision says the World is a framework concern.

Current reality:
- `world.py` defines `World`, `Cell`, `create_world` -- all generic in concept
- `transition.py` mutates the World directly (regen, movement, consumption)
- `observation.py` reads the World to build observations

If the world is framework-owned:
- The framework must apply actions to the world (or delegate to a world update function)
- Systems receive observations but never access the world directly
- World configuration (size, obstacles, regen rates) becomes a framework config concern

**Tension**: System A's transition uses world-specific mechanics (resource consumption, regeneration). If different systems have different world interaction models, the world interaction API must be extensible -- but the vision proposes a single, consistent world.

**Recommendation**: Start with a single `WorldInterface` that supports read access (for sensors) and a defined set of action effects (move, consume). System-specific world mechanics (e.g., new action types) can be handled via action-type extension rather than world-class extension.

### 5.4 Is a Global Replay Contract Realistic?

**Yes, with caveats.** A global replay contract is feasible if it includes:

- A **base layer** (system-agnostic): step index, world snapshots (grid state + agent position), action taken, energy, termination
- An **extension layer** (system-specific): drive outputs, decision traces, intermediate computations

The current trace data already has this implicit split:
- Base: `TransitionTrace` (world snapshots, position, energy, action outcomes)
- Extension: `HungerDriveOutput`, `DecisionTrace`

**Risk**: The 3-snapshot model (before, after_regen, after_action) is System A-specific. Other systems might not have a regen phase, or might have more phases. The replay contract must define snapshot points generically (e.g., "world before action" and "world after action" as minimum, with optional intermediate snapshots).

### 5.5 Is System-Aware Visualization Compatible with Modularization?

**Partially.** The current visualization has two layers of coupling:

1. **Structural coupling** (resolvable): `SnapshotResolver` accesses specific `TransitionTrace` fields. This can be generalized to a `ReplaySnapshot` interface.
2. **Content coupling** (harder): `StepAnalysisPanel` renders hunger drive activation, contribution tables, decision pipeline details. This is deeply System A-specific content.

For multi-system support, the visualization needs:
- A **generic base view**: grid rendering, agent position, energy, action taken -- works for any system
- A **system-specific detail view**: drive analysis, decision pipeline, etc. -- pluggable per system

This is architecturally tractable but non-trivial. The current `ViewModelBuilder` would need to delegate system-specific content construction to a system-provided builder.

### 5.6 Are the Proposed Phases Sensible?

**Yes, with minor adjustments noted below in Section 7.** The five-phase sequence (interfaces -> extraction -> framework alignment -> contract stabilization -> validation) is a sound layering that avoids premature coupling and enables incremental validation.

---

## 6. Major Refactoring Fronts

### 6.1 System SDK Interface Extraction

**Scope**: Define abstract base classes or Protocols for the core system components.

Key interfaces to define:
- `SystemInterface`: top-level `step(state, observation) -> (action, new_state, trace)`
- `SensorInterface`: `observe(world, position) -> Observation`
- `DriveInterface`: `compute(state, observation) -> DriveOutput`
- `PolicyInterface`: `select_action(contributions, observation, ...) -> DecisionTrace`
- `TransitionInterface`: `step(world, state, action, ...) -> TransitionResult`

**Current friction**: These behaviors exist as module-level functions, not as classes/interfaces. The refactoring involves wrapping them into interface-conforming classes without changing behavior.

### 6.2 Episode Execution Loop Extraction

**Scope**: Move the episode execution loop from `runner.py` to the framework.

Currently `run_episode()` directly constructs System A agent state, calls `build_observation()`, and runs `episode_step()` per timestep. The generic loop structure (init -> loop -> record -> terminate) must be preserved, but system interactions must go through interfaces.

**Key decision**: The framework needs a way to initialize episode state. Currently this is hardcoded in `run_episode()` (`AgentState(energy=..., observation_buffer=...)`). System initialization must become a system method.

### 6.3 Configuration Model Decomposition

**Scope**: Split `SimulationConfig` into framework config and system config.

Framework config (system-agnostic):
- `GeneralConfig` (seed)
- `ExecutionConfig` (max_steps)
- `LoggingConfig`

System A config (system-specific):
- `AgentConfig`
- `PolicyConfig`
- `TransitionConfig`
- `WorldConfig` (partially -- grid dimensions are arguably framework, regen parameters are system-dependent)

**Impact**: This affects `ExperimentConfig`, `RunConfig`, and the OFAT parameter path mechanism. The parameter path currently addresses sections of `SimulationConfig` -- with a split config, the addressing scheme needs to distinguish framework vs system parameters.

### 6.4 World Extraction and Interface Definition

**Scope**: Move `World`, `Cell`, and `create_world` to a framework-level module.

The World model (`world.py`) is already relatively generic: grid cells with types and resource values, agent position, bounds checking. The main System A-specificity is in `create_world()` which applies obstacles and sparse eligibility -- these are world configuration concerns that can stay generic.

**Subtlety**: `transition.py` currently owns world mutation (`_apply_regeneration`, `_apply_movement`, `_apply_consume`). These will need to be refactored into either:
- A world interaction API on the framework side
- System-level action handlers that the framework calls

### 6.5 Replay Contract Formalization

**Scope**: Define a system-agnostic base trace format alongside system-specific extensions.

Minimum base trace per step:
- Step index, timestep
- World state before and after (at minimum two snapshots)
- Agent position and energy before and after
- Action taken and outcome (moved, consumed, terminated)

System-specific extension:
- Drive outputs (type varies per system)
- Decision pipeline details (varies per system)
- Additional intermediate snapshots

**Format**: The extension mechanism could use a `dict[str, Any]` (flexible but untyped) or a `SystemTraceInterface` (typed but requires per-system implementation). Recommend starting with a typed approach using generics.

### 6.6 Visualization Generalization

**Scope**: Separate base grid visualization from system-specific analysis views.

What stays generic:
- `GridWidget` rendering (cells, agent, obstacles, resources)
- `ReplayControlsPanel`, `StatusPanel`
- `ViewerState`, state transitions, `PlaybackController`

What becomes system-specific:
- `StepAnalysisPanel` content (currently hardcoded for hunger drive + softmax)
- Debug overlays (action preference, drive contribution, consumption opportunity)
- Portions of `ViewModelBuilder` that construct analysis ViewModels

**Approach**: Introduce a `SystemVisualizationAdapter` that a system provides to build its system-specific view models and overlay data.

### 6.7 CLI Multi-System Routing

**Scope**: The CLI needs to determine which system to use for execution and visualization.

Options:
- System type in experiment config (new field)
- System type inferred from persisted metadata (for visualization/resume)
- System registry that maps type identifiers to implementations

Current CLI directly imports `ExperimentExecutor` which directly uses `RunExecutor` which directly calls System A. The entire execution chain needs an indirection point.

---

## 7. Proposed Milestone Phases

The vision document proposes five phases. Below they are restated with implementation-oriented detail based on the current repository state.

### Phase 1 -- Interface Definition

**Goal**: Define the SDK interfaces and contracts without changing existing behavior.

Work:
- Define abstract `SystemInterface` with `step()`, `initialize_state()`, `sensor()`
- Define `DriveInterface`, `PolicyInterface`, `TransitionInterface`, `SensorInterface`
- Define `WorldInterface` for read access and action application
- Define base `StepTrace` and `EpisodeTrace` for the replay contract
- Define framework-level `FrameworkConfig` vs system-level `SystemConfig` split
- All interfaces should be abstract base classes or `typing.Protocol`

**Deliverable**: New module (e.g., `axis_sdk/` or `axis_framework/interfaces/`) with interface definitions. No behavior change.

### Phase 2 -- Extraction and Conformance

**Goal**: Refactor System A to conform to the new interfaces.

Work:
- Wrap existing System A functions into classes implementing SDK interfaces
- Create `SystemA` class implementing `SystemInterface`
- Move `run_episode` and `episode_step` logic: framework part into a framework executor, system part into `SystemA.step()`
- Split `SimulationConfig` into `FrameworkConfig` + `SystemAConfig`
- Move `World`, `Cell`, `create_world` to framework-level module
- Refactor `transition.py`: separate world mutation (framework) from system state update (system)

**Constraint**: All existing tests must continue to pass. This phase should be strictly behavior-preserving.

### Phase 3 -- Framework Alignment

**Goal**: Make the experimentation framework system-agnostic.

Work:
- `RunExecutor` calls system via `SystemInterface` rather than importing `run_episode` / `create_world`
- `ExperimentExecutor` operates on generic config types
- OFAT parameter path mechanism works with framework + system config split
- Resume logic handles system type metadata
- CLI gains `--system` parameter or reads system type from config

**Deliverable**: The experimentation framework can execute any `SystemInterface` implementation without modification.

### Phase 4 -- Contract Stabilization

**Goal**: Stabilize the replay contract and align visualization.

Work:
- Finalize base `StepTrace` / `EpisodeTrace` format
- System A produces traces conforming to the new contract (with System A-specific extension data)
- `SnapshotResolver` works with generic base trace
- `ViewModelBuilder` delegates system-specific content to a `SystemVisualizationAdapter`
- Base visualization (grid, agent, controls) works for any system
- System A-specific views (analysis panel, overlays) are provided via adapter
- Repository metadata includes system type

**Deliverable**: Visualization works for any system that conforms to the replay contract.

### Phase 5 -- Validation via Second System

**Goal**: Prove the framework works by implementing a second system.

Work:
- Implement `SystemAPlusW` (or similar) -- a variant that uses the world model / memory
- Confirm it can be added without modifying framework code
- Run comparative experiments across `SystemA` and `SystemAPlusW`
- Visualize both systems through the same visualization framework

**Deliverable**: Two systems running side-by-side with shared framework, comparable experiments, unified visualization.

---

## 8. Stability Boundaries

The following should remain stable during this milestone. Future agents and developers should **not** casually alter these foundations.

### 8.1 Must Remain Stable

| Concern | Rationale |
|---------|-----------|
| **Frozen Pydantic model pattern** | All value types, configs, results are frozen. This is a core design decision that enables immutability guarantees across the system. |
| **Repository filesystem layout** | The `experiment -> runs -> episodes` hierarchy with JSON artifacts is well-tested and sound. Multi-system support should extend it, not replace it. |
| **Immutable vs mutable artifact distinction** | Config/result/summary = immutable; status/metadata = mutable. This enables resume safety. |
| **Resume at run-level granularity** | Run-level completion detection is simple and reliable. Episode-level resume would add significant complexity for marginal benefit. |
| **Replay-based visualization philosophy** | Visualization reads persisted data, never interacts with live execution. This decoupling should be preserved. |
| **Deterministic execution given seed** | Seed -> episode must be fully deterministic. This is foundational for reproducibility. |
| **3-world-snapshot minimum per step** | The before/intermediate/after snapshot pattern provides full auditability. The number and naming of snapshots may vary per system, but the principle of capturing world state at phase boundaries should persist. |
| **Unidirectional visualization data flow** | `ViewerState -> ViewModelBuilder -> Widgets -> signals -> Controller`. This pattern is well-tested and should not be replaced with bidirectional state. |
| **Test infrastructure** | Builders, fixtures, and assertion utilities should be preserved and extended, not replaced. |

### 8.2 May Evolve

| Concern | Expected Change |
|---------|----------------|
| `SimulationConfig` structure | Will be split into framework + system configs |
| `StepResult` / `TransitionTrace` types | Will gain a generic base layer |
| Public API surface (`__init__.py`) | Will be reorganized across packages |
| Module locations | Files may move between packages |
| CLI argument structure | Will gain system selection |

---

## 9. Risks and Open Questions

### 9.1 Transition Decomposition Complexity

The `transition.py:step()` function is the most complex function in the codebase. It combines world mutation, energy computation, memory update, and termination logic in a specific 6-phase sequence. Decomposing this into framework-owned (world mutation) and system-owned (agent state update) parts requires careful design to preserve the phase ordering and snapshot semantics.

**Risk**: Incorrect decomposition could break the deterministic execution guarantee or the snapshot contract.

### 9.2 Config Decomposition and OFAT

The OFAT parameter sweep uses dot-path addressing (`"transition.energy_gain_factor"`) into `SimulationConfig`. If config is split into framework + system configs, the parameter path mechanism must know which config to address. This affects both experiment definition and resume (which re-resolves configs from persisted data).

**Open question**: Should persisted experiment configs store the unified config (backward compatible) or the split config (forward-looking)?

### 9.3 Replay Contract Extensibility

The global replay contract must be generic enough for future systems but specific enough to be useful for visualization. A `dict[str, Any]` extension mechanism is flexible but loses type safety. A typed generic approach is safer but requires each system to define and register its trace types.

**Open question**: How should system-specific trace data be serialized and deserialized when loading persisted episodes? The repository currently uses `model_validate()` on concrete System A types.

### 9.4 Visualization Adapter Boundary

The `StepAnalysisPanel` currently renders a detailed numeric readout of the hunger drive pipeline. For a second system with different internals, this panel must show different content. The adapter pattern is clear in principle, but the boundary between "generic step info" and "system-specific analysis" needs careful definition.

**Risk**: If the boundary is drawn too generically, the analysis panel becomes useless. If drawn too specifically, it's not reusable.

### 9.5 Package Structure Decision

The target architecture suggests multiple packages (e.g., `axis_sdk`, `axis_framework`, `axis_system_a`). Currently everything is in `axis_system_a`.

**Open question**: Should the evolution use:
- (a) A single package with sub-packages (`axis/sdk/`, `axis/framework/`, `axis/systems/system_a/`)
- (b) Multiple top-level packages in the same repo
- (c) Separate repositories (unlikely for this milestone)

The choice affects import paths, test organization, and installation.

### 9.6 World Configuration Ownership

`WorldConfig` is currently part of `SimulationConfig`. Some world properties are truly generic (grid dimensions, obstacle density), while others may be system-specific (regeneration mode, regen rate as used by System A's transition).

**Open question**: Where does the boundary lie between framework-level world config and system-level world config? Different systems may require different world configurations.

### 9.7 Backward Compatibility of Persisted Artifacts

Existing experiment results are serialized as System A-specific JSON. After the modular evolution, the deserialization path must either:
- Remain backward-compatible with existing artifacts
- Require a migration of existing data
- Accept that pre-evolution artifacts are a different format

**Recommendation**: Existing artifacts should remain loadable. New artifacts should include system type metadata. Visualization should handle both formats.

---

## 10. Recommended Use of This Document

### For Claude Code Agents

- Read this document **before** beginning any implementation work on the modular evolution
- Use it as a constraint: the stability boundaries (Section 8) define what not to break
- Use the refactoring fronts (Section 6) to scope individual work packages
- Validate your implementation decisions against the consistency checks (Section 5)
- Do not treat this as a detailed spec -- write specs for individual phases based on this foundation

### For Human Developers

- Use this as orientation when reviewing or planning modular evolution work
- The architectural delta (Section 4) gives the clearest picture of the gap
- The risks (Section 9) should be resolved in design discussions before implementation begins
- The phases (Section 7) provide a sequencing guide but are not rigid -- adjust based on what you learn during implementation

### General Guidance

- This is a **kickoff** document, not a **plan**. Each phase will need its own detailed spec.
- Always validate against the actual codebase, not just this document. The code is authoritative.
- When in doubt, preserve existing behavior. The current system works. The modular evolution should make it extensible, not fragile.
