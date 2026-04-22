# WP-01: Workflow Enum And Manifest Update

**Phase**: 1 -- Foundation  
**Dependencies**: None  
**Scope**: Medium  
**Engineering reference**: Sections 3, 9, 11, 12

---

## Objective

Update the workspace manifest model to the new canonical workflow state set.

This WP establishes the schema and validation behavior that all later workflow
changes depend on.

---

## Deliverables

Modify:

- `src/axis/framework/workspaces/types.py`

Add or update tests in:

- `tests/framework/` manifest / workspace model tests

---

## Required Capabilities

At minimum:

- `WorkspaceStatus` uses only:
  - `draft`
  - `active`
  - `analyzing`
  - `completed`
  - `closed`
- `WorkspaceLifecycleStage` uses only:
  - `idea`
  - `draft`
  - `spec`
  - `implementation`
  - `analysis`
  - `documentation`
  - `final`
- removed values such as `idea` and `running` for `status` are rejected
- removed values are not silently mapped

---

## Implementation Steps

1. Update the `WorkspaceStatus` enum.
2. Update the `WorkspaceLifecycleStage` enum.
3. Ensure manifest validation fails cleanly on removed legacy values.
4. Add tests for accepted new values.
5. Add tests for rejected removed values.

---

## Design Notes

- Do not add migration validators in this WP.
- The user should update `workspace.yaml` explicitly when using removed values.
- Keep the manifest shape unchanged; only the allowed workflow values change.

---

## Verification

1. New canonical workflow values validate successfully.
2. Removed workflow values fail with clear validation errors.
3. Existing class/type manifest rules still work unchanged.

---

## Files Modified

- `src/axis/framework/workspaces/types.py`
- tests covering manifest validation

## Files Deleted

None.
