# WP-04 Catalog / Registrar Foundations

## Goal

Introduce explicit infrastructure catalogs for plugin-provided capabilities.

## Why This Package Exists

The current plugin-backed registries are global module state:

- systems
- worlds
- world visualization adapters
- system visualization adapters
- comparison extensions

This is workable today, but it is not the right long-term dependency boundary
for composition-driven services.

It is also not the first implementation wave.

The first step is not to delete the registries.

The first step is to introduce explicit catalog / registrar abstractions that
can become the injected dependency boundary.

## Scope

### Define initial catalog abstractions

Introduce explicit infrastructure objects for:

- system factories
- world factories
- world visualization adapters
- system visualization adapters
- comparison extensions

### Keep the current registry modules operational

The current registry modules may remain behind adapters during this wave.

The immediate objective is to establish the new abstraction boundary, not to
fully delete the old registry modules.

This package should start only after:

- CLI/package extraction
- command module extraction
- manual composition root introduction
- first workspace service boundaries

### Separate registration-side and consumption-side concerns where useful

Registrar types may be introduced where they improve clarity, but they are not
mandatory for every category in the first wave.

## Files To Change

- `src/axis/framework/registry.py`
- `src/axis/world/registry.py`
- `src/axis/visualization/registry.py`
- `src/axis/framework/comparison/extensions.py`

Potential new files:

- `src/axis/framework/catalogs.py`
- `src/axis/framework/registrars.py`

## Deliverables

- explicit catalogs or catalog-like abstractions exist
- they are suitable for DI registration
- current global registries remain bridgeable

## Non-Goals

- complete elimination of old registry modules
- forcing local runtime registries like `ActionRegistry` into this abstraction

## Tests

Add/update tests covering:

- catalog lookup behavior
- duplicate registration behavior
- preservation of the split between world and system visualization lookup
- compatibility with existing registry expectations

## Acceptance Criteria

- there is now a composition-friendly infrastructure abstraction for
  plugin-provided
  capabilities
