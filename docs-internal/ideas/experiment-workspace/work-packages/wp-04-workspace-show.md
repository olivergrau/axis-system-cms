# WP-04: Workspace Show / Summary

**Phase**: 1 -- Workspace Inspection  
**Dependencies**: WP-01, WP-02  
**Scope**: Small  
**Engineering reference**: Section 4.4

---

## Objective

Implement a read-oriented summary view of a workspace.

This WP should provide a structured summary object that the CLI can later
render as text or JSON.

---

## Deliverables

Create:

- `src/axis/framework/workspaces/summary.py`
- `tests/framework/workspaces/test_summary.py`

Modify:

- `src/axis/framework/workspaces/__init__.py`

---

## Required Summary Content

At minimum include:

- workspace identity
- class and type
- status and lifecycle stage
- primary configs
- primary results
- primary comparisons
- primary measurements
- checker result summary

---

## Implementation Steps

1. Build a typed summary model or structured dict output.
2. Load the manifest through WP-01.
3. Reuse checker output from WP-02.
4. Produce a concise machine-readable summary for later CLI rendering.

---

## Design Notes

- Keep the summary module pure and read-only.
- Do not print directly from this module.
- The CLI should delegate to this layer and only handle formatting.

---

## Verification

1. A workspace summary can be built for each probe workspace type.
2. Missing optional artifact groups do not break summary generation.
3. Validation status can be included without duplicating checker logic.

---

## Files Created

- `src/axis/framework/workspaces/summary.py`
- `tests/framework/workspaces/test_summary.py`

## Files Modified

- `src/axis/framework/workspaces/__init__.py`

## Files Deleted

None.
