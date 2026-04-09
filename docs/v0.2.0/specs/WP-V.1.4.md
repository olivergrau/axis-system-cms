# WP-V.1.4 Implementation Brief -- Visualization Registry

## Context

WP-V.1.2 defined the adapter protocols. WP-V.1.3 provided the fallback adapters (`DefaultWorldVisualizationAdapter`, `NullSystemVisualizationAdapter`). This work package implements the registry that maps `world_type` and `system_type` strings to adapter factories, with automatic fallback to the defaults.

The visualization registry follows the same pattern as the existing system registry (`axis/framework/registry.py`) and world registry (`axis/world/registry.py`): module-level dict, `register_*()` functions, `resolve_*()` functions with fallback behavior.

### Predecessor State (After WP-V.1.3)

```
src/axis/visualization/
    __init__.py
    types.py                             # Supporting types
    protocols.py                         # Adapter protocols
    adapters/
        __init__.py
        default_world.py                 # DefaultWorldVisualizationAdapter
        null_system.py                   # NullSystemVisualizationAdapter
```

### Existing Registry Patterns

The project has two established registries:

**System registry** (`axis/framework/registry.py`):
- `_SYSTEM_REGISTRY: dict[str, SystemFactory]`
- `register_system(type, factory)` -- raises `ValueError` on duplicate
- `get_system_factory(type)` -- raises `KeyError` on unknown
- `create_system(type, config)` -- convenience wrapper

**World registry** (`axis/world/registry.py`):
- `_WORLD_REGISTRY: dict[str, WorldFactory]`
- `register_world(type, factory)` -- raises `ValueError` on duplicate
- `get_world_factory(type)` -- raises `KeyError` on unknown
- `create_world_from_config(config, position, seed)` -- convenience wrapper

**Key difference for visualization**:  The visualization registry does NOT raise on unknown types. It falls back to the default/null adapters. This is by design -- the viewer should render gracefully even for world/system types that don't have specialized visualization.

### Architectural Decisions (Binding)

- **D4**: Default adapters for unknown types -- graceful degradation
- `resolve_world_adapter()` falls back to `DefaultWorldVisualizationAdapter`
- `resolve_system_adapter()` falls back to `NullSystemVisualizationAdapter`

### Reference Documents

- `docs/v0.2.0/architecture/evolution/visualization-architecture.md` -- Section 12 (Adapter Resolution and Registration)
- `docs/v0.2.0/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.1.4

---

## Objective

Create `src/axis/visualization/registry.py` with:

1. World visualization adapter registration and resolution (with fallback)
2. System visualization adapter registration and resolution (with fallback)
3. Convenience query for registered types

The registry is used at viewer launch time (WP-V.4.4) to resolve adapters based on `world_type` and `system_type` from the loaded `BaseEpisodeTrace`.

---

## Scope

### 1. Type Aliases

```python
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from axis.visualization.adapters.default_world import DefaultWorldVisualizationAdapter
from axis.visualization.adapters.null_system import NullSystemVisualizationAdapter

# Factory types
WorldVisFactory = Callable[[dict[str, Any]], Any]
SystemVisFactory = Callable[[], Any]
```

**Design notes**:

- `WorldVisFactory` takes `world_config: dict[str, Any]` and returns an object satisfying `WorldVisualizationAdapter` protocol. The return type is `Any` because the protocol uses structural subtyping.
- `SystemVisFactory` takes no arguments and returns an object satisfying `SystemVisualizationAdapter` protocol.
- The factory signatures mirror the architecture spec Section 12.1.

### 2. Module-Level Registries

```python
_WORLD_VIS_REGISTRY: dict[str, WorldVisFactory] = {}
_SYSTEM_VIS_REGISTRY: dict[str, SystemVisFactory] = {}
```

### 3. Registration Functions

```python
def register_world_visualization(
    world_type: str,
    factory: WorldVisFactory,
) -> None:
    """Register a world visualization adapter factory.

    Called at module import time by each world package that provides
    a visualization adapter.

    Raises ValueError if the world_type is already registered.
    """
    if world_type in _WORLD_VIS_REGISTRY:
        raise ValueError(
            f"World visualization for '{world_type}' is already registered."
        )
    _WORLD_VIS_REGISTRY[world_type] = factory


def register_system_visualization(
    system_type: str,
    factory: SystemVisFactory,
) -> None:
    """Register a system visualization adapter factory.

    Called at module import time by each system package that provides
    a visualization adapter.

    Raises ValueError if the system_type is already registered.
    """
    if system_type in _SYSTEM_VIS_REGISTRY:
        raise ValueError(
            f"System visualization for '{system_type}' is already registered."
        )
    _SYSTEM_VIS_REGISTRY[system_type] = factory
