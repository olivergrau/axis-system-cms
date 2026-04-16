# WP-03: Shared-Prefix Alignment

**Phase**: 1 -- Core Comparison Foundation  
**Dependencies**: WP-01  
**Scope**: Small  
**Spec reference**: Section 8

---

## Objective

Implement the shared-prefix alignment helpers used by all stepwise comparison metrics.

The alignment layer must be minimal, explicit, and must not pad traces.

---

## Deliverables

Create:

- `src/axis/framework/comparison/alignment.py`
- `tests/framework/comparison/test_alignment.py`

---

## Required Behavior

Given two episode traces, compute:

- `reference_total_steps`
- `candidate_total_steps`
- `aligned_steps`
- `reference_extra_steps`
- `candidate_extra_steps`

And expose a simple aligned iteration mechanism over the shared prefix.

---

## Implementation Steps

1. Create a helper function such as:
   ```python
   def compute_alignment(reference_trace, candidate_trace) -> AlignmentSummary:
       ...
   ```
2. Add a helper for aligned step pairs:
   ```python
   def iter_aligned_steps(reference_trace, candidate_trace):
       ...
   ```
3. Do not add synthetic padding or inferred steps.
4. Keep timestep basis equal to persisted episode timestep order.

---

## Tests

Cover at least:

- equal-length traces
- longer reference trace
- longer candidate trace
- zero-step traces
- aligned iterator returns only shared-prefix steps

---

## Verification

1. Alignment summaries match the spec formulas exactly.
2. No padding behavior exists in the implementation.

---

## Files Created

- `src/axis/framework/comparison/alignment.py`
- `tests/framework/comparison/test_alignment.py`

## Files Modified

None.

## Files Deleted

None.
