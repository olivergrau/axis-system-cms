# Modular Architecture Evolution -- Implementation Roadmap

**Based on**: `modular-architecture-kickoff.md`, `modular-architecture-questions-answers.md`, `Modular Architecture Evolution.md`
**Status**: Approved architectural direction, pre-implementation

---

## How to Read This Document

This is a **coarse roadmap** -- not a detailed implementation plan. Each work package (WP) describes:

- what it achieves
- what it touches in the current codebase
- what its key deliverables are
- what must be true before it starts (dependencies)

Work packages are grouped into **phases**. Phases are sequential. Work packages within a phase can often be parallelized, but some have internal ordering noted in their dependencies.

**For Claude Code agents**: Each WP should become a self-contained implementation task. Read the kickoff document and Q&A answers before starting any WP. Respect the stability boundaries from the kickoff document (Section 8).

**For human developers**: Use this as a planning and review guide. Each WP is scoped for roughly one focused work session.

---

## Architectural Decisions Summary

These decisions were made in the Q&A document and are **binding for all work packages**.

| # | Decision | Choice |
|---|----------|--------|
| Q1 | Step contract | Opaque `system.step()` -- framework never orchestrates sub-components |
| Q2 | World mutation | Framework-owned -- systems return action intents, framework applies them |
| Q3 | Regeneration | Framework-owned, configurable via framework config |
| Q4 | Action space | Shared base actions (movement + stay), extensible per system (e.g., consume) |
| Q5 | Package structure | Single package `axis` with sub-packages: `sdk`, `framework`, `world`, `systems`, `visualization` |
| Q6 | Config architecture | Unified config: flat framework sections (`general`, `execution`, `world`) + opaque `system: dict` |
| Q7 | OFAT paths | Prefixed dot-paths: `framework.execution.max_steps`, `system.policy.temperature` |
| Q8 | Trace extensibility | Base trace + `system_data: dict[str, Any]` |
| Q9 | Snapshots | 2 mandatory (`BEFORE`, `AFTER_ACTION`) + optional named intermediates |
| Q10 | Visualization | Adapter with structured extension points (`SystemVisualizationAdapter`) |
| Q11 | System registry | Explicit code-level registry (dict of factory functions) |
| Q12 | WorldConfig | Framework owns structure (grid size, obstacles); system owns dynamics (regen params) |
| Q13 | Backward compat | Clean break -- no legacy artifact support required |
| Q14 | Observations | System-defined, opaque to framework |
| Q15 | Energy/vitality | Mandatory normalized metric `[0, 1]` exposed by all systems |
| Q16 | Termination | Both framework (`max_steps`) and system (`vitality <= 0`, etc.) can terminate |
| Q17 | Phase names | Fixed minimal set (`BEFORE`, `AFTER_ACTION`) + optional system-declared extras |
| Q18 | Tests | New test suites for new structure; old tests can be rewritten |

### Global System Assumptions (from Q&A preamble)

All systems must conform to:

- Energy-based state (mandatory)
- Drive-based modulation (1..N drives, mandatory)
- Policy-driven action selection (mandatory)
- Framework-owned world interaction
- Explicit transition function with structured trace output
- Step-level traceability (replay contract conformance)

These are **SDK-enforced structural constraints**, not framework-dispatch concerns. The framework calls `system.step()` and receives results. The SDK interfaces ensure systems are internally well-structured.

---

## Phase 0 -- Preparation

### WP-0.1: Package Scaffold

**Goal**: Create the new `axis` package structure alongside the existing `axis_system_a` package. No code moves yet -- just the directory structure, `__init__.py` files, and `pyproject.toml` update.

**Touches**:
- `pyproject.toml` (new package name, entry points)
- `src/axis/` directory creation

**Target structure**:
```
src/axis/
    __init__.py
    sdk/
        __init__.py
    framework/
        __init__.py
    world/
        __init__.py
    systems/
        __init__.py
        system_a/
            __init__.py
    visualization/
        __init__.py
```

**Deliverable**: The `axis` package is installable and importable. All sub-packages are empty but exist. The old `axis_system_a` package still works unchanged.

