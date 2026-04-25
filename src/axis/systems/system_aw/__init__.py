"""System A+W -- dual-drive agent with curiosity and world model."""

from axis.systems.system_aw.config import SystemAWConfig
from axis.systems.system_aw.system import SystemAW

__all__ = [
    "SystemAW",
    "SystemAWConfig",
]


def register() -> None:
    """Register system_aw: system factory + visualization adapter."""
    from axis.framework.registry import register_system, registered_system_types

    if "system_aw" not in registered_system_types():

        def _factory(cfg: dict) -> SystemAW:
            return SystemAW(SystemAWConfig(**cfg))

        register_system("system_aw", _factory)

    from axis.framework.metrics.extensions import registered_metric_extensions

    if "system_aw" not in registered_metric_extensions():
        try:
            import axis.systems.system_aw.metrics  # noqa: F401
        except ImportError:
            pass

    from axis.visualization.registry import registered_system_visualizations

    if "system_aw" not in registered_system_visualizations():
        try:
            import axis.systems.system_aw.visualization  # noqa: F401
        except ImportError:
            pass
