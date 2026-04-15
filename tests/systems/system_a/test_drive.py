"""WP-2.4 unit tests -- HungerDrive."""

from __future__ import annotations

import pytest

from axis.sdk.interfaces import DriveInterface
from axis.systems.construction_kit.observation.types import CellObservation, Observation
from axis.systems.construction_kit.drives.hunger import HungerDrive
from axis.systems.construction_kit.drives.types import HungerDriveOutput
from axis.systems.construction_kit.memory.types import ObservationBuffer
from axis.systems.system_a.types import AgentState


def _make_drive(
    consume_weight: float = 1.5,
    stay_suppression: float = 0.1,
    max_energy: float = 100.0,
) -> HungerDrive:
    return HungerDrive(
        consume_weight=consume_weight,
        stay_suppression=stay_suppression,
        max_energy=max_energy,
    )


def _make_state(energy: float) -> AgentState:
    return AgentState(
        energy=energy,
        observation_buffer=ObservationBuffer(entries=(), capacity=5),
    )


def _make_observation(
    current_r: float = 0.0,
    up_r: float = 0.0,
    down_r: float = 0.0,
    left_r: float = 0.0,
    right_r: float = 0.0,
) -> Observation:
    return Observation(
        current=CellObservation(traversability=1.0, resource=current_r),
        up=CellObservation(traversability=1.0, resource=up_r),
        down=CellObservation(traversability=1.0, resource=down_r),
        left=CellObservation(traversability=1.0, resource=left_r),
        right=CellObservation(traversability=1.0, resource=right_r),
    )


class TestDrive:
    """HungerDrive unit tests."""

    def test_full_energy_zero_activation(self) -> None:
        drive = _make_drive()
        output = drive.compute(_make_state(
            100.0), _make_observation(0.5, 0.5, 0.5, 0.5, 0.5))
        assert output.activation == 0.0
        assert all(c == 0.0 for c in output.action_contributions)

    def test_zero_energy_full_activation(self) -> None:
        drive = _make_drive()
        output = drive.compute(_make_state(0.0), _make_observation())
        assert output.activation == 1.0

    def test_half_energy_half_activation(self) -> None:
        drive = _make_drive()
        output = drive.compute(_make_state(50.0), _make_observation())
        assert output.activation == pytest.approx(0.5)

    def test_movement_contribution_proportional_to_resource(self) -> None:
        drive = _make_drive()
        output = drive.compute(_make_state(50.0), _make_observation(up_r=0.6))
        # s_up = activation * resource = 0.5 * 0.6 = 0.3
        assert output.action_contributions[0] == pytest.approx(0.3)

    def test_consume_contribution_weighted(self) -> None:
        drive = _make_drive(consume_weight=1.5)
        output = drive.compute(_make_state(
            50.0), _make_observation(current_r=0.5))
        # s_consume = activation * consume_weight * current_resource = 0.5 * 1.5 * 0.5 = 0.375
        assert output.action_contributions[4] == pytest.approx(0.375)

    def test_stay_contribution_negative(self) -> None:
        drive = _make_drive(stay_suppression=0.1)
        output = drive.compute(_make_state(50.0), _make_observation())
        # s_stay = -stay_suppression * activation = -0.1 * 0.5 = -0.05
        assert output.action_contributions[5] == pytest.approx(-0.05)
        assert output.action_contributions[5] < 0

    def test_zero_resource_neighbors_zero_movement_contributions(self) -> None:
        drive = _make_drive()
        output = drive.compute(_make_state(50.0), _make_observation())
        # All neighbor resources are 0, so movement contributions should be 0
        assert output.action_contributions[0] == 0.0  # up
        assert output.action_contributions[1] == 0.0  # down
        assert output.action_contributions[2] == 0.0  # left
        assert output.action_contributions[3] == 0.0  # right

    def test_contributions_tuple_length(self) -> None:
        drive = _make_drive()
        output = drive.compute(_make_state(50.0), _make_observation())
        assert isinstance(output, HungerDriveOutput)
        assert len(output.action_contributions) == 6

    def test_drive_interface_conformance(self) -> None:
        drive = _make_drive()
        assert isinstance(drive, DriveInterface)
