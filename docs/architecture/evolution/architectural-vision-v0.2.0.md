# AXIS Modular Framework -- Architectural Vision

**Version**: v0.2.0 (target)
**Predecessor**: AXIS System A v0.1.0
**Status**: Approved architectural direction

---

## 1. Context and Intent

AXIS v0.1.0 is a fully functional simulation framework implementing **System A**: a minimal mechanistic agent with a single hunger drive, navigating a 2D grid world. The system is complete -- 1215+ tests, deterministic execution, full traceability, OFAT experimentation, resume support, and a PySide6 replay visualization.

The project's research question is:

> How much adaptive and goal-directed behavior can emerge from minimal mechanistic systems before introducing richer representational structures?

Answering this requires building and comparing **multiple systems** of increasing complexity -- System A (baseline), System A+W (with world model), and further variants. The current architecture cannot support this: System A's logic is woven into the execution framework, persistence layer, and visualization. Adding a second system would require duplicating or forking the framework.

This document defines the architectural vision for **AXIS v0.2.0**: a modular framework that separates system behavior from execution infrastructure, enabling multiple systems to coexist under a shared experimentation, persistence, and visualization framework.

---

## 2. Guiding Principles

### 2.1 The Core Separation

```
Systems define behavior.
Frameworks define execution.
Contracts define integration.
```

A **System** is a composition of components that maps:

> (world_view, agent_state) -> (action, new_state, trace)

It includes: agent state representation, sensor model, drives, policy, transition logic.
It excludes: episode execution, experiment orchestration, world mutation, persistence, visualization.

### 2.2 Global System Assumptions

All systems within the AXIS framework share fundamental structural properties. These are not optional -- they are framework-level invariants.

1. **Energy-based state**: Every system maintains an explicit energy scalar, observable as a normalized vitality metric `[0, 1]`.
2. **Drive-based modulation**: Every system implements one or more drives that modulate action selection. Drive outputs must be traceable.
3. **Policy-driven action selection**: Action selection is governed by a policy component consuming observations, internal state, and drive outputs.
4. **Framework-owned world**: Systems interact with the world through defined interfaces. They do not own or directly mutate it.
5. **Explicit transition function**: State evolution is deterministic given inputs. Transitions produce structured, traceable output.
6. **Step-level traceability**: Every system produces trace data conforming to the global replay contract.

These assumptions enable system interchangeability, experiment comparability, and unified visualization.

### 2.3 Immutability and Determinism

These carry forward from v0.1.0 as non-negotiable invariants:

- All value types, configs, results, and trace data are frozen Pydantic models
- The World is the sole mutable container in the runtime
- Execution is fully deterministic given a seed
- State transitions produce new immutable instances, never mutation

---

## 3. System Architecture

### 3.1 Package Structure

```
src/axis/
    sdk/                    # Interfaces, contracts, base types
    framework/              # Execution, persistence, config, CLI
    world/                  # World model, factory, action engine, dynamics
    systems/
        system_a/           # System A implementation
        system_a_plus_w/    # System A+W implementation (future)
    visualization/          # Replay viewer, adapter framework
```

Single installable package. Import paths: `from axis.sdk import SystemInterface`, `from axis.framework import ExperimentExecutor`, `from axis.systems.system_a import SystemA`.

### 3.2 Layer Diagram

