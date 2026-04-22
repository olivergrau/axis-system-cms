# WP-05: Summary, Validation, And Scaffold Alignment

**Phase**: 5 -- Read-only surfaces and creation flow  
**Dependencies**: WP-01, WP-03, WP-04  
**Scope**: Medium  
**Engineering reference**: Sections 8, 9, 11, 13

---

## Objective

Align workspace inspection, validation, and scaffolding with the new workflow
model so the user-facing workflow story is coherent.

---

## Deliverables

Modify:

- `src/axis/framework/workspaces/summary.py`
- `src/axis/framework/workspaces/validation.py`
- `src/axis/framework/cli/commands/workspaces.py`
- `src/axis/framework/cli/parser.py` or scaffolding flow as needed

Add or update tests in:

- `tests/framework/workspaces/test_summary.py`
- `tests/framework/workspaces/test_validation.py`
- CLI output/parser tests related to scaffolding if covered

---

## Required Capabilities

At minimum:

- summaries display the new workflow values correctly
- closed workspaces still validate structurally
- scaffolding offers only the new canonical workflow values
- scaffold defaults align with the spec:
  - `status: draft`
  - `lifecycle_stage: idea`

---

## Implementation Steps

1. Ensure summary rendering handles the new enum values cleanly.
2. Confirm validation treats closed workspaces as valid when structurally sound.
3. Update scaffolding choices to the new canonical workflow sets.
4. Remove deprecated status options from scaffolding.
5. Add tests for summary, validation, and scaffold-facing behavior.

---

## Design Notes

- This WP is mostly alignment, not new workflow logic.
- Avoid adding speculative workflow consistency rules unless they are required
  by the spec.
- Keep `lifecycle_stage` descriptive; do not use it for blocking behavior here.

---

## Verification

1. `show` surfaces the new workflow state clearly.
2. `check` succeeds on valid closed workspaces.
3. New workspaces scaffold only canonical workflow values.

---

## Files Modified

- `src/axis/framework/workspaces/summary.py`
- `src/axis/framework/workspaces/validation.py`
- scaffolding-related CLI code
- summary / validation / parser tests

## Files Deleted

None.
