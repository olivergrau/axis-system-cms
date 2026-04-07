"""Root conftest for v0.2.0 test suites.

Registers shared fixtures for the new axis package tests.
"""

from tests.v02.fixtures.config_fixtures import (  # noqa: F401
    experiment_config,
    experiment_config_dict,
    framework_config,
    framework_config_dict,
    system_a_config_dict,
)
