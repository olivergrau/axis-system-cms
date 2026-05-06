"""System A+W measurement plot extension."""

from __future__ import annotations

from pathlib import Path

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
    output_path = request.series_plots_root / "system-specific" / "system_aw" / filename
    return output_path, GeneratedPlotArtifact(
        plot_id=plot_id,
        level="series",
        plot_group="system_specific",
        relative_output_path=str(output_path.relative_to(request.workspace_path)),
        title=title,
        description=description,
        system_type="system_aw",
        producer_kind="system_extension",
        producer_system_type="system_aw",
    )


@register_measurement_plot_extension("system_aw")
def system_aw_measurement_plots(
    request: SeriesMeasurementPlotRequest,
) -> list[GeneratedPlotArtifact]:
    entries = list(request.experiments)
    labels = [entry["experiment_id"] for entry in entries]
    metrics = [entry["behavior_metrics"]["system_specific_metrics"] for entry in entries]
    artifacts: list[GeneratedPlotArtifact] = []

    fig, ax = create_figure(figsize=(10, 5))
    ax.plot(labels, [m["system_aw_curiosity"]["mean_spatial_novelty"] for m in metrics], marker="o", label="spatial")
    ax.plot(labels, [m["system_aw_curiosity"]["mean_sensory_novelty"] for m in metrics], marker="o", label="sensory")
    ax.plot(labels, [m["system_aw_curiosity"]["mean_composite_novelty"] for m in metrics], marker="o", label="composite")
    ax.tick_params(axis="x", rotation=30)
    ax.legend()
    output_path, artifact = _save_series_plot(
        request,
        "aw-curiosity-profile.png",
        "aw-curiosity-profile",
        "A+W Curiosity Profile",
        "Compares spatial, sensory, and composite novelty signals across the series.",
    )
    finalize_plot(fig, output_path)
    artifacts.append(artifact)

    fig, ax = create_figure(figsize=(7, 5))
    ax.scatter(
        [m["system_aw_arbitration"]["mean_hunger_weight"] for m in metrics],
        [m["system_aw_arbitration"]["mean_curiosity_weight"] for m in metrics],
    )
    for label, m in zip(labels, metrics):
        ax.annotate(
            label,
            (
                m["system_aw_arbitration"]["mean_hunger_weight"],
                m["system_aw_arbitration"]["mean_curiosity_weight"],
            ),
            fontsize=8,
            xytext=(4, 4),
            textcoords="offset points",
        )
    ax.set_xlabel("mean hunger weight")
    ax.set_ylabel("mean curiosity weight")
    output_path, artifact = _save_series_plot(
        request,
        "aw-arbitration-balance.png",
        "aw-arbitration-balance",
        "A+W Arbitration Balance",
        "Shows how hunger and curiosity weights are balanced across experiments.",
    )
    finalize_plot(fig, output_path)
    artifacts.append(artifact)

    fig, ax = create_figure(figsize=(7, 5))
    ax.scatter(
        [m["system_aw_world_model"]["world_model_unique_cells"] for m in metrics],
        [m["system_aw_world_model"]["world_model_revisit_ratio"] for m in metrics],
    )
    for label, m in zip(labels, metrics):
        ax.annotate(
            label,
            (
                m["system_aw_world_model"]["world_model_unique_cells"],
                m["system_aw_world_model"]["world_model_revisit_ratio"],
            ),
            fontsize=8,
            xytext=(4, 4),
            textcoords="offset points",
        )
    ax.set_xlabel("world model unique cells")
    ax.set_ylabel("revisit ratio")
    output_path, artifact = _save_series_plot(
        request,
        "aw-world-model-profile.png",
        "aw-world-model-profile",
        "A+W World Model Profile",
        "Relates world-model coverage and revisit structure across the series.",
    )
    finalize_plot(fig, output_path)
    artifacts.append(artifact)

    return artifacts
