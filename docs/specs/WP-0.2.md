# WP-0.2 Implementation Brief -- Test Infrastructure Preparation

> **Updated:** This spec has been updated to reflect the final implementation.
> Key changes from the original spec:
> - `SystemAConfigBuilder` no longer includes `world_dynamics` or
>   `with_regen_rate()`. Builder output keys are `{"agent", "policy",
>   "transition"}`. The `DEFAULT_REGEN_RATE` constant has been removed.
> - Regeneration parameters moved from system config to `BaseWorldConfig`.

## Context

We are implementing the **modular architecture evolution** of the AXIS project. WP-0.1 established the `axis` package scaffold and the `tests/` directory tree.

This work package is **WP-0.2**. It populates the new test infrastructure with shared utilities, builders, fixtures, and assertion helpers that subsequent work packages will rely on when writing tests for the new `axis` package.

### Predecessor State (After WP-0.1)

```
src/axis/                                   # Empty package scaffold (docstring-only __init__.py files)
    sdk/, framework/, world/, systems/system_a/, visualization/

src/axis_system_a/                          # Unchanged, fully functional

tests/
    conftest.py                             # Existing: registers axis_system_a fixtures
    builders/                               # Existing: WorldBuilder, AgentStateBuilder, MemoryBuilder
    fixtures/                               # Existing: world_fixtures, agent_fixtures, etc.
    utils/                                  # Existing: assertions, trace_assertions
    unit/, integration/, behavioral/, e2e/  # Existing test suites (1215+ tests)
    visualization/                          # Existing visualization tests
    v02/                                    # New (from WP-0.1): empty scaffold
        conftest.py
        sdk/, framework/, world/, systems/system_a/, visualization/
        test_scaffold.py
```

The existing test infrastructure uses a well-established pattern:

- **Builders** (`tests/builders/`): Fluent builder classes for constructing domain objects (`WorldBuilder`, `AgentStateBuilder`, `MemoryBuilder`)
- **Fixtures** (`tests/fixtures/`): Pytest fixtures providing pre-built objects (`small_world`, `valid_config`, `empty_cell`, etc.), registered via `conftest.py`
- **Utils** (`tests/utils/`): Assertion helpers (`assert_model_frozen`, `assert_probabilities_valid`, `assert_trace_energy_consistent`, etc.)
- **Root conftest**: Registers fixture modules via `pytest_plugins`

All existing utilities import from `axis_system_a`. The new test infrastructure must import from `axis` -- but since `axis` has no types yet (only empty `__init__.py` files), WP-0.2 prepares the **structure and patterns** that later WPs will populate with concrete builders and fixtures.

### Architectural Decisions (Binding)

- **Q18**: New test suites for new structure; old tests can be rewritten
- **Q5**: Single `axis` package with sub-packages

### Reference Documents

- `docs/architecture/evolution/architectural-vision-v0.2.0.md` -- Section 3 (package structure)
- `docs/architecture/evolution/modular-architecture-roadmap.md` -- WP-0.2 definition
- `docs/architecture/evolution/modular-architecture-questions-answers.md` -- Q18

---

## Objective

Establish the test utility infrastructure for the new `axis` package. This includes:

1. Builder base class and conventions
2. Assertion helper modules (empty, with documented patterns)
3. Fixture conftest structure
4. Shared constants and factory functions

The goal is that when WP-1.1 (SDK interfaces) and WP-1.2 (world contracts) begin, their test authors find a ready-made infrastructure and only need to add domain-specific builders and fixtures -- not reinvent the test patterns.

This WP produces **reusable test scaffolding**, not domain tests. It writes no tests that exercise `axis` domain behavior (there is no domain behavior yet).

---

## Scope

### 1. Builder Base Pattern

Create a documented builder convention under `tests/builders/`.

**File**: `tests/builders/__init__.py`

Contains a brief docstring explaining the builder convention:

