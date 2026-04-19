# Experiment Output Abstraction Engineering Spec

## 1. Purpose

This engineering specification derives the implementation shape of the
framework-level **Experiment Output** abstraction from:

- [Experiment Output Abstraction Spec](./experiment-output-abstraction-spec.md)

The goal is to introduce a normalized output layer above persistence and below
Workspace workflows, while preserving the existing repository layout.


## 2. Implementation Goal

The framework shall gain a new internal semantic layer that interprets a
completed experiment as one of two normalized output forms:

- `PointExperimentOutput`
- `SweepExperimentOutput`

This layer shall then become the entry point for:

- CLI experiment inspection
- Workspace result tracking
- Workspace comparison entry resolution
- Workspace visualization entry resolution


## 3. Architectural Placement

### 3.1 New framework module

The abstraction should be introduced in:

- `src/axis/framework/experiment_output.py`

This module should remain internal to the framework in the first wave.

### 3.2 Responsibilities of `experiment_output.py`

The module should contain:

- output-form enum(s)
- normalized output models
- loader / builder functions from persisted repository artifacts
- validation of persisted output semantics

The module should **not** contain:

- repository IO primitives
- CLI argument parsing
- Workspace-specific business rules


## 4. Existing Code Areas Affected

Based on the current codebase, the refactoring will affect at least these
areas:

### 4.1 Experiment configuration and execution

- `src/axis/framework/config.py`
- `src/axis/framework/experiment.py`

### 4.2 Persistence

- `src/axis/framework/persistence.py`

### 4.3 CLI inspection

- `src/axis/framework/cli.py`

### 4.4 Workspace layer

- `src/axis/framework/workspaces/types.py`
- `src/axis/framework/workspaces/sync.py`
- `src/axis/framework/workspaces/summary.py`
- `src/axis/framework/workspaces/compare_resolution.py`
- `src/axis/framework/workspaces/visualization.py`
- type-specific handlers under:
  - `src/axis/framework/workspaces/handlers/`

### 4.5 Comparison layer

- `src/axis/framework/workspaces/compare.py`
- possibly comparison entry helpers in:
  - `src/axis/framework/comparison/`


## 5. New Internal Model

### 5.1 Output form enum

Introduce a framework-level enum, likely:

- `ExperimentOutputForm`
  - `POINT`
  - `SWEEP`

### 5.2 Base output model

Introduce an internal base model:

- `ExperimentOutput`

Required fields:

- `experiment_id`
- `experiment_type`
- `output_form`
- `system_type`
- `created_at`
- `num_runs`
- `experiment_root_path`
- `summary_path`
- optional `status`
- optional `name`
- optional `description`

### 5.3 Point model

Introduce:

- `PointExperimentOutput`

Additional required fields:

- `primary_run_id`
- `primary_run_path`

Optional convenience fields:

- `primary_run_summary_path`
- `primary_run_result_path`

### 5.4 Sweep model

Introduce:

- `SweepExperimentOutput`

Additional required fields:

- `parameter_path`
- `parameter_values`
- `baseline_run_id`
- `run_ids`
- `variation_descriptions`

Optional convenience fields:

- `baseline_run_path`
- `run_paths`


## 6. Persistence Changes

### 6.1 Principle

The filesystem layout should remain unchanged in the first wave.

No directory tree redesign is required.

### 6.2 Required explicit fields

The framework shall persist explicit experiment-output semantics rather than
relying only on runtime derivation.

The first wave should persist:

- `output_form` at experiment level
- `primary_run_id` for point outputs
- `baseline_run_id` for sweep outputs

### 6.3 Likely persistence locations

The most natural place for experiment-level output semantics is:

- `ExperimentMetadata`

This implies extending:

- `src/axis/framework/persistence.py`

Current `ExperimentMetadata` contains:

- `experiment_id`
- `created_at`
- `experiment_type`
- `system_type`
- `name`
- `description`

It should be expanded with at least:

