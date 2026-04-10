# WP-1.4 Implementation Brief -- Framework Config Types

> **Updated:** This spec has been updated to reflect the final implementation.
> Key changes from the original spec:
> - Section 6 ("Regeneration Config is System Responsibility") is outdated.
>   Regeneration parameters now live in `BaseWorldConfig` (via `extra="allow"`),
>   not in `system.world_dynamics`. System config keys are
>   `{"agent", "policy", "transition"}`.
> - `BaseWorldConfig` now uses `extra="allow"` so grid-specific fields
>   pass through as extras while the SDK type remains minimal.

## Context

We are implementing the **modular architecture evolution** of the AXIS project. WP-1.1 defined the core SDK interfaces, WP-1.2 defined the world contracts (`Position`, `WorldView`, `ActionOutcome`, `BaseWorldConfig`), and WP-1.3 defined the replay contract (`WorldSnapshot`, `BaseStepTrace`, `BaseEpisodeTrace`).

This work package is **WP-1.4**. It defines the new configuration model for the modular framework: the typed framework config, the experiment config, and the OFAT parameter path resolution for the new prefixed dot-path scheme.

### Predecessor State (After WP-1.3)

```
src/axis/sdk/
    __init__.py                 # Full SDK exports
    interfaces.py               # System and sub-component interfaces
    types.py                    # DecideResult, TransitionResult, PolicyResult
    position.py                 # Position
    world_types.py              # CellView, WorldView, ActionOutcome, BaseWorldConfig
    actions.py                  # Base action constants
    snapshot.py                 # WorldSnapshot, snapshot_world
    trace.py                    # BaseStepTrace, BaseEpisodeTrace
```

### Current v0.1.0 Configuration

The existing config hierarchy in `axis_system_a`:

```
SimulationConfig                     # Top-level, flat structure
    general: GeneralConfig           # seed
    world: WorldConfig               # grid_width, grid_height, regen params, obstacle_density
    agent: AgentConfig               # initial_energy, max_energy, buffer_capacity
    policy: PolicyConfig             # selection_mode, temperature, stay_suppression, consume_weight
    transition: TransitionConfig     # move_cost, consume_cost, stay_cost, max_consume, energy_gain_factor
    execution: ExecutionConfig       # max_steps
    logging: LoggingConfig           # enabled, console, jsonl, verbosity
```

All 7 sections live under `SimulationConfig`. OFAT parameter paths are un-prefixed: `"agent.initial_energy"`, `"world.grid_width"`.

In the modular architecture, this splits into:

- **Framework config** (this WP): `general`, `execution`, `world` (structural only), `logging`
- **System config** (opaque dict): `agent`, `policy`, `transition`, `world_dynamics` (regen params)
- **Experiment config** (this WP): wraps framework config + system type + system dict + OFAT parameters

### Architectural Decisions (Binding)

- **Q6**: Unified config -- flat framework sections (`general`, `execution`, `world`, `logging`) + opaque `system: dict`
- **Q7**: Prefixed dot-paths for OFAT: `"framework.execution.max_steps"`, `"system.policy.temperature"`
- **Q12**: Framework owns world structure; system owns dynamics (regen params)

### Reference Documents

- `docs/architecture/evolution/architectural-vision-v0.2.0.md` -- Section 6 (Experimentation Framework)
- `docs/architecture/evolution/modular-architecture-roadmap.md` -- WP-1.4 definition
- `docs/architecture/evolution/modular-architecture-questions-answers.md` -- Q6, Q7, Q12

---

## Objective

Define the framework-level configuration types and OFAT parameter addressing. This includes:

1. `GeneralConfig` -- seed configuration
2. `ExecutionConfig` -- step limits and execution parameters
3. `LoggingConfig` -- logging toggles and paths
4. `FrameworkConfig` -- composite framework configuration
5. `ExperimentType` -- experiment type enum
6. `ExperimentConfig` -- the top-level experiment definition
7. OFAT parameter path resolution functions for the new prefixed scheme

These are **typed Pydantic models with validation**. The OFAT functions are implemented with full logic, as they are purely config-manipulation code.

---

## Scope

### 1. Sub-Configuration Types

**File**: `src/axis/framework/config.py`

