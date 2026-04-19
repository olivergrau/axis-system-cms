# WP-01: Workspace Manifest Model

**Phase**: 1 -- Workspace Foundation  
**Dependencies**: None  
**Scope**: Medium  
**Spec reference**: Sections 7, 8, 9, 10, 11, 16, 18

---

## Objective

Create the typed representation of `workspace.yaml`.

This model is the foundation for:

- workspace loading
- workspace validation
- scaffolding
- summary rendering
- workspace-aware execution and comparison flows

The intent is to avoid raw untyped dictionaries as the primary
representation of workspace state.

---

## Deliverables

Create:

- `src/axis/framework/workspaces/__init__.py`
- `src/axis/framework/workspaces/types.py`
- `tests/framework/workspaces/__init__.py`
- `tests/framework/workspaces/test_types.py`

No SDK changes are expected in this WP.

---

## Required Models

At minimum define:

- `WorkspaceClass`
- `WorkspaceType`
- `WorkspaceStatus`
- `WorkspaceLifecycleStage`
- `ArtifactKind`
- `LinkedArtifactRef`
- `WorkspaceManifest`

The manifest model should include:

- required core fields
- type-specific required fields
- optional `primary_*` fields
- optional `linked_*` fields

Use frozen Pydantic models, following existing AXIS conventions.

---

## Implementation Steps

1. Create `framework/workspaces/__init__.py` with public exports.
2. Implement `types.py` with enums and manifest model only. No IO or CLI logic.
3. Encode valid class/type combinations inside the model layer.
4. Encode type-specific required fields:
   - `question` for investigation
   - `development_goal` for development
   - `system_under_test` for `single_system`
   - `reference_system` and `candidate_system` for `system_comparison`
   - `artifact_kind` and `artifact_under_development` for development types
5. Treat `primary_*` and `linked_*` as optional tuple/list fields.
6. Keep path-like fields as strings for now; do not resolve them in this WP.

---

## Design Notes

- Keep the model names close to the spec terms.
- Put all workspace typing in `framework/workspaces/types.py`.
- Do not create an SDK contract unless a later WP proves it is necessary.
- Validation should fail early on invalid class/type combinations.

---

## Verification

1. A valid `single_system` manifest can be instantiated.
2. A valid `system_comparison` manifest can be instantiated.
3. A valid `system_development` manifest can be instantiated.
4. Invalid class/type combinations fail validation.
5. Missing type-specific required fields fail validation.
6. Models are frozen and reject mutation.

---

## Files Created

- `src/axis/framework/workspaces/__init__.py`
- `src/axis/framework/workspaces/types.py`
- `tests/framework/workspaces/__init__.py`
- `tests/framework/workspaces/test_types.py`

## Files Modified

None.

## Files Deleted

None.
