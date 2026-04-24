"""Tests for the System C behavioral metric extension."""

from __future__ import annotations

import pytest

from axis.framework.metrics.types import MetricSummaryStats, StandardBehaviorMetrics
from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import CellView

import axis.systems.system_c.metrics as system_c_metrics


def _snapshot() -> WorldSnapshot:
    cell = CellView(cell_type="empty", resource_value=0.0)
    grid = ((cell,),)
    return WorldSnapshot(
        grid=grid,
        agent_position=Position(x=0, y=0),
        width=1,
        height=1,
    )


def _step() -> BaseStepTrace:
    snap = _snapshot()
    return BaseStepTrace(
        timestep=0,
        action="up",
        world_before=snap,
        world_after=snap,
        agent_position_before=Position(x=0, y=0),
        agent_position_after=Position(x=0, y=0),
        vitality_before=1.0,
        vitality_after=0.9,
        terminated=False,
        system_data={
            "decision_data": {
                "drive": {
                    "action_contributions": (1.0, 0.5, 0.0, 0.0, 0.0, 0.0),
                },
                "prediction": {
                    "modulated_scores": (0.5, 0.25, 0.0, 0.0, 0.0, 0.0),
                },
            },
            "trace_data": {
                "prediction": {
                    "error_positive": 0.2,
                    "error_negative": 0.1,
                    "confidence_value": 0.4,
                    "frustration_value": 0.3,
                },
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


class TestSystemCBehaviorMetrics:
    def test_system_c_behavior_metrics(self) -> None:
        trace = BaseEpisodeTrace(
            system_type="system_c",
            steps=(_step(),),
            total_steps=1,
            termination_reason="max_steps_reached",
            final_vitality=0.9,
            final_position=Position(x=0, y=0),
            world_type="grid_2d",
            world_config={},
        )

        result = system_c_metrics.system_c_behavior_metrics(
            (trace,),
            _standard_metrics(),
        )
        metrics = result["system_c_prediction"]
        assert metrics["mean_prediction_error"] == pytest.approx(0.3)
        assert metrics["signed_prediction_error"] == pytest.approx(0.1)
        assert metrics["confidence_trace_mean"] == pytest.approx(0.4)
        assert metrics["frustration_trace_mean"] == pytest.approx(0.3)
        assert metrics["prediction_modulation_strength"] == pytest.approx(0.125)
        assert metrics["prediction_step_count"] == 1