- `output_form`
- `primary_run_id: str | None`
- `baseline_run_id: str | None`

### 6.4 Run-level sweep metadata

Sweep reconstruction must be fully possible from persisted artifacts.

Current `RunMetadata` already contains:

- `variation_description`
- `base_seed`

It should be expanded for sweep runs with at least:

- `variation_index: int | None`
- `variation_value: Any | None`

Persisting `is_baseline: bool | None` is recommended if it makes validation and
reconstruction simpler.

### 6.5 Validation rule

When persisting experiment metadata, the framework must validate:

- `single_run <-> point`
- `ofat <-> sweep`

Invalid combinations must raise explicit errors.


## 7. Experiment Execution Integration

### 7.1 Output-form assignment during execution

`ExperimentExecutor` in:

- `src/axis/framework/experiment.py`

should become responsible for assigning persisted output semantics when an
experiment completes.

This likely requires:

- deriving the expected output form from `ExperimentConfig.experiment_type`
- assigning `primary_run_id` for `single_run`
- assigning `baseline_run_id` for `ofat`
- writing these into persisted metadata

### 7.2 Point output assignment

For `single_run`:

- `output_form = point`
- `primary_run_id = run-0000`

### 7.3 Sweep output assignment

For `ofat`:

- `output_form = sweep`
- `baseline_run_id = run-0000`

If the framework ever changes OFAT baseline rules later, this explicit field
prevents downstream ambiguity.


## 8. Experiment Output Loader

### 8.1 Loader responsibility

The new module `experiment_output.py` should provide a loader such as:

- `load_experiment_output(repo, experiment_id)`

This loader should read:

- `ExperimentConfig`
- `ExperimentMetadata`
- `ExperimentSummary`
- run IDs
- optional `RunMetadata`

and return:

- `PointExperimentOutput` or
- `SweepExperimentOutput`

### 8.2 Loader behavior

The loader must:

- validate output semantics
- reject inconsistent persisted data
- construct normalized output objects
- expose stable paths and operational identifiers

### 8.3 No hidden inference

The loader may use persisted information plus repository discovery, but it must
not silently guess missing semantic fields where the spec requires explicit
persistence.


## 9. CLI Refactoring

### 9.1 `axis experiments show`

This command should be refactored to:

1. load the experiment output
2. render output-form-specific information

For point outputs, show at least:

- `output_form`
- `primary_run_id`
- run summary focus

For sweep outputs, show at least:

- `output_form`
- `parameter_path`
- `parameter_values`
- `baseline_run_id`
- sweep summary focus

### 9.2 `axis experiments list`

This command should surface:

- `output_form`
- `num_runs`

This allows users to distinguish point experiments from sweep experiments
without opening individual directories manually.

### 9.3 `axis runs show`

This command should remain run-centric, but should additionally surface:

- enclosing `output_form`
- variation information for sweep runs when available


## 10. Workspace Refactoring

### 10.1 Manifest model update

Workspace result tracking must no longer treat run directories as primary
results.

This requires refactoring:

- `src/axis/framework/workspaces/types.py`

The current `primary_results` field allows `list[str | dict]`.

It should be tightened toward structured result entries carrying output
semantics.

### 10.2 Structured primary result entry

The first wave should introduce a typed result entry model with at least:

- `path`
- `output_form`
- `system_type`
- `role`
- `created_at`

Recommended additional fields:

- `primary_run_id`
- `baseline_run_id`

### 10.3 Path identity

Workspace result paths should now identify experiment roots:

- `results/<experiment-id>`

not:

- `results/<experiment-id>/runs/<run-id>`

### 10.4 Manifest sync

`src/axis/framework/workspaces/sync.py` must be updated so that:

- `sync_manifest_after_run(...)` records experiment-root result entries
- output semantics are written into `primary_results`
- development-specific fields remain coherent

For `system_development`, development-specific fields may continue to refer to
experiment-root result entries in v1, even if operational comparison later
selects the contained primary run.

### 10.5 Summary rendering

