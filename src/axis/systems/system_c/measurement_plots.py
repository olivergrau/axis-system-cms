"""System C measurement plot extension."""

from __future__ import annotations

from axis.framework.workspaces.plot_extensions import register_measurement_plot_extension
from axis.framework.workspaces.plotting import create_figure, finalize_plot
from axis.sdk.measurement_plots import GeneratedPlotArtifact, SeriesMeasurementPlotRequest


def _save_series_plot(
    request: SeriesMeasurementPlotRequest,
    filename: str,
    plot_id: str,
    title: str,
    description: str,
):
    output_path = request.series_plots_root / "system-specific" / "system_c" / filename
    return output_path, GeneratedPlotArtifact(
        plot_id=plot_id,
        level="series",
        plot_group="system_specific",
        relative_output_path=str(output_path.relative_to(request.workspace_path)),
        title=title,
        description=description,
        system_type="system_c",
        producer_kind="system_extension",
        producer_system_type="system_c",
    )


def _save_experiment_plot(
    request: SeriesMeasurementPlotRequest,
    experiment_id: str,
    filename: str,
    plot_id: str,
    title: str,
    description: str,
):
    output_path = request.experiment_plot_roots[experiment_id] / "system-specific" / "system_c" / filename
    return output_path, GeneratedPlotArtifact(
        plot_id=plot_id,
        level="experiment",
        plot_group="experiment_system_specific",
        relative_output_path=str(output_path.relative_to(request.workspace_path)),
        title=title,
        description=description,
        system_type="system_c",
        producer_kind="system_extension",
        producer_system_type="system_c",
    )


@register_measurement_plot_extension("system_c")
def system_c_measurement_plots(
    request: SeriesMeasurementPlotRequest,
) -> list[GeneratedPlotArtifact]:
    entries = list(request.experiments)
    labels = [entry["experiment_id"] for entry in entries]
    metrics = [entry["behavior_metrics"]["system_specific_metrics"]["system_c_prediction"] for entry in entries]
    comp = [
        entry["comparison_summary"]
        for entry in entries
    ]
    artifacts: list[GeneratedPlotArtifact] = []

    fig, ax = create_figure(figsize=(10, 5))
    ax.plot(labels, [m["mean_prediction_error"] for m in metrics], marker="o", label="abs error")
    ax.plot(labels, [m["signed_prediction_error"] for m in metrics], marker="o", label="signed error")
    ax.tick_params(axis="x", rotation=30)
    ax.legend()
    output_path, artifact = _save_series_plot(
        request,
        "c-prediction-error-profile.png",
        "c-prediction-error-profile",
        "System C Prediction Error Profile",
        "Tracks absolute and signed prediction error across the series.",
    )
    finalize_plot(fig, output_path)
    artifacts.append(artifact)

    fig, ax = create_figure(figsize=(7, 5))
    ax.scatter(
        [m["confidence_trace_mean"] for m in metrics],
        [m["frustration_trace_mean"] for m in metrics],
    )
    for label, m in zip(labels, metrics):
        ax.annotate(label, (m["confidence_trace_mean"], m["frustration_trace_mean"]), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("confidence trace mean")
    ax.set_ylabel("frustration trace mean")
    output_path, artifact = _save_series_plot(
        request,
        "c-trace-balance.png",
        "c-trace-balance",
        "System C Trace Balance",
        "Shows the balance between confidence and frustration traces.",
    )
    finalize_plot(fig, output_path)
    artifacts.append(artifact)

    fig, ax = create_figure(figsize=(7, 5))
    ax.scatter(
        [m["prediction_modulation_strength"] for m in metrics],
        [
            c["candidate_survival_rate"] - c["reference_survival_rate"]
            for c in comp
        ],
    )
    for label, m, c in zip(labels, metrics, comp):
        ax.annotate(label, (m["prediction_modulation_strength"], c["candidate_survival_rate"] - c["reference_survival_rate"]), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("prediction modulation strength")
    ax.set_ylabel("survival delta")
    output_path, artifact = _save_series_plot(
        request,
        "c-comparison-impact.png",
        "c-comparison-impact",
        "System C Comparison Impact",
        "Relates prediction modulation strength to survival difference.",
    )
    finalize_plot(fig, output_path)
    artifacts.append(artifact)

    for entry in entries:
        exp_id = entry["experiment_id"]
        metric = entry["behavior_metrics"]["system_specific_metrics"]["system_c_prediction"]
        comp_summary = entry["comparison_summary"]

        fig, ax = create_figure(figsize=(8, 4.5))
        ax.bar(
            [
                "abs_error",
                "signed_error",
                "confidence",
                "frustration",
                "mod_strength",
            ],
            [
                metric["mean_prediction_error"],
                metric["signed_prediction_error"],
                metric["confidence_trace_mean"],
                metric["frustration_trace_mean"],
                metric["prediction_modulation_strength"],
            ],
        )
        ax.tick_params(axis="x", rotation=20)
        ax.set_ylabel("value")
        output_path, artifact = _save_experiment_plot(
            request,
            exp_id,
            "c-prediction-snapshot.png",
            "c-prediction-snapshot",
            f"{exp_id} System C Prediction Snapshot",
            "Per-experiment snapshot of prediction error, traces, and modulation strength.",
        )
        finalize_plot(fig, output_path)
        artifacts.append(artifact)

        fig, ax = create_figure(figsize=(8, 4.5))
        ax.bar(
            ["survival_delta", "steps_delta", "vitality_delta"],
            [
                comp_summary["candidate_survival_rate"] - comp_summary["reference_survival_rate"],
                comp_summary["total_steps_delta"]["mean"],
                comp_summary["final_vitality_delta"]["mean"],
            ],
        )
        ax.axhline(0.0, color="gray", linestyle="--", linewidth=1)
        ax.tick_params(axis="x", rotation=20)
        ax.set_ylabel("delta")
        output_path, artifact = _save_experiment_plot(
            request,
            exp_id,
            "c-outcome-deltas.png",
            "c-outcome-deltas",
            f"{exp_id} System C Outcome Deltas",
            "Per-experiment comparison deltas associated with prediction behavior.",
        )
        finalize_plot(fig, output_path)
        artifacts.append(artifact)

    return artifacts
