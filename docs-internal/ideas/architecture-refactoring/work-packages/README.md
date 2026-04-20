# Architecture Refactoring Work Packages

This directory contains the detailed implementation work packages for the AXIS
architecture refactoring program.

These packages derive from:

- [Architecture Refactoring Spec](../architecture-refactoring-spec.md)
- [Architecture Refactoring Engineering Spec](../architecture-refactoring-engineering-spec.md)
- [Architecture Refactoring Work Packages](../architecture-refactoring-work-packages.md)

The packages are written to be implementation-facing and suitable as direct
input for coding agents.

## Package Order

1. `wp-01-cli-package-extraction.md`
2. `wp-03-command-module-extraction.md`
3. `wp-02-manual-composition-root.md`
4. `wp-06-handler-contract-stabilization.md`
5. `wp-07-workspace-service-layer.md`
6. `wp-08-manifest-mutation-layer.md`
7. `wp-04-catalog-registrar-foundations.md`
8. `wp-05-plugin-discovery-catalog-bridge.md`
9. `wp-09-registry-consumer-migration.md`
10. `wp-10-rendering-cleanup.md`
11. `wp-11-tests-and-docs.md`

## Architectural Rule

The refactoring must preserve the external AXIS command surface and external
plugin model while improving internal structure.

In particular:

- the `axis` entrypoint must remain stable
- plugins must continue to expose `register()`
- the composition root must not become a service locator
- business logic must move away from direct dependence on global registries
