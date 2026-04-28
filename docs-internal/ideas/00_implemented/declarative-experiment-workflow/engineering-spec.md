# Declarative Experiment Workflow Engineering Spec

## 1. Purpose

This engineering specification translates the declarative experiment workflow
specification into a concrete implementation plan for the current AXIS
codebase.

The implementation target is intentionally narrow:

- add a workspace-local `experiment.yaml`
- introduce a new `axis workspaces run-series` command
- support only `system_comparison` workspaces in v1
- reuse the existing `measure` workflow internally
- generate per-experiment artifacts plus aggregate series outputs
- scaffold reporting without generating scientific interpretation


## 2. Implementation Goals

The implementation must:

- keep the existing `workspace.yaml` / `measurement_workflow` model intact
- introduce a typed experiment-series model beside the workspace manifest
- resolve each experiment from a fixed candidate base config plus inline delta
- avoid mutating the workspace’s primary config files
- fail fast on any experiment or aggregation error
- preserve the current service-oriented workspace architecture


## 3. Current Architecture

The relevant code areas already in place are:

- workspace manifest model:
  - `src/axis/framework/workspaces/types.py`
- workspace manifest loading:
  - `src/axis/framework/workspaces/types.py`
- workspace sync after run / compare:
  - `src/axis/framework/workspaces/sync.py`
- workspace measurement orchestration:
  - `src/axis/framework/workspaces/services/measurement_service.py`
- workspace run orchestration:
  - `src/axis/framework/workspaces/services/run_service.py`
- workspace compare orchestration:
  - `src/axis/framework/workspaces/services/compare_service.py`
- CLI parser:
  - `src/axis/framework/cli/parser.py`
- CLI dispatch:
  - `src/axis/framework/cli/dispatch.py`
- CLI workspace commands:
  - `src/axis/framework/cli/commands/workspaces.py`

This means the new series feature should be added as a thin orchestration layer
on top of existing run / compare / measure behavior rather than as a new
parallel execution subsystem.


## 4. Architectural Placement

### 4.1 Keep experiment series outside `WorkspaceManifest`

Do not add the ordered experiment list directly into
`WorkspaceManifest` in `types.py`.

Reason:

- `workspace.yaml` stores stable workspace policy
- `experiment.yaml` stores one concrete research plan
- keeping them separate avoids unnecessary manifest churn and keeps the
  workspace model smaller

### 4.2 Add a dedicated experiment-series module

Introduce a new internal module, likely:

- `src/axis/framework/workspaces/experiment_series.py`

This module should contain:

- the typed Pydantic models for `experiment.yaml`
- validation rules
- a loader function

It should not contain:

- CLI parsing
- filesystem artifact export
- workspace execution logic

### 4.3 Add a dedicated orchestration service

Introduce a new service, likely:

- `src/axis/framework/workspaces/services/experiment_series_service.py`

This service should be the main implementation entry point for series
execution.

It should orchestrate:

- loading the workspace manifest
- loading the experiment series
- experiment-by-experiment temporary config resolution
- invocation of `WorkspaceMeasurementService`
- aggregate output generation
- optional notes scaffold handling


## 5. New Internal Model

### 5.1 Top-level series model

Recommended models in `experiment_series.py`:

- `ExperimentSeriesManifest`
- `ExperimentSeriesDefaults`
- `ExperimentSeriesExportConfig`
- `ExperimentSeriesNotesConfig`
- `ExperimentSeriesLabelsConfig`
- `ExperimentSeriesExperiment`

### 5.2 Minimal field set

The typed model should support at least:

#### `ExperimentSeriesManifest`

- `version: int`
- `workflow_type: Literal["experiment_series"]`
- `workspace_type: WorkspaceType | str`
- `title: str | None`
- `description: str | None`
- `defaults: ExperimentSeriesDefaults | None`
- `experiments: list[ExperimentSeriesExperiment]`

#### `ExperimentSeriesExperiment`

- `id: str`
- `label: str | None`
- `title: str`
- `enabled: bool = True`
- `notes: str | None`
- `hypothesis: list[str] | None`
- `candidate_config_delta: dict[str, Any]`

