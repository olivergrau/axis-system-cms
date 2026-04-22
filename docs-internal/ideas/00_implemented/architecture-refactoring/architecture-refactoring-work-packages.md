# Architecture Refactoring Work Packages

## Purpose

This document provides a first coarse implementation roadmap for the AXIS
architecture refactoring described in:

- [Architecture Refactoring Spec](./architecture-refactoring-spec.md)
- [Architecture Refactoring Engineering Spec](./architecture-refactoring-engineering-spec.md)

The packages below are intentionally still broad. Their purpose is to define a
clear delivery sequence before detailed implementation packages are written.


## Current Code Reality

The current codebase already has a sound domain layering, but the architectural
pressure points are concentrated at the framework edges:

- `src/axis/framework/cli.py` is still monolithic
- workspace orchestration is spread across helper modules and CLI handlers
- plugin-backed registries are global and side-effect-based
- manifest synchronization already carries business semantics
- handler contracts are not fully explicit

At the same time, the core domain/persistence layers are not the first
refactoring target:

- `experiment.py`
- `persistence.py`
- `experiment_output.py`
- `comparison/*`


## Delivery Strategy

The refactoring should proceed in five layers:

1. **CLI and composition root**
   Extract the CLI into a package, extract command modules, and introduce the
   manual composition entry boundary.
2. **Workflow structure**
   Stabilize handler contracts and introduce workspace service classes.
3. **Manifest and output structure**
   Introduce output-aware workspace orchestration and manifest mutation
   structure.
4. **Catalog / registry adaptation**
   Introduce composition-friendly catalogs while preserving external plugin
   behavior.
5. **Hardening**
   Migrate remaining registry consumers, shrink residual command logic, and
   update tests/docs continuously during the program.


## Work Packages

### WP-01: CLI Package Extraction and Entrypoint Compatibility

Split the monolithic CLI into a package while preserving the current script
entrypoint.

Scope:

- replace single-module CLI structure with `framework/cli/`
- introduce:
  - parser module
  - dispatch module
  - command package
- preserve `axis.framework.cli:main` compatibility
- keep command behavior stable while moving structure

Primary files:

- `src/axis/framework/cli.py` or replacement package boundary
- `pyproject.toml`


### WP-02: Manual Composition Root and Context Builder

Introduce an explicit manual composition root after the CLI/package split and
initial command extraction.

Scope:

- define the composition root in the CLI entry layer
- introduce a `_build_context()`-style function
- wire core framework services and infrastructure there
- enforce constructor-based dependency injection
- keep composition at the edges only

Primary files:

- new CLI package modules


### WP-03: Initial Command Module Extraction

Move command implementations out of the monolithic CLI file into grouped command
modules.

Scope:

- experiments commands
- runs commands
- compare commands
- visualize commands
- workspace commands
- rendering moves with command handlers
- business logic does not move into command modules

Primary files:

- `src/axis/framework/cli/commands/*.py`


### WP-04: Catalog / Registrar Foundations

Introduce composition-friendly infrastructure catalogs for plugin-provided
capabilities.

Scope:

- define initial catalog abstractions for:
  - systems
  - worlds
  - world visualization adapters
  - system visualization adapters
  - comparison extensions
- allow current global registries to remain temporarily behind adapters
- establish registrar direction where useful

Primary files:

- `src/axis/framework/registry.py`
- `src/axis/world/registry.py`
- `src/axis/visualization/registry.py`
- `src/axis/framework/comparison/extensions.py`


### WP-05: Plugin Discovery to Catalog Bridge

Refactor plugin discovery so it remains externally stable but populates
composition-friendly catalogs.

Scope:

- keep entry-point / YAML plugin discovery behavior
- preserve plugin-local `register()` model
- bridge discovered plugin capabilities into catalogs/registrars
- avoid direct plugin-to-composition-root mutation

Primary files:

- `src/axis/plugins.py`
- plugin registration modules under:
  - `src/axis/systems/*/__init__.py`
  - `src/axis/world/*/__init__.py`


### WP-06: Handler Contract Stabilization

Make workspace handler interfaces explicit and remove reflective behavior.

