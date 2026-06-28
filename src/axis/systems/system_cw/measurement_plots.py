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


def _save_experiment_plot(
    request: SeriesMeasurementPlotRequest,
    experiment_id: str,
    filename: str,
    plot_id: str,
    title: str,
    description: str,
):
    output_path = request.experiment_plot_roots[experiment_id] / "system-specific" / "system_cw" / filename
    return output_path, GeneratedPlotArtifact(
        plot_id=plot_id,
        level="experiment",
        plot_group="experiment_system_specific",
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

    for entry in entries:
        exp_id = entry["experiment_id"]
        metric = entry["behavior_metrics"]["system_specific_metrics"]
        comp_summary = entry["comparison_summary"]

        fig, ax = create_figure(figsize=(8, 4.5))
        pred = metric["system_cw_prediction"]
        ax.bar(
            ["feature", "hunger", "curiosity", "top_action_changed"],
            [
                pred["feature_prediction_error_mean"],
                pred["hunger_prediction_error_mean"],
                pred["curiosity_prediction_error_mean"],
                metric["system_cw_prediction_impact"]["prediction_changed_top_action_rate"],
            ],
        )
        ax.tick_params(axis="x", rotation=20)
        ax.set_ylabel("value")
        output_path, artifact = _save_experiment_plot(
            request,
            exp_id,
            "cw-prediction-snapshot.png",
            "cw-prediction-snapshot",
            f"{exp_id} C+W Prediction Snapshot",
            "Per-experiment snapshot of prediction error and top-action change rate.",
        )
        finalize_plot(fig, output_path)
        artifacts.append(artifact)

        fig, ax = create_figure(figsize=(8, 4.5))
        traces = metric["system_cw_traces"]
        modulation = metric["system_cw_modulation"]
        ax.bar(
            [
                "h_conf",
                "h_frust",
                "c_conf",
                "c_frust",
                "h_mod",
                "c_mod",
            ],
            [
                traces["hunger_confidence_trace_mean"],
                traces["hunger_frustration_trace_mean"],
                traces["curiosity_confidence_trace_mean"],
                traces["curiosity_frustration_trace_mean"],
                modulation["hunger_modulation_strength"],
                modulation["curiosity_modulation_strength"],
            ],
        )
        ax.tick_params(axis="x", rotation=20)
        ax.set_ylabel("value")
        output_path, artifact = _save_experiment_plot(
            request,
            exp_id,
            "cw-traces-modulation.png",
            "cw-traces-modulation",
            f"{exp_id} C+W Traces And Modulation",
            "Per-experiment snapshot of confidence/frustration traces and modulation strengths.",
        )
        finalize_plot(fig, output_path)
        artifacts.append(artifact)

        fig, ax = create_figure(figsize=(8, 4.5))
        arbitration = metric["system_cw_arbitration"]
        curiosity = metric["system_cw_curiosity"]
        world_model = metric["system_cw_world_model"]
        ax.bar(
            [
                "hunger_w",
                "curiosity_w",
                "comp_novelty",
                "world_unique",
                "survival_delta",
            ],
            [
                arbitration["mean_hunger_weight"],
                arbitration["mean_curiosity_weight"],
                curiosity["mean_composite_novelty"],
                min(1.0, world_model["world_model_unique_cells"] / 200.0),
                comp_summary["candidate_survival_rate"] - comp_summary["reference_survival_rate"],
            ],
        )
        ax.axhline(0.0, color="gray", linestyle="--", linewidth=1)
        ax.tick_params(axis="x", rotation=20)
        ax.set_ylabel("value")
        output_path, artifact = _save_experiment_plot(
            request,
            exp_id,
            "cw-arbitration-curiosity-outcome.png",
            "cw-arbitration-curiosity-outcome",
            f"{exp_id} C+W Arbitration Curiosity Outcome",
            "Per-experiment snapshot of arbitration, curiosity, world-model coverage, and survival delta.",
        )
        finalize_plot(fig, output_path)
        artifacts.append(artifact)

    return artifacts
