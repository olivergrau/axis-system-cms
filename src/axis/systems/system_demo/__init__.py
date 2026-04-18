"""System Demo -- minimal system for workflow testing."""

from axis.systems.system_demo.system import DemoConfig, SystemDemo

__all__ = ["SystemDemo", "DemoConfig"]


def register() -> None:
    """Register system_demo with the framework."""
    from axis.framework.registry import register_system, registered_system_types

    if "system_demo" not in registered_system_types():

        def _factory(cfg: dict) -> SystemDemo:
            return SystemDemo(DemoConfig(**cfg))

        register_system("system_demo", _factory)