```
                ┌─────────────────────────────────────────────┐
                │              CLI / Entry Points              │
                └──────────────────┬──────────────────────────┘
                                   │
                ┌──────────────────▼──────────────────────────┐
                │         Experimentation Framework            │
                │  ExperimentExecutor, RunExecutor, Resume      │
                │  Config resolution, OFAT, seed handling       │
                └─────┬────────────────────┬──────────────────┘
                      │                    │
         ┌────────────▼─────────┐  ┌───────▼──────────────────┐
         │   System Registry     │  │   Persistence Layer       │
         │   (type -> factory)   │  │   ExperimentRepository    │
         └────────────┬─────────┘  │   JSON artifacts, resume  │
                      │            └───────┬──────────────────┘
         ┌────────────▼─────────┐          │
         │   Framework Runner    │          │
         │   Episode loop        │          │
         │   Step lifecycle      │          │
         └──┬─────────────┬─────┘          │
            │             │                │
   ┌────────▼───┐   ┌────▼────────┐       │
   │  System     │   │  World       │       │
   │  (via SDK)  │   │  Framework   │       │
   │  decide()   │   │  Regen, move │       │
   │  transition()│  │  Action API  │       │
   └─────────────┘   └─────────────┘       │
                                           │
                ┌──────────────────────────▼───────────────────┐
                │            Visualization Layer                │
                │  Base: grid, agent, controls, state machine   │
                │  Adapter: system-specific analysis, overlays  │
                │  Replay Contract -> ViewModels -> Widgets     │
                └─────────────────────────────────────────────┘
```

### 3.3 Dependency Direction

```
SDK (interfaces, contracts)          -- depends on nothing
World Framework                      -- depends on SDK types
Framework (execution, persistence)   -- depends on SDK, World
Systems (System A, A+W)             -- depends on SDK, World
Visualization                        -- depends on SDK (replay contract), Framework (persistence)
CLI                                  -- depends on Framework, Registry
```

Systems never depend on the Framework. The Framework never depends on any specific System. This is the central architectural constraint.

---

## 4. System SDK

### 4.1 SystemInterface

The primary contract between a system and the framework. The framework interacts with systems exclusively through this interface.

```
SystemInterface
    system_type() -> str
    action_space() -> tuple[str, ...]

    initialize_state(system_config: dict) -> AgentState
    vitality(agent_state: AgentState) -> float       # [0, 1]

    decide(world_view, agent_state, rng)
        -> DecideResult(action: str, decision_data: dict)

    transition(agent_state, action_outcome, new_observation)
        -> TransitionResult(new_state: AgentState, trace_data: dict,
                            terminated: bool, termination_reason: str | None)
```

**Two-phase step contract**: The framework calls `decide()` to get the action intent, applies it to the world, then calls `transition()` with the outcome. This is necessary because the framework owns world mutation (Section 5) but the system must choose the action first.

```
Framework step lifecycle:
  1. world_before = snapshot(world)
  2. run world dynamics (regen)        -- framework-owned, configurable
  3. world_after_dynamics = snapshot(world)  -- optional intermediate
  4. world_view = read_only(world)
  5. observation = system.sensor.observe(world_view, position)
  6. decide_result = system.decide(world_view, agent_state, rng)
  7. action_outcome = world.apply_action(decide_result.action)
  8. world_after = snapshot(world)
  9. new_observation = system.sensor.observe(world_view, position)
  10. transition_result = system.transition(agent_state, action_outcome, new_observation)
  11. check termination (system-signaled or max_steps)
  12. build BaseStepTrace
```

### 4.2 Sub-Component Interfaces

Systems must implement these internally. The framework does not call them directly -- they exist to enforce structural consistency and enable testing, inspection, and documentation.

```
SensorInterface
    observe(world_view, position) -> Observation     # system-defined type

DriveInterface
    compute(agent_state, observation) -> DriveOutput  # system-defined type

PolicyInterface
    select(drive_outputs, observation, rng) -> PolicyResult

TransitionInterface
    transition(agent_state, action_outcome, observation)
        -> TransitionResult
```

Every system must have at least one `DriveInterface` implementation and a `PolicyInterface` implementation. This is a structural requirement, not a framework dispatch mechanism.

### 4.3 System Registration

Explicit code-level registry:

```python
SYSTEM_REGISTRY: dict[str, SystemFactory] = {
    "system_a": SystemA.create,
    "system_a_plus_w": SystemAPlusW.create,
}
```

No plugin system, no dynamic discovery. Systems are registered at import time. Adding a new system requires a code change to the registry -- this is acceptable and intentional for this milestone.

---

## 5. World Framework

### 5.1 Ownership Model

