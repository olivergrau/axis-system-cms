# WP-09 Validation and Drift Detection

## Goal

Tighten validation and drift detection around the new output abstraction and
the refactored workspace result semantics.

## Why This Package Exists

Current validation in `src/axis/framework/workspaces/validation.py`
already checks:

- workspace structure
- declared paths
- config guardrails for non-`single_run`

But it does not yet validate:

- structured output entries
- output-form consistency
- experiment-root result identity

## Scope

### Workspace validation updates

Extend validation for:

- structured `primary_results`
- required fields on result entries
- valid experiment-root result paths
- coherence between entry metadata and persisted experiment output

### Drift detection updates

Update drift detection to:

- reason about experiment-root outputs rather than run-path entries
- detect stale or missing experiment roots
- detect mismatches between manifest result entry metadata and actual persisted output semantics

### Output-level validation

Validation must surface clear errors if persisted experiment output semantics
are inconsistent.

## Files To Change

- `src/axis/framework/workspaces/validation.py`
- `src/axis/framework/workspaces/drift.py`
- `src/axis/framework/experiment_output.py`

## Deliverables

- output-aware workspace validation
- output-aware drift detection
- explicit semantic error reporting

## Tests

Update/add tests in:

- `tests/framework/workspaces/test_validation.py`
- add drift tests if needed

## Acceptance Criteria

- workspaces with malformed output entries are rejected clearly
- output-semantic inconsistencies are surfaced before later commands act on them
