# WP-04: Closed-Workspace Enforcement

**Phase**: 4 -- Policy enforcement  
**Dependencies**: WP-01, WP-02  
**Scope**: Medium  
**Engineering reference**: Sections 7, 11, 12

---

## Objective

Make closed workspaces operationally read-only by blocking mutating workflow
actions in the service layer.

---

## Deliverables

Modify:

- `src/axis/framework/workspaces/services/run_service.py`
- `src/axis/framework/workspaces/services/compare_service.py`

Add or update tests in:

- `tests/framework/test_workspace_services.py`

---

## Required Capabilities

At minimum:

- `WorkspaceRunService.execute(...)` rejects closed workspaces
- `WorkspaceRunService.set_candidate(...)` rejects closed workspaces
- `WorkspaceCompareService.compare(...)` rejects closed workspaces
- error messages are clear and action-oriented

---

## Implementation Steps

1. Load the manifest before mutating workflow operations.
2. Add explicit closed-state checks in run service methods.
3. Add explicit closed-state checks in compare service methods.
4. Use direct `ValueError` messages that explain the command is blocked because
   the workspace is closed.
5. Add focused service tests for each blocked path.

---

## Design Notes

- Enforcement belongs in services, not only in CLI commands.
- Keep inspection behavior unchanged; only mutating operations are blocked.
- Do not broaden this WP into lifecycle-stage-based gating.

---

## Verification

1. Closed workspaces cannot be run.
2. Closed workspaces cannot be compared.
3. Closed workspaces cannot change candidate config.
4. Open workspaces still behave exactly as before.

---

## Files Modified

- `src/axis/framework/workspaces/services/run_service.py`
- `src/axis/framework/workspaces/services/compare_service.py`
- service tests

## Files Deleted

None.
