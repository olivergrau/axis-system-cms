# Architecture Refactoring Detailed Draft

## Purpose

This detailed draft refines the first architectural refactoring direction for
AXIS.

It builds on the observations from:

- [Architecture Refactoring Draft](./architecture-refactoring-draft.md)

The intent is to define a practical, implementation-oriented restructuring path
that improves scalability of the codebase without triggering a large disruptive
rewrite.


## Design Goal

The refactoring should improve the ability of the framework to absorb further
feature growth in:

- CLI commands
- workspace workflows
- output-aware inspection
- comparison routing
- development-oriented workflow support

while preserving:

- the existing user-facing CLI concepts
- the current persistence model
- the current domain layering


## Architectural Direction

The refactoring should move AXIS toward:

- package-oriented CLI structure
- explicit workflow/use-case services
- typed mutation of workspace manifests
- explicit handler contracts
- explicit constructor injection with a centralized composition root

The framework should remain pragmatic and explicit.

The refactoring is not intended to introduce:

- a heavy enterprise architecture
- a persistence redesign
- speculative abstractions for unsupported future modes


## Core Decisions

### 1. CLI becomes a package

The CLI should stop growing as a single module.

The target shape is:

- `src/axis/framework/cli/`
- `src/axis/framework/cli/__init__.py`
- `src/axis/framework/cli/parser.py`
- `src/axis/framework/cli/dispatch.py`
- `src/axis/framework/cli/commands/`

With command grouping such as:

- `src/axis/framework/cli/commands/experiments.py`
- `src/axis/framework/cli/commands/runs.py`
- `src/axis/framework/cli/commands/compare.py`
- `src/axis/framework/cli/commands/visualize.py`
- `src/axis/framework/cli/commands/workspaces.py`

The existing `axis.framework.cli` import path can be preserved through package
entry wiring.


### 2. CLI retains only parser and dispatch responsibilities

The CLI layer should keep:

- parser construction
- argument-to-command dispatch
- top-level error handling
- composition-root setup

The CLI layer should not hold:

- domain logic
- workflow orchestration logic
- manifest mutation logic
- experiment/workspace business rules

Rendering is allowed in command modules, but business logic is not.


### 3. Workspace workflows gain explicit service classes

The workspace subsystem should gain a use-case/service layer under:

- `src/axis/framework/workspaces/services/`

Initial candidate services:

- `WorkspaceRunService`
- `WorkspaceCompareService`
- `WorkspaceInspectionService`

Potential additional services later:

- `WorkspaceVisualizationService`
- `WorkspaceScaffoldService`

These services should coordinate existing lower-level modules such as:

- resolution
- compare resolution
- sync
- validation
- summary

This creates an explicit orchestration layer and reduces workflow knowledge in:

- CLI command modules
- helper modules
- ad hoc cross-module coordination


### 4. Services should be explicit classes

Services should be implemented as classes with constructor-injected
dependencies.

This is preferred over large free-function modules because the orchestration
paths increasingly depend on multiple collaborators such as:

- repositories
- loaders
- mutators
- renderers
- output interpreters

Class-based services provide a cleaner boundary for both DI and testing.


### 5. Manifest synchronization should be split into IO and mutation semantics

`sync.py` should stop being the place where business semantics are encoded
directly as dictionary edits.

The refactoring direction is:

- keep YAML roundtrip IO where it already lives
- move manifest update semantics into a typed mutation layer

Likely direction:

- `manifest_mutator.py`
- or `manifest_update.py`

Responsibilities split:

- `sync.py`
  - load/write `workspace.yaml`
  - coordinate mutation application
- manifest mutator layer
  - define how result and comparison updates change manifest state


### 6. Manifest mutation should be typed, but not over-engineered

The goal is not to build a second complete persistence model for
`workspace.yaml`.

The goal is to avoid continued growth of raw dictionary mutation logic.

Therefore the recommended approach is:

- typed mutation methods or update objects
- focused mutation helpers for concrete operations

Examples:

- append experiment result entry
- append comparison result
- update development candidate pointers

This should stay lighter than a complete second writable manifest model.


### 7. The workspace handler contract should be made explicit

The current handler abstraction is useful and should remain.

However, the contract should become explicit and reflection-free.

In particular:

- no `inspect.signature(...)` probing
- no behavior differences based on optional hidden method shapes

Handler methods should have stable signatures, for example:

