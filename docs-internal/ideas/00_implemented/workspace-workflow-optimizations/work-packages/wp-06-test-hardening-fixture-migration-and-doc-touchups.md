# WP-06: Test Hardening, Fixture Migration, And Doc Touch-Ups

**Phase**: 6 -- Hardening  
**Dependencies**: WP-01 through WP-05  
**Scope**: Medium  
**Engineering reference**: Sections 12, 13, 14

---

## Objective

Finish the workflow transition by updating tests, shipped workspace fixtures,
and workflow-facing docs/help text.

---

## Deliverables

Modify:

- existing workspace fixture manifests under `workspaces/`
- workflow-related docs/help text as needed
- any remaining tests still using removed workflow values

Add or update tests in:

- parser tests
- CLI output tests
- workspace service tests
- validation/summary tests

---

## Required Capabilities

At minimum:

- repository workspace examples use canonical workflow values
- tests no longer rely on removed values unless they are explicitly testing
  rejection
- explicit tests exist for failure on removed status values
- workflow-facing help/docs no longer mention deprecated states

---

## Implementation Steps

1. Update workspace fixture manifests in `workspaces/`.
2. Update any test data that still uses removed values like `idea` or
   `running`.
3. Add negative tests for removed legacy states.
4. Update parser/help text or small docs references if they mention old
   workflow labels.
5. Run the relevant framework/workspace test suites and fix any regressions.

---

## Design Notes

- This WP should intentionally distinguish between:
  - fixtures updated to new canonical values
  - negative tests that still use removed values to verify rejection
- Keep doc changes limited to places directly affected by the workflow rename.

---

## Verification

1. Repo workspace examples validate under the new workflow schema.
2. Removed legacy workflow values are covered by explicit failing tests.
3. No remaining workflow-facing help text suggests deprecated state names.

---

## Files Modified

- workspace fixture manifests
- workflow-related tests
- small workflow-facing docs/help references

## Files Deleted

None.
