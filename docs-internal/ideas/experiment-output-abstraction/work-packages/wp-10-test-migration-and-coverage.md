# WP-10 Test Migration and Coverage

## Goal

Add the missing tests and migrate existing ones so the Experiment Output
refactor is protected end to end.

## Why This Package Exists

The refactor touches:

- persistence
- experiment execution
- CLI inspection
- workspace manifests
- compare resolution
- visualization resolution

Without targeted coverage, regressions will be easy to introduce.

## Scope

### New core tests

Add tests for:

- point output loading
- sweep output loading
- invalid output semantics
- sweep variation reconstruction

### CLI tests

Add/update:

- experiment inspection behavior
- run inspection behavior

### Workspace tests

Add/update:

- structured result entry sync
- output-aware summary rendering
- point-vs-point compare success
- sweep compare failure
- sweep visualize failure without explicit selection

## Relevant Test Areas

- `tests/framework/test_persistence.py`
- `tests/framework/test_experiment.py`
- create a new `tests/framework/test_experiment_output.py`
- `tests/framework/test_cli.py`
- `tests/framework/test_ofat_integration.py`
- `tests/framework/workspaces/test_integration.py`
- `tests/framework/workspaces/test_summary.py`
- `tests/framework/workspaces/test_types.py`
- `tests/framework/workspaces/test_validation.py`

## Deliverables

- new output-abstraction core tests
- migrated CLI and Workspace tests
- explicit failure-case tests for unsupported sweep operations

## Acceptance Criteria

- all major refactor surfaces are covered by targeted tests
- unsupported sweep cases are locked down by tests, not just by intention
