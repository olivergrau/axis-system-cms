# Experiment Output Abstraction Detailed Draft

## Purpose

This detailed draft refines the first proposal for a framework-level
**Experiment Output** abstraction in AXIS-CMS.

The abstraction is intended to sit in the architectural layer:

- above persistence,
- above raw experiment execution artifacts,
- below Workspace workflows.

Its purpose is to give the framework a consistent semantic model for completed
experiment outputs, independent of whether the underlying experiment was:

- a `single_run`, or
- an `ofat` sweep.


## Architectural Position

AXIS already has a clear conceptual progression:

- step
- episode
- run
- experiment
- workspace

The `single_run` vs `ofat` distinction is already a distinction at the
**experiment level**.

Therefore, the abstraction introduced here must also live at the
**experiment level**, not only inside Workspace logic.

This means:

- persistence may remain filesystem-based and mostly unchanged,
- but framework consumers must no longer interpret experiments purely through
  raw run paths,
- and instead should operate through a normalized `ExperimentOutput` model.


## Core Design Decision

The framework shall distinguish exactly two experiment output forms in v1:

- `point`
- `sweep`

These forms are conceptually mapped as follows:

- `experiment_type = single_run` => `output_form = point`
- `experiment_type = ofat` => `output_form = sweep`

In v1, this mapping remains conceptually fixed, but `output_form` should still
be treated as an **explicit persisted field**, not merely as a derived runtime
interpretation.

This is an intentional design choice:

- derivation alone would technically work for the current two experiment types,
  but
- explicit persistence creates a more stable semantic contract,
- avoids hidden inference,
- reduces "magic" in downstream consumers,
- and gives future refactorings a clearer migration path if additional output
  forms are ever introduced.

Therefore the framework should aim for:

- conceptual mapping from `experiment_type` to `output_form`,
- plus explicit persisted representation of `output_form`.


## Why This Abstraction Is Needed

### Current situation

The raw persisted structure is already unified enough:

- every experiment has one experiment root,
- one config,
- one metadata file,
- one summary,
- one or more runs.

However, the meaning of those artifacts differs substantially:

#### `single_run`

- exactly one run
- one directly operational run summary
- one directly operational set of episode traces
- experiment and run are almost interchangeable in operational workflows

#### `ofat`

- multiple runs
- each run is a variation along one parameter axis
- one baseline run
- one sweep-level experiment summary with delta semantics
- the ordered run set is meaningful as a whole

This means the difference is **semantic**, not primarily structural.


## Output Model Overview

The abstraction introduced here is:

- one `ExperimentOutput` base concept
- with two concrete forms:
  - `PointExperimentOutput`
  - `SweepExperimentOutput`

The abstraction represents **one complete experiment**, never an individual run
or episode.


## Base Experiment Output

Every experiment output should expose a common set of framework-level fields.

The exact implementation type is left open until the spec, but the conceptual
shape in v1 should include at least:

- `experiment_id`
- `experiment_type`
- `output_form`
- `system_type`
- `created_at`
- `num_runs`
- `experiment_root_path`
- `summary_path`

Optional but strongly recommended common fields:

- `name`
- `description`
- `status`

The purpose of the base model is:

- to give CLI, Workspaces, and future analysis code one stable entry point,
- without forcing all consumers to understand raw repository structure.


## Point Experiment Output

`PointExperimentOutput` represents an experiment whose operational meaning is a
single concrete run.

### Required conceptual fields

In addition to the base fields:

- `primary_run_id`
- `primary_run_path`

Optional convenience fields:

- `primary_run_summary_path`
- `primary_run_result_path`

### Semantics

A Point Output says:

- this experiment should be treated as one concrete executable result
- its primary operational run is explicitly known

This is the form that current Workspace flows already implicitly assume.


## Sweep Experiment Output

`SweepExperimentOutput` represents an experiment whose operational meaning is
an ordered parameter sweep.

### Required conceptual fields

In addition to the base fields:

- `parameter_path`
- `parameter_values`
- `baseline_run_id`
- `run_ids`
- `variation_descriptions`

Optional convenience fields:

- `baseline_run_path`
- `run_paths`

### Semantics

A Sweep Output says:

- this experiment is not just "many unrelated runs"
- it is one coherent sweep over one parameter axis
- one run is the baseline
- the run set must be interpreted as an ordered family

This is the minimum required model for preserving OFAT semantics.


## Summary Handling

The output abstraction should not embed the full persisted summary object as an
opaque blob in v1.

Instead:

- the abstraction should reference or interpret the experiment summary,
- and expose only the fields needed for normalized downstream use.

This keeps the model lightweight while preserving explicit output semantics.


## Persistence Impact

### Principle

The persistence layer should remain as stable as possible.

The initial goal is not to redesign the repository tree.

### Allowed adjustments

However, smaller persistence changes are explicitly allowed if they make output
semantics more robust and less dependent on brittle inference.

These changes should remain additive and local.

### Persistence review target

During implementation, the framework must verify whether the following data is
already available robustly enough for output construction:

- `experiment_type`
- `output_form`
- `system_type`
- `created_at`
- `num_runs`
- `parameter_path`
- `parameter_values`
- variation ordering
- baseline run identity

