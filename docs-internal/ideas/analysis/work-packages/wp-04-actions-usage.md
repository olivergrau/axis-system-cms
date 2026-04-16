# WP-04: Action-Space and Usage Metrics

**Phase**: 2 -- Generic Metrics  
**Dependencies**: WP-01, WP-02, WP-03  
**Scope**: Medium  
**Spec reference**: Sections 11, 16

---

## Objective

Implement action-space handling and action usage statistics.

This WP is responsible for making non-identical action spaces comparable through shared labels while preserving one-sided per-system action statistics.

---

## Deliverables

Create:

- `src/axis/framework/comparison/actions.py`

Modify or create:

- `src/axis/framework/comparison/metrics.py`
- `tests/framework/comparison/test_actions.py`

---

## Required Behavior

The implementation must:

- compute the shared action-label intersection
- compute full per-system action counts
- compute deltas only on shared labels
- compute `reference_most_used_action`
- compute `candidate_most_used_action`
- emit `ambiguous_due_to_tie` where required

---

## Implementation Steps

1. Add helpers to extract action labels from episode traces.
2. Add helpers to compute:
   - full count maps per system
   - shared-label count deltas
3. Add most-used-action logic with explicit tie handling.
4. Keep full per-system counts even for non-shared actions.
5. Ensure no paired delta is emitted for non-shared labels.

---

## Tests

Cover at least:

- identical action spaces
- partially overlapping action spaces
- one-sided extra actions
- no shared actions
- tied most-used-action case
- clean untied most-used-action case

---

## Verification

1. Shared-label deltas are only computed on the label intersection.
2. Non-shared actions remain visible in one-sided counts.
3. Tied maxima emit `ambiguous_due_to_tie`.

---

## Files Created

- `src/axis/framework/comparison/actions.py`
- `tests/framework/comparison/test_actions.py`

## Files Modified

- `src/axis/framework/comparison/metrics.py`

## Files Deleted

None.
