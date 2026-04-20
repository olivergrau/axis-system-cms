# WP-05 Plugin Discovery Catalog Bridge

## Goal

Preserve the external plugin story while routing plugin-provided capabilities
toward catalogs / registrars that fit the DI model.

## Why This Package Exists

AXIS already has a usable external plugin story:

- entry points
- `axis-plugins.yaml`
- plugin-local `register()`

That should not be broken.

But if DI is introduced without adapting plugin registration, the system will
accumulate two separate composition systems:

- plugin-driven global registries
- composition-root-driven services

This package provides the bridge.

This bridge should begin only after the first manual composition root exists
and the initial catalog abstractions are already defined.

## Scope

### Preserve plugin discovery behavior

The current discovery flow in `src/axis/plugins.py` must remain externally
usable.

### Preserve plugin `register()` entrypoints

Plugins should continue to expose `register()` from the user/plugin author
perspective.

### Bridge discovery into catalogs / registrars

The composition root should be able to:

1. trigger plugin discovery
2. populate catalogs / registrars
3. expose those catalogs through the shared application context

### Avoid direct plugin-to-composition-root mutation

Plugins must not directly mutate the composition root or shared application
context.

## Files To Change

- `src/axis/plugins.py`
- plugin registration modules under:
  - `src/axis/systems/*/__init__.py`
  - `src/axis/world/*/__init__.py`
- potentially visualization registration paths as well

## Deliverables

- discovery still works
- plugin registration still works
- catalogs/registrars are populated through the discovery process

## Non-Goals

- complete redesign of plugin authoring API

## Tests

Add/update tests covering:

- entry-point discovery behavior
- YAML plugin loading behavior
- registration still occurs exactly once
- discovered capabilities appear in catalogs

## Acceptance Criteria

- external plugin behavior is preserved
- internal composition is now compatible with explicit catalogs