```python
from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig


class GeneralConfig(BaseModel):
    """General experiment configuration."""

    model_config = ConfigDict(frozen=True)

    seed: int


class ExecutionConfig(BaseModel):
    """Execution control parameters."""

    model_config = ConfigDict(frozen=True)

    max_steps: int = Field(..., gt=0)


class LoggingConfig(BaseModel):
    """Logging configuration.

    Controls console output, JSONL file logging, and verbosity.
    """

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    console_enabled: bool = True
    jsonl_enabled: bool = False
    jsonl_path: str | None = None
    include_decision_trace: bool = True
    include_transition_trace: bool = True
    verbosity: str = "compact"    # "compact" or "verbose"

    @model_validator(mode="after")
    def _validate_jsonl(self) -> LoggingConfig:
        if self.jsonl_enabled and self.jsonl_path is None:
            raise ValueError("jsonl_path must be set when jsonl_enabled is True")
        return self
```

**Design notes**:

- `GeneralConfig`, `ExecutionConfig`, `LoggingConfig` carry forward from v0.1.0 with identical fields
- `LoggingConfig` preserves the jsonl validation rule
- These are framework-owned -- all systems share the same execution and logging config

### 2. FrameworkConfig

**File**: `src/axis/framework/config.py` (same file)

```python
class FrameworkConfig(BaseModel):
    """Complete framework configuration.

    Contains all framework-owned settings. System-specific settings
    are not included here -- they travel as an opaque dict in
    ExperimentConfig.system.
    """

    model_config = ConfigDict(frozen=True)

    general: GeneralConfig
    execution: ExecutionConfig
    world: BaseWorldConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
```

**Design notes**:

- `world` uses `BaseWorldConfig` from the SDK (WP-1.2) -- framework-level structural config only
- `logging` has a defaulting factory, same as v0.1.0
- This replaces the framework-owned portion of `SimulationConfig`

### 3. ExperimentType Enum

**File**: `src/axis/framework/config.py` (same file)

```python
class ExperimentType(str, enum.Enum):
    """Type of experiment."""

    SINGLE_RUN = "single_run"
    OFAT = "ofat"
```

Carried forward unchanged from `axis_system_a.experiment.ExperimentType`.

### 4. ExperimentConfig

**File**: `src/axis/framework/config.py` (same file)

```python
class ExperimentConfig(BaseModel):
    """Top-level experiment definition.

    Per Q6=C: framework sections are flat at the top level
    (general, execution, world, logging). The system section
    is an opaque dict validated by the system at instantiation.
    """

    model_config = ConfigDict(frozen=True)

    # ── System identification ──
    system_type: str

    # ── Experiment parameters ──
    experiment_type: ExperimentType

    # ── Framework config (flat sections) ──
    general: GeneralConfig
    execution: ExecutionConfig
    world: BaseWorldConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # ── System config (opaque) ──
    system: dict[str, Any]

    # ── Run parameters ──
    num_episodes_per_run: int = Field(..., gt=0)
    agent_start_position: Position = Field(default_factory=lambda: Position(x=0, y=0))

    # ── OFAT parameters ──
    parameter_path: str | None = None
    parameter_values: tuple[Any, ...] | None = None

    @model_validator(mode="after")
    def _validate_ofat(self) -> ExperimentConfig:
        if self.experiment_type == ExperimentType.SINGLE_RUN:
            if self.parameter_path is not None or self.parameter_values is not None:
                raise ValueError(
                    "parameter_path and parameter_values must be None for single_run"
                )
        elif self.experiment_type == ExperimentType.OFAT:
            if self.parameter_path is None or self.parameter_values is None:
                raise ValueError(
                    "parameter_path and parameter_values are required for ofat"
                )
            if len(self.parameter_values) == 0:
                raise ValueError("parameter_values must be non-empty for ofat")
        return self
```

**Design notes**:

- `system_type` is a string -- looked up in the system registry (WP-3.1)
- Framework sections are flat: `general`, `execution`, `world`, `logging` (per Q6=C)
- `system` is `dict[str, Any]` -- the framework does not validate it; the system does at instantiation
- `parameter_path` uses the new prefixed scheme: `"framework.execution.max_steps"` or `"system.policy.temperature"`
- The OFAT validator matches v0.1.0 rules: single_run requires no OFAT fields, ofat requires both fields non-empty
- `agent_start_position` defaults to `(0, 0)`, matching v0.1.0

