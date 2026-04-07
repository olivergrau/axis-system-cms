# WP-3.1 Implementation Brief -- System Registry

## Context

We are implementing **Phase 3 -- Framework Alignment** of the AXIS modular architecture evolution. Phase 2 delivered the world model (`axis.world`), action engine, and System A conforming to `SystemInterface`. Phase 3 makes the framework system-agnostic by routing through SDK interfaces.

This work package is **WP-3.1**. It implements the system registry: a simple, explicit mechanism for mapping system type strings to factory functions that produce `SystemInterface` implementations.

### Predecessor State (After Phase 2)

```
src/axis/
    sdk/
        interfaces.py       # SystemInterface, SensorInterface, etc.
        types.py             # DecideResult, TransitionResult, PolicyResult
        world_types.py       # WorldView, ActionOutcome, BaseWorldConfig, CellView
        trace.py             # BaseStepTrace, BaseEpisodeTrace
        snapshot.py          # WorldSnapshot, snapshot_world
        actions.py           # BASE_ACTIONS, MOVEMENT_DELTAS
        position.py          # Position
    framework/
        __init__.py          # re-exports from config.py
        config.py            # FrameworkConfig, ExperimentConfig, OFAT utilities
    world/
        model.py             # CellType, RegenerationMode, Cell, World
        factory.py           # create_world()
        actions.py           # ActionRegistry, create_action_registry()
        dynamics.py          # apply_regeneration()
    systems/system_a/
        system.py            # SystemA (implements SystemInterface)
        config.py            # SystemAConfig
        actions.py           # handle_consume()
        ...                  # sensor, drive, policy, transition, memory, types
```

The framework currently has `config.py` but no registry, runner, or executor modules.

### Architectural Decisions (Binding)

- **Q11 = (A) Explicit registry in code**: A simple `dict[str, SystemFactory]` mapping system type strings to factory callables. No classpath scanning, no plugins, no dynamic loading.
- **Q1 = Two-phase step**: Framework calls `system.decide()` then `system.transition()`. The registry only handles system **creation**, not step orchestration.
- **Clean break (Q13)**: No need to support legacy `axis_system_a` through the registry.

### Reference Documents

- `docs/v0.2.0/architecture/evolution/modular-architecture-roadmap.md` -- WP-3.1 definition
- `docs/v0.2.0/architecture/evolution/modular-architecture-questions-answers.md` -- Q11 decision
- `src/axis/sdk/interfaces.py` -- `SystemInterface` protocol

---

## Objective

Provide a system registry that:

1. Maps system type strings (e.g., `"system_a"`) to factory functions
2. Allows programmatic registration of new system types
3. Provides clear error reporting for unknown system types
4. Auto-registers System A at import time
5. Is used by the framework runner and executors (WP-3.2, WP-3.3) to resolve system types from `ExperimentConfig.system_type`

---

## Scope

### 1. System Factory Protocol

A system factory is a callable that takes a system config dict and returns a `SystemInterface` instance.

```python
SystemFactory = Callable[[dict[str, Any]], SystemInterface]
```

The factory receives the `system: dict[str, Any]` section from `ExperimentConfig`. It is responsible for:
- Parsing and validating the config dict into system-specific typed config
- Constructing the system instance
- Registering any custom actions the system needs (e.g., `handle_consume`)

The factory does **not** receive `FrameworkConfig` -- it only sees its own config dict. Framework-level concerns (seed, max_steps, world shape) are handled by the runner.

### 2. Registry Module (`axis/framework/registry.py`)

```python
"""System registry: maps system type strings to factory functions."""

from __future__ import annotations

from typing import Any

from axis.sdk.interfaces import SystemInterface

SystemFactory = Callable[[dict[str, Any]], SystemInterface]

# Module-level registry
_SYSTEM_REGISTRY: dict[str, SystemFactory] = {}


def register_system(system_type: str, factory: SystemFactory) -> None:
    """Register a system factory for a given system type.

    Raises ValueError if the system type is already registered.
    """


def get_system_factory(system_type: str) -> SystemFactory:
    """Look up a system factory by type string.

    Raises KeyError with a descriptive message listing available types
    if the requested type is not registered.
    """


def registered_system_types() -> tuple[str, ...]:
    """Return all registered system type strings (sorted)."""


def create_system(system_type: str, system_config: dict[str, Any]) -> SystemInterface:
    """Convenience: look up factory and create a system instance.

    Equivalent to get_system_factory(system_type)(system_config).
    """
```

### 3. System A Factory

