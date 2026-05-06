"""System C+W measurement plot extension."""

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
    output_path = request.series_plots_root / "system-specific" / "system_cw" / filename
    return output_path, GeneratedPlotArtifact(
        plot_id=plot_id,
        level="series",
        plot_group="system_specific",
        relative_output_path=str(output_path.relative_to(request.workspace_path)),
        title=title,
        description=description,
        system_type="system_cw",
        producer_kind="system_extension",
        producer_system_type="system_cw",
    )


@register_measurement_plot_extension("system_cw")
def system_cw_measurement_plots(
    request: SeriesMeasurementPlotRequest,
) -> list[GeneratedPlotArtifact]:
    entries = list(request.experiments)
    labels = [entry["experiment_id"] for entry in entries]
    metrics = [entry["behavior_metrics"]["system_specific_metrics"] for entry in entries]
    comp = [entry["comparison_summary"] for entry in entries]
    artifacts: list[GeneratedPlotArtifact] = []

    fig, ax = create_figure(figsize=(7, 5))
    ax.scatter(
        [m["system_cw_prediction_impact"]["behavioral_prediction_impact_rate"] for m in metrics],
        [c["candidate_survival_rate"] - c["reference_survival_rate"] for c in comp],
    )
    for label, m, c in zip(labels, metrics, comp):
        ax.annotate(
            label,
            (
                m["system_cw_prediction_impact"]["behavioral_prediction_impact_rate"],
                c["candidate_survival_rate"] - c["reference_survival_rate"],
            ),
            fontsize=8,
            xytext=(4, 4),
            textcoords="offset points",
        )
    ax.set_xlabel("behavioral prediction impact rate")
    ax.set_ylabel("survival delta")
    output_path, artifact = _save_series_plot(
        request,
        "prediction-impact-vs-survival.png",
        "prediction-impact-vs-survival",
        "Prediction Impact vs Survival",
        "Relates behavioral prediction impact to survival difference across experiments.",
    )
    finalize_plot(fig, output_path)
    artifacts.append(artifact)

    fig, ax = create_figure(figsize=(7, 5))
    ax.scatter(
        [m["system_cw_modulation"]["hunger_modulation_strength"] for m in metrics],
        [m["system_cw_modulation"]["curiosity_modulation_strength"] for m in metrics],
        c=[c["candidate_survival_rate"] - c["reference_survival_rate"] for c in comp],
    )
    for label, m in zip(labels, metrics):
        ax.annotate(label, (m["system_cw_modulation"]["hunger_modulation_strength"], m["system_cw_modulation"]["curiosity_modulation_strength"]), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("hunger modulation strength")
    ax.set_ylabel("curiosity modulation strength")
    output_path, artifact = _save_series_plot(
        request,
        "modulation-strength-vs-performance.png",
        "modulation-strength-vs-performance",
        "Modulation Strengths vs Performance",
        "Shows hunger and curiosity modulation strengths against performance structure.",
    )
    finalize_plot(fig, output_path)
    artifacts.append(artifact)

    fig, ax = create_figure(figsize=(10, 5))
    ax.plot(labels, [m["system_cw_prediction"]["feature_prediction_error_mean"] for m in metrics], marker="o", label="feature")
    ax.plot(labels, [m["system_cw_prediction"]["hunger_prediction_error_mean"] for m in metrics], marker="o", label="hunger")
    ax.plot(labels, [m["system_cw_prediction"]["curiosity_prediction_error_mean"] for m in metrics], marker="o", label="curiosity")
    ax.tick_params(axis="x", rotation=30)
    ax.legend()
    output_path, artifact = _save_series_plot(
        request,
        "prediction-error-profile.png",
        "prediction-error-profile",
        "Prediction Error Profile",
        "Tracks feature, hunger, and curiosity prediction error across the series.",
    )
    finalize_plot(fig, output_path)
    artifacts.append(artifact)

    fig, ax = create_figure(figsize=(7, 5))
    ax.scatter(
        [m["system_cw_arbitration"]["mean_hunger_weight"] for m in metrics],
        [m["system_cw_arbitration"]["mean_curiosity_weight"] for m in metrics],
        c=[c["candidate_survival_rate"] - c["reference_survival_rate"] for c in comp],
    )
    for label, m in zip(labels, metrics):
        ax.annotate(label, (m["system_cw_arbitration"]["mean_hunger_weight"], m["system_cw_arbitration"]["mean_curiosity_weight"]), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("mean hunger weight")
    ax.set_ylabel("mean curiosity weight")
    output_path, artifact = _save_series_plot(
        request,
        "curiosity-hunger-weight-plane.png",
        "curiosity-hunger-weight-plane",
        "Curiosity-Hunger Weight Plane",
        "Shows arbitration weight structure between hunger and curiosity.",
    )
    finalize_plot(fig, output_path)
    artifacts.append(artifact)

    fig, ax = create_figure(figsize=(10, 5))
    ax.plot(labels, [m["system_cw_traces"]["hunger_trace_balance"] for m in metrics], marker="o", label="hunger")
    ax.plot(labels, [m["system_cw_traces"]["curiosity_trace_balance"] for m in metrics], marker="o", label="curiosity")
    ax.plot(labels, [m["system_cw_traces"]["trace_divergence_mean"] for m in metrics], marker="o", label="divergence")
    ax.tick_params(axis="x", rotation=30)
    ax.legend()
    output_path, artifact = _save_series_plot(
        request,
        "cw-trace-balance-profile.png",
        "cw-trace-balance-profile",
        "C+W Trace Balance Profile",
        "Tracks trace balance and divergence signals across experiments.",
    )
    finalize_plot(fig, output_path)
    artifacts.append(artifact)

    fig, ax = create_figure(figsize=(10, 5))
    ax.plot(labels, [m["system_cw_prediction_impact"]["prediction_changed_top_action_rate"] for m in metrics], marker="o", label="changed top action")
    ax.plot(labels, [m["system_cw_prediction_impact"]["counterfactual_hunger_modulation_impact"] for m in metrics], marker="o", label="hunger cf impact")
    ax.plot(labels, [m["system_cw_prediction_impact"]["counterfactual_curiosity_modulation_impact"] for m in metrics], marker="o", label="curiosity cf impact")
    ax.tick_params(axis="x", rotation=30)
    ax.legend()
    output_path, artifact = _save_series_plot(
        request,
        "cw-comparison-deltas.png",
        "cw-comparison-deltas",
        "C+W Comparison Deltas",
        "Shows how often prediction changes the selected action and modulation counterfactuals matter.",
    )
    finalize_plot(fig, output_path)
    artifacts.append(artifact)

    return artifacts
