# WP-11 Tests and Docs

## Goal

Update regression coverage and internal documentation to support the refactored
architecture.

## Why This Package Exists

This refactoring changes structural boundaries more than end-user behavior.

That means the main risk is not obvious feature regression alone, but
architectural drift:

- command logic drifting back into the wrong layer
- services bypassing DI rules
- business logic continuing to consume global registries directly

Tests and docs must lock in the intended architecture.

This package is not the place where test updates first appear.

Each preceding work package must carry its own regression coverage updates.
This package exists for cross-cutting cleanup, gap-filling, and final
documentation alignment.

## Scope

### Testing

Add/update tests for:

- CLI entrypoint compatibility
- composition-root / context-building behavior
- catalog/registrar population
- plugin discovery preservation
- workspace service behavior
- behavior-preserving command execution

### Documentation

Update internal docs to reflect:

- final CLI package direction
- DI usage rules
- catalog/registrar boundaries
- manifest mutation responsibilities

## Files To Change

- `tests/framework/`
- `tests/framework/workspaces/`
- `docs-internal/ideas/architecture-refactoring/`

Potential public docs only if command behavior or contributor-facing extension
mechanics need explanation.

## Deliverables

- regression coverage for the refactoring boundary
- internal architecture docs aligned to implemented structure

## Non-Goals

- no user-facing feature design changes

## Acceptance Criteria

- architectural intent is preserved by tests and documentation
- future contributors can follow the new boundaries without reverse-engineering
  the refactoring from code alone
- no major work package depends on deferring all of its test updates into this
  final package