**Dependencies**: None.

**Key constraint**: The existing `axis_system_a` package and all its tests must remain fully functional during this phase. The new package exists alongside it initially.

---

### WP-0.2: Test Infrastructure Preparation

**Goal**: Set up the new test directory structure mirroring the package structure. Establish test utilities and fixtures that will be needed across phases.

**Touches**:
- `tests/` directory structure (new subdirectories for `sdk`, `framework`, `world`, `systems/system_a`, `visualization`)
- Shared test fixtures / builders (can be adapted from existing ones)

**Deliverable**: Test directories exist. Shared fixtures are available. Running the full test suite still works (existing tests still pass).

**Dependencies**: WP-0.1.

---

## Phase 1 -- SDK and Contracts

Define all interfaces and contract types. No existing code is moved or changed. This phase produces the "type system" of the new architecture.

### WP-1.1: Core SDK Interfaces

**Goal**: Define the abstract interfaces that all systems must implement.

**Module**: `axis/sdk/interfaces.py` (or split across files as appropriate)

**Interfaces to define**:

```
SystemInterface
    step(world_view, agent_state, rng) -> StepOutput
    initialize_state(config) -> AgentState
    system_type() -> str
    vitality(agent_state) -> float           # normalized [0, 1]
    action_space() -> tuple[str, ...]        # registered action names

SensorInterface
    observe(world_view, position) -> Any     # system-specific observation type

DriveInterface
    compute(state, observation) -> Any       # system-specific drive output

PolicyInterface
    select(drive_outputs, observation, rng) -> PolicyOutput

TransitionInterface
    transition(state, action, action_outcome, observation) -> TransitionOutput
```

**Key design notes**:
- `SystemInterface.step()` receives a read-only world view, not a mutable World
- `SystemInterface.step()` returns a `StepOutput` containing: selected action (str), new agent state, system trace data (dict), terminated flag, termination reason (optional str)
- Sub-component interfaces (`SensorInterface`, etc.) are **mandatory internal contracts** -- systems must implement them, but the framework only calls `SystemInterface`
- All interfaces should be `typing.Protocol` or abstract base classes
- `AgentState` at the SDK level is opaque (systems define their own); only `vitality()` provides a framework-readable metric

**Deliverable**: Interface definitions with docstrings. No implementations yet.

**Dependencies**: WP-0.1.

---

### WP-1.2: World Contracts

**Goal**: Define the world-related contracts: `WorldView` (read-only), `ActionOutcome`, action registration model, and base `WorldConfig`.

**Module**: `axis/sdk/world.py` or `axis/world/contracts.py`

**Types to define**:

```
WorldView (Protocol)
    get_cell(position) -> CellView
    agent_position -> Position
    width -> int
    height -> int
    is_within_bounds(position) -> bool
    is_traversable(position) -> bool

CellView
    cell_type: str
    resource_value: float

ActionOutcome
    action: str
    moved: bool
    new_position: Position
    consumed: bool
    resource_consumed: float
    # extensible for future action types

BaseWorldConfig
    grid_width: int
    grid_height: int
    obstacle_density: float
```

**Key design notes**:
- `WorldView` is what systems see -- read-only, no mutation allowed
- `ActionOutcome` is what the framework returns to the system after applying an action to the world
- Base actions defined at framework level: `"up"`, `"down"`, `"left"`, `"right"`, `"stay"`
- Systems register additional actions (e.g., `"consume"`) with corresponding world handlers
- The world action API will be defined in WP-2.2 (implementation), but the contract is defined here

**Deliverable**: Contract types, frozen Pydantic models where applicable.

**Dependencies**: WP-0.1.

---

### WP-1.3: Replay Contract

**Goal**: Define the base step trace, episode trace, and snapshot types for the global replay contract.

**Module**: `axis/sdk/replay.py`

**Types to define**:

```
BaseStepTrace
    timestep: int
    action: str
    world_before: WorldSnapshot       # mandatory
    world_after: WorldSnapshot        # mandatory
    intermediate_snapshots: dict[str, WorldSnapshot]  # optional, named
    agent_position_before: Position
    agent_position_after: Position
    vitality_before: float
    vitality_after: float
    terminated: bool
    termination_reason: str | None
    system_data: dict[str, Any]        # opaque system-specific trace

BaseEpisodeTrace
    steps: tuple[BaseStepTrace, ...]
    total_steps: int
    termination_reason: str
    system_type: str

WorldSnapshot (reuse/adapt existing)
    cells: ...
    agent_position: Position
    width: int
    height: int
```

**Key design notes**:
- `vitality_before` / `vitality_after` replace the System A-specific `energy_before` / `energy_after` at the contract level
- `system_data` carries all system-specific trace information (drive outputs, decision traces, etc.)
- `intermediate_snapshots` allows System A to provide its `AFTER_REGEN` snapshot without forcing other systems to
- These types are the serialization/persistence contract -- all persisted episode data must conform

**Deliverable**: Replay contract types with full field definitions and docstrings.

**Dependencies**: WP-1.2 (for `WorldSnapshot`, `Position`).

---

### WP-1.4: Framework Config Types

**Goal**: Define the new config structure at the framework level.

**Module**: `axis/framework/config.py`

**Types to define**:

```
GeneralConfig
    seed: int

ExecutionConfig
    max_steps: int

LoggingConfig
    enabled: bool
    console_enabled: bool
    # ... (carry forward from current)

BaseWorldConfig
    grid_width: int
    grid_height: int
    obstacle_density: float

FrameworkConfig
    general: GeneralConfig
    execution: ExecutionConfig
    world: BaseWorldConfig
    logging: LoggingConfig

ExperimentConfig
    system_type: str
    experiment_type: ExperimentType
    framework: FrameworkConfig          # or inline: general, execution, world, logging
    system: dict[str, Any]
    num_episodes_per_run: int
    agent_start_position: Position
    # OFAT fields:
    parameter_path: str | None          # prefixed: "framework.world.grid_width" or "system.policy.temperature"
    parameter_values: tuple[Any, ...] | None
```

**Key design notes**:
- Based on Q6=C: `general`, `execution`, `world`, `logging` stay as flat top-level sections; `system` is a dict
- OFAT parameter paths use prefixed dot-paths (Q7=A): `"framework.execution.max_steps"` or `"system.policy.temperature"`
- The framework validates framework sections. The system validates `system: dict` at instantiation time.
- `ExperimentType` carries forward (`single_run`, `ofat`)

**Deliverable**: Config types, validation logic for OFAT paths, `set_config_value` / `get_config_value` adapted for the new split.

**Dependencies**: WP-1.2 (for `Position`, `BaseWorldConfig`).

---

## Phase 2 -- Extraction and Conformance

Move existing code into the new structure and make System A conform to the SDK interfaces. This is the heaviest refactoring phase.

### WP-2.1: World Extraction

**Goal**: Move `World`, `Cell`, `CellType`, `create_world` and world-related types from `axis_system_a` to `axis/world/`. Adapt `create_world` to accept `BaseWorldConfig`.

**Touches**:
- `axis_system_a/world.py` -> `axis/world/model.py`
- `axis_system_a/enums.py` (CellType moves to `axis/world/`)
- `axis_system_a/snapshots.py` (WorldSnapshot moves to `axis/world/` or `axis/sdk/`)

**Key work**:
- Move `World`, `Cell`, `CellType` to `axis/world/model.py`
- Move `WorldSnapshot`, `snapshot_world` to `axis/world/snapshots.py`
- Move `create_world` to `axis/world/factory.py`
- Implement `WorldView` protocol on `World` (read-only view)
- Keep backward-compatible re-exports in `axis_system_a` temporarily if needed during the transition

**Deliverable**: World model lives in `axis/world/`. `WorldView` protocol is implemented.

**Dependencies**: WP-1.2.

---

### WP-2.2: World Action Engine

**Goal**: Implement the framework-owned world action application layer. This is the code that applies agent actions to the world.

**Module**: `axis/world/actions.py`

