# WP-02: Close Mutation And Workflow Service

**Phase**: 2 -- Workflow mutation  
**Dependencies**: WP-01  
**Scope**: Medium  
**Engineering reference**: Sections 4, 5, 10, 11

---

## Objective

Implement the canonical close operation for workspaces.

This WP should create the single service-level path that mutates a workspace
into its final closed state.

---

## Deliverables

Modify:

- `src/axis/framework/workspaces/manifest_mutator.py`

Create:

- `src/axis/framework/workspaces/services/workflow_service.py`

Add or update tests in:

- `tests/framework/test_workspace_services.py`
- any focused mutator tests

---

## Required Capabilities

At minimum provide:

- a mutator that sets:
  - `status: closed`
  - `lifecycle_stage: final`
- a service that:
  - loads the manifest roundtrip
  - applies the close mutation
  - writes the manifest back
  - returns a small result object
- rejection of closing an already closed workspace

---

## Implementation Steps

1. Add a close mutator function to the manifest mutation layer.
2. Raise `ValueError` if the workspace is already closed.
3. Add a workflow service that owns close orchestration.
4. Keep file IO roundtrip-preserving, consistent with existing workspace
   mutation patterns.
5. Add focused tests for successful close and duplicate close rejection.

---

## Design Notes

- The CLI should not mutate `workspace.yaml` directly.
- Keep the close operation intentionally narrow; do not implement reopen here.
- Return a small structured result that is easy for CLI text and JSON output to
  consume.

---

## Verification

1. A non-closed workspace can be closed through the service.
2. The manifest ends up with `status=closed` and `lifecycle_stage=final`.
3. Closing an already closed workspace fails clearly.

---

## Files Created

- `src/axis/framework/workspaces/services/workflow_service.py`

## Files Modified

- `src/axis/framework/workspaces/manifest_mutator.py`
- tests covering workflow service behavior

## Files Deleted

None.
