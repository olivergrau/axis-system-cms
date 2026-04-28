# Declarative Experiment Workflow Spec

## 1. Purpose

This specification defines a first-class **experiment series** workflow for
AXIS workspaces.

The goal is to automate a user workflow that is already stable in practice:

1. choose a configuration
2. execute a measured workspace run
3. inspect exported summaries
4. record manual interpretation
5. repeat for the next experiment

The feature should turn that manual loop into a declarative workspace-local
execution plan that:

- runs a defined sequence of experiments
- exports the existing measurement artifacts for each experiment
- produces a final cross-experiment overview
- scaffolds notes without performing scientific interpretation


## 2. Scope

### 2.1 Implemented in v1

Version 1 targets only:

- `workspace_class = investigation`
- `workspace_type = system_comparison`

If the command is invoked on any other workspace type, AXIS must fail with an
explicit guardrail error explaining that experiment series execution is only
supported for `system_comparison` in v1.

### 2.2 Deliberately Out of Scope in v1

The following are not supported in v1:

- `single_system` execution
- `system_development`
- `world_development`
- OFAT / sweep outputs inside series execution
- resume after partial failure
- automatic scientific interpretation

### 2.3 Forward Compatibility

Even though v1 only supports `system_comparison`, the schema should be designed
so that `single_system` can be added later without requiring a conceptual
rewrite.

That means:

- the experiment-series file must identify the intended workspace type
- the orchestration model should be step-based and handler-aware
- comparison-specific outputs must not be baked into the core schema in a way
  that prevents future `single_system` support


## 3. Product Position

This feature is positioned as an **experiment series** capability.

It is not:

- a generic workflow engine
- a sweep framework
- a campaign system across multiple workspaces

The main value in v1 is:

- artifact organization
- repeatable series execution
- consistent cross-experiment reporting inside one workspace

It is explicitly **not** intended to compare across multiple workspaces.


## 4. Core Design

### 4.1 Two Configuration Layers

The design is split into two layers:

1. `workspace.yaml`
   This remains the home of stable workspace policy, including
   `measurement_workflow`.

2. `experiment.yaml`
   This becomes the home of the concrete experiment series definition for one
   workspace.

This separation is required because the series definition is not just another
workspace preference. It is a bounded, explicit research plan.

### 4.2 Discovery Model

The experiment series file lives in the workspace root as:

```text
experiment.yaml
```

The workspace manifest does not need to point to it explicitly in v1.

Resolution rule:

- if `axis workspaces run-series <workspace>` is invoked, AXIS looks for
  `<workspace>/experiment.yaml`
- if the file is missing, the command fails with a clear error message


## 5. Command Surface

### 5.1 New Command

AXIS introduces:

```bash
axis workspaces run-series <workspace>
```

Example:

```bash
axis workspaces run-series .
```

Optional flag:

```bash
axis workspaces run-series . --update-notes
```

### 5.2 Command Behavior

The command must:

1. load and validate `workspace.yaml`
2. enforce workspace-type guardrails
3. load and validate `experiment.yaml`
4. execute all enabled experiments in declared order
5. export per-experiment measurement artifacts
6. generate aggregate outputs for the full series
7. leave `notes.md` untouched by default
8. overwrite `notes.md` only when `--update-notes` is specified

### 5.3 Failure Behavior

The series is fail-fast.

If any experiment step fails, including:

- config resolution
- run execution
- comparison
- summary export
- aggregate generation

then:

- the full series command fails
- later experiments are not executed
- no resume support is provided in v1


## 6. Workspace Guardrails

### 6.1 v1 Guardrail

If `run-series` is called on a workspace that is not `system_comparison`,
AXIS must fail with a message in this spirit:

> `axis workspaces run-series` currently supports only
> `system_comparison` workspaces. This workspace is `<actual_type>`.

### 6.2 Deferred `single_system`

`single_system` semantics are intentionally deferred from implementation, but
reserved conceptually:

- the first recorded point experiment would serve as the baseline
- the latest point experiment would serve as the candidate
- sweep outputs would be excluded from auto-resolution
- comparison would remain point-vs-point only

This future behavior should inform schema design, but must not expand the v1
runtime scope.


## 7. `experiment.yaml` Schema

### 7.1 Top-Level Shape

The file defines one ordered experiment series for one workspace.

Required top-level fields:

```yaml
version: 1
workflow_type: experiment_series
workspace_type: system_comparison
experiments: []
```

Optional top-level fields:

- `title`
- `description`
- `defaults`
- `notes`

### 7.2 Required Semantics

- `workspace_type` must match the actual workspace type
- `experiments` must be an ordered non-empty list
- experiment IDs must be unique and immutable within the file
- labels are user-facing and may differ from IDs

### 7.3 Proposed Schema

```yaml
version: 1
workflow_type: experiment_series
workspace_type: system_comparison
title: System C+W predictive modulation series
description: Iterative candidate-side comparison against system A+W

defaults:
  export:
    comparison_summary: true
    candidate_run_summary: true
    reference_run_summary: false
  notes:
    scaffold_notes: true
  labels:
    measurement_label_pattern: "{experiment_id}"

experiments:
  - id: exp_01
    label: config2
    title: Weak Symmetric Prediction
    enabled: true
    hypothesis:
      - Prediction should affect behavior slightly
      - Curiosity should be more sensitive than hunger
    notes: Small symmetric predictive influence
    candidate_config_delta:
      system:
        prediction:
          hunger:
            positive_sensitivity: 0.4
            negative_sensitivity: 0.6
          curiosity:
            positive_sensitivity: 0.4
            negative_sensitivity: 0.6

  - id: exp_02
    label: config3
    title: Curiosity-Dominant Prediction
    enabled: true
    hypothesis:
      - Prediction should filter exploration more selectively
    candidate_config_delta:
      system:
        prediction:
          curiosity:
            positive_sensitivity: 0.7
            negative_sensitivity: 0.9
```


## 8. Experiment Record Semantics

### 8.1 Required Fields Per Experiment

Each experiment must define:

- `id`
- `title`
- `enabled`
- `candidate_config_delta`

### 8.2 Optional Fields Per Experiment

- `label`
- `notes`
- `hypothesis`

### 8.3 IDs vs Labels

Two identifiers are required conceptually:

- `id`
  stable, unique, machine-oriented
- `label`
  optional human-facing identifier used for exported file naming

If `label` is absent, AXIS uses `id` for export labeling.


## 9. Config Resolution Model

### 9.1 Resolution Rule

Each experiment is resolved from a fixed baseline, never from the previous
experiment.

For `system_comparison` in v1:

- the reference config comes from `workspace.yaml`
- the candidate config also starts from the workspace primary config for the
  candidate role
- the experiment applies a candidate-side delta to that candidate base config

There is no inheritance from previous experiments.

### 9.2 Delta Semantics

The only supported experiment configuration mode in v1 is:

- inline deep-merge deltas

Not supported in v1:

- full config file references inside `experiment.yaml`
- mixed delta/file-reference mode

### 9.3 Temporary Config Materialization

AXIS must not mutate the workspace’s original primary config files.

Instead it must:

1. resolve the full experiment config in memory
2. materialize temporary configs for execution
3. run the experiment using those temporary configs
4. persist enough metadata to reconstruct the fully resolved config later

This preserves manual-mode configs as stable user assets.


## 10. Execution Semantics

### 10.1 Enabled/Disabled Experiments

The user controls execution inclusion through per-experiment flags in
`experiment.yaml`.

Rule:

- all experiments with `enabled: true` are executed
- experiments with `enabled: false` are skipped

No separate CLI subset/range syntax is required in v1.

### 10.2 Per-Experiment Internal Flow

For each enabled experiment in a `system_comparison` workspace, AXIS must:

1. resolve temporary configs
2. execute the workspace run
3. execute the workspace compare
4. export the comparison summary
5. export the candidate run summary
6. record experiment metadata in the series outputs

Implementation requirement:

- reuse the existing `measure` orchestration where possible
- do not duplicate run/compare/export semantics in a second independent code
  path

### 10.3 Failure Policy

Any failure aborts the series immediately.

No experiment after the failure point is executed.

No resume support is provided.


## 11. Per-Experiment Output Model

### 11.1 Measurement Folders

Each experiment produces one measurement folder under the workspace
measurement root.

The folder naming should reuse the existing numbering logic from
`measurement_workflow`, for example:

```text
measurements/experiment_0/
measurements/experiment_1/
measurements/experiment_2/
```

### 11.2 File Naming

Per-experiment log file names should reuse existing `measurement_workflow`
patterns when possible.

The series engine may pass the experiment `label` to `measure` via the same
label override mechanism already used by the CLI.

### 11.3 Persisted Metadata

Each experiment execution must record machine-readable metadata that links:

