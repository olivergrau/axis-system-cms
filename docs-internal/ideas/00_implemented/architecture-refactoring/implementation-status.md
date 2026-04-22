# Architecture Refactoring — Implementation Status

All 11 work packages from the architecture refactoring program have been
implemented. This document summarizes what was delivered.

## Completed Work Packages

### Wave 1: CLI & Composition

| WP | Title | Status | Key Deliverables |
|----|-------|--------|-----------------|
| WP-01 | CLI Package Extraction | Done | `cli.py` → `cli/` package (4 files) |
| WP-03 | Command Module Extraction | Done | `_handlers.py` → 5 command modules in `cli/commands/` |
| WP-02 | Manual Composition Root | Done | `cli/context.py` with `CLIContext` + `build_context()` |
| WP-06 | Handler Contract Stabilization | Done | `run_filter` added to base handler; `inspect.signature` removed |
| WP-07 | Workspace Service Layer | Done | `workspaces/services/` package with 3 service classes |
| WP-08 | Manifest Mutation Layer | Done | `workspaces/manifest_mutator.py` — typed mutation ops |

### Wave 2: Catalogs & Registry Migration

| WP | Title | Status | Key Deliverables |
|----|-------|--------|-----------------|
| WP-04 | Catalog / Registrar Foundations | Done | `framework/catalogs.py` — generic `Catalog[T]` abstraction |
| WP-05 | Plugin Discovery Catalog Bridge | Done | `build_catalogs_from_registries()` bridge; catalogs in context |
| WP-09 | Registry Consumer Migration | Done | Optional catalog params on `create_system`, `create_world_from_config`, `resolve_*_adapter`, `build_system_specific_analysis` |

### Wave 3: Cleanup & Verification

| WP | Title | Status | Key Deliverables |
|----|-------|--------|-----------------|
| WP-10 | Rendering Cleanup | Done | Rendering already local to command modules after WP-03 |
| WP-11 | Tests and Docs | Done | Architectural boundary tests; this status document |

## Key Architecture Rules (Implemented)

1. **Composition at the edge**: `build_context()` in `cli/context.py` is the
   single construction point. Services receive dependencies through constructors.

2. **No `inspect.signature`**: Handler contracts are explicit. All workspace
   handlers share the same `resolve_run_targets(... run_filter=None)` signature.

3. **No external DI container**: Manual composition only (`CLIContext` dataclass).

4. **Catalogs coexist with global registries**: Optional catalog parameters on
   consumer functions allow progressive migration without breaking existing code.

5. **Manifest mutations are typed**: `manifest_mutator.py` provides explicit
   business-level operations; `sync.py` handles only YAML I/O coordination.

6. **Rendering is local**: Each command module owns its formatting; services
   return structured data.

## File Map

```
src/axis/framework/cli/
├── __init__.py          # main(), re-exports
├── parser.py            # build_parser()
├── dispatch.py          # route args → command handlers
├── context.py           # CLIContext, build_context()
└── commands/
    ├── __init__.py
    ├── experiments.py
    ├── runs.py
    ├── compare.py
    ├── visualize.py
    └── workspaces.py

src/axis/framework/
├── catalogs.py          # Catalog[T], build_catalogs_from_registries()
└── workspaces/
    ├── manifest_mutator.py   # Typed mutation operations
    └── services/
        ├── __init__.py
        ├── run_service.py
        ├── compare_service.py
        └── inspection_service.py
```

## Test Coverage

New test files added during the refactoring:

- `tests/framework/test_cli_context.py` — composition root tests
- `tests/framework/test_workspace_services.py` — service layer tests
- `tests/framework/test_manifest_mutator.py` — mutation layer tests
- `tests/framework/test_catalogs.py` — catalog abstraction tests
- `tests/framework/test_plugin_catalog_bridge.py` — discovery bridge tests
- `tests/framework/test_architecture_boundaries.py` — cross-cutting boundary tests

All 2202 tests pass (41 new tests added).