If any of these cannot be reconstructed reliably enough from:

- `ExperimentConfig`
- `ExperimentMetadata`
- `ExperimentSummary`
- `RunMetadata`

then small persistence additions are acceptable.

In particular, this detailed draft now recommends that `output_form` be added
explicitly to persisted experiment-level metadata rather than being treated as a
purely derived property.

The principle is:

- derive only where derivation is genuinely harmless,
- persist explicitly where the field carries stable semantic meaning that many
  downstream layers will depend on.

`output_form` falls into the second category.


## Output Artifact Path vs Operational Selection

This draft introduces a strict distinction between:

### 1. Output artifact path

The path of the experiment output as a framework-level artifact.

Example:

- `results/<experiment-id>`

### 2. Operational selection

The concrete run selected for a specific operation such as:

- compare
- visualize
- run-role resolution

Examples:

- Point Output:
  - primary run = `run-0000`
- Sweep Output:
  - baseline run = first variation
  - or one explicitly selected variation run

This distinction is essential.

Without it, the framework collapses output identity and operational selection
into one path concept and becomes point-output-biased.


## Immediate Consequence For Workspaces

The current Workspace model should be refactored so that `primary_results`
tracks **experiment-root outputs**, not run directories.

That means the primary result entries should conceptually point to:

- `results/<experiment-id>`

and not to:

- `results/<experiment-id>/runs/<run-id>`

The run selection required for compare or visualization must then be resolved
through the `ExperimentOutput`, not through direct path assumptions.

Backward compatibility is not a priority here because the Workspace system is
still new enough to be refactored cleanly.


## CLI Integration

The abstraction should be used consistently across the framework, not only by
Workspaces.

### Scope

The first direct CLI consumers should be:

- `axis experiments show`
- `axis experiments list`

Run-oriented CLI commands may remain run-oriented, but should become aware of
their enclosing output form.

### Desired behavior

The CLI should no longer simply expose raw experiment structure.

Instead it should interpret experiments as either:

- Point Outputs
- Sweep Outputs

and render summaries accordingly.

This makes the refactoring framework-wide rather than workspace-local.


## Compare Integration

After the refactoring, compare should conceptually accept
**Experiment Outputs** as its higher-level input layer.

### v1 operational target

Only one case must become actively supported in the first refactoring wave:

- `point vs point`

This should map internally to the current run-vs-run comparison flow.

### Future cases

The design should remain open for later cases:

- `point vs sweep`
- `sweep vs point`
- `sweep vs sweep`

These are out of scope for the first implementation wave, but the output model
must not block them.


## Visualization Integration

Visualization should also become output-aware.

That means:

- resolve `ExperimentOutput` first
- then resolve the concrete run to visualize

This is especially important because a Sweep Output may contain multiple valid
run candidates for visualization, while a Point Output has a natural default.


## Workspace Integration

### Point Output

All current Workspace types can continue to operate on Point Outputs.

This includes:

- `investigation / single_system`
- `investigation / system_comparison`
- `development / system_development`

### Sweep Output

The output model must support Sweep Outputs in the framework, but Workspace
behavior should remain conservative in the first wave.

In particular:

- current Workspace workflows should continue to rely on Point Outputs
- Sweep Output support in Workspace mode should be introduced later and
  selectively
- the likely first target remains:
  - `investigation / single_system`


## Proposed Initial Module Placement

The abstraction should initially live in a single framework module:

- `src/axis/framework/experiment_output.py`

The module may later be expanded into a package if needed, but the first
introduction should stay compact.


## Design Constraints

The implementation should preserve these constraints:

- no repository redesign in v1
- explicit output semantics are preferred over implicit derivation when they
  improve clarity and stability
- no point-only assumptions in new framework interfaces
- no forced early support for sweep-aware comparison semantics

The relationship between `experiment_type` and `output_form` must still remain
well-defined and validated. Explicit persistence does not mean unconstrained
duplication. It means:

- both fields may exist,
- their allowed combinations are validated,
- and the framework treats invalid combinations as errors rather than silently
  inferring intent.


## Open Questions

1. Should `primary_run_id` and `baseline_run_id` remain purely derived, or be
   persisted as explicit metadata for robustness?
2. Should variation ordering be trusted from `parameter_values` alone, or also
   persisted explicitly in run metadata?
3. Should `axis runs show` surface enclosing output-form information directly?
4. Should the output abstraction eventually become part of public SDK-facing
   framework APIs, or remain an internal framework contract?
5. Should Workspace manifests eventually store typed output entries instead of
   plain result paths?


## Detailed Draft Recommendation

Proceed with a framework-level refactoring that introduces `ExperimentOutput`
as the canonical semantic interpretation of completed experiments.

The first wave should:

- introduce `PointExperimentOutput` and `SweepExperimentOutput`
- persist `output_form` explicitly at the experiment level
- refactor result identity from run-path-centric to experiment-output-centric
- make CLI inspection output-aware
- make compare and visualize output-aware at the entry layer
- refactor Workspace `primary_results` to experiment roots
- keep Workspace behavior operationally focused on Point Outputs for now

This creates a clean architectural foundation for future OFAT support in
Workspace mode without prematurely complicating comparison or development
workflows.
