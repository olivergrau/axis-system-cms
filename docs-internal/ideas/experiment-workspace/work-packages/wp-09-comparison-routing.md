# WP-09: Workspace Comparison Routing

**Phase**: 3 -- Workspace Compare  
**Dependencies**: WP-08  
**Scope**: Medium  
**Engineering reference**: Sections 4.5, 9.4

---

## Objective

Implement workspace-aware comparison output placement under `comparisons/`.

This WP introduces the actual workspace comparison flow while reusing the
existing comparison package under `framework/comparison/`.

---

## Deliverables

Create:

- `src/axis/framework/workspaces/compare.py`
- `tests/framework/workspaces/test_compare.py`

Modify:

- `src/axis/framework/cli.py`
- `src/axis/framework/workspaces/__init__.py`

---

## Required Behavior

Implement:

- `axis workspaces compare <workspace-path>`
- delegation from CLI into `framework/workspaces/compare.py`
- use of the comparison plan from WP-08
- structured placement of comparison artifacts under `comparisons/`

The CLI remains a delegator only.

---

## Implementation Steps

1. Define a workspace comparison service in `compare.py`.
2. Resolve comparison inputs via WP-08.
3. Invoke the existing comparison entrypoints under `framework/comparison/`.
4. Persist comparison outputs under `comparisons/`.
5. Return a structured comparison result to the CLI.

---

## Design Notes

- Do not reimplement comparison metrics here.
- Support existing system-specific comparison extensions automatically via the comparison package.
- Keep artifact naming simple and deterministic.

---

## Verification

1. `axis workspaces compare <workspace-path>` can compare a `system_comparison` workspace.
2. Comparison outputs are written under `comparisons/`.
3. Existing `axis compare ...` remains unchanged.
4. System-specific extensions still appear in workspace comparison results.

---

## Files Created

- `src/axis/framework/workspaces/compare.py`
- `tests/framework/workspaces/test_compare.py`

## Files Modified

- `src/axis/framework/cli.py`
- `src/axis/framework/workspaces/__init__.py`

## Files Deleted

None.
