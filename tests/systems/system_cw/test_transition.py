from __future__ import annotations

from axis.sdk.position import Position
from axis.sdk.world_types import ActionOutcome
from axis.systems.construction_kit.observation.types import CellObservation, Observation
from axis.systems.system_cw.config import SystemCWConfig
from axis.systems.system_cw.system import SystemCW
from tests.builders.system_cw_config_builder import SystemCWConfigBuilder


def _make_observation(current: float, neighbors: float = 0.0) -> Observation:
    current_cell = CellObservation(traversability=1.0, resource=current)
    neighbor_cell = CellObservation(traversability=1.0, resource=neighbors)
    return Observation(
        current=current_cell,
        up=neighbor_cell,
        down=neighbor_cell,
        left=neighbor_cell,
        right=neighbor_cell,
    )


def test_first_transition_populates_last_observation_without_prediction_update() -> None:
    system = SystemCW(SystemCWConfig(**SystemCWConfigBuilder().build()))
    state = system.initialize_state()
    result = system.transition(
        state,
        ActionOutcome(action="stay", moved=False, new_position=Position(x=0, y=0)),
        _make_observation(0.2, 0.1),
    )
    assert result.new_state.last_observation is not None
    assert "prediction" not in result.trace_data


def test_second_transition_updates_shared_memory_and_both_trace_paths() -> None:
    system = SystemCW(SystemCWConfig(**SystemCWConfigBuilder().build()))
    state = system.initialize_state()
    first = system.transition(
        state,
        ActionOutcome(action="up", moved=True, new_position=Position(x=0, y=1)),
        _make_observation(0.0, 0.2),
    )
    second = system.transition(
        first.new_state,
        ActionOutcome(action="up", moved=True, new_position=Position(x=0, y=2)),
        _make_observation(0.4, 0.8),
    )
    prediction = second.trace_data["prediction"]
    assert prediction["predicted_features"] is not None
    assert second.new_state.predictive_memory != first.new_state.predictive_memory
    assert second.new_state.hunger_trace_state != first.new_state.hunger_trace_state
    assert second.new_state.curiosity_trace_state != first.new_state.curiosity_trace_state
    assert prediction["curiosity"]["is_movement_action"] is True
    assert prediction["curiosity"]["used_nonmove_penalty_rule"] is False


def test_nonmovement_transition_marks_curiosity_penalty_branch() -> None:
    system = SystemCW(SystemCWConfig(**SystemCWConfigBuilder().build()))
    state = system.initialize_state()
    first = system.transition(
        state,
        ActionOutcome(action="stay", moved=False, new_position=Position(x=0, y=0)),
        _make_observation(0.2, 0.1),
    )
    second = system.transition(
        first.new_state,
        ActionOutcome(action="stay", moved=False, new_position=Position(x=0, y=0)),
        _make_observation(0.3, 0.2),
    )
    prediction = second.trace_data["prediction"]
    assert prediction["curiosity"]["is_movement_action"] is False
    assert prediction["curiosity"]["used_nonmove_penalty_rule"] is True