- `resolve_run_targets(..., run_filter: str | None = None)`

or another equally explicit contract.

The important point is that handler capabilities should be visible in the type
contract, not inferred at runtime.


### 8. Compare and visualize resolution remain local to workspaces

The refactoring should not prematurely generalize workspace-specific resolution
logic into a global resolution subsystem.

For now:

- workspace compare resolution stays under `framework/workspaces/`
- workspace visualization resolution stays under `framework/workspaces/`

What should improve is internal reuse:

- smaller shared helpers
- less duplication in output-aware selection


### 9. Rendering should be local to subsystems

Rendering should be extracted from the central CLI file, but not collapsed into
one global rendering framework.

Preferred direction:

- command-specific rendering in CLI command modules
- workspace-specific rendering helpers in workspace modules when needed

This keeps rendering close to the corresponding use case without turning the
whole framework into a generic presentation layer.


### 10. Dependency injection should start with explicit composition

The refactoring should adopt explicit DI as a real architectural mechanism,
but the first wave does not need an external DI container dependency.

The preferred first implementation direction is:

- constructor injection from the first refactoring wave
- a manual CLI composition root, for example via `_build_context()`
- no external DI container in the first wave


### 11. The external plugin model should remain, but map internally to
composition-aware catalogs

AXIS should keep its existing external plugin story:

- plugin discovery via entry points / `axis-plugins.yaml`
- plugin-local `register()` functions
- plugin packages for systems, worlds, and extensions

This external surface is useful and should not be discarded.

However, internally, plugin-provided capabilities should move away from being
consumed through module-global registries.

The preferred direction is:

- preserve plugin discovery
- preserve plugin registration entrypoints
- adapt internal registration to explicit catalog / registrar objects

Likely internal concepts:

- `SystemCatalog`
- `WorldCatalog`
- `ComparisonExtensionCatalog`
- optionally registrar objects used during plugin registration

This means:

- plugins continue to “register”
- but business logic should increasingly depend on injected catalogs rather than
  importing global registry modules directly


## Plugin / Registry Compatibility With Explicit Composition

### Current state

Today the plugin model is roughly:

1. discover plugin modules
2. import plugin module
3. call plugin `register()`
4. plugin mutates module-level global registries

This works, but it is not an ideal long-term fit for a composition-oriented
runtime.


### Target compatibility model

The DI layer and the plugin layer should be complementary:

- plugin layer:
  - discovers and contributes capabilities
- catalog / registrar layer:
  - stores those capabilities in explicit infrastructure objects
- composition root:
  - wires services using those infrastructure objects

This avoids two bad extremes:

- forcing plugins to know about the composition root
- keeping business logic coupled directly to module-global registries forever


### Compatibility rule

Plugins should not register directly into the composition root.

Instead:

- plugins register capabilities
- the framework exposes registrars / catalogs
- the composition root consumes those catalogs as dependencies

This keeps plugin composition explicit while avoiding container-driven plugin
magic.


### Migration direction

The migration should likely happen in stages:

1. keep existing global registries operational
2. introduce catalog wrappers / registrar abstractions
3. route new services through injected catalogs
4. progressively reduce direct usage of registry globals in business logic
5. later, if desired, make plugin registration target registrars explicitly

This allows the DI rollout and registry refactor to progress together without
breaking the existing plugin-facing extension model.


## Composition Model

### Composition root

The composition root should live in the CLI entry layer.

This is the natural place to assemble:

- repositories
- services
- renderers
- mutators
- output loaders

The application context should be built once per CLI process invocation.


### Registration style

Registrations should be explicit and local to the composition root.

That means:

- no hidden global container
- no module-level ambient service lookups
- no service locator spread across the codebase


### Service usage

Command modules should request services from the container and delegate to them.

Business logic should not reach back into the container during normal
operation.

Composition should happen at the edges, not inside the domain workflows.


### Catalog registration in the composition root

The composition root should own the bridge between:

- plugin discovery
- catalogs / registrars
- the composition root

This implies:

- plugin discovery happens before high-level service resolution
- discovered plugin registrations populate the relevant catalogs
- those catalogs are then exposed through the shared application context

That gives the rest of the application a stable dependency model:

- services depend on catalogs
- not on discovery code
- and not on module-global registries


## Concrete First-Wave Refactoring Targets

### Target A: CLI package extraction

Extract from the current monolithic CLI:

- parser creation
- command dispatch
- workspace command handling
- experiment/run/compare/visualize command handling

The first wave does not need to perfect the final command architecture.

It needs to establish the package boundary and remove the single-file growth
hotspot.


### Target B: Workspace services

Introduce first service classes for the highest-friction workspace workflows:

- run
- compare
- inspection

The first service wave should absorb orchestration that is currently spread
across:

- CLI command handlers
- resolution helpers
- sync helpers
- handler-specific logic


### Target C: Explicit handler interface

Refactor the handler contract so all handlers expose the same stable method
signatures for:

- config creation
- run target resolution
- comparison target resolution
- type-specific validation

This should remove reflection-based behavior branching.


### Target D: Manifest mutation layer

Extract the actual mutation semantics currently embedded in sync logic into a
typed mutation layer.

This should happen early because workspace features are likely to keep growing.


### Target E: Composition-root-backed orchestration

As the command modules and services are introduced, wire them through the
composition root from the start.

This should prevent the system from first re-growing concrete construction
logic and only later attempting to retrofit composition.


### Target F: Registry-to-catalog adaptation

As DI is introduced, the registry system should also be adapted in the same
refactoring program.

The first goal is not a full replacement of plugin registration.

The first goal is:

- explicit catalog objects
- services depending on those catalogs
- a clear adapter bridge from existing registry/plugin behavior to the new
  internal dependency model

This means the registry refactor should follow the initial CLI/workflow
cleanup rather than being forced into the very first wave.


## Migration Strategy

The detailed draft recommends documenting all refactoring waves together, but
still executing them incrementally.

### Wave 1

- introduce CLI package structure
- extract initial command modules
- introduce manual composition root
- stabilize handler signatures
- keep tests updated alongside each extracted command area

### Wave 2

- introduce workspace services
- extract manifest mutation logic
- move workspace workflows onto services
- integrate `experiment_output.py` explicitly into workspace service
  orchestration
- introduce first explicit catalogs / registrars
- bridge plugin discovery into those catalogs
- migrate services from direct registry usage toward injected catalogs

### Wave 3

- clean remaining command rendering boundaries
- refine composition further where it improves orchestration clarity
- perform selective cleanup of residual old helper responsibilities
- further reduce direct dependence on global registry modules


## What Should Stay Stable

The following should remain stable through the refactoring:

- the artifact directory layout
- experiment and run persistence semantics
- the conceptual meaning of `ExperimentOutput`
- workspace feature behavior from the user perspective
- comparison core package structure
- the external plugin experience for systems, worlds, and extensions


## Risks To Manage

### 1. Over-refactoring too early

The refactoring should not explode into a full architectural rewrite.

It should stay anchored to:

- current hotspots
- current complexity
- immediate future growth pressure


### 2. Hiding logic behind the container

Introducing DI should not lead to a situation where system behavior is harder
to reason about because object creation becomes opaque.

The container should be explicit and centralized.


### 2b. Letting registries and DI drift apart

If DI is introduced but plugin-backed registries remain an unrelated parallel
mechanism, the framework will accumulate two competing composition systems.

That should be avoided by adapting registries into catalog/registrar-backed
dependencies early in the refactoring program.


### 3. Mixing rendering and domain logic again in new command modules

Extracting command modules only helps if they remain thin:

- input mapping
- service invocation
- output rendering

not:

- business rules
- domain coordination
- persistence mutation


## Expected Benefits

If this refactoring is executed well, the likely benefits are:

- smaller and more understandable CLI surface implementation
- clearer ownership of workspace workflows
- less fragile YAML/manifest update logic
- more explicit extension boundaries
- easier unit testing of high-level use cases
- lower cost of future feature additions


## Recommendation

Proceed with the refactoring as a structured multi-wave program.

The first concrete implementation focus should be:

1. CLI package extraction
2. handler contract cleanup
3. DI composition root introduction
4. initial registry-to-catalog adaptation

Then:

5. workspace service layer
6. manifest mutation layer

This is the most pragmatic sequence because it reduces the largest current
growth risks without destabilizing the deeper domain and persistence layers.


## Next Step

If this detailed draft still looks correct, the next step should be a first
normative `architecture-refactoring-spec.md` that defines:

- target package boundaries
- DI rules
- plugin/catalog compatibility rules
- command/service responsibilities
- handler contract rules
- manifest mutation responsibilities
