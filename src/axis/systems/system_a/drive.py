"""System A hunger drive -- drive activation and per-action contributions."""

from __future__ import annotations

from axis.systems.system_a.types import HungerDriveOutput, Observation


class SystemAHungerDrive:
    """Hunger drive for System A.

    Satisfies DriveInterface. Computes drive activation and per-action
    contributions based on energy level and observation.

    d_H(t) = clamp(1 - E_t / E_max, 0, 1)

    Movement:  s_dir     = d_H * r_dir
    Consume:   s_consume = d_H * w_consume * r_c
    Stay:      s_stay    = -lambda_stay * d_H
    """

    def __init__(
        self,
        *,
        consume_weight: float,
        stay_suppression: float,
        max_energy: float,
    ) -> None:
        self._consume_weight = consume_weight
        self._stay_suppression = stay_suppression
        self._max_energy = max_energy

    def compute(self, agent_state: object, observation: Observation) -> HungerDriveOutput:
        """Compute hunger drive output from current state and observation."""
        energy: float = agent_state.energy  # type: ignore[attr-defined]
        d_h = max(0.0, min(1.0, 1.0 - energy / self._max_energy))

        s_up = d_h * observation.up.resource
        s_down = d_h * observation.down.resource
        s_left = d_h * observation.left.resource
        s_right = d_h * observation.right.resource
        s_consume = d_h * self._consume_weight * observation.current.resource
        s_stay = -self._stay_suppression * d_h

        return HungerDriveOutput(
            activation=d_h,
            action_contributions=(s_up, s_down, s_left, s_right, s_consume, s_stay),
        )
