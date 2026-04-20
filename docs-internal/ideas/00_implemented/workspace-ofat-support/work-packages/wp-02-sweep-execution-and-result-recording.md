# WP-02 Sweep Execution and Result Recording

## Goal

Ensure that OFAT execution inside a `single_system` workspace produces a proper
workspace-owned sweep result and records it correctly in `workspace.yaml`.

## Why This Package Exists

After validation is relaxed, a valid `single_system + ofat` config must not only
run successfully, it must also integrate cleanly with the Workspace result
model:

- execution artifacts under `results/<experiment-id>/`
- exactly one structured `primary_results` entry for the sweep output
- explicit `output_form = sweep`
- experiment-root result identity

The current execution and sync pipeline is already close, but this package must
verify and harden the exact OFAT semantics.

## Scope

### Confirm OFAT works through normal workspace run

`axis workspaces run <workspace>` must support OFAT in `single_system` with no
special flag.

The command should:

1. resolve the active config
2. execute it through the standard workspace-owned repository under
   `<workspace>/results/`
3. sync one structured result entry for the produced experiment

### Record sweep semantics in the manifest

For each OFAT execution, the synced `primary_results` entry must carry at
minimum:

- `path = results/<experiment-id>`
- `output_form = sweep`
- `system_type`
- `role`
- `baseline_run_id`

If additional fields are already present in the current result entry model,
they should remain coherent.

### Preserve point behavior

This package must not regress existing point execution behavior for:

- `single_system`
- `system_comparison`
- `system_development`

## Files To Change

- `src/axis/framework/cli.py`
- `src/axis/framework/workspaces/execute.py`
- `src/axis/framework/workspaces/sync.py`

Potential verification helpers:

- `src/axis/framework/experiment_output.py`

## Deliverables

- OFAT execution works through workspace-owned mode for `single_system`
- sweep outputs are recorded as one experiment-root result entry
- `workspace.yaml` contains correct sweep metadata after sync

## Non-Goals

- no sweep inspection command yet
- no compare changes yet
- no scaffold changes yet

## Tests

Add or update tests covering:

- `axis workspaces run` on valid `single_system + ofat`
- result artifacts created under `<workspace>/results/<experiment-id>/`
- synced `primary_results` entry uses experiment-root path
- synced entry has `output_form = sweep`
- synced entry has `baseline_run_id`

Suggested primary test targets:

- `tests/framework/workspaces/test_integration.py`

## Acceptance Criteria

- OFAT execution in `single_system` produces a workspace-local sweep output
- each sweep appears as exactly one `primary_results` entry
- point execution semantics remain unchanged
