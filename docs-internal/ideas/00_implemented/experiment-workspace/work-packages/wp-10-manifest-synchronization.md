# WP-10: Manifest Synchronization

**Phase**: 4 -- Workspace State Management  
**Dependencies**: WP-06, WP-09  
**Scope**: Medium  
**Spec reference**: Sections 11, 17  
**Engineering reference**: Sections 4.5, 9.4

---

## Objective

Keep `workspace.yaml` aligned with artifacts produced by workspace-aware run
and compare commands.

This WP is essential because the workspace manifest is authoritative.

---

## Deliverables

Create:

- `src/axis/framework/workspaces/sync.py`
- `tests/framework/workspaces/test_sync.py`

Modify:

- `src/axis/framework/workspaces/execute.py`
- `src/axis/framework/workspaces/compare.py`
- `src/axis/framework/workspaces/__init__.py`

---

## Required Behavior

Support controlled manifest updates after:

- workspace-aware execution
- workspace-aware comparison

At minimum support:

- updating `primary_results`
- updating `primary_comparisons`
- preserving existing non-overwritten manifest fields

---

## Implementation Steps

1. Define manifest update helpers in `sync.py`.
2. Decide update rules for appending vs replacing `primary_*` fields.
3. Integrate those rules into workspace execution and comparison flows.
4. Keep updates explicit and deterministic.

Use:

- `ruamel.yaml` for write paths that must preserve readability of `workspace.yaml`

---

## Design Notes

- Do not silently mutate unrelated manifest fields.
- Avoid generic arbitrary YAML rewriting; work through the typed manifest model.
- If update policy is ambiguous, fail explicitly rather than guessing.
- Do not use plain `PyYAML` for writeback in this WP; it does not preserve comments and formatting adequately for workspace manifests.

---

## Verification

1. Workspace-aware run updates `primary_results` correctly.
2. Workspace-aware compare updates `primary_comparisons` correctly.
3. Existing manifest metadata is preserved.
4. Manifest remains valid after synchronization.

---

## Files Created

- `src/axis/framework/workspaces/sync.py`
- `tests/framework/workspaces/test_sync.py`

## Files Modified

- `src/axis/framework/workspaces/execute.py`
- `src/axis/framework/workspaces/compare.py`
- `src/axis/framework/workspaces/__init__.py`

## Files Deleted

None.
