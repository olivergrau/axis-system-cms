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

# --- Registration ---
from axis.world.registry import register_world  # noqa: E402


def _signal_landscape_factory(
    config: object,
    agent_position: object,
    seed: object,
) -> SignalLandscapeWorld:
    # type: ignore[arg-type]
    return create_signal_landscape(config, agent_position, seed=seed)


# type: ignore[arg-type]
register_world("signal_landscape", _signal_landscape_factory)