**Key work**:
- Extract `_apply_movement` from `transition.py` into a framework-level action handler
- Extract `_apply_consume` from `transition.py` into a system-registered action handler
- Extract `_apply_regeneration` from `transition.py` into `axis/world/dynamics.py` (framework-owned, configurable)
- Define action handler registration: systems register handlers for their custom actions (e.g., `"consume"`)
- Implement `apply_action(world, action_str, context) -> ActionOutcome`
- Base actions (`up`, `down`, `left`, `right`, `stay`) are built-in
- System-specific actions are registered at system instantiation

**Key design note**: This is where the Q2 decision (framework applies actions) materializes. The current `transition.py` is decomposed:

| Current location | New location | Owner |
|-----------------|-------------|-------|
| `_apply_regeneration` | `axis/world/dynamics.py` | Framework |
| `_apply_movement` | `axis/world/actions.py` | Framework (base action) |
| `_apply_consume` | `axis/systems/system_a/actions.py` | System A (registered handler) |
| Energy computation | `axis/systems/system_a/transition.py` | System A |
| Memory update | `axis/systems/system_a/transition.py` | System A |
| Termination check | `axis/systems/system_a/transition.py` | System A |
| Snapshot capture | `axis/world/snapshots.py` (world) + system (agent) | Split |

**Deliverable**: Working action engine. Regen runs as framework step. Movement is framework-handled. Consume is system-registered. `ActionOutcome` returned to caller.

**Dependencies**: WP-2.1, WP-1.2.

---

### WP-2.3: System A Conformance -- Internal Restructure

**Goal**: Refactor System A's internal modules into the new package location and wrap them as SDK-conforming implementations.

**Module**: `axis/systems/system_a/`

**Key work**:
- Create `SystemA` class implementing `SystemInterface`
- Wrap `build_observation` into `SystemASensor` implementing `SensorInterface`
- Wrap `compute_hunger_drive` into `SystemAHungerDrive` implementing `DriveInterface`
- Wrap `select_action` into `SystemAPolicy` implementing `PolicyInterface`
- Refactor `transition.py::step()` into `SystemATransition` implementing `TransitionInterface`
  - Remove world mutation logic (now in WP-2.2)
  - Keep energy computation, memory update, termination check
  - Accept `ActionOutcome` from framework instead of mutating world directly
- Implement `SystemA.step()` as the orchestration of: sensor -> drive -> policy -> action intent -> (framework applies action) -> transition with outcome
- Define `SystemAConfig` as a typed Pydantic model that validates from `dict[str, Any]`
  - Contains: `AgentConfig`, `PolicyConfig`, `TransitionConfig`, `WorldDynamicsConfig` (regen params)
- Implement `SystemA.vitality()` returning `energy / max_energy`

**Important**: `SystemA.step()` must produce trace data conforming to `BaseStepTrace`, with System A-specific data (drive output, decision trace, transition details) packed into `system_data`.

**Deliverable**: `SystemA` class that conforms to `SystemInterface`. All System A logic preserved. Behavior identical to current system.

**Dependencies**: WP-2.1, WP-2.2, WP-1.1, WP-1.3.

---

### WP-2.4: System A Test Suite

**Goal**: Write the new test suite for the refactored System A. Behavioral equivalence tests ensure the refactored system produces identical results to the original.

**Key work**:
- Unit tests for each sub-component (`SystemASensor`, `SystemAHungerDrive`, `SystemAPolicy`, `SystemATransition`)
- Integration test: `SystemA.step()` produces correct `StepOutput` for known inputs
- Behavioral equivalence: run the same scenario (seed, config, world) through both old `run_episode` and new `SystemA` -- results must match exactly
- Test `SystemAConfig` validation from dict
- Test vitality computation
- Test action registration (consume handler)

**Deliverable**: Comprehensive test suite under `tests/systems/system_a/`. All tests green.

**Dependencies**: WP-2.3.

---

## Phase 3 -- Framework Alignment

Make the experimentation framework system-agnostic by routing through the SDK interfaces.

### WP-3.1: System Registry

**Goal**: Implement the system registry and factory mechanism.

