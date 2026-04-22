# WP-03: CLI Close Command Integration

**Phase**: 3 -- CLI surface  
**Dependencies**: WP-02  
**Scope**: Small  
**Engineering reference**: Sections 6, 11, 13

---

## Objective

Expose workspace closing as a first-class CLI operation.

This WP should make `axis workspaces close <workspace-path>` available in both
text and JSON output modes.

---

## Deliverables

Modify:

- `src/axis/framework/cli/parser.py`
- `src/axis/framework/cli/commands/workspaces.py`
- `src/axis/framework/cli/context.py`

Add or update tests in:

- `tests/framework/test_cli_parser.py`
- `tests/framework/test_cli_output.py`
- service/context tests if needed

---

## Required Capabilities

At minimum:

- parser recognizes `workspaces close`
- CLI context wires the workflow service
- command delegates to the workflow service
- text mode confirms closure clearly
- JSON mode returns structured confirmation

---

## Implementation Steps

1. Add the `close` subcommand to the workspace parser.
2. Wire workflow service construction into CLI context.
3. Add `cmd_workspaces_close(...)`.
4. Keep the command thin: call service, format response.
5. Add parser and output tests.

---

## Design Notes

- Match the existing workspace command style.
- Keep text output concise and explicit about the new workflow state.
- Do not add reopen or generic editing commands in this WP.

---

## Verification

1. `axis workspaces close <workspace>` parses successfully.
2. Text mode shows the workspace is now closed/final.
3. JSON mode returns machine-readable workflow state data.

---

## Files Modified

- `src/axis/framework/cli/parser.py`
- `src/axis/framework/cli/commands/workspaces.py`
- `src/axis/framework/cli/context.py`
- parser / CLI output tests

## Files Deleted

None.
