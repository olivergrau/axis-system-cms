# WP-02 Core Experiment Output Module

## Goal

Introduce the framework-level normalized output abstraction in:

- `src/axis/framework/experiment_output.py`

This module becomes the canonical loader and validator for completed experiment
outputs.

## Why This Package Exists

Current framework consumers read raw artifacts directly:

- CLI inspection loads metadata/config/summary separately
- Workspace code assumes run-path-shaped results
- compare/visualize entry logic starts from experiment IDs and raw run lists

There is no single canonical model for:

- point experiment output
- sweep experiment output

## Scope

### Define output form enum

Introduce:

- `ExperimentOutputForm`
  - `POINT`
  - `SWEEP`

### Define normalized models

Introduce:

- `ExperimentOutput`
- `PointExperimentOutput`
- `SweepExperimentOutput`

The fields must follow the engineering spec.

### Implement repository-based loader

Add a loader such as:

- `load_experiment_output(repo, experiment_id)`

It should:

- load config, metadata, summary
- inspect run IDs
- validate persisted semantics
- return a normalized point or sweep output object

### Explicit validation

The loader must fail clearly if:

- persisted `output_form` is missing
- `experiment_type` and `output_form` disagree
- point output lacks `primary_run_id`
- sweep output lacks `baseline_run_id`
- sweep variation ordering cannot be reconstructed

## Files To Add / Change

- add:
  - `src/axis/framework/experiment_output.py`

Optional small changes:

- `src/axis/framework/__init__.py`
  if re-exports are desired

## Deliverables

- canonical output form enum
- canonical normalized output models
- repository-backed loader
- strict output validation

## Non-Goals

- no CLI migration yet
- no Workspace migration yet

## Tests

Add new tests:

- create `tests/framework/test_experiment_output.py`

Cover:

- loading point output
- loading sweep output
- rejecting missing or inconsistent semantics
- validating sweep ordering recovery

## Acceptance Criteria

- any completed experiment can be loaded as a normalized Experiment Output
- point and sweep outputs are clearly distinguishable
- all required semantic fields come from persisted artifacts, not loose runtime guesses
