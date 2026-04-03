"""Tests for episode result structures."""

import json

import pytest
from pydantic import ValidationError

from axis_system_a import (
    Action,
    AgentSnapshot,
    AgentState,
    CellObservation,
    Cell,
    CellType,
    DecisionTrace,
    HungerDriveOutput,
    MemoryState,
    Observation,
    Position,
    RegenSummary,
    SelectionMode,
    TerminationReason,
    TransitionTrace,
    WorldSnapshot,
)
from axis_system_a.results import (
    EpisodeResult,
    EpisodeSummary,
    StepResult,
    compute_episode_summary,
)
from tests.fixtures.observation_fixtures import make_observation


def _make_drive_output() -> HungerDriveOutput:
    return HungerDriveOutput(
        activation=0.5,
        action_contributions=(0.1, 0.1, 0.1, 0.1, 0.3, -0.05),
    )


def _make_decision_result() -> DecisionTrace:
    return DecisionTrace(
        raw_contributions=(0.1, 0.1, 0.1, 0.1, 0.3, -0.05),
        admissibility_mask=(True, True, True, True, True, True),
        masked_contributions=(0.1, 0.1, 0.1, 0.1, 0.3, -0.05),
        probabilities=(0.15, 0.15, 0.15, 0.15, 0.2, 0.2),
        selected_action=Action.CONSUME,
        temperature=1.0,
        selection_mode=SelectionMode.ARGMAX,
    )


def _make_world_snapshot() -> WorldSnapshot:
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    return WorldSnapshot(
        grid=((empty,),), agent_position=Position(x=0, y=0),
        width=1, height=1,
    )


def _make_transition_trace(*, terminated: bool = False) -> TransitionTrace:
    ws = _make_world_snapshot()
    ms = MemoryState(capacity=5)
    return TransitionTrace(
        action=Action.CONSUME,
        position_before=Position(x=1, y=1),
        position_after=Position(x=1, y=1),
        moved=False,
        consumed=True,
        resource_consumed=0.5,
        energy_before=50.0,
        energy_after=53.0 if not terminated else 0.0,
        energy_delta=3.0 if not terminated else -50.0,
        memory_entries_before=0,
        memory_entries_after=1,
        terminated=terminated,
        world_before=ws,
        world_after_regen=ws,
        world_after_action=ws,
        agent_snapshot_before=AgentSnapshot(
            energy=50.0, position=Position(x=1, y=1),
            memory_entry_count=0, memory_timestep_range=None,
        ),
        agent_snapshot_after=AgentSnapshot(
            energy=53.0 if not terminated else 0.0,
            position=Position(x=1, y=1),
            memory_entry_count=1, memory_timestep_range=(0, 0),
        ),
        memory_state_before=ms,
        memory_state_after=MemoryState(entries=(), capacity=5),
        observation_before=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
        observation_after=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
        regen_summary=RegenSummary(cells_updated=0, regen_rate=0.0),
        termination_reason=(
            TerminationReason.ENERGY_DEPLETED if terminated else None
        ),
    )


def _make_step_result(
    *, timestep: int = 0, terminated: bool = False,
) -> StepResult:
    return StepResult(
        timestep=timestep,
        observation=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
        selected_action=Action.CONSUME,
        drive_output=_make_drive_output(),
        decision_result=_make_decision_result(),
        transition_trace=_make_transition_trace(terminated=terminated),
        energy_before=50.0,
        energy_after=53.0 if not terminated else 0.0,
        terminated=terminated,
    )


def _make_summary(steps: tuple[StepResult, ...]) -> EpisodeSummary:
    return compute_episode_summary(steps)


class TestTerminationReason:
    def test_energy_depleted_value(self):
        assert TerminationReason.ENERGY_DEPLETED == "energy_depleted"

    def test_max_steps_reached_value(self):
        assert TerminationReason.MAX_STEPS_REACHED == "max_steps_reached"

    def test_is_string_enum(self):
        assert isinstance(TerminationReason.ENERGY_DEPLETED, str)


