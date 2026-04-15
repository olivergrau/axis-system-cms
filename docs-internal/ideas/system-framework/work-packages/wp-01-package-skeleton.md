# WP-01: Package Skeleton

**Phase**: 1 -- Foundation
**Dependencies**: None
**Scope**: Small
**Spec reference**: Section 4.1, Section 7.8

---

## Objective

Create the `construction_kit/` package directory structure with empty `__init__.py` files for all component families. This establishes the target locations for all subsequent extraction WPs.

---

## Deliverables

Create the following directory tree under `src/axis/systems/`:

```text
construction_kit/
    __init__.py
    observation/
        __init__.py
    drives/
        __init__.py
    policy/
        __init__.py
    arbitration/
        __init__.py
    energy/
        __init__.py
    memory/
        __init__.py
    prediction/
        __init__.py
    traces/
        __init__.py
    modulation/
        __init__.py
    types/
        __init__.py
```

Also create the test directory:

```text
tests/systems/construction_kit/
    __init__.py
```

---

## Implementation Steps

1. Create all directories and `__init__.py` files listed above.
2. Each `__init__.py` should contain only a module docstring describing the component family's purpose (one line).
3. The top-level `construction_kit/__init__.py` docstring: `"""System Construction Kit -- reusable building blocks for composing agent architectures."""`
4. The `prediction/`, `traces/`, and `modulation/` packages are created empty (prepared for Phase 2).

---

## `__init__.py` Docstrings

| Package | Docstring |
|---------|-----------|
| `construction_kit/` | `"""System Construction Kit -- reusable building blocks for composing agent architectures."""` |
| `observation/` | `"""Observation types and sensor implementations."""` |
| `drives/` | `"""Drive primitives and drive output types."""` |
| `policy/` | `"""Action selection policies."""` |
| `arbitration/` | `"""Multi-drive score combination and weight computation."""` |
| `energy/` | `"""Energy management utilities."""` |
| `memory/` | `"""Bounded memory structures and update functions."""` |
| `prediction/` | `"""Predictive memory and prediction error processing (Phase 2)."""` |
| `traces/` | `"""Trace dynamics and bounded accumulation (Phase 2)."""` |
| `modulation/` | `"""Action score modulation functions (Phase 2)."""` |
| `types/` | `"""Shared type definitions and constants."""` |

---

## Verification

1. `python -c "import axis.systems.construction_kit"` -- succeeds
2. `python -c "import axis.systems.construction_kit.observation"` -- succeeds
3. `python -c "import axis.systems.construction_kit.prediction"` -- succeeds
4. `python -m pytest tests/ -x` -- all existing tests still pass (no changes to existing code)

---

## Files Created

- `src/axis/systems/construction_kit/__init__.py`
- `src/axis/systems/construction_kit/observation/__init__.py`
- `src/axis/systems/construction_kit/drives/__init__.py`
- `src/axis/systems/construction_kit/policy/__init__.py`
- `src/axis/systems/construction_kit/arbitration/__init__.py`
- `src/axis/systems/construction_kit/energy/__init__.py`
- `src/axis/systems/construction_kit/memory/__init__.py`
- `src/axis/systems/construction_kit/prediction/__init__.py`
- `src/axis/systems/construction_kit/traces/__init__.py`
- `src/axis/systems/construction_kit/modulation/__init__.py`
- `src/axis/systems/construction_kit/types/__init__.py`
- `tests/systems/construction_kit/__init__.py`

## Files Modified

None.

## Files Deleted

None.
