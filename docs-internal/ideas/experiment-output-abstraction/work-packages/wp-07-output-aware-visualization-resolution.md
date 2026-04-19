# WP-07 Output-Aware Visualization Resolution

## Goal

Refactor workspace visualization resolution so it becomes output-aware and no
longer relies on implicit run defaults except where the output form defines one
unambiguously.

## Why This Package Exists

Current `src/axis/framework/workspaces/visualization.py`
works directly from workspace experiments and manifest role hints.

It assumes a natural run default by taking the first run found.

That is acceptable for point outputs but not for sweep outputs.

## Scope

### Resolve output first

Refactor visualization target resolution so it:

1. resolves the experiment output
2. checks the output form
3. selects a run accordingly

### Point behavior

For point outputs:

- use `primary_run_id` as the default run

### Sweep behavior

For sweep outputs:

- require explicit run or variation selection in v1
- do not silently default to baseline or first run

If no explicit selection exists, fail clearly.

## Files To Change

- `src/axis/framework/workspaces/visualization.py`
- `src/axis/framework/cli.py`

Optional CLI enhancement:

- add explicit run selection support in workspace visualization if needed

## Deliverables

- output-aware visualization resolution
- explicit sweep failure without explicit selection

## Tests

Update/add tests in:

- `tests/framework/workspaces/test_integration.py`

Cover:

- point output resolves cleanly
- sweep output without explicit selection fails clearly

## Acceptance Criteria

- workspace visualization no longer relies on implicit first-run selection for all output forms
- sweep ambiguity is surfaced as an error, not silently guessed away
