# WP-11: Drift Detection and Stronger Consistency

**Phase**: 4 -- Post-Execution Consistency  
**Dependencies**: WP-02, WP-10  
**Scope**: Medium  
**Engineering reference**: Section 10.3

---

## Objective

Detect workspace drift once real execution and comparison artifacts exist.

This WP strengthens consistency guarantees beyond the initial checker.

---

## Deliverables

Create:

- `src/axis/framework/workspaces/drift.py`
- `tests/framework/workspaces/test_drift.py`

Modify:

- `src/axis/framework/workspaces/validation.py`
- `src/axis/framework/workspaces/__init__.py`

---

## Required Drift Signals

At minimum detect:

- declared primary artifacts that are missing
- likely primary artifacts present in the workspace but undeclared
- comparison role incompleteness in comparison workspaces
- manifest/artifact mismatches after workspace-aware operations

Warnings vs errors should remain explicit.

---

## Implementation Steps

1. Add drift-detection helpers that inspect workspace content against manifest state.
2. Integrate drift findings into the checker result.
3. Keep drift detection separate from basic structural validation.
4. Ensure comparison workspaces get role completeness checks.

---

## Design Notes

- Drift detection should be additive, not a replacement for the checker.
- Keep heuristics conservative; do not guess too aggressively about undeclared files.
- Do not mutate the workspace in this WP.

---

## Verification

1. Missing declared artifacts are detected.
2. Undeclared likely-primary artifacts can be flagged as warnings.
3. Comparison role completeness problems are detected.
4. Drift findings appear through the workspace check flow.

---

## Files Created

- `src/axis/framework/workspaces/drift.py`
- `tests/framework/workspaces/test_drift.py`

## Files Modified

- `src/axis/framework/workspaces/validation.py`
- `src/axis/framework/workspaces/__init__.py`

## Files Deleted

None.
