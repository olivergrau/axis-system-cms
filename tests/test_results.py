"""Tests for episode result structures."""

import pytest
from pydantic import ValidationError

from axis_system_a import (
    Action,
    AgentState,
    CellObservation,
    DecisionResult,
    HungerDriveOutput,
    MemoryState,
    Observation,
    Position,
    TerminationReason,
    TransitionTrace,
)
from axis_system_a.results import EpisodeResult, EpisodeStepRecord


def _make_observation() -> Observation:
    cell = CellObservation(traversability=1.0, resource=0.5)
    return Observation(current=cell, up=cell, down=cell, left=cell, right=cell)


def _make_drive_output() -> HungerDriveOutput:
    return HungerDriveOutput(
        activation=0.5,
        action_contributions=(0.1, 0.1, 0.1, 0.1, 0.3, -0.05),
    )


def _make_decision_result() -> DecisionResult:
    return DecisionResult(
        raw_contributions=(0.1, 0.1, 0.1, 0.1, 0.3, -0.05),
        admissibility_mask=(True, True, True, True, True, True),
        masked_contributions=(0.1, 0.1, 0.1, 0.1, 0.3, -0.05),
        probabilities=(0.15, 0.15, 0.15, 0.15, 0.2, 0.2),
        selected_action=Action.CONSUME,
    )


def _make_transition_trace() -> TransitionTrace:
    return TransitionTrace(
        action=Action.CONSUME,
        position_before=Position(x=1, y=1),
        position_after=Position(x=1, y=1),
        moved=False,
        consumed=True,
        resource_consumed=0.5,
        energy_before=50.0,
        energy_after=53.0,
        energy_delta=3.0,
        memory_entries_before=0,
        memory_entries_after=1,
        terminated=False,
    )


def _make_step_record(*, timestep: int = 0, terminated: bool = False) -> EpisodeStepRecord:
    return EpisodeStepRecord(
        timestep=timestep,
        observation=_make_observation(),
        action=Action.CONSUME,
        drive_output=_make_drive_output(),
        decision_result=_make_decision_result(),
        transition_trace=_make_transition_trace(),
        energy_after=53.0,
        terminated=terminated,
    )


class TestTerminationReason:
    def test_energy_depleted_value(self):
        assert TerminationReason.ENERGY_DEPLETED == "energy_depleted"

    def test_max_steps_reached_value(self):
        assert TerminationReason.MAX_STEPS_REACHED == "max_steps_reached"

    def test_is_string_enum(self):
        assert isinstance(TerminationReason.ENERGY_DEPLETED, str)


class TestEpisodeStepRecord:
    def test_valid_construction(self):
        record = _make_step_record()
        assert record.timestep == 0
        assert record.action is Action.CONSUME
        assert record.energy_after == 53.0
        assert record.terminated is False

    def test_frozen(self):
        record = _make_step_record()
        with pytest.raises(ValidationError):
            record.timestep = 1

    def test_timestep_negative_invalid(self):
        with pytest.raises(ValidationError):
            EpisodeStepRecord(
                timestep=-1,
                observation=_make_observation(),
                action=Action.STAY,
                drive_output=_make_drive_output(),
                decision_result=_make_decision_result(),
                transition_trace=_make_transition_trace(),
                energy_after=50.0,
                terminated=False,
            )

    def test_energy_after_negative_invalid(self):
        with pytest.raises(ValidationError):
            EpisodeStepRecord(
                timestep=0,
                observation=_make_observation(),
                action=Action.STAY,
                drive_output=_make_drive_output(),
                decision_result=_make_decision_result(),
                transition_trace=_make_transition_trace(),
                energy_after=-1.0,
                terminated=False,
            )

    def test_all_fields_present(self):
        record = _make_step_record()
        assert hasattr(record, "timestep")
        assert hasattr(record, "observation")
        assert hasattr(record, "action")
        assert hasattr(record, "drive_output")
        assert hasattr(record, "decision_result")
        assert hasattr(record, "transition_trace")
        assert hasattr(record, "energy_after")
        assert hasattr(record, "terminated")


class TestEpisodeResult:
    def test_valid_construction(self):
        record = _make_step_record(terminated=True)
        result = EpisodeResult(
            steps=(record,),
            total_steps=1,
            termination_reason=TerminationReason.ENERGY_DEPLETED,
            final_agent_state=AgentState(
                energy=0.0, memory_state=MemoryState(capacity=5),
            ),
            final_position=Position(x=1, y=1),
            final_observation=_make_observation(),
        )
        assert result.total_steps == 1
        assert result.termination_reason is TerminationReason.ENERGY_DEPLETED

    def test_frozen(self):
        record = _make_step_record(terminated=True)
        result = EpisodeResult(
            steps=(record,),
            total_steps=1,
            termination_reason=TerminationReason.ENERGY_DEPLETED,
            final_agent_state=AgentState(
                energy=0.0, memory_state=MemoryState(capacity=5),
            ),
            final_position=Position(x=1, y=1),
            final_observation=_make_observation(),
        )
        with pytest.raises(ValidationError):
            result.total_steps = 2

    def test_total_steps_negative_invalid(self):
        with pytest.raises(ValidationError):
            EpisodeResult(
                steps=(),
                total_steps=-1,
                termination_reason=TerminationReason.MAX_STEPS_REACHED,
                final_agent_state=AgentState(
                    energy=50.0, memory_state=MemoryState(capacity=5),
                ),
                final_position=Position(x=0, y=0),
                final_observation=_make_observation(),
            )

    def test_steps_is_tuple(self):
        result = EpisodeResult(
            steps=(),
            total_steps=0,
            termination_reason=TerminationReason.MAX_STEPS_REACHED,
            final_agent_state=AgentState(
                energy=50.0, memory_state=MemoryState(capacity=5),
            ),
            final_position=Position(x=0, y=0),
            final_observation=_make_observation(),
        )
        assert isinstance(result.steps, tuple)
