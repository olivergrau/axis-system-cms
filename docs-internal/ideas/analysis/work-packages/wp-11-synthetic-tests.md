# WP-11: Synthetic Comparison Test Suite

**Phase**: 5 -- Verification and Fixtures  
**Dependencies**: WP-01 through WP-10  
**Scope**: Medium  
**Spec reference**: Cross-cutting verification

---

## Objective

Create a deterministic synthetic test suite for the comparison core.

This WP is about correctness and edge-case coverage, not implementation of new comparison logic.

---

## Deliverables

Create:

- `tests/framework/comparison/fixtures.py`
- extend existing comparison tests or add:
  - `tests/framework/comparison/test_validation.py`
  - `tests/framework/comparison/test_alignment.py`
  - `tests/framework/comparison/test_actions.py`
  - `tests/framework/comparison/test_metrics.py`
  - `tests/framework/comparison/test_compare.py`
  - `tests/framework/comparison/test_system_c_extension.py`

---

## Fixture Requirements

Provide compact synthetic helpers for:

- minimal episode traces
- valid paired traces
- invalid paired traces
- unequal-length traces
- overlapping and non-overlapping action spaces
- tied rankings
- `System C`-style decision payloads with raw/modulated scores

Use `BaseEpisodeTrace` and `BaseStepTrace` directly.

---

## Implementation Steps

1. Add reusable synthetic trace builders.
2. Keep fixtures small and explicit.
3. Prefer direct hand-constructed traces over full system execution.
4. Cover every spec-critical edge case with deterministic values.

---

## Verification

1. Comparison logic is covered by deterministic tests.
2. Spec edge cases can be reproduced without relying on experiment artifacts.

---

## Files Created

- `tests/framework/comparison/fixtures.py`

## Files Modified

- multiple comparison test files under `tests/framework/comparison/`

## Files Deleted

None.
