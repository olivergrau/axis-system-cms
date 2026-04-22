# WP-07: Optional Styling And Runtime Logging Alignment

**Phase**: 3 -- Polish  
**Dependencies**: WP-03, WP-04, WP-05  
**Scope**: Medium  
**Engineering reference**: Sections 4.5, 8.6, 11, 12

---

## Objective

Add conservative semantic styling for interactive terminals and align runtime
episode logging with the same presentation principles.

This WP should only begin after structural normalization has already landed.

---

## Deliverables

Modify:

- `src/axis/framework/cli/output.py`
- `src/axis/framework/logging.py`

Possibly create:

- `src/axis/framework/cli/output_styles.py` if the style layer warrants a split

Add or update tests:

- styling-aware output tests
- runtime logging output tests

---

## Required Changes

- add optional semantic ANSI styling
- enable styling only for interactive terminals or explicit supported cases
- preserve plain-text readability without color
- improve verbose `EpisodeLogger` console formatting
- consider clearer episode boundaries where they materially help readability

---

## Implementation Steps

1. Add a conservative style policy to the shared output layer.
2. Restrict styling primarily to prefixes, labels, and headings.
3. Refactor runtime verbose output away from dense one-line JSON blobs.
4. Keep JSONL behavior unchanged.

---

## Design Notes

- Styling is reinforcement, not structure.
- Runtime logging should remain compact and stable.
- Do not add decorative formatting that harms redirected output.

---

## Verification

1. Interactive terminals can receive semantic styling without losing plain-text meaning.
2. Non-interactive output remains readable and stable.
3. Verbose runtime logging is easier to scan than raw one-line JSON dumps.
4. JSONL logging output remains unchanged.

---

## Files Created

- `src/axis/framework/cli/output_styles.py` only if needed

## Files Modified

- `src/axis/framework/cli/output.py`
- `src/axis/framework/logging.py`
- styling/logging tests

## Files Deleted

None.

