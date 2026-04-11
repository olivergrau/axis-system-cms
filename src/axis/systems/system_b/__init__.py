"""System B -- scout agent with scan action."""

from axis.systems.system_b.config import SystemBConfig
from axis.systems.system_b.system import SystemB

__all__ = [
    "SystemB",
    "SystemBConfig",
]


def register() -> None:
    """Register system_b: system factory + visualization adapter."""
    from axis.framework.registry import register_system, registered_system_types

    if "system_b" not in registered_system_types():

        def _factory(cfg: dict) -> SystemB:
            return SystemB(SystemBConfig(**cfg))

        register_system("system_b", _factory)

    from axis.visualization.registry import registered_system_visualizations

    if "system_b" not in registered_system_visualizations():
        try:
            import axis.systems.system_b.visualization  # noqa: F401
        except ImportError:
            pass
