"""Tests for the System A+W behavioral metric extension."""

from __future__ import annotations

import pytest

from axis.framework.metrics.types import MetricSummaryStats, StandardBehaviorMetrics
from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import CellView

import axis.systems.system_aw.metrics as system_aw_metrics


def _snapshot() -> WorldSnapshot:
    cell = CellView(cell_type="empty", resource_value=0.0)
    grid = ((cell,),)
    return WorldSnapshot(
        grid=grid,
        agent_position=Position(x=0, y=0),
        width=1,
        height=1,
    )


def _step(
    *,
    timestep: int,
    action: str,
    hunger_activation: float,
    hunger_weight: float,
    curiosity_weight: float,
    curiosity_activation: float,
    spatial_novelty: tuple[float, float, float, float],
    sensory_novelty: tuple[float, float, float, float],
    composite_novelty: tuple[float, float, float, float],
    visit_count_at_current: int,
    visit_counts_map: list[list[object]],
) -> BaseStepTrace:
    snap = _snapshot()
    return BaseStepTrace(
        timestep=timestep,
        action=action,
        world_before=snap,
        world_after=snap,
        agent_position_before=Position(x=0, y=0),
        agent_position_after=Position(x=0, y=0),
        vitality_before=1.0,
        vitality_after=0.9,
        terminated=False,
        system_data={
            "decision_data": {
                "hunger_drive": {
                    "activation": hunger_activation,
                },
                "curiosity_drive": {
                    "activation": curiosity_activation,
                    "spatial_novelty": spatial_novelty,
                    "sensory_novelty": sensory_novelty,
                    "composite_novelty": composite_novelty,
                },
                "arbitration": {
                    "hunger_weight": hunger_weight,
                    "curiosity_weight": curiosity_weight,
                },
            },
            "trace_data": {
                "visit_count_at_current": visit_count_at_current,
                "visit_counts_map": visit_counts_map,
            },
        },
        world_data={},
    )


def _standard_metrics() -> StandardBehaviorMetrics:
    stats = MetricSummaryStats(mean=1.0, std=0.0, min=1.0, max=1.0, n=1)
    return StandardBehaviorMetrics(
        mean_steps=1.0,
        death_rate=0.0,
        mean_final_vitality=1.0,
        resource_gain_per_step=stats,
        net_energy_efficiency=stats,
        successful_consume_rate=stats,
        consume_on_empty_rate=stats,
        failed_movement_rate=stats,
        action_entropy=stats,
        policy_sharpness=stats,
        action_inertia=stats,
        unique_cells_visited=stats,
        coverage_efficiency=stats,
        revisit_rate=stats,
    )


class TestSystemAWBehaviorMetrics:
    def test_system_aw_behavior_metrics(self) -> None:
        trace = BaseEpisodeTrace(
            system_type="system_aw",
            steps=(
                _step(
                    timestep=0,
                    action="up",
                    hunger_activation=0.4,
                    hunger_weight=0.3,
                    curiosity_weight=0.6,
                    curiosity_activation=0.8,
                    spatial_novelty=(1.0, 0.5, 0.5, 0.0),
                    sensory_novelty=(0.2, 0.2, 0.1, 0.1),
                    composite_novelty=(0.6, 0.35, 0.3, 0.05),
                    visit_count_at_current=2,
                    visit_counts_map=[[[0, 0], 1], [[0, 1], 2], [[1, 1], 1]],
                ),
                _step(
                    timestep=1,
                    action="consume",
                    hunger_activation=0.6,
                    hunger_weight=0.8,
                    curiosity_weight=0.2,
                    curiosity_activation=0.4,
                    spatial_novelty=(0.5, 0.5, 0.5, 0.5),
                    sensory_novelty=(0.0, 0.1, 0.0, 0.1),
                    composite_novelty=(0.25, 0.3, 0.25, 0.3),
                    visit_count_at_current=3,
                    visit_counts_map=[[[0, 0], 1], [[0, 1], 2], [[1, 1], 1]],
                ),
            ),
            total_steps=2,
            termination_reason="max_steps_reached",
            final_vitality=0.9,
            final_position=Position(x=0, y=0),
            world_type="grid_2d",
            world_config={},
        )

        result = system_aw_metrics.system_aw_behavior_metrics(
            (trace,),
            _standard_metrics(),
        )

        arb = result["system_aw_arbitration"]
        assert arb["curiosity_dominance_rate"] == pytest.approx(0.5)
        assert arb["mean_curiosity_weight"] == pytest.approx(0.4)
        assert arb["mean_hunger_weight"] == pytest.approx(0.55)
        assert arb["arbitrated_step_count"] == 2

        curiosity = result["system_aw_curiosity"]
        assert curiosity["mean_curiosity_activation"] == pytest.approx(0.6)
        assert curiosity["mean_spatial_novelty"] == pytest.approx(0.5)
        assert curiosity["mean_sensory_novelty"] == pytest.approx(0.1)
        assert curiosity["mean_composite_novelty"] == pytest.approx(0.3)
        assert curiosity["curiosity_pressure_rate"] == pytest.approx(0.5)

        behavior = result["system_aw_behavior"]
        assert behavior["curiosity_led_move_rate"] == pytest.approx(0.5)
        assert behavior["consume_under_curiosity_pressure_rate"] == pytest.approx(0.0)
        assert behavior["movement_step_rate"] == pytest.approx(0.5)
        assert behavior["consume_step_rate"] == pytest.approx(0.5)

        world_model = result["system_aw_world_model"]
        assert world_model["world_model_unique_cells"] == pytest.approx(3.0)
        assert world_model["mean_visit_count_at_current"] == pytest.approx(2.5)
        assert world_model["world_model_revisit_ratio"] == pytest.approx(0.25)