```
"""Test builders for the axis package.

Builders follow the fluent pattern:
    result = SomeBuilder().with_x(value).with_y(value).build()

Each builder:
- Has sensible defaults (builds a valid object with no arguments)
- Returns self from all with_* methods
- Produces the target object from build()
"""
```

**File**: `tests/builders/config_builder.py`

A `FrameworkConfigBuilder` that will produce `FrameworkConfig` objects once they exist (WP-1.4). For now, this file contains a **stub builder** that produces a plain dict matching the anticipated framework config shape. This allows later WPs to fill in the real type without restructuring tests.

```python
class FrameworkConfigBuilder:
    """Fluent builder for framework config dicts.

    Produces a dict matching the framework config structure.
    Will be updated to produce FrameworkConfig once WP-1.4 defines the type.
    """

    def __init__(self) -> None:
        self._general = {"seed": 42}
        self._execution = {"max_steps": 200}
        self._world = {"grid_width": 10, "grid_height": 10, "obstacle_density": 0.0}
        self._logging = {"enabled": False}

    def with_seed(self, seed: int) -> FrameworkConfigBuilder: ...
    def with_max_steps(self, max_steps: int) -> FrameworkConfigBuilder: ...
    def with_world_size(self, width: int, height: int) -> FrameworkConfigBuilder: ...
    def with_obstacle_density(self, density: float) -> FrameworkConfigBuilder: ...
    def build(self) -> dict: ...
```

Each `with_*` method sets the relevant field and returns `self`. `build()` returns the assembled dict.

**File**: `tests/builders/system_config_builder.py`

A `SystemAConfigBuilder` that produces a dict matching System A's anticipated config structure:

```python
class SystemAConfigBuilder:
    """Fluent builder for System A config dicts.

    Produces a dict matching the anticipated SystemAConfig structure.
    Will be updated to produce SystemAConfig once WP-2.3 defines the type.
    """

    def __init__(self) -> None:
        self._agent = {
            "initial_energy": 50.0,
            "max_energy": 100.0,
            "memory_capacity": 5,
        }
        self._policy = {
            "selection_mode": "sample",
            "temperature": 1.0,
            "stay_suppression": 0.1,
            "consume_weight": 1.5,
        }
        self._transition = {
            "move_cost": 1.0,
            "consume_cost": 1.0,
            "stay_cost": 0.5,
            "max_consume": 1.0,
            "energy_gain_factor": 10.0,
        }

    def with_initial_energy(self, energy: float) -> SystemAConfigBuilder: ...
    def with_max_energy(self, energy: float) -> SystemAConfigBuilder: ...
    def with_temperature(self, temp: float) -> SystemAConfigBuilder: ...
    def build(self) -> dict: ...
```

The default values match the existing test fixtures in `tests/fixtures/scenario_fixtures.py` to preserve numerical continuity in future behavioral comparison tests.

---

### 2. Assertion Helpers

Create assertion helper modules under `tests/utils/`.

**File**: `tests/utils/__init__.py`

Docstring only:

```
"""Shared test assertion helpers for the axis package."""
```

**File**: `tests/utils/assertions.py`

Generic assertion helpers that do not depend on any `axis` domain types:

```python
def assert_frozen(instance: object, field_name: str, value: object) -> None:
    """Assert that setting a field on a frozen Pydantic model raises."""

def assert_valid_probability_distribution(probs: tuple[float, ...], *, tol: float = 1e-9) -> None:
    """Assert all values >= 0 and sum to 1.0."""

def assert_dict_has_keys(d: dict, *keys: str) -> None:
    """Assert a dict contains all specified keys."""

def assert_normalized_metric(value: float) -> None:
    """Assert a value is in [0.0, 1.0]."""
```

These are simple, reusable helpers. They import only `pytest`, not any `axis` types. Later WPs may add domain-specific assertion modules (e.g., `trace_assertions.py`, `world_assertions.py`) that import `axis` types.

**File**: `tests/utils/trace_assertions.py`

Placeholder with documented future purpose:

