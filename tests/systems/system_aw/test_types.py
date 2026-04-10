"""WP-2 unit tests -- System A+W internal types."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis.systems.system_a.types import HungerDriveOutput, MemoryState
from axis.systems.system_aw.types import (
    AgentStateAW,
    CuriosityDriveOutput,
    DriveWeights,
    WorldModelState,
)


class TestWorldModelState:
    """WorldModelState unit tests."""

    def test_world_model_state_defaults(self) -> None:
        wm = WorldModelState()
        assert wm.relative_position == (0, 0)
        assert wm.visit_counts == ()

    def test_world_model_state_with_visits(self) -> None:
        visits = (((0, 0), 3), ((1, 0), 1))
        wm = WorldModelState(relative_position=(1, 0), visit_counts=visits)
        assert wm.relative_position == (1, 0)
        assert wm.visit_counts == visits
        assert len(wm.visit_counts) == 2

    def test_world_model_state_frozen(self) -> None:
        wm = WorldModelState()
        with pytest.raises(ValidationError):
            wm.relative_position = (1, 1)  # type: ignore[misc]


class TestCuriosityDriveOutput:
    """CuriosityDriveOutput unit tests."""

    def test_curiosity_drive_output_valid(self) -> None:
        out = CuriosityDriveOutput(
            activation=0.85,
            spatial_novelty=(1.0, 1.0, 0.5, 1.0),
            sensory_novelty=(0.0, 0.0, 0.3, 0.0),
            composite_novelty=(0.5, 0.5, 0.4, 0.5),
            action_contributions=(0.4, 0.4, 0.3, 0.4, -0.2, -0.2),
        )
        assert out.activation == 0.85
        assert len(out.spatial_novelty) == 4
        assert len(out.sensory_novelty) == 4
        assert len(out.composite_novelty) == 4
        assert len(out.action_contributions) == 6

    def test_curiosity_drive_output_activation_bounds(self) -> None:
        kwargs = dict(
            spatial_novelty=(0.0, 0.0, 0.0, 0.0),
            sensory_novelty=(0.0, 0.0, 0.0, 0.0),
            composite_novelty=(0.0, 0.0, 0.0, 0.0),
            action_contributions=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        )
        with pytest.raises(ValidationError):
            CuriosityDriveOutput(activation=-0.1, **kwargs)
        with pytest.raises(ValidationError):
            CuriosityDriveOutput(activation=1.1, **kwargs)

    def test_curiosity_drive_output_tuple_lengths(self) -> None:
        with pytest.raises(ValidationError):
            CuriosityDriveOutput(
                activation=0.5,
                spatial_novelty=(1.0, 1.0, 1.0),  # 3 instead of 4
                sensory_novelty=(0.0, 0.0, 0.0, 0.0),
                composite_novelty=(0.0, 0.0, 0.0, 0.0),
                action_contributions=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            )
        with pytest.raises(ValidationError):
            CuriosityDriveOutput(
                activation=0.5,
                spatial_novelty=(0.0, 0.0, 0.0, 0.0),
                sensory_novelty=(0.0, 0.0, 0.0, 0.0),
                composite_novelty=(0.0, 0.0, 0.0, 0.0),
                action_contributions=(0.0, 0.0, 0.0, 0.0,
                                      0.0),  # 5 instead of 6
            )


class TestDriveWeights:
    """DriveWeights unit tests."""

    def test_drive_weights_valid(self) -> None:
        w = DriveWeights(hunger_weight=0.475, curiosity_weight=0.250)
        assert w.hunger_weight == 0.475
        assert w.curiosity_weight == 0.250

    def test_drive_weights_nonneg(self) -> None:
        with pytest.raises(ValidationError):
            DriveWeights(hunger_weight=-0.1, curiosity_weight=0.5)
        with pytest.raises(ValidationError):
            DriveWeights(hunger_weight=0.5, curiosity_weight=-0.1)


class TestAgentStateAW:
    """AgentStateAW unit tests."""

    def _make_state(
        self,
        energy: float = 50.0,
        capacity: int = 5,
    ) -> AgentStateAW:
        return AgentStateAW(
            energy=energy,
            memory_state=MemoryState(entries=(), capacity=capacity),
            world_model=WorldModelState(),
        )

    def test_agent_state_aw_valid(self) -> None:
        state = self._make_state()
        assert state.energy == 50.0
        assert len(state.memory_state.entries) == 0
        assert state.world_model.relative_position == (0, 0)

    def test_agent_state_aw_frozen(self) -> None:
        state = self._make_state()
        with pytest.raises(ValidationError):
            state.energy = 99.0  # type: ignore[misc]

    def test_agent_state_aw_energy_nonneg(self) -> None:
        with pytest.raises(ValidationError):
            self._make_state(energy=-1.0)


class TestConventions:
    """Cross-type ordering convention tests."""

    def test_action_ordering_consistency(self) -> None:
        hunger_out = HungerDriveOutput(
            activation=0.5,
            action_contributions=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6),
        )
        curiosity_out = CuriosityDriveOutput(
            activation=0.5,
            spatial_novelty=(1.0, 1.0, 1.0, 1.0),
            sensory_novelty=(0.0, 0.0, 0.0, 0.0),
            composite_novelty=(0.5, 0.5, 0.5, 0.5),
            action_contributions=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6),
        )
        assert len(hunger_out.action_contributions) == 6
        assert len(curiosity_out.action_contributions) == 6


class TestSerialization:
    """Serialization round-trip tests."""

    def test_world_model_state_serializable(self) -> None:
        visits = (((0, 0), 3), ((1, 0), 1))
        wm = WorldModelState(relative_position=(1, 0), visit_counts=visits)
        data = wm.model_dump()
        restored = WorldModelState.model_validate(data)
        assert restored == wm

    def test_agent_state_aw_serializable(self) -> None:
        state = AgentStateAW(
            energy=75.0,
            memory_state=MemoryState(entries=(), capacity=5),
            world_model=WorldModelState(
                relative_position=(2, -1),
                visit_counts=(((0, 0), 1), ((1, 0), 2), ((2, -1), 1)),
            ),
        )
        data = state.model_dump()
        restored = AgentStateAW.model_validate(data)
        assert restored == state
