# Architecture Refactoring Engineering Spec

## 1. Purpose

This engineering specification derives a concrete implementation direction from:

- [Architecture Refactoring Draft](./architecture-refactoring-draft.md)
- [Architecture Refactoring Detailed Draft](./architecture-refactoring-detailed-draft.md)
- [Architecture Refactoring Spec](./architecture-refactoring-spec.md)

Its purpose is to define a pragmatic, code-aligned refactoring program for the
current AXIS solution.


## 2. Current Code Reality

The refactoring must start from the actual current implementation, not from an
imagined clean slate.

### 2.1 CLI

The current CLI is still implemented as a single module:

- `src/axis/framework/cli.py`

It currently contains:

- parser construction
- command dispatch
- command orchestration
- text rendering
- JSON rendering
- top-level error handling

The packaging entrypoint is currently:

- `pyproject.toml`
  - `axis = "axis.framework.cli:main"`

This means the refactoring must preserve a stable import path or provide a
compatible package-level replacement for `axis.framework.cli:main`.


### 2.2 Workspace orchestration

The workspace subsystem already has useful module separation:

- `workspaces/resolution.py`
- `workspaces/execute.py`
- `workspaces/compare_resolution.py`
- `workspaces/visualization.py`
- `workspaces/summary.py`
- `workspaces/validation.py`
- `workspaces/sync.py`
- `workspaces/handler.py`

However, higher-level workflow coordination is still spread across:

- CLI handlers
- helper modules
- sync logic
- handler subclasses


### 2.3 Current registry / plugin model

Plugin discovery currently lives in:

- `src/axis/plugins.py`

It discovers plugins through:

- setuptools entry points (`axis.plugins`)
- `axis-plugins.yaml`

Plugin modules expose `register()` and currently mutate module-global
registries such as:

- `src/axis/framework/registry.py`
  - systems
- `src/axis/world/registry.py`
  - worlds
- `src/axis/visualization/registry.py`
  - visualization adapters
- `src/axis/framework/comparison/extensions.py`
  - comparison extensions

The visualization registry is internally split into two separate registries:

- world visualization factories
- system visualization factories

The later catalog design should preserve that split rather than collapsing it
prematurely into one undifferentiated registry concept.

This is the primary compatibility constraint for DI.


### 2.4 Local runtime registries

Not every registry-like component should be pulled into the same refactoring.

For example:

- `src/axis/world/actions.py`

creates an `ActionRegistry` as a local per-run/per-episode runtime structure.

This is not the same kind of global plugin-backed registry and should not be
forced into the same catalog migration prematurely.


### 2.5 Experiment and persistence layers

The following layers are already in reasonably good shape and are not the first
refactoring target:

- `src/axis/framework/experiment.py`
- `src/axis/framework/persistence.py`
- `src/axis/framework/experiment_output.py`
- `src/axis/framework/comparison/*`

The refactoring should integrate with these layers, not redesign them.


## 3. Engineering Goals

The architecture refactoring program should achieve the following:

1. reduce CLI concentration
2. introduce explicit service orchestration for growing workflows
3. introduce constructor injection and composition cleanly and early
4. preserve the external plugin story
5. replace direct business-logic dependence on global registries with explicit
   catalogs
6. stabilize extension contracts
7. reduce direct YAML business mutation logic


## 4. Target Structure Overview

The target direction is:

- CLI package
- command modules
- service classes
- composition root
- manual composition context
- explicit catalogs / registrars
- typed manifest mutation layer


## 5. CLI Refactoring

### 5.1 Target package direction

The CLI should be refactored toward:

- `src/axis/framework/cli/`

Recommended initial files:

- `src/axis/framework/cli/__init__.py`
- `src/axis/framework/cli/parser.py`
- `src/axis/framework/cli/dispatch.py`
- `src/axis/framework/cli/commands/experiments.py`
- `src/axis/framework/cli/commands/runs.py`
- `src/axis/framework/cli/commands/compare.py`
- `src/axis/framework/cli/commands/visualize.py`
- `src/axis/framework/cli/commands/workspaces.py`

### 5.2 Entry-point compatibility

The packaging entrypoint currently targets:

- `axis.framework.cli:main`

The refactoring must preserve this external entrypoint contract.

Recommended approach:

