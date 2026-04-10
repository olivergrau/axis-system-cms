"""Scaffold verification tests for WP-0.1.

Verifies that the axis package structure is correctly set up.
"""

from __future__ import annotations


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


def test_axis_visualization_importable() -> None:
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
        # WP-3.1: System registry
        "SystemFactory",
        "create_system",
        "get_system_factory",
        "register_system",
        "registered_system_types",
        # WP-3.2: Episode runner
        "run_episode",
        "setup_episode",
        # WP-3.3: Run executor
        "RunConfig",
        "RunExecutor",
        "RunResult",
        "RunSummary",
        "compute_run_summary",
        "resolve_episode_seeds",
        # WP-3.3: Experiment executor
        "ExperimentExecutor",
        "ExperimentResult",
        "ExperimentSummary",
        "RunSummaryEntry",
        "compute_experiment_summary",
        "resolve_run_configs",
        "variation_description",
        "execute_experiment",
        "resume_experiment",
        "is_run_complete",
        # WP-3.4: Persistence
        "ExperimentRepository",
        "ExperimentStatus",
        "ExperimentStatusRecord",
        "ExperimentMetadata",
        "RunStatus",
        "RunStatusRecord",
        "RunMetadata",
        # Logging runtime
        "EpisodeLogger",
    }
    actual = set(axis.framework.__all__)
    assert expected == actual


def test_world_exports_model_and_factory() -> None:
    """axis.world exports the world model types and factory."""
    import axis.world

    expected = {
        # WP-2.1: World extraction
        "CellType",
        "RegenerationMode",
        "Cell",
        "World",
        "create_world",
        # WP-2.2: Action engine and dynamics
        "ActionRegistry",
        "create_action_registry",
        # World registry
        "register_world",
        "get_world_factory",
        "registered_world_types",
        "create_world_from_config",
    }
    actual = set(axis.world.__all__)
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
        "MutableWorldProtocol",
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


def test_system_a_exports() -> None:
    """axis.systems.system_a exports SystemA, SystemAConfig, handle_consume."""
    import axis.systems.system_a

    expected = {
        "SystemA",
        "SystemAConfig",
        "handle_consume",
    }
    actual = set(axis.systems.system_a.__all__)
    assert expected == actual
