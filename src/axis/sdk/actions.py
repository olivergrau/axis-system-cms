"""Base action constants shared across all systems.

These actions are handled by the framework's world action engine.
Systems may declare additional actions (e.g., 'consume') in their
action_space(). Additional actions require registered handlers.
"""

# Movement actions -- handled by framework
UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"

# Inaction -- handled by framework
STAY = "stay"

# Ordered tuple of base actions
BASE_ACTIONS: tuple[str, ...] = (UP, DOWN, LEFT, RIGHT, STAY)

# Movement direction deltas: action -> (dx, dy)
MOVEMENT_DELTAS: dict[str, tuple[int, int]] = {
    UP: (0, -1),
    DOWN: (0, +1),
    LEFT: (-1, 0),
    RIGHT: (+1, 0),
}
