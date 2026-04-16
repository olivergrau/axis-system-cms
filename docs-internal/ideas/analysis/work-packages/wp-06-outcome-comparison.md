# WP-06: Outcome Comparison

**Phase**: 2 -- Generic Metrics  
**Dependencies**: WP-01, WP-03  
**Scope**: Small  
**Spec reference**: Section 18

---

## Objective

Implement the whole-episode outcome comparison block.

This block must remain separate from shared-prefix divergence metrics.

---

## Deliverables

Modify:

- `src/axis/framework/comparison/metrics.py`
- `tests/framework/comparison/test_metrics.py`

---

## Required Fields

Implement:

- `reference_termination_reason`
- `candidate_termination_reason`
- `reference_final_vitality`
- `candidate_final_vitality`
- `final_vitality_delta`
- `reference_total_steps`
- `candidate_total_steps`
- `total_step_delta`
- `longer_survivor`

---

## Implementation Steps

1. Add a helper such as:
   ```python
   def compute_outcome_comparison(reference_trace, candidate_trace) -> OutcomeComparison:
       ...
   ```
2. Use total episode length, not aligned length, for outcome comparison.
3. Compute `longer_survivor` exactly as specified.
4. Keep this block independent from metric-family internals.

---

## Tests

Cover at least:

- equal-length episodes
- longer reference episode
- longer candidate episode
- different termination reasons
- identical termination reasons

---

## Verification

1. Outcome facts are based on full episode traces.
2. `longer_survivor` is correct in all three cases.

---

## Files Created

None.

## Files Modified

- `src/axis/framework/comparison/metrics.py`
- `tests/framework/comparison/test_metrics.py`

## Files Deleted

None.
