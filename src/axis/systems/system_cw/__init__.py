"""System C+W -- predictive dual-drive agent."""

from axis.systems.construction_kit.types.actions import handle_consume
from axis.systems.system_cw.config import (
    DrivePredictionConfig,
    PredictionOutcomeConfig,
    PredictionSharedConfig,
    SystemCWConfig,
    SystemCWPredictionConfig,
)
from axis.systems.system_cw.system import SystemCW

__all__ = [
    "DrivePredictionConfig",
    "PredictionOutcomeConfig",
    "PredictionSharedConfig",
    "SystemCW",
    "SystemCWConfig",
    "SystemCWPredictionConfig",
    "handle_consume",
]


def register() -> None:
    """Register system_cw: system factory + visualization + metrics + comparison."""
    from axis.framework.registry import register_system, registered_system_types

    if "system_cw" not in registered_system_types():

        def _factory(cfg: dict) -> SystemCW:
            return SystemCW(SystemCWConfig(**cfg))

        register_system("system_cw", _factory)

    from axis.visualization.registry import registered_system_visualizations

    if "system_cw" not in registered_system_visualizations():
        try:
            import axis.systems.system_cw.visualization  # noqa: F401
        except ImportError:
            pass

    from axis.framework.metrics.extensions import registered_metric_extensions

    if "system_cw" not in registered_metric_extensions():
        try:
            import axis.systems.system_cw.metrics  # noqa: F401
        except ImportError:
            pass

    from axis.framework.comparison.extensions import registered_extensions

    if "system_cw" not in registered_extensions():
        try:
            import axis.systems.system_cw.comparison  # noqa: F401
        except ImportError:
            pass