The World is **framework-owned**. Systems never hold a mutable reference to it. They receive a read-only `WorldView` for observation and receive `ActionOutcome` results after the framework applies their actions.

```
World (mutable, framework-owned)
    ├── grid: Cell[height][width]
    ├── agent_position: Position
    ├── width, height: int
    └── methods: get_cell, set_cell, is_within_bounds, is_traversable,
                 tick, extract_resource, snapshot

WorldView (read-only protocol, passed to systems)
    ├── get_cell(position) -> CellView
    ├── agent_position -> Position
    ├── width, height -> int
    └── is_within_bounds, is_traversable
```

### 5.2 World Dynamics

World dynamics (regeneration) are owned by the world itself, invoked by the framework:

- The framework calls `world.tick()` each step; the world applies its own dynamics internally
- Mode and rates are specified in the framework config's world section and stored in the world at creation
- Systems do not control regeneration -- they experience it as part of the world state they observe
- Resource extraction is also world-owned via `world.extract_resource(position, max_amount)`

This ensures cross-system consistency: two systems in the same world configuration see the same regeneration behavior. The world is a self-contained entity that knows how to evolve its own state.

### 5.3 Action Engine

The framework applies actions to the world on behalf of systems.

**Base actions** (framework-provided):
- `up`, `down`, `left`, `right` -- grid movement, handled by the framework
- `stay` -- no-op

**Extended actions** (system-registered):
- `consume` -- resource extraction, registered by System A
- Future systems may register additional action types

Each system declares its action space via `action_space() -> tuple[str, ...]`. The framework verifies that all declared actions have registered handlers before execution begins.

```python
ActionOutcome
    action: str
    moved: bool
    new_position: Position
    data: dict[str, Any]       # action-specific results (e.g., consumed amount)
```

The `ActionOutcome` tells the system what happened in the world as a result of its action. The `data` dict carries action-specific results (e.g., `{"consumed": True, "resource_consumed": 0.5}` for consume, `{"scan_total": 1.2}` for scan). The system uses this to update its internal state (energy, memory, etc.).

### 5.4 World Configuration

`BaseWorldConfig` is a minimal SDK type with only `world_type: str` as a framework-defined field. All other fields (grid dimensions, obstacles, regeneration parameters) pass through as Pydantic extras via `extra="allow"`, validated by the world factory for the specific world type.

For the built-in `grid_2d` world type, the factory validates extras against `Grid2DWorldConfig`:

| Field | Description |
|-------|-------------|
| `grid_width`, `grid_height` | Grid dimensions |
| `obstacle_density` | Fraction of cells that are obstacles |
| `resource_regen_rate` | Per-step regeneration amount |
| `regeneration_mode` | `"all_traversable"` or `"sparse_fixed_ratio"` |
| `regen_eligible_ratio` | Fraction of cells eligible for regeneration |

This design allows custom world types (hex grids, continuous spaces) to define their own configuration fields without modifying the SDK.

---

## 6. Experimentation Framework

### 6.1 Configuration Model

```
ExperimentConfig
    system_type: str                      # "system_a", "system_a_plus_w"
    experiment_type: ExperimentType        # single_run, ofat
    general: GeneralConfig                # seed
    execution: ExecutionConfig            # max_steps
    world: BaseWorldConfig                # grid_width, grid_height, obstacle_density
    logging: LoggingConfig                # enabled, console, jsonl, etc.
    system: dict[str, Any]                # opaque, validated by system
    num_episodes_per_run: int
    agent_start_position: Position
    parameter_path: str | None            # OFAT: prefixed dot-path
    parameter_values: tuple[Any, ...] | None
```

The config keeps framework sections flat (`general`, `execution`, `world`, `logging`) and the system section as an opaque dict. The system validates its own config blob at instantiation.

### 6.2 OFAT Parameter Paths

Prefixed dot-paths distinguish framework and system parameters:

```
"framework.execution.max_steps"         -- framework parameter
"framework.world.grid_width"            -- framework parameter
"system.policy.temperature"             -- system-specific parameter
```

