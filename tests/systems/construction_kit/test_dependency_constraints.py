"""Dependency constraint tests for the System Construction Kit.

These tests enforce the architectural boundaries defined in the
System Construction Kit spec (Sections 5, 9.6) and prevent regressions
where forbidden imports creep back in.
"""

from __future__ import annotations

import re
from pathlib import Path


def find_imports_matching(package_path: str, pattern: str) -> list[str]:
    """Scan Python files for import lines matching a regex pattern.

    Returns list of "file:line_number: import_line" strings.
    """
    violations: list[str] = []
    root = Path(package_path)
    for py_file in sorted(root.rglob("*.py")):
        for i, line in enumerate(py_file.read_text().splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(pattern, stripped):
                violations.append(f"{py_file}:{i}: {stripped}")
    return violations


class TestConstructionKitBoundaries:
    """Construction kit must not reach into framework, world, or concrete systems."""

    def test_no_framework_imports(self) -> None:
        """Construction kit must not depend on axis.framework."""
        violations = find_imports_matching(
            package_path="src/axis/systems/construction_kit",
            pattern=r"(from|import)\s+axis\.framework",
        )
        assert violations == [], f"Forbidden framework imports: {violations}"

    def test_no_world_imports(self) -> None:
        """Construction kit must not depend on axis.world."""
        violations = find_imports_matching(
            package_path="src/axis/systems/construction_kit",
            pattern=r"(from|import)\s+axis\.world\b",
        )
        assert violations == [], f"Forbidden world imports: {violations}"

    def test_no_concrete_system_imports(self) -> None:
        """Construction kit must not depend on any concrete system."""
        violations = find_imports_matching(
            package_path="src/axis/systems/construction_kit",
            pattern=r"(from|import)\s+axis\.systems\.system_",
        )
        assert violations == [], f"Forbidden system imports: {violations}"


class TestCrossSystemBoundaries:
    """No concrete system may import from another concrete system."""

    def test_no_cross_system_imports(self) -> None:
        """All shared code should come from the construction kit."""
        violations: list[str] = []
        for system_name in ("system_a", "system_aw", "system_b", "system_c"):
            other_systems = [
                s for s in ("system_a", "system_aw", "system_b", "system_c")
                if s != system_name
            ]
            for other in other_systems:
                hits = find_imports_matching(
                    package_path=f"src/axis/systems/{system_name}",
                    pattern=rf"(from|import)\s+axis\.systems\.{other}\b",
                )
                violations.extend(hits)
        assert violations == [], f"Cross-system imports found: {violations}"


class TestNoCircularDependencies:
    """Construction kit packages must not have circular dependencies."""

    def test_no_circular_construction_kit_imports(self) -> None:
        """Import each package and verify no ImportError from circular references."""
        import axis.systems.construction_kit.observation
        import axis.systems.construction_kit.drives
        import axis.systems.construction_kit.policy
        import axis.systems.construction_kit.arbitration
        import axis.systems.construction_kit.energy
        import axis.systems.construction_kit.memory
        import axis.systems.construction_kit.types
        import axis.systems.construction_kit.prediction
        import axis.systems.construction_kit.traces
        import axis.systems.construction_kit.modulation


class TestUpstreamBoundaries:
    """Framework and SDK must not depend on the construction kit."""

    def test_framework_does_not_import_construction_kit(self) -> None:
        """Framework must not depend on the construction kit."""
        violations = find_imports_matching(
            package_path="src/axis/framework",
            pattern=r"(from|import)\s+axis\.systems\.construction_kit",
        )
        assert violations == [
        ], f"Framework imports construction kit: {violations}"

    def test_sdk_does_not_import_construction_kit(self) -> None:
        """SDK must not depend on the construction kit."""
        violations = find_imports_matching(
            package_path="src/axis/sdk",
            pattern=r"(from|import)\s+axis\.systems\.construction_kit",
        )
        assert violations == [], f"SDK imports construction kit: {violations}"
