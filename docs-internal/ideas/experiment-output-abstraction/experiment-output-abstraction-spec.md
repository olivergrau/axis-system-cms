# Experiment Output Abstraction Spec

## 1. Purpose

This specification defines a framework-level abstraction for
**Experiment Outputs** in AXIS-CMS.

The abstraction standardizes how completed experiments are interpreted by the
framework and by higher-level consumers such as:

- CLI inspection commands
- Workspace result tracking
- Workspace comparison routing
- Workspace visualization routing

The abstraction sits:

- above persistence,
- above raw experiment execution artifacts,
- below Workspaces.


## 2. Scope

This spec covers:

- the normative Experiment Output model
- supported output forms in v1
- required persisted semantics for point and sweep outputs
- output-aware behavior expected from framework consumers
- Workspace result tracking implications

This spec does **not** redesign:

- the repository filesystem layout
- the low-level step / episode / run artifact model
- the direct execution semantics of `axis experiments run`


## 3. Layering

The relevant AXIS layering is:

- step
- episode
- run
- experiment
- workspace

This spec defines an interpretation layer at the **experiment level**.

The Experiment Output abstraction must therefore be implemented:

- after experiment persistence,
- before Workspace logic,
- and as a framework-level concept rather than a workspace-local convention.


## 4. Normative Terms

### 4.1 Experiment Output

An **Experiment Output** is the normalized framework interpretation of one
completed experiment artifact tree.

An Experiment Output always represents:

- exactly one experiment

It never represents:

- one run
- one episode
- one workspace

### 4.2 Output Form

An **output form** describes the semantic shape of an Experiment Output.

v1 defines exactly two output forms:

- `point`
- `sweep`

### 4.3 Point Output

A **Point Output** is an Experiment Output whose operational meaning is centered
on one primary run.

### 4.4 Sweep Output

A **Sweep Output** is an Experiment Output whose operational meaning is centered
on an ordered run set representing one parameter sweep.

### 4.5 Output Artifact Path

The **output artifact path** is the experiment-root path that identifies the
persisted experiment output artifact.

Example:

- `results/<experiment-id>`

### 4.6 Operational Selection

**Operational selection** is the later selection of a concrete run from an
Experiment Output for an operation such as compare or visualize.

Operational selection is distinct from output artifact identity.


## 5. Supported Output Forms in v1

The framework shall support exactly two output forms in v1:

- `point`
- `sweep`

No additional output forms are valid in v1.


## 6. Relationship Between `experiment_type` and `output_form`

The relationship between experiment type and output form is normative:

- `experiment_type = single_run` requires `output_form = point`
- `experiment_type = ofat` requires `output_form = sweep`

Any other combination is invalid and must be rejected by the framework.

This relationship must be validated explicitly wherever experiment output
artifacts are created or loaded.


## 7. Persistence Requirements

### 7.1 General principle

Persistence may be extended to support explicit output semantics.

The repository layout does not need to change in v1.

### 7.2 Explicit persistence

The following semantics must be explicitly persisted rather than treated as
purely derived runtime inference:

- `output_form`
- `primary_run_id` for point outputs
- `baseline_run_id` for sweep outputs

### 7.3 Sweep robustness

Sweep-specific semantics must be fully recoverable from persisted artifacts
alone.

Therefore, sweep structure must not depend only on inferring order from
configuration fields at runtime.

The framework must ensure that persisted artifacts are sufficient to recover:

- sweep identity
- variation ordering
- variation values
- baseline run identity


## 8. Required Experiment-Level Output Model

Every Experiment Output must expose, at minimum, the following common fields:

- `experiment_id`
- `experiment_type`
- `output_form`
- `system_type`
- `created_at`
- `num_runs`
- `experiment_root_path`
- `summary_path`

Recommended additional common fields:

- `name`
- `description`
- `status`


## 9. Point Output Requirements

### 9.1 Required fields

A Point Output must expose:

- all common Experiment Output fields
- `primary_run_id`
- `primary_run_path`

Optional convenience fields may include:

- `primary_run_summary_path`
- `primary_run_result_path`

### 9.2 Semantics

A Point Output must represent an experiment whose operational meaning is a
single primary run.

### 9.3 Persisted primary run identity

`primary_run_id` must be explicitly persisted.

It must not be treated as an unstable convention such as "the first run found
on disk".


## 10. Sweep Output Requirements

### 10.1 Required fields

A Sweep Output must expose:

- all common Experiment Output fields
- `parameter_path`
- `parameter_values`
- `baseline_run_id`
- `run_ids`
- `variation_descriptions`

Optional convenience fields may include:

- `baseline_run_path`
- `run_paths`

### 10.2 Semantics

A Sweep Output must represent one coherent parameter sweep rather than a
collection of unrelated runs.

### 10.3 Persisted baseline identity

`baseline_run_id` must be explicitly persisted.

It must not rely only on positional inference such as "the first listed run".

### 10.4 Persisted sweep ordering

Sweep ordering must be recoverable from persisted artifacts alone.

To ensure this, run-level metadata for sweep runs must additionally persist:

- `variation_index`
- `variation_value`

Persisting `is_baseline` is recommended and may be adopted if it simplifies
robust recovery and validation.


## 11. Artifact Identity vs Operational Selection

The framework must distinguish strictly between:

- experiment output artifact identity
- operational run selection

### 11.1 Artifact identity

The identity of a completed result artifact is the experiment root:

- `results/<experiment-id>`

