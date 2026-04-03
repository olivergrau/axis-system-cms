"""Action space and selection mode enums for AXIS System A."""

import enum


class Action(enum.IntEnum):
    """Agent action space.

    Stable ordering used by policy and drive modules for array indexing.
    """

    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    CONSUME = 4
    STAY = 5


class SelectionMode(str, enum.Enum):
    """Policy action selection mode."""

    SAMPLE = "sample"
    ARGMAX = "argmax"


class CellType(str, enum.Enum):
    """Grid cell type."""

    EMPTY = "empty"
    RESOURCE = "resource"
    OBSTACLE = "obstacle"


class TerminationReason(str, enum.Enum):
    """Reason for episode termination."""

    ENERGY_DEPLETED = "energy_depleted"
    MAX_STEPS_REACHED = "max_steps_reached"