**Relationship to `FrameworkConfig`**:

`ExperimentConfig` contains the same framework fields (`general`, `execution`, `world`, `logging`) at the top level. A `FrameworkConfig` can be extracted from an `ExperimentConfig`:

```python
def extract_framework_config(experiment_config: ExperimentConfig) -> FrameworkConfig:
    """Extract the FrameworkConfig from an ExperimentConfig."""
    return FrameworkConfig(
        general=experiment_config.general,
        execution=experiment_config.execution,
        world=experiment_config.world,
        logging=experiment_config.logging,
    )
```

This function is defined in the same module.

### 5. OFAT Parameter Path Resolution

**File**: `src/axis/framework/config.py` (same file)

OFAT parameter paths in the new architecture use prefixed dot-paths:

```
framework.general.seed
framework.execution.max_steps
framework.world.grid_width
system.agent.initial_energy
system.policy.temperature
```

The first segment is the **domain prefix** (`framework` or `system`). The remaining segments are the path within that domain.

```python
# Valid framework sections for OFAT addressing
_FRAMEWORK_SECTIONS: frozenset[str] = frozenset({
    "general", "execution", "world", "logging"
})


def parse_parameter_path(path: str) -> tuple[str, str, str]:
    """Parse a prefixed OFAT parameter path.

    Args:
        path: Dot-separated path like 'framework.execution.max_steps'
              or 'system.policy.temperature'.

    Returns:
        Tuple of (domain, section, field).
        domain is 'framework' or 'system'.

    Raises:
        ValueError: If the path is malformed or references invalid sections.
    """
    parts = path.split(".")
    if len(parts) != 3:
        raise ValueError(
            f"Parameter path must have exactly 3 segments "
            f"(domain.section.field), got {len(parts)}: '{path}'"
        )
    domain, section, field = parts
    if domain not in ("framework", "system"):
        raise ValueError(
            f"Parameter path domain must be 'framework' or 'system', "
            f"got '{domain}' in '{path}'"
        )
    if domain == "framework" and section not in _FRAMEWORK_SECTIONS:
        raise ValueError(
            f"Invalid framework section '{section}' in '{path}'. "
            f"Valid sections: {sorted(_FRAMEWORK_SECTIONS)}"
        )
    return domain, section, field


def get_config_value(config: ExperimentConfig, path: str) -> Any:
    """Read a value from an ExperimentConfig using a prefixed dot-path.

    Args:
        config: The experiment config to read from.
        path: Prefixed dot-path (e.g., 'framework.execution.max_steps').

    Returns:
        The value at the specified path.

    Raises:
        ValueError: If the path is invalid.
        KeyError: If the field does not exist.
    """
    domain, section, field = parse_parameter_path(path)
    if domain == "framework":
        section_obj = getattr(config, section)
        if not hasattr(section_obj, field):
            raise KeyError(
                f"Framework section '{section}' has no field '{field}'"
            )
        return getattr(section_obj, field)
    else:  # system
        if section not in config.system:
            raise KeyError(f"System config has no section '{section}'")
        section_dict = config.system[section]
        if field not in section_dict:
            raise KeyError(
                f"System section '{section}' has no field '{field}'"
            )
        return section_dict[field]


def set_config_value(config: ExperimentConfig, path: str, value: Any) -> ExperimentConfig:
    """Return a new ExperimentConfig with one value overridden.

    Does not mutate the original config. Uses model_copy for framework
    fields and dict copy for system fields.

    Args:
        config: The experiment config to copy and modify.
        path: Prefixed dot-path (e.g., 'system.policy.temperature').
        value: The new value.

    Returns:
        A new ExperimentConfig with the value overridden.

    Raises:
        ValueError: If the path is invalid.
    """
    domain, section, field = parse_parameter_path(path)
    if domain == "framework":
        section_obj = getattr(config, section)
        new_section = section_obj.model_copy(update={field: value})
        return config.model_copy(update={section: new_section})
    else:  # system
        import copy
        new_system = copy.deepcopy(dict(config.system))
        if section not in new_system:
            new_system[section] = {}
        new_system[section][field] = value
        return config.model_copy(update={"system": new_system})
```

