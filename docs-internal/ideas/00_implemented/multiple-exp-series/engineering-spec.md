# Multiple Experiment Series Per Workspace Engineering Spec

## 1. Purpose

This engineering specification maps the multiple-series product specification
onto the current AXIS codebase.

It defines:

- which existing components must change
- which new data structures are required
- how series-local execution roots are introduced
- how reset becomes series-aware and confirmation-based

The goal is to implement the new multi-series model without weakening the
existing ad-hoc workspace workflow.


## 2. Current Implementation Baseline

The current implementation has these characteristics:

- series execution assumes one workspace-root `experiment.yaml`
- `run-series` does not require a series selector
- series outputs are written under workspace-global roots
- `reset` immediately clears:
  - `<workspace>/results/`
  - `<workspace>/comparisons/`
  - `<workspace>/measurements/`
- `reset` also clears manifest-tracked generated artifacts such as:
  - `primary_results`
  - `primary_comparisons`

Relevant code locations:

- `src/axis/framework/workspaces/experiment_series.py`
  - series manifest model + loader
- `src/axis/framework/workspaces/services/experiment_series_service.py`
  - end-to-end series execution
- `src/axis/framework/workspaces/services/measurement_service.py`
  - run + compare orchestration for measured workflows
- `src/axis/framework/workspaces/execute.py`
  - workspace-rooted execution routing
- `src/axis/framework/workspaces/compare.py`
  - workspace-rooted comparison routing
- `src/axis/framework/workspaces/services/workflow_service.py`
  - `reset` implementation
- `src/axis/framework/workspaces/manifest_mutator.py`
  - manifest cleanup behavior
- `src/axis/framework/cli/parser.py`
  - CLI flags
- `src/axis/framework/cli/commands/workspaces.py`
  - command handlers


## 3. Implementation Goals

The implementation must achieve all of the following:

- support many registered series per workspace
- require explicit `--series <series-id>` selection for `run-series`
- resolve series manifests from `workspace.yaml`, not by implicit root lookup
- route declarative series artifacts into series-local roots
- preserve ad-hoc workspace-global execution behavior
- make `reset` inspect both workspace-global and series-local generated roots
- make non-`--force` reset preview first and destructive action second


## 4. Workspace Manifest Model Changes

### 4.1 New Manifest Fields