```python
"""Trace and replay contract assertion helpers.

This module will provide assertions for BaseStepTrace, BaseEpisodeTrace,
and system-specific trace data once the replay contract types are defined
in WP-1.3.

Current state: empty -- will be populated in WP-1.3 or WP-2.4.
"""
```

---

### 3. Fixture Infrastructure

**File**: `tests/conftest.py`

Populate the root conftest for the v02 test tree:

```python
"""Root conftest for v0.2.0 test suites.

Registers shared fixture modules for the new axis package tests.
"""

pytest_plugins = [
    "tests.v02.fixtures.config_fixtures",
]
```

**File**: `tests/fixtures/__init__.py`

Docstring only:

```
"""Shared pytest fixtures for the axis package test suites."""
```

**File**: `tests/fixtures/config_fixtures.py`

Provides reusable config fixtures using the builders:

```python
@pytest.fixture
def framework_config_dict() -> dict:
    """Default framework config as dict."""
    return FrameworkConfigBuilder().build()

@pytest.fixture
def system_a_config_dict() -> dict:
    """Default System A config as dict."""
    return SystemAConfigBuilder().build()

@pytest.fixture
def experiment_config_dict(framework_config_dict, system_a_config_dict) -> dict:
    """Complete experiment config as dict (framework + system sections)."""
    return {
        "system_type": "system_a",
        "experiment_type": "single_run",
        **framework_config_dict,
        "system": system_a_config_dict,
        "num_episodes_per_run": 3,
        "agent_start_position": {"x": 0, "y": 0},
        "parameter_path": None,
        "parameter_values": None,
    }
```

These fixtures produce **dicts** matching the anticipated config shape. Once WP-1.4 defines the real config types, these fixtures will be updated to produce typed instances. The dict shape serves as a contract test in the meantime.

---

### 4. Constants Module

**File**: `tests/constants.py`

Shared test constants that codify the default scenario parameters. These match the existing `_BASE_CONFIG_DICT` in `tests/fixtures/scenario_fixtures.py`:

```python
"""Shared test constants for the v0.2.0 test suites.

These values define the default test scenario and must remain consistent
with the existing v0.1.0 test fixtures for behavioral comparison.
"""

# Framework defaults
DEFAULT_SEED = 42
DEFAULT_MAX_STEPS = 200
DEFAULT_GRID_WIDTH = 10
DEFAULT_GRID_HEIGHT = 10
DEFAULT_OBSTACLE_DENSITY = 0.0

# System A defaults
DEFAULT_INITIAL_ENERGY = 50.0
DEFAULT_MAX_ENERGY = 100.0
DEFAULT_MEMORY_CAPACITY = 5
DEFAULT_TEMPERATURE = 1.0
DEFAULT_SELECTION_MODE = "sample"
DEFAULT_STAY_SUPPRESSION = 0.1
DEFAULT_CONSUME_WEIGHT = 1.5
DEFAULT_MOVE_COST = 1.0
DEFAULT_CONSUME_COST = 1.0
DEFAULT_STAY_COST = 0.5
DEFAULT_MAX_CONSUME = 1.0
DEFAULT_ENERGY_GAIN_FACTOR = 10.0
```

These constants are used by the builders and can be referenced directly in tests.

---

### 5. Verification Tests

**File**: `tests/test_infrastructure.py`

Tests that verify the test infrastructure itself works:

1. **Builder smoke tests**:
   - `FrameworkConfigBuilder().build()` produces a dict with keys: `general`, `execution`, `world`, `logging`
   - `SystemAConfigBuilder().build()` produces a dict with keys: `agent`, `policy`, `transition`
   - Builder chaining works: `FrameworkConfigBuilder().with_seed(99).with_max_steps(500).build()` applies overrides correctly
   - `SystemAConfigBuilder().with_initial_energy(75.0).build()` applies the override

