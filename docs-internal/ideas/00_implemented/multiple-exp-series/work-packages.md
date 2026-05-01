# Multiple Experiment Series Per Workspace Work Packages

## Purpose

This document defines a coarse-grained implementation roadmap for the
multiple-series-per-workspace feature.

It is derived from:

- [spec.md](./spec.md)
- [engineering-spec.md](./engineering-spec.md)

The goal is to define a delivery structure that is:

- implementable in bounded steps
- aligned with the current AXIS architecture
- explicit about where model changes happen first


## Current Code Reality

The current codebase already provides useful building blocks:

- typed workspace manifests
- typed experiment-series manifests
- workspace-owned execution and comparison services
- reusable measurement and reporting flow
- a workspace reset service with manifest mutation wiring

However, the current implementation still assumes a singleton series model:

- one workspace-root `experiment.yaml`
- workspace-global artifact roots for series outputs
- no workspace-level series registry
- no series-local generated-artifact manifest tracking
- immediate destructive `reset` with no preview or confirmation


## Delivery Strategy

The implementation should proceed in six layers:

1. **Manifest model and series registry**
   Introduce the new canonical workspace-level series structure.
2. **Series resolution and local root routing**
   Make the codebase able to resolve one selected series and derive its local
   paths.
3. **Series execution and manifest tracking**
   Route series-generated artifacts into series-local roots and record them
   under `experiment_series.entries[*].generated`.
4. **CLI integration**
   Require explicit `--series` selection and expose the new behavior
   consistently.
5. **Reset redesign**
   Make reset inspect, preview, confirm, and clear both ad-hoc and series-local
   generated scopes.
6. **Hardening and docs**
   Add validation, tests, and user-facing documentation updates.

Important note:

- the existing `primary_*` manifest fields remain as the ad-hoc tracking fields
  during this implementation
- their later rename to `adhoc_*` is intentionally deferred and must not be
  folded into this rollout


## Work Packages

### WP-01: Workspace Series Registry And Manifest Models

Introduce the new workspace-level `experiment_series` registry and the typed
models required to support it.

Scope:

- extend the workspace manifest model with:
  - `experiment_series`
  - `ExperimentSeriesEntry`
  - `ExperimentSeriesGeneratedArtifacts`
  - `ExperimentSeriesRegistry`
- validate:
  - unique series IDs
  - unique series paths
  - workspace-relative paths
  - paths under `series/`
  - `experiment.yaml` filename requirement
- keep ad-hoc tracking fields unchanged for now:
  - `primary_results`
  - `primary_comparisons`
- define the ownership rule:
  - ad-hoc tracking stays top-level
  - series tracking lives only under `experiment_series.entries[*].generated`

Primary files:

- `src/axis/framework/workspaces/types.py`
- `src/axis/framework/workspaces/validation.py`


### WP-02: Series Resolution And Path Helpers

Replace the singleton root-series discovery model with manifest-driven
series resolution and centralize series-local path derivation.

Scope:

- resolve a series by `series_id` from `workspace.yaml`
- load the registered `series/<series-id>/experiment.yaml`
- add helper(s) to derive:
  - series root
  - series manifest path
  - series `results/`
  - series `measurements/`
  - series `comparisons/`
  - series `notes.md`
- fail clearly for:
  - missing `experiment_series`
  - unknown `series_id`
  - missing registered file
  - invalid series manifest

Primary files:

- `src/axis/framework/workspaces/experiment_series.py`
- `src/axis/framework/workspaces/resolution.py` or a new
  `src/axis/framework/workspaces/series_paths.py`


### WP-03: Root-Aware Execution, Comparison, And Measurement Services

Make the existing workspace execution stack root-aware so that declarative
series execution can run entirely inside a selected series directory.

Scope:

- parameterize result repository roots
- parameterize measurement roots
- parameterize comparison output roots
- keep ad-hoc workspace behavior unchanged
- ensure series mode writes only to:
  - `series/<series-id>/results/`
  - `series/<series-id>/measurements/`
  - `series/<series-id>/comparisons/`

Primary files:

- `src/axis/framework/workspaces/execute.py`
- `src/axis/framework/workspaces/compare.py`
- `src/axis/framework/workspaces/services/run_service.py`
- `src/axis/framework/workspaces/services/measurement_service.py`
- `src/axis/framework/workspaces/services/compare_service.py`


### WP-04: Series Execution Service And Series-Owned Manifest Tracking

Upgrade the series orchestration layer so it runs one selected series and
records all generated artifacts under the owning series entry in the workspace
manifest.

Scope:

- require `series_id` in the service API
- resolve the selected series entry and local roots
- execute enabled experiments in declared order
- write aggregate outputs and notes into the series directory
- update:
  - `experiment_series.entries[*].generated.results`
  - `experiment_series.entries[*].generated.comparisons`
  - `experiment_series.entries[*].generated.measurement_runs`
- ensure series outputs do not leak into:
  - `primary_results`
  - `primary_comparisons`

Primary files:

