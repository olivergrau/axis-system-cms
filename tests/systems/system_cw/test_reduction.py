from __future__ import annotations

import numpy as np
import pytest

from axis.sdk.position import Position
from axis.sdk.world_types import ActionOutcome
from axis.systems.construction_kit.observation.types import CellObservation, Observation
from axis.systems.system_aw.config import SystemAWConfig
from axis.systems.system_aw.system import SystemAW
from axis.systems.system_cw.config import SystemCWConfig
from axis.systems.system_cw.system import SystemCW
from axis.world.grid_2d.model import Cell, CellType, World
from tests.builders.system_aw_config_builder import SystemAWConfigBuilder
from tests.builders.system_cw_config_builder import SystemCWConfigBuilder


def _make_resource_grid(width: int, height: int, value: float = 0.3) -> list[list[Cell]]:
    return [
        [Cell(cell_type=CellType.RESOURCE, resource_value=value) for _ in range(width)]
        for _ in range(height)
    ]


def _make_observation(resource: float = 0.3) -> Observation:
    cell = CellObservation(traversability=1.0, resource=resource)
    return Observation(current=cell, up=cell, down=cell, left=cell, right=cell)


def test_neutral_prediction_reduces_to_aw_for_action_selection() -> None:
    cw_cfg = SystemCWConfig(**(
        SystemCWConfigBuilder()
        .with_hunger_prediction(
            positive_sensitivity=0.0,
            negative_sensitivity=0.0,
            prediction_bias_scale=0.0,
        )
        .with_curiosity_prediction(
            positive_sensitivity=0.0,
            negative_sensitivity=0.0,
            prediction_bias_scale=0.0,
        )
        .with_selection_mode("argmax")
        .build()
    ))
    aw_cfg = SystemAWConfig(**(
        SystemAWConfigBuilder()
        .with_selection_mode("argmax")
        .build()
    ))
    cw = SystemCW(cw_cfg)
    aw = SystemAW(aw_cfg)
    world = World(_make_resource_grid(5, 5, 0.5), Position(x=2, y=2))
    cw_result = cw.decide(world, cw.initialize_state(), np.random.default_rng(42))
    aw_result = aw.decide(world, aw.initialize_state(), np.random.default_rng(42))
    assert cw_result.action == aw_result.action


def test_neutral_prediction_matches_aw_energy_trajectory() -> None:
    cw_cfg = SystemCWConfig(**(
        SystemCWConfigBuilder()
        .with_hunger_prediction(
            positive_sensitivity=0.0,
            negative_sensitivity=0.0,
            prediction_bias_scale=0.0,
        )
        .with_curiosity_prediction(
            positive_sensitivity=0.0,
            negative_sensitivity=0.0,
            prediction_bias_scale=0.0,
        )
        .with_selection_mode("argmax")
        .build()
    ))
    aw_cfg = SystemAWConfig(**(
        SystemAWConfigBuilder()
        .with_selection_mode("argmax")
        .build()
    ))
    cw = SystemCW(cw_cfg)
    aw = SystemAW(aw_cfg)
    cw_state = cw.initialize_state()
    aw_state = aw.initialize_state()
    world = World(_make_resource_grid(5, 5, 0.3), Position(x=2, y=2))

    for step in range(5):
        cw_result = cw.decide(world, cw_state, np.random.default_rng(100 + step))
        aw_result = aw.decide(world, aw_state, np.random.default_rng(100 + step))
        assert cw_result.action == aw_result.action
        action = cw_result.action
        moved = action in {"up", "down", "left", "right"}
        outcome = ActionOutcome(action=action, moved=moved, new_position=Position(x=2, y=2))
        obs = _make_observation(0.3)
        cw_state = cw.transition(cw_state, outcome, obs).new_state
        aw_state = aw.transition(aw_state, outcome, obs).new_state

    assert cw_state.energy == pytest.approx(aw_state.energy)
