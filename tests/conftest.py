"""Root conftest -- shared fixtures for all test suites."""

from axis.plugins import discover_plugins

discover_plugins()

from tests.fixtures.config_fixtures import (  # noqa: E402, F401
    experiment_config,
    experiment_config_dict,
    framework_config,
    framework_config_dict,
    system_a_config_dict,
)
