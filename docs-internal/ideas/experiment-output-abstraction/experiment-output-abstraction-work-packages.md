# Experiment Output Abstraction Work Packages

## Purpose

This document provides a first coarse implementation roadmap for introducing
the framework-level **Experiment Output** abstraction described in:

- [Experiment Output Abstraction Spec](./experiment-output-abstraction-spec.md)
- [Experiment Output Abstraction Engineering Spec](./experiment-output-abstraction-engineering-spec.md)

The packages below are intentionally still broad. Their purpose is to define a
clear delivery sequence before detailed implementation packages are written.


## Delivery Strategy

The refactoring should proceed in five layers:

1. **Persisted semantics**
   Add explicit output semantics to persisted experiment and run metadata.
2. **Core output abstraction**
   Introduce `experiment_output.py` and normalize completed experiments into
   point or sweep outputs.
3. **Consumer migration**
   Move CLI inspection and Workspace result identity onto Experiment Outputs.
4. **Operational routing**
   Refactor compare and visualize entry logic to resolve through
   Experiment Outputs.
5. **Hardening**
   Tighten validation, tests, and docs.


## Work Packages

### WP-01: Persisted Output Semantics

Add explicit experiment-output semantics to persistence.

Scope:

- extend `ExperimentMetadata`
- extend `RunMetadata` for sweep runs
- validate `experiment_type <-> output_form`
- persist `primary_run_id`
- persist `baseline_run_id`
- persist sweep variation metadata

Primary files:

- `src/axis/framework/persistence.py`
- `src/axis/framework/experiment.py`


### WP-02: Core Experiment Output Module

Introduce the new normalized output abstraction.

Scope:

- add `src/axis/framework/experiment_output.py`
- define:
  - output form enum
  - base output model
  - point output model
  - sweep output model
- implement loader/builder from repository artifacts
- validate persisted semantics on load

Primary files:

- `src/axis/framework/experiment_output.py`


### WP-03: CLI Inspection Migration

Refactor experiment inspection commands to use Experiment Outputs.

Scope:

- `axis experiments list`
- `axis experiments show`
- `axis runs show` surfaces enclosing output form and variation metadata

Primary files:

- `src/axis/framework/cli.py`


### WP-04: Workspace Result Identity Refactor

Refactor Workspace result tracking from run-path-centric to
experiment-output-centric.

Scope:

- structured `primary_results` entries
- experiment-root paths instead of run paths
- output-aware result-entry model in workspace manifests
- summary rendering updated accordingly

Primary files:

- `src/axis/framework/workspaces/types.py`
- `src/axis/framework/workspaces/sync.py`
- `src/axis/framework/workspaces/summary.py`


### WP-05: Workspace Execution Synchronization Update

Update workspace run synchronization so produced results are recorded as
experiment outputs.

Scope:

- sync after run writes experiment-root result entries
- output form and key output fields included in manifest updates
- development-specific fields stay coherent with experiment-output identity

Primary files:

- `src/axis/framework/workspaces/execute.py`
- `src/axis/framework/workspaces/sync.py`


### WP-06: Output-Aware Comparison Resolution

Refactor workspace comparison entry resolution to work from Experiment Outputs.

Scope:

- resolve experiment outputs first
- support only `point vs point`
- explicitly reject:
  - `point vs sweep`
  - `sweep vs point`
  - `sweep vs sweep`

Primary files:

- `src/axis/framework/workspaces/compare_resolution.py`
- `src/axis/framework/workspaces/compare.py`


### WP-07: Output-Aware Visualization Resolution

Refactor visualization routing to resolve through Experiment Outputs.

Scope:

- point outputs use `primary_run_id`
- sweep outputs require explicit selection
- clear failure on ambiguous sweep visualization

Primary files:

- `src/axis/framework/workspaces/visualization.py`
- `src/axis/framework/cli.py`


### WP-08: Workspace Handler Alignment

Align the existing workspace handlers with experiment-output-centric result
tracking.

Scope:

- `single_system`
- `system_comparison`
- `system_development`
- remove latent run-path assumptions
- keep current guardrails for non-`single_run` workspace configs

Primary files:

- `src/axis/framework/workspaces/handlers/single_system.py`
- `src/axis/framework/workspaces/handlers/system_comparison.py`
- `src/axis/framework/workspaces/handlers/system_development.py`


### WP-09: Validation and Drift Detection

Tighten validation around output semantics and workspace consistency.

Scope:

- workspace manifest validation for structured `primary_results`
- drift detection for experiment-root result entries
- explicit errors for inconsistent persisted output semantics

Primary files:

- `src/axis/framework/workspaces/validation.py`
- `src/axis/framework/workspaces/drift.py`
- `src/axis/framework/experiment_output.py`


### WP-10: Test Migration and New Coverage

Add and update tests across the framework.

Scope:

- point output load tests
- sweep output load tests
- metadata consistency tests
- CLI inspection tests
- workspace result sync tests
- compare failure tests for sweep cases
- visualization failure tests for sweep cases

Primary areas:

- `tests/framework/`
- `tests/framework/workspaces/`


### WP-11: Manual and Internal Documentation Update

Update public and internal documentation to reflect the new output model.

Scope:

- output-aware experiment inspection
- workspace result semantics
- structured `primary_results`
- explicit unsupported sweep cases in Workspace compare/visualize

Primary files:

- `docs/manuals/axis-overview.md`
- `docs/manuals/cli-manual.md`
- `docs/manuals/workspace-manual.md`
- related internal idea/spec docs as needed


## Recommended Sequence

Recommended implementation order:

1. `WP-01 Persisted Output Semantics`
2. `WP-02 Core Experiment Output Module`
3. `WP-03 CLI Inspection Migration`
4. `WP-04 Workspace Result Identity Refactor`
5. `WP-05 Workspace Execution Synchronization Update`
6. `WP-06 Output-Aware Comparison Resolution`
7. `WP-07 Output-Aware Visualization Resolution`
8. `WP-08 Workspace Handler Alignment`
9. `WP-09 Validation and Drift Detection`
10. `WP-10 Test Migration and New Coverage`
11. `WP-11 Manual and Internal Documentation Update`


## Parallelization Opportunities

The following packages can likely be done in parallel after the core is in
place:

- `WP-03 CLI Inspection Migration`
- `WP-04 Workspace Result Identity Refactor`

Then later:

- `WP-06 Output-Aware Comparison Resolution`
- `WP-07 Output-Aware Visualization Resolution`

`WP-10` and `WP-11` should be held until the main structural changes stabilize.


## Milestones

### Milestone 1: Output Semantics Core

Includes:

- `WP-01`
- `WP-02`

Outcome:

- completed experiments can be loaded as point or sweep outputs

### Milestone 2: Consumer Migration

Includes:

- `WP-03`
- `WP-04`
- `WP-05`

Outcome:

- CLI and Workspace result identity use Experiment Outputs

### Milestone 3: Operational Routing and Hardening

Includes:

- `WP-06`
- `WP-07`
- `WP-08`
- `WP-09`
- `WP-10`
- `WP-11`

Outcome:

- compare and visualize are output-aware
- unsupported sweep cases fail explicitly
- docs and tests align with the new model


## Recommendation

Start with the semantic core first and delay consumer migration until
`ExperimentOutput` is fully defined and persisted correctly.

The highest-risk parts are:

- incorrect or incomplete persisted output semantics
- lingering run-path assumptions in Workspace code
- inconsistent CLI behavior between raw experiments and workspaces

Therefore the implementation should first stabilize:

- metadata
- output loading
- validation

before migrating compare and visualization.