**Module**: `axis/framework/registry.py`

**Key work**:
- `SYSTEM_REGISTRY: dict[str, SystemFactory]`
- `SystemFactory` protocol: `(system_config: dict, framework_config: FrameworkConfig) -> SystemInterface`
- `get_system(system_type: str) -> SystemFactory` with clear error on unknown type
- Register `SystemA` at import time
- `register_system(type_str, factory)` for programmatic registration

**Deliverable**: Working registry. `get_system("system_a")` returns a factory that creates a `SystemA` instance.

**Dependencies**: WP-1.1, WP-2.3.

---

### WP-3.2: Framework Episode Runner

**Goal**: Implement the framework-owned episode execution loop that works with any `SystemInterface`.

**Module**: `axis/framework/runner.py`

**Key work**:
- `run_episode(system, world, framework_config, rng) -> BaseEpisodeTrace`
- Step loop:
  1. Framework captures `world_before` snapshot
  2. Framework runs world dynamics (regeneration) per config -> captures intermediate snapshot if applicable
  3. Framework builds `WorldView` from current world state
  4. Framework calls `system.step(world_view, agent_state, rng)` -> `StepOutput`
  5. Framework applies action to world via action engine (WP-2.2) -> `ActionOutcome`
  6. System receives outcome (via callback or second-phase call -- design detail to resolve in spec)
  7. Framework captures `world_after` snapshot
  8. Framework checks termination (system-signaled or `max_steps`)
  9. Framework builds `BaseStepTrace` from all data
- Episode termination: system returns `terminated=True` OR step count reaches `max_steps`
- `TerminationReason`: `"max_steps_reached"` (framework) or system-provided string

**Design note on step flow**: The Q1=A decision (opaque step) combined with Q2=A (framework applies actions) creates a subtle question: does the framework call `system.step()` to get the action intent, then apply it, then tell the system the outcome? This suggests a two-call pattern per step:

```
Option A: system.step() returns action intent, framework applies, framework calls system.process_outcome()
Option B: system.step() returns action intent + a partial state; framework applies action and calls system.finalize(outcome)
Option C: system.step() receives a callback/world-proxy that handles application internally
```

**Recommendation**: Option A is cleanest. The `SystemInterface` gets two methods: `decide(world_view, agent_state, rng) -> ActionIntent` and `transition(agent_state, action_outcome, observation) -> TransitionOutput`. The framework orchestrates: decide -> apply -> observe -> transition. This preserves opaque system internals while giving the framework control of world mutation.

This is a refinement of the Q1 answer -- the system still owns all its internal logic, but the framework needs the action *before* it can apply it to the world, and the system needs the outcome *after*.

**Deliverable**: Generic episode runner that works with any registered system.

**Dependencies**: WP-2.2, WP-1.1, WP-1.3, WP-3.1.

---

### WP-3.3: Framework Run and Experiment Executors

**Goal**: Refactor `RunExecutor` and `ExperimentExecutor` to be system-agnostic.

**Module**: `axis/framework/run.py`, `axis/framework/experiment.py`

**Key work**:
- `RunExecutor` receives a `SystemInterface` (resolved from registry) instead of calling `run_episode` / `create_world` directly
- `RunExecutor` uses the framework episode runner (WP-3.2) instead of System A's `run_episode`
- `ExperimentExecutor` resolves system type from `ExperimentConfig.system_type`, looks up registry, creates system instance
- OFAT `resolve_run_configs` works with new `ExperimentConfig`: handles prefixed paths, delegates system path validation to system's config handler
- `ExperimentConfig` carries `system_type` field
- Run summary computation generalized (may need to use vitality instead of raw energy)

**Key design note**: `RunSummary` currently uses System A-specific metrics (`mean_final_energy`, `death_rate`, `consumption_count`). These need to become:
- Framework-level: `mean_steps`, `std_steps`, `mean_final_vitality`, `std_final_vitality`, `death_rate` (vitality-based)
- System-specific summary data: consumption count, etc. (in a `system_summary` dict or similar)

