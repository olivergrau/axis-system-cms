"""Scaffold verification tests for WP-0.1.

Verifies that the axis package structure is correctly set up
and that the existing axis_system_a package remains functional.
"""

from __future__ import annotations

import importlib


def test_axis_package_importable() -> None:
    """The axis package is importable."""
    import axis  # noqa: F401


def test_axis_sdk_importable() -> None:
    """axis.sdk sub-package is importable."""
    import axis.sdk  # noqa: F401


def test_axis_framework_importable() -> None:
    """axis.framework sub-package is importable."""
    import axis.framework  # noqa: F401


def test_axis_world_importable() -> None:
    """axis.world sub-package is importable."""
    import axis.world  # noqa: F401


def test_axis_systems_importable() -> None:
    """axis.systems sub-package is importable."""
    import axis.systems  # noqa: F401


def test_axis_systems_system_a_importable() -> None:
    """axis.systems.system_a sub-package is importable."""
    import axis.systems.system_a  # noqa: F401


def test_axis_visualization_importable() -> None:
    """axis.visualization sub-package is importable."""
    import axis.visualization  # noqa: F401


def test_legacy_package_importable() -> None:
    """The existing axis_system_a package is still importable."""
    import axis_system_a  # noqa: F401


def test_legacy_imports_still_work() -> None:
    """Key existing imports from axis_system_a still work."""
    from axis_system_a import SimulationConfig, World, Action  # noqa: F401


def test_unpopulated_packages_are_empty() -> None:
    """Axis sub-packages not yet populated export no public symbols."""
    import types

    module_names = [
        "axis.world",
        "axis.systems",
        "axis.systems.system_a",
        "axis.visualization",
    ]
    for name in module_names:
        mod = importlib.import_module(name)
        public = [
            attr
            for attr in dir(mod)
            if not attr.startswith("_")
            and not isinstance(getattr(mod, attr), types.ModuleType)
        ]
        assert public == [], f"{name} has unexpected public symbols: {public}"


def test_framework_exports_config_types() -> None:
    """axis.framework exports the config types and helpers."""
    import axis.framework

    expected = {
        # WP-1.4: Framework config types
        "ExperimentConfig",
        "ExperimentType",
        "ExecutionConfig",
        "FrameworkConfig",
        "GeneralConfig",
        "LoggingConfig",
        "extract_framework_config",
        "get_config_value",
        "parse_parameter_path",
        "set_config_value",
    }
    actual = set(axis.framework.__all__)
    assert expected == actual


def test_sdk_exports_interfaces_and_types() -> None:
    """axis.sdk exports the interfaces, data types, and world contracts."""
    import axis.sdk

    expected = {
        # WP-1.1: Interfaces and types
        "SystemInterface",
        "SensorInterface",
        "DriveInterface",
        "PolicyInterface",
        "TransitionInterface",
        "DecideResult",
        "TransitionResult",
        "PolicyResult",
        # WP-1.2: World contracts
        "Position",
        "CellView",
        "WorldView",
        "ActionOutcome",
        "BaseWorldConfig",
        "BASE_ACTIONS",
        "UP",
        "DOWN",
        "LEFT",
        "RIGHT",
        "STAY",
        "MOVEMENT_DELTAS",
        # WP-1.3: Replay contract
        "WorldSnapshot",
        "snapshot_world",
        "BaseStepTrace",
        "BaseEpisodeTrace",
    }
    actual = set(axis.sdk.__all__)
    assert expected == actual