2. **Fixture smoke tests**:
   - `framework_config_dict` fixture produces a valid dict
   - `system_a_config_dict` fixture produces a valid dict
   - `experiment_config_dict` fixture produces a complete dict with `system_type`, `experiment_type`, `system`
   - `experiment_config_dict["system_type"]` equals `"system_a"`

3. **Assertion helper tests**:
   - `assert_normalized_metric(0.5)` passes
   - `assert_normalized_metric(1.5)` fails
   - `assert_dict_has_keys({"a": 1, "b": 2}, "a", "b")` passes
   - `assert_dict_has_keys({"a": 1}, "a", "b")` fails

4. **Constants consistency test**:
   - `DEFAULT_INITIAL_ENERGY <= DEFAULT_MAX_ENERGY` (mirrors the existing validation rule)
   - `DEFAULT_GRID_WIDTH > 0`
   - `DEFAULT_MAX_STEPS > 0`
   - `DEFAULT_TEMPERATURE > 0`

---

### 6. Existing Tests Remain Untouched

No existing test file under `tests/` (outside of `tests/`) is modified. The existing `conftest.py` at `tests/conftest.py` is not changed. Both old and new test trees must run successfully under `pytest tests/`.

---

## Out of Scope

Do **not** implement any of the following in WP-0.2:

- Any `axis` domain types (interfaces, configs, models)
- Builders that produce typed `axis` objects (only dict-based stubs)
- World builder for the new `axis.world` types (will come in WP-2.1)
- Trace assertion helpers that reference `BaseStepTrace` (will come with WP-1.3)
- Visualization test utilities (will come with WP-4.4)
- Fixtures that import from `axis.sdk`, `axis.framework`, etc. (nothing exists there yet)
- Modifications to any file outside `tests/`
- Any changes to `src/axis/` or `src/axis_system_a/`

---

## Architectural Constraints

### 1. No Dependency on `axis` Domain Types

The builders and fixtures produce **dicts**, not typed objects. This is intentional: the `axis` package has no domain types yet. When later WPs define types, the builders will be upgraded in-place to produce typed instances. The dict shape acts as a forward contract.

### 2. Match Existing Conventions

The new test infrastructure should feel familiar to anyone who has worked with the existing `tests/builders/`, `tests/fixtures/`, and `tests/utils/` modules:

- Builders are fluent (return `self` from `with_*` methods, `build()` at the end)
- Fixtures are pytest-decorated functions in dedicated fixture modules
- Fixtures are registered via conftest `pytest_plugins` lists
- Assertion helpers are plain functions starting with `assert_`

### 3. Default Values Match v0.1.0

The default values in builders, fixtures, and constants must match the existing `_BASE_CONFIG_DICT` in `tests/fixtures/scenario_fixtures.py`. This ensures that when System A is refactored in Phase 2, behavioral comparison tests can use the same numerical setup.

One exception: `DEFAULT_MAX_STEPS` is set to `200` (not `1000`) as a pragmatic default for faster test execution. Individual tests can override to `1000` via the builder when needed.

### 4. Isolation of Test Trees

The `tests/` tree has its own `conftest.py` and does not inherit fixtures from the root `tests/conftest.py`. This prevents accidental dependencies on `axis_system_a`-specific fixtures in the new test suites.

If a test under `tests/` needs a fixture from the existing tree, it must be explicitly re-created or imported -- not silently inherited.

---

## Expected File Structure

After WP-0.2, these files are **new or modified**:

```
tests/conftest.py                           # MODIFIED (was empty, now has pytest_plugins)
tests/constants.py                          # NEW
tests/builders/__init__.py                  # NEW (docstring + convention docs)
tests/builders/config_builder.py            # NEW (FrameworkConfigBuilder)
tests/builders/system_config_builder.py     # NEW (SystemAConfigBuilder)
tests/fixtures/__init__.py                  # NEW (docstring only)
tests/fixtures/config_fixtures.py           # NEW (config fixtures)
tests/utils/__init__.py                     # NEW (docstring only)
tests/utils/assertions.py                   # NEW (generic assertion helpers)
tests/utils/trace_assertions.py             # NEW (placeholder)
tests/test_infrastructure.py                # NEW (verification tests)
```

