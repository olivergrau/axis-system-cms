# Modular Architecture Evolution -- Open Questions

**Purpose**: This document lists all architectural decisions that must be resolved before implementation begins. Each question includes answer suggestions to guide decision-making.

**How to use**: Read each question, consider the suggestions, and write your answer in the **Answer** field. A future Claude Code agent will read this document to proceed with implementation.

---

Please assume the following before reading the answers to the quetsions:

---

### **Global System Assumptions (Framework-Level Contracts)**

All systems implemented within the AXIS framework must adhere to a shared set of **fundamental assumptions and structural properties**.

These are **not optional design choices**, but **framework-level invariants** that the Experimentation Framework, Persistence Layer, and Visualization system rely on.

#### **1. Energy-Based State**

Every system must maintain an explicit **energy state** as part of the agent state.

* Energy is a primary scalar variable
* It influences system dynamics (e.g. survival, behavior modulation)
* It is updated during each transition step
* It must be observable and included in replay data

---

#### **2. Drive-Based Modulation (1–N Drives)**

Every system must implement **one or more drives** that influence decision-making.

* Drives produce signals that modulate the policy
* At least one drive must be present (e.g. Hunger in System A)
* Multiple drives are allowed and expected in extended systems
* Drive outputs must be traceable and optionally included in step-level data

---

#### **3. Policy-Driven Action Selection**

Action selection must be governed by a **policy component**.

* The policy consumes:

  * observations
  * internal state
  * drive outputs
* The policy produces:

  * action scores and/or probabilities
  * a selected action
* The decision process must be traceable for replay and debugging

---

#### **4. World Interaction Model**

All systems operate within a **framework-provided world**.

* Systems do not own the world
* Interaction with the world occurs through defined interfaces
* Actions must have well-defined effects on the world state
* World state changes must be captured in the transition trace

---

#### **5. Explicit Transition Function**

Each system must define a **transition function** that governs state evolution.

* Transitions are deterministic given:

  * current state
  * world state
  * selected action
* The transition must produce:

  * next agent state
  * updated world state (via framework interaction)
  * structured trace data

---

#### **6. Step-Level Traceability**

Every system must produce **structured step-level trace data**.

This includes, at minimum:

* observation
* drive outputs
* policy decision (scores/probabilities, selected action)
* transition results (state changes, energy update, world interaction)

This trace must conform to the **global replay contract**.

---

#### **7. Compatibility with the Replay Model**

All systems must produce outputs compatible with the **global replay model**:

* step-indexed execution
* phase-aware state snapshots (e.g. BEFORE, AFTER_REGEN, AFTER_ACTION)
* deterministic reconstruction from persisted data

---

### **Summary**

Any system integrated into the AXIS framework must conform to:

> an energy-driven, drive-modulated, policy-based agent model
> operating within a framework-owned world,
> with explicit transitions and fully traceable step-level behavior.

These assumptions form the **common foundation across all systems** and enable:

* system interchangeability
* experiment comparability
* unified visualization and analysis

---

## Q1. System Step Contract

**Context**: The vision document defines SDK sub-component interfaces (`DriveInterface`, `PolicyInterface`, `TransitionInterface`, `SensorInterface`) but also implies the framework orchestrates execution. Currently `runner.py:episode_step()` chains `compute_hunger_drive -> select_action -> transition.step` -- this is a System A-specific orchestration chain.

**Question**: Should the framework call a single opaque `system.step(state, observation) -> (action, new_state, trace)` per timestep, or should the framework orchestrate the sub-components individually (e.g., `system.sense()`, then `system.decide()`, then `system.transition()`)?

**Why it matters**: This determines where the per-step orchestration lives. Opaque step = systems own their internal pipeline. Framework-orchestrated = framework must understand the sub-component calling convention.

**Suggestions**:

- **(A) Single opaque `system.step()` (Recommended)**: The framework calls `system.step(state, observation)`. The system internally orchestrates its own sub-components. Sub-component interfaces exist for inspection, testing, and documentation -- not for framework-level dispatch. This preserves encapsulation and allows systems to have arbitrarily different internal pipelines.

- **(B) Framework orchestrates sub-components**: The framework calls `system.sensor.observe()`, then `system.drive.compute()`, then `system.policy.select()`, then `system.transition.step()` in a defined order. This gives the framework full visibility into the step pipeline but forces all systems into the same sub-component structure.