**Design notes**:

- `parse_parameter_path` is the central validation function -- validates domain, section (for framework), and structure
- `get_config_value` reads from framework sub-configs (via `getattr`) or system dict (via nested key access)
- `set_config_value` returns a **new** config (immutability), using `model_copy` for framework fields and `copy.deepcopy` for the system dict
- For framework paths, the field is validated against the actual Pydantic model at set time (Pydantic will reject invalid fields)
- For system paths, no field validation at the config level -- the system validates its own config at instantiation

### 6. Framework Package Exports

**File**: `src/axis/framework/__init__.py`

Update the framework `__init__.py` to export the public API:

```python
"""Experimentation Framework -- execution, persistence, config, CLI."""

from axis.framework.config import (
    ExperimentConfig,
    ExperimentType,
    ExecutionConfig,
    FrameworkConfig,
    GeneralConfig,
    LoggingConfig,
    extract_framework_config,
    get_config_value,
    parse_parameter_path,
    set_config_value,
)

__all__ = [
    "GeneralConfig",
    "ExecutionConfig",
    "LoggingConfig",
    "FrameworkConfig",
    "ExperimentType",
    "ExperimentConfig",
    "extract_framework_config",
    "parse_parameter_path",
    "get_config_value",
    "set_config_value",
]
```

---

## Out of Scope

Do **not** implement any of the following in WP-1.4:

- `RunConfig` / `RunResult` / `RunSummary` types (WP-3.3)
- `resolve_run_configs()` / `resolve_episode_seeds()` (WP-3.3)
- `ExperimentSummary` / `ExperimentResult` (WP-3.3)
- System registry (WP-3.1)
- `SystemAConfig` typed model (WP-2.3)
- Logging implementation (`AxisLogger`) -- carried forward separately
- `RunExecutor` / `ExperimentExecutor` (WP-3.3)
- Any `axis_system_a` modifications
- Any modifications outside `src/axis/framework/`, `src/axis/sdk/`, and `tests/`

---

## Architectural Constraints

### 1. Flat Framework Sections (Q6=C)

Framework config sections (`general`, `execution`, `world`, `logging`) are flat at the top level of `ExperimentConfig`, not nested under a `framework` key. This matches Q6=C.

The `FrameworkConfig` composite type exists for convenience (passing all framework settings as one object to the runner), but `ExperimentConfig` stores them individually.

### 2. Opaque System Config

`ExperimentConfig.system` is `dict[str, Any]`. The framework:

- Stores it
- Serializes it
- Passes it to the system factory
- Applies OFAT overrides to it (via `set_config_value`)

It does **not** validate the contents. The system validates its config blob at instantiation time.

### 3. Prefixed OFAT Paths (Q7=A)

Parameter paths use a mandatory prefix:

| Prefix | Scope | Example |
|--------|-------|---------|
| `framework.` | Framework-owned config sections | `framework.execution.max_steps` |
| `system.` | System-specific dict | `system.policy.temperature` |

This replaces the v0.1.0 un-prefixed scheme (`"execution.max_steps"`, `"agent.initial_energy"`). The prefix is mandatory -- there is no fallback.

### 4. Frozen Pydantic Models

All config types are frozen Pydantic models. Config modification produces new instances via `model_copy()`.

### 5. No Circular Dependencies

```
axis.sdk.position         -- no axis imports
axis.sdk.world_types      -- imports position
axis.framework.config     -- imports from axis.sdk (Position, BaseWorldConfig)
```

`axis.framework` depends on `axis.sdk`. No reverse dependency.

### 6. World Config is Extensible via Extras

`BaseWorldConfig` uses `ConfigDict(extra="allow")` with only `world_type: str` as a defined field. Grid-specific fields (`grid_width`, `grid_height`, `obstacle_density`, `resource_regen_rate`, etc.) pass through as Pydantic extras.

