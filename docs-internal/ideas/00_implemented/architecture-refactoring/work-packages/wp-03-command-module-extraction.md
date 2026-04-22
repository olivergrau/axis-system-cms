# WP-03 Command Module Extraction

## Goal

Extract command implementations from the central CLI into grouped command
modules.

## Why This Package Exists

After the CLI package seam exists, the next major scaling step is to reduce the
operational and rendering density of the current command implementation.

The system already has natural command groupings:

- experiments
- runs
- compare
- visualize
- workspaces

## Scope

### Extract grouped command modules

Introduce command modules under:

- `src/axis/framework/cli/commands/`

Recommended first groups:

- `experiments.py`
- `runs.py`
- `compare.py`
- `visualize.py`
- `workspaces.py`

### Move rendering with command handling

Text and JSON rendering should move with the corresponding command handler.

### Keep business logic out of command modules

Command modules may:

- interpret arguments
- invoke services/helpers
- render output

They must not absorb:

- workflow business rules
- registry mutation
- manifest mutation semantics

## Files To Change

- new CLI command modules
- CLI dispatch layer

## Deliverables

- grouped command modules exist
- central CLI dispatch shrinks materially
- rendering is no longer concentrated in the old CLI file

## Non-Goals

- service extraction belongs later
- registry/catalog redesign belongs elsewhere

## Tests

Update/add tests covering:

- representative commands in each command group
- text/json output behavior preservation

Likely targets:

- `tests/framework/test_cli.py`

## Acceptance Criteria

- command implementations are grouped by functional area
- command modules remain thin and non-business-logic-heavy