The framework resolves framework paths directly. For system paths, it delegates to the system's config handler or applies dict-level updates.

### 6.3 Execution Chain

```
ExperimentExecutor
    resolve_run_configs(ExperimentConfig) -> tuple[RunConfig, ...]
    for each RunConfig:
        system = REGISTRY[config.system_type].create(config.system, config)
        RunExecutor(system).execute(run_config)

RunExecutor
    resolve_episode_seeds(num_episodes, base_seed)
    for each seed:
        world = create_world(config.world, start_position, seed)
        system.register_actions(world)    # register consume handler, etc.
        framework_runner.run_episode(system, world, config, rng)
            -> BaseEpisodeTrace

FrameworkRunner.run_episode
    state = system.initialize_state(system_config)
    for timestep in range(max_steps):
        ... (step lifecycle from Section 4.1) ...
    -> BaseEpisodeTrace
```

The experiment framework is fully system-agnostic. It never imports system code directly. All interaction goes through `SystemInterface`.

### 6.4 Resume

Run-level granularity preserved from v0.1.0:

- A run is either fully complete (skip) or fully re-executed
- Resume re-resolves all run configs deterministically
- Experiment metadata now includes `system_type` for consistency checking
- Cannot resume an experiment with a different system type

### 6.5 Termination

Dual termination model:

| Source | Mechanism | Reason |
|--------|-----------|--------|
| **Framework** | `timestep >= max_steps` | `"max_steps_reached"` |
| **System** | `transition_result.terminated == True` | System-provided string (e.g., `"energy_depleted"`) |

The framework checks both after each step. System termination takes priority (reported first in the trace).

---

## 7. Replay Contract

### 7.1 Base Step Trace

The global replay contract defines the system-agnostic data that every step must produce:

```
BaseStepTrace
    timestep: int
    action: str
    world_before: WorldSnapshot              # mandatory
    world_after: WorldSnapshot               # mandatory
    intermediate_snapshots: dict[str, WorldSnapshot]  # optional, named
    agent_position_before: Position
    agent_position_after: Position
    vitality_before: float                   # normalized [0, 1]
    vitality_after: float
    terminated: bool
    termination_reason: str | None
    system_data: dict[str, Any]              # system-specific, opaque
```

### 7.2 Snapshot Model

Two mandatory snapshots per step:

| Snapshot | Captures |
|----------|----------|
| `world_before` | World state before the system acts (after dynamics/regen) |
| `world_after` | World state after all mutations |

Systems may provide additional named snapshots via `intermediate_snapshots`. System A provides `"after_regen"` (world state after regeneration, before action application).

### 7.3 Extension Mechanism

System-specific trace data lives in `system_data: dict[str, Any]`:

- System A stores: `HungerDriveOutput`, `DecisionTrace`, transition details, memory state, detailed energy breakdown
- System A+W would store: additional drive outputs, world model state, planning trace
- The framework never reads `system_data` -- only the visualization adapter does

### 7.4 Episode Trace

```
BaseEpisodeTrace
    system_type: str
    steps: tuple[BaseStepTrace, ...]
    total_steps: int
    termination_reason: str
    final_vitality: float
    final_position: Position
```

---

## 8. Persistence Layer

### 8.1 Repository Layout

Preserved from v0.1.0, extended with system type awareness:

```
{repository_root}/
└── {experiment_id}/
    ├── experiment_config.json          # ExperimentConfig (with system_type)
    ├── experiment_metadata.json        # includes system_type
    ├── experiment_status.json
    ├── experiment_summary.json
    └── runs/
        └── {run_id}/
            ├── run_config.json
            ├── run_metadata.json
            ├── run_status.json
            ├── run_summary.json
            ├── run_result.json
            └── episodes/
                ├── episode_0001.json   # BaseEpisodeTrace
                └── ...
```

### 8.2 Serialization

- All artifacts use JSON via Pydantic `model_dump(mode="json")`
- Episode traces follow `BaseEpisodeTrace` schema
- `system_data` is serialized as a nested dict -- no type information needed at the framework level
- Each system's visualization adapter deserializes `system_data` into typed objects when needed

