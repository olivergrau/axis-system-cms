# WP-05 Workspace Execution Sync Update

## Goal

Update workspace run synchronization so executed results are recorded as
experiment outputs rather than direct run paths.

## Why This Package Exists

Current `src/axis/framework/workspaces/execute.py`
already writes artifacts into `workspace/results/`.

But `src/axis/framework/workspaces/sync.py`
still records run-shaped result entries.

That is incompatible with the new experiment-output identity model.

## Scope

### Update the workspace run manifest synchronization logic

Change it so that after execution it writes structured experiment-output result
entries using:

- experiment-root path
- output-form metadata
- role
- system type
- created timestamp

### Use Experiment Output data

The sync layer should preferably load the normalized Experiment Output rather
than reconstructing values manually.

### Keep development fields coherent

For `system_development`, development-specific fields must remain consistent,
but they should align with experiment-output identity.

If those fields still need run-level operational semantics later, they should
store that explicitly rather than encoding it through run-shaped primary result
paths.

## Files To Change

- `src/axis/framework/workspaces/sync.py`
- potentially:
  - `src/axis/framework/workspaces/execute.py`

## Deliverables

- experiment-root-based manifest sync
- structured result entry creation
- development manifest fields kept coherent

## Tests

Update/add tests in:

- `tests/framework/workspaces/test_integration.py`
- additional sync-focused tests if needed

Cover:

- workspace run writes experiment-root entries
- entry metadata matches persisted output semantics
- development-specific fields remain valid

## Acceptance Criteria

- after `axis workspaces run`, `workspace.yaml` contains experiment-output-centric result entries
- no newly written manifest entry points to `runs/<run-id>` as the primary identity
