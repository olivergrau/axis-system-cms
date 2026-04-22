# WP-04: Workspace Output Normalization

**Phase**: 2 -- Command Migration  
**Dependencies**: WP-01, WP-02  
**Scope**: Medium  
**Engineering reference**: Sections 4.2, 8.3, 9

---

## Objective

Refactor workspace-oriented CLI output onto the shared presentation layer.

This WP should make workspace inspection and validation output clearly
structured, especially for long `show` responses and mixed validation/drift
states.

---

## Deliverables

Modify:

- `src/axis/framework/cli/commands/workspaces.py`

Add or update tests:

- workspace CLI output tests under `tests/framework/cli/` and/or
  `tests/framework/workspaces/`

---

## Priority Surfaces

The first migration pass should cover:

- `cmd_workspaces_show`
- `cmd_workspaces_check`
- `cmd_workspaces_comparison_result`
- `cmd_workspaces_sweep_result`
- workspace success/completion messages where they remain plain text

---

## Required Output Shape

The migrated workspace output should support:

- title line
- identity and state block
- overview before deep artifact detail
- grouped artifact sections
- grouped validation findings
- separate drift warnings where applicable

---

## Implementation Steps

1. Normalize `workspaces show` around overview-first rendering.
2. Normalize `workspaces check` around valid / valid-with-warnings / invalid states.
3. Refactor artifact section rendering onto shared helpers.
4. Keep JSON workspace outputs unchanged.
5. Align small workspace success messages with the new semantic wording.

---

## Design Notes

- `workspaces show` should optimize first for “what is the current situation?”
- Do not bury validation state at the bottom as an afterthought if it is materially important.
- Preserve detailed artifact visibility, but tier it below identity and state.

---

## Verification

1. `workspaces show` reads as a sectioned detail view rather than a flat field dump.
2. `workspaces check` distinguishes validity, warnings, and drift clearly.
3. Sweep result output becomes more consistently structured.
4. JSON workspace command output remains unchanged.

---

## Files Created

None required.

## Files Modified

- `src/axis/framework/cli/commands/workspaces.py`
- related CLI/workspace output tests

## Files Deleted

None.

