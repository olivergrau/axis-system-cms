# WP-05: Divergence Metrics

**Phase**: 2 -- Generic Metrics  
**Dependencies**: WP-01, WP-03  
**Scope**: Medium  
**Spec reference**: Sections 13, 14, 15, 17

---

## Objective

Implement the generic divergence metric families:

- action divergence
- position divergence
- vitality divergence

This WP also owns the required time-series outputs.

---

## Deliverables

Create or extend:

- `src/axis/framework/comparison/metrics.py`
- `tests/framework/comparison/test_metrics.py`

---

## Required Metrics

Implement:

- `first_action_divergence_step`
- `action_mismatch_count`
- `action_mismatch_rate`
- `first_position_divergence_step`
- `trajectory_distance_series`
- `mean_trajectory_distance`
- `max_trajectory_distance`
- `vitality_difference_series`
- `mean_absolute_vitality_difference`
- `max_absolute_vitality_difference`

Position distance in v1 must use Manhattan distance.

---

## Implementation Steps

1. Use aligned step pairs from `alignment.py`.
2. Compute action divergence from selected action labels.
3. Compute trajectory distance from aligned positions.
4. Compute vitality difference from aligned vitality values.
5. Keep series as simple arrays in timestep order.
6. Use centralized tolerance values where relevant.

---

## Tests

Cover at least:

- no divergence at all
- immediate action divergence
- delayed action divergence
- immediate position divergence
- delayed position divergence
- unequal vitality curves
- empty aligned prefix

---

## Verification

1. The first-divergence fields are correct.
2. Series values match hand-computed expectations.
3. Mean and max aggregates match series contents.

---

## Files Created

- `tests/framework/comparison/test_metrics.py`

## Files Modified

- `src/axis/framework/comparison/metrics.py`

## Files Deleted

None.