```

### 4. Resolution Functions

```python
def resolve_world_adapter(
    world_type: str,
    world_config: dict[str, Any],
) -> Any:
    """Resolve a world visualization adapter by type.

    If a factory is registered for world_type, calls it with world_config.
    Otherwise, returns a DefaultWorldVisualizationAdapter (graceful fallback).
    """
    factory = _WORLD_VIS_REGISTRY.get(world_type)
    if factory is not None:
        return factory(world_config)
    return DefaultWorldVisualizationAdapter()


def resolve_system_adapter(
    system_type: str,
) -> Any:
    """Resolve a system visualization adapter by type.

    If a factory is registered for system_type, calls it.
    Otherwise, returns a NullSystemVisualizationAdapter (graceful fallback).
    """
    factory = _SYSTEM_VIS_REGISTRY.get(system_type)
    if factory is not None:
        return factory()
    return NullSystemVisualizationAdapter()
```

**Key difference from world/system registries**: No `KeyError` on unknown types. The visualization registry uses graceful fallback.

### 5. Query Functions

```python
def registered_world_visualizations() -> tuple[str, ...]:
    """Return all registered world visualization type strings (sorted)."""
    return tuple(sorted(_WORLD_VIS_REGISTRY))


def registered_system_visualizations() -> tuple[str, ...]:
    """Return all registered system visualization type strings (sorted)."""
    return tuple(sorted(_SYSTEM_VIS_REGISTRY))
```

### 6. Test Isolation Helper

```python
def _clear_registries() -> None:
    """Clear all registrations. FOR TESTING ONLY.

    Used by test fixtures to ensure registry state is clean between tests.
    """
    _WORLD_VIS_REGISTRY.clear()
    _SYSTEM_VIS_REGISTRY.clear()
