# WP-02: Error Framing And Dispatch Integration

**Phase**: 1 -- Foundation Integration  
**Dependencies**: WP-01  
**Scope**: Small  
**Engineering reference**: Sections 4, 7

---

## Objective

Centralize user-facing text-mode error framing and integrate it into CLI
dispatch.

This WP should make AXIS error presentation feel consistent before the larger
command migrations begin.

---

## Deliverables

Modify:

- `src/axis/framework/cli/dispatch.py`
- selected command modules that have simple duplicated stderr errors

Add tests:

- `tests/framework/cli/test_dispatch.py` or equivalent focused coverage

---

## Required Changes

- replace the top-level raw `print(f"Error: {exc}", file=sys.stderr)` fallback
- use shared output helpers for error lines
- support optional hint rendering for obvious operational failures
- reduce duplicated direct stderr formatting where easy and low-risk

---

## Implementation Steps

1. Update `dispatch.py` to use the shared output layer for top-level exceptions.
2. Standardize the default error prefix and message structure.
3. Migrate a few low-risk direct stderr prints where the change is mechanical.
4. Add tests confirming stderr formatting remains explicit and readable.

---

## Design Notes

- This WP is about presentation, not exception model redesign.
- `SystemExit`-based flows may remain in place for now.
- Do not block later command migrations on perfect exception taxonomy.

---

## Verification

1. Unhandled CLI exceptions present through the shared error format.
2. Stderr output remains plain-text readable.
3. Common operational failures can include a concise hint when appropriate.

---

## Files Created

None required.

## Files Modified

- `src/axis/framework/cli/dispatch.py`
- selected CLI command modules
- `tests/framework/cli/test_dispatch.py` or equivalent

## Files Deleted

None.

