# Workspace OFAT Support Work Packages

This directory contains the detailed implementation work packages for bounded
OFAT support in AXIS Experiment Workspaces.

These packages derive from:

- [Workspace OFAT Support Spec](../workspace-ofat-support-spec.md)
- [Workspace OFAT Support Engineering Spec](../workspace-ofat-support-engineering-spec.md)
- [Workspace OFAT Support Work Packages](../workspace-ofat-support-work-packages.md)

The packages are written to be implementation-facing and suitable as direct
input for coding agents.

## Package Order

1. `wp-01-single-system-ofat-validation.md`
2. `wp-02-sweep-execution-and-result-recording.md`
3. `wp-03-sweep-result-command.md`
4. `wp-04-single-system-compare-refinement.md`
5. `wp-05-optional-ofat-starter-scaffolding.md`
6. `wp-06-test-coverage-and-hardening.md`
7. `wp-07-docs-update.md`

## Architectural Rule

The `axis` CLI remains a delegator.

Business logic for Workspace OFAT support belongs in framework modules,
primarily:

- `src/axis/framework/workspaces/validation.py`
- `src/axis/framework/workspaces/execute.py`
- `src/axis/framework/workspaces/compare_resolution.py`
- `src/axis/framework/workspaces/visualization.py`
- `src/axis/framework/workspaces/sweep_result.py` (new)

No business logic should be introduced into the CLI that properly belongs in
the framework layer.