- **(C) Hybrid**: The framework calls `system.step()` but the `SystemInterface` also exposes sub-components for optional introspection. Systems that follow the standard pipeline get automatic debug/trace support; systems with custom pipelines still work but provide their own traces.

**Answer**:

Definitively (A) Single opaque system.step(). This gives max flexibility for the Systems to decide what to do.

---

## Q2. World Mutation Ownership

**Context**: The vision says the World is framework-owned. Currently, `transition.py:step()` directly mutates the World (applies regeneration, moves the agent, consumes resources). The system's transition function is both computing agent state changes *and* writing to the World.

**Question**: Who applies actions to the World -- the system or the framework?

**Why it matters**: This is the deepest decomposition question. It determines how `transition.py` is split and whether systems ever touch the World directly.

**Suggestions**:

- **(A) Framework applies actions to World (Recommended)**: The system returns an action intent (e.g., `Action.CONSUME`). The framework owns all World mutation: regeneration, movement, resource consumption. The system receives the outcome (consumed amount, new position, etc.) and updates its own internal state (energy, memory) accordingly. This cleanly separates world physics from agent logic.

- **(B) System mutates World directly**: Systems receive a mutable World reference and apply their own transitions, including world mutation. The framework trusts the system to follow world rules. Simpler to implement (keep `transition.py` mostly intact) but breaks world encapsulation.

- **(C) World exposes action API**: The World provides methods like `world.apply_move(action)`, `world.apply_consume(position, max_consume)`. The system calls these rather than mutating the grid directly. This is a middle ground -- systems interact with the world but through a controlled API.

**Answer**:

(A) - The Framework should apply actions to World. The Framework must own World mutations (and the World). But one question remains: What if we want to provide more than one world (with different features)? There must be a contract how a system can modify the world. So the Framework should apply the changes, but depending on the world those changes can be different, so it needs different methods (consume, remove obstacle or whatever). I think we must think about that a bit more.

---

## Q3. World Regeneration Ownership

**Context**: Currently, `_apply_regeneration()` runs every step as Phase 1 of the transition. It's a world-level process (all cells regenerate), not an agent action. In the vision, the World is a framework concern.