class TestStepResult:
    def test_valid_construction(self):
        record = _make_step_result()
        assert record.timestep == 0
        assert record.selected_action is Action.CONSUME
        assert record.energy_before == 50.0
        assert record.energy_after == 53.0
        assert record.terminated is False

    def test_frozen(self):
        record = _make_step_result()
        with pytest.raises(ValidationError):
            record.timestep = 1

    def test_timestep_negative_invalid(self):
        with pytest.raises(ValidationError):
            StepResult(
                timestep=-1,
                observation=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
                selected_action=Action.STAY,
                drive_output=_make_drive_output(),
                decision_result=_make_decision_result(),
                transition_trace=_make_transition_trace(),
                energy_before=50.0,
                energy_after=50.0,
                terminated=False,
            )

    def test_energy_after_negative_invalid(self):
        with pytest.raises(ValidationError):
            StepResult(
                timestep=0,
                observation=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
                selected_action=Action.STAY,
                drive_output=_make_drive_output(),
                decision_result=_make_decision_result(),
                transition_trace=_make_transition_trace(),
                energy_before=50.0,
                energy_after=-1.0,
                terminated=False,
            )

    def test_all_fields_present(self):
        record = _make_step_result()
        assert hasattr(record, "timestep")
        assert hasattr(record, "observation")
        assert hasattr(record, "selected_action")
        assert hasattr(record, "drive_output")
        assert hasattr(record, "decision_result")
        assert hasattr(record, "transition_trace")
        assert hasattr(record, "energy_before")
        assert hasattr(record, "energy_after")
        assert hasattr(record, "terminated")

    def test_selected_action_consistency(self):
        record = _make_step_result()
        assert record.selected_action is record.decision_result.selected_action

    def test_to_dict(self):
        record = _make_step_result()
        d = record.to_dict()
        assert isinstance(d, dict)
        json.dumps(d, default=str)


class TestEpisodeSummary:
    def test_valid_construction(self):
        steps = (_make_step_result(timestep=0), _make_step_result(timestep=1))
        summary = compute_episode_summary(steps)
        assert summary.survival_length == 2
        assert summary.total_consume_events == 2
        assert summary.mean_energy == 53.0

    def test_action_counts_sum_to_total(self):
        steps = (_make_step_result(timestep=0), _make_step_result(timestep=1))
        summary = compute_episode_summary(steps)
        assert sum(summary.action_counts.values()) == 2

    def test_empty_steps(self):
        summary = compute_episode_summary(())
        assert summary.survival_length == 0
        assert summary.mean_energy == 0.0

    def test_frozen(self):
        steps = (_make_step_result(),)
        summary = compute_episode_summary(steps)
        with pytest.raises(ValidationError):
            summary.survival_length = 99


class TestEpisodeResult:
    def test_valid_construction(self):
        record = _make_step_result(terminated=True)
        steps = (record,)
        result = EpisodeResult(
            steps=steps,
            total_steps=1,
            termination_reason=TerminationReason.ENERGY_DEPLETED,
            final_agent_state=AgentState(
                energy=0.0, memory_state=MemoryState(capacity=5),
            ),
            final_position=Position(x=1, y=1),
            final_observation=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
            summary=_make_summary(steps),
        )
        assert result.total_steps == 1
        assert result.termination_reason is TerminationReason.ENERGY_DEPLETED

    def test_frozen(self):
        record = _make_step_result(terminated=True)
        steps = (record,)
        result = EpisodeResult(
            steps=steps,
            total_steps=1,
            termination_reason=TerminationReason.ENERGY_DEPLETED,
            final_agent_state=AgentState(
                energy=0.0, memory_state=MemoryState(capacity=5),
            ),
            final_position=Position(x=1, y=1),
            final_observation=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
            summary=_make_summary(steps),
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
                final_observation=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
                summary=compute_episode_summary(()),
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
            final_observation=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
            summary=compute_episode_summary(()),
        )
        assert isinstance(result.steps, tuple)

    def test_to_dict(self):
        record = _make_step_result(terminated=True)
        steps = (record,)
        result = EpisodeResult(
            steps=steps,
            total_steps=1,
            termination_reason=TerminationReason.ENERGY_DEPLETED,
            final_agent_state=AgentState(
                energy=0.0, memory_state=MemoryState(capacity=5),
            ),
            final_position=Position(x=1, y=1),
            final_observation=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
            summary=_make_summary(steps),
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        json.dumps(d, default=str)

    def test_summary_matches_steps(self):
        record = _make_step_result(terminated=True)
        steps = (record,)
        result = EpisodeResult(
            steps=steps,
            total_steps=1,
            termination_reason=TerminationReason.ENERGY_DEPLETED,
            final_agent_state=AgentState(
                energy=0.0, memory_state=MemoryState(capacity=5),
            ),
            final_position=Position(x=1, y=1),
            final_observation=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
            summary=_make_summary(steps),
        )
        assert result.summary.survival_length == result.total_steps
