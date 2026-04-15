"""System A -- hunger-driven baseline agent."""

from axis.systems.construction_kit.types.actions import handle_consume
from axis.systems.system_a.config import SystemAConfig
from axis.systems.system_a.system import SystemA

__all__ = [
    "SystemA",
    "SystemAConfig",
    "handle_consume",
]


def register() -> None:
    """Register system_a: system factory + visualization adapter."""
    from axis.framework.registry import register_system, registered_system_types

    if "system_a" not in registered_system_types():

        def _factory(cfg: dict) -> SystemA:
            return SystemA(SystemAConfig(**cfg))

        register_system("system_a", _factory)

    from axis.visualization.registry import registered_system_visualizations

    if "system_a" not in registered_system_visualizations():
        try:
            import axis.systems.system_a.visualization  # noqa: F401
        except ImportError:
            pass
