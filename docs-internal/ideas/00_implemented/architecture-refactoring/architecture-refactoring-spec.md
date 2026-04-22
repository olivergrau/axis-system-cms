# Architecture Refactoring Spec

## 1. Purpose

This specification defines the first architecture refactoring program for AXIS.

Its purpose is to improve the scalability of the implementation while
preserving the current user-facing concepts and the current filesystem-based
artifact model.

The refactoring is explicitly intended to address practical growth pressure in:

- CLI implementation
- workspace workflows
- workflow orchestration
- plugin / registry composition
- manifest mutation logic

This specification is not a redesign of the framework’s domain model.


## 2. Scope

This specification defines:

- the target CLI package structure
- the target use-case/service structure for workspaces
- the rules for command modules
- the rules for service classes
- the rules for dependency injection
- the compatibility model between DI and the existing plugin system
- the direction for refactoring registries into catalogs / registrars
- the direction for manifest mutation handling
- the workspace handler contract direction

This specification does **not** define:

- a persistence redesign
- a new public plugin API
- a new experiment or workspace feature
- a new comparison model
- a new visualization model


## 3. Architectural Intent

The framework shall evolve toward:

- package-oriented command structure
- explicit service orchestration
- explicit constructor injection with a centralized composition root
- explicit infrastructure catalogs instead of implicit registry usage in
  business logic
- typed manifest mutation semantics

The framework shall remain:

- explicit
- pragmatic
- filesystem-oriented
- CLI-first


## 4. Non-Goals

The refactoring must not introduce:

- a heavy enterprise architecture without concrete need
- a full persistence abstraction layer
- a service-locator architecture
- plugin code that depends directly on the composition root
- speculative abstractions for unsupported future modes


## 5. CLI Structure

### 5.1 CLI package

The CLI shall be refactored from a single implementation module into a package:

- `src/axis/framework/cli/`

This package shall contain at minimum:

- parser construction
- top-level dispatch
- grouped command modules

### 5.2 Command modules

Command implementations shall be grouped by functional area under:

- `src/axis/framework/cli/commands/`

Typical command groupings include:

- experiments
- runs
- compare
- visualize
- workspaces

### 5.3 CLI responsibility boundary

The CLI layer shall be responsible only for:

- parser construction
- command dispatch
- composition root setup
- top-level error mapping

Command modules may perform:

- argument interpretation
- service invocation
- text rendering
- JSON rendering

Command modules must not contain:

- domain business logic
- workflow coordination logic
- direct manifest business rules
- registry mutation logic


## 6. Workspace Service Structure

### 6.1 Workspace service package

Workspace use-case orchestration shall be introduced under:

- `src/axis/framework/workspaces/services/`

### 6.2 Service model

Workspace workflow orchestration shall be implemented through explicit service
classes.

Initial service areas should include:

- workspace run
- workspace compare
- workspace inspection

### 6.3 Service responsibilities

Services shall coordinate existing lower-level modules such as:

- resolution
- compare resolution
- validation
- sync
- summary
- output-aware inspection helpers

Services shall encapsulate workflow knowledge currently spread across helper
modules and CLI code.


## 7. Dependency Injection

### 7.1 DI is required

The architecture shall adopt dependency injection as a first-class structural
mechanism.

The initial DI model shall use explicit constructor injection and manual
composition from a centralized composition root.

### 7.2 Initial DI implementation

The first refactoring wave shall not introduce an external DI container
dependency.

Instead, the CLI entry layer shall expose a small composition function such as:

- `_build_context()`

This function shall assemble and return the high-level collaborators needed by
dispatch and command modules.

Container-based DI may be reconsidered later if manual wiring becomes a real
maintenance burden.

### 7.3 Composition root

The composition root shall live in the CLI entry layer.

It shall be responsible for assembling:

- services
- repositories
- output loaders
- manifest mutators
- catalogs / registrars
- rendering helpers where appropriate

### 7.4 DI usage rules

Composition shall happen at the edges of the application:

- CLI entry / dispatch
- top-level composition code

Business logic shall not use a service-locator pattern.

Services shall receive their dependencies explicitly through constructor
injection.


## 8. Plugin and Registry Compatibility

### 8.1 External plugin model remains

The external plugin model shall remain intact.

This includes:

- plugin discovery via entry points and/or `axis-plugins.yaml`
- plugin-local `register()` entrypoints
- externally visible plugin-style registration of systems, worlds, and
  extensions

### 8.2 Internal registry model shall evolve

Internally, business logic should progressively stop depending directly on
module-global registries.

The architecture shall instead introduce explicit infrastructure objects such
as:

- `SystemCatalog`
- `WorldCatalog`
- `ComparisonExtensionCatalog`

