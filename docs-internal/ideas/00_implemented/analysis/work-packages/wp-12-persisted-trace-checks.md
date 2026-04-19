# WP-12: Persisted Trace Compatibility Checks

**Phase**: 5 -- Verification and Fixtures  
**Dependencies**: WP-07 through WP-10  
**Scope**: Small  
**Spec reference**: Engineering validation against real artifacts

---

## Objective

Verify that the comparison layer works against real persisted AXIS episode traces.

This WP is the bridge between synthetic correctness and actual repository artifacts.

---

## Deliverables

Create:

- `tests/framework/comparison/test_persisted_traces.py`

Potentially reuse:

- traces under `experiments/results/`
- repository loaders
- replay access utilities

---

## Required Checks

The tests should verify that:

- valid persisted trace pairs can be loaded and compared
- comparison does not assume fields absent from the current replay contract
- the `System C` extension can read real `decision_data` and `trace_data`
- JSON output shape remains serializable

---

## Implementation Steps

1. Select a small stable subset of persisted traces or copy minimal fixtures into test assets if needed.
2. Use repository/replay loaders rather than ad hoc file parsing where practical.
3. Verify at least one generic comparison and one `System C` extension path.
4. Keep this test suite narrow; do not duplicate all synthetic edge-case testing.

---

## Tests

Cover at least:

- load and compare a valid real trace pair
- verify generic metric blocks are present
- verify `system_c_prediction` block is attachable on real `System C` traces

If no stable `System A` and `System C` persisted pair exists yet, use:

- real `System C` traces for extension compatibility
- synthetic fixtures for cross-system pairing correctness

---

## Verification

1. The comparison package works on real persisted artifacts.
2. No hidden assumptions remain about trace payload shape.

---

## Files Created

- `tests/framework/comparison/test_persisted_traces.py`

## Files Modified

None.

## Files Deleted

None.
