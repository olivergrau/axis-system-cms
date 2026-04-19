# WP-11 Docs Update

## Goal

Update public and internal documentation so it reflects the new Experiment
Output model and the resulting workspace semantics.

## Why This Package Exists

Current docs still describe:

- experiment inspection in raw artifact terms
- workspace result identity in a way that was historically run-shaped
- OFAT mainly as a direct experiment concern, not yet in terms of point vs
  sweep outputs

The refactor changes the framework’s conceptual language and should be visible
in docs.

## Scope

### Public docs

Update:

- `docs/manuals/axis-overview.md`
- `docs/manuals/cli-manual.md`
- `docs/manuals/workspace-manual.md`

Topics:

- experiment outputs as point vs sweep
- output-aware experiment inspection
- structured `primary_results`
- experiment-root result identity
- explicit unsupported sweep cases in workspace compare/visualize

### Internal docs

Update internal spec threads if implementation details diverged.

## Deliverables

- manuals aligned with the new output model
- terminology consistency across framework and workspace docs

## Acceptance Criteria

- public docs describe the same semantic model the code now implements
- no user-facing manual still implies that workspace primary results are run-path identities
