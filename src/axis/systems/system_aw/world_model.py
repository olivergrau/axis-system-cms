"""System A+W spatial world model -- dead reckoning and visit-count map."""

from __future__ import annotations

from axis.systems.system_aw.types import WorldModelState

# Agent-relative direction deltas.
# UP = (0, +1), DOWN = (0, -1) in the agent's frame.
# This is independent of the SDK's world coordinate system.
DIRECTION_DELTAS: dict[str, tuple[int, int]] = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
    "consume": (0, 0),
    "stay": (0, 0),
}

_CARDINAL_DIRECTIONS = ("up", "down", "left", "right")


def _to_dict(
    visit_counts: tuple[tuple[tuple[int, int], int], ...],
) -> dict[tuple[int, int], int]:
    """Convert frozen visit-count tuple to mutable dict."""
    return dict(visit_counts)


def _to_tuple(
    visit_dict: dict[tuple[int, int], int],
) -> tuple[tuple[tuple[int, int], int], ...]:
    """Convert working dict to sorted frozen tuple."""
    return tuple(sorted(visit_dict.items()))


def create_world_model() -> WorldModelState:
    """Create initial world model: position (0,0), visit count 1 at origin.

    Model reference: Section 4.1.6.
    """
    return WorldModelState(
        relative_position=(0, 0),
        visit_counts=(((0, 0), 1),),
    )


def update_world_model(
    state: WorldModelState,
    action: str,
    moved: bool,
) -> WorldModelState:
    """Update world model after an action.

    Dead reckoning: p_hat_{t+1} = p_hat_t + mu_t * delta(a_t)
    Visit count:    w_{t+1}(p_hat_{t+1}) += 1

    Model reference: Sections 4.1.3, 4.1.5.
    """
    if action not in DIRECTION_DELTAS:
        raise ValueError(f"Unknown action: {action!r}")

    dx, dy = DIRECTION_DELTAS[action]
    mu = 1 if moved else 0
    px, py = state.relative_position
    new_pos = (px + mu * dx, py + mu * dy)

    visits = _to_dict(state.visit_counts)
    visits[new_pos] = visits.get(new_pos, 0) + 1

    return WorldModelState(
        relative_position=new_pos,
        visit_counts=_to_tuple(visits),
    )


def get_visit_count(
    state: WorldModelState,
    rel_pos: tuple[int, int],
) -> int:
    """Return visit count at a relative position, 0 for unvisited."""
    for pos, count in state.visit_counts:
        if pos == rel_pos:
            return count
    return 0


def get_neighbor_position(
    state: WorldModelState,
    direction: str,
) -> tuple[int, int]:
    """Compute relative position of neighbor in given direction."""
    dx, dy = DIRECTION_DELTAS[direction]
    px, py = state.relative_position
    return (px + dx, py + dy)


def spatial_novelty(
    state: WorldModelState,
    direction: str,
    k: float = 1.0,
) -> float:
    """Spatial novelty for a neighbor direction.

    nu^spatial_dir = 1 / (1 + w_t(p_hat_t + delta(dir)))^k

    k controls decay sharpness: k=1 is standard, k>1 steepens
    the contrast between visited and unvisited cells.

    Model reference: Section 5.2.4.
    """
    neighbor = get_neighbor_position(state, direction)
    w = get_visit_count(state, neighbor)
    return 1.0 / (1.0 + w) ** k


def all_spatial_novelties(
    state: WorldModelState,
    k: float = 1.0,
) -> tuple[float, float, float, float]:
    """Spatial novelty for all four cardinal directions.

    Returns: (nu_up, nu_down, nu_left, nu_right)
    """
    return tuple(  # type: ignore[return-value]
        spatial_novelty(state, d, k) for d in _CARDINAL_DIRECTIONS
    )
