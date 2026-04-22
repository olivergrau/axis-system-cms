# AXIS Codebase Map

## Top-Level Structure

- `README.md`: top-level project explanation and CLI overview
- `docs/`: public manuals, tutorials, cheat sheets, concepts
- `docs-internal/`: architecture history, engineering specs, internal design
- `src/axis/`: implementation
- `tests/`: test suite
- `workspaces/`: example and active workspace directories
- `experiments/`: ready-to-run example configs and some result artifacts

## Source Layout

### `src/axis/sdk`

Purpose: stable contracts and shared domain types.

Key files:

- `interfaces.py`: `SystemInterface` and related sub-protocols
- `types.py`: result containers such as `DecideResult` and `TransitionResult`
- `trace.py`: base episode and step trace models
- `world_types.py`: world-side config and protocol types
- `snapshot.py`, `position.py`, `actions.py`: shared value objects

When to read:

- any time you need to understand framework/system boundaries
- any time you are adding a new system or world type

### `src/axis/framework`

Purpose: orchestration, execution, persistence, CLI, comparison, workspaces.

Key files:

- `config.py`: top-level experiment config model, OFAT path handling
- `runner.py`: episode loop
- `run.py`: run-level execution and summaries
- `experiment.py`: experiment-level orchestration and resume behavior
- `persistence.py`: artifact layout and JSON IO
- `registry.py`: system registry and system factory lookup
- `catalogs.py`: injectable catalog abstraction layered over registries

Subpackages:

- `cli/`: parser and dispatch
- `comparison/`: paired trace comparison pipeline
- `workspaces/`: scaffold, run, compare, sync, validation, resolution

When to read:

- running/debugging experiments
- understanding artifact flow
- workspace behavior
- comparison behavior

### `src/axis/systems`

Purpose: concrete agent implementations plus the reusable construction kit.

Important subdirectories:

- `construction_kit/`: reusable building blocks for system-internal logic
- `system_a/`: hunger baseline
- `system_aw/`: hunger + curiosity + world model
- `system_b/`: SDK/demo custom system
- `system_c/`: predictive modulation system

Fast orientation:

- start with `system.py`
- then read `config.py`, `types.py`, `transition.py`
- then dip into `construction_kit/` as needed

### `src/axis/world`

Purpose: pluggable environment implementations and action application.

Key files:

- `registry.py`: world factory registry and resolver
- `actions.py`: action registry and base movement handlers

World implementations:

- `grid_2d/`: default rectangular grid world
- `toroidal/`: wraparound world
- `signal_landscape/`: dynamic signal/hotspot world

### `src/axis/visualization`

Purpose: replay loading, adapter resolution, view model construction, Qt UI.

Key files:

- `launch.py`: visualization entry point
- `registry.py`: world/system visualization adapter registry
- `view_model_builder.py`: generic assembly of frame view models
- `snapshot_resolver.py`: chooses which replay snapshot corresponds to a
  step/phase selection
- `ui/`: widgets and main window

Important design feature:

- the base viewer is generic
- system/world specificity enters through adapters

## Where To Look For Common Tasks

### "How does one episode execute?"

- `src/axis/framework/runner.py`

### "How is a system instantiated from config?"

- `src/axis/framework/registry.py`
- corresponding system `config.py` and `system.py`

### "How are experiments persisted on disk?"

- `src/axis/framework/persistence.py`

### "How do workspaces resolve what to run or compare?"

- `src/axis/framework/workspaces/execute.py`
- `src/axis/framework/workspaces/resolution.py`
- `src/axis/framework/workspaces/compare.py`
- `src/axis/framework/workspaces/handlers/`

### "How does replay visualization stay generic?"

- `src/axis/visualization/launch.py`
- `src/axis/visualization/registry.py`
- `src/axis/visualization/view_model_builder.py`

### "How does comparison work?"

- `src/axis/framework/comparison/compare.py`
- neighboring modules in `src/axis/framework/comparison/`

## Most Important Public Docs

- `README.md`
- `docs/manuals/axis-overview.md`
- `docs/manuals/cli-manual.md`
- `docs/manuals/workspace-manual.md`
- `docs/manuals/comparison-manual.md`
- `docs/manuals/system-aw-manual.md`
- `docs/manuals/system-dev-manual.md`

## Most Important Internal Docs

- `docs-internal/architecture/index.md`
- `docs-internal/architecture/evolution/architectural-vision-v0.2.0.md`
- `docs-internal/ideas/architecture-refactoring/implementation-status.md`

Use internal docs for design history and intent, but use source code for
current behavior when they diverge.
