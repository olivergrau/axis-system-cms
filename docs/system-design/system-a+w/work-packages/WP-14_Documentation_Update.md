# WP-14: Documentation Update

## Metadata
- Work Package: WP-14
- Title: Documentation and Scaffold Update
- System: System A+W
- Source Files: `README.md`, `tests/test_scaffold.py`, `src/axis/systems/system_aw/__init__.py`
- Dependencies: WP-10 (system implemented), WP-13 (configs created)

---

## 1. Objective

Update project-level documentation and test scaffolding to reflect the existence of System A+W as a fully operational system type. After this WP, System A+W is discoverable, documented, and verified by the CI scaffold tests.

---

## 2. Changes

### 2.1 README.md

Add System A+W to the existing documentation. Changes are **additive** — no existing content is removed.

#### Systems Section

Add a System A+W entry alongside the existing System A and System B descriptions:

```markdown
### System A+W — Dual-Drive Agent with Curiosity and World Model

System A+W extends System A with a second drive (curiosity) and a spatial world model.
The agent balances hunger-driven resource-seeking with curiosity-driven exploration,
modulated by a dynamic weight function that implements a Maslow-like hierarchy:
hunger gates curiosity.

Key additions over System A:
- **Curiosity drive** with composite novelty (spatial + sensory)
- **Spatial world model** (visit-count map via dead reckoning)
- **Dynamic drive arbitration** (hunger suppresses curiosity as energy decreases)

When curiosity parameters are zeroed, System A+W reduces exactly to System A.

Design documents: `docs/system-design/system-a+w/`
```

#### CLI Examples Section

Add System A+W config examples:

```markdown
# Run System A+W baseline (dual-drive with curiosity)
axis run experiments/configs/system-aw-baseline.yaml

# Sweep over curiosity strength (μ_C = 0.0 to 1.0)
axis run experiments/configs/system-aw-curiosity-sweep.yaml

# Exploration demo (large grid, high curiosity)
axis run experiments/configs/system-aw-exploration-demo.yaml
```

#### Configuration Section

Add a System A+W configuration reference showing the new `curiosity` and `arbitration` sub-sections. Note that they are optional with defaults.

### 2.2 tests/test_scaffold.py

Add scaffold tests for System A+W:

```python
def test_axis_systems_system_aw_importable() -> None:
    """axis.systems.system_aw sub-package is importable."""
    import axis.systems.system_aw  # noqa: F401


def test_system_aw_exports() -> None:
    """axis.systems.system_aw exports SystemAW, SystemAWConfig."""
    import axis.systems.system_aw

    expected = {
        "SystemAW",
        "SystemAWConfig",
    }
    actual = set(axis.systems.system_aw.__all__)
    assert expected == actual
```

Also verify that `"system_aw"` is registered:

```python
def test_system_aw_registered() -> None:
    """system_aw is registered in the system registry."""
    from axis.framework import registered_system_types

    assert "system_aw" in registered_system_types()
```

### 2.3 Package __init__.py Verification

Ensure `src/axis/systems/system_aw/__init__.py` exports exactly:

```python
__all__ = [
    "SystemAW",
    "SystemAWConfig",
]
```

This was defined in WP-10; WP-14 verifies it via the scaffold test.

---

## 3. Verification Checklist

The following must all pass after this WP:

| # | Check | How |
|---|---|---|
| 1 | README mentions System A+W | Manual review + grep |
| 2 | README has CLI examples for all 3 configs | Manual review |
| 3 | `import axis.systems.system_aw` succeeds | `test_axis_systems_system_aw_importable` |
| 4 | Package exports correct | `test_system_aw_exports` |
| 5 | System registered | `test_system_aw_registered` |
| 6 | Baseline config runs end-to-end | `axis run experiments/configs/system-aw-baseline.yaml` |
| 7 | Existing tests still pass | Full `pytest` run |

---

## 4. Test Plan

### File: `tests/test_scaffold.py` (additions)

| # | Test | Description |
|---|---|---|
| 1 | `test_axis_systems_system_aw_importable` | `import axis.systems.system_aw` succeeds |
| 2 | `test_system_aw_exports` | `__all__` contains exactly `{"SystemAW", "SystemAWConfig"}` |
| 3 | `test_system_aw_registered` | `"system_aw"` in `registered_system_types()` |

---

## 5. Non-Goals

- **No new README file** — changes are additions to the existing README
- **No CHANGELOG** — the release notes will cover this (separate from implementation)
- **No API documentation** — docstrings in source code are sufficient
- **No migration guide** — System A+W is a new system type, not a replacement

---

## 6. Acceptance Criteria

- [ ] README documents System A+W in the Systems section
- [ ] README has CLI examples for all 3 experiment configs
- [ ] README documents the new `curiosity` and `arbitration` config sections
- [ ] Scaffold test verifies `axis.systems.system_aw` is importable
- [ ] Scaffold test verifies package exports (`SystemAW`, `SystemAWConfig`)
- [ ] Scaffold test verifies system registry contains `"system_aw"`
- [ ] `axis run experiments/configs/system-aw-baseline.yaml` completes successfully
- [ ] All existing tests continue to pass (no regressions)
- [ ] All 3 new scaffold tests pass