This means:
- `BaseWorldConfig(grid_width=10, grid_height=10, obstacle_density=0.1, resource_regen_rate=0.05)` stores all extra fields transparently
- OFAT paths like `framework.world.grid_width` work because `getattr(config.world, "grid_width")` accesses the extra field
- The world factory parses extras into `Grid2DWorldConfig` for type-safe validation
- Custom world types can pass different extras (e.g. `hex_radius=5`)

The system config dict contains only system-owned sections:

```json
{
    "system": {
        "agent": { "initial_energy": 50.0, "max_energy": 100.0, "buffer_capacity": 5 },
        "policy": { "selection_mode": "sample", "temperature": 1.0, ... },
        "transition": { "move_cost": 1.0, ... }
    }
}
```

The framework runner does not extract or pass regen parameters -- regeneration is handled internally by the world via `World.tick()`.

---

## Expected File Structure

After WP-1.4, these files are **new or modified**:

```
src/axis/framework/__init__.py              # MODIFIED (exports added)
src/axis/framework/config.py                # NEW (all config types + OFAT functions)
tests/framework/test_config.py          # NEW (verification tests)
tests/builders/config_builder.py        # MODIFIED (updated to use FrameworkConfig)
tests/builders/system_config_builder.py # UNCHANGED (still produces dicts)
tests/constants.py                      # UNCHANGED
```

Unchanged:

```
src/axis/sdk/                               # UNCHANGED
src/axis_system_a/                          # UNCHANGED
```

### Builder Update

The `FrameworkConfigBuilder` from WP-0.2 currently produces a plain `dict`. After WP-1.4, it should be updated to produce a `FrameworkConfig` instance instead. The builder API (method names, defaults) stays the same -- only the `build()` return type changes.

```python
# Before (WP-0.2)
def build(self) -> dict: ...

# After (WP-1.4)
def build(self) -> FrameworkConfig: ...
```

