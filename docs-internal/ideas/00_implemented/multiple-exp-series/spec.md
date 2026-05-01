# Multiple Experiment Series Per Workspace Spec

## 1. Purpose

This specification defines how AXIS workspaces support multiple declarative
experiment series inside one workspace.

The goal is to separate two concerns that are currently conflated:

- the workspace as the long-lived investigation container
- the series as one named experiment campaign inside that container

This makes it possible to keep several related but distinct campaigns together,
for example:

- a system-only series
- a world-only series
- a follow-up series after an initial broad campaign

without mixing their measurements, notes, and aggregate outputs.


## 2. Scope

This specification covers:

- the canonical multi-series workspace structure
- workspace manifest semantics for series registration
- series-local artifact layout
- command selection semantics for running a series
- reset semantics for mixed ad-hoc and series-aware workspaces
- the relationship between ad-hoc workspace workflows and series workflows

This specification does **not** define:

- automatic migration from older single-series layouts
- implicit series discovery without workspace registration
- cross-series auto-comparison
- a generic workflow engine across multiple workspaces


## 3. Product Position

This feature is a workspace-level campaign organization feature.

It is not:

- a replacement for ordinary ad-hoc workspace runs
- a replacement for the existing workspace root artifact model
- a global campaign manager spanning many workspaces

The intended product model is:

- ad-hoc workspace activity continues to use the ordinary workspace roots
- declarative series execution becomes a named, explicitly selected sub-workflow
  inside the workspace


## 4. Core Design

### 4.1 Two Levels

AXIS must treat the following as distinct levels:

- Workspace
  - the overall investigation container
- Series
  - one named declarative experiment campaign inside that workspace

### 4.2 Canonical Storage Model

The canonical storage model is:

- one workspace-level series index in `workspace.yaml`
- one dedicated `series/` directory in the workspace root
- one subdirectory per registered series
- one `experiment.yaml` per series directory

This means the series system is no longer singleton-shaped.

### 4.3 No Legacy Compatibility Layer

This specification does not preserve the older root-level single-series model.

In the canonical model defined here:

- root-level `experiment.yaml` is not part of the supported series workflow
- series must live under `series/<series-id>/experiment.yaml`
- `run-series` must operate only on explicitly selected registered series


## 5. Workspace Manifest Semantics

### 5.1 New Workspace-Level Registry

`workspace.yaml` must expose a first-class registry of available series.

Example shape:

```yaml
experiment_series:
  entries:
    - id: system-variants
      path: series/system-variants/experiment.yaml
      title: System-only variants
      generated:
        results: []
        comparisons: []
        measurement_runs: []
    - id: world-variants
      path: series/world-variants/experiment.yaml
      title: World-only variants
      generated:
        results: []
        comparisons: []
        measurement_runs: []
```

### 5.2 Required Semantics

The workspace-level series registry must satisfy:

- `entries` is required when the workspace declares any series
- every series entry has a unique `id`
- every `path` is workspace-relative
- every `path` must point to a file under `series/`
- every `path` must end in `experiment.yaml`
- each registered `id` must correspond to exactly one registered path
- each registered series entry owns its own generated-artifact tracking

### 5.3 Series-Owned Manifest Tracking

Series-generated manifest tracking must live under the corresponding
`experiment_series.entries[*]` item.

It must not be merged into the workspace-global ad-hoc tracking fields such as:

- `primary_results`
- `primary_comparisons`

Conceptually:

- workspace-global tracking fields describe ad-hoc workspace activity
- series-local tracking fields describe generated artifacts for one named series

Recommended shape:

```yaml
experiment_series:
  entries:
    - id: system-variants
      path: series/system-variants/experiment.yaml
      title: System-only variants
      generated:
        results:
          - path: series/system-variants/results/exp-001
            timestamp: "2026-05-01T12:00:00"
            config: series/system-variants/results/exp-001/experiment_config.json
            primary_run_id: run-0000
        comparisons:
          - series/system-variants/comparisons/comparison-001.json
        measurement_runs:
          - path: series/system-variants/measurements/experiment_1
            label: system-variants-exp_01
```

This specification does not require the exact final field names above, but it
does require the structural rule:

- series-generated tracking belongs under the owning series entry
- workspace-global tracking belongs only to ad-hoc workflow

### 5.4 No Default Series

This specification does not define a default or active series pointer.

The reason is intentional:

- series execution is a deliberate campaign choice
- implicit default selection is error-prone
- users should state the target series explicitly when invoking series commands


## 6. Canonical Directory Layout

### 6.1 Workspace Layout

The canonical workspace layout becomes:

