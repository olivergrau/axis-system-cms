# 1. Purpose and Scope

## What This Codebase Implements

AXIS System A is a deterministic agent-environment simulation framework that implements a formally specified model of perception, internal drives, and decision-making. The system models a single agent interacting with a discrete 2D grid world through a closed perception-decision-action loop.

The implementation covers three architectural layers:

1. **Core Runtime** -- The simulation engine: world model, sensor layer, memory, hunger drive, policy/decision pipeline, transition engine, episode runner, and full execution tracing.

2. **Experimentation Framework** -- Multi-run experiment orchestration with OFAT (One-Factor-At-a-Time) parameter sweeps, deterministic seed management, file-based persistence, resume capability, and aggregate statistics.

3. **Visualization** -- An interactive PySide6 episode viewer with grid rendering, phase-granular replay (BEFORE / AFTER_REGEN / AFTER_ACTION), debug overlays, and a step-by-step decision analysis panel.

## Architectural Layers

```
+------------------------------------------------------------------+
|                         CLI (cli.py)                              |
+------------------------------------------------------------------+
|                                                                   |
|  +----------------------------+  +-----------------------------+  |
|  |   Experimentation Layer    |  |    Visualization Layer      |  |
|  |  experiment.py             |  |  visualization/             |  |
|  |  experiment_executor.py    |  |    snapshot_resolver.py     |  |
|  |  run.py                    |  |    viewer_state.py          |  |
|  |  repository.py             |  |    view_model_builder.py    |  |
|  |                            |  |    ui/                      |  |
|  +----------------------------+  +-----------------------------+  |
|                |                              |                   |
|                v                              v                   |
|  +-----------------------------------------------------------+   |
|  |                    Core Runtime                            |   |
|  |  world.py  observation.py  memory.py  drives.py           |   |
|  |  policy.py  transition.py  runner.py  results.py          |   |
|  +-----------------------------------------------------------+   |
|                                                                   |
|  +-----------------------------------------------------------+   |
|  |               Foundation (types.py, enums.py, config.py)  |   |
|  +-----------------------------------------------------------+   |
+------------------------------------------------------------------+
```

## Intentionally Out of Scope

The following are not part of the current implementation:

- Multi-agent scenarios (single agent only)
- Learning, training, or parameter optimization
- Non-local observation models
- Drives beyond hunger (architecture supports multiple, only hunger implemented)
- Stochastic world dynamics (world is deterministic; only policy selection is stochastic)
- Parallel or distributed execution (all runs execute sequentially)
- Remote persistence or database backends (file-based only)
- Web-based visualization (PySide6 desktop only)