**Question**: Is world regeneration a framework responsibility (runs before the system is called each step) or a system responsibility (the system's transition triggers it)?

**Why it matters**: This affects the step lifecycle and snapshot timing. If regeneration is framework-owned, the framework captures pre-regen and post-regen snapshots. If system-owned, each system decides whether and how regeneration works.

**Suggestions**:

- **(A) Framework-owned (Recommended)**: Regeneration is a world-level process managed by the framework's step lifecycle. The framework runs regen before calling the system, captures the post-regen snapshot, then passes the observation to the system. This keeps world evolution consistent across systems.

- **(B) System-owned**: Each system triggers regeneration as part of its transition. Different systems could have different regen strategies. More flexible, but makes cross-system world consistency harder.

- **(C) Configurable per experiment**: The framework config specifies the world evolution strategy (regen mode, rates). The framework applies it. Systems don't control it. Similar to (A) but makes the configurability explicit.

**Answer**:

(C) Framework owned but configurable.

---

## Q4. Action Space Definition

**Context**: System A uses a fixed `Action` IntEnum with 6 values: `UP, DOWN, LEFT, RIGHT, CONSUME, STAY`. The drive output and policy pipeline use 6-element tuples indexed by this enum. Future systems might need different action spaces (e.g., no CONSUME, additional actions, continuous actions).

**Question**: Should the action space be fixed at the framework level (all systems use the same actions), or should each system define its own action space?

**Why it matters**: A fixed action space simplifies the framework (world knows how to apply every action), but limits future systems. A per-system action space is more flexible but requires the framework and world to handle unknown action types.

**Suggestions**:

- **(A) Shared base actions, extensible per system (Recommended)**: The framework defines base grid actions (`UP, DOWN, LEFT, RIGHT, STAY`) that the World knows how to apply. Systems can define additional system-specific actions (like `CONSUME`). The World provides an extension point for system-registered action handlers. The replay contract records actions using a string-based identifier rather than a fixed enum.

- **(B) Fixed framework-level action space**: All systems use the same `Action` enum. This is the simplest approach and works for the current milestone (System A and System A+W likely share the same action space). Limits future extensibility.

- **(C) Fully system-defined action space**: Each system declares its own action type. The framework treats actions as opaque values, only passing them between system and world. Maximum flexibility, but the framework and visualization cannot reason about actions.

**Answer**:

(A) - I follow your recommendation. 

---

## Q5. Package Structure

**Context**: Currently everything lives in one package: `axis_system_a`. The modular evolution introduces framework code, SDK interfaces, and (eventually) multiple systems. The package structure needs to accommodate this.

**Question**: What package structure should the modular architecture use?

**Why it matters**: Import paths, test organization, installability, and the daily developer experience all depend on this.

**Suggestions**:

- **(A) Single package with sub-packages (Recommended)**: One installable package `axis` with internal structure:
  ```
  src/axis/
      sdk/           # interfaces, base types, contracts
      framework/     # execution, persistence, config, CLI
      world/         # world model, world factory, action application
      systems/
          system_a/  # current System A, refactored to conform
      visualization/ # replay, UI (with system adapter hooks)
  ```
  Pros: one install, simple imports (`from axis.sdk import SystemInterface`), no cross-package dependency management. Cons: not independently versionable.

- **(B) Multiple packages in monorepo**: Three packages `axis-sdk`, `axis-framework`, `axis-system-a` in the same repo, each with their own `pyproject.toml`. Pros: clean dependency boundaries, independently installable. Cons: more complex build/install, cross-package development friction.

- **(C) Keep `axis_system_a`, add siblings**: Add `axis_sdk` and `axis_framework` as sibling packages. System A stays as `axis_system_a` but now depends on `axis_sdk`. Preserves backward compatibility of the existing package name.

**Answer**:

(A) - I follow your suggestions here. 

---

## Q6. Configuration Architecture

**Context**: `SimulationConfig` currently bundles 7 sub-configs: `general`, `world`, `agent`, `policy`, `transition`, `execution`, `logging`. Some are framework concerns (general, execution, logging), some are system-specific (agent, policy, transition), and some are mixed (world). The OFAT mechanism uses dot-path addressing (`"transition.energy_gain_factor"`) into this flat structure.

**Question**: How should the config be restructured for multi-system support?

**Why it matters**: Config structure affects experiment definition, OFAT sweeps, persistence, resume, and CLI. It's the most pervasive structural change.

**Suggestions**:

- **(A) Framework config + opaque system config blob (Recommended)**:
  ```python
  class ExperimentConfig:
      system_type: str                       # e.g., "system_a"
      framework: FrameworkConfig             # general, execution, logging, world
      system_config: dict[str, Any]          # system-specific, validated by system
      # OFAT fields...
  ```
  The system validates its own config blob at initialization. OFAT paths are prefixed: `"framework.execution.max_steps"` or `"system.policy.temperature"`. Pros: clean separation, no need for framework to know system config schema. Cons: system config is untyped at the framework level.

- **(B) Framework config + typed system config via generics**:
  ```python
  class ExperimentConfig(Generic[SC]):
      system_type: str
      framework: FrameworkConfig
      system_config: SC                      # SC = SystemAConfig, etc.
  ```
  Pros: full type safety. Cons: generics complicate serialization, persistence, and CLI.

- **(C) Unified config with system section**:
  ```python
  class ExperimentConfig:
      system_type: str
      general: GeneralConfig
      execution: ExecutionConfig
      world: WorldConfig
      system: dict[str, Any]                 # everything system-specific
  ```
  Similar to (A) but keeps some config flat. Simpler migration from current structure.

**Answer**:

(C) is ok for me. The untyped config is not a problem for me, it can be json and responsibility for the System is to parse this. 

---

## Q7. OFAT Parameter Path Mechanism

**Context**: The current OFAT mechanism uses `set_config_value(config, "transition.energy_gain_factor", value)` which addresses fields within `SimulationConfig` via dot-paths. After config decomposition, this addressing scheme needs to change.

**Question**: How should OFAT parameter paths work with the split config?

**Why it matters**: OFAT is core to the experimentation framework. The parameter addressing must work for both framework and system parameters, and must be compatible with persistence and resume.

**Suggestions**:

- **(A) Prefixed dot-paths (Recommended)**: Parameter paths gain a prefix indicating the config domain:
  - `"framework.execution.max_steps"` -- framework parameter
  - `"framework.world.grid_width"` -- framework parameter
  - `"system.policy.temperature"` -- system-specific parameter

  The framework handles framework paths natively. For system paths, it delegates to the system's config handler. Pros: clear, backward-expressible, extensible. Cons: slightly more verbose than current paths.

- **(B) Flat paths with auto-routing**: Keep current `"transition.energy_gain_factor"` style. The framework tries the framework config first; if not found, delegates to the system config. Pros: existing config files mostly work. Cons: ambiguity if framework and system have sections with the same name.

- **(C) Path scoped to config type**: OFAT config specifies which config to address:
  ```json
  { "parameter_scope": "system", "parameter_path": "policy.temperature" }
  ```
  Pros: explicit. Cons: more verbose config files.

**Answer**:

(A) Prefixed dot-paths

---

## Q8. Replay Contract: Trace Extensibility

**Context**: Currently `StepResult` contains System A-specific types (`HungerDriveOutput`, `DecisionTrace`). The global replay contract needs a system-agnostic base with system-specific extensions.

**Question**: How should system-specific trace data be carried in the replay contract?

**Why it matters**: This determines how trace data is serialized, deserialized, and consumed by the visualization layer.

**Suggestions**:

- **(A) Base trace + typed extension via `system_data: dict[str, Any]` (Recommended)**:
  ```python
  class BaseStepTrace:
      timestep: int
      action: str
      world_before: WorldSnapshot
      world_after: WorldSnapshot
      agent_position_before: Position
      agent_position_after: Position
      energy_before: float
      energy_after: float
      terminated: bool
      system_data: dict[str, Any]    # system-specific, opaque to framework
  ```
  System A stores its `HungerDriveOutput` and `DecisionTrace` as serialized dicts under `system_data`. Visualization uses a system adapter to interpret `system_data`. Pros: simple, extensible, no generics. Cons: loses Pydantic type safety for the extension portion.

- **(B) Generic typed trace**:
  ```python
  class StepTrace(Generic[SD]):
      # base fields...
      system_data: SD               # SD = SystemAStepData, etc.
  ```
  Pros: full type safety. Cons: generics make serialization/deserialization harder. Repository must know the system type to deserialize.

- **(C) Separate base and system trace files**: The repository stores `base_trace.json` (generic) and `system_trace.json` (system-specific) per episode. Visualization loads only what it needs. Pros: clean separation on disk. Cons: doubles file count, harder to correlate.

**Answer**:

(A) sounds plausible to mee.

---

## Q9. World Snapshot Model

**Context**: System A captures 3 world snapshots per step (before, after_regen, after_action) corresponding to its 6-phase transition pipeline. Future systems may have different phase structures. The replay contract must specify how many and which snapshots exist.

**Question**: What is the minimum world snapshot contract for the replay layer?

**Why it matters**: The `SnapshotResolver` and `PlaybackController` currently assume exactly 3 phases per step. The replay contract's phase model determines how navigation and rendering work.

**Suggestions**:

- **(A) Two mandatory snapshots + optional intermediates (Recommended)**: The base contract requires:
  - `world_before_action` -- world state before the system acts
  - `world_after_action` -- world state after all mutations

  Systems may provide additional named snapshots (e.g., System A adds `world_after_regen`). The `ReplayPhase` enum becomes dynamic or extensible. The visualization supports navigating base phases by default and system-provided phases via adapter.

- **(B) Keep 3 mandatory snapshots**: All systems must provide `before`, `after_regen`, `after_action`. Systems without a regen phase simply set `after_regen = before`. Pros: simple, consistent navigation. Cons: forces a phase structure that may not apply to all systems.

- **(C) System declares its phase set**: Each system registers its phases (e.g., `["BEFORE", "AFTER_REGEN", "AFTER_ACTION"]` for System A, `["BEFORE", "AFTER"]` for simpler systems). The visualization dynamically adapts to the phase set. Pros: fully flexible. Cons: visualization complexity increases.

**Answer**:

(A)

---

## Q10. Visualization Adapter

**Context**: The visualization currently builds System A-specific content: `StepAnalysisPanel` shows hunger drive activation, observation table, decision pipeline. Debug overlays show action preferences, drive contributions, consumption opportunities. For multi-system support, these need to become pluggable.

**Question**: How should system-specific visualization be integrated?

**Why it matters**: The current visualization is detailed and useful *because* it's System A-specific. The adapter must preserve this richness while being extensible.

**Suggestions**:

- **(A) Adapter with structured extension points (Recommended)**: Define a `SystemVisualizationAdapter` interface that systems implement:
  ```python
  class SystemVisualizationAdapter(Protocol):
      def build_step_analysis(self, step_trace) -> str | list[AnalysisSection]
      def build_overlays(self, step_trace) -> list[OverlayData] | None
      def phase_names(self) -> list[str]
  ```
  The framework visualization calls the adapter for system-specific content. System A's current `StepAnalysisPanel` logic moves into `SystemAVisualizationAdapter`. The base grid rendering, controls, and state machine remain framework-owned.

- **(B) Generic text-based analysis panel**: The step analysis panel renders a system-provided text block (formatted markdown or monospace text). The system is responsible for formatting its own trace data as human-readable text. Pros: simple framework side. Cons: loses structured rendering (tables, alignment).

- **(C) System provides custom widgets**: Systems contribute their own PySide6 widgets for the detail area. The framework provides a container and base controls. Pros: full rendering control. Cons: systems must depend on PySide6, tight UI coupling.

**Answer**:

(A)

---

## Q11. System Registration and Discovery

**Context**: The framework needs to know which systems are available and how to instantiate them. Currently there's only System A, hardcoded. For multi-system support, the framework needs a registration or discovery mechanism.

**Question**: How should systems be registered and instantiated?

**Why it matters**: This determines how the CLI, experiment config, and resume logic find and load the correct system.

**Suggestions**:

- **(A) Explicit registry in code (Recommended for this milestone)**: A simple dictionary mapping system type strings to factory functions:
  ```python
  SYSTEM_REGISTRY: dict[str, Callable[[dict], SystemInterface]] = {
      "system_a": SystemA.from_config,
      "system_a_plus_w": SystemAPlusW.from_config,
  }
  ```
  Registered at import time. The framework looks up the system type from the experiment config. Pros: simple, explicit, debuggable. Cons: requires code change to add a new system (acceptable for this milestone; the vision explicitly says "no plugin system" as a non-goal).

- **(B) Entry point-based discovery**: Systems register via Python entry points in `pyproject.toml`. The framework discovers them at runtime via `importlib.metadata`. Pros: no code change to add systems. Cons: more complex, implicit, magic-ish.

- **(C) Config specifies module path**: The experiment config includes a `system_module: "axis.systems.system_a"` field. The framework dynamically imports it. Pros: flexible. Cons: fragile, import errors at runtime.

**Answer**:

(A) - registry in code is fully ok for me.

---

## Q12. WorldConfig Ownership

**Context**: `WorldConfig` currently contains: `grid_width`, `grid_height`, `resource_regen_rate`, `obstacle_density`, `regeneration_mode`, `regen_eligible_ratio`. Some of these are clearly framework-level (grid dimensions, obstacle density). Others are tied to System A's transition mechanics (regen rate, regen mode, regen ratio).

**Question**: How should world configuration be split between framework and system?

**Why it matters**: This affects what's consistent across systems (same world for comparable experiments) and what's system-specific.

**Suggestions**:

- **(A) Core framework world config + system-extensible world config (Recommended)**: Framework owns:
  - `grid_width`, `grid_height`, `obstacle_density`

  System-specific (passed via system config):
  - `resource_regen_rate`, `regeneration_mode`, `regen_eligible_ratio`

  The framework creates the base grid. Systems (or their transition functions) request regen behavior via their own config. Pros: core world is consistent, system behavior varies. Cons: boundary between "world structure" and "world dynamics" needs care.

- **(B) All world config is framework**: The framework owns all `WorldConfig` fields. Systems cannot influence world generation or dynamics. Pros: maximum cross-system consistency. Cons: limits system expressiveness (e.g., a system might want a different regen model).

- **(C) World config is entirely system-owned**: Each system specifies its own world config. The framework creates worlds per system specification. Pros: maximum flexibility. Cons: lose the ability to compare systems in identical environments.

**Answer**:

(A)

> **Updated:** The implementation evolved beyond option (A). `BaseWorldConfig`
> is now a minimal SDK type with only `world_type: str` defined; all other
> fields (including grid dimensions, obstacles, and regeneration parameters)
> pass through as Pydantic extras via `extra="allow"`. The world factory
> (`Grid2DWorldConfig`) validates world-type-specific fields internally.
>
> Additionally, the world now owns its dynamics through `MutableWorldProtocol`
> methods: `tick()` (per-step dynamics like regeneration), `extract_resource()`
> (resource extraction without systems importing concrete world types), and
> `snapshot()` (self-serialization). Custom world types can be registered via
> `register_world()` / `create_world_from_config()`, making the world layer
> as pluggable as the system layer.

---

## Q13. Backward Compatibility of Persisted Artifacts

**Context**: Existing experiments were persisted with System A-specific types (`SimulationConfig`, `StepResult`, `EpisodeResult`, etc.). After modularization, artifact schemas will change (new fields like `system_type`, restructured configs). Existing experiments in `experiments/results/` would break under new deserialization.

**Question**: What backward compatibility strategy should we follow?

**Why it matters**: Determines whether existing experiment data remains usable after the evolution.

**Suggestions**:

- **(A) Version-tolerant loading (Recommended)**: New artifacts include a `schema_version` or `system_type` field. The repository detects legacy artifacts (no `system_type` field) and loads them assuming `system_type = "system_a"` with v0.1.0 schema. New artifacts use the new schema. Pros: existing data remains usable, smooth migration. Cons: legacy loading code must be maintained.

- **(B) Clean break**: Declare that pre-modularization artifacts are a different format. Existing data is not loadable by the new framework without explicit migration. Users re-run experiments if needed. Pros: no legacy code. Cons: loses existing data.

- **(C) Migration tool**: Provide a one-time migration script that rewrites existing artifacts into the new schema. Pros: clean forward state. Cons: must handle all edge cases, one-time effort.

**Answer**:

(B) is totally fine for me. No need to keep a backward compatibility.

---

## Q14. Observation Type Generality

**Context**: The current `Observation` type is System A-specific: 5 `CellObservation` fields (current + 4 Von Neumann neighbors), each with `traversability` and `resource`. Future systems might use different sensor models (larger neighborhood, additional features, different representation).

**Question**: Should the framework define a generic observation type, or should each system define its own?

**Why it matters**: If observations are system-specific, the framework cannot inspect or log them generically. If framework-defined, all systems are constrained to the same observation structure.

**Suggestions**:

- **(A) System-defined observations (Recommended)**: Each system defines its own observation type. The framework treats observations as opaque values passed between the sensor and the system's decision pipeline. The base replay contract stores observations as serialized system data, not as framework-level types. Pros: full flexibility, no observation coupling. Cons: framework cannot reason about observation content.

- **(B) Framework defines a base observation type**: The framework defines a minimal observation structure (e.g., local neighborhood grid patch). Systems extend it. Pros: some framework-level observation reasoning possible. Cons: constrains future sensor models.

- **(C) Observations are always `dict[str, Any]`**: Maximum flexibility, minimum structure. Pros: anything goes. Cons: no type safety, hard to test, hard to visualize.

**Answer**:

(A)

---

## Q15. Energy as Framework or System Concept

**Context**: Energy is currently central to System A: it drives the hunger drive, determines termination, and is tracked per-step. Future systems might not use energy at all, or might use different survival metrics.

**Question**: Is "energy" (or more generally, an agent survival metric) a framework concept or a system concept?

**Why it matters**: The base replay contract, visualization status bar, and termination logic all currently assume energy exists.

**Suggestions**:

- **(A) Base metric exposed by all systems (Recommended)**: The `SystemInterface` requires systems to expose a normalized "vitality" or "health" metric `[0, 1]` that the framework uses for display and basic termination detection. Systems map their internal state (energy, health, etc.) to this metric. Pros: framework can display and reason about system health generically. Cons: forces systems to define a health metric even if the concept doesn't naturally apply.

- **(B) Energy is system-specific**: Energy is a System A concept. The framework does not know about energy. The replay base contract does not include energy -- it's in `system_data`. Termination is signaled by the system returning a terminated flag, not by the framework checking energy. The visualization adapter provides an energy display for System A. Pros: clean separation. Cons: framework cannot show energy in the status bar without an adapter.

- **(C) Optional framework metric**: Systems may optionally expose a vitality metric. The framework displays it if available, omits it if not. Pros: flexible. Cons: optional contracts tend to create inconsistent experiences.

**Answer**:

(A)

---

## Q16. Termination Ownership

**Context**: Currently, termination is determined in Phase 6 of `transition.py`: `terminated = new_energy <= 0.0`. The framework also terminates on `max_steps`. These are two different kinds of termination: system-driven (energy depleted) vs framework-driven (step limit).

**Question**: Who decides when an episode terminates?

**Suggestions**:

- **(A) Both framework and system can terminate (Recommended)**: The framework enforces `max_steps` as a hard stop. The system can signal termination via its step return value (e.g., `terminated=True`). The `TerminationReason` distinguishes framework-driven (`MAX_STEPS_REACHED`) from system-driven reasons (which are system-specific strings like `"energy_depleted"`). Pros: clean, both concerns are addressed. Cons: need to define termination reason as extensible.

- **(B) Only framework terminates**: Systems never signal termination. The framework terminates on `max_steps` or on external conditions. Pros: simplest. Cons: agent death by energy depletion cannot be modeled.

- **(C) Only system terminates**: Systems decide all termination, including step limits. Pros: system has full control. Cons: framework cannot enforce experiment bounds.

**Answer**:

(A)

---

## Q17. Snapshot Point Names for Multi-System

**Context**: The current `ReplayPhase` enum has three values: `BEFORE`, `AFTER_REGEN`, `AFTER_ACTION`. The `PlaybackController` uses these for navigation. If the phase model becomes dynamic (per Q9), the navigation and visualization must adapt.

**Question**: If you chose dynamic/extensible phases in Q9, should phase navigation in the visualization be string-based (arbitrary phase names) or should there be a fixed minimal set with optional extensions?

**Suggestions**:

- **(A) Fixed minimal set + optional extras (Recommended if Q9=A)**: The framework guarantees `BEFORE` and `AFTER_ACTION` phases exist. Systems may register additional intermediate phases. Navigation always works with at least two phases. System-provided phases appear in the phase selector when available. Pros: predictable base behavior, extensible. Cons: navigation logic must handle variable phase counts.

- **(B) Fully string-based**: Phases are arbitrary strings. The framework sorts and navigates them in declared order. Pros: maximum flexibility. Cons: no guaranteed structure, easy to break navigation.

**Answer**:

(A)

---

## Q18. Test Strategy During Refactoring

**Context**: The repository has 1215+ tests. The modular evolution will move and restructure code. Tests must continue to pass throughout or be explicitly migrated.

**Question**: What is the test strategy during the refactoring?

**Suggestions**:

- **(A) Strict green-bar throughout (Recommended)**: Every commit must pass all existing tests. Tests that reference moved code are updated in the same commit. New interfaces and framework components get new tests. Pros: confidence at every step. Cons: slower, requires disciplined refactoring.

- **(B) Phase-level green bar**: Tests may break within a phase but must be green at the end of each phase. Pros: allows more aggressive restructuring within phases. Cons: broken tests during a phase can mask regressions.

- **(C) Separate test suites**: Legacy tests run against the compatibility layer. New tests run against the new structure. Pros: clean separation. Cons: maintaining two test suites is expensive.

**Answer**:

(C) Tests can be rewritten based on the new system. No need to stick to old and outdated tests.

---

## Summary Checklist

After answering all questions, verify:

- [x] Q1-Q3 form a consistent picture of the step lifecycle (who does what, in what order)
- [x] Q4 and Q6-Q7 are consistent (action space, config structure, OFAT paths align)
- [x] Q8-Q9 and Q10 form a consistent replay and visualization story
- [x] Q5 and Q11 are compatible (package structure supports registration approach)
- [x] Q12-Q16 define clear framework vs system boundaries

Once complete, save this file. A future Claude Code session will read your answers and proceed with implementation planning.
