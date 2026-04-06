# 2. System Overview

## High-Level Structure

The system decomposes into three major subsystems with clear dependency direction:

### Core Runtime

The simulation engine executes the agent-environment loop. A single step follows the chain: **observe -> drive -> decide -> act -> update**. The runtime is fully deterministic given a seed, and every step produces a complete `StepResult` trace capturing all intermediate data.

Key characteristics:
- All domain models are frozen Pydantic `BaseModel` instances (immutable after creation)
- The `World` object is the sole mutable container in the runtime
- State transitions produce new immutable `AgentState` instances; the world is mutated in place
- Three world snapshots are captured per step (before, after-regen, after-action) for full auditability

### Experimentation Framework

Orchestrates multi-episode runs and multi-run experiments. Supports two experiment types:
- `single_run` -- one configuration, multiple episodes
- `ofat` -- one parameter varied across multiple values, each producing a separate run

All artifacts are persisted to a file-based repository. Experiments support resume after partial failure.

### Visualization

An interactive PySide6 application for replaying episodes step-by-step with phase granularity. Architecture follows a strict unidirectional data flow:

```
ViewerState (immutable) --> ViewModelBuilder --> ViewerFrameViewModel --> Widgets
     ^                                                                      |
     |                    (pure transitions)                                |
     +--------------------------------- signals ----------------------------+
```

## Current Maturity

- **Core Runtime**: Fully implemented and stable. ~700 unit tests. Determinism validated through behavioral and integration tests.
- **Experimentation Framework**: Fully implemented including OFAT, resume, and summary computation. ~160 integration/e2e tests.
- **Visualization**: Fully implemented with grid rendering, three overlay types, phase-granular replay, and a comprehensive decision analysis panel. ~630 visualization tests.
- **CLI**: Complete with `experiments` (list/run/resume/show), `runs` (list/show), and `visualize` commands.
- **Total test count**: 1215+ tests across all layers.
