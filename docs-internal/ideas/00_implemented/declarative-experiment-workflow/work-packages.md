# Declarative Experiment Workflow Work Packages

## Purpose

This document breaks the declarative experiment workflow implementation into
concrete work packages derived from:

- [spec.md](./spec.md)
- [engineering-spec.md](./engineering-spec.md)

The rollout is intentionally incremental.

The most important principle is:

> do not build a second execution stack

The new series feature must reuse the existing workspace run / compare /
measure flow wherever possible.


## WP-01: Series Manifest Model And Loader

### Goal

Introduce the typed `experiment.yaml` model and validation layer.

### Scope

- add `src/axis/framework/workspaces/experiment_series.py`
- define typed models for:
  - top-level series manifest
  - defaults block
  - experiment entries
- implement `load_experiment_series(workspace_path)`
- validate:
  - supported version
  - workflow type
  - non-empty experiment list
  - unique experiment IDs
  - at least one enabled experiment
  - non-empty `candidate_config_delta` for enabled experiments

### Deliverables

- typed series model
- YAML loader
- unit tests for validation failures and happy path

### Depends On

- none


## WP-02: Temporary Config Materialization

### Goal

Resolve each experiment from the workspace candidate base config plus inline
delta, without mutating the real config files.

### Scope

- add `src/axis/framework/workspaces/config_materialization.py`
- load the baseline candidate config from `workspace.yaml`
- deep-merge `candidate_config_delta`
- write materialized temp configs to a workspace-local temp directory
- return paths plus resolved config metadata as needed
- validate that base reference/candidate configs are resolvable

### Deliverables

- config materialization helper
- temp directory strategy
- unit tests for merge semantics and non-mutation guarantees

### Depends On

- WP-01


## WP-03: Config Override Support In Execution Path

### Goal

Allow the existing run/measure pipeline to execute against temporary configs
for one experiment in the series.

### Scope

- extend the run/measure path to accept config overrides by role
- likely touch:
  - `WorkspaceMeasurementService`
  - `WorkspaceRunService`
- preserve current behavior when no override is supplied
- ensure `measure` can run a `system_comparison` workspace using:
  - original reference config
  - temporary candidate config

### Deliverables

- override-capable service API
- backward-compatible default behavior
- service tests for override wiring

### Depends On

- WP-02


## WP-04: Experiment Series Orchestration Service

### Goal

Introduce the main orchestration service that executes enabled experiments in
order and fails fast on any error.

### Scope

- add `src/axis/framework/workspaces/services/experiment_series_service.py`
- load workspace manifest and series manifest
- guardrail on unsupported workspace type
- iterate enabled experiments in declared order
- materialize temp config for each experiment
- call `measurement_service.measure(...)` with:
  - label override
  - config override
  - optional per-experiment run notes
- collect structured series-execution results
- stop immediately on failure

### Deliverables

- `WorkspaceExperimentSeriesService`
- typed result object
- fail-fast execution behavior
- service tests for sequencing and abort behavior

### Depends On

- WP-01
- WP-02
- WP-03


## WP-05: Aggregate Series Reporting

### Goal

Generate final cross-experiment outputs from authoritative structured artifacts,
not by parsing exported text logs.

### Scope

- add `src/axis/framework/workspaces/series_reporting.py`
- build a normalized in-memory representation of executed experiments
- render:
  - `measurements/series-summary.md`
  - `measurements/series-summary.json`
  - `measurements/series-metrics.csv`
- include comparison lenses for:
  - previous experiment
  - baseline experiment
  - workspace reference system
- keep reporting factual and metric-based only

### Deliverables

- aggregate Markdown renderer
- aggregate JSON renderer
- aggregate CSV renderer
- tests for output structure and key contents

### Depends On

- WP-04


## WP-06: Notes Scaffold And `--update-notes`

### Goal

Support explicit regeneration of `notes.md` through a safe opt-in flag.

### Scope

- add `src/axis/framework/workspaces/series_notes.py`
- generate a scaffold with:
  - one section per experiment
  - copied hypotheses
  - placeholders for observations and interpretation
- implement `--update-notes` behavior:
  - default: do not touch `notes.md`
  - with flag: overwrite `notes.md` with regenerated scaffold
- ensure the series service returns whether notes were updated

### Deliverables

- scaffold generator
- explicit overwrite path
- tests for default no-touch behavior and opt-in overwrite behavior

### Depends On

- WP-04


## WP-07: CLI Integration

### Goal

Expose the experiment series workflow through the workspace CLI.

### Scope

- update `src/axis/framework/cli/parser.py`
- update `src/axis/framework/cli/dispatch.py`
- update `src/axis/framework/cli/commands/workspaces.py`
- add:
  - `axis workspaces run-series <workspace>`
  - `--allow-world-changes`
  - `--override-guard`
  - `--update-notes`
  - standard output mode support
- wire the new service through CLI context/dependency construction

### Deliverables

- parser support
- dispatch support
- user-facing command implementation
- CLI tests

### Depends On

- WP-04
- WP-05
- WP-06


## WP-08: Machine-Readable Series Manifest And Metadata Linking

### Goal

Persist one machine-readable summary artifact that links the declared series to
the realized outputs.

### Scope

- write `measurements/series-manifest.json`
- include:
  - series metadata
  - experiment order
  - measurement directories
  - result IDs
  - comparison IDs
  - aggregate output paths
- make the file suitable for future tooling and inspection commands

### Deliverables

- series-manifest writer
- JSON schema shape stabilized in tests

### Depends On

- WP-04
- WP-05


## WP-09: Integration Hardening

### Goal

Validate the whole end-to-end feature on realistic workspace fixtures.

### Scope

- add integration tests for:
  - successful two-experiment series
  - disabled experiment skipping
  - unsupported workspace-type guardrail
  - fail-fast behavior on mid-series error
  - untouched original config files
  - `--update-notes` overwrite path
- verify aggregate artifacts are written where expected

### Deliverables

- integration coverage
- regression protection for the orchestration path

### Depends On

- WP-07
- WP-08


## Recommended Delivery Order

Recommended implementation sequence:

1. WP-01
2. WP-02
3. WP-03
4. WP-04
5. WP-05
6. WP-06
7. WP-07
8. WP-08
9. WP-09

This order keeps the highest-risk technical dependency early:

- running the existing workspace pipeline against temporary configs without
  mutating user-owned config files


## Suggested Milestones

### Milestone A

Core internal execution works.

Includes:

- WP-01
- WP-02
- WP-03
- WP-04

### Milestone B

User-visible outputs and reporting are in place.

Includes:

- WP-05
- WP-06
- WP-07

### Milestone C

Persistence and hardening are complete.

Includes:

- WP-08
- WP-09


## Definition Of Done

The feature is done for v1 when:

- `axis workspaces run-series .` works for `system_comparison`
- `experiment.yaml` is validated and enforced
- every enabled experiment executes via the existing measure path
- aggregate Markdown, JSON, and CSV outputs are generated
- `notes.md` is only overwritten when `--update-notes` is explicitly passed
- unsupported workspace types fail with a clear guardrail
- original workspace config files remain unchanged
