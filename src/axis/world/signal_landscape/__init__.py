"""Signal landscape world package -- drifting-hotspot world for scout agents.

Registered as world type ``"signal_landscape"``.
"""

from axis.world.signal_landscape.config import SignalLandscapeConfig
from axis.world.signal_landscape.dynamics import Hotspot
from axis.world.signal_landscape.factory import create_signal_landscape
from axis.world.signal_landscape.model import (
    SignalCell,
    SignalCellType,
    SignalLandscapeWorld,
)

__all__ = [
    "SignalCell",
    "SignalCellType",
    "SignalLandscapeWorld",
    "SignalLandscapeConfig",
    "Hotspot",
    "create_signal_landscape",
]


def register() -> None:
    """Register signal_landscape: world factory + visualization adapter."""
    from axis.world.registry import register_world, registered_world_types

    if "signal_landscape" not in registered_world_types():

        def _factory(config, agent_position, seed):
            return create_signal_landscape(config, agent_position, seed=seed)

        register_world("signal_landscape", _factory)

    from axis.visualization.registry import registered_world_visualizations

    if "signal_landscape" not in registered_world_visualizations():
        try:
            import axis.world.signal_landscape.visualization  # noqa: F401
        except ImportError:
            pass
