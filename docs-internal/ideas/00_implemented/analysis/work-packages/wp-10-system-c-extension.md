# WP-10: System C Prediction Comparison Extension

**Phase**: 4 -- System-Specific Extensions  
**Dependencies**: WP-09  
**Scope**: Medium  
**Spec reference**: Section 20

---

## Objective

Implement the first system-specific comparison extension for `System C`.

The extension must use persisted trace data only. It must not depend on live system objects.

---

## Deliverables

Create or extend:

- `src/axis/framework/comparison/extensions.py`
- optionally `src/axis/framework/comparison/system_c.py`
- `tests/framework/comparison/test_system_c_extension.py`

---

## Required Metrics

Implement:

- `prediction_active_step_count`
- `prediction_active_step_rate`
- `top_action_changed_by_modulation_count`
- `top_action_changed_by_modulation_rate`
- `mean_modulation_delta`

Use `epsilon` and `ranking_epsilon` exactly as defined in the spec.

---

## Input Signals

Read from persisted `System C` comparison inputs:

- `decision_data["drive"]["action_contributions"]`
- `decision_data["prediction"]["modulated_scores"]`

Do not assume more than the current persisted shape.

If required signals are missing, emit:

- `missing_required_signal`

where appropriate.

---

## Implementation Steps

1. Add a `System C` extension builder.
2. Detect `System C` participation from trace identity.
3. Compute prediction-active steps using raw vs. modulated score difference.
4. Compute top-action-changed-by-modulation with tie handling.
5. Compute mean modulation delta over aligned steps.
6. Attach the block under:
   - `system_specific_analysis.system_c_prediction`

---

## Tests

Cover at least:

- prediction-active steps present
- no prediction activity
- top-action changed clearly
- ambiguous top-action due to tie
- missing required `decision_data` signals

Use small synthetic traces rather than large persisted files for core correctness.

---

## Verification

1. The extension uses only persisted trace payloads.
2. Ambiguous steps are not silently counted as positive changes.
3. The extension is optional and does not affect non-System-C comparisons.

---

## Files Created

- `tests/framework/comparison/test_system_c_extension.py`
- `src/axis/framework/comparison/system_c.py` (optional but recommended)

## Files Modified

- `src/axis/framework/comparison/extensions.py`

## Files Deleted

None.
