# 13. Architectural Strengths, Current Limitations, and Spec Deviations

## Architectural Strengths

### Separation of Concerns

Each module has a single, well-defined responsibility. The drive module knows nothing about the transition engine. The policy module knows nothing about the world model. Information flows through well-typed interfaces (`Observation`, `HungerDriveOutput`, `DecisionTrace`).

### Determinism

The entire simulation is deterministic given a seed. The RNG is created from a seed at the episode level and threaded through the step pipeline. World generation (obstacles, eligibility) uses `np.random.default_rng(seed)` for reproducibility. This enables exact replay, debugging, and behavioral regression testing.

### Full Traceability

Every step captures exhaustive trace data: drive output, full decision pipeline (raw contributions, mask, masked, probabilities), and three world snapshots (before, after-regen, after-action). No information is lost between input and output.

### Immutable Models

All value types, configs, results, and view models are frozen Pydantic `BaseModel` instances. State transitions produce new instances via `model_copy(update={...})`. Only `World` is mutable (required for efficient grid updates during transition). This prevents accidental mutation bugs and makes the data flow auditable.

### Layered Execution

Clear separation between runtime (episode execution), orchestration (run/experiment execution), and persistence (repository). Each layer can be tested independently. The runner doesn't know about persistence, the executor doesn't know about drive computation.

### Persistence Discipline

The repository layer uses a consistent save/load pattern with JSON serialization. Immutable artifacts are protected by `overwrite=False` by default. Status files have a clear lifecycle. Resume works by checking artifact completeness, not by reconstructing state.

### Visualization Unidirectional Flow

The visualization follows a strict Model-View pattern: widgets never mutate state, they emit intent signals. The controller applies pure transitions. The rebuilt frame flows down to all widgets. This makes the UI predictable and testable.

### Test Coverage Depth

1200+ tests across five categories provide confidence in correctness. Behavioral tests validate system-level properties. Integration tests exercise lifecycle transitions. Visualization tests cover the entire rendering pipeline with offscreen rendering.

## Current Limitations

### Sequential Execution Only

All episodes within a run and all runs within an experiment execute sequentially. There is no parallel execution via multiprocessing or threading. For large experiments (many episodes, many runs), this is the primary performance bottleneck.

### Single Drive

Only the hunger drive is implemented. The architecture supports multiple drives (the `action_contributions` tuple could be the sum of multiple drives), but no infrastructure for drive composition exists.

### No Learning or Adaptation

The agent's policy is fixed: hunger drive + softmax selection with static parameters. There is no learning, reward signal, or parameter optimization. The agent does not improve across episodes.

### No World Model

The agent has no internal representation of the world. Memory stores raw observations but is not used by the current drive or policy (the hunger drive only uses the current observation). Memory is populated but functionally unused in the baseline.

### File-Based Persistence Only

The repository uses the local filesystem. No database, no remote storage, no concurrent access protection. Experiment names with special characters could cause filesystem issues.

### Baseline Experiment Types Only

Only `single_run` and `ofat` experiment types are supported. No factorial designs, no multi-factor sweeps, no adaptive experiments.

### PySide6 Desktop Only

Visualization requires a PySide6 display environment (X11/Wayland). No web-based or headless rendering alternative exists.

### No Streaming / Live Visualization

Visualization operates on completed episodes loaded from disk. There is no streaming mode to visualize an episode as it executes.

### Overlay Z-Order Limitation

In the grid widget's `paintEvent`, overlays are drawn after the agent circle. Action preference arrows originate from the cell center and have limited length relative to the agent circle, making them partially obscured.

## Deviations Between Spec and Implementation

### Memory Usage

The formal specification defines memory as an input to the drive computation. In the implementation, `MemoryState` is maintained and updated correctly, but `compute_hunger_drive()` does not accept or use memory. The drive computation uses only the current observation.

### Spec Phase Naming

The visualization spec references phases as "before action", "after regeneration", "after action". The implementation uses the enum values `BEFORE`, `AFTER_REGEN`, `AFTER_ACTION`. The ordering matches the spec: regeneration runs first (Phase 1 of transition), then the action (Phase 2).

### Softmax Temperature Convention

The spec defines temperature as a softmax temperature. The implementation uses `temperature` as the inverse temperature (β) in `exp(β * x)`. Higher temperature means sharper (more deterministic) distributions, not softer. This is a naming convention difference -- the computation is correct.

### Out-of-Scope Spec Sections

The following spec sections are defined but not implemented:
- Multi-drive composition framework (spec Section 7)
- World model / planning (spec discusses as future direction)
- Non-local sensor models

---

## Suggested Follow-Up Documentation

The following documents would build on this architecture documentation:

1. **Architecture Optimization Analysis** -- Identify bottlenecks, propose parallel execution, profile persistence overhead
2. **Module Dependency Map** -- Visual dependency graph with import analysis
3. **Extension Guide** -- How to add new drives, experiment types, or visualization overlays
4. **Contributor Onboarding Guide** -- Development environment setup, coding conventions, PR workflow
5. **Visualization User Guide** -- How to use the viewer effectively (keyboard shortcuts, overlay interpretation)
6. **Configuration Reference** -- Complete parameter reference with descriptions, ranges, and effects
7. **Data Model Schema Reference** -- JSON schema for all persisted artifacts