### 5.3 Validation rules

Validation must enforce:

- `version == 1`
- `workflow_type == "experiment_series"`
- `workspace_type == "system_comparison"` for v1 runtime acceptance
- `experiments` is non-empty
- experiment IDs are unique
- at least one experiment is enabled
- every enabled experiment has a non-empty `candidate_config_delta`

Optional but recommended:

- validate that `label` does not contain path separators
- validate that IDs are filesystem-safe enough for downstream usage


## 6. Loader Design

### 6.1 Loader function

Recommended API:

- `load_experiment_series(workspace_path: Path) -> ExperimentSeriesManifest`

Behavior:

- resolve `<workspace>/experiment.yaml`
- read YAML
- validate against the typed model
- raise explicit `ValueError` or `ValidationError` on failure

### 6.2 Workspace compatibility check

The loader should only validate the series file itself.

The compatibility check between:

- loaded workspace manifest
- loaded experiment series

should live in the service layer, not in the standalone loader.

Reason:

- the series file may be read independently
- compatibility is a runtime orchestration concern


## 7. Temporary Config Resolution

### 7.1 Principle

Each experiment must resolve from a fixed base candidate config from
`workspace.yaml`, never from the previous experiment.

For v1 `system_comparison`:

- reference config remains the workspace primary config for `role=reference`
- candidate config starts from the workspace primary config for
  `role=candidate`
- the experiment’s `candidate_config_delta` is deep-merged onto that candidate
  base config

### 7.2 No mutation of user configs

The implementation must not edit:

- `workspace.yaml`
- the original config files referenced in `primary_configs`

Instead it must create temporary materialized config files for each experiment.

### 7.3 Temporary config location

Recommended workspace-local location:

- `<workspace>/.axis_tmp/experiment_series/<series_run_id>/`

Within that directory:

- one temp candidate config per experiment
- optional copied reference config if needed for a stable run contract

Example:

```text
.axis_tmp/experiment_series/20260428T120501Z/
  exp_01-candidate.yaml
  exp_02-candidate.yaml
```

This location should be:

- internal
- disposable
- excluded from any user-facing notes or final reports

### 7.4 Merge utility

The config merge logic should reuse an existing deep-merge utility if one
already exists in the framework.

If not, add a focused helper in a workspace-local module such as:

- `src/axis/framework/workspaces/config_materialization.py`

Responsibilities:

- load baseline YAML
- deep-merge experiment delta
- write resolved YAML to a temp file
- return the resolved path plus the resolved full config object if needed


## 8. Execution Strategy

### 8.1 Reuse `WorkspaceMeasurementService`

Series execution must call into `WorkspaceMeasurementService.measure(...)`
rather than duplicating:

- run execution
- compare execution
- per-experiment log planning

This preserves one source of truth for:

- measurement folder numbering
- comparison numbering
- exported log naming

### 8.2 Required extension to measurement service

The current `WorkspaceMeasurementService.measure(...)` assumes the workspace’s
active config bindings remain unchanged.

Series execution needs a way to run one experiment against a temporary
candidate config without mutating the workspace’s original config files.

Recommended approach:

- extend `WorkspaceMeasurementService.measure(...)`
- or more likely `WorkspaceRunService.execute(...)`

to accept temporary config overrides for the current run.

Preferred shape:

- `config_overrides_by_role: dict[str, Path] | None`

For v1:

- `reference` override is optional
- `candidate` override is required for series experiments

This is better than mutating `primary_configs` in memory because it makes the
execution contract explicit.

### 8.3 Per-experiment execution loop

`WorkspaceExperimentSeriesService.run_series(...)` should:

1. load manifest
2. guard on workspace type
3. load `experiment.yaml`
4. locate reference and candidate base config entries
5. create a temporary series-run directory
6. iterate enabled experiments in declared order
7. materialize temp candidate config for the current experiment
8. invoke `measurement_service.measure(...)` with:
   - experiment label
   - optional run notes derived from experiment title / notes
   - config override(s)