```

This follows the pattern of test-only helpers. Module-level registries need explicit clearing in tests to avoid cross-test contamination.

### 7. No Auto-Registration

Unlike the system registry (which auto-registers `system_a` and `system_b` at import time), the visualization registry does **not** auto-register any adapters. Registration happens when the concrete adapter modules are imported (WP-V.2.x). This keeps the registry module dependency-free.

### 8. Module Docstring

```python
"""Visualization adapter registry.

Maps world_type and system_type strings to visualization adapter factories.
Falls back to DefaultWorldVisualizationAdapter and NullSystemVisualizationAdapter
for unknown types, enabling graceful degradation.

Registration pattern (called by concrete adapter modules):

    # In axis/world/grid_2d/visualization.py
    from axis.visualization.registry import register_world_visualization
    register_world_visualization("grid_2d", lambda wc: Grid2DWorldVisualizationAdapter(wc))

    # In axis/systems/system_a/visualization.py
    from axis.visualization.registry import register_system_visualization
    register_system_visualization("system_a", lambda: SystemAVisualizationAdapter())

Resolution (called by session controller at viewer launch):

    world_adapter = resolve_world_adapter(episode.world_type, episode.world_config)
    system_adapter = resolve_system_adapter(episode.system_type)
"""
```

---

## Out of Scope

Do **not** implement any of the following in WP-V.1.4:

- Concrete adapter implementations (WP-V.2.x)
- Adapter registration calls (happen in WP-V.2.x when concrete adapters are implemented)
- Any PySide6 or UI code
- Session controller or launch logic (WP-V.4.4)
- Any modifications to existing registries (system, world)

---

## Architectural Constraints

### 1. Graceful Fallback

The resolve functions must **never raise** on unknown types. They return default/null adapters instead. This is a deliberate design difference from the system and world registries.

### 2. No Circular Dependencies

The registry imports only from:
- `axis.visualization.adapters.default_world` -- `DefaultWorldVisualizationAdapter`
- `axis.visualization.adapters.null_system` -- `NullSystemVisualizationAdapter`

It does **not** import from `axis.visualization.protocols` (protocols are for type-checking, not runtime). It does **not** import from any world or system package.

### 3. Module-Level State

Like the existing registries, visualization registration state is module-level. This means:
- Registration order matters in tests (use `_clear_registries()` in fixtures)
- Registration happens at import time for concrete adapters
- The registry is a singleton per process

### 4. Duplicate Registration Prevention

`register_world_visualization()` and `register_system_visualization()` raise `ValueError` on duplicate registration, consistent with existing registry behavior.

---

## Testing Requirements

**File**: `tests/v02/visualization/test_registry.py` (new)

Use a `pytest` fixture that calls `_clear_registries()` before each test to ensure isolation.

### Registration tests

1. **`test_register_world_visualization`**:
   - Register a factory for `"test_world"`, assert `"test_world"` in `registered_world_visualizations()`

2. **`test_register_system_visualization`**:
   - Register a factory for `"test_system"`, assert `"test_system"` in `registered_system_visualizations()`

3. **`test_register_world_duplicate_raises`**:
   - Register `"test_world"`, register again -- assert `ValueError`

4. **`test_register_system_duplicate_raises`**:
   - Register `"test_system"`, register again -- assert `ValueError`

### Resolution tests

5. **`test_resolve_world_adapter_registered`**:
   - Register a factory for `"test_world"` that returns a mock adapter
   - `resolve_world_adapter("test_world", {})` returns the mock adapter

6. **`test_resolve_world_adapter_unknown_falls_back`**:
   - Without registering anything, `resolve_world_adapter("unknown", {})` returns a `DefaultWorldVisualizationAdapter`

7. **`test_resolve_system_adapter_registered`**:
   - Register a factory for `"test_system"` that returns a mock adapter
   - `resolve_system_adapter("test_system")` returns the mock adapter

8. **`test_resolve_system_adapter_unknown_falls_back`**:
   - Without registering anything, `resolve_system_adapter("unknown")` returns a `NullSystemVisualizationAdapter`

### Factory argument tests

9. **`test_world_vis_factory_receives_world_config`**:
   - Register a factory that captures its argument
   - Call `resolve_world_adapter("test_world", {"grid_width": 10})`
   - Assert the factory received `{"grid_width": 10}`

10. **`test_system_vis_factory_called_without_args`**:
    - Register a factory that records it was called
    - Call `resolve_system_adapter("test_system")`
    - Assert the factory was called (no arguments)

### Query tests

11. **`test_registered_world_visualizations_empty`**:
    - After clearing, assert returns empty tuple

12. **`test_registered_world_visualizations_sorted`**:
    - Register `"beta"` then `"alpha"`, assert result is `("alpha", "beta")`

13. **`test_registered_system_visualizations_sorted`**:
    - Register `"sys_b"` then `"sys_a"`, assert result is `("sys_a", "sys_b")`

### Clear helper test

14. **`test_clear_registries`**:
    - Register entries in both registries
    - Call `_clear_registries()`
    - Assert both are empty

### Import test

15. **`test_import_registry_functions`**:
    - `from axis.visualization.registry import register_world_visualization, register_system_visualization, resolve_world_adapter, resolve_system_adapter, registered_world_visualizations, registered_system_visualizations`
    - Assert all are callable

### Existing tests

All existing tests must continue to pass.

---

## Implementation Style

- Python 3.11+
- Module-level dicts following the existing registry pattern
- Type aliases for factory callables
- Clear docstrings with usage examples
- `_clear_registries()` prefixed with underscore to indicate test-only use

---

## Expected Deliverable

1. `src/axis/visualization/registry.py` with registration, resolution, query, and clear functions
2. `tests/v02/visualization/test_registry.py` with all tests
3. Confirmation that all existing tests still pass

---

## Expected File Structure

After WP-V.1.4:

```
src/axis/visualization/
    __init__.py                          # UNCHANGED
    types.py                             # UNCHANGED (from WP-V.1.1)
    protocols.py                         # UNCHANGED (from WP-V.1.2)
    registry.py                          # NEW
    adapters/
        __init__.py                      # UNCHANGED (from WP-V.1.3)
        default_world.py                 # UNCHANGED (from WP-V.1.3)
        null_system.py                   # UNCHANGED (from WP-V.1.3)

tests/v02/visualization/
    __init__.py                          # UNCHANGED
    test_types.py                        # UNCHANGED (from WP-V.1.1)
    test_protocols.py                    # UNCHANGED (from WP-V.1.2)
    test_default_adapters.py             # UNCHANGED (from WP-V.1.3)
    test_registry.py                     # NEW
```

---

## Important Final Constraint

The visualization registry is approximately 60-80 lines of production code. It is deliberately simple: two dicts, four mutation functions, two resolution functions with fallback, two query functions, and one test helper.

The critical behavior to test is the **fallback**: `resolve_world_adapter("unknown_type", {})` must return a working `DefaultWorldVisualizationAdapter`, not raise an error. This is what enables the viewer to open any replay, even for world/system types that were added after the viewer was built.

After WP-V.1.4, Phase V-1 is complete. The visualization package has:
- All structured data types (types.py)
- Both adapter protocols (protocols.py)
- Fallback adapters (adapters/default_world.py, adapters/null_system.py)
- The adapter registry (registry.py)

This forms the complete foundation for concrete adapters (Phase V-2) and the base layer (Phase V-3).