- convert `axis/framework/cli.py` into `axis/framework/cli/__init__.py`
- keep `main()` exported there

Alternative acceptable approach:

- retain a thin compatibility `cli.py` shim that imports `main` from the new
  package

### 5.3 Responsibility split

#### `parser.py`

Responsible for:

- parser construction
- subparser wiring

#### `dispatch.py`

Responsible for:

- top-level command dispatch
- exit-code mapping
- high-level error handling

#### `commands/*.py`

Responsible for:

- parsing command-level argument semantics
- invoking services
- rendering text/json output

Must not contain:

- workflow business rules
- registry mutation rules
- manifest business semantics


## 6. Dependency Composition Introduction

### 6.1 Initial approach

The first refactoring wave should use explicit constructor injection and a
manual composition root.

Recommended initial pattern:

- a `_build_context()` function in the CLI entry layer
- explicit constructor wiring for services and helpers
- no external DI container dependency in the first wave

This matches the current scale of the codebase and avoids introducing a runtime
architecture dependency before the command/module boundaries have been cleaned
up.

### 6.2 Future container option

An external DI container may be reconsidered later if manual composition
becomes difficult to maintain. It is not required for this refactoring program.

### 6.3 Composition root

The composition root should live in the refactored CLI entry layer.

It should:

1. build the application context
2. trigger plugin discovery / registration bridge where needed
3. wire services
4. wire repositories / mutators / helpers
5. expose collaborators to dispatch/command modules

### 6.4 DI rules

#### Allowed

- constructor injection into services
- explicit manual factory/helper wiring
- edge-level composition in dispatch/entry code

#### Not allowed

- service-locator use inside business logic
- plugin code mutating the composition context directly
- hidden global composition state from framework modules


## 7. Catalog / Registrar Refactoring

### 7.1 Why catalogs are needed

The current plugin model is global-registry based.

That is compatible with plugin discovery but not ideal as the internal
dependency boundary for DI-driven services.

The first refactoring goal is therefore not to remove plugin registration, but
to introduce explicit infrastructure objects that can be injected.

### 7.2 Initial catalog candidates

The first catalog wave should cover the current global plugin-backed registries:

- system factories
- world factories
- comparison extensions
- world visualization adapters
- system visualization adapters

Likely initial concepts:

- `SystemCatalog`
- `WorldCatalog`
- `ComparisonExtensionCatalog`
- `WorldVisualizationCatalog`
- `SystemVisualizationCatalog`

### 7.3 Registrar direction

Where beneficial, registrars may be introduced as the mutable registration-side
API while catalogs act as the consumption-side API.

This split is optional in the first wave but is directionally preferred.

### 7.4 Migration timing and bridge

This migration should begin after the CLI/package split and manual composition
root are already in place.

The initial implementation should likely use an adapter strategy:

- preserve the existing registry modules
- add catalog wrappers or registrar abstractions around them
- expose those catalog abstractions through the shared application context
- gradually migrate services to consume catalogs instead of registry globals

This keeps the migration incremental.

### 7.5 Plugin compatibility rule

Plugins must continue to expose `register()`.

But the engineering direction should move toward:

- plugins registering capabilities through explicit registrar/catalog-aware
  mechanisms

The composition root should remain responsible for connecting plugin discovery
to the composed catalogs.


## 8. Workspace Service Refactoring

### 8.1 Initial service package

Introduce:

- `src/axis/framework/workspaces/services/`

### 8.2 Initial service candidates

First-wave candidates:

- `WorkspaceRunService`
- `WorkspaceCompareService`
- `WorkspaceInspectionService`

Optional later candidates:

- `WorkspaceVisualizationService`
- `WorkspaceScaffoldService`

### 8.3 Service dependencies

Typical service dependencies may include:

- repository factory or repository instances
- experiment output loader
- manifest mutator
- summary builder
- resolution helpers
- workspace handler resolver

The service layer should be the first major consumer of constructor-injected
collaborators.

The workspace service layer must explicitly depend on the existing experiment
output abstraction in:

- `src/axis/framework/experiment_output.py`

In practice this means services should use:

- `load_experiment_output(...)`
- `PointExperimentOutput`
- `SweepExperimentOutput`

where output-aware workspace workflows require typed experiment/result
semantics above raw persistence.


## 9. Handler Contract Refactoring

### 9.1 Current issue

