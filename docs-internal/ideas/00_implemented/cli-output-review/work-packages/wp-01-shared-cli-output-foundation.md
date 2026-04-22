# WP-01: Shared CLI Output Foundation

**Phase**: 1 -- Foundation  
**Dependencies**: None  
**Scope**: Medium  
**Engineering reference**: Sections 3, 6, 9, 11

---

## Objective

Implement a small shared CLI text-output layer for human-oriented terminal
presentation.

This WP should create the reusable rendering helpers that later command
migrations depend on.

---

## Deliverables

Create:

- `src/axis/framework/cli/output.py`
- `tests/framework/cli/test_output.py`

Modify:

- `src/axis/framework/cli/__init__.py` if exports need adjustment

---

## Required Capabilities

At minimum provide helpers for:

- title lines
- section headings
- field rows
- list rows
- info lines
- success lines
- warning lines
- error lines
- hint lines

Also define:

- default indentation behavior
- blank-line section behavior
- optional style policy hooks

---

## Implementation Steps

1. Introduce a minimal renderer or helper set in `output.py`.
2. Keep the API small and semantic rather than overly generic.
3. Ensure plain text is the default and works without color.
4. Add tests for stable plain-text rendering behavior.
5. Avoid coupling the helper layer to any command-specific domain logic.

---

## Design Notes

- Start with the smallest useful abstraction.
- Prefer explicit helper names over a generic mini-template engine.
- Keep JSON concerns completely out of this module.

---

## Verification

1. Shared helpers can render headings, sections, labels, and semantic status lines.
2. Plain-text rendering is stable and readable.
3. The helper API is small enough that later command migrations can adopt it directly.

---

## Files Created

- `src/axis/framework/cli/output.py`
- `tests/framework/cli/test_output.py`

## Files Modified

- `src/axis/framework/cli/__init__.py` if needed

## Files Deleted

None.

