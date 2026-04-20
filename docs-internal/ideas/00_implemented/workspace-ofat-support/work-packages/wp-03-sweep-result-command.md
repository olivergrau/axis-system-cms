# WP-03 Sweep Result Command

## Goal

Add a first-class Workspace command for inspecting sweep outputs:

- `axis workspaces sweep-result <workspace>`

## Why This Package Exists

Workspace `show` is intentionally management-only, and Workspace `compare` is
reserved for comparisons.

Sweep outputs therefore need their own inspection entrypoint.

The current codebase has:

- no dedicated sweep-result command
- no focused workspace module for resolving and rendering sweep outputs

## Scope

### Add a dedicated workspace module

Introduce a focused helper module, preferably:

- `src/axis/framework/workspaces/sweep_result.py`

Responsibilities:

- load workspace manifest
- filter `primary_results` to sweep outputs only
- resolve the target sweep
- render sweep result information for text and JSON

### Add CLI integration

Expose:

- `axis workspaces sweep-result <workspace>`

Supported selection behavior:

- default:
  - newest sweep output in the workspace
- explicit:
  - `--experiment <experiment-id>`

### Reject non-sweep targets explicitly

If the selected output is a point output, fail clearly.

If no sweep outputs exist, fail clearly.

### Render minimum required sweep information

At minimum, the command must expose:

- experiment ID
- system type
- parameter path
- parameter values
- baseline run ID
- variation descriptions
- experiment summary with OFAT deltas

## Files To Change

- `src/axis/framework/cli.py`
- `src/axis/framework/workspaces/sweep_result.py` (new)

Potential dependencies:

- `src/axis/framework/experiment_output.py`
- `src/axis/framework/persistence.py`

## Deliverables

- new `sweep-result` command
- default newest-sweep selection
- explicit `--experiment` selection
- text and JSON output modes

## Non-Goals

- no sweep comparison
- no point-vs-sweep comparison
- no migration of `show` into an analysis command

## Tests

Add or update tests covering:

- `sweep-result` selects newest sweep by default
- `sweep-result --experiment <eid>` selects explicit sweep
- `sweep-result --experiment <eid>` rejects point outputs
- `sweep-result` fails when no sweep outputs exist
- JSON output includes required sweep fields

Suggested primary test target:

- `tests/framework/workspaces/test_integration.py`

## Acceptance Criteria

- sweep outputs can be inspected without using `show` or `compare`
- command behavior is explicit and non-ambiguous
- text and JSON rendering both work
