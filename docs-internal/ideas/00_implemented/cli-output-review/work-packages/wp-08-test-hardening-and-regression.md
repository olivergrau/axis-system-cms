# WP-08: Test Hardening And Regression Coverage

**Phase**: 4 -- Hardening  
**Dependencies**: WP-01 through WP-07  
**Scope**: Medium  
**Engineering reference**: Section 13

---

## Objective

Add or consolidate the tests needed to make the new CLI presentation layer
safe to evolve.

This WP should explicitly protect both human-oriented text mode and the
requirement that JSON mode remain unchanged.

---

## Deliverables

Create or expand tests under:

- `tests/framework/cli/`
- `tests/framework/` for logging-focused cases

---

## Required Coverage

At minimum cover:

- shared output helper rendering
- top-level error framing
- representative comparison text output
- representative workspace text output
- representative experiments and runs text output
- JSON regression coverage for migrated commands
- runtime logging output if WP-07 lands

---

## Implementation Steps

1. Audit which migrated surfaces still lack text-output tests.
2. Add focused output assertions rather than overly brittle giant snapshots.
3. Add explicit JSON regression tests for migrated command families.
4. Add logging tests if verbose runtime rendering changed.

---

## Design Notes

- Prefer small, high-signal assertions over giant fixture dumps when possible.
- Protect structural conventions without making benign wording cleanup impossible.
- Keep JSON regression coverage explicit.

---

## Verification

1. All migrated command families have focused text-output test coverage.
2. JSON mode is protected by regression tests.
3. Shared helper behavior can change intentionally through one obvious test surface.
4. Logging changes, if any, are covered separately from CLI command tests.

---

## Files Created

- new tests under `tests/framework/cli/` as needed

## Files Modified

- existing CLI and logging tests as needed

## Files Deleted

None.
