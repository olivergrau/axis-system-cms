"""WP-5 unit tests -- SystemAWHungerDrive."""

from __future__ import annotations

import pytest

from axis.systems.system_a.drive import SystemAHungerDrive
from axis.systems.system_a.types import (
    AgentState,
    CellObservation,
    HungerDriveOutput,
    ObservationBuffer,
    Observation,
)
from axis.systems.system_aw.drive_hunger import SystemAWHungerDrive
from axis.systems.system_aw.types import AgentStateAW, WorldModelState


def _make_drive(
    consume_weight: float = 2.5,
    stay_suppression: float = 0.1,
    max_energy: float = 100.0,
) -> SystemAWHungerDrive:
    return SystemAWHungerDrive(
        consume_weight=consume_weight,
        stay_suppression=stay_suppression,
        max_energy=max_energy,
    )


def _make_agent_state_aw(energy: float = 50.0) -> AgentStateAW:
    return AgentStateAW(
        energy=energy,
        observation_buffer=ObservationBuffer(entries=(), capacity=5),
        world_model=WorldModelState(),
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


class TestBasicBehavior:
    """Hunger drive basic behavior tests."""

    def test_fully_sated(self) -> None:
        drive = _make_drive()
        state = _make_agent_state_aw(energy=100.0)
        obs = _make_observation(current_r=0.8)
        out = drive.compute(state, obs)
        assert out.activation == pytest.approx(0.0)
        # All contributions should be 0 (d_H * anything = 0)
        for i in range(5):
            assert out.action_contributions[i] == pytest.approx(0.0)

    def test_starving(self) -> None:
        drive = _make_drive()
        state = _make_agent_state_aw(energy=0.0)
        obs = _make_observation(current_r=0.8)
        out = drive.compute(state, obs)
        assert out.activation == pytest.approx(1.0)
        assert out.action_contributions[4] == pytest.approx(
            2.5 * 0.8)  # CONSUME

    def test_half_energy(self) -> None:
        drive = _make_drive()
        state = _make_agent_state_aw(energy=50.0)
        obs = _make_observation()
        out = drive.compute(state, obs)
        assert out.activation == pytest.approx(0.5)

    def test_movement_contribution(self) -> None:
        drive = _make_drive()
        state = _make_agent_state_aw(energy=50.0)
        obs = _make_observation(up_r=0.4)
        out = drive.compute(state, obs)
        assert out.action_contributions[0] == pytest.approx(0.5 * 0.4)  # UP

    def test_consume_contribution(self) -> None:
        drive = _make_drive(consume_weight=2.5)
        state = _make_agent_state_aw(energy=50.0)
        obs = _make_observation(current_r=0.8)
        out = drive.compute(state, obs)
        assert out.action_contributions[4] == pytest.approx(0.5 * 2.5 * 0.8)

    def test_stay_suppression(self) -> None:
        drive = _make_drive(stay_suppression=0.1)
        state = _make_agent_state_aw(energy=50.0)
        obs = _make_observation()
        out = drive.compute(state, obs)
        assert out.action_contributions[5] == pytest.approx(-0.1 * 0.5)  # STAY


class TestCompatibility:
    """AgentStateAW compatibility tests."""

    def test_works_with_agent_state_aw(self) -> None:
        drive = _make_drive()
        state = _make_agent_state_aw(energy=90.0)
        obs = _make_observation()
        out = drive.compute(state, obs)
        assert out.activation == pytest.approx(0.1)

    def test_output_type(self) -> None:
        drive = _make_drive()
        state = _make_agent_state_aw()
        obs = _make_observation()
        out = drive.compute(state, obs)
        assert isinstance(out, HungerDriveOutput)

    def test_contributions_tuple_length(self) -> None:
        drive = _make_drive()
        state = _make_agent_state_aw()
        obs = _make_observation()
        out = drive.compute(state, obs)
        assert len(out.action_contributions) == 6


class TestWorkedExamples:
    """Worked example verification."""

    def test_example_a1_hunger(self) -> None:
        """A1: e=90, E_max=100 -> d_H=0.10."""
        drive = _make_drive(consume_weight=2.5, stay_suppression=0.1)
        state = _make_agent_state_aw(energy=90.0)
        obs = _make_observation(
            current_r=0.8, up_r=0.0, down_r=0.0, left_r=0.3, right_r=0.0,
        )
        out = drive.compute(state, obs)
        assert out.activation == pytest.approx(0.10, abs=0.005)
        # phi_H: UP=0.0, DOWN=0.0, LEFT=0.03, RIGHT=0.0, CONSUME=0.20, STAY=-0.01
        assert out.action_contributions[0] == pytest.approx(
            0.0, abs=0.005)       # UP
        assert out.action_contributions[2] == pytest.approx(
            0.03, abs=0.005)      # LEFT
        assert out.action_contributions[4] == pytest.approx(
            0.20, abs=0.005)      # CONSUME
        # STAY
        assert out.action_contributions[5] == pytest.approx(-0.01, abs=0.005)

    def test_example_b1_hunger(self) -> None:
        """B1: e=50, d_H=0.50."""
        drive = _make_drive(consume_weight=2.5, stay_suppression=0.1)
        state = _make_agent_state_aw(energy=50.0)
        obs = _make_observation(
            current_r=0.6, up_r=0.0, down_r=0.4, left_r=0.0, right_r=0.0,
        )
        out = drive.compute(state, obs)
        assert out.activation == pytest.approx(0.50, abs=0.005)
        assert out.action_contributions[1] == pytest.approx(
            0.20, abs=0.005)     # DOWN
        assert out.action_contributions[4] == pytest.approx(
            0.75, abs=0.005)     # CONSUME

    def test_example_c1_hunger(self) -> None:
        """C1: e=5, d_H=0.95."""
        drive = _make_drive(consume_weight=2.5, stay_suppression=0.1)
        state = _make_agent_state_aw(energy=5.0)
        obs = _make_observation(
            current_r=0.5, up_r=0.0, down_r=0.0, left_r=0.0, right_r=0.2,
        )
        out = drive.compute(state, obs)
        assert out.activation == pytest.approx(0.95, abs=0.005)
        assert out.action_contributions[4] == pytest.approx(
            0.95 * 2.5 * 0.5, abs=0.01)
        assert out.action_contributions[3] == pytest.approx(
            0.95 * 0.2, abs=0.01)


class TestIdentity:
    """Identity with System A drive."""

    def test_matches_system_a_drive(self) -> None:
        aw_drive = _make_drive()
        a_drive = SystemAHungerDrive(
            consume_weight=2.5, stay_suppression=0.1, max_energy=100.0,
        )
        for energy in [0.0, 25.0, 50.0, 75.0, 100.0]:
            state = _make_agent_state_aw(energy=energy)
            obs = _make_observation(
                current_r=0.5, up_r=0.3, down_r=0.1, left_r=0.7, right_r=0.2,
            )
            aw_out = aw_drive.compute(state, obs)
            a_out = a_drive.compute(state, obs)
            assert aw_out.activation == pytest.approx(a_out.activation)
            for i in range(6):
                assert aw_out.action_contributions[i] == pytest.approx(
                    a_out.action_contributions[i],
                )
