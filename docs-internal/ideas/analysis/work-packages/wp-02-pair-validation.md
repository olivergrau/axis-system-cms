# WP-02: Pair Validation

**Phase**: 1 -- Core Comparison Foundation  
**Dependencies**: WP-01  
**Scope**: Medium  
**Spec reference**: Sections 6, 7, 11

---

## Objective

Implement strict validation for paired comparison.

The validator must determine whether two episode traces are eligible for paired comparison and must emit explicit validation errors when they are not.

---

## Deliverables

Create:

- `src/axis/framework/comparison/validation.py`
- `tests/framework/comparison/test_validation.py`

Potentially reuse:

- `axis.sdk.trace.BaseEpisodeTrace`
- `axis.framework.run.RunConfig`
- `axis.framework.persistence.RunMetadata`

---

## Validation Responsibilities

The validator must check:

- valid episode trace inputs
- world type equality
- world config equality
- start position equality
- episode seed identity
- nonempty shared action-label intersection

It must support:

- explicit episode seed identity when available
- derived seed identity using episode index and base seed when explicit seed is absent

---

## Implementation Steps

1. Add a top-level validation function such as:
   ```python
   def validate_trace_pair(...) -> PairValidationResult:
       ...
   ```
2. Add helper logic to resolve pairing mode:
   - `explicit_episode_seed`
   - `derived_seed_from_index`
3. Compare `world_type` and `world_config` exactly.
4. Resolve start position from episode traces and/or run config as needed.
5. Extract action labels used or available for both traces and compute their intersection.
6. Emit the validation error `action_space_no_shared_labels` when the shared set is empty.
7. Return a structured `PairValidationResult`; do not raise for normal validation failure.

---

## Concrete Inputs

The validator should accept:

- `reference_trace`
- `candidate_trace`
- optional reference/candidate run metadata
- optional reference/candidate run config
- optional reference/candidate episode index

This gives enough context for transitional derived-seed pairing.

---

## Tests

Cover at least:

- valid pair with same world, same seed, same start position
- explicit seed pairing
- derived seed pairing
- world type mismatch
- world config mismatch
- start position mismatch
- seed mismatch
- empty shared action-label intersection
- malformed input trace handling

---

## Verification

1. Valid pairs return `is_valid_pair = true`.
2. Invalid pairs return `is_valid_pair = false` with explicit error codes.
3. Validation does not silently downgrade strict mismatches.

---

## Files Created

- `src/axis/framework/comparison/validation.py`
- `tests/framework/comparison/test_validation.py`

## Files Modified

None.

## Files Deleted

None.