The System A factory function is defined in the registry module (or imported from System A's package) and auto-registered.

```python
def _system_a_factory(system_config: dict[str, Any]) -> SystemInterface:
    """Factory for System A."""
    from axis.systems.system_a import SystemA, SystemAConfig
    config = SystemAConfig(**system_config)
    return SystemA(config)
```

**Auto-registration**: System A is registered when `axis.framework.registry` is first imported:

```python
# At module level, after the registry functions:
register_system("system_a", _system_a_factory)
```

This ensures `"system_a"` is always available without requiring consumers to manually register it.

### 4. Action Registration

Action registration (e.g., `handle_consume` for System A) is **not** part of the system registry. Actions are registered by the framework runner (WP-3.2) when setting up an episode. The runner will:

1. Call `create_system(system_type, config)` to get a `SystemInterface`
2. Call `system.action_space()` to discover what actions the system needs
3. Register system-specific action handlers with the `ActionRegistry`

The system factory returns a system instance. The action handlers are a separate concern managed by the runner's setup phase.

**Design decision**: Each system must provide a way for the runner to obtain its custom action handlers. Two options:

- **(A) Convention-based import**: The runner imports `handle_consume` from `axis.systems.system_a.actions` based on `system_type`.
- **(B) System provides handlers**: The `SystemInterface` is extended with an optional `action_handlers() -> dict[str, ActionHandler]` method.

**Choice: (B)**. This is cleaner and avoids import-path magic. The system interface already defines `action_space()` (what actions exist). Adding `action_handlers()` (how custom actions work) is a natural complement.

We add one method to `SystemInterface`:

```python
def action_handlers(self) -> dict[str, Any]:
    """Return custom action handlers for registration with ActionRegistry.

    Returns a mapping of action_name -> handler_callable for actions
    beyond the base set (up/down/left/right/stay). The framework
    runner registers these with the ActionRegistry before episode execution.

    Systems with no custom actions return an empty dict.
    """
```

System A's implementation:

```python
def action_handlers(self) -> dict[str, Any]:
    from axis.systems.system_a.actions import handle_consume
    return {"consume": handle_consume}
```

### 5. Package Exports

`axis/framework/__init__.py` updated to include registry exports:

```python
from axis.framework.registry import (
    SystemFactory,
    create_system,
    get_system_factory,
    register_system,
    registered_system_types,
)
```

---

## Out of Scope

Do **not** implement any of the following in WP-3.1:

- Framework episode runner (WP-3.2)
- Run/experiment executors (WP-3.3)
- Persistence layer changes (WP-3.4)
- CLI changes (WP-3.5)
- Dynamic plugin loading, classpath scanning, or entry-point-based discovery
- System B / System A+W (Phase 5)

---

## Architectural Constraints

### 1. Simple Dict Registry

The registry is a module-level `dict[str, SystemFactory]`. No class wrapping, no metaclass magic, no singleton pattern. The dict is private (`_SYSTEM_REGISTRY`); public access is through the four functions.

### 2. Duplicate Registration is an Error

Calling `register_system("system_a", ...)` when `"system_a"` is already registered raises `ValueError`. This prevents accidental overwrites. Systems are registered once.

### 3. Unknown System Type is a KeyError

Calling `get_system_factory("unknown")` raises `KeyError` with a message like:
`"Unknown system type 'unknown'. Available types: system_a"`

### 4. Factory Receives Only System Config

The factory signature is `(dict[str, Any]) -> SystemInterface`. It does not receive `FrameworkConfig`, `seed`, `max_steps`, or world-related parameters. The system only sees its own config section.

### 5. action_handlers() Contract

`action_handlers()` returns handlers for actions **not in `BASE_ACTIONS`**. The framework runner will verify that every action in `system.action_space()` either exists in `BASE_ACTIONS` or has a handler provided by `action_handlers()`. Missing handlers are an error at runner setup time, not at registry time.

---

## Expected File Structure

After WP-3.1, these files are **new**:

```
src/axis/framework/registry.py          # NEW (system registry)
tests/v02/framework/test_registry.py    # NEW (registry tests)
```

These files are **modified**:

```
src/axis/framework/__init__.py          # MODIFIED (add registry exports)
src/axis/sdk/interfaces.py              # MODIFIED (add action_handlers to SystemInterface)
src/axis/systems/system_a/system.py     # MODIFIED (implement action_handlers)
tests/v02/test_scaffold.py              # MODIFIED (update framework exports)
```

---

## Testing Requirements

### Registry Tests (`tests/v02/framework/test_registry.py`)

| Test | Description |
|------|-------------|
| `test_system_a_auto_registered` | `"system_a" in registered_system_types()` on import |
| `test_create_system_a` | `create_system("system_a", config_dict)` returns valid `SystemInterface` |
| `test_created_system_type` | `system.system_type() == "system_a"` |
| `test_created_system_action_space` | `system.action_space()` includes base + consume |
| `test_unknown_system_type_raises` | `get_system_factory("nonexistent")` raises `KeyError` |
| `test_unknown_system_error_message` | Error includes available types |
| `test_duplicate_registration_raises` | `register_system("system_a", ...)` twice raises `ValueError` |
| `test_register_custom_system` | Register mock factory, then `create_system()` returns it |
| `test_registered_system_types_sorted` | `registered_system_types()` returns sorted tuple |
| `test_factory_receives_config` | Factory function is called with the config dict |
| `test_action_handlers_system_a` | `system.action_handlers()` returns `{"consume": callable}` |
| `test_action_handlers_contract` | All non-base actions in `action_space()` have handlers |

All existing tests (1657) must continue to pass.

---

## Implementation Style

- Python 3.11+
- Module-level registry (not a class)
- `typing.Protocol` already used for `SystemInterface`
- Factory type alias: `SystemFactory = Callable[[dict[str, Any]], SystemInterface]`
- Auto-registration at module load time (bottom of `registry.py`)
- Tests follow established patterns from `tests/v02/`

---

## Expected Deliverable

1. Registry module at `src/axis/framework/registry.py`
2. `action_handlers()` method added to `SystemInterface` protocol
3. `action_handlers()` implemented in `SystemA`
4. Updated `src/axis/framework/__init__.py` with registry exports
5. Updated `tests/v02/test_scaffold.py`
6. Registry tests at `tests/v02/framework/test_registry.py`
7. Confirmation that all tests pass