### 8.3 Backward Compatibility

**Clean break** from v0.1.0 artifacts. Pre-modularization experiment data is not loadable by the new framework. This avoids legacy code paths and keeps the codebase clean.

### 8.4 Summary Types

```
RunSummary
    num_episodes: int
    mean_steps, std_steps: float
    mean_final_vitality, std_final_vitality: float    # replaces energy
    death_rate: float                                  # vitality-based
    system_summary: dict[str, Any]                     # system-specific aggregates

ExperimentSummary
    num_runs: int
    run_entries: tuple[RunSummaryEntry, ...]            # with OFAT deltas
```

---

## 9. Visualization Layer

### 9.1 Architecture

Preserved from v0.1.0: strict unidirectional data flow, replay-based, read-only.

```
Repository -> ReplayAccessService -> SnapshotResolver -> ViewModelBuilder -> Widgets
     ^                                                                         |
     |                  (pure state transitions)                              |
     +---------------------------- signals -----------------------------------+
```

### 9.2 Generic Base Layer

The framework provides system-agnostic visualization:

| Component | Content |
|-----------|---------|
| `GridWidget` | Cell rendering (obstacle, empty, resource gradient), agent marker |
| `StatusPanel` | Step index, phase, playback mode, vitality (via adapter label) |
| `ReplayControlsPanel` | Step/play/pause/stop, phase selector |
| `PlaybackController` | Phase-aware navigation with variable phase counts |
| `ViewerState` | Immutable state with coordinate, playback mode, selections |

### 9.3 Phase Navigation

Fixed minimal set plus optional system-provided extras:

| Phase | Source | Guaranteed |
|-------|--------|------------|
| `BEFORE` | Framework | Yes |
| `AFTER_ACTION` | Framework | Yes |
| System-declared intermediates | System adapter | No |

System A declares: `["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]`.
A simpler system might declare only: `["BEFORE", "AFTER_ACTION"]`.

The `PlaybackController` adapts navigation to the available phase set. Navigation always works with at least two phases.

### 9.4 SystemVisualizationAdapter

Protocol that systems implement for rich visualization:

```
SystemVisualizationAdapter
    phase_names() -> list[str]
    vitality_label() -> str                              # e.g., "Energy"
    format_vitality(value: float, state: dict) -> str    # e.g., "3.45 / 5.00"

    build_step_analysis(step_trace: BaseStepTrace) -> list[AnalysisSection]
    build_overlays(step_trace: BaseStepTrace) -> list[OverlayData] | None
```

The adapter reads `system_data` from `BaseStepTrace` and constructs system-specific content:

**System A adapter** provides:
- Step analysis: hunger drive activation, observation table, decision pipeline (softmax, probabilities), outcome
- Debug overlays: action preference arrows, drive contribution bars, consumption opportunity indicators
- Phase names: `BEFORE`, `AFTER_REGEN`, `AFTER_ACTION`
- Vitality label: `"Energy"`
- Vitality format: `"3.45 / 5.00"` (energy / max_energy)

The adapter preserves the full richness of v0.1.0's visualization. No information is lost.

---

## 10. System A -- Refactored Architecture

System A is refactored from module-level functions into SDK-conforming classes, preserving identical behavior.

### 10.1 Component Map

| v0.1.0 Module | v0.2.0 Component | Interface |
|---------------|-------------------|-----------|
| `observation.py:build_observation` | `SystemASensor` | `SensorInterface` |
| `drives.py:compute_hunger_drive` | `SystemAHungerDrive` | `DriveInterface` |
| `policy.py:select_action` | `SystemAPolicy` | `PolicyInterface` |
| `transition.py:step` (agent logic) | `SystemATransition` | `TransitionInterface` |
| `transition.py:step` (world mutation) | `axis/world/actions.py` | Framework action engine |
| `transition.py:_apply_regeneration` | `axis/world/dynamics.py` | Framework world dynamics |
| `runner.py:episode_step` | `SystemA.decide()` + `SystemA.transition()` | `SystemInterface` |
| `runner.py:run_episode` | `axis/framework/runner.py` | Framework runner |
| `config.py:SimulationConfig` | `FrameworkConfig` + `SystemAConfig` | Split config |

