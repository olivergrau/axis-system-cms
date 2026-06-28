from __future__ import annotations

from pathlib import Path

from axis.framework.workspaces.plot_extensions import build_system_measurement_plots
from axis.sdk.measurement_plots import SeriesMeasurementPlotRequest
from axis.systems.system_c import register


def test_system_c_measurement_plots_include_experiment_level_artifacts(tmp_path: Path) -> None:
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
                        "system_c_prediction": {
                            "mean_prediction_error": 0.22,
                            "signed_prediction_error": -0.03,
                            "confidence_trace_mean": 0.14,
                            "frustration_trace_mean": 0.09,
                            "prediction_modulation_strength": 0.18,
                        },
                    },
                },
                "comparison_summary": {
                    "candidate_survival_rate": 0.42,
                    "reference_survival_rate": 0.38,
                    "total_steps_delta": {"mean": 17.0},
                    "final_vitality_delta": {"mean": 0.04},
                },
            },
        ),
    )

    artifacts = build_system_measurement_plots("system_c", request)
    experiment_artifacts = [a for a in artifacts if a.level == "experiment"]
    assert experiment_artifacts
    assert any(a.plot_group == "experiment_system_specific" for a in experiment_artifacts)
    assert any("system-specific/system_c" in a.relative_output_path for a in experiment_artifacts)
    for artifact in experiment_artifacts:
        assert (tmp_path / artifact.relative_output_path).is_file()
