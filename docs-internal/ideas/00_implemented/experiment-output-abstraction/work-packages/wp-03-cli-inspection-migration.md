# WP-03 CLI Inspection Migration

## Goal

Refactor experiment inspection commands so they render normalized Experiment
Outputs instead of assembling raw artifact views ad hoc.

## Why This Package Exists

Current CLI inspection in `src/axis/framework/cli.py`:

- `_cmd_experiments_show(...)`
- `_cmd_runs_list(...)`
- `_cmd_runs_show(...)`

currently loads raw metadata/config/summary directly and prints low-level
structure.

This bypasses the new output abstraction entirely.

## Scope

### Update `axis experiments show`

Refactor `_cmd_experiments_show(...)` to:

1. load the Experiment Output
2. render output-form-aware information

For point outputs, show at least:

- `output_form`
- `primary_run_id`

For sweep outputs, show at least:

- `output_form`
- `parameter_path`
- `parameter_values`
- `baseline_run_id`

### Update `axis experiments list`

If there is a dedicated list command path in `src/axis/framework/cli.py`,
surface:

- `output_form`
- `num_runs`

### Update `axis runs show`

Keep it run-oriented, but also display:

- enclosing `output_form`
- variation metadata for sweep runs

## Files To Change

- `src/axis/framework/cli.py`
- new dependency on:
  - `src/axis/framework/experiment_output.py`

## Deliverables

- output-aware experiment inspection
- run inspection enriched with enclosing output semantics

## Non-Goals

- no Workspace changes yet
- no compare refactor yet

## Tests

Update/add tests in:

- `tests/framework/test_cli.py`

Cover:

- `experiments show` for point outputs
- `experiments show` for sweep outputs
- `runs show` includes output-form info

## Acceptance Criteria

- CLI experiment inspection no longer depends on raw implicit knowledge of single_run vs OFAT
- output-aware fields are visible in text and JSON modes where appropriate
