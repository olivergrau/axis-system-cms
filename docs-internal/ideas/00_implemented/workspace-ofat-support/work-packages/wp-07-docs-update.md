# WP-07 Docs Update

## Goal

Update public and internal documentation to match the bounded Workspace OFAT
support that is actually implemented.

## Why This Package Exists

Current manuals still describe Workspaces as `single_run`-only.

This will become incorrect once OFAT is supported for:

- `investigation / single_system`

The docs must explain both the new supported path and the remaining limits.

## Scope

### Update the public workspace manual

Revise `docs/manuals/workspace-manual.md` so it explains:

- OFAT is allowed only for `investigation / single_system`
- `axis workspaces run` can produce sweep outputs there
- `axis workspaces sweep-result` is the inspection command for sweep outputs
- `show` remains management-only
- workspace compare in `single_system` remains point-vs-point only
- sweep visualization requires explicit run selection

### Update the public overview documentation

Revise `docs/manuals/axis-overview.md` so it reflects:

- Workspaces are no longer globally `single_run`-only
- the allowance is bounded to `single_system`
- `primary_results` may contain both point and sweep outputs

### Keep internal docs aligned

If implementation details shift during coding, update the OFAT support idea docs
to keep the spec, engineering spec, and work packages aligned with reality.

## Files To Change

- `docs/manuals/workspace-manual.md`
- `docs/manuals/axis-overview.md`
- `docs-internal/ideas/workspace-ofat-support/*.md` as needed

## Deliverables

- corrected public manual statements
- new usage examples for sweep-result
- accurate description of point-only compare limits

## Non-Goals

- no new feature design beyond the existing OFAT support spec

## Acceptance Criteria

- public docs no longer claim that all Workspaces are `single_run`-only
- users can understand:
  - where OFAT is allowed
  - how to inspect sweep outputs
  - what remains unsupported
