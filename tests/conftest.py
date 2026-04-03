"""Root conftest — registers shared fixture modules."""

pytest_plugins = [
    "tests.fixtures.world_fixtures",
    "tests.fixtures.agent_fixtures",
    "tests.fixtures.observation_fixtures",
    "tests.fixtures.scenario_fixtures",
]
