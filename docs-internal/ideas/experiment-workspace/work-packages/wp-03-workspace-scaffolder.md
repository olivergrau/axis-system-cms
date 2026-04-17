# WP-03: Workspace Scaffolder

**Phase**: 1 -- Workspace Creation  
**Dependencies**: WP-01  
**Scope**: Medium  
**Spec reference**: Sections 12, 14, 15  
**Engineering reference**: Sections 4.1, 6

---

## Objective

Implement interactive creation of valid initial workspaces.

The scaffolder should turn the workspace spec into a practical starting point.

---

## Deliverables

Create:

- `src/axis/framework/workspaces/scaffold.py`
- `tests/framework/workspaces/test_scaffold.py`

Modify later in CLI WP:

- `src/axis/framework/cli.py`

---

## Required Behavior

The scaffolder must:

- create the required directory tree
- create `workspace.yaml`
- create `README.md`
- create `notes.md`
- create required type-specific directories
- create initial executable config files

For config generation:

- `single_system` and development workspaces get at least one baseline config
- `system_comparison` gets at least two executable configs

---

## Implementation Steps

1. Define a non-CLI scaffolding API that accepts typed scaffold input.
2. Create the directory tree according to workspace type.
3. Generate an initial `workspace.yaml` from the typed manifest model.
4. Create placeholder markdown artifacts.
5. Create initial configs using existing AXIS config shapes.
6. Keep generated contents minimal but valid.

Interactive prompt handling belongs to the CLI layer, but the logic that
builds the workspace contents belongs here.

---

## Design Notes

- Keep the scaffolder idempotence rules simple:
  - fail if target path already exists unless later WPs define overwrite flags
- Do not embed terminal prompt logic in this module.
- Use framework-side helper functions to render default file contents.

---

## Verification

1. The scaffolder can create a valid `single_system` workspace.
2. The scaffolder can create a valid `system_comparison` workspace.
3. The scaffolder can create a valid `system_development` workspace.
4. Generated workspaces pass the checker from WP-02.
5. Generated configs are structurally valid AXIS configs.

---

## Files Created

- `src/axis/framework/workspaces/scaffold.py`
- `tests/framework/workspaces/test_scaffold.py`

## Files Modified

None in this WP.

## Files Deleted

None.
