# WP-07 Workspace Service Layer

## Goal

Introduce explicit workspace use-case services and move workflow orchestration
onto them.

## Why This Package Exists

Workspace workflows are currently split across:

- CLI handlers
- resolution helpers
- compare resolution
- sync logic
- summary helpers
- handler-specific behavior

This is manageable now, but it is an obvious scaling seam.

The workspace subsystem is the best first place to introduce explicit
application services.

## Scope

### Introduce a service package

Add:

- `src/axis/framework/workspaces/services/`

### Introduce first service classes

Initial target services:

- `WorkspaceRunService`
- `WorkspaceCompareService`
- `WorkspaceInspectionService`

The inspection service scope should explicitly include the workspace
`sweep-result` flow currently implemented in:

- `src/axis/framework/workspaces/sweep_result.py`

### Move orchestration into services

These services should coordinate:

- resolution
- validation
- execution
- sync
- summary/inspection helpers
- sweep-result helpers
- `experiment_output.py` loading and output-aware result interpretation

### Wire services through constructor injection

These services should become first-class consumers of constructor-injected
collaborators built from the shared application context.

## Files To Change

- new `src/axis/framework/workspaces/services/`
- CLI workspace command module
- existing workspace helper modules as collaborators

## Deliverables

- first explicit workflow service layer
- less workflow knowledge in command modules
- workspace orchestration boundaries become clearer
- workspace services explicitly depend on `load_experiment_output(...)` where
  output-aware workflow decisions are required
- sweep-result inspection becomes part of the explicit workspace service
  orchestration boundary

## Non-Goals

- do not rewrite every workspace helper into a class immediately

## Tests

Add/update tests covering:

- run workflow through service layer
- compare workflow through service layer
- inspection workflow through service layer
- sweep-result workflow through service layer where introduced in this wave
- output-aware service behavior for point/sweep-aware workspace flows where
  applicable

## Acceptance Criteria

- workspace use cases are coordinated through service classes rather than
  scattered helper orchestration
