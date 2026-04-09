# WP-0.1 Implementation Brief -- Package Scaffold

## Context

We are beginning the **modular architecture evolution** of the AXIS project: the transition from a monolithic `axis_system_a` package to a modular `axis` package with sub-packages for SDK, framework, world, systems, and visualization.

This work package is **WP-0.1**, the very first package in the evolution roadmap. It establishes the physical package structure that all subsequent work packages will populate.

### Predecessor State

The current repository contains:

```
src/axis_system_a/
    __init__.py
    cli.py, config.py, drives.py, enums.py, experiment.py,
    experiment_executor.py, logging.py, memory.py, observation.py,
    policy.py, repository.py, results.py, run.py, runner.py,
    snapshots.py, transition.py, types.py, world.py
    visualization/
        __init__.py
        (14 modules)
        ui/
            __init__.py
            (10 modules)

tests/
    conftest.py
    behavioral/, builders/, e2e/, fixtures/, integration/, unit/, utils/, visualization/
```

There is no `pyproject.toml` or `setup.py`. The package is installed directly via `PYTHONPATH` or `pip install -e .` with an implicit setup. Dependencies are in `requirements.txt`.

The existing test suite contains 1215+ tests. All must continue to pass after this WP.

### Architectural Decisions (Binding)

- **Q5**: Single package `axis` with sub-packages: `sdk`, `framework`, `world`, `systems`, `visualization`
- **Q18**: New test suites for new structure; old tests can be rewritten (but in this WP, old tests must still pass -- no old code is moved or changed)

### Reference Documents

- `docs/architecture/evolution/architectural-vision-v0.2.0.md` -- Section 3 (System Architecture)
- `docs/architecture/evolution/modular-architecture-roadmap.md` -- WP-0.1 definition
- `docs/architecture/evolution/modular-architecture-questions-answers.md` -- Q5

---

## Objective

Create the new `axis` package directory structure alongside the existing `axis_system_a` package. Establish `pyproject.toml` for the project. Ensure the new package is importable. Ensure the old package and all its tests remain fully functional.

This WP is **pure scaffolding**. No application code is written. No existing code is moved. No behavior changes.

---

## Scope

### 1. Create `pyproject.toml`

The project currently has no `pyproject.toml`. Create one that:

- Defines the project as `axis` (package name for the evolved system)
- Specifies Python `>=3.11`
- Lists current dependencies from `requirements.txt`:
  - `numpy>=1.26,<3.0`
  - `pydantic>=2.0,<3.0`
  - `PySide6>=6.6,<7`
  - `pyyaml>=6.0,<7.0`
  - `typing-extensions>=4.8,<5.0`
- Lists dev dependencies (or optional group):
  - `pytest>=8.0,<9.0`
  - `pytest-cov>=4.0,<5.0`
- Configures **both** `axis_system_a` and `axis` as discoverable packages (both must be importable during the transition period)
- Defines the CLI entry point `axis` pointing to the existing `axis_system_a.cli:main` (preserving current behavior)
- Configures pytest (tool.pytest.ini_options): `testpaths = ["tests"]`

**Important**: The `requirements.txt` file should be kept for now (some tooling may depend on it). It can be removed in a later WP.

#### Build system

Use `setuptools` with `pyproject.toml` as the single source of truth:

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"
```

Use `[tool.setuptools.packages.find]` to discover packages under `src/`.

---

### 2. Create the `axis` Package Directory Tree

Create the following directory structure under `src/`:

```
src/axis/
    __init__.py
    sdk/
        __init__.py
    framework/
        __init__.py
    world/
        __init__.py
    systems/
        __init__.py
        system_a/
            __init__.py
    visualization/
        __init__.py
```

Each `__init__.py` file must contain:

- A module docstring describing the sub-package's purpose (one line is sufficient)
- No imports, no code

The docstrings should match the architectural vision:

| Sub-package | Docstring |
|-------------|-----------|
| `axis` | `"""AXIS Modular Framework."""` |
| `axis.sdk` | `"""System SDK -- interfaces, contracts, and base types."""` |
| `axis.framework` | `"""Experimentation Framework -- execution, persistence, config, CLI."""` |
| `axis.world` | `"""World Framework -- world model, factory, action engine, dynamics."""` |
| `axis.systems` | `"""System implementations."""` |
| `axis.systems.system_a` | `"""System A -- hunger-driven baseline agent."""` |
| `axis.visualization` | `"""Visualization -- replay viewer and system adapter framework."""` |

---

### 3. Create the New Test Directory Tree

Create the following test directory structure:

```
tests/
    __init__.py
    conftest.py
    sdk/
        __init__.py
    framework/
        __init__.py
    world/
        __init__.py
    systems/
        __init__.py
        system_a/
            __init__.py
    visualization/
        __init__.py
