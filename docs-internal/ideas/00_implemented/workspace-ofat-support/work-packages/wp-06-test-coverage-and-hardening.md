# WP-06 Test Coverage and Hardening

## Goal

Add focused regression coverage so bounded Workspace OFAT support remains
stable.

## Why This Package Exists

This feature changes a previously strict global rule:

- Workspaces were `single_run`-only

That means both acceptance and rejection behavior need strong tests:

- OFAT allowed only in one workspace type
- mixed point/sweep histories behave predictably
- sweep inspection is explicit

## Scope

### Validation coverage

Cover:

- valid `single_system + ofat`
- invalid `system_comparison + ofat`
- invalid `system_development + ofat`

### Execution and sync coverage

Cover:

- OFAT execution inside workspace-owned mode
- sweep result entry creation
- experiment-root identity under `results/<experiment-id>`

### Sweep inspection coverage

Cover:

- `sweep-result` default newest-sweep selection
- `sweep-result --experiment <eid>`
- explicit failure when selected output is a point

### Compare behavior coverage

Cover:

- mixed point/sweep histories in `single_system`
- point-only selection
- sweep rejection in workspace compare

### Visualization compatibility coverage

Keep explicit sweep visualization behavior covered:

- sweep requires explicit `--run`
- valid explicit run selection succeeds

## Files To Change

Primary test files:

- `tests/framework/workspaces/test_validation.py`
- `tests/framework/workspaces/test_integration.py`
- `tests/framework/test_cli.py`

Potential auxiliary test updates:

- `tests/framework/test_experiment_output.py`

## Deliverables

- updated validation tests
- new or expanded integration coverage for OFAT workspace flows
- CLI coverage for `sweep-result`

## Non-Goals

- no new product behavior beyond what earlier packages define

## Acceptance Criteria

- the bounded OFAT support contract is covered end to end
- unsupported workspace types remain guarded
- mixed point/sweep histories no longer rely on untested assumptions
