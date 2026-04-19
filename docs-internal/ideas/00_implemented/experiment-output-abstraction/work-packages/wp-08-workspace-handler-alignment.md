# WP-08 Workspace Handler Alignment

## Goal

Align the existing workspace handlers with experiment-output-centric result
identity and remove lingering assumptions that primary results are run-shaped.

## Why This Package Exists

Current handlers:

- `src/axis/framework/workspaces/handlers/single_system.py`
- `src/axis/framework/workspaces/handlers/system_comparison.py`
- `src/axis/framework/workspaces/handlers/system_development.py`

still encode assumptions that compare and visualization can recover everything
from experiment ordering plus raw run resolution.

After the Experiment Output refactor, handlers should think in terms of:

- roles
- experiment outputs
- output-form compatibility

## Scope

### `single_system`

Keep current point-output workflow, but ensure manifest ordering and result
semantics are compatible with experiment-root output entries.

### `system_comparison`

Continue resolving reference/candidate by system role, but against experiment
outputs rather than run-shaped assumptions.

### `system_development`

Maintain:

- baseline/candidate flow
- non-`single_run` guardrails

but align development result references with experiment-output identity.

## Files To Change

- `src/axis/framework/workspaces/handlers/single_system.py`
- `src/axis/framework/workspaces/handlers/system_comparison.py`
- `src/axis/framework/workspaces/handlers/system_development.py`

## Deliverables

- handlers compatible with experiment-root result entries
- no latent run-path dependence in workspace role logic
- current workspace-type semantics preserved

## Tests

Update existing workspace integration tests:

- `tests/framework/workspaces/test_integration.py`
- `tests/framework/workspaces/test_validation.py`

## Acceptance Criteria

- handler behavior remains semantically correct after output-centric manifest changes
- existing workspace types still operate correctly for point outputs
