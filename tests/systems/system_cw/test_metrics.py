from __future__ import annotations

import pytest

from axis.framework.metrics.types import MetricSummaryStats, StandardBehaviorMetrics
from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import CellView

import axis.systems.system_cw.metrics as system_cw_metrics


def _snapshot() -> WorldSnapshot:
    cell = CellView(cell_type="empty", resource_value=0.0)
    return WorldSnapshot(
        grid=((cell,),),
        agent_position=Position(x=0, y=0),
        width=1,
        height=1,
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


def test_system_cw_metrics_extract_dual_channels() -> None:
    snap = _snapshot()
    step = BaseStepTrace(
        timestep=0,
        action="up",
        world_before=snap,
        world_after=snap,
        agent_position_before=Position(x=0, y=0),
        agent_position_after=Position(x=0, y=1),
        vitality_before=1.0,
        vitality_after=0.9,
        terminated=False,
        system_data={
            "decision_data": {
                "hunger_drive": {"activation": 0.8},
                "curiosity_drive": {
                    "activation": 0.5,
                    "spatial_novelty": (0.6, 0.4, 0.2, 0.8),
                    "sensory_novelty": (0.1, 0.2, 0.3, 0.4),
                    "composite_novelty": (0.35, 0.30, 0.25, 0.60),
                },
                "arbitration": {"hunger_weight": 0.4, "curiosity_weight": 0.6},
                "prediction": {
                    "hunger_modulation": {
                        "raw_scores": (1.0, 0.0, 0.0, 0.0, 0.0, -0.1),
                        "final_scores": (0.8, 0.0, 0.0, 0.0, 0.0, -0.08),
                        "reliability_factors": (0.8, 1.0, 1.0, 1.0, 1.0, 1.2),
                    },
                    "curiosity_modulation": {
                        "raw_scores": (0.4, 0.0, 0.0, 0.0, -0.3, -0.3),
                        "final_scores": (0.5, 0.0, 0.0, 0.0, -0.3, -0.3),
                        "reliability_factors": (1.25, 1.0, 1.0, 1.0, 1.0, 1.0),
                    },
                    "counterfactual_combined_scores": (0.42, 0.05, 0.01, 0.0, -0.18, -0.19),
                    "counterfactual_combined_scores_without_hunger_prediction": (
                        0.42, 0.05, 0.01, 0.0, -0.18, -0.19
                    ),
                    "counterfactual_combined_scores_without_curiosity_prediction": (
                        0.32, 0.05, 0.01, 0.0, -0.18, -0.19
                    ),
                },
                "combined_scores": (0.62, 0.05, 0.01, 0.0, -0.18, -0.19),
            },
            "trace_data": {
                "visit_count_at_current": 3,
                "visit_counts_map": [[[0, 0], 2], [[0, 1], 1]],
                "prediction": {
                    "feature_error_positive": 0.15,
                    "feature_error_negative": 0.05,
                    "hunger": {
                        "error_positive": 0.2,
                        "error_negative": 0.1,
                        "actual": 0.3,
                        "predicted": 0.2,
                        "confidence_value": 0.4,
                        "frustration_value": 0.2,
                    },
                    "curiosity": {
                        "error_positive": 0.3,
                        "error_negative": 0.0,
                        "actual": 0.21,
                        "predicted": 0.0,
                        "novelty_weight": 0.7,
                        "used_nonmove_penalty_rule": False,
                        "is_movement_action": True,
                        "confidence_value": 0.5,
                        "frustration_value": 0.1,
                    },
                },
            },
        },
        world_data={},
    )
    trace = BaseEpisodeTrace(
        system_type="system_cw",
        steps=(step,),
        total_steps=1,
        termination_reason="max_steps_reached",
        final_vitality=0.9,
        final_position=Position(x=0, y=1),
        world_type="grid_2d",
        world_config={},
    )

    result = system_cw_metrics.system_cw_behavior_metrics((trace,), _standard_metrics())
    prediction = result["system_cw_prediction"]
    modulation = result["system_cw_modulation"]
    traces = result["system_cw_traces"]
    arbitration = result["system_cw_arbitration"]
    curiosity = result["system_cw_curiosity"]
    world_model = result["system_cw_world_model"]
    impact = result["system_cw_prediction_impact"]

    assert prediction["prediction_step_count"] == 1
    assert prediction["feature_prediction_error_mean"] == pytest.approx(0.2)
    assert prediction["hunger_prediction_error_mean"] == pytest.approx(0.3)
    assert prediction["curiosity_prediction_error_mean"] == pytest.approx(0.3)
    assert prediction["hunger_signed_prediction_error"] == pytest.approx(0.1)
    assert prediction["curiosity_signed_prediction_error"] == pytest.approx(0.3)
    assert prediction["mean_novelty_weight"] == pytest.approx(0.7)
    assert prediction["movement_prediction_step_rate"] == pytest.approx(1.0)

    assert modulation["hunger_modulation_strength"] == pytest.approx(0.0366666667)
    assert modulation["curiosity_modulation_strength"] == pytest.approx(0.0166666667)
    assert modulation["mean_modulation_divergence"] == pytest.approx(0.02)
    assert modulation["hunger_reinforcement_rate"] == pytest.approx(1 / 6)
    assert modulation["hunger_suppression_rate"] == pytest.approx(1 / 6)
    assert modulation["curiosity_reinforcement_rate"] == pytest.approx(1 / 6)
    assert modulation["curiosity_suppression_rate"] == pytest.approx(0.0)

    assert traces["hunger_confidence_trace_mean"] == pytest.approx(0.4)
    assert traces["hunger_frustration_trace_mean"] == pytest.approx(0.2)
    assert traces["curiosity_confidence_trace_mean"] == pytest.approx(0.5)
    assert traces["curiosity_frustration_trace_mean"] == pytest.approx(0.1)
    assert traces["hunger_trace_balance"] == pytest.approx(0.2)
    assert traces["curiosity_trace_balance"] == pytest.approx(0.4)
    assert traces["trace_divergence_mean"] == pytest.approx(0.2)
    assert traces["nonzero_hunger_trace_rate"] == pytest.approx(1.0)
    assert traces["nonzero_curiosity_trace_rate"] == pytest.approx(1.0)

    assert arbitration["mean_hunger_weight"] == pytest.approx(0.4)
    assert arbitration["mean_curiosity_weight"] == pytest.approx(0.6)
    assert arbitration["curiosity_dominance_rate"] == pytest.approx(1.0)
    assert arbitration["mean_curiosity_activation"] == pytest.approx(0.5)
    assert arbitration["curiosity_pressure_rate"] == pytest.approx(0.0)
    assert arbitration["prediction_weighted_curiosity_pressure"] == pytest.approx(0.21)
    assert arbitration["prediction_weighted_hunger_pressure"] == pytest.approx(0.32)

    assert curiosity["mean_spatial_novelty"] == pytest.approx(0.5)
    assert curiosity["mean_sensory_novelty"] == pytest.approx(0.25)
    assert curiosity["mean_composite_novelty"] == pytest.approx(0.375)
    assert curiosity["curiosity_led_move_rate"] == pytest.approx(0.0)
    assert curiosity["consume_under_curiosity_pressure_rate"] is None
    assert curiosity["novel_move_yield_mean"] == pytest.approx(0.21)
    assert curiosity["novel_move_success_rate"] == pytest.approx(1.0)

    assert world_model["world_model_unique_cells"] == pytest.approx(2.0)
    assert world_model["mean_visit_count_at_current"] == pytest.approx(3.0)
    assert world_model["world_model_revisit_ratio"] == pytest.approx(1.0 - (2 / 3))

    assert impact["behavioral_prediction_impact_rate"] == pytest.approx(0.0)
    assert impact["prediction_changed_top_action_rate"] == pytest.approx(0.0)
    assert impact["prediction_changed_arbitrated_margin"] == pytest.approx(0.20)
    assert impact["nonmove_curiosity_penalty_rate"] is None
    assert impact["counterfactual_hunger_modulation_impact"] == pytest.approx(0.0)
    assert impact["counterfactual_curiosity_modulation_impact"] == pytest.approx(0.0)


def test_system_cw_extended_prediction_impact_metrics() -> None:
    snap = _snapshot()
    step = BaseStepTrace(
        timestep=0,
        action="stay",
        world_before=snap,
        world_after=snap,
        agent_position_before=Position(x=0, y=0),
        agent_position_after=Position(x=0, y=0),
        vitality_before=1.0,
        vitality_after=0.9,
        terminated=False,
        system_data={
            "decision_data": {
                "hunger_drive": {"activation": 0.2},
                "curiosity_drive": {
                    "activation": 0.9,
                    "spatial_novelty": (0.4, 0.4, 0.4, 0.4),
                    "sensory_novelty": (0.4, 0.4, 0.4, 0.4),
                    "composite_novelty": (0.4, 0.4, 0.4, 0.4),
                },
                "arbitration": {"hunger_weight": 0.2, "curiosity_weight": 0.8},
                "prediction": {
                    "hunger_modulation": {
                        "raw_scores": (0.0, 0.0, 0.0, 0.0, 0.1, -0.1),
                        "final_scores": (0.0, 0.0, 0.0, 0.0, 0.1, -0.1),
                        "reliability_factors": (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
                    },
                    "curiosity_modulation": {
                        "raw_scores": (0.1, 0.1, 0.1, 0.1, -0.3, -0.3),
                        "final_scores": (0.1, 0.1, 0.1, 0.1, -0.05, -0.3),
                        "reliability_factors": (1.0, 1.0, 1.0, 1.0, 0.5, 1.0),
                    },
                    "counterfactual_combined_scores": (0.08, 0.08, 0.08, 0.08, -0.22, -0.26),
                    "counterfactual_combined_scores_without_hunger_prediction": (
                        0.08, 0.08, 0.08, 0.08, -0.02, 0.20
                    ),
                    "counterfactual_combined_scores_without_curiosity_prediction": (
                        0.08, 0.08, 0.08, 0.08, -0.22, -0.26
                    ),
                },
                "combined_scores": (0.08, 0.08, 0.08, 0.08, -0.02, 0.20),
            },
            "trace_data": {
                "visit_count_at_current": 1,
                "visit_counts_map": [[[0, 0], 1]],
                "prediction": {
                    "feature_error_positive": 0.0,
                    "feature_error_negative": 0.0,
                    "hunger": {
                        "error_positive": 0.0,
                        "error_negative": 0.0,
                        "actual": 0.0,
                        "predicted": 0.0,
                        "confidence_value": 0.0,
                        "frustration_value": 0.0,
                    },
                    "curiosity": {
                        "error_positive": 0.0,
                        "error_negative": 0.0,
                        "actual": -0.18,
                        "predicted": -0.18,
                        "novelty_weight": 0.0,
                        "used_nonmove_penalty_rule": True,
                        "is_movement_action": False,
                        "confidence_value": 0.0,
                        "frustration_value": 0.0,
                    },
                },
            },
        },
        world_data={},
    )
    trace = BaseEpisodeTrace(
        system_type="system_cw",
        steps=(step,),
        total_steps=1,
        termination_reason="max_steps_reached",
        final_vitality=0.9,
        final_position=Position(x=0, y=0),
        world_type="grid_2d",
        world_config={},
    )

    result = system_cw_metrics.system_cw_behavior_metrics((trace,), _standard_metrics())
    impact = result["system_cw_prediction_impact"]
    assert impact["behavioral_prediction_impact_rate"] == pytest.approx(1.0)
    assert impact["prediction_changed_top_action_rate"] == pytest.approx(1.0)
    assert impact["prediction_changed_arbitrated_margin"] == pytest.approx(0.12)
    assert impact["nonmove_curiosity_penalty_rate"] == pytest.approx(1.0)
    assert impact["counterfactual_hunger_modulation_impact"] == pytest.approx(0.0)
    assert impact["counterfactual_curiosity_modulation_impact"] == pytest.approx(1.0)