The workspace manifest model needs a new optional top-level block:

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
```

### 4.2 New Pydantic Models

Introduce manifest-side models similar in style to the existing workspace type
models:

- `ExperimentSeriesGeneratedArtifacts`
  - `results: list[...]`
  - `comparisons: list[...]`
  - `measurement_runs: list[...]`
- `ExperimentSeriesEntry`
  - `id: str`
  - `path: str`
  - `title: str | None`
  - `generated: ExperimentSeriesGeneratedArtifacts`
- `ExperimentSeriesRegistry`
  - `entries: list[ExperimentSeriesEntry]`

These should live alongside the workspace manifest models in:

- `src/axis/framework/workspaces/types.py`

### 4.3 Ownership Rule

The manifest ownership rule must be explicit:

- ad-hoc workspace-generated tracking remains in existing workspace-global
  fields such as `primary_results` and `primary_comparisons`
- series-generated tracking must live only under
  `experiment_series.entries[*].generated`

Series execution must not append its result or comparison references into the
existing ad-hoc top-level fields.

### 4.4 Validation Rules

Manifest validation should enforce:

- `entries` non-empty when the block exists
- unique series IDs
- unique series paths
- workspace-relative paths only
- paths must begin with `series/`
- paths must end with `/experiment.yaml` or exactly `experiment.yaml` at the end
  of the registered series directory

The validator should not silently normalize invalid paths.


## 5. Series Manifest Loading Changes

### 5.1 Current Loader

Current loader behavior in `experiment_series.py` is singleton-shaped:

- load `<workspace>/experiment.yaml`

### 5.2 Required Change

Replace the root-only loader with a path-aware loader:

- accept `workspace_path`
- accept `series_id`
- resolve the series entry from `workspace.yaml`
- load the registered `path`

Recommended shape:

```python
load_experiment_series(workspace_path: Path | str, *, series_id: str) -> ExperimentSeriesManifest
```

or an equivalent pair of helper functions:

- one to resolve the registry entry
- one to load the YAML from the resolved path

### 5.3 Failure Cases

Loading must fail explicitly when:

- `--series` is omitted
- the workspace has no `experiment_series` block
- the requested series ID is not registered
- the registered file does not exist
- the registered YAML is invalid


## 6. CLI Surface Changes

### 6.1 `run-series`

`axis workspaces run-series` must gain:

- required `--series <series-id>`

Parser changes:

- `src/axis/framework/cli/parser.py`

Dispatch / command changes:

- `src/axis/framework/cli/dispatch.py`
- `src/axis/framework/cli/commands/workspaces.py`

`cmd_workspaces_run_series(...)` must accept and forward:

- `series_id: str`

### 6.2 `reset`

`axis workspaces reset` must gain:

- optional `--force`

Without `--force`:

- preview only
- ask for confirmation
- only then mutate filesystem + manifest

With `--force`:

- skip prompt
- execute immediately

Parser and command wiring changes belong in the same files as above.


## 7. Series-Local Path Resolution

### 7.1 New Helper Layer

The implementation needs a small helper layer that can derive all series-local
roots from a resolved series entry.

Recommended helper outputs:

- series root
  - `<workspace>/series/<series-id>/`
- series experiment manifest path
  - `<workspace>/series/<series-id>/experiment.yaml`
- series results root
  - `<workspace>/series/<series-id>/results/`
- series measurements root
  - `<workspace>/series/<series-id>/measurements/`
- series comparisons root
  - `<workspace>/series/<series-id>/comparisons/`
- series notes path
  - `<workspace>/series/<series-id>/notes.md`

This helper should be used consistently by:

- series execution
- series reporting
- notes scaffolding
- reset preview and deletion

### 7.2 Suggested Module

Either:

- extend `src/axis/framework/workspaces/resolution.py`

or introduce a dedicated module such as:

- `src/axis/framework/workspaces/series_paths.py`

The latter is likely cleaner.


## 8. Series Execution Routing Changes

### 8.1 Current State

Series execution currently writes into workspace-global roots because it reuses:

- workspace-global repository roots
- workspace-global comparison output routing
- workspace-global measurement output routing

### 8.2 Required Direction

The series workflow must be parameterized by a series-local root set.

Concretely:

- series execution must use a repository rooted at
  `series/<series-id>/results/`
- series comparisons must be written under
  `series/<series-id>/comparisons/`
- series measurements and aggregates must be written under
  `series/<series-id>/measurements/`
- notes scaffolding must target
  `series/<series-id>/notes.md`
- series-generated manifest tracking must be written under the matching
  `experiment_series.entries[*].generated` block

### 8.3 `ExperimentRepository` Rooting

The easiest path is to continue using `ExperimentRepository`, but instantiate it
with a different root for series execution:

- ad-hoc mode: `<workspace>/results/`
- series mode: `<workspace>/series/<series-id>/results/`

This keeps persistence semantics stable while relocating artifacts.


## 9. Execution Service Changes

### 9.1 `WorkspaceExperimentSeriesService`

This service becomes the main coordinator of series-local routing.

It must now:

- resolve the selected series entry
- derive the series-local roots
- load the series manifest from the series path
- execute all run/comparison/reporting work against series-local roots
- update the owning series entry's generated-artifact tracking fields

Recommended signature change:

```python
run_series(
    workspace_path: Path,
    *,
    series_id: str,
    override_guard: bool = False,
    update_notes: bool = False,
    catalogs: dict | None = None,
    progress: object | None = None,
) -> WorkspaceExperimentSeriesServiceResult
```

The service result may also need to expose enough information to persist series
tracking entries cleanly, for example:

- produced experiment IDs
- produced comparison output paths
- produced measurement directories

### 9.2 Root-Awareness Injection

The current services assume workspace-global roots in multiple places.

To avoid one-off hacks, the implementation should introduce explicit root
parameters where needed rather than relying on hidden globals.

Likely touched services:

- `WorkspaceRunService`
- `WorkspaceMeasurementService`
- `WorkspaceCompareService`
- workspace execution / comparison helpers

### 9.3 Measurement Workflow Reuse

The current measurement workflow logic is still useful, but it must become root-aware.

At minimum it needs:

- configurable measurement root
- configurable comparison root
- configurable result repository root

The existing manifest `measurement_workflow` structure may still define
filenames and numbering patterns, but the base directory for series execution
must be series-local.


## 10. Comparison Routing Changes

### 10.1 Current State

`compare_workspace(...)` hardcodes:

- results root: `<workspace>/results/`
- output root: `<workspace>/comparisons/`

### 10.2 Required Change

Introduce root-aware comparison routing.

Recommended shape:

- keep the current workspace-global helper for ad-hoc mode
- add parameters or a sibling helper for series-local mode

For example:

```python
compare_workspace(
    workspace_path: Path,
    ...,
    results_root: Path | None = None,
    comparisons_root: Path | None = None,
)
```

or a series-aware wrapper that passes the local roots explicitly.

### 10.3 Target Resolution

Series comparisons should resolve only against the selected series-local
results root by default.

Ad-hoc compare remains workspace-global and must not auto-read series-local
results.


## 11. Notes Scaffolding Changes

Series notes must move from:

- `<workspace>/notes.md`

to:

- `<workspace>/series/<series-id>/notes.md`

The notes rendering logic itself can stay mostly unchanged.

The main required change is target path routing inside
`WorkspaceExperimentSeriesService`.


## 12. Reset Redesign

### 12.1 Current State

Current reset is immediate and non-interactive:

- clear workspace-global `results/`
- clear workspace-global `comparisons/`
- clear workspace-global `measurements/`
- clear manifest-tracked generated fields

### 12.2 New Two-Step Model

Reset must become:

1. inspect
2. preview
3. confirm
4. execute

unless `--force` is provided.

### 12.3 New Internal Separation

The workflow service should separate:

- planning what would be deleted
- actually deleting it

Recommended service-level split:

- `plan_reset(workspace_path: Path) -> WorkspaceResetPlan`
- `reset(workspace_path: Path, *, force: bool = False, confirm: bool = False) -> WorkspaceResetResult`

The exact signatures may vary, but the separation of concerns is important.

### 12.4 New Reset Plan Model

Introduce a model that can describe both scopes.

Suggested shape:

- `WorkspaceResetScope`
  - `label: str`
  - `paths: list[str]`
- `WorkspaceResetPlan`
  - `workspace_path: str`
  - `workspace_global_paths: list[str]`
  - `series_paths_by_id: dict[str, list[str]]`
  - `manifest_fields_to_clear: list[str]`

This model should be renderable in both:

- text output
- JSON output

### 12.5 Deletion Rules

Reset execution must delete only generated roots:

Workspace-global:

- `results/`
- `measurements/`
- `comparisons/`

Per registered series:

- `series/<series-id>/results/`
- `series/<series-id>/measurements/`
- `series/<series-id>/comparisons/`

It must preserve:

- `workspace.yaml`
- workspace-root `notes.md`
- `series/<series-id>/experiment.yaml`
- `series/<series-id>/notes.md`
- any series directory content outside the generated roots

### 12.6 Manifest Cleanup

Current manifest cleanup logic in `reset_workspace_artifacts(...)` is
workspace-global only.

This should be extended carefully:

- clear ad-hoc generated tracking fields such as `primary_results` and
  `primary_comparisons`
- clear `experiment_series.entries[*].generated.results`
- clear `experiment_series.entries[*].generated.comparisons`
- clear `experiment_series.entries[*].generated.measurement_runs`

The cleanup function should not assume that deleting artifacts also means
deleting authored series registry entries.

### 12.7 CLI Confirmation Flow

`cmd_workspaces_reset(...)` should change to:

1. request a reset plan from the workflow service
2. render the plan
3. if `--force`, execute immediately
4. otherwise ask the user for confirmation
5. execute only on confirmation

Suggested confirmation wording:

> Delete the generated workspace artifacts listed above?

If declined:

- print a cancellation message
- exit successfully without changes

Because the current mode is non-Plan terminal interaction, a small direct prompt
in the CLI command implementation is appropriate.


## 13. Text Output and JSON Output

### 13.1 `run-series`

JSON mode must remain machine-readable and include at least:

- selected `series_id`
- series-local aggregate output paths
- `notes_updated`

Text mode should mention the selected series clearly so that the user can see
which campaign is being executed.

### 13.2 `reset`

JSON mode should distinguish:

- preview output
- executed reset result

This can be done either via:

- a `mode: preview|executed` field

or separate command output shapes with an explicit top-level discriminator.

Text mode should show:

- workspace-global paths to be cleared
- series-local paths grouped by series ID
- manifest fields that will be cleared


## 14. Validation and Check Integration

`axis workspaces check` should become series-aware.

It should validate:

- registry structure
- registered file existence
- series manifest validity
- duplicate series IDs
- duplicate series paths

This should likely be implemented in the existing workspace validation layer
rather than as ad-hoc checks inside `run-series`.


## 15. Tests

At minimum, add or update tests for:

### 15.1 Manifest and Loading

- valid workspace manifest with two registered series
- duplicate series ID rejection
- invalid path rejection
- missing registered series file rejection
- `run-series` without `--series` rejection
- unknown `--series` rejection

### 15.2 Series Routing

- `run-series --series system-variants` writes results under
  `series/system-variants/results/`
- aggregate outputs go under
  `series/system-variants/measurements/`
- notes scaffolding writes to
  `series/system-variants/notes.md`
- ad-hoc workspace `run` still writes to workspace-global roots

### 15.3 Reset

- reset preview lists workspace-global roots
- reset preview lists all registered series-local roots
- non-force reset cancellation leaves filesystem unchanged
- `--force` reset clears both workspace-global and series-local generated roots
- reset preserves `experiment.yaml` and `notes.md` files under series roots
- manifest cleanup still clears ad-hoc generated tracking fields

### 15.4 Comparison Isolation

- ad-hoc compare reads only workspace-global artifacts
- series execution compares only within the selected series-local root


## 16. Suggested Implementation Sequence

1. add workspace manifest registry models and validation
2. add path-aware series resolution helpers
3. update CLI parser and `run-series` command to require `--series`
4. make series loader resolve the selected registered series file
5. refactor series execution services to accept explicit local roots
6. route series results, comparisons, measurements, and notes into the series directory
7. redesign reset into preview + confirm + `--force`
8. extend validation and integration tests


## 17. Risks

Main implementation risks:

- root assumptions are currently spread across several workspace services
- series-local repository rooting will touch both execution and comparison flows
- reset preview and execution must not accidentally delete authored files

The safest mitigation is to centralize path derivation early and make the
affected services explicitly root-aware rather than patching path logic in many
places ad hoc.


## 18. Recommendation

Proceed with implementation.

The design is technically feasible within the current AXIS architecture. The
most important engineering move is to make workspace services explicitly aware
of execution roots and artifact scopes, then build series-local routing and
reset planning on top of that.
