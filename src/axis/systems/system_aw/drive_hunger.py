"""System A+W hunger drive -- delegates to System A's hunger drive."""

from __future__ import annotations

from axis.systems.system_a.drive import SystemAHungerDrive
from axis.systems.system_a.types import HungerDriveOutput, Observation


class SystemAWHungerDrive:
    """Hunger drive for System A+W.

    Thin wrapper that delegates entirely to System A's hunger drive.
    Works with AgentStateAW via duck-typing on the energy attribute.

    Model reference: Sections 5.1, 6.2.
    """

    def __init__(
        self,
        *,
        consume_weight: float,
        stay_suppression: float,
        max_energy: float,
    ) -> None:
        self._drive = SystemAHungerDrive(
            consume_weight=consume_weight,
            stay_suppression=stay_suppression,
            max_energy=max_energy,
        )

    def compute(
        self,
        agent_state: object,
        observation: Observation,
    ) -> HungerDriveOutput:
        """Compute hunger drive activation and action contributions.

        agent_state must have an energy: float attribute.
        """
        return self._drive.compute(agent_state, observation)