- experiment ID
- label
- title
- hypothesis
- resolved config delta
- realized measurement folder
- produced result IDs
- produced comparison IDs


## 12. Aggregate Outputs

### 12.1 Required Aggregate Outputs

A successful series must produce:

- a cross-experiment Markdown overview
- a machine-readable JSON series summary
- a per-experiment metrics table spanning all experiments

Recommended file names:

- `measurements/series-summary.md`
- `measurements/series-summary.json`
- `measurements/series-metrics.csv`

### 12.2 Minimum Success Condition

The series is only considered successful if:

- all generic metrics are computed for every experiment
- all system-specific metrics are computed for every experiment
- all required aggregate outputs are rendered successfully

If any required metric computation fails, the series fails.

### 12.3 Primary Table View

The most important aggregate table in v1 is:

- one per-experiment metric table across the whole series

This table should let the user compare all configs at a glance.

Best/worst rankings and anomaly summaries may be added later, but are not the
primary v1 reporting goal.


## 13. Comparison Lenses in the Final Overview

For `system_comparison`, the final overview should include three comparison
lenses:

1. previous experiment
   progression view
2. baseline experiment
   campaign anchor view
3. workspace reference system
   scientific comparison view

This means the final overview should support all of the following:

- how experiment `n` changed relative to experiment `n-1`
- how experiment `n` changed relative to the series baseline
- how experiment `n` candidate compares to its reference system run

These lenses should be clearly separated in the generated Markdown rather than
mixed into one ambiguous comparison narrative.


## 14. Notes and Reporting Boundaries

### 14.1 Interpretation Boundary

AXIS must stay at **pure reporting** in v1.

That means:

- metric reporting is allowed
- factual delta reporting is allowed
- scientific interpretation is not generated automatically

Examples of allowed generated language:

- `death_rate decreased from 0.28 to 0.22`
- `behavioral_prediction_impact_rate increased from 0.14 to 0.20`

Examples of disallowed automatic claims:

- `prediction improves exploration quality`
- `curiosity became too permissive`
- `the system entered an exploitation-biased regime`

Those remain the user’s responsibility in `notes.md`.

### 14.2 Notes Scaffold

AXIS should support notes scaffolding.

Desired behavior:

- AXIS can generate a notes scaffold for the experiment series
- experiment hypotheses should be copied into the scaffold
- the scaffold should help the user fill in observations and interpretation

### 14.3 Notes Update Guardrail

Because `notes.md` is user-edited, AXIS should not overwrite it silently.

Required v1 behavior:

- default behavior: `notes.md` remains untouched
- if `--update-notes` is specified, AXIS overwrites `notes.md` with a newly
  generated scaffold
- if `--update-notes` is not specified, AXIS must not modify `notes.md`

This keeps the command safe for normal use while still allowing explicit
regeneration when the user wants a fresh scaffold.


## 15. Architecture

### 15.1 Required Components

The implementation should introduce:

- a typed experiment-series model
- a loader and validator for `experiment.yaml`
- a `WorkspaceExperimentSeriesService`
- series-aware aggregate renderers

### 15.2 Reuse Requirements

The new series feature must reuse existing primitives:

- workspace loading and validation
- `measure`
- summary rendering
- persisted result/comparison resolution

The feature must not introduce a second independent definition of:

- how runs are executed
- how comparisons are executed
- how measurement logs are exported


## 16. Validation Rules

At minimum, validation must enforce:

- `experiment.yaml` exists when the command is called
- `version` is supported
- `workflow_type` is `experiment_series`
- `workspace_type` matches the real workspace
- experiment IDs are unique
- at least one experiment is enabled
- every experiment provides a valid delta object
- no unsupported workspace type is executed


## 17. Future Extensions

The following are plausible later extensions, but not part of v1:

- runtime support for `single_system`
- optional file-reference config mode
- resume from partial failure
- richer JSON output schemas
- anomaly tables
- ranking views
- optional baseline selection beyond “first enabled experiment”
- non-interactive notes overwrite policy flags


## 18. Recommended v1 Summary

Version 1 should therefore be:

- a workspace-root `experiment.yaml`
- a new `axis workspaces run-series` command
- implemented only for `system_comparison`
- delta-based against fixed workspace baseline configs
- fail-fast with no resume
- Markdown-first plus JSON support
- notes-scaffolding capable
- pure-reporting only, not automatic interpretation

This keeps the feature aligned with the current AXIS architecture while making
the user’s real experiment workflow reproducible and much less manual.
