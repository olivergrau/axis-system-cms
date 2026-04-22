# AXIS Execution And Artifact Flow

## From Config To Result

AXIS execution flows through four nested levels:

1. experiment config
2. run config
3. episode execution
4. persisted artifacts and optional replay/comparison

`ExperimentConfig` is defined in `src/axis/framework/config.py`.

It separates:

- framework-owned configuration:
  `general`, `execution`, `world`, `logging`
- system-owned opaque configuration:
  `system`

This separation matters because the framework should not need system-specific
knowledge to run experiments.

## Experiment Execution

`ExperimentExecutor` in `src/axis/framework/experiment.py`:

- resolves single-run or OFAT experiments into concrete `RunConfig` objects
- executes each run
- computes experiment summaries
- optionally persists artifacts through `ExperimentRepository`
- supports resuming persisted experiments

OFAT behavior:

- parameter paths use a `framework.*` or `system.*` prefix
- each run receives a seed offset from the baseline seed

## Episode Loop

`run_episode()` in `src/axis/framework/runner.py` is the most important
runtime function.

Per step, the loop does roughly this:

1. capture `world_before`
2. ask system to `decide()`
3. let the world advance its own dynamics via `tick()`
4. capture intermediate snapshot after regeneration/dynamics
5. apply action through the action registry
6. capture `world_after`
7. ask system to `observe()` the post-action world
8. ask system to `transition()`
9. build `BaseStepTrace`

Important detail:

- step traces include multiple snapshots, not just before/after
- this is why replay and phase-based visualization are richer than a simple
  action log

## Artifact Layout

Persistence is owned by `ExperimentRepository` in
`src/axis/framework/persistence.py`.

Canonical structure:

```text
<results-root>/
  <experiment-id>/
    experiment_config.json
    experiment_metadata.json
    experiment_status.json
    experiment_summary.json
    runs/
      <run-id>/
        run_config.json
        run_metadata.json
        run_status.json
        run_summary.json
        run_result.json
        episodes/
          episode_0001.json
          episode_0002.json
          ...
```

This means replay and comparison are driven from persisted artifacts, not from
live runtime state.

## Workspaces

Workspaces wrap execution in a higher-level container.

Workspace logic lives in `src/axis/framework/workspaces/`.

Core idea:

- a workspace owns its own `results/` directory
- configs, results, comparisons, and notes live together
- the workspace manifest records intent and execution history

Workspace execution is routed through `execute_workspace()` in
`src/axis/framework/workspaces/execute.py`, which simply points an
`ExperimentRepository` at `<workspace>/results/`.

This is an important design choice:

- the normal experiment engine is reused
- workspaces are a coordination and artifact-management layer, not a second
  execution engine

## Comparison

The comparison layer is a post-hoc analysis pipeline.

Entry points:

- CLI: `axis compare`
- Python: `compare_episode_traces()` and `compare_runs()`

Core implementation:

- `src/axis/framework/comparison/compare.py`

Comparison validates that two traces are meaningfully comparable, then derives:

- alignment
- action divergence
- position divergence
- vitality divergence
- outcome differences
- optional system-specific analysis extensions

Important mental model:

- comparison is asymmetric: reference vs candidate
- comparison uses persisted traces
- comparison never mutates the original artifacts

## Visualization

Visualization also operates on persisted traces.

Flow:

1. load episode trace from repository
2. resolve system/world visualization adapters
3. build a session controller
4. map replay snapshots into generic UI view models
5. render in the Qt UI

Main files:

- `src/axis/visualization/launch.py`
- `src/axis/visualization/registry.py`
- `src/axis/visualization/view_model_builder.py`

Important design feature:

- visualization does not need to know system internals directly
- adapters interpret replay payloads into overlays, labels, and analysis blocks

## Plugin And Catalog Evolution

Some older docs describe a more static registry-only architecture.
Current code has evolved toward plugin discovery and injectable catalogs:

- `src/axis/plugins.py`
- `src/axis/framework/catalogs.py`

Practical interpretation:

- classic registries are still present
- catalogs form a more composition-friendly abstraction
- plugin-based loading now coexists with the older global registry model
