"""System SDK -- interfaces, contracts, and base types."""

from axis.sdk.actions import BASE_ACTIONS, DOWN, LEFT, MOVEMENT_DELTAS, RIGHT, STAY, UP
from axis.sdk.interfaces import (
    DriveInterface,
    PolicyInterface,
    SensorInterface,
    SystemInterface,
    TransitionInterface,
)
from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot, snapshot_world
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.types import DecideResult, PolicyResult, TransitionResult
from axis.sdk.world_types import (
    ActionOutcome,
    BaseWorldConfig,
    CellView,
    MutableWorldProtocol,
    WorldView,
)

__all__ = [
    # Interfaces
    "SystemInterface",
    "SensorInterface",
    "DriveInterface",
    "PolicyInterface",
    "TransitionInterface",
    # Data types
    "DecideResult",
    "TransitionResult",
    "PolicyResult",
    "Position",
    "CellView",
    "WorldView",
    "ActionOutcome",
    "BaseWorldConfig",
    "MutableWorldProtocol",
    # Replay contract
    "WorldSnapshot",
    "snapshot_world",
    "BaseStepTrace",
    "BaseEpisodeTrace",
    # Action constants
    "BASE_ACTIONS",
    "UP",
    "DOWN",
    "LEFT",
    "RIGHT",
    "STAY",
    "MOVEMENT_DELTAS",
]
