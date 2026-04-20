# WP-06 Handler Contract Stabilization

## Goal

Make the workspace handler contract explicit and remove reflection-based
behavior branching.

## Why This Package Exists

The current workspace resolution path uses runtime signature inspection to
detect whether handlers support `run_filter`.

This is a sign that the interface contract is not explicit enough for continued
growth.

The handler model itself is useful and should remain.

The contract shape is what needs refactoring.

## Scope

### Stabilize handler signatures

Shared workflow methods should have explicit, stable signatures across
implementations.

Priority target:

- add `run_filter: str | None = None` to the base
  `resolve_run_targets(...)` contract so every handler shares the same
  signature

The current base handler contract does not yet include `run_filter`; this
package adds it to the shared contract and removes the need for
`inspect.signature(...)` branching in workspace resolution.

Comparison-target resolution should also be tightened as part of the same
contract cleanup, especially:

- `resolve_comparison_targets(...)`
- the currently loose `repo: object` dependency typing in the base handler

### Remove reflection from workflow routing

Eliminate `inspect.signature(...)`-based branching in workspace resolution.

### Keep handler-based extensibility

This package should not replace the handler pattern.

It should make it more explicit and reliable.

## Files To Change

- `src/axis/framework/workspaces/handler.py`
- `src/axis/framework/workspaces/resolution.py`
- workspace handler implementations

## Deliverables

- explicit handler contract
- no runtime signature probing
- cleaner run-target resolution path

## Non-Goals

- no workspace service layer yet

## Tests

Add/update tests covering:

- all workspace handlers conform to the same contract
- `run_filter` behavior remains correct where supported
- comparison-target resolution remains compatible with the tightened contract

## Acceptance Criteria

- workspace handlers are extension points with explicit contracts rather than
  reflective behavior