**Deliverable**: `RunExecutor` and `ExperimentExecutor` that work with any system. OFAT works with prefixed paths.

**Dependencies**: WP-3.2, WP-3.1, WP-1.4.

---

### WP-3.4: Persistence Layer Adaptation

**Goal**: Adapt `ExperimentRepository` for multi-system support.

**Module**: `axis/framework/persistence/` (restructured from current `repository.py`)

**Key work**:
- Experiment metadata includes `system_type`
- Serialization uses `BaseStepTrace` / `BaseEpisodeTrace` for episode data (system data is serialized as part of the dict)
- Deserialization loads base trace data generically; system adapter can rehydrate `system_data` into typed objects if needed
- Repository layout unchanged (experiment -> runs -> episodes) per stability boundary
- Immutable/mutable artifact distinction preserved
- Resume logic checks `system_type` consistency (cannot resume an experiment with a different system type)
- Config artifacts store the new `ExperimentConfig` format (with `system_type`, `framework`, `system` sections)

**Deliverable**: Repository handles multi-system artifacts. Resume works with system type awareness.

**Dependencies**: WP-3.3, WP-1.3, WP-1.4.

---

### WP-3.5: CLI Adaptation

**Goal**: Update the CLI for multi-system support.

**Module**: `axis/framework/cli/` (restructured)

**Key work**:
- `axis experiments run` accepts system type (from config or `--system` flag)
- `axis experiments resume` reads system type from persisted experiment metadata
- `axis visualize` resolves system type from experiment metadata (for adapter selection)
- CLI imports framework executors, not System A code directly
- System registry is used for system resolution
- Help text updated for multi-system awareness

**Deliverable**: CLI works with any registered system. System selection is explicit.

**Dependencies**: WP-3.3, WP-3.4, WP-3.1.

---

### WP-3.6: Framework Test Suite

**Goal**: Test the framework components independently of any specific system.

**Key work**:
- Test episode runner with a mock `SystemInterface` (simple echo system)
- Test `RunExecutor`, `ExperimentExecutor` with mock system
- Test OFAT path resolution with prefixed paths
- Test registry lookup and error handling
- Test repository with new config/trace formats
- Test resume with system type consistency
- Test CLI argument parsing (unit level)

**Deliverable**: Framework test suite under `tests/framework/`. All tests green.

**Dependencies**: WP-3.2 through WP-3.5.

---

## Phase 4 -- Contract Stabilization and Visualization

Align the visualization layer with the multi-system architecture.

### WP-4.1: Visualization Base Layer Extraction

**Goal**: Separate the generic visualization components (grid rendering, controls, state machine) from System A-specific content.

**Module**: `axis/visualization/`

**Key work**:
- Move generic components to `axis/visualization/`:
  - `GridWidget` (cell rendering, agent marker, resource display)
  - `ReplayControlsPanel`, `StatusPanel`
  - `ViewerState`, state transitions
  - `PlaybackController`
  - `ReplayAccessService` (reads `BaseEpisodeTrace` from repository)
- `SnapshotResolver` generalized: works with `BaseStepTrace` mandatory snapshots (`BEFORE`, `AFTER_ACTION`) + handles optional intermediate snapshots from `intermediate_snapshots` dict
- `ViewModelBuilder` split: base builder (grid, agent, vitality, action) + system adapter call for detail views
- `StatusPanel` shows vitality instead of raw energy (or system adapter provides label)

**Deliverable**: Generic visualization that can render any system's base replay data (grid, agent position, vitality, actions).

**Dependencies**: WP-1.3, WP-3.4.

---

### WP-4.2: Visualization Adapter Interface

**Goal**: Define and implement the `SystemVisualizationAdapter` protocol.

**Module**: `axis/sdk/visualization.py`, `axis/visualization/adapter.py`

**Key work**:
- Define `SystemVisualizationAdapter` protocol:
  ```
  build_step_analysis(step_trace: BaseStepTrace) -> list[AnalysisSection]
  build_overlays(step_trace: BaseStepTrace) -> list[OverlayData] | None
  phase_names() -> list[str]        # e.g., ["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]
  vitality_label() -> str            # e.g., "Energy" for System A
  format_vitality(value: float) -> str  # e.g., "3.45 / 5.00"
  ```
