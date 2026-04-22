# Architecture Refactoring Draft

## Purpose

This draft captures the first pragmatic refactoring directions that now appear
useful in AXIS after the recent growth in:

- experiment execution
- experiment output abstraction
- workspace workflows
- workspace-specific inspection and comparison logic
- CLI surface area

The goal is **not** to redesign AXIS academically or introduce patterns for
their own sake.

The goal is to identify the first refactorings that will most likely improve:

- maintainability
- feature velocity
- local reasoning
- testability
- architectural control as the framework continues to grow


## Current Assessment

The overall architecture is still fundamentally sound.

The core layering already has a reasonable shape:

- `config`
- `run`
- `experiment`
- `experiment_output`
- `workspace`

Persistence is simple and stable.
The newer `ExperimentOutput` abstraction is also directionally correct.

The concern is not that the codebase is already collapsing.

The concern is that several parts of the framework are now at the point where
additional feature growth will become noticeably more expensive unless a few
targeted structural refactorings are introduced.


## Main Growth Hotspots

### 1. CLI concentration

The most obvious hotspot is:

- `src/axis/framework/cli.py`

This file is now very large and contains several kinds of responsibility at
once:

- parser construction
- top-level dispatch
- command orchestration
- output formatting
- error mapping
- partial workflow coordination

Even though the CLI is conceptually intended to remain a delegator, it is now
large enough that it risks becoming a hidden application layer.

This is a practical scaling issue, not just a stylistic one.


### 2. Workspace orchestration is spread across many modules

The workspace subsystem is already split into multiple files, which is good:

- `resolution.py`
- `execute.py`
- `compare_resolution.py`
- `visualization.py`
- `summary.py`
- `sync.py`
- `validation.py`
- handlers

However, the operational workflows are now distributed across these modules
without a sufficiently explicit use-case layer.

As a result, the logic for a single workflow such as:

- run workspace
- compare workspace
- inspect workspace

is spread across:

- CLI handlers
- resolution helpers
- sync helpers
- handler subclasses
- summary/rendering logic

This is still manageable today, but it is a likely growth friction point.


### 3. The handler abstraction is promising, but not fully stable yet

The workspace handler model is a good step:

- `single_system`
- `system_comparison`
- `system_development`

It provides a natural extension boundary for workspace-specific behavior.

But the abstraction is not yet fully explicit.

For example, the run resolution path currently uses runtime signature
inspection to determine whether a handler supports a `run_filter` parameter.

That is a sign that the interface contract is lagging behind the actual
behavioral needs of the system.


### 4. Workspace manifest synchronization is becoming business logic

`sync.py` is no longer just a persistence helper.

It already contains meaningful workflow semantics, such as:

- how result entries are shaped
- how development-specific result tracking is updated
- how current candidate results are advanced
- how current comparison pointers are maintained

This is exactly the kind of logic that tends to become fragile if it remains as
direct dictionary mutation against serialized YAML structures.


### 5. Dependencies are still mostly concrete and directly instantiated

Across the framework, many high-level flows directly construct and use concrete
infrastructure components such as:

- `ExperimentRepository`
- YAML loaders / serializers
- CLI prompt libraries
- formatting/rendering helpers

This is not automatically wrong.

But as orchestration grows, it makes high-level behaviors harder to isolate and
test, and it makes alternative execution contexts harder to introduce later.


### 6. Plugin discovery and registries are still global and side-effect-based

AXIS already has a plugin-style extension model for:

- systems
- worlds
- comparison extensions
- visualization side registrations

This is currently driven by:

- plugin discovery in `axis.plugins`
- plugin-local `register()` functions
- module-level global registries

This model works, but it has two properties that become more problematic once a
composition layer is introduced:

- registration is side-effect-based
- the registries are global module state

If left unchanged, the framework risks ending up with two parallel
infrastructure mechanisms:

- global registries for plugin-provided factories and extensions
- a composition-root-based service layer for services and workflow
  orchestration

That would be survivable, but architecturally untidy and likely to become
confusing over time.


## What Does *Not* Look Like the Main Problem

### Persistence

The filesystem-backed persistence model is not currently the main architectural
problem.

It is simple, understandable, and consistent with the framework’s artifact
orientation.

Minor improvements may become useful later, but a persistence redesign is not
the first refactoring priority.


### Experiment output abstraction

The `ExperimentOutput` layer appears to be a useful architectural addition
rather than a mistake.

It gives the framework a cleaner semantic layer between raw persisted artifacts
and workspace/CLI consumers.

This area may need refinement, but it does not currently look like the first
place that needs restructuring.


### Comparison module structure

The comparison package is comparatively well-separated already:

- validation
- alignment
- metrics
- outcome
- summary
- extensions

This part looks more scalable than several other areas.


