# WP-12: Integration Hardening

**Phase**: 5 -- Stability Pass  
**Dependencies**: WP-01 through WP-11  
**Scope**: Medium  
**Engineering reference**: Section 13

---

## Objective

Harden workspace support against real repository usage and CLI behavior.

This WP focuses on integration quality rather than new features.

---

## Deliverables

Create:

- `tests/framework/workspaces/test_cli_integration.py`
- `tests/framework/workspaces/test_end_to_end.py`

Modify as needed:

- `src/axis/framework/cli.py`
- `src/axis/framework/workspaces/*.py`

---

## Required Hardening Areas

Cover:

- CLI error reporting
- invalid workspace path handling
- invalid manifest handling
- partial artifact states
- compatibility with old `axis experiments run <config>` flow
- compatibility with old `axis compare ...` flow
- compatibility with old `axis visualize --experiment ... --run ... --episode ...` flow

---

## Implementation Steps

1. Add end-to-end tests for scaffold/check/show/run/compare/visualize.
2. Add CLI failure-path tests.
3. Add compatibility tests proving old command paths still work.
4. Review and improve error messages for common failure cases.

---

## Design Notes

- This WP should not add new user-facing concepts unless absolutely necessary.
- Stabilize behavior before public documentation is written.
- Keep tests deterministic and filesystem-local.

---

## Verification

1. Workspace commands behave consistently end-to-end.
2. Failure cases produce readable diagnostics.
3. Existing non-workspace AXIS commands remain unaffected.

---

## Files Created

- `tests/framework/workspaces/test_cli_integration.py`
- `tests/framework/workspaces/test_end_to_end.py`

## Files Modified

- `src/axis/framework/cli.py`
- `src/axis/framework/workspaces/*.py`

## Files Deleted

None.