```text
workspaces/my-workspace/
  workspace.yaml
  notes.md
  results/
  measurements/
  comparisons/
  series/
    system-variants/
      experiment.yaml
      notes.md
      results/
      measurements/
      comparisons/
    world-variants/
      experiment.yaml
      notes.md
      results/
      measurements/
      comparisons/
```

### 6.2 Semantics of the Two Roots

Workspace-global roots remain reserved for ad-hoc activity:

- `results/`
- `measurements/`
- `comparisons/`
- workspace-root `notes.md`

Series-local roots are reserved for declarative series execution:

- `series/<series-id>/results/`
- `series/<series-id>/measurements/`
- `series/<series-id>/comparisons/`
- `series/<series-id>/notes.md`

This preserves the existing ad-hoc workflow while keeping declarative campaign
artifacts isolated.


## 6.3 Reset Awareness

Because the workspace now contains two artifact scopes:

- workspace-global ad-hoc artifacts
- series-local declarative artifacts

the reset workflow must become series-aware.

It is no longer sufficient to blindly clear only:

- `results/`
- `measurements/`
- `comparisons/`

at the workspace root.

Reset must account for:

- workspace-global roots
- every registered series-local root
- the distinction between authored files and generated files


## 7. Series Discovery Model

Series discovery is manifest-driven, not directory-driven.

That means:

- AXIS must not treat arbitrary subdirectories under `series/` as active series
- only series listed in `workspace.yaml` are valid command targets
- if a registered path is missing, validation must fail explicitly

This avoids accidental or stale series directories silently becoming part of the
official workspace state.


## 8. Series File Semantics

### 8.1 File Location

Each registered series must define its declaration in:

```text
series/<series-id>/experiment.yaml
```

### 8.2 File Meaning

Each such file defines exactly one ordered series campaign for the owning
workspace.

The series file remains the home of:

- declared experiment order
- per-experiment deltas
- series title and description
- series defaults
- notes scaffolding behavior

### 8.3 Existing `experiment.yaml` Semantics

The existing experiment-series schema remains the basis for the per-series file.

This specification changes:

- where the file lives
- how it is discovered
- where its outputs are written

It does not require the core experiment-list semantics to be reinvented.


## 9. Command Surface

### 9.1 `run-series`

The canonical invocation becomes:

```bash
axis workspaces run-series <workspace> --series <series-id>
```

Example:

```bash
axis workspaces run-series . --series system-variants
```

Optional notes overwrite remains available:

```bash
axis workspaces run-series . --series system-variants --update-notes
```

### 9.2 Required Selection Rule

`--series` is required.

If omitted, AXIS must fail with an explicit error in this spirit:

> `axis workspaces run-series` requires `--series <series-id>`.
> This workspace may contain multiple registered series.

### 9.3 Resolution Rule

When `--series <series-id>` is provided, AXIS must:

1. load `workspace.yaml`
2. resolve the requested series entry by ID
3. load that series file from its registered path
4. execute the series against the owning workspace
5. write all series-generated artifacts into that series directory

### 9.4 `reset`

`axis workspaces reset <workspace>` remains the workspace-level cleanup command,
but it must become series-aware.

The command must support:

```bash
axis workspaces reset <workspace>
axis workspaces reset <workspace> --force
```

### 9.5 Interactive Confirmation Model

Without `--force`, reset must not immediately delete anything.

Instead it must:

1. inspect the workspace
2. enumerate which generated paths will be cleared
3. present that plan to the user
4. ask for explicit confirmation
5. execute the reset only after confirmation

If the user declines, the command must exit without modifying artifacts or
manifest state.

### 9.6 `--force`

`--force` skips the confirmation prompt and executes the reset immediately.

This is intended for scripted or already-reviewed workflows.


## 10. Artifact Routing

### 10.1 Ad-hoc Workflow

Ad-hoc workspace commands remain workspace-global.

This includes commands such as:

- `axis workspaces run`
- `axis workspaces compare`
- `axis workspaces measure`

Their artifacts continue to go to:

- `<workspace>/results/`
- `<workspace>/measurements/`
- `<workspace>/comparisons/`
- `<workspace>/notes.md` where applicable

### 10.2 Series Workflow

Series execution must be series-local.

For a selected series `<series-id>`, `run-series` must write to:

- `<workspace>/series/<series-id>/results/`
- `<workspace>/series/<series-id>/measurements/`
- `<workspace>/series/<series-id>/comparisons/`
- `<workspace>/series/<series-id>/notes.md`

### 10.3 Aggregate Outputs

The aggregate outputs produced by `run-series` must be written under the
selected series measurement root:

- `series-summary.md`
- `series-summary.json`
- `series-metrics.csv`
- `series-manifest.json`

Example:

