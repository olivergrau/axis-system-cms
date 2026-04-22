# WP-03: Comparison Output Normalization

**Phase**: 2 -- Command Migration  
**Dependencies**: WP-01, WP-02  
**Scope**: Medium  
**Engineering reference**: Sections 4.2, 8.2, 9

---

## Objective

Refactor CLI comparison text output onto the shared presentation layer.

This is the highest-value first migration because `compare.py` currently has
the densest and most sequential text formatting.

---

## Deliverables

Modify:

- `src/axis/framework/cli/commands/compare.py`

Add or update tests:

- `tests/framework/cli/` comparison-focused output tests

---

## Required Output Shape

At minimum the migrated comparison output should support:

- title or result headline
- comparison identity block
- validation block
- per-episode results section
- statistical summary section
- clearer no-valid-pairs handling

---

## Implementation Steps

1. Extract or isolate the comparison text rendering path.
2. Replace ad hoc dashed separators with shared section rendering.
3. Normalize validation failure output.
4. Normalize metric rows through shared field/list helpers.
5. Keep JSON rendering unchanged.

---

## Design Notes

- Preserve the existing domain content and numeric detail.
- Improve structure without collapsing useful detail.
- Avoid mixing explanatory prose and metrics in an unbroken print stream.

---

## Verification

1. Run-level comparison output is visibly sectioned and easier to scan.
2. Single-episode comparison output follows the same semantic conventions.
3. No-valid-pairs cases render clearly.
4. JSON compare output is unchanged.

---

## Files Created

None required.

## Files Modified

- `src/axis/framework/cli/commands/compare.py`
- comparison output tests under `tests/framework/cli/`

## Files Deleted

None.

