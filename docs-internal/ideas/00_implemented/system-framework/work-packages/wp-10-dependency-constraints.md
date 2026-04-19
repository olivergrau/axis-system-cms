# WP-10: Dependency Constraint Tests

**Phase**: 1 -- Foundation
**Dependencies**: WP-01 through WP-09
**Scope**: Small
**Spec reference**: Sections 5, 9.6

---

## Objective

Create automated tests that verify the construction kit's dependency constraints. These tests enforce the architectural boundaries and prevent regressions where forbidden imports creep back in.

---

## Tests to Implement

### `tests/systems/construction_kit/test_dependency_constraints.py`

#### 1. Construction kit must not import from framework

Scan all Python files under `src/axis/systems/construction_kit/` and verify none contain `from axis.framework` or `import axis.framework`.

```python
def test_no_framework_imports():
    """Construction kit must not depend on axis.framework."""
    violations = find_imports_matching(
        package_path="src/axis/systems/construction_kit",
        pattern=r"(from|import)\s+axis\.framework",
    )
    assert violations == [], f"Forbidden framework imports: {violations}"
```

#### 2. Construction kit must not import from world

Scan all Python files under `src/axis/systems/construction_kit/` and verify none contain `from axis.world` or `import axis.world`.

Exception: imports from `axis.sdk.world_types` are allowed (these are protocol definitions, not world implementations).

```python
def test_no_world_imports():
    """Construction kit must not depend on axis.world."""
    violations = find_imports_matching(
        package_path="src/axis/systems/construction_kit",
        pattern=r"(from|import)\s+axis\.world\b",
    )
    assert violations == [], f"Forbidden world imports: {violations}"
```

#### 3. Construction kit must not import from concrete systems

Scan all Python files under `src/axis/systems/construction_kit/` and verify none contain imports from `axis.systems.system_a`, `axis.systems.system_aw`, or `axis.systems.system_b`.

```python
def test_no_concrete_system_imports():
    """Construction kit must not depend on any concrete system."""
    violations = find_imports_matching(
        package_path="src/axis/systems/construction_kit",
        pattern=r"(from|import)\s+axis\.systems\.system_",
    )
    assert violations == [], f"Forbidden system imports: {violations}"
```

#### 4. No cross-system imports between concrete systems

Verify that no concrete system imports from another concrete system. All shared code should come from the construction kit.

```python
def test_no_cross_system_imports():
    """No concrete system may import from another concrete system."""
    violations = []
    for system_name in ("system_a", "system_aw", "system_b"):
        other_systems = [s for s in ("system_a", "system_aw", "system_b") if s != system_name]
        for other in other_systems:
            hits = find_imports_matching(
                package_path=f"src/axis/systems/{system_name}",
                pattern=rf"(from|import)\s+axis\.systems\.{other}\b",
            )
            violations.extend(hits)
    assert violations == [], f"Cross-system imports found: {violations}"
```

#### 5. No circular dependencies within construction kit

Verify that internal construction kit imports follow the allowed dependency graph (Section 5.1 of the spec). No circular imports.

```python
def test_no_circular_construction_kit_imports():
    """Construction kit packages must not have circular dependencies."""
    # Import each package and verify no ImportError from circular references
    import axis.systems.construction_kit.observation
    import axis.systems.construction_kit.drives
    import axis.systems.construction_kit.policy
    import axis.systems.construction_kit.arbitration
    import axis.systems.construction_kit.energy
    import axis.systems.construction_kit.memory
    import axis.systems.construction_kit.types
```

#### 6. Framework and SDK remain untouched

Verify that no files in `src/axis/framework/` or `src/axis/sdk/` import from the construction kit. The construction kit is a system-side concern.

```python
def test_framework_does_not_import_construction_kit():
    """Framework must not depend on the construction kit."""
    violations = find_imports_matching(
        package_path="src/axis/framework",
        pattern=r"(from|import)\s+axis\.systems\.construction_kit",
    )
    assert violations == [], f"Framework imports construction kit: {violations}"

def test_sdk_does_not_import_construction_kit():
    """SDK must not depend on the construction kit."""
    violations = find_imports_matching(
        package_path="src/axis/sdk",
        pattern=r"(from|import)\s+axis\.systems\.construction_kit",
    )
    assert violations == [], f"SDK imports construction kit: {violations}"
```

---

## Helper Function

The test file includes a shared helper:

```python
import re
from pathlib import Path


def find_imports_matching(package_path: str, pattern: str) -> list[str]:
    """Scan Python files for import lines matching a regex pattern.

    Returns list of "file:line_number: import_line" strings.
    """
    violations = []
    root = Path(package_path)
    for py_file in root.rglob("*.py"):
        for i, line in enumerate(py_file.read_text().splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(pattern, stripped):
                violations.append(f"{py_file}:{i}: {stripped}")
    return violations
```

---

## Verification

1. `python -m pytest tests/systems/construction_kit/test_dependency_constraints.py -v` -- all constraint tests pass
2. `python -m pytest tests/ -x` -- full suite still passes

---

## Files Created
- `tests/systems/construction_kit/test_dependency_constraints.py`

## Files Deleted
None.

## Files Modified
None (this WP only adds tests, no source changes).