`workspaces/resolution.py` currently uses runtime signature inspection to decide
whether a handler supports `run_filter`.

This is an architectural smell and should be removed.

### 9.2 Required direction

The handler interface should be made explicit and stable.

Especially:

- `resolve_run_targets(...)`
- `resolve_comparison_targets(...)`
- scaffold hooks
- validation hooks

The first cleanup target should be the run-target resolution signature so all
handlers share one explicit contract.


## 10. Manifest Mutation Refactoring

### 10.1 Current state

`workspaces/sync.py` currently combines:

- YAML roundtrip load/save
- business-level update semantics
- development-workflow side effects

### 10.2 Required separation

The refactoring should split this into:

- manifest IO / roundtrip coordination
- typed mutation logic

### 10.3 Recommended direction

Introduce a focused mutation layer, for example:

- `workspaces/manifest_mutator.py`

Potential responsibilities:

- append primary result
- append comparison result
- update development-specific pointers
- update current candidate references

`sync.py` can remain as a thin wrapper coordinating YAML load/save and delegating
semantic changes to the mutator.

The mutator should operate on YAML / `ruamel.yaml` roundtrip structures rather
than on a separate Pydantic write model, so comment preservation remains
compatible with typed manifest-update semantics.


## 11. Rendering Refactoring

### 11.1 Central CLI rendering must shrink

The current CLI contains a large amount of inline rendering.

This should be moved into:

- command modules
- subsystem-local helpers where appropriate

### 11.2 Scope limit

No global framework-wide rendering layer is required in the first refactoring
program.

Rendering should remain close to the corresponding command/use case.


## 12. Implementation Waves

### 12.1 Wave 1

Focus:

- CLI package extraction
- `main()` compatibility preservation
- command module extraction
- manual composition root introduction
- handler signature cleanup
- per-package CLI regression test updates

### 12.2 Wave 2

Focus:

- workspace service introduction
- command modules delegating to services
- manifest mutator introduction
- experiment-output-aware workspace service integration
- initial catalog/registrar adaptation
- plugin-discovery-to-catalog bridge
- gradual shift from direct registry usage to injected catalogs in workspace
  workflows

### 12.3 Wave 3

Focus:

- broader composition cleanup where useful
- cleanup of remaining residual orchestration in command modules
- deeper reduction of direct global registry imports in business logic
- additional service extraction where the codebase proves it useful


## 13. Specific Engineering Recommendations

### 13.1 Preserve current domain core

Do not refactor first:

- `experiment.py`
- `persistence.py`
- comparison core package

These are not the primary scaling hotspot today.

### 13.2 Refactor edges first

Refactor first:

- CLI
- workspace orchestration
- composition / dependency boundaries
- registry consumption model

### 13.3 Do not unify all registries blindly

The first catalog refactor should target plugin-backed global registries.

Do not force local runtime mechanisms such as `ActionRegistry` into the same
abstraction wave unless a concrete pressure point appears.


## 14. Tests and Verification

The refactoring program should preserve behavior through focused regression
coverage.

Particular areas that need protection:

- CLI command behavior
- plugin discovery and registration behavior
- system/world lookup behavior
- workspace run/compare/inspection workflows
- visualization adapter resolution

The engineering expectation is not a single large migration, but stepwise
refactoring with behavior-preserving test coverage after each wave.


## 15. Acceptance Criteria

This engineering direction is correctly established when:

- the CLI is no longer a monolithic implementation hotspot
- an explicit composition root exists
- services are instantiated through constructor injection
- workspace workflows are coordinated through explicit service classes
- handler contracts are explicit and no longer reflective
- plugin discovery still works from the user perspective
- service/business logic can consume catalogs instead of importing registry
  globals directly
- `sync.py` no longer carries growing business semantics as raw dictionary
  mutation logic


## 16. Recommendation

Proceed with the architecture refactoring as a deliberate implementation program
with these initial priorities:

1. extract the CLI into a package while preserving the current entrypoint
2. extract command modules so orchestration stops living in one file
3. introduce a manual composition root / `_build_context()`
4. clean the workspace handler contract
5. introduce workspace services
6. extract a manifest mutation layer
7. begin catalog / registrar adaptation

This order best matches the current codebase and addresses the current scaling
pressure without disrupting the core experiment and persistence model.
