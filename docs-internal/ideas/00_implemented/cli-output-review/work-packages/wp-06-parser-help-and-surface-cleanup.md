# WP-06: Parser Help And Remaining Surface Cleanup

**Phase**: 3 -- Surface Cleanup  
**Dependencies**: WP-03, WP-04, WP-05  
**Scope**: Small  
**Engineering reference**: Sections 4.4, 8.5

---

## Objective

Clean up parser help text and any remaining low-priority terminal-facing
surfaces that still feel inconsistent after the main command migrations.

---

## Deliverables

Modify:

- `src/axis/framework/cli/parser.py`
- any remaining command modules with small direct text outputs

Add or update tests:

- parser/help output tests where coverage exists or is practical

---

## Required Changes

- remove duplicated examples
- improve grouping and readability of help text where feasible
- align remaining direct text outputs with the shared CLI language

---

## Implementation Steps

1. Audit help text for duplication and flatness.
2. Simplify or regroup examples and descriptions where needed.
3. Migrate remaining small direct text outputs onto shared helpers if useful.
4. Keep parser behavior unchanged unless a clear text-quality defect requires change.

---

## Design Notes

- This WP should remain lightweight.
- Do not turn help cleanup into a parser redesign.
- Focus on the visible issues already identified in the draft review.

---

## Verification

1. Duplicated example lines are removed.
2. Help output is easier to scan than before.
3. Remaining small terminal-facing outputs no longer feel like stylistic outliers.

---

## Files Created

None required.

## Files Modified

- `src/axis/framework/cli/parser.py`
- any small remaining terminal-facing command modules

## Files Deleted

None.

