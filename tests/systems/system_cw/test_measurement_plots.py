from __future__ import annotations

from pathlib import Path

from axis.framework.workspaces.plot_extensions import build_system_measurement_plots
from axis.sdk.measurement_plots import SeriesMeasurementPlotRequest
from axis.systems.system_cw import register


def test_system_cw_measurement_plots_include_experiment_level_artifacts(tmp_path: Path) -> None:
    register()
    request = SeriesMeasurementPlotRequest(
        workspace_path=tmp_path,
        series_id="alpha",
        workspace_type="system_comparison",
        measurements_root=tmp_path / "series" / "alpha" / "measurements",
        series_plots_root=tmp_path / "series" / "alpha" / "measurements" / "plots",
        experiment_plot_roots={
            "exp_01": tmp_path / "series" / "alpha" / "measurements" / "experiment_1" / "plots",
        },
        experiments=(
            {
                "experiment_id": "exp_01",
                "behavior_metrics": {
                    "system_specific_metrics": {
                        "system_cw_prediction": {
                            "feature_prediction_error_mean": 0.21,
                            "hunger_prediction_error_mean": 0.18,
                            "curiosity_prediction_error_mean": 0.15,
                        },
                        "system_cw_traces": {
                            "hunger_confidence_trace_mean": 0.06,
                            "hunger_frustration_trace_mean": 0.03,
                            "curiosity_confidence_trace_mean": 0.04,
                            "curiosity_frustration_trace_mean": 0.02,
                            "hunger_trace_balance": 0.03,
                            "curiosity_trace_balance": 0.02,
                            "trace_divergence_mean": 0.05,
                        },
                        "system_cw_modulation": {
                            "hunger_modulation_strength": 0.11,
                            "curiosity_modulation_strength": 0.16,
                        },
                        "system_cw_arbitration": {
                            "mean_hunger_weight": 0.44,
                            "mean_curiosity_weight": 0.56,
                        },
                        "system_cw_curiosity": {
                            "mean_composite_novelty": 0.52,
                        },
                        "system_cw_world_model": {
                            "world_model_unique_cells": 96.0,
                        },
                        "system_cw_prediction_impact": {
                            "behavioral_prediction_impact_rate": 0.12,
                            "prediction_changed_top_action_rate": 0.13,
                            "counterfactual_hunger_modulation_impact": 0.04,
                            "counterfactual_curiosity_modulation_impact": 0.05,
                        },
                    },
                },
                "comparison_summary": {
                    "candidate_survival_rate": 0.50,
                    "reference_survival_rate": 0.46,
                },
            },
        ),
    )

    artifacts = build_system_measurement_plots("system_cw", request)
    experiment_artifacts = [a for a in artifacts if a.level == "experiment"]
    assert experiment_artifacts
    assert any(a.plot_group == "experiment_system_specific" for a in experiment_artifacts)
    assert any("system-specific/system_cw" in a.relative_output_path for a in experiment_artifacts)
    for artifact in experiment_artifacts:
        assert (tmp_path / artifact.relative_output_path).is_file()