- Define `AnalysisSection` and `OverlayData` types
- Framework visualization calls adapter for system-specific content areas
- Adapter is resolved from system registry (each system provides its visualization adapter)

**Deliverable**: Adapter protocol defined. Framework visualization integrates adapter calls.

**Dependencies**: WP-4.1, WP-1.1.

---

### WP-4.3: System A Visualization Adapter

**Goal**: Implement `SystemAVisualizationAdapter` that preserves the current rich visualization for System A.

**Module**: `axis/systems/system_a/visualization.py`

**Key work**:
- Extract current `StepAnalysisPanel` rendering logic into `SystemAVisualizationAdapter.build_step_analysis()`
  - Hunger drive activation display
  - Observation table
  - Decision pipeline (softmax, probabilities, selected action)
- Extract debug overlay construction into `build_overlays()`
  - Action preference overlay
  - Drive contribution overlay
  - Consumption opportunity overlay
- `phase_names()` returns `["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]`
- `vitality_label()` returns `"Energy"`
- `format_vitality()` formats energy with max

**Key note**: This adapter reads `system_data` from `BaseStepTrace` and deserializes System A-specific types (`HungerDriveOutput`, `DecisionTrace`) to build its detailed views.

**Deliverable**: Full System A visualization preserved through the adapter pattern. Behavior identical to current visualization.

**Dependencies**: WP-4.2, WP-2.3.

---

### WP-4.4: Visualization Test Suite

**Goal**: Test the visualization layer with both generic and System A-specific content.

**Key work**:
- Test base rendering with a mock system (no adapter -- base grid, agent, vitality only)
- Test System A adapter produces correct analysis sections and overlays
- Test snapshot resolver with 2-phase and 3-phase step traces
- Test playback controller with variable phase counts

**Deliverable**: Visualization test suite. All tests green.

**Dependencies**: WP-4.1 through WP-4.3.

---

## Phase 5 -- Validation via Second System

Prove the architecture works by adding a second system without modifying framework code.

### WP-5.1: System A+W Design and Implementation

**Goal**: Implement a second system (`SystemAPlusW`) that demonstrates the framework's extensibility. This system should be a meaningful variant -- e.g., an agent that uses the world model and/or memory in its decision process.

**Module**: `axis/systems/system_a_plus_w/`

**Key work**:
- Define `SystemAPlusWConfig` (validated from dict)
- Implement `SystemAPlusW` conforming to `SystemInterface`
- Different internal pipeline (e.g., additional drives, memory-aware policy, or world model)
- Register in system registry
- Provide `SystemAPlusWVisualizationAdapter` (can be minimal initially)

**Constraint**: **No framework code modifications** should be needed. If any are, it's a signal that the interfaces need refinement.

**Deliverable**: Second system running through the framework.

**Dependencies**: All of Phase 3 and Phase 4.

---

### WP-5.2: Cross-System Validation

**Goal**: Run comparative experiments and visualization across both systems.

**Key work**:
- Run `system_a` experiment through the new framework, verify results
- Run `system_a_plus_w` experiment through the same framework
- Run OFAT experiment comparing a parameter across both systems (or within each)
- Visualize both systems' episodes through the unified visualization
- Verify: framework code was not modified for System A+W

**Deliverable**: Both systems run, persist, resume, and visualize correctly through the shared framework.

**Dependencies**: WP-5.1.

---

### WP-5.3: Cleanup and Removal of Legacy Package

**Goal**: Remove the old `axis_system_a` package now that everything lives in `axis/`.

**Key work**:
- Remove `src/axis_system_a/` entirely
- Remove old test files that reference the legacy package
- Update `pyproject.toml` to remove old package
- Verify all tests pass with only the new `axis` package
- Update CLI entry points

**Deliverable**: Single `axis` package. No legacy code remaining.

**Dependencies**: WP-5.2, full confidence that the new structure is complete.

---

## Phase Summary

