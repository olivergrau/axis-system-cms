# WP-09 Registry Consumer Migration

## Goal

Migrate high-level framework logic from direct global-registry consumption to
catalog-driven dependencies.

## Why This Package Exists

Introducing catalogs only helps if business logic actually consumes them.

Today key framework paths still depend directly on global registries:

- `run.py` uses system creation helpers
- `runner.py` uses world creation helpers
- `visualization/launch.py` resolves adapters from the visualization registry
- `comparison/compare.py` dispatches extensions via the comparison extension
  registry

This package migrates those edges to the new dependency model.

## Scope

### Migrate system/world consumption

Replace direct use of global registry helpers in high-level execution paths with
catalog-driven dependencies where appropriate.

### Migrate visualization adapter resolution

Move visualization launch away from direct registry access and toward injected
adapter catalogs or equivalent abstractions.

### Migrate comparison extension dispatch

Move comparison extension consumption toward an injected extension catalog.

### Leave local runtime registries alone

This package should not absorb:

- `ActionRegistry`

unless a concrete problem appears.

## Files To Change

- `src/axis/framework/run.py`
- `src/axis/framework/runner.py`
- `src/axis/visualization/launch.py`
- `src/axis/framework/comparison/compare.py`

Potential catalog modules as collaborators.

## Deliverables

- business logic depends on injected catalogs more than direct global registries
- plugin/registry/DI alignment becomes real rather than only conceptual

## Non-Goals

- full elimination of old registry modules in one step

## Tests

Add/update tests covering:

- system creation still works
- world creation still works
- visualization adapter resolution still works
- comparison extensions still dispatch correctly

## Acceptance Criteria

- high-level business logic has begun moving off direct global-registry imports
  toward explicit catalog dependencies
