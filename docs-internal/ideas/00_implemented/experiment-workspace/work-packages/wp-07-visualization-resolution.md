# WP-07: Workspace Visualization Resolution

**Phase**: 3 -- Replay Resolution  
**Dependencies**: WP-01, WP-06  
**Scope**: Small  
**Engineering reference**: implied by workspace-aware usage flows

---

## Objective

Resolve replay targets from workspace state so visualization can operate on
workspace-owned artifacts.

This WP supports command shapes such as:

- `axis visualize --workspace <workspace-path> --episode 1`
- `axis visualize --workspace <workspace-path> --role reference --episode 1`

---

## Deliverables

Create:

- `src/axis/framework/workspaces/visualization.py`
- `tests/framework/workspaces/test_visualization_resolution.py`

Modify:

- `src/axis/framework/cli.py`
- `src/axis/framework/workspaces/__init__.py`

---

## Required Behavior

Support:

- replay resolution for `single_system`
- replay resolution for `system_comparison`
- role selection for reference/candidate sides
- default artifact selection rules

This WP is resolution-focused. It should adapt the existing visualization
entrypoints rather than reimplement the viewer.

---

## Implementation Steps

1. Resolve workspace-local execution artifacts suitable for replay.
2. Define role selection behavior for comparison workspaces.
3. Adapt CLI argument parsing so `axis visualize` can accept a workspace mode.
4. Delegate to existing visualization infrastructure once the target artifact is resolved.

---

## Design Notes

- Keep the viewer itself unchanged.
- Reuse existing replay access and visualization entrypoints.
- Fail explicitly if the workspace is not replay-ready.

---

## Verification

1. A `single_system` workspace can resolve a replay target.
2. A `system_comparison` workspace can resolve replay targets by role.
3. Existing non-workspace visualization still works unchanged.

---

## Files Created

- `src/axis/framework/workspaces/visualization.py`
- `tests/framework/workspaces/test_visualization_resolution.py`

## Files Modified

- `src/axis/framework/cli.py`
- `src/axis/framework/workspaces/__init__.py`

## Files Deleted

None.
