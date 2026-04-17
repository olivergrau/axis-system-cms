# WP-08: Workspace Compare Resolution

**Phase**: 3 -- Comparison Resolution  
**Dependencies**: WP-01, WP-06  
**Scope**: Medium  
**Spec reference**: Sections 13, 17  
**Engineering reference**: Sections 4.5, 9.4

---

## Objective

Resolve comparison targets from workspace state.

This WP defines how a workspace becomes a comparison input to the existing
comparison package.

---

## Deliverables

Create:

- `src/axis/framework/workspaces/compare_resolution.py`
- `tests/framework/workspaces/test_compare_resolution.py`

Modify:

- `src/axis/framework/workspaces/__init__.py`

---

## Required Resolution Behavior

Support at minimum:

- `system_comparison`
- `system_development` where comparison is a secondary validation artifact

Resolution should determine:

- the reference-side artifact set
- the candidate-side artifact set
- the comparison mode to invoke

At minimum define:

- `WorkspaceCompareTarget`
- `WorkspaceComparisonPlan`

---

## Implementation Steps

1. Load the workspace manifest and workspace artifact state.
2. Resolve comparison inputs from `primary_results` and/or comparison-ready workspace state.
3. For `system_comparison`, map reference/candidate roles explicitly.
4. For development workspaces, define how baseline-vs-candidate comparisons are selected.
5. Keep this WP resolution-only; no comparison output writing yet.

---

## Design Notes

- Reuse the existing comparison package rather than creating a parallel one.
- The workspace layer should prepare inputs, not duplicate comparison logic.
- If a workspace is not comparison-ready, fail explicitly with a clear diagnostic.

---

## Verification

1. A comparison workspace resolves to a valid comparison plan.
2. A development workspace can resolve a validation comparison plan when artifacts exist.
3. Missing reference/candidate artifacts fail explicitly.

---

## Files Created

- `src/axis/framework/workspaces/compare_resolution.py`
- `tests/framework/workspaces/test_compare_resolution.py`

## Files Modified

- `src/axis/framework/workspaces/__init__.py`

## Files Deleted

None.
