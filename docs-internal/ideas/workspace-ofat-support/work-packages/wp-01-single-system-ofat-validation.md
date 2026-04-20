# WP-01 Single-System OFAT Validation

## Goal

Relax the current global Workspace experiment-type guardrail so OFAT is allowed
only for `investigation / single_system`.

## Why This Package Exists

The current code still blocks OFAT for every workspace type:

- `src/axis/framework/workspaces/validation.py`
  - `check_config_experiment_types(...)` currently rejects every config whose
    `experiment_type != "single_run"`
- `src/axis/framework/workspaces/execute.py`
  - calls that validation before execution and therefore blocks valid
    `single_system + ofat` runs

This is the first hard blocker for Workspace OFAT support.

## Scope

### Make validation workspace-type-aware

Refine config-type validation so it depends on the manifest's workspace type.

Required behavior:

- `single_system`
  - allow `single_run`
  - allow `ofat`
- `system_comparison`
  - allow `single_run` only
- `system_development`
  - allow `single_run` only

### Preserve precise failure semantics

When OFAT is used in an unsupported workspace type, validation must fail with a
clear, direct message naming:

- the config path
- the detected `experiment_type`
- the workspace type restriction

### Keep framework OFAT validation in force

This package should not reimplement OFAT config validation.

Workspace validation should only decide whether OFAT is allowed in the current
workspace type. Normal config validation remains the source of truth for:

- `parameter_path`
- `parameter_values`
- other OFAT-specific config invariants

## Files To Change

- `src/axis/framework/workspaces/validation.py`
- `src/axis/framework/workspaces/execute.py`

Likely test updates:

- `tests/framework/workspaces/test_validation.py`
- `tests/framework/workspaces/test_integration.py`

## Deliverables

- workspace-type-aware experiment-type validation
- execution no longer blocks valid OFAT configs in `single_system`
- continued rejection of OFAT in all other workspace types

## Non-Goals

- no new command yet
- no compare behavior changes yet
- no scaffold enhancements yet

## Tests

Add or update tests covering:

- valid `single_system + ofat` passes `check_workspace(...)`
- `system_comparison + ofat` fails validation
- `system_development + ofat` fails validation
- `execute_workspace(...)` no longer fails early for valid
  `single_system + ofat`

## Acceptance Criteria

- valid OFAT configs are accepted only for `workspace_type = single_system`
- all other workspace types remain `single_run`-only
- failure messages remain explicit and precise
