# WP-06 Output-Aware Comparison Resolution

## Goal

Refactor workspace comparison entry logic so it resolves Experiment Outputs
first and only then performs operational run selection.

## Why This Package Exists

Current `src/axis/framework/workspaces/compare_resolution.py`
is still built around:

- experiment IDs
- raw run IDs
- manifest ordering
- direct experiment metadata checks

It does not yet understand point vs sweep outputs explicitly.

## Scope

### Resolve outputs first

Refactor comparison planning so it:

1. identifies candidate experiment outputs
2. loads them via `experiment_output.py`
3. validates supported combinations
4. selects concrete runs only after output validation

### Support only `point vs point`

In v1:

- `point vs point` must work

All other combinations must fail explicitly:

- `point vs sweep`
- `sweep vs point`
- `sweep vs sweep`

### Update comparison execution entry

`src/axis/framework/workspaces/compare.py`
should continue to call the existing run comparison engine for supported
point-vs-point cases.

This package applies to the output-aware workspace/high-level comparison entry
layer.

It does not require restricting the existing direct `axis compare` CLI when the
user already provides explicit experiment/run coordinates.

## Files To Change

- `src/axis/framework/workspaces/compare_resolution.py`
- `src/axis/framework/workspaces/compare.py`
- new dependency on:
  - `src/axis/framework/experiment_output.py`

## Deliverables

- output-aware comparison planning
- explicit rejection of unsupported sweep-related compare cases

## Tests

Update/add tests in:

- `tests/framework/workspaces/test_integration.py`
- comparison-specific tests under:
  - `tests/framework/comparison/`
    only if new helpers are introduced there

Cover:

- `point vs point` still works
- all sweep-involved combinations fail clearly

## Acceptance Criteria

- compare entry resolution no longer starts from raw run-path assumptions
- unsupported output combinations are rejected with explicit errors
