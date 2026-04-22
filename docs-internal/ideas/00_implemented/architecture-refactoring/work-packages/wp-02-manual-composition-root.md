# WP-02 Manual Composition Root and Context Builder

## Goal

Introduce explicit manual composition at the framework entry boundary.

## Why This Package Exists

The refactoring direction requires explicit composition from the start, and the
current system still constructs most high-level collaborators concretely in
top-level flows.

Without an early composition root, later service extraction would only recreate
construction logic in a different form.

## Scope

### Define a composition root

The composition root should live in the refactored CLI entry layer and assemble
the high-level application context.

It should expose a helper such as:

- `_build_context()`

It should assemble:

- repositories or repository factories
- workspace services
- manifest mutators
- output helpers
- rendering helpers where appropriate

Catalogs / registrars are not part of the initial `WP-02` deliverable. The
composition root should simply be structured so those dependencies can be added
later in the catalog wave without another architectural reset.

### Enforce edge-only composition

The package should establish the rule that:

- composition happens at the edge
- services receive dependencies through constructors
- no service-locator behavior appears inside domain/workflow logic

## Files To Change

- new CLI package composition modules

Potential new files:

- `src/axis/framework/cli/composition.py`
- `src/axis/framework/cli/context.py`

## Deliverables

- explicit composition root exists
- services can be built from the shared application context

## Non-Goals

- not all services must exist yet
- plugin/catalo‌g integration can still be partial at this stage

## Tests

Add or update tests covering:

- context can be built without command execution
- core services can be constructed from the context
- command entry still works

## Acceptance Criteria

- AXIS has an explicit composition root / `_build_context()` boundary
- constructor injection is established as the framework direction
