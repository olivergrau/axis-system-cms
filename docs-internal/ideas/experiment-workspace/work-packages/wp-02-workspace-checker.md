# WP-02: Workspace Checker

**Phase**: 1 -- Validation Foundation  
**Dependencies**: WP-01  
**Scope**: Medium  
**Spec reference**: Sections 12, 13, 14, 15, 20

---

## Objective

Implement structural and semantic validation for workspace directories.

This WP should answer:

- does the workspace root contain the required files and directories?
- is `workspace.yaml` valid?
- do declared primary artifacts exist?
- are required directories present for the declared workspace type?

---

## Deliverables

Create:

- `src/axis/framework/workspaces/validation.py`
- `tests/framework/workspaces/test_validation.py`

Modify:

- `src/axis/framework/workspaces/__init__.py`

No CLI changes yet in this WP.

---

## Required Result Types

At minimum define:

- `WorkspaceCheckSeverity`
- `WorkspaceCheckIssue`
- `WorkspaceCheckResult`

These may live in `types.py` or `validation.py`, but keep them inside
`framework/workspaces/`.

---

## Required Checks

Implement checks for:

- presence of `workspace.yaml`
- manifest parse validity
- shared top-level directory presence
- required directories by workspace type
- existence of declared `primary_configs`
- existence of declared `primary_results`
- existence of declared `primary_comparisons`
- existence of declared `primary_measurements`

Warnings should be supported for incomplete-but-not-invalid states.

---

## Implementation Steps

1. Add a manifest loader helper that reads `workspace.yaml`.
2. Add directory-structure checks against the spec.
3. Add primary-artifact existence checks based on manifest fields.
4. Add warnings for plausible incomplete states:
   - no `primary_results` yet
   - empty `comparisons/` in a comparison workspace still in draft
   - empty `measurements/`
5. Return a structured check result rather than printing directly.

---

## Design Notes

- Keep checker output machine-readable first.
- Human-readable formatting belongs later in `show` or CLI functions.
- This WP should not mutate the workspace.
- Linked external artifacts may be checked only for basic path existence if present.

---

## Verification

1. A valid probe workspace passes with no errors.
2. Missing `workspace.yaml` fails explicitly.
3. Missing `engineering/` in a development workspace fails explicitly.
4. Missing declared primary artifact paths fail explicitly.
5. Incomplete but plausible states can emit warnings instead of hard failures.

---

## Files Created

- `src/axis/framework/workspaces/validation.py`
- `tests/framework/workspaces/test_validation.py`

## Files Modified

- `src/axis/framework/workspaces/__init__.py`

## Files Deleted

None.