### 11.2 Operational selection

Operations such as compare and visualize may subsequently select a specific run
inside that output.

Examples:

- Point Output:
  - select `primary_run_id`
- Sweep Output:
  - select `baseline_run_id`
  - or select one explicit variation run

No framework interface may collapse these two concepts into one path
assumption.


## 12. Framework Module Placement

The Experiment Output abstraction shall initially live in a framework-level
module:

- `src/axis/framework/experiment_output.py`

This module is responsible for:

- defining output forms
- constructing normalized Experiment Outputs from persisted experiment artifacts
- validating persisted output semantics


## 13. CLI Requirements

### 13.1 Output-aware inspection

The framework CLI inspection layer must become Experiment-Output-aware.

At minimum, the following commands must use Experiment Outputs as their
interpretation layer:

- `axis experiments list`
- `axis experiments show`

### 13.2 Run inspection

`axis runs show` may remain run-oriented, but must surface the enclosing
output form.

For sweep runs, it should additionally display variation information when
available.


## 14. Compare Requirements

### 14.1 Entry-level abstraction

High-level comparison entry logic that resolves comparisons from experiment
identity or workspace result identity must operate on Experiment Outputs rather
than directly on raw run-path assumptions.

This requirement applies in particular to:

- Workspace comparison routing
- any future high-level comparison API that accepts experiment-level identities

It does **not** forbid the existing direct run-vs-run comparison CLI from
continuing to operate on explicit `(experiment_id, run_id)` coordinates.

### 14.2 Supported case in v1

The only comparison case that must be actively supported in the first
refactoring wave is:

- `point vs point`

This restriction applies to the new high-level output-aware comparison entry
layer.

This case may internally map to the existing run-vs-run comparison machinery.

### 14.3 Unsupported cases

The following cases are not supported in v1:

- `point vs sweep`
- `sweep vs point`
- `sweep vs sweep`

When such cases are encountered, the framework must fail explicitly with a
clear error.

Silent fallback behavior is forbidden.

This restriction does **not** invalidate explicit direct run-vs-run use of the
existing `axis compare` command when the user already provides concrete run
coordinates.


## 15. Visualization Requirements

### 15.1 Output-aware resolution

Visualization resolution must become Experiment-Output-aware.

It must first resolve an Experiment Output, then resolve the concrete run to
visualize.

### 15.2 Point Output behavior

For Point Outputs, the framework may use `primary_run_id` as the natural
default run selection.

### 15.3 Sweep Output behavior

For Sweep Outputs, visualization must not silently guess a default run in v1.

If no explicit run or variation selection is provided, the framework must fail
with a clear error indicating that sweep visualization requires explicit run
selection.


## 16. Workspace Requirements

### 16.1 Primary result identity

Workspace result tracking must move from run-path-centric identity to
experiment-output-centric identity.

Therefore `primary_results` must refer to experiment-root output artifacts:

- `results/<experiment-id>`

and not to run directories such as:

- `results/<experiment-id>/runs/<run-id>`

### 16.2 Structured result entries

Workspace `primary_results` must be represented as structured output entries,
not plain paths.

At minimum, each entry must carry:

- `path`
- `output_form`
- `system_type`
- `role`
- `created_at`

Recommended additional fields:

- `primary_run_id`
- `baseline_run_id`

### 16.3 Initial operational scope

Workspace operations in the first refactoring wave may remain operationally
focused on Point Outputs.

Sweep Outputs may be modeled at framework level before they become fully
supported by Workspace workflows.


## 17. SDK Exposure

In v1, Experiment Output is a framework-internal model.

It is not required to become an externally exposed SDK contract in the first
wave.


## 18. Error Handling

The framework must prefer explicit validation errors over implicit inference
whenever output semantics are inconsistent or unsupported.

In particular, the framework must fail explicitly when:

- `experiment_type` and `output_form` disagree
- required point-output fields are missing
- required sweep-output fields are missing
- variation ordering cannot be reconstructed from persisted artifacts
- a consumer requests an unsupported compare case
- a consumer requests sweep visualization without explicit run selection


## 19. Conformance Rules

An implementation conforms to this spec only if:

- it represents completed experiments through a normalized Experiment Output
  layer
- it persists `output_form` explicitly
- it persists `primary_run_id` and `baseline_run_id` explicitly
- it persists sufficient sweep metadata to reconstruct sweep ordering and
  baseline identity
- it updates CLI inspection to use Experiment Outputs
- it updates Workspace result tracking to use experiment-root outputs and
  structured result entries
- it rejects unsupported output combinations and operations explicitly


## 20. Non-Goals for v1

The following are not required in the first implementation wave:

- repository layout redesign
- public SDK exposure of Experiment Output
- sweep-aware Workspace comparison semantics
- default baseline visualization behavior for sweeps
- support for output forms beyond `point` and `sweep`


## 21. Recommendation

Proceed with a framework-wide refactoring that introduces Experiment Output as
the canonical semantic representation of completed experiments.

The first implementation wave should:

- add explicit persisted output semantics
- normalize completed experiments into `PointExperimentOutput` and
  `SweepExperimentOutput`
- move CLI inspection onto this layer
- move Workspace result identity to experiment-root outputs
- make compare and visualization output-aware at the entry layer
- preserve the current repository layout
- keep active Workspace workflows focused on Point Outputs for now

This provides a clean and explicit foundation for later OFAT support in
`investigation / single_system` without prematurely complicating the rest of
the Workspace system.
