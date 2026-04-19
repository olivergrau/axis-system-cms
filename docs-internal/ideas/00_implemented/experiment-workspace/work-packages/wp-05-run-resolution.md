# WP-05: Workspace Run Resolution

**Phase**: 2 -- Execution Resolution  
**Dependencies**: WP-01  
**Scope**: Medium  
**Spec reference**: Sections 13, 15, 17  
**Engineering reference**: Sections 4.5, 9.4

---

## Objective

Resolve executable run targets from a workspace.

This WP should define how AXIS interprets a workspace as something that can be
executed, without yet writing artifacts into the workspace.

---

## Deliverables

Create:

- `src/axis/framework/workspaces/resolution.py`
- `tests/framework/workspaces/test_resolution.py`

Modify:

- `src/axis/framework/workspaces/__init__.py`

---

## Required Resolution Behavior

Support:

- `single_system`
- `system_comparison`
- `system_development`
- `world_development` at least structurally

Resolution should determine:

- which config paths are executable
- which roles apply to those configs
- what the default execution set is for the workspace

At minimum define typed result models such as:

- `WorkspaceRunTarget`
- `WorkspaceExecutionPlan`

---

## Implementation Steps

1. Resolve `primary_configs` from `workspace.yaml`.
2. Classify them by workspace type and role.
3. For `single_system`, define the single execution target.
4. For `system_comparison`, define reference and candidate execution targets.
5. For development workspaces, define baseline validation execution targets.
6. Keep the result as a typed plan for later execution routing.

---

## Design Notes

- Do not run experiments here.
- Do not mutate the workspace here.
- Build on existing `ExperimentConfig` loading rather than inventing a new config format.
- If a workspace declares configs that cannot be resolved into a meaningful execution plan, fail explicitly.

---

## Verification

1. A `single_system` workspace resolves to one execution target.
2. A `system_comparison` workspace resolves to reference and candidate targets.
3. A development workspace resolves to one or more validation targets.
4. Invalid or missing `primary_configs` fail explicitly.

---

## Files Created

- `src/axis/framework/workspaces/resolution.py`
- `tests/framework/workspaces/test_resolution.py`

## Files Modified

- `src/axis/framework/workspaces/__init__.py`

## Files Deleted

None.