9. record the returned measurement metadata
10. continue until all enabled experiments are complete
11. generate aggregate artifacts
12. handle notes scaffold prompt / output


## 9. CLI Integration

### 9.1 Parser changes

In:

- `src/axis/framework/cli/parser.py`

Add:

- `axis workspaces run-series <workspace-path>`

Recommended v1 options:

- `--allow-world-changes`
- `--override-guard`
- `--update-notes`
- `--output {text,json}`

Do not add experiment-range flags in v1.

Experiment enable/disable remains a file-level concern in `experiment.yaml`.

### 9.2 Dispatch changes

In:

- `src/axis/framework/cli/dispatch.py`

Add a new branch:

- `args.action == "run-series"`

Dispatch to:

- `cmd_workspaces_run_series(...)`

### 9.3 Command function

In:

- `src/axis/framework/cli/commands/workspaces.py`

Add:

- `cmd_workspaces_run_series(...)`

Responsibilities:

- create progress reporter
- call the new service
- print user-facing success output
- print JSON output when requested


## 10. Service-Layer API

### 10.1 Result model

Introduce a dataclass for the service result, likely:

- `WorkspaceExperimentSeriesServiceResult`

Recommended fields:

- `series_title: str | None`
- `executed_experiment_count: int`
- `executed_experiment_ids: list[str]`
- `measurement_directories: list[str]`
- `series_summary_markdown_path: str`
- `series_summary_json_path: str`
- `series_metrics_csv_path: str`
- `notes_updated: bool`

### 10.2 Main method

Recommended API:

- `run_series(workspace_path: Path, *, allow_world_changes: bool = False, override_guard: bool = False, progress: object | None = None) -> WorkspaceExperimentSeriesServiceResult`

Dependencies to inject:

- `measurement_service`
- `load_manifest_fn`
- `load_experiment_series_fn`
- optional helper(s) for config materialization and report generation


## 11. Aggregate Output Generation

### 11.1 New reporting module

Introduce a dedicated aggregation module, likely:

- `src/axis/framework/workspaces/series_reporting.py`

This module should contain:

- a normalized in-memory experiment-series result model
- Markdown rendering
- JSON rendering
- CSV table rendering

It should not contain:

- experiment execution
- manifest loading
- CLI output formatting

### 11.2 Input data for aggregation

The aggregate renderer needs, per experiment:

- experiment ID
- label
- title
- hypothesis
- measurement directory
- comparison number
- comparison log path
- run-summary log path
- run experiment IDs
- resolved result IDs from the workspace manifest or service return

It also needs derived summary data such as:

- generic run metrics
- system-specific run metrics
- key comparison metrics

### 11.3 Source of metric data

Do not parse the human-readable exported logs back into structured data.

Instead the aggregate layer should read the authoritative structured artifacts
already persisted by the framework, for example:

- workspace result summaries
- persisted behavior metrics JSON
- workspace comparison envelopes

This avoids lossy text parsing and keeps the aggregate model robust.

### 11.4 Required aggregate outputs

The aggregate layer must emit:

- `measurements/series-summary.md`
- `measurements/series-summary.json`
- `measurements/series-metrics.csv`

### 11.5 Comparison sections in Markdown

The generated Markdown report should structure comparisons into explicit
sections:

- progression view
  compare each experiment with the previous enabled experiment
- baseline view
  compare each experiment with the first enabled experiment
- reference-system view
  compare each experiment’s candidate against its paired reference

The report must remain factual and metric-based.


## 12. Notes Scaffold Handling

### 12.1 Notes scaffold generator

Introduce a small helper module, likely:

- `src/axis/framework/workspaces/series_notes.py`

Responsibilities:

- generate a Markdown scaffold for `notes.md`
- include one section per experiment
- copy experiment hypotheses into the scaffold
- leave observation and interpretation sections empty or placeholder-based

### 12.2 Overwrite policy

The spec requires a guardrail before overwriting `notes.md`.

Required v1 behavior:

- default behavior: do not overwrite `notes.md`
- if `--update-notes` is present, overwrite `notes.md` with the generated
  scaffold

This fits the current CLI architecture better than an interactive prompt and
keeps non-interactive runs deterministic.