## First Refactoring Candidates

### Candidate A: Split the CLI into command modules

The first likely refactoring should be a decomposition of the CLI into smaller
command modules, for example:

- `framework/commands/experiments.py`
- `framework/commands/runs.py`
- `framework/commands/workspaces.py`
- `framework/commands/visualize.py`
- `framework/commands/compare.py`

The top-level `cli.py` would remain the actual console entrypoint, but would
primarily:

- build the parser
- register command handlers
- dispatch to modular command implementations

This would reduce the CLI file as a growth hotspot without changing the user
surface.


### Candidate B: Introduce explicit workspace use-case services

The workspace subsystem would likely benefit from a small application-service
layer, for example:

- `WorkspaceRunService`
- `WorkspaceCompareService`
- `WorkspaceInspectionService`

These would not replace the existing modules.

Instead, they would orchestrate them explicitly and absorb the workflow-level
knowledge that is currently scattered across:

- CLI handlers
- resolution modules
- sync helpers
- workspace handlers


### Candidate C: Make the handler contract explicit

The handler system should become more explicit and less reflective.

Examples of improvement:

- no `inspect.signature(...)` probing
- a stable method signature for run target resolution
- explicit support for optional run-selection/filter inputs

This would make the workspace-type extension boundary more reliable and easier
to evolve.


### Candidate D: Move manifest mutation into a typed mutation layer

Instead of accumulating more direct dictionary updates in `sync.py`, the
framework would likely benefit from a typed manifest mutation layer.

This could take forms such as:

- `WorkspaceManifestMutator`
- `WorkspaceManifestUpdater`
- explicit update models applied to parsed manifest state

The YAML round-trip serializer can remain in place.

The refactoring target is the mutation semantics, not the YAML library.


### Candidate E: Apply lightweight dependency inversion in high-level flows

This does **not** mean introducing a full DI container or enterprise framework.

It means introducing dependency boundaries where they already clearly matter,
especially in high-level orchestration code.

Examples:

- pass repositories and loaders explicitly into services
- reduce direct construction of concrete dependencies in top-level workflows
- make inspection/rendering logic easier to test separately from IO


### Candidate F: Refactor global registries into explicit catalogs/registrars

The existing plugin model should remain visible externally, but the internal
registry mechanism should evolve.

The likely direction is:

- keep plugin discovery
- keep plugin `register()` entrypoints
- replace direct dependence on module-global registries with explicit
  infrastructure objects such as:
  - `SystemCatalog`
  - `WorldCatalog`
  - `ComparisonExtensionCatalog`
  - and matching registrar APIs where appropriate

This would make the plugin system compatible with explicit composition without
forcing plugins to know about the composition root itself.

In that model:

- plugins register capabilities into catalogs / registrars
- the composition root assembles services using those catalogs
- business logic no longer reads directly from global registry modules


## Likely Prioritization

At the moment, the most promising first priority order seems to be:

1. split the CLI into command-oriented modules
2. introduce explicit workspace use-case services
3. stabilize the handler contract
4. introduce an explicit composition root
5. evolve plugin registries into catalogs / registrars in a later wave
6. refactor manifest mutation into a typed layer
7. apply lightweight dependency inversion where it improves orchestration


## Refactoring Principles

These refactorings should follow a few practical rules:

- no persistence redesign unless clearly needed
- no pattern introduction without a concrete pressure point
- no speculative generalization for unneeded future workspace types
- no premature external DI/container dependency
- preserve the existing mental model for users
- keep command behavior stable while internal structure improves
- preserve the external plugin experience while improving internal composition


## Initial Recommendation

The first refactoring wave should likely focus on:

- CLI decomposition
- workspace orchestration clarity
- handler interface explicitness
- manual composition root introduction

The registry-to-catalog adaptation should follow after the initial CLI and
workflow structure cleanup rather than being forced into the very first wave.

That would address the most visible scaling risks while keeping the framework
recognizable and operational.

It would also create a cleaner foundation for future features in:

- workspace workflows
- output-aware inspection
- richer development workflows
- additional bounded experiment modes


## Open Questions For Next Draft

The next refinement step should answer:

1. Where exactly should command modules live?
2. Should workspace services live under `framework/workspaces/` or as a more
   general framework service layer?
3. How much of current `sync.py` should move into a typed manifest updater?
4. How should global registries map onto DI-aware catalogs / registrars?
5. Which constructor dependencies are worth abstracting first?
6. Which parts of the CLI should remain formatting-only versus orchestration?


## Next Step

If this direction still looks sound after review, the next document should be a
more concrete `detailed-draft` that:

- maps the proposed refactorings to current modules
- identifies the first safe extraction seams
- estimates migration impact
- and separates immediate refactorings from later, optional structural cleanup