- `src/axis/framework/workspaces/services/experiment_series_service.py`
- `src/axis/framework/workspaces/series_reporting.py`
- `src/axis/framework/workspaces/series_notes.py`
- manifest sync / mutator helpers as needed


### WP-05: `run-series` CLI Redesign

Expose the new multi-series execution model through the CLI with explicit
selection semantics.

Scope:

- require:
  - `axis workspaces run-series <workspace> --series <series-id>`
- reject omitted `--series` with an expressive error
- keep existing flags where still applicable:
  - `--override-guard`
  - `--update-notes`
- ensure text and JSON output identify the selected series
- include series-local output paths in JSON results

Primary files:

- `src/axis/framework/cli/parser.py`
- `src/axis/framework/cli/dispatch.py`
- `src/axis/framework/cli/commands/workspaces.py`


### WP-06: Series-Aware Reset Plan And Confirmation Flow

Redesign workspace reset from an immediate destructive action into a two-step,
series-aware cleanup flow.

Scope:

- add a reset planning step that enumerates:
  - workspace-global generated roots
  - series-local generated roots for every registered series
  - manifest fields to be cleared
- render that plan in text and JSON
- ask for confirmation unless `--force` is supplied
- with `--force`, execute immediately
- preserve authored files such as:
  - `workspace.yaml`
  - workspace-root `notes.md`
  - `series/<series-id>/experiment.yaml`
  - `series/<series-id>/notes.md`
- clear manifest tracking in both scopes:
  - top-level ad-hoc tracking
  - `experiment_series.entries[*].generated.*`

Primary files:

- `src/axis/framework/workspaces/services/workflow_service.py`
- `src/axis/framework/workspaces/manifest_mutator.py`
- `src/axis/framework/cli/commands/workspaces.py`
- `src/axis/framework/cli/parser.py`


### WP-07: Validation, Integration Tests, And Regression Hardening

Add the test coverage needed to stabilize the new model and prevent accidental
cross-scope regressions.

Scope:

- workspace manifest validation for registered series
- series loader failure cases
- explicit `--series` CLI enforcement
- series-local routing of:
  - results
  - comparisons
  - measurements
  - notes
- manifest tracking written under `experiment_series.entries[*].generated`
- verification that ad-hoc tracking remains in `primary_*` for now
- reset preview, cancellation, and `--force`
- reset preservation of authored files

Primary areas:

- `tests/framework/workspaces/test_validation.py`
- `tests/framework/workspaces/test_integration.py`
- `tests/framework/test_workspace_services.py`
- CLI parser / dispatch tests


### WP-08: Manual And Internal Documentation Update

Update public and internal documentation to reflect the new canonical
multi-series model.

Scope:

- document the `experiment_series` registry in `workspace.yaml`
- document `series/<series-id>/experiment.yaml`
- document required `--series <series-id>`
- document series-local artifact roots
- document series-aware `reset` preview and `--force`
- document that `primary_*` still means ad-hoc tracking for now

Primary files:

- `docs/manuals/workspace-manual.md`
- `docs/manuals/experiment-series-manual.md`
- `docs/manuals/cli-manual.md`
- `docs/manuals/axis-overview.md`
- `docs-internal/ideas/multiple-exp-series/*.md` as needed


## Suggested Execution Order

The recommended order is:

1. `WP-01`
2. `WP-02`
3. `WP-03`
4. `WP-04`
5. `WP-05`
6. `WP-06`
7. `WP-07`
8. `WP-08`


## Suggested Dependency Logic

- `WP-01` must land first because all later work depends on the canonical
  manifest structure.
- `WP-02` depends on `WP-01` because series resolution requires the registry.
- `WP-03` depends on `WP-02` because root-aware services need centralized
  series path resolution.
- `WP-04` depends on `WP-01`, `WP-02`, and `WP-03` because it orchestrates the
  complete series execution stack.
- `WP-05` depends on `WP-04` because the CLI should call the canonical
  service-layer implementation.
- `WP-06` depends on `WP-01` and should preferably follow `WP-04`/`WP-05`
  because reset must understand the final artifact ownership model.
- `WP-07` depends on all previous packages.
- `WP-08` should follow once behavior is stable enough to document precisely.


## Verification Goal

After completing all work packages:

1. A workspace can register multiple named series in `workspace.yaml`.
2. `axis workspaces run-series <workspace> --series <id>` executes only the
   selected series.
3. Series-generated artifacts live entirely under the selected series
   directory.
4. Series-generated manifest tracking is stored under the owning
   `experiment_series.entries[*].generated` block.
5. Ad-hoc workspace activity still uses the workspace-global roots and the
   current `primary_*` tracking fields.
6. `axis workspaces reset <workspace>` previews both ad-hoc and series-local
   generated deletions before acting.
7. `axis workspaces reset <workspace> --force` performs the same reset without
   prompting.


## Future Note

The later rename from `primary_*` to `adhoc_*` is intentionally outside the
scope of these work packages.

That rename should happen only after the multi-series implementation is in
place and operationally stable.
