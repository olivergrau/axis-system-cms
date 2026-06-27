from __future__ import annotations

from pathlib import Path

from axis.framework.workspaces.plot_extensions import build_system_measurement_plots
from axis.sdk.measurement_plots import SeriesMeasurementPlotRequest
from axis.systems.system_aw import register


def test_system_aw_measurement_plots_include_experiment_level_artifacts(tmp_path: Path) -> None:
    register()
    request = SeriesMeasurementPlotRequest(
        workspace_path=tmp_path,
        series_id="alpha",
        workspace_type="single_system",
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
                        "system_aw_arbitration": {
                            "mean_hunger_weight": 0.3,
                            "mean_curiosity_weight": 0.7,
                            "curiosity_dominance_rate": 0.6,
                            "arbitrated_step_count": 100,
                        },
                        "system_aw_curiosity": {
                            "mean_curiosity_activation": 0.55,
                            "mean_spatial_novelty": 0.61,
                            "mean_sensory_novelty": 0.42,
                            "mean_composite_novelty": 0.53,
                            "curiosity_pressure_rate": 0.4,
                        },
                        "system_aw_behavior": {
                            "curiosity_led_move_rate": 0.48,
                            "consume_under_curiosity_pressure_rate": 0.11,
                            "movement_step_rate": 0.7,
                            "consume_step_rate": 0.08,
                        },
                        "system_aw_world_model": {
                            "world_model_unique_cells": 88.0,
                            "mean_visit_count_at_current": 1.6,
                            "world_model_revisit_ratio": 0.31,
                        },
                    },
                },
            },
        ),
    )

    artifacts = build_system_measurement_plots("system_aw", request)
    experiment_artifacts = [a for a in artifacts if a.level == "experiment"]
    assert experiment_artifacts
    assert any(a.plot_group == "experiment_system_specific" for a in experiment_artifacts)
    assert any("system-specific/system_aw" in a.relative_output_path for a in experiment_artifacts)
    for artifact in experiment_artifacts:
        assert (tmp_path / artifact.relative_output_path).is_file()


def test_system_aw_measurement_plots_tolerate_none_values(tmp_path: Path) -> None:
    register()
    request = SeriesMeasurementPlotRequest(
        workspace_path=tmp_path,
        series_id="alpha",
        workspace_type="single_system",
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
                        "system_aw_arbitration": {
                            "mean_hunger_weight": None,
                            "mean_curiosity_weight": 0.7,
                            "curiosity_dominance_rate": 0.6,
                            "arbitrated_step_count": 100,
                        },
                        "system_aw_curiosity": {
                            "mean_curiosity_activation": 0.55,
                            "mean_spatial_novelty": 0.61,
                            "mean_sensory_novelty": None,
                            "mean_composite_novelty": 0.53,
                            "curiosity_pressure_rate": 0.4,
                        },
                        "system_aw_behavior": {
                            "curiosity_led_move_rate": 0.48,
                            "consume_under_curiosity_pressure_rate": None,
                            "movement_step_rate": 0.7,
                            "consume_step_rate": 0.08,
                        },
                        "system_aw_world_model": {
                            "world_model_unique_cells": 88.0,
                            "mean_visit_count_at_current": 1.6,
                            "world_model_revisit_ratio": None,
                        },
                    },
                },
            },
        ),
    )

    artifacts = build_system_measurement_plots("system_aw", request)
    assert artifacts
    for artifact in artifacts:
        assert (tmp_path / artifact.relative_output_path).is_file()