The `SystemAConfigBuilder` continues to produce a `dict` (System A's typed config is WP-2.3).

The `config_fixtures.py` fixtures should be updated accordingly:

- `framework_config_dict` renamed to `framework_config`, returns `FrameworkConfig`
- `system_a_config_dict` stays as-is (still a dict)
- `experiment_config_dict` renamed to `experiment_config`, returns `ExperimentConfig`

The old fixture names should be kept as aliases for backward compatibility with `test_infrastructure.py`.

---

## Testing Requirements

### Config type verification tests (`tests/framework/test_config.py`)

Must include:

1. **GeneralConfig**:
   - `GeneralConfig(seed=42)` constructs
   - Frozen: setting `seed` raises

2. **ExecutionConfig**:
   - `ExecutionConfig(max_steps=200)` constructs
   - `max_steps=0` raises validation error
   - Frozen

3. **LoggingConfig**:
   - Default construction: `LoggingConfig()` produces `enabled=True`, `console_enabled=True`, etc.
   - `LoggingConfig(jsonl_enabled=True, jsonl_path="/tmp/x.jsonl")` works
   - `LoggingConfig(jsonl_enabled=True)` without `jsonl_path` raises validation error
   - Frozen

4. **FrameworkConfig**:
   - Full construction with all sub-configs
   - `logging` defaults if not provided
   - Frozen
   - `extract_framework_config(experiment_config)` produces matching `FrameworkConfig`

5. **ExperimentConfig (single_run)**:
   - Minimal construction with `experiment_type=SINGLE_RUN`, no OFAT fields
   - `parameter_path` provided for single_run raises
   - `system` is a dict, accepted as-is
   - `agent_start_position` defaults to `(0, 0)`

6. **ExperimentConfig (ofat)**:
   - Construction with `experiment_type=OFAT`, `parameter_path`, `parameter_values`
   - Missing `parameter_path` raises
   - Missing `parameter_values` raises
   - Empty `parameter_values` raises
   - `parameter_path="framework.execution.max_steps"` validates successfully
   - `parameter_path="system.policy.temperature"` validates successfully

7. **parse_parameter_path**:
   - `parse_parameter_path("framework.execution.max_steps")` returns `("framework", "execution", "max_steps")`
   - `parse_parameter_path("system.policy.temperature")` returns `("system", "policy", "temperature")`
   - `parse_parameter_path("invalid.a.b")` raises (bad domain)
   - `parse_parameter_path("framework.invalid.x")` raises (bad section)
   - `parse_parameter_path("a.b")` raises (too few segments)
   - `parse_parameter_path("a.b.c.d")` raises (too many segments)

8. **get_config_value**:
   - `get_config_value(config, "framework.execution.max_steps")` returns the max_steps value
   - `get_config_value(config, "framework.general.seed")` returns the seed
   - `get_config_value(config, "system.agent.initial_energy")` returns from system dict
   - `get_config_value(config, "system.nonexistent.field")` raises `KeyError`
   - `get_config_value(config, "framework.execution.nonexistent")` raises `KeyError`

9. **set_config_value**:
   - `set_config_value(config, "framework.execution.max_steps", 500)` returns new config with `max_steps=500`
   - Original config is unchanged (immutability)
   - `set_config_value(config, "system.policy.temperature", 2.0)` returns new config with updated system dict
   - Original system dict is unchanged
   - `set_config_value(config, "framework.general.seed", 99)` returns new config with `seed=99`

10. **Constants consistency**:
    - Default values in `FrameworkConfig` built from `FrameworkConfigBuilder().build()` match the constants in `tests/constants.py`
    - `DEFAULT_SEED`, `DEFAULT_MAX_STEPS`, `DEFAULT_GRID_WIDTH`, `DEFAULT_GRID_HEIGHT`, `DEFAULT_OBSTACLE_DENSITY`

### Builder update tests

The updated `FrameworkConfigBuilder.build()` now returns `FrameworkConfig`. The `test_infrastructure.py` tests must still pass. Add:

- `FrameworkConfigBuilder().build()` returns a `FrameworkConfig` instance (not dict)
- `FrameworkConfigBuilder().build().general.seed` equals `DEFAULT_SEED`
- `FrameworkConfigBuilder().with_seed(99).build().general.seed` equals `99`
- `FrameworkConfigBuilder().with_max_steps(500).build().execution.max_steps` equals `500`

### Existing test suite

All existing tests must still pass.

---

## Implementation Style

- Python 3.11+
- Frozen Pydantic `BaseModel` for all config types
- Pydantic `@model_validator` for cross-field validation
- `Field(...)` with constraints (`gt`, `ge`, `le`, `lt`)
- Clear docstrings on all types and functions
- Type hints throughout
- `copy.deepcopy` for safe dict mutation in `set_config_value`
- No dependencies beyond `pydantic`, `axis.sdk`, stdlib

---

## Expected Deliverable

1. `src/axis/framework/config.py` with all config types and OFAT functions
2. Updated `src/axis/framework/__init__.py` with exports
3. Updated `tests/builders/config_builder.py` to produce `FrameworkConfig`
4. Updated `tests/fixtures/config_fixtures.py` with typed fixtures
5. Verification tests at `tests/framework/test_config.py`
6. Updated `tests/test_infrastructure.py` if needed (builder return type changed)
7. Confirmation that all existing tests still pass

---

## Important Final Constraint

This WP is the last in Phase 1 (SDK and Contracts). After it completes, the full type system of the new architecture is defined:

| WP | Types defined | Location |
|----|--------------|----------|
| WP-1.1 | `SystemInterface`, sub-component interfaces, `DecideResult`, `TransitionResult`, `PolicyResult` | `axis.sdk` |
| WP-1.2 | `Position`, `CellView`, `WorldView`, `ActionOutcome`, `BaseWorldConfig`, base actions | `axis.sdk` |
| WP-1.3 | `WorldSnapshot`, `BaseStepTrace`, `BaseEpisodeTrace` | `axis.sdk` |
| WP-1.4 | `FrameworkConfig`, `ExperimentConfig`, OFAT resolution | `axis.framework` |

Phase 2 (Extraction and Conformance) will populate these types with concrete implementations: moving the `World` class, building the action engine, wrapping System A in SDK interfaces, and writing the new test suite.

The most important property of the config types is **consistency with the existing test fixtures**. The default values in `FrameworkConfig` (built via `FrameworkConfigBuilder`) must match `tests/constants.py`, which in turn matches the v0.1.0 `_BASE_CONFIG_DICT` from `tests/fixtures/scenario_fixtures.py`. When Phase 2 runs behavioral equivalence tests, these defaults ensure numerical identity.