Scope:

- stabilize handler method signatures
- remove `inspect.signature(...)`-based branching
- make run-target resolution contract explicit
- keep current handler-based extensibility

Primary files:

- `src/axis/framework/workspaces/handler.py`
- `src/axis/framework/workspaces/resolution.py`
- workspace handler implementations


### WP-07: Workspace Service Layer

Introduce explicit workspace use-case services and move workflow coordination
onto them.

Scope:

- `WorkspaceRunService`
- `WorkspaceCompareService`
- `WorkspaceInspectionService`
- move orchestration out of CLI and scattered helper coordination
- wire services through DI

Primary files:

- new `src/axis/framework/workspaces/services/`
- existing workspace modules as collaborators


### WP-08: Manifest Mutation Layer

Extract typed manifest mutation semantics from raw YAML dictionary update logic.

Scope:

- introduce a manifest mutator/update layer
- keep YAML roundtrip IO
- move business semantics out of `sync.py`
- support:
  - primary result appends
  - comparison result appends
  - development workflow pointer updates

Primary files:

- `src/axis/framework/workspaces/sync.py`
- new manifest mutator/update module(s)


### WP-09: Registry Consumer Migration

Migrate high-level business logic from direct global-registry consumption toward
catalog-driven dependencies.

Scope:

- run/system creation path
- world creation path
- visualization adapter resolution path
- comparison extension dispatch path
- leave local runtime registries such as `ActionRegistry` out of scope unless a
  concrete need appears

Primary files:

- `src/axis/framework/run.py`
- `src/axis/framework/runner.py`
- `src/axis/visualization/launch.py`
- `src/axis/framework/comparison/compare.py`


### WP-10: Rendering Cleanup and Edge Simplification

Reduce residual rendering and orchestration coupling at the framework edges.

Scope:

- keep rendering local to command modules
- remove remaining oversized formatting helpers from central CLI code
- avoid introducing a global rendering subsystem

Primary files:

- CLI package command modules
- selected workspace/inspection helpers


### WP-11: Tests and Documentation Update

Add and update tests and documentation for the refactored structure.

Scope:

- CLI behavior preservation tests
- plugin discovery/registration behavior preservation tests
- catalog-based dependency tests
- workspace service tests
- docs update for internal architecture records

Primary areas:

- `tests/framework/`
- `tests/framework/workspaces/`
- `docs-internal/ideas/architecture-refactoring/`


## Recommended Sequence

1. `WP-01 CLI Package Extraction and Entrypoint Compatibility`
2. `WP-03 Initial Command Module Extraction`
3. `WP-02 Manual Composition Root and Context Builder`
4. `WP-06 Handler Contract Stabilization`
5. `WP-07 Workspace Service Layer`
6. `WP-08 Manifest Mutation Layer`
7. `WP-04 Catalog / Registrar Foundations`
8. `WP-05 Plugin Discovery to Catalog Bridge`
9. `WP-09 Registry Consumer Migration`
10. `WP-10 Rendering Cleanup and Edge Simplification`
11. `WP-11 Tests and Documentation Update`

Notes:

- `WP-02` only becomes useful once the command/module boundaries are clearer.
- `WP-04` and `WP-05` should begin in Wave 2, not in the first CLI extraction
  wave.
- `WP-07` should wait until the composition root and handler contract direction
  are in place.
- `WP-09` should happen after catalogs exist, otherwise it would only create a
  temporary abstraction gap.
- test updates should happen inside each package, not only in `WP-11`


## Milestones

### Milestone 1: New Composition Boundary

Complete when:

- the CLI is package-based
- `main()` remains externally compatible
- an explicit `_build_context()`-style composition root exists

### Milestone 2: Explicit Workflow Structure

Complete when:

- workspace services exist
- handler contracts are explicit
- manifest mutation semantics are no longer buried in raw sync dict edits
- experiment-output-aware workspace orchestration is explicit

### Milestone 3: DI-Compatible Extension Model

Complete when:

- plugin discovery still works externally
- internal business logic can consume catalogs instead of direct global
  registries
- registry/DI coexistence is no longer ad hoc