Unchanged:

```
tests/conftest.py                               # UNCHANGED
tests/builders/, tests/fixtures/, tests/utils/  # UNCHANGED
tests/unit/, tests/integration/, etc.           # UNCHANGED
tests/test_scaffold.py                      # UNCHANGED (from WP-0.1)
tests/sdk/, tests/framework/, etc.      # UNCHANGED (empty from WP-0.1)
```

---

## Testing Requirements

### Infrastructure verification tests (`tests/test_infrastructure.py`)

Must include:

1. Builder dict output structure:
   - `FrameworkConfigBuilder().build()` has keys `general`, `execution`, `world`, `logging`
   - `SystemAConfigBuilder().build()` has keys `agent`, `policy`, `transition`
   - `FrameworkConfigBuilder().build()["general"]["seed"]` equals `DEFAULT_SEED`
   - `SystemAConfigBuilder().build()["agent"]["initial_energy"]` equals `DEFAULT_INITIAL_ENERGY`

2. Builder override behavior:
   - `FrameworkConfigBuilder().with_seed(99).build()["general"]["seed"]` equals `99`
   - `SystemAConfigBuilder().with_initial_energy(75.0).build()["agent"]["initial_energy"]` equals `75.0`

3. Fixture structure:
   - `experiment_config_dict` has keys `system_type`, `experiment_type`, `general`, `execution`, `world`, `logging`, `system`, `num_episodes_per_run`, `agent_start_position`
   - `experiment_config_dict["system_type"]` equals `"system_a"`
   - `experiment_config_dict["system"]` matches `system_a_config_dict`

4. Assertion helpers:
   - `assert_normalized_metric(0.0)` passes
   - `assert_normalized_metric(1.0)` passes
   - `assert_normalized_metric(-0.1)` fails (raises `AssertionError`)
   - `assert_normalized_metric(1.1)` fails
   - `assert_dict_has_keys({"a": 1, "b": 2}, "a", "b")` passes
   - `assert_dict_has_keys({"a": 1}, "b")` fails

5. Constants self-consistency:
   - `DEFAULT_INITIAL_ENERGY > 0`
   - `DEFAULT_INITIAL_ENERGY <= DEFAULT_MAX_ENERGY`
   - `DEFAULT_GRID_WIDTH > 0 and DEFAULT_GRID_HEIGHT > 0`
   - `DEFAULT_MAX_STEPS > 0`
   - `DEFAULT_TEMPERATURE > 0`

### Existing test suite

All 1215+ existing tests must still pass. The new files add to but do not interfere with the existing test tree.

---

## Implementation Style

- Python 3.11+
- Clear type hints
- Fluent builder pattern (return `self` from `with_*` methods)
- Concise docstrings on classes and non-obvious functions
- No dependencies on `axis` types (only stdlib, pytest, and dicts)
- No clever metaprogramming
- No unnecessary abstractions

---

## Expected Deliverable

1. Builder modules under `tests/builders/`
2. Assertion helper modules under `tests/utils/`
3. Fixture module under `tests/fixtures/`
4. Constants module at `tests/constants.py`
5. Updated `tests/conftest.py` with fixture registration
6. Verification tests at `tests/test_infrastructure.py`
7. Confirmation that all existing tests still pass

---

## Important Final Constraint

This is an **infrastructure-only** work package. It establishes patterns and utilities, not domain logic or domain tests.

The most important property is **consistency**: the builders, fixtures, and assertion helpers must follow the same conventions as the existing test infrastructure, and the default values must match the established test scenarios.

When later WPs define `axis` types, upgrading these builders from dict-producing to type-producing should be a **mechanical change**: replace `-> dict` with `-> FrameworkConfig`, replace dict construction with model construction, keep the same API.

If any design decision feels like it belongs in a later WP (e.g., world builders, trace assertions, visualization fixtures), it does. Defer it.
