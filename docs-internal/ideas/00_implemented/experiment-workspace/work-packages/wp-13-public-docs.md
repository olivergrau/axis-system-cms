# WP-13: Public Documentation and Examples

**Phase**: 5 -- Documentation Pass  
**Dependencies**: WP-12  
**Scope**: Small

---

## Objective

Publish stable public documentation for workspace support once the
implementation is hardened.

This WP should not start before command behavior and artifact placement are
stable enough to document confidently.

---

## Deliverables

Modify and/or create:

- public CLI docs under `docs/`
- workspace usage guides
- examples aligned with the implemented command behavior

Add tests only if the repository already validates docs examples structurally.

---

## Required Documentation Areas

Document:

- what a workspace is
- when to use workspace mode vs direct config-path mode
- `axis workspaces scaffold`
- `axis workspaces check`
- `axis workspaces show`
- `axis workspaces run`
- `axis workspaces compare`
- workspace-aware visualization if implemented publicly
- expected artifact placement under `results/`, `comparisons/`, and `measurements/`

---

## Implementation Steps

1. Review the final implemented command shapes.
2. Update or create public docs under `docs/`.
3. Add one or more example workspaces aligned with the real implementation.
4. Ensure examples no longer describe speculative command behavior.

---

## Design Notes

- Public docs should describe implemented behavior only.
- Keep internal idea/draft/spec docs separate from public usage docs.
- Do not document unstable placeholder artifact naming.

---

## Verification

1. Public docs match implemented CLI commands.
2. Public examples match real workspace behavior.
3. Docs distinguish workspace mode from the legacy direct config-path mode.

---

## Files Created

TBD, based on final public doc placement.

## Files Modified

TBD, based on final public doc placement.

## Files Deleted

None.