## 13. Manifest and Sync Considerations

### 13.1 Keep using normal workspace sync

Series execution should rely on the normal workspace run/compare sync path in:

- `src/axis/framework/workspaces/sync.py`

That means:

- `primary_results` continue to be appended normally
- `primary_comparisons` continue to be appended normally

No special-case manifest mutation path is required for v1 series execution.

### 13.2 Need series-local machine-readable metadata

The workspace manifest alone is not sufficient to capture the experiment-series
mapping cleanly.

Recommended additional artifact:

- `measurements/series-manifest.json`

This file should record:

- series metadata
- experiment order
- resolved measurement directories
- result/comparison linkage
- aggregate output paths

This file is internal and machine-oriented.


## 14. Validation and Guardrails

Validation must happen at two levels.

### 14.1 Series-file validation

Handled by the `ExperimentSeriesManifest` model:

- schema shape
- unique IDs
- enabled experiment presence
- supported workflow type and version

### 14.2 Runtime validation

Handled by `WorkspaceExperimentSeriesService`:

- workspace type is `system_comparison`
- workspace has usable `primary_configs`
- exactly one reference and one candidate base config can be resolved
- temp config materialization succeeds
- each measurement run completes
- each aggregate metric source exists and is parseable

### 14.3 Error style

Errors should be direct and explainable.

Examples:

- missing `experiment.yaml`
- duplicate experiment IDs
- no enabled experiments
- workspace type unsupported for run-series
- candidate base config missing from `primary_configs`
- failed candidate config materialization for experiment `exp_03`


## 15. Suggested File-Level Changes

### 15.1 New files

Recommended additions:

- `src/axis/framework/workspaces/experiment_series.py`
- `src/axis/framework/workspaces/config_materialization.py`
- `src/axis/framework/workspaces/series_reporting.py`
- `src/axis/framework/workspaces/series_notes.py`
- `src/axis/framework/workspaces/services/experiment_series_service.py`

### 15.2 Modified files

Expected modifications:

- `src/axis/framework/cli/parser.py`
- `src/axis/framework/cli/dispatch.py`
- `src/axis/framework/cli/commands/workspaces.py`
- `src/axis/framework/workspaces/services/measurement_service.py`
- possibly `src/axis/framework/workspaces/services/run_service.py`
- possibly `src/axis/framework/cli/context.py` for service wiring


## 16. Testing Strategy

### 16.1 Unit tests

Add tests for:

- `experiment.yaml` loading and validation
- duplicate experiment ID rejection
- empty enabled-set rejection
- config delta materialization
- aggregate table generation

### 16.2 Service tests

Add tests for:

- v1 guardrail on unsupported workspace type
- fail-fast behavior on experiment failure
- correct per-experiment invocation ordering
- temp config override wiring into measure/run
- generated output path registration

### 16.3 Integration tests

Add one end-to-end integration test for a minimal `system_comparison`
workspace with:

- two enabled experiments
- one disabled experiment
- series aggregate output assertions
- verification that original primary config files are unchanged


## 17. Incremental Rollout Recommendation

The safest implementation sequence is:

1. add `experiment.yaml` typed model and loader
2. add temp config materialization
3. add config override support to the measurement/run path
4. add the series service
5. add CLI command wiring
6. add aggregate renderers
7. add optional notes scaffold generation
8. harden with integration tests

This sequence reduces risk because the hardest architectural dependency is the
ability to run existing workspace execution logic against temporary configs
without mutating the workspace’s manual-mode assets.


## 18. Key Engineering Decision Summary

The core engineering choices are:

- separate `experiment.yaml`, not `workspace.yaml`
- typed series model in a dedicated module
- fixed-baseline delta resolution, never previous-experiment inheritance
- temporary config materialization, never source-config mutation
- reuse `measure` internally
- fail-fast series execution
- aggregate from structured artifacts, not from exported text logs
- Markdown-first reporting with JSON and CSV support
- notes scaffolding without automatic interpretation

This preserves architectural consistency with the current AXIS workspace layer
while making the declarative experiment series operationally practical.
