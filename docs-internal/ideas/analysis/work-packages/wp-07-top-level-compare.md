# WP-07: Top-Level Compare Entry Point

**Phase**: 3 -- Comparison Orchestration  
**Dependencies**: WP-01 through WP-06  
**Scope**: Medium  
**Spec reference**: Sections 4, 12, 21

---

## Objective

Implement the top-level paired comparison entry point.

This function orchestrates:

- validation
- alignment
- generic metrics
- outcome comparison
- structured result assembly

It must return a structured result both for successful and failed-validation comparisons.

---

## Deliverables

Create:

- `src/axis/framework/comparison/compare.py`
- `tests/framework/comparison/test_compare.py`

Potentially update:

- `src/axis/framework/comparison/__init__.py`

---

## Required Entry Point

Provide a top-level function with the shape defined in the engineering spec, for example:

```python
def compare_episode_traces(
    reference_trace,
    candidate_trace,
    *,
    reference_run_metadata=None,
    candidate_run_metadata=None,
    reference_run_config=None,
    candidate_run_config=None,
    reference_episode_index=None,
    candidate_episode_index=None,
):
    ...
```

---

## Implementation Steps

1. Call validation first.
2. If validation fails, return a structured failed-validation result.
3. Compute alignment summary.
4. Compute generic metric families.
5. Compute outcome comparison.
6. Assemble the final `PairedTraceComparisonResult`.
7. Leave `system_specific_analysis` empty for now; this will be extended later.

---

## Tests

Cover at least:

- successful valid comparison
- failed comparison due to validation
- result shape includes all required top-level sections
- failed result still contains identity and validation information

---

## Verification

1. One top-level call yields a complete result object.
2. Failure mode is explicit and structured.

---

## Files Created

- `src/axis/framework/comparison/compare.py`
- `tests/framework/comparison/test_compare.py`

## Files Modified

- `src/axis/framework/comparison/__init__.py`

## Files Deleted

None.