### 10.2 SystemA Class

```
SystemA implements SystemInterface
    sensor: SystemASensor
    drive: SystemAHungerDrive
    policy: SystemAPolicy
    transition: SystemATransition
    config: SystemAConfig

    decide(world_view, agent_state, rng):
        observation = self.sensor.observe(world_view, position)
        drive_output = self.drive.compute(agent_state, observation)
        decision = self.policy.select(drive_output, observation, rng)
        return DecideResult(action=decision.action, data={...})

    transition(agent_state, action_outcome, new_observation):
        ... energy computation, memory update, termination check ...
        return TransitionResult(new_state, trace_data, terminated, reason)

    vitality(state):
        return state.energy / self.config.max_energy
```

### 10.3 SystemAConfig

Validated from `dict[str, Any]` (the opaque `system` section of `ExperimentConfig`):

```
SystemAConfig
    agent: AgentConfig              # initial_energy, max_energy, buffer_capacity
    policy: PolicyConfig            # selection_mode, temperature, stay_suppression, consume_weight
    transition: TransitionConfig    # move_cost, consume_cost, stay_cost, max_consume, energy_gain_factor
    # Note: WorldDynamicsConfig has been removed. Regeneration parameters
    # (resource_regen_rate, regeneration_mode, regen_eligible_ratio) now
    # live in BaseWorldConfig (the world: section of the config file).
```

### 10.4 Consume Action Handler

System A registers a `consume` action handler with the world framework:

```python
def handle_consume(world: MutableWorldProtocol, position: Position, context: dict) -> ActionOutcome:
    max_consume = context["max_consume"]
    delta = world.extract_resource(position, max_consume)
    return ActionOutcome(
        action="consume", moved=False, new_position=position,
        data={"consumed": delta > 0, "resource_consumed": delta},
    )
```

This handler is registered when the system is initialized for an episode. The framework calls it when the system's `decide()` returns `action="consume"`.

---

## 11. System A+W -- Anticipated Architecture

System A+W (A + World model) is the first validation target for the framework. It extends System A with:

- **World model**: Internal spatial representation built from observation history
- **Memory utilization**: The existing FIFO memory (populated but unused in System A) feeds the world model
- **Exploration drive**: A second drive that encourages visiting unexplored or resource-rich areas based on the world model
- **Modified policy**: Combines hunger drive and exploration drive outputs

### 11.1 Component Structure

```
SystemAPlusW implements SystemInterface
    sensor: SystemASensor                  # reuse from System A
    drives: [SystemAHungerDrive,           # reuse from System A
             ExplorationDrive]             # new: uses world model
    policy: SystemAPlusWPolicy             # new: combines two drives
    transition: SystemAPlusWTransition     # new: updates world model
    world_model: InternalWorldModel        # new: agent's spatial memory
```

The key validation question: can this system be added without modifying any framework code? If yes, the modular architecture is proven.

---

## 12. Data Flow -- Complete Step Lifecycle

```
    Framework                              System                    World
    ─────────                              ──────                    ─────
        │                                                              │
        ├── snapshot_before ◄──────────────────────────────────────────┤
        │                                                              │
        ├── world.tick() ────────────────────────────────────────────────►│
        │                                                              │
        ├── snapshot_intermediate (optional) ◄──────────────────────────┤
        │                                                              │
        ├── build_world_view ◄─────────────────────────────────────────┤
        │                                                              │
        ├── system.decide(world_view, state, rng) ────►│               │
        │                                              │               │
        │   [sensor: observe]                          │               │
        │   [drive: compute]                           │               │
        │   [policy: select]                           │               │
        │                                              │               │
        │◄──── DecideResult(action, data) ─────────────┤               │
        │                                                              │
        ├── world.apply_action(action) ────────────────────────────────►│
        │                                                              │
        │◄──── ActionOutcome ──────────────────────────────────────────┤
        │                                                              │
        ├── snapshot_after ◄───────────────────────────────────────────┤
        │                                                              │
        ├── system.transition(state, outcome, obs) ────►│              │
        │                                               │              │
        │   [energy update]                             │              │
        │   [memory update]                             │              │
        │   [termination check]                         │              │
        │                                               │              │
        │◄──── TransitionResult(new_state, trace) ──────┤              │
        │                                                              │
        ├── build BaseStepTrace                                        │
        │                                                              │
        ├── check termination (framework or system)                    │
        │                                                              │
        └── next step or finalize episode                              │
```