Registrar objects may also be introduced where helpful.

### 8.3 Compatibility rule

Plugins shall not register directly into the composition root.

Instead:

- plugins contribute capabilities through registration mechanisms
- registration populates catalogs / registrars
- the composition root provides those catalogs to services

### 8.4 Composition bridge

The composition root shall own the bridge between:

- plugin discovery
- catalog / registrar population
- composition-root wiring

This ensures that:

- services depend on explicit catalogs
- not on plugin discovery
- and not on module-global registries


## 9. Registry Refactoring Direction

### 9.1 Catalog transition

The existing registry model shall be progressively adapted into explicit
catalog-based infrastructure.

The transition may proceed in stages. It does not need to start in the first
CLI extraction wave, but it shall begin once the CLI/package boundary and
manual composition root are in place.

### 9.2 Business-logic boundary

High-level business logic and workflow services should depend on injected
catalogs rather than importing registry globals directly.

### 9.3 Backward-compatible transition

The migration may temporarily preserve existing registry modules as
implementation details or adapters, but they shall no longer be the preferred
dependency boundary for new orchestration logic.


## 10. Workspace Handler Contract

### 10.1 Handler abstraction remains

The workspace handler model shall remain the extension boundary for
workspace-type-specific behavior.

### 10.2 Handler contract must be explicit

Handler interfaces shall be explicit and reflection-free.

The framework shall not rely on runtime signature inspection to determine
handler capabilities.

### 10.3 Stable method signatures

Handler methods that participate in shared workflows shall expose stable method
signatures across implementations.

This applies especially to:

- run-target resolution
- comparison-target resolution
- scaffold responsibilities
- validation hooks


## 11. Manifest Mutation

### 11.1 Mutation logic must be separated from YAML IO

The YAML roundtrip mechanism may remain in place.

However, business semantics for `workspace.yaml` updates shall be separated from
raw YAML load/save handling.

### 11.2 Typed mutation layer

Workspace manifest changes shall be expressed through a typed mutation layer,
such as:

- mutator methods
- update objects
- explicit updater classes

The purpose is to avoid unbounded growth of direct dictionary mutation logic in
workflow code.

### 11.3 Scope

This mutation layer is intended for targeted manifest operations, not for a
complete second persistence model.

The mutation layer shall operate at the YAML / `ruamel.yaml` data-structure
level, using typed update operations over roundtrip-preserving structures.

It shall not require a separate Pydantic write model that would break comment
preservation.


## 12. Rendering

### 12.1 Rendering leaves central CLI

Text and JSON rendering shall be removed from the monolithic CLI entry module.

### 12.2 Rendering stays local

Rendering should remain close to the corresponding use case.

Preferred locations:

- command modules for CLI-facing rendering
- subsystem-local helpers where needed

The architecture shall not introduce a large global rendering subsystem unless
later growth clearly demands it.


## 13. Migration Program

### 13.1 Wave 1

Wave 1 shall prioritize:

- CLI package extraction
- command module extraction
- manual composition root introduction
- handler contract stabilization
- test preservation for each moved command area

### 13.2 Wave 2

Wave 2 shall prioritize:

- workspace service layer introduction
- migration of workspace workflows onto services
- typed manifest mutation extraction
- experiment-output-aware service orchestration
- initial registry-to-catalog adaptation
- plugin-discovery-to-catalog bridging
- service dependency shift from registry globals toward catalogs

### 13.3 Wave 3

Wave 3 shall prioritize:

- further composition cleanup where it improves orchestration clarity
- selective cleanup of residual command/rendering boundaries
- further reduction of direct global-registry usage


## 14. Stability Requirements

The refactoring must preserve:

- existing artifact directory layout
- experiment/run persistence model
- existing conceptual experiment/workspace model
- existing external plugin discovery model
- current user-facing command concepts


## 15. Acceptance Criteria

This refactoring direction is considered successfully established when:

- CLI growth is no longer concentrated in one monolithic module
- command modules no longer contain business logic
- workspace workflows are coordinated through explicit service classes
- constructor injection is introduced through a centralized composition root
- plugin discovery still works externally
- internal business logic can depend on explicit catalogs instead of global
  registries
- handler contracts are explicit and no longer rely on reflection
- manifest mutation semantics are no longer expressed as ad hoc business logic
  in raw YAML dictionary updates


## 16. Recommendation

Proceed with the refactoring as a structured, incremental program.

The first implementation focus should be:

1. CLI package extraction
2. command module extraction
3. manual composition root
4. handler contract cleanup

Then:

5. workspace service layer
6. manifest mutation layer
7. registry-to-catalog adaptation

This is the most pragmatic path because it addresses the current scaling risks
without destabilizing the deeper experiment, persistence, and output layers.
