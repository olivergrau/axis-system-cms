"""System A+W curiosity drive -- novelty computation and drive pipeline."""

from __future__ import annotations

from axis.systems.system_a.types import MemoryState, Observation
from axis.systems.system_aw.types import CuriosityDriveOutput, WorldModelState
from axis.systems.system_aw.world_model import all_spatial_novelties


def compute_spatial_novelty(
    world_model: WorldModelState,
    k: float = 1.0,
) -> tuple[float, float, float, float]:
    """Per-direction spatial novelty from the visit-count map.

    Returns: (nu_up, nu_down, nu_left, nu_right)

    nu^spatial_dir = 1 / (1 + w_t(p_hat_t + delta(dir)))^k

    Model reference: Section 5.2.4.
    """
    return all_spatial_novelties(world_model, k)


def compute_sensory_novelty(
    observation: Observation,
    memory: MemoryState,
) -> tuple[float, float, float, float]:
    """Per-direction sensory novelty from observation vs memory mean.

    Returns: (nu_up, nu_down, nu_left, nu_right)

    nu^sensory_dir = |r_dir(t) - mean(r_dir over memory)|
    When memory is empty, mean = 0.

    Model reference: Section 5.2.5.
    """
    current = (
        observation.up.resource,
        observation.down.resource,
        observation.left.resource,
        observation.right.resource,
    )

    if len(memory.entries) == 0:
        return current  # |r - 0| = r (all non-negative)

    n = len(memory.entries)
    means = [0.0, 0.0, 0.0, 0.0]
    for entry in memory.entries:
        obs = entry.observation
        means[0] += obs.up.resource
        means[1] += obs.down.resource
        means[2] += obs.left.resource
        means[3] += obs.right.resource
    means = [m / n for m in means]

    # type: ignore[return-value]
    return tuple(abs(c - m) for c, m in zip(current, means))


def compute_composite_novelty(
    spatial: tuple[float, float, float, float],
    sensory: tuple[float, float, float, float],
    alpha: float,
) -> tuple[float, float, float, float]:
    """Alpha-weighted blend of spatial and sensory novelty.

    nu_dir = alpha * nu^spatial_dir + (1 - alpha) * nu^sensory_dir

    alpha=1.0: pure spatial (visit-count only)
    alpha=0.0: pure sensory (observation-difference only)
    alpha=0.5: equal weighting (default)

    Model reference: Section 5.2.6.
    """
    return tuple(  # type: ignore[return-value]
        alpha * s_spatial + (1 - alpha) * s_sensory
        for s_spatial, s_sensory in zip(spatial, sensory)
    )


def compute_novelty_saturation(memory: MemoryState) -> float:
    """Compute mean novelty saturation from memory.

    Returns 0.0 when memory is empty (maximum curiosity).

    sigma_j = mean over directions of |r_dir^(j) - mean(r_dir)|
    nu_bar_t = mean over entries of sigma_j

    Model reference: Section 5.2.2.
    """
    entries = memory.entries
    if len(entries) == 0:
        return 0.0

    n = len(entries)

    # Compute per-direction means across all entries
    dir_sums = [0.0, 0.0, 0.0, 0.0]
    for entry in entries:
        obs = entry.observation
        dir_sums[0] += obs.up.resource
        dir_sums[1] += obs.down.resource
        dir_sums[2] += obs.left.resource
        dir_sums[3] += obs.right.resource
    dir_means = [s / n for s in dir_sums]

    # Compute per-entry surprise sigma_j
    total_surprise = 0.0
    for entry in entries:
        obs = entry.observation
        entry_resources = (
            obs.up.resource,
            obs.down.resource,
            obs.left.resource,
            obs.right.resource,
        )
        sigma_j = sum(
            abs(r - m) for r, m in zip(entry_resources, dir_means)
        ) / 4
        total_surprise += sigma_j

    return total_surprise / n


def compute_curiosity_activation(
    base_curiosity: float,
    novelty_saturation: float,
) -> float:
    """Compute curiosity drive activation.

    d_C = mu_C * (1 - nu_bar_t)

    Bounded to [0, mu_C].

    Model reference: Section 5.2.1.
    """
    return base_curiosity * (1.0 - novelty_saturation)


class SystemAWCuriosityDrive:
    """Curiosity drive for System A+W.

    Computes the curiosity drive activation and per-action
    contributions from the composite novelty signal.

    Model reference: Sections 5.2, 6.3.
    """

    def __init__(
        self,
        *,
        base_curiosity: float,
        spatial_sensory_balance: float,
        explore_suppression: float,
        novelty_sharpness: float = 1.0,
    ) -> None:
        self._mu_c = base_curiosity
        self._alpha = spatial_sensory_balance
        self._lambda_explore = explore_suppression
        self._k = novelty_sharpness

    def compute(
        self,
        observation: Observation,
        memory: MemoryState,
        world_model: WorldModelState,
    ) -> CuriosityDriveOutput:
        """Compute curiosity drive output.

        Pipeline:
        1. Spatial novelty (from world model)
        2. Sensory novelty (from observation + memory)
        3. Composite novelty (alpha-blend)
        4. Novelty saturation (from memory)
        5. Drive activation
        6. Action contributions
        """
        spatial = compute_spatial_novelty(world_model, self._k)
        sensory = compute_sensory_novelty(observation, memory)
        composite = compute_composite_novelty(spatial, sensory, self._alpha)

        saturation = compute_novelty_saturation(memory)
        activation = compute_curiosity_activation(self._mu_c, saturation)

        # Action contributions (Model Section 6.3)
        # Movement: phi_C(dir) = nu_dir (composite novelty)
        # CONSUME/STAY: phi_C = -lambda_explore
        action_contributions = (
            composite[0],               # UP
            composite[1],               # DOWN
            composite[2],               # LEFT
            composite[3],               # RIGHT
            -self._lambda_explore,      # CONSUME
            -self._lambda_explore,      # STAY
        )

        return CuriosityDriveOutput(
            activation=activation,
            spatial_novelty=spatial,
            sensory_novelty=sensory,
            composite_novelty=composite,
            action_contributions=action_contributions,
        )