```
Phase 0 -- Preparation                    [2 WPs]
  WP-0.1  Package scaffold
  WP-0.2  Test infrastructure

Phase 1 -- SDK and Contracts               [4 WPs]
  WP-1.1  Core SDK interfaces
  WP-1.2  World contracts
  WP-1.3  Replay contract
  WP-1.4  Framework config types

Phase 2 -- Extraction and Conformance      [4 WPs]
  WP-2.1  World extraction
  WP-2.2  World action engine
  WP-2.3  System A conformance
  WP-2.4  System A test suite

Phase 3 -- Framework Alignment             [6 WPs]
  WP-3.1  System registry
  WP-3.2  Framework episode runner
  WP-3.3  Run and experiment executors
  WP-3.4  Persistence adaptation
  WP-3.5  CLI adaptation
  WP-3.6  Framework test suite

Phase 4 -- Visualization                   [4 WPs]
  WP-4.1  Base layer extraction
  WP-4.2  Adapter interface
  WP-4.3  System A visualization adapter
  WP-4.4  Visualization test suite

Phase 5 -- Validation                      [3 WPs]
  WP-5.1  System A+W implementation
  WP-5.2  Cross-system validation
  WP-5.3  Legacy cleanup
                                     Total: 23 WPs
```

---

## Dependency Graph (Coarse)

```
WP-0.1 ─────────────────────────────────────┐
  │                                          │
WP-0.2                                       │
                                             │
WP-1.1 ──┬── WP-1.2 ──┬── WP-1.3           │
          │             │                     │
          │             └── WP-1.4           │
          │                   │               │
          │    WP-2.1 ── WP-2.2              │
          │         └──────┬──┘               │
          │                │                  │
          └──── WP-2.3 ───┘                  │
                  │                           │
               WP-2.4                         │
                  │                           │
          WP-3.1─┤                            │
                 │                            │
          WP-3.2─┤                            │
                 │                            │
          WP-3.3─┤                            │
                 │                            │
          WP-3.4─┤                            │
                 │                            │
          WP-3.5─┘                            │
                 │                            │
          WP-3.6                              │
                 │                            │
          WP-4.1─┤                            │
                 │                            │
          WP-4.2─┤                            │
                 │                            │
          WP-4.3─┘                            │
                 │                            │
          WP-4.4                              │
                 │                            │
          WP-5.1                              │
                 │                            │
          WP-5.2                              │
                 │                            │
          WP-5.3 ─────────────────────────────┘
```

---

## Design Refinement Note

**WP-3.2 surfaces a step-flow refinement** that deserves explicit attention:

The Q&A decided: opaque `system.step()` (Q1=A) + framework applies actions (Q2=A). These two decisions create a natural two-phase step:

1. **System decides**: `system.decide(world_view, state, rng) -> (action, decision_trace)`
2. **Framework applies**: `world.apply_action(action) -> ActionOutcome`
3. **System transitions**: `system.transition(state, outcome, observation) -> (new_state, trace)`

This refines the single `system.step()` into `decide()` + `transition()`, which is the minimal decomposition needed for framework-owned world mutation. The system still owns all internal logic (drives, policy, memory, energy) -- the framework just needs the action intent *before* it can modify the world.

**This should be confirmed during WP-1.1 (interface definition) before WP-2.3 implements it.**

---

## Risks Carried Forward

| Risk | Phase affected | Mitigation |
|------|---------------|------------|
| Transition decomposition (splitting `transition.py` 6-phase pipeline) | Phase 2 | WP-2.4 equivalence tests catch regressions |
| OFAT parameter path migration | Phase 3 | Test OFAT thoroughly in WP-3.6 |
| World action extensibility (Q2 follow-up from your answer) | Phase 2 | Design the action handler registration carefully in WP-2.2 |
| Visualization adapter richness vs generality | Phase 4 | Start with System A adapter that preserves current quality |
| Two-phase step refinement (decide + transition) | Phase 1-2 | Resolve in WP-1.1 before coding |
| New test suites may miss edge cases covered by old tests | All phases | Review old test coverage before writing new suites |