`src/axis/framework/workspaces/summary.py` must become output-aware and render
structured result entries rather than assuming run-path-centric results.


## 11. Comparison Refactoring

### 11.1 Entry resolution

Workspace comparison resolution should first resolve experiment outputs, then
apply operational selection.

Affected area:

- `src/axis/framework/workspaces/compare_resolution.py`

### 11.2 Supported v1 case

Only `point vs point` comparison must be implemented in the first wave.

This should map internally to:

- load two point outputs
- extract their primary runs
- call the existing run comparison machinery

This limitation applies to the output-aware comparison entry layer, especially
Workspace comparison routing.

It does not require disabling or rewriting the existing direct raw run-vs-run
`axis compare` command, which already accepts explicit experiment/run
coordinates and remains valid for legitimate OFAT run-to-run comparisons.

### 11.3 Explicit failures

All unsupported combinations must fail explicitly:

- `point vs sweep`
- `sweep vs point`
- `sweep vs sweep`

The error text should state clearly that sweep-based workspace comparison is not
yet supported.


## 12. Visualization Refactoring

### 12.1 Entry resolution

Workspace visualization entry logic should first resolve an experiment output.

Affected area:

- `src/axis/framework/workspaces/visualization.py`

### 12.2 Point output behavior

For point outputs:

- use `primary_run_id` as the natural default

### 12.3 Sweep output behavior

For sweep outputs:

- no default run selection in v1
- require explicit run or variation selection
- otherwise raise a clear error


## 13. Development Workspace Compatibility

### 13.1 Current policy

The currently implemented workspace guardrails already reject non-`single_run`
configs in workspace mode.

That behavior should remain intact during this refactoring.

### 13.2 Development workspaces

`development / system_development` should continue to operate only on point
outputs in the first wave.

The new Experiment Output layer should improve its internal semantics but must
not expand its operational scope yet.


## 14. Testing Strategy

### 14.1 New tests required

The refactoring should add coverage for:

- loading a point output from persisted artifacts
- loading a sweep output from persisted artifacts
- rejecting inconsistent persisted output semantics
- `axis experiments show` rendering point outputs
- `axis experiments show` rendering sweep outputs
- `axis runs show` surfacing enclosing output form
- workspace manifest sync writing experiment-root result entries
- workspace comparison succeeding for `point vs point`
- workspace comparison failing clearly for any sweep-involved case
- workspace visualization failing clearly for sweep outputs without explicit
  selection

### 14.2 Existing tests to update

Expect current Workspace tests to need updates where they assume:

- `primary_results` entries are run paths
- comparison resolution starts from run-path assumptions


## 15. Migration Strategy

### 15.1 Order of implementation

Recommended sequence:

1. Extend persistence metadata
2. Introduce `experiment_output.py`
3. Refactor CLI inspection
4. Refactor Workspace manifest result semantics
5. Refactor compare entry resolution
6. Refactor visualization entry resolution
7. Update tests and manuals

### 15.2 Backward compatibility

Backward compatibility is not a requirement for this refactoring wave.

The current Workspace feature and persisted workspace manifests are still young
enough that direct contract updates are preferable to carrying compatibility
layers.

Likewise, experiment metadata contracts may be renewed directly where needed.


## 16. Out of Scope

This engineering wave does not include:

- sweep-aware workspace comparison behavior
- sweep-aware workspace workflows
- public SDK exposure of Experiment Outputs
- repository tree redesign


## 17. Recommendation

Proceed with a framework-wide refactoring centered on a new
`experiment_output.py` module and explicit persisted output semantics.

The refactoring should:

- keep the repository structure stable
- make experiment outputs explicit and typed
- remove run-path-centric assumptions from Workspace result identity
- make CLI, compare, and visualization output-aware
- prepare the framework for future OFAT-in-workspace support without enabling
  it prematurely

This is the cleanest path toward later `sweep` support in
`investigation / single_system` while preserving the simplicity of the current
point-based workspace workflows.
