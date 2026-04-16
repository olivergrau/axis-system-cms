"""System C -- predictive action modulation agent."""

from axis.systems.construction_kit.types.actions import handle_consume
from axis.systems.system_c.config import PredictionConfig, SystemCConfig
from axis.systems.system_c.system import SystemC

__all__ = [
    "PredictionConfig",
    "SystemC",
    "SystemCConfig",
    "handle_consume",
]


def register() -> None:
    """Register system_c: system factory + visualization adapter."""
    from axis.framework.registry import register_system, registered_system_types

    if "system_c" not in registered_system_types():

        def _factory(cfg: dict) -> SystemC:
            return SystemC(SystemCConfig(**cfg))

        register_system("system_c", _factory)

    from axis.visualization.registry import registered_system_visualizations

    if "system_c" not in registered_system_visualizations():
        try:
            import axis.systems.system_c.visualization  # noqa: F401
        except ImportError:
            pass
