# WP-01 Persisted Output Semantics

## Goal

Introduce explicit persisted experiment-output semantics so the framework no
longer has to infer key output meaning from weak conventions.

This package establishes the persistence foundation for the entire refactoring.

## Why This Package Exists

Current persisted experiment artifacts already distinguish enough to roughly
tell `single_run` and `ofat` apart, but key semantics are not explicit.

Current code:

- `ExperimentMetadata` in `src/axis/framework/persistence.py` stores:
  - `experiment_id`
  - `created_at`
  - `experiment_type`
  - `system_type`
- `RunMetadata` in `src/axis/framework/persistence.py` stores:
  - `run_id`
  - `experiment_id`
  - `variation_description`
  - `created_at`
  - `base_seed`

Missing today:

- explicit `output_form`
- explicit `primary_run_id`
- explicit `baseline_run_id`
- explicit sweep variation metadata robust enough for normalized output loading

## Scope

### Extend `ExperimentMetadata`

Add:

- `output_form`
- `primary_run_id: str | None`
- `baseline_run_id: str | None`

### Extend `RunMetadata`

For sweep-capable persistence, add:

- `variation_index: int | None`
- `variation_value: Any | None`
- optional `is_baseline: bool | None`

### Update experiment finalization

In `src/axis/framework/experiment.py`:

- assign `output_form = point` for `single_run`
- assign `output_form = sweep` for `ofat`
- persist `primary_run_id` for point experiments
- persist `baseline_run_id` for sweep experiments
- persist sweep run metadata for each OFAT run

### Add validation

Persisted combinations must be validated:

- `single_run <-> point`
- `ofat <-> sweep`

Invalid combinations must raise explicit errors.

## Files To Change

- `src/axis/framework/persistence.py`
- `src/axis/framework/experiment.py`

## Deliverables

- extended metadata models
- adjusted metadata write paths in experiment execution
- consistency validation for experiment-type/output-form pairing

## Non-Goals

- no new output abstraction module yet
- no CLI changes yet
- no Workspace manifest changes yet

## Tests

Update existing tests and create new tests where needed:

- `tests/framework/test_persistence.py`
- `tests/framework/test_experiment.py`
- create a new persistence-focused executor test file if needed
- `tests/framework/test_ofat_integration.py`

Cover at least:

- single-run persistence includes `output_form=point`
- OFAT persistence includes `output_form=sweep`
- point experiments persist `primary_run_id`
- sweep experiments persist `baseline_run_id`
- sweep runs persist variation metadata

## Acceptance Criteria

- completed experiments persist explicit output semantics
- sweep semantics are reconstructible from persisted artifacts alone
- invalid persisted pairings are rejected explicitly
