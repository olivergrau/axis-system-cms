# Experiment Output Abstraction Work Packages

This directory contains the detailed implementation work packages for the
framework-level **Experiment Output** refactoring.

These packages derive from:

- [Experiment Output Abstraction Spec](../experiment-output-abstraction-spec.md)
- [Experiment Output Abstraction Engineering Spec](../experiment-output-abstraction-engineering-spec.md)
- [Experiment Output Abstraction Work Packages](../experiment-output-abstraction-work-packages.md)

The packages are written to be implementation-facing and suitable as direct
input for coding agents.

## Package Order

1. `wp-01-persisted-output-semantics.md`
2. `wp-02-core-experiment-output-module.md`
3. `wp-03-cli-inspection-migration.md`
4. `wp-04-workspace-result-identity-refactor.md`
5. `wp-05-workspace-execution-sync-update.md`
6. `wp-06-output-aware-comparison-resolution.md`
7. `wp-07-output-aware-visualization-resolution.md`
8. `wp-08-workspace-handler-alignment.md`
9. `wp-09-validation-and-drift-detection.md`
10. `wp-10-test-migration-and-coverage.md`
11. `wp-11-docs-update.md`

## Architectural Rule

The `axis` CLI remains a delegator.

Business logic for experiment outputs belongs in framework modules, primarily:

- `src/axis/framework/experiment_output.py`
- existing framework persistence / experiment modules
- existing workspace modules where Workspace-specific interpretation is needed

No logic should be introduced into the CLI that properly belongs in the
framework layer.
