from __future__ import annotations

import numpy as np

from axis.systems.system_cw.config import SystemCWConfig
from axis.systems.system_cw.system import SystemCW
from axis.systems.system_cw.types import AgentStateCW
from axis.world.grid_2d.model import Cell, CellType, World
from axis.sdk.position import Position
from tests.builders.system_cw_config_builder import SystemCWConfigBuilder


def _make_resource_grid(width: int, height: int, value: float = 0.5) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.RESOURCE, resource_value=value) for _ in range(width)]
        for _ in range(height)
    ]


def test_initialize_state_uses_shared_memory_and_two_trace_states() -> None:
    system = SystemCW(SystemCWConfig(**SystemCWConfigBuilder().build()))
    state = system.initialize_state()
    assert isinstance(state, AgentStateCW)
    assert state.predictive_memory.feature_dim == 10
    assert state.hunger_trace_state.confidence == ()
    assert state.curiosity_trace_state.confidence == ()


def test_decide_exposes_dual_modulation_payload() -> None:
    system = SystemCW(SystemCWConfig(**SystemCWConfigBuilder().build()))
    world = World(_make_resource_grid(5, 5, 0.5), Position(x=2, y=2))
    result = system.decide(world, system.initialize_state(), np.random.default_rng(42))
    assert "hunger_drive" in result.decision_data
    assert "curiosity_drive" in result.decision_data
    assert "prediction" in result.decision_data
    assert "hunger_modulation" in result.decision_data["prediction"]
    assert "curiosity_modulation" in result.decision_data["prediction"]
    assert "counterfactual_combined_scores" in result.decision_data["prediction"]
    assert "counterfactual_combined_scores_without_hunger_prediction" in result.decision_data["prediction"]
    assert "counterfactual_combined_scores_without_curiosity_prediction" in result.decision_data["prediction"]
    assert "counterfactual_top_action" in result.decision_data["prediction"]
