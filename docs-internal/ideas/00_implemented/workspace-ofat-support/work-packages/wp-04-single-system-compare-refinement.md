# WP-04 Single-System Compare Refinement

## Goal

Refine `single_system` comparison resolution so mixed point/sweep histories are
handled correctly without enabling sweep comparison.

## Why This Package Exists

Current `single_system` comparison still resolves by manifest order:

- `src/axis/framework/workspaces/handlers/single_system.py`
  delegates to `_resolve_by_manifest_order(...)`
- `src/axis/framework/workspaces/compare_resolution.py`
  currently uses the first two experiment entries it can resolve

That becomes wrong once `single_system` can contain both:

- point outputs
- sweep outputs

The intended behavior is stricter:

- compare only point outputs
- use first point output as reference
- use latest point output as candidate

## Scope

### Filter comparison candidates to point outputs

Auto-resolution for `single_system` must:

1. inspect the result entries or resolved experiment outputs
2. ignore sweep outputs for workspace compare
3. build the comparison pair from point outputs only

### Define auto-selection semantics

Required behavior:

- reference:
  - first point output in historical manifest order
- candidate:
  - latest point output in historical manifest order

If fewer than two point outputs exist:

- fail explicitly

### Keep explicit override support

If explicit experiment IDs are provided, the system must still validate them
through the output-aware path.

If an explicit target is a sweep output:

- fail explicitly
- point the user to `axis workspaces sweep-result`

## Files To Change

- `src/axis/framework/workspaces/handlers/single_system.py`
- `src/axis/framework/workspaces/compare_resolution.py`
- `src/axis/framework/workspaces/compare.py`

## Deliverables

- `single_system` compare ignores sweep outputs
- explicit sweep compare targets fail with a clear message
- point-only compare semantics remain usable in mixed histories

## Non-Goals

- no sweep-vs-sweep compare
- no point-vs-sweep compare
- no changes to direct raw `axis compare` run-vs-run semantics

## Tests

Add or update tests covering:

- mixed point/sweep history: compare uses first point and latest point
- explicit sweep experiment passed to workspace compare -> clear error
- fewer than two point outputs -> clear error
- pure point history behavior still works

Suggested primary test target:

- `tests/framework/workspaces/test_integration.py`

## Acceptance Criteria

- `single_system` compare remains point-vs-point only
- mixed histories no longer break compare semantics
- users get a clear message directing them to `sweep-result` for sweep outputs