```

The name `v02` is chosen to keep the new test tree clearly separate from the existing test directories (`unit/`, `integration/`, `behavioral/`, `visualization/`, `e2e/`) during the transition. This avoids any naming conflicts or conftest interference.

`tests/__init__.py` files should be empty (standard pytest discovery).

`tests/conftest.py` should be empty initially -- it will gain shared fixtures in WP-0.2.

---

### 4. Verification Test

Create a single, minimal test file that verifies the scaffold is correct:

**File**: `tests/test_scaffold.py`

This test file must verify:

1. The `axis` package is importable
2. All sub-packages are importable:
   - `axis.sdk`
   - `axis.framework`
   - `axis.world`
   - `axis.systems`
   - `axis.systems.system_a`
   - `axis.visualization`
3. The existing `axis_system_a` package is still importable
4. Key existing imports still work: `from axis_system_a import SimulationConfig, World, Action`

This is a structural smoke test, not a behavioral test.

---

### 5. Verify Existing Tests Still Pass

After creating the scaffold, the full existing test suite (`pytest tests/`) must pass without modification. The scaffold adds files but changes no existing code.

---

## Out of Scope

Do **not** implement any of the following in WP-0.1:

- SDK interfaces or types
- Framework config types
- World model code
- System A refactored code
- Visualization adapter types
- System registry
- Any behavior, logic, or domain types in the new `axis` package
- Moving any existing code from `axis_system_a` to `axis`
- Modifying any existing source files in `axis_system_a`
- Modifying any existing test files
- Removing `requirements.txt`
- Defining CLI entry points for the new package (the `axis` CLI continues to point to existing code)

---

## Architectural Constraints

### 1. Coexistence

Both `axis_system_a` and `axis` must be importable simultaneously. The `pyproject.toml` must configure package discovery to find both under `src/`.

### 2. No Existing Code Changes

Zero modifications to any file under `src/axis_system_a/` or `tests/` (except adding the new `tests/` subdirectory).

### 3. No Namespace Collisions

The new `axis` package must not conflict with `axis_system_a` in any way. They are independent packages under the same `src/` root.

### 4. Minimal Content

The new `__init__.py` files must contain only a docstring. No imports, no `__all__`, no version constants. These will be populated by later WPs.

---

## Expected File Structure

After WP-0.1, the repository should contain these **new** files:

```
pyproject.toml                              # NEW

src/axis/__init__.py                        # NEW (docstring only)
src/axis/sdk/__init__.py                    # NEW (docstring only)
src/axis/framework/__init__.py              # NEW (docstring only)
src/axis/world/__init__.py                  # NEW (docstring only)
src/axis/systems/__init__.py                # NEW (docstring only)
src/axis/systems/system_a/__init__.py       # NEW (docstring only)
src/axis/visualization/__init__.py          # NEW (docstring only)

tests/__init__.py                       # NEW (empty)
tests/conftest.py                       # NEW (empty)
tests/sdk/__init__.py                   # NEW (empty)
tests/framework/__init__.py             # NEW (empty)
tests/world/__init__.py                 # NEW (empty)
tests/systems/__init__.py               # NEW (empty)
tests/systems/system_a/__init__.py      # NEW (empty)
tests/visualization/__init__.py         # NEW (empty)
tests/test_scaffold.py                  # NEW (verification test)
```

These files are listed top to bottom. For any file that already exists or would be modified, this note marks them:

```
requirements.txt                            # UNCHANGED (kept as-is)
src/axis_system_a/                          # UNCHANGED (no modifications)
tests/conftest.py                           # UNCHANGED
tests/unit/, tests/integration/, etc.       # UNCHANGED
```

---

## Testing Requirements

### Scaffold verification test (`tests/test_scaffold.py`)

The following assertions must be present:

1. **Package importability**: `import axis` succeeds
2. **Sub-package importability**: Each of the 6 sub-packages imports successfully
3. **Legacy package importability**: `import axis_system_a` succeeds
4. **Legacy import smoke test**: `from axis_system_a import SimulationConfig, World, Action` succeeds
5. **New packages are empty**: `dir(axis.sdk)` contains no public symbols beyond the module docstring (no unexpected exports)

### Existing test suite

Run `pytest tests/ -x` and confirm all 1215+ existing tests pass. This is a manual verification step, not a new test.

---

## Implementation Style

- Python 3.11+
- Minimal files, minimal content
- docstrings where specified, nothing else
- Standard `pyproject.toml` conventions
- No clever metaprogramming, no dynamic imports, no conditional logic

---

## Expected Deliverable

1. `pyproject.toml` with correct project metadata, dependencies, package discovery, and CLI entry point
2. The `src/axis/` directory tree with docstring-only `__init__.py` files
3. The `tests/` directory tree with empty `__init__.py` files
4. `tests/test_scaffold.py` with the verification test
5. Confirmation that all existing tests still pass

---

## Important Final Constraint

This is the **simplest possible work package** in the entire roadmap. Its only purpose is to lay down the directory structure and build configuration for the modular architecture.

It must be:

- Trivially correct
- Trivially reversible (just delete new files and revert `pyproject.toml`)
- Zero-risk to existing functionality

If any design decision feels like it belongs in a later WP, it does. Defer it. The scaffold is just empty directories, empty files, and a `pyproject.toml`.
