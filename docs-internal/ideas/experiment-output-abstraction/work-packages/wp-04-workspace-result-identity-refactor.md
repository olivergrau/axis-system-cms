# WP-04 Workspace Result Identity Refactor

## Goal

Refactor Workspace result identity from run-path-centric to
experiment-output-centric.

## Why This Package Exists

Current Workspace result semantics are still transitional:

- `WorkspaceManifest` in `src/axis/framework/workspaces/types.py`
  has `primary_results: list[str | dict] | None`
- `src/axis/framework/workspaces/sync.py`
  currently writes entries whose `path` is still run-shaped:
  - `results/<experiment-id>/runs/<run-id>`
- `src/axis/framework/workspaces/summary.py`
  still assumes artifact entries can be interpreted directly from those paths

This blocks clean output abstraction.

## Scope

### Introduce typed workspace result entries

Refactor Workspace manifest support toward structured entries for `primary_results`.

At minimum, each entry should carry:

- `path`
- `output_form`
- `system_type`
- `role`
- `created_at`

Recommended:

- `primary_run_id`
- `baseline_run_id`

### Change identity path

Primary result identity must move to:

- `results/<experiment-id>`

and stop using:

- `results/<experiment-id>/runs/<run-id>`

### Update summary rendering

`summary.py` must render the new structured entries and existence checks
against experiment roots.

## Files To Change

- `src/axis/framework/workspaces/types.py`
- `src/axis/framework/workspaces/summary.py`

Likely helper updates:

- `src/axis/framework/workspaces/validation.py`

## Deliverables

- typed primary result entry model
- experiment-root-based result identity
- summary aware of structured result entries

## Non-Goals

- sync logic itself may remain for WP-05
- compare/visualize migration belongs later

## Tests

Update/add tests in:

- `tests/framework/workspaces/test_types.py`
- `tests/framework/workspaces/test_summary.py`

## Acceptance Criteria

- Workspace manifests can represent experiment outputs directly
- run-path-centric `primary_results` assumptions are removed from the typed model
