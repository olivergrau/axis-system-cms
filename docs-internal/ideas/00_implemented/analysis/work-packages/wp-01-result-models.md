# WP-01: Comparison Result Models

**Phase**: 1 -- Core Comparison Foundation  
**Dependencies**: None  
**Scope**: Medium  
**Spec reference**: Sections 10, 12, 21

---

## Objective

Create the typed result models for paired trace comparison.

These models define the stable internal schema for:

- identity
- validation
- alignment
- generic metrics
- outcome comparison
- optional system-specific analysis blocks

The intent is to avoid raw untyped dictionaries as the primary representation.

---

## Deliverables

Create:

- `src/axis/framework/comparison/__init__.py`
- `src/axis/framework/comparison/types.py`
- `tests/framework/comparison/__init__.py`
- `tests/framework/comparison/test_types.py`

---

## Required Models

At minimum define:

- `PairValidationResult`
- `AlignmentSummary`
- `ActionDivergenceMetrics`
- `PositionDivergenceMetrics`
- `VitalityDivergenceMetrics`
- `ActionUsageMetrics`
- `OutcomeComparison`
- `GenericComparisonMetrics`
- `PairedTraceComparisonResult`

Also define explicit value types for:

- comparison result mode
- pairing mode
- ambiguity/special-state values

Use frozen Pydantic models, following existing AXIS conventions.

---

## Implementation Steps

1. Create `comparison/__init__.py` with a one-line package docstring and public exports.
2. Implement `types.py` with frozen models only. No comparison logic in this WP.
3. Represent special states explicitly, either via string literals or small enums.
4. Include the tolerance values in a typed home:
   - `epsilon = 1e-9`
   - `ranking_epsilon = 1e-6`
5. Ensure `system_specific_analysis` is present as an optional dict-like field on the top-level result.

---

## Design Notes

- Keep the structure close to the spec names.
- Do not over-normalize into dozens of tiny models.
- Use simple array/list fields for time series.
- Preserve explicit `validation_errors` as structured machine-readable values.

---

## Verification

1. Models can be instantiated with valid example data.
2. Models are frozen and reject mutation.
3. Series fields accept simple arrays.
4. Ambiguity values can be represented without coercion.

---

## Files Created

- `src/axis/framework/comparison/__init__.py`
- `src/axis/framework/comparison/types.py`
- `tests/framework/comparison/__init__.py`
- `tests/framework/comparison/test_types.py`

## Files Modified

None.

## Files Deleted

None.
