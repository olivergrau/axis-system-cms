"""System A+W measurement plot extension."""

from __future__ import annotations

from pathlib import Path

from axis.framework.workspaces.plot_extensions import register_measurement_plot_extension
from axis.framework.workspaces.plotting import create_figure, finalize_plot
from axis.sdk.measurement_plots import GeneratedPlotArtifact, SeriesMeasurementPlotRequest


def _safe_value(value: float | int | None) -> float:
    """Return a plotting-safe numeric value."""
    return 0.0 if value is None else float(value)


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


def _save_experiment_plot(
    request: SeriesMeasurementPlotRequest,
    experiment_id: str,
    filename: str,
    plot_id: str,
    title: str,
    description: str,
):
    output_path = request.experiment_plot_roots[experiment_id] / "system-specific" / "system_aw" / filename
    return output_path, GeneratedPlotArtifact(
        plot_id=plot_id,
        level="experiment",
        plot_group="experiment_system_specific",
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
    ax.plot(labels, [_safe_value(m["system_aw_curiosity"]["mean_spatial_novelty"]) for m in metrics], marker="o", label="spatial")
    ax.plot(labels, [_safe_value(m["system_aw_curiosity"]["mean_sensory_novelty"]) for m in metrics], marker="o", label="sensory")
    ax.plot(labels, [_safe_value(m["system_aw_curiosity"]["mean_composite_novelty"]) for m in metrics], marker="o", label="composite")
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
        [_safe_value(m["system_aw_arbitration"]["mean_hunger_weight"]) for m in metrics],
        [_safe_value(m["system_aw_arbitration"]["mean_curiosity_weight"]) for m in metrics],
    )
    for label, m in zip(labels, metrics):
        ax.annotate(
            label,
            (
                _safe_value(m["system_aw_arbitration"]["mean_hunger_weight"]),
                _safe_value(m["system_aw_arbitration"]["mean_curiosity_weight"]),
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
        [_safe_value(m["system_aw_world_model"]["world_model_unique_cells"]) for m in metrics],
        [_safe_value(m["system_aw_world_model"]["world_model_revisit_ratio"]) for m in metrics],
    )
    for label, m in zip(labels, metrics):
        ax.annotate(
            label,
            (
                _safe_value(m["system_aw_world_model"]["world_model_unique_cells"]),
                _safe_value(m["system_aw_world_model"]["world_model_revisit_ratio"]),
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

    for entry in entries:
        exp_id = entry["experiment_id"]
        metric = entry["behavior_metrics"]["system_specific_metrics"]

        fig, ax = create_figure(figsize=(8, 4.5))
        curiosity = metric["system_aw_curiosity"]
        ax.bar(
            ["spatial", "sensory", "composite", "activation"],
            [
                _safe_value(curiosity["mean_spatial_novelty"]),
                _safe_value(curiosity["mean_sensory_novelty"]),
                _safe_value(curiosity["mean_composite_novelty"]),
                _safe_value(curiosity["mean_curiosity_activation"]),
            ],
        )
        ax.set_ylim(0.0, 1.0)
        ax.set_ylabel("value")
        output_path, artifact = _save_experiment_plot(
            request,
            exp_id,
            "aw-curiosity-snapshot.png",
            "aw-curiosity-snapshot",
            f"{exp_id} A+W Curiosity Snapshot",
            "Per-experiment snapshot of novelty components and curiosity activation.",
        )
        finalize_plot(fig, output_path)
        artifacts.append(artifact)

        fig, ax = create_figure(figsize=(8, 4.5))
        arbitration = metric["system_aw_arbitration"]
        behavior = metric["system_aw_behavior"]
        world_model = metric["system_aw_world_model"]
        ax.bar(
            [
                "hunger_w",
                "curiosity_w",
                "dominance",
                "curiosity_move",
                "consume_under_pressure",
                "revisit_ratio",
            ],
            [
                _safe_value(arbitration["mean_hunger_weight"]),
                _safe_value(arbitration["mean_curiosity_weight"]),
                _safe_value(arbitration["curiosity_dominance_rate"]),
                _safe_value(behavior["curiosity_led_move_rate"]),
                _safe_value(behavior["consume_under_curiosity_pressure_rate"]),
                _safe_value(world_model["world_model_revisit_ratio"]),
            ],
        )
        ax.tick_params(axis="x", rotation=20)
        ax.set_ylabel("value")
        output_path, artifact = _save_experiment_plot(
            request,
            exp_id,
            "aw-behavior-balance.png",
            "aw-behavior-balance",
            f"{exp_id} A+W Behavior Balance",
            "Per-experiment summary of arbitration, curiosity-led behavior, and revisit structure.",
        )
        finalize_plot(fig, output_path)
        artifacts.append(artifact)

    return artifacts