---

## 13. Cross-System Experimentation

The framework enables comparative experiments across systems:

```json
{
    "system_type": "system_a",
    "experiment_type": "ofat",
    "parameter_path": "system.policy.temperature",
    "parameter_values": [0.5, 1.0, 2.0],
    ...
}
```

```json
{
    "system_type": "system_a_plus_w",
    "experiment_type": "single_run",
    ...
}
```

Both experiments:
- Run through the same `ExperimentExecutor`
- Persist to the same repository with the same artifact structure
- Produce `BaseEpisodeTrace` conforming to the same replay contract
- Visualize through the same viewer (with system-specific adapters for detail views)
- Produce comparable `RunSummary` data (vitality-based metrics)

---

## 14. Success Criteria

This architectural vision is realized when:

1. System A runs entirely via `SystemInterface` -- no direct framework imports of system logic
2. System A+W can be implemented by adding files under `axis/systems/system_a_plus_w/` and a registry entry -- no framework code changes
3. Both systems execute through the same `ExperimentExecutor`
4. Both systems persist via the same `ExperimentRepository`
5. Both systems visualize through the same viewer, with system-appropriate detail views
6. OFAT parameter sweeps work for both framework and system parameters
7. Resume works with system type metadata
8. No hidden coupling between system and framework remains
9. All behavioral properties of v0.1.0 are preserved for System A (determinism, traceability, snapshot coverage)

---

## 15. Non-Goals (This Milestone)

- Full plugin system or dynamic system loading
- Performance optimization (parallel execution, caching)
- Multi-agent systems
- Learning or adaptation within episodes
- Non-grid world types (architecture supports them via the world registry, but none are implemented yet)
- Web-based visualization
- Backward compatibility with v0.1.0 artifacts

---

## 16. Risk Summary

| Risk | Impact | Mitigation |
|------|--------|------------|
| Transition decomposition breaks determinism | High | Behavioral equivalence tests: same seed -> same results before and after |
| Two-phase step (decide + transition) is awkward for System A | Medium | System A adapter wraps its existing single-pass logic cleanly |
| World action extensibility (future action types) | Medium | Action handler registration is simple dict-based; evolve when needed |
| Visualization adapter too generic, loses detail quality | Medium | System A adapter preserves current v0.1.0 visualization exactly |
| OFAT path migration introduces bugs | Medium | Thorough OFAT tests with both framework and system paths |
| New test suites miss old edge cases | Medium | Review old test coverage before writing new suites |

---

## 17. Relationship to Existing Documents

| Document | Role |
|----------|------|
| `docs/architecture/v0.1.0/*` | Authoritative description of the current system |
| `docs/specs/System A Baseline.md` | Formal specification of System A agent |
| `docs/specs/The_World.md` | Formal specification of the world model |
| `docs/specs/The_Sensor_Model.md` | Formal specification of the sensor model |
| `docs/architecture/evolution/modular-architecture-evolution.md` | Original vision document |
| `docs/architecture/evolution/modular-architecture-kickoff.md` | Current-state vs target-state analysis |
| `docs/architecture/evolution/modular-architecture-questions-answers.md` | All architectural decisions |
| `docs/architecture/evolution/modular-architecture-roadmap.md` | Implementation roadmap (23 work packages) |
| **This document** | Architectural vision for v0.2.0 |