```text
series/system-variants/measurements/series-summary.md
series/system-variants/measurements/series-summary.json
series/system-variants/measurements/series-metrics.csv
series/system-variants/measurements/series-manifest.json
```


## 11. Notes Model

Notes for declarative series execution are series-local.

That means:

- `--update-notes` during `run-series` targets
  `series/<series-id>/notes.md`
- workspace-root `notes.md` remains the ad-hoc workspace notes file

This is required because notes usually belong to one campaign, not to all
campaigns mixed together.


## 12. Results and Comparison Semantics

### 12.1 Series Results

Series execution owns its own result namespace.

Persisted experiment results produced by a series must go into the selected
series-local `results/` root, not into the workspace-global `results/`.

This avoids:

- accidental mixing of ad-hoc and declarative campaign runs
- ambiguity about result ownership
- fragile series-to-result bookkeeping

Additionally, the manifest references to those results must be recorded under
the owning series entry in `experiment_series`, not in `primary_results`.

### 12.2 Series Comparisons

Comparisons produced by a series must go into the selected series-local
`comparisons/` root.

Their manifest references must also be recorded under the owning series entry in
`experiment_series`, not in `primary_comparisons`.

### 12.3 Ad-hoc Compare Behavior

An ad-hoc workspace comparison, meaning a comparison command with no explicit
series context, must continue to operate only on ad-hoc workspace-global runs.

This preserves the existing non-series workflow as a separate operational mode.


## 13. Reset Semantics

### 13.1 Reset Scope

Workspace reset must clear generated artifacts in both scopes:

- workspace-global ad-hoc scope
- every registered series-local scope

### 13.2 Generated Artifacts To Clear

At minimum, reset must clear:

Workspace-global:

- `<workspace>/results/`
- `<workspace>/measurements/`
- `<workspace>/comparisons/`

For each registered series `<series-id>`:

- `<workspace>/series/<series-id>/results/`
- `<workspace>/series/<series-id>/measurements/`
- `<workspace>/series/<series-id>/comparisons/`

### 13.3 Authored Files Must Be Preserved

Reset must not delete authored files such as:

- `workspace.yaml`
- workspace-root `notes.md`
- `series/<series-id>/experiment.yaml`
- `series/<series-id>/notes.md`
- manually authored README or documentation files

### 13.4 Manifest Reset Semantics

Reset must clear manifest tracking for generated artifacts that belong to the
workspace-global ad-hoc workflow.

This includes at minimum:

- `primary_results`
- `primary_comparisons`

Reset must also clear the generated-artifact tracking fields for every
registered series entry under `experiment_series`.

### 13.5 Reset Preview

The non-`--force` reset preview must clearly distinguish:

- workspace-global paths to be cleared
- series-local paths to be cleared, grouped by series ID

The preview must be specific enough that the user can see which scopes are
affected before any deletion happens.


## 14. Validation Rules

The workspace validator must enforce at least the following:

- every registered series ID is unique
- every registered series path is workspace-relative
- every registered series path points under `series/`
- every registered series file exists
- every registered series file is valid under the experiment-series schema
- the series file's declared `workspace_type` matches the owning workspace

Additionally:

- a `run-series --series <id>` invocation must fail if `<id>` is not registered
- a missing or invalid registered series file must fail explicitly


## 15. Non-Goals

This specification does not introduce:

- implicit root-level `experiment.yaml` support
- auto-selection of a default series
- auto-comparison across different series
- auto-promotion of ad-hoc results into a series
- a many-workspace campaign abstraction


## 16. Minimal Command Set

This specification requires only:

- `axis workspaces run-series <workspace> --series <series-id>`
- `axis workspaces reset <workspace>`
- `axis workspaces reset <workspace> --force`

Possible future commands such as:

- `axis workspaces list-series`
- `axis workspaces show-series`

are compatible with this model, but are not required by this specification.


## 17. Implementation Direction

The intended implementation direction is:

1. add a workspace-level series registry to `workspace.yaml`
2. require series declarations to live under `series/<series-id>/experiment.yaml`
3. require `--series <series-id>` for `run-series`
4. route all series artifacts into the selected series directory
5. make `reset` inspect and clear both workspace-global and series-local
   generated artifacts
6. add a confirmation-first reset flow with `--force` override
7. keep ad-hoc workspace behavior unchanged and workspace-global


## 18. Recommendation

This design should be adopted.

It solves a real structural limitation in the current experiment-series model
and does so with a clean separation:

- workspace-global roots for ad-hoc investigation activity
- series-local roots for named declarative campaigns

The key design choices are:

- dedicated `series/` directory
- explicit workspace-level series index
- explicit `--series` selection
- no legacy compatibility burden
- no implicit defaults
