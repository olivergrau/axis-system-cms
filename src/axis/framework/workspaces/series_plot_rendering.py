"""Rendering of generic and system-specific series measurement plots."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from axis.framework.workspaces.plot_extensions import build_system_measurement_plots
from axis.sdk.measurement_plots import GeneratedPlotArtifact, SeriesMeasurementPlotRequest

from .plotting import create_figure, finalize_plot


@dataclass(frozen=True)
class PlotRenderFailure:
    plot_id: str
    message: str
    system_type: str | None = None


@dataclass(frozen=True)
class SeriesPlotRenderResult:
    series_id: str
    generated: tuple[GeneratedPlotArtifact, ...]
    failures: tuple[PlotRenderFailure, ...]
    manifest_path: str
    report_path: str


def render_series_measurement_plots(
    workspace_path: Path,
    *,
    series_id: str,
    extension_catalog: object | None = None,
) -> SeriesPlotRenderResult:
    """Render generic and system-specific plots for one workspace series."""
    from axis.framework.workspaces.series_paths import resolve_series_paths
    from axis.framework.workspaces.types import load_manifest

    ws = Path(workspace_path)
    manifest = load_manifest(ws)
    workspace_type = manifest.workspace_type.value
    series_paths = resolve_series_paths(ws, series_id=series_id)
    summary_json_path = series_paths.measurements_root / "series-summary.json"
    if not summary_json_path.is_file():
        raise ValueError(
            f"Series summary not found: {summary_json_path}. "
            "Run the series first so aggregate measurement artifacts exist."
        )

    payload = json.loads(summary_json_path.read_text(encoding="utf-8"))
    raw_entries = tuple(payload.get("experiments", ()))
    if not raw_entries:
        raise ValueError(
            f"Series summary contains no experiments: {summary_json_path}"
        )

    prepared_entries: list[dict[str, Any]] = []
    for entry in raw_entries:
        prepared = dict(entry)
        comparison_output_path = prepared.get("comparison_output_path")
        if comparison_output_path:
            comparison_path = ws / comparison_output_path
            if comparison_path.is_file():
                comparison_envelope = json.loads(
                    comparison_path.read_text(encoding="utf-8")
                )
                prepared["_comparison_envelope"] = comparison_envelope
                prepared["_comparison_result"] = comparison_envelope.get(
                    "comparison_result"
                )
        prepared_entries.append(prepared)
    entries = tuple(prepared_entries)

    plots_root = series_paths.measurements_root / "plots"
    generated: list[GeneratedPlotArtifact] = []
    failures: list[PlotRenderFailure] = []

    experiment_plot_roots = {
        entry["experiment_id"]: ws / entry["measurement_dir"] / "plots"
        for entry in entries
    }
    _clear_plot_roots(plots_root, tuple(experiment_plot_roots.values()))

    for plot_id, render_fn in _GENERIC_SERIES_PLOTS:
        try:
            artifact = render_fn(
                ws=ws,
                workspace_type=workspace_type,
                entries=entries,
                output_root=plots_root,
            )
            generated.append(artifact)
        except Exception as exc:
            failures.append(PlotRenderFailure(plot_id=plot_id, message=str(exc)))

    for entry in entries:
        comparison_path = ws / entry["comparison_output_path"]
        comparison_result = entry.get("_comparison_result")
        if comparison_result is None:
            failures.append(
                PlotRenderFailure(
                    plot_id="generic-per-experiment",
                    message=f"Comparison output missing: {comparison_path}",
                )
            )
            continue
        output_root = experiment_plot_roots[entry["experiment_id"]]
        plot_entry = dict(entry)
        plot_entry["workspace_type"] = workspace_type
        for plot_id, render_fn in _GENERIC_EXPERIMENT_PLOTS:
            try:
                artifact = render_fn(
                    ws=ws,
                    entry=plot_entry,
                    comparison_result=comparison_result,
                    output_root=output_root,
                )
                generated.append(artifact)
            except Exception as exc:
                failures.append(
                    PlotRenderFailure(
                        plot_id=f"{entry['experiment_id']}:{plot_id}",
                        message=str(exc),
                    )
                )

    grouped_entries: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        system_type = (
            entry.get("behavior_metrics", {}).get("system_type")
            or entry.get("run_summary", {}).get("system_type")
        )
        if system_type is None:
            continue
        grouped_entries.setdefault(system_type, []).append(entry)

    for system_type, system_entries in grouped_entries.items():
        request = SeriesMeasurementPlotRequest(
            workspace_path=ws,
            series_id=series_id,
            workspace_type=workspace_type,
            measurements_root=series_paths.measurements_root,
            series_plots_root=plots_root,
            experiment_plot_roots={
                entry["experiment_id"]: experiment_plot_roots[entry["experiment_id"]]
                for entry in system_entries
            },
            experiments=tuple(system_entries),
        )
        try:
            generated.extend(
                build_system_measurement_plots(
                    system_type,
                    request,
                    extension_catalog=extension_catalog,
                )
            )
        except Exception as exc:
            failures.append(
                PlotRenderFailure(
                    plot_id=f"{system_type}:extension",
                    message=str(exc),
                    system_type=system_type,
                )
            )

    manifest_path = plots_root / "plots-manifest.json"
    report_path = plots_root / "plots-report.md"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _build_plots_report_markdown(
            workspace_type=workspace_type,
            series_id=series_id,
            generated=tuple(generated),
            failures=tuple(failures),
            workspace_path=ws,
            manifest_path=manifest_path,
            report_path=report_path,
        ),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(
            {
                "series_id": series_id,
                "workspace_type": workspace_type,
                "generated_at": datetime.now(UTC).isoformat(),
                "report_path": str(report_path.relative_to(ws)),
                "generated": [asdict(item) for item in generated],
                "failures": [asdict(item) for item in failures],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return SeriesPlotRenderResult(
        series_id=series_id,
        generated=tuple(generated),
        failures=tuple(failures),
        manifest_path=str(manifest_path.relative_to(ws)),
        report_path=str(report_path.relative_to(ws)),
    )


def _labels(entries: tuple[dict[str, Any], ...]) -> list[str]:
    return [entry["experiment_id"] for entry in entries]


def _role_label_pair(workspace_type: str) -> tuple[str, str]:
    if workspace_type == "single_system":
        return "current", "baseline"
    return "candidate", "reference"


def _survival_label_pair(workspace_type: str) -> tuple[str, str]:
    left, right = _role_label_pair(workspace_type)
    return f"{left} survival", f"{right} survival"


def _delta_label(workspace_type: str, quantity: str) -> str:
    left, right = _role_label_pair(workspace_type)
    return f"{quantity} ({left} - {right})"


def _longer_label_pair(workspace_type: str) -> tuple[str, str]:
    left, right = _role_label_pair(workspace_type)
    return f"{left} longer", f"{right} longer"


def _series_overview_root(output_root: Path) -> Path:
    return output_root / "series-overview"


def _experiment_comparison_root(output_root: Path) -> Path:
    return output_root / "experiment-comparison"


def _clear_plot_roots(series_plots_root: Path, experiment_plot_roots: tuple[Path, ...]) -> None:
    for root in (series_plots_root, *experiment_plot_roots):
        if root.exists():
            shutil.rmtree(root)


def _role_noun_pair(workspace_type: str) -> tuple[str, str]:
    if workspace_type == "single_system":
        return "current system", "baseline system"
    return "candidate system", "reference system"


def _artifact_sort_key(item: GeneratedPlotArtifact) -> tuple[str, str, str]:
    return (
        item.plot_group,
        item.producer_system_type or "",
        item.relative_output_path,
    )


def _experiment_id_from_relative_path(relative_output_path: str) -> str | None:
    for part in Path(relative_output_path).parts:
        if part.startswith("experiment_"):
            return part
    return None


def _link_from_report(report_path: Path, target: Path) -> str:
    return os.path.relpath(target, start=report_path.parent)


def _build_plots_report_markdown(
    *,
    workspace_type: str,
    series_id: str,
    generated: tuple[GeneratedPlotArtifact, ...],
    failures: tuple[PlotRenderFailure, ...],
    workspace_path: Path,
    manifest_path: Path,
    report_path: Path,
) -> str:
    left_noun, right_noun = _role_noun_pair(workspace_type)
    generated_sorted = sorted(generated, key=_artifact_sort_key)
    lines: list[str] = []
    lines.append(f"# Series Plot Report: {series_id}")
    lines.append("")
    lines.append(f"- Workspace type: `{workspace_type}`")
    lines.append(f"- Generated plots: `{len(generated)}`")
    lines.append(f"- Failures: `{len(failures)}`")
    lines.append(f"- Plot manifest: [{manifest_path.name}]({_link_from_report(report_path, manifest_path)})")
    lines.append("")
    lines.append("This report groups the generated plot artifacts by plotting layer and provides")
    lines.append("direct links to each image file.")
    lines.append("")

    def add_plot_item(item: GeneratedPlotArtifact) -> None:
        target_path = workspace_path / item.relative_output_path
        link = _link_from_report(report_path, target_path)
        lines.append(f"### {item.title or item.plot_id}")
        lines.append("")
        lines.append(f"- Plot id: `{item.plot_id}`")
        lines.append(f"- Source: `{item.producer_kind}`")
        if item.producer_system_type:
            lines.append(f"- System source: `{item.producer_system_type}`")
        lines.append(f"- File: [{target_path.name}]({link})")
        if item.description:
            lines.append(f"- Reading note: {item.description}")
        lines.append("")
        lines.append(f"![{item.title or item.plot_id}]({link})")
        lines.append("")

    lines.append("## Series Overview")
    lines.append("")
    lines.append(
        f"These plots summarize the whole series at a glance. In this workspace, "
        f"they compare the `{left_noun}` against the `{right_noun}` where pairwise "
        "comparison semantics apply."
    )
    lines.append("")
    for item in generated_sorted:
        if item.plot_group == "series_overview":
            add_plot_item(item)

    system_groups = sorted(
        {
            item.producer_system_type
            for item in generated_sorted
            if item.plot_group == "system_specific" and item.producer_system_type
        }
    )
    if system_groups:
        lines.append("## System-Specific Plots")
        lines.append("")
        lines.append(
            "These plots come from registered system plot extensions and are meant to "
            "highlight mechanism-specific structure."
        )
        lines.append("")
        for system_type in system_groups:
            lines.append(f"### {system_type}")
            lines.append("")
            for item in generated_sorted:
                if item.plot_group == "system_specific" and item.producer_system_type == system_type:
                    add_plot_item(item)

    experiment_ids = sorted(
        {
            _experiment_id_from_relative_path(item.relative_output_path)
            for item in generated_sorted
            if item.plot_group == "experiment_comparison"
        } - {None}
    )
    if experiment_ids:
        lines.append("## Per-Experiment Comparison Plots")
        lines.append("")
        lines.append(
            "These plots sit under each experiment measurement folder and visualize "
            "pairwise distributions and outcome structure."
        )
        lines.append("")
        for experiment_id in experiment_ids:
            lines.append(f"### {experiment_id}")
            lines.append("")
            for item in generated_sorted:
                if item.plot_group != "experiment_comparison":
                    continue
                if _experiment_id_from_relative_path(item.relative_output_path) == experiment_id:
                    add_plot_item(item)

    experiment_ids_system = sorted(
        {
            _experiment_id_from_relative_path(item.relative_output_path)
            for item in generated_sorted
            if item.plot_group == "experiment_system_specific"
        } - {None}
    )
    if experiment_ids_system:
        lines.append("## Per-Experiment System-Specific Plots")
        lines.append("")
        lines.append(
            "These plots come from system plot extensions but are rendered into the "
            "individual experiment folders, so they can be read alongside the "
            "generic comparison plots."
        )
        lines.append("")
        for experiment_id in experiment_ids_system:
            lines.append(f"### {experiment_id}")
            lines.append("")
            for item in generated_sorted:
                if item.plot_group != "experiment_system_specific":
                    continue
                if _experiment_id_from_relative_path(item.relative_output_path) == experiment_id:
                    add_plot_item(item)

    if failures:
        lines.append("## Plot Failures")
        lines.append("")
        for failure in failures:
            system_hint = f" (`{failure.system_type}`)" if failure.system_type else ""
            lines.append(f"- `{failure.plot_id}`{system_hint}: {failure.message}")
        lines.append("")

    return "\n".join(lines)


def _render_survival_rates(*, ws: Path, workspace_type: str, entries, output_root: Path):
    labels = _labels(entries)
    cand = [entry["comparison_summary"]["candidate_survival_rate"] for entry in entries]
    ref = [entry["comparison_summary"]["reference_survival_rate"] for entry in entries]
    fig, ax = create_figure(figsize=(10, 5))
    xs = list(range(len(labels)))
    width = 0.38
    cand_label, ref_label = _survival_label_pair(workspace_type)
    ax.bar([x - width / 2 for x in xs], cand, width=width, label=cand_label)
    ax.bar([x + width / 2 for x in xs], ref, width=width, label=ref_label)
    ax.set_xticks(xs, labels, rotation=30, ha="right")
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel("survival rate")
    ax.legend()
    output_path = _series_overview_root(output_root) / "survival-rates.png"
    finalize_plot(fig, output_path)
    return GeneratedPlotArtifact(
        plot_id="survival-rates",
        level="series",
        plot_group="series_overview",
        relative_output_path=str(output_path.relative_to(ws)),
        title="Survival Rates",
        description="Compares horizon-reaching survival rates across the whole series.",
        producer_kind="framework",
    )


def _render_paired_survival_counts(*, ws: Path, workspace_type: str, entries, output_root: Path):
    labels = _labels(entries)
    cand = [entry["comparison_summary"]["candidate_longer_count"] for entry in entries]
    ref = [entry["comparison_summary"]["reference_longer_count"] for entry in entries]
    eq = [entry["comparison_summary"]["equal_count"] for entry in entries]
    fig, ax = create_figure(figsize=(10, 5))
    xs = list(range(len(labels)))
    cand_label, ref_label = _longer_label_pair(workspace_type)
    ax.bar(xs, cand, label=cand_label)
    ax.bar(xs, ref, bottom=cand, label=ref_label)
    ax.bar(xs, eq, bottom=[c + r for c, r in zip(cand, ref)], label="equal")
    ax.set_xticks(xs, labels, rotation=30, ha="right")
    ax.set_ylabel("paired episode count")
    ax.legend()
    output_path = _series_overview_root(output_root) / "paired-survival-counts.png"
    finalize_plot(fig, output_path)
    return GeneratedPlotArtifact(
        plot_id="paired-survival-counts",
        level="series",
        plot_group="series_overview",
        relative_output_path=str(output_path.relative_to(ws)),
        title="Paired Survival Counts",
        description="Shows, per experiment, how many paired episodes ended with one side living longer or ending equal.",
        producer_kind="framework",
    )


def _render_trajectory_vs_survival(*, ws: Path, workspace_type: str, entries, output_root: Path):
    labels = _labels(entries)
    x = [entry["comparison_summary"]["mean_trajectory_distance"]["mean"] for entry in entries]
    y = [
        entry["comparison_summary"]["candidate_survival_rate"]
        - entry["comparison_summary"]["reference_survival_rate"]
        for entry in entries
    ]
    fig, ax = create_figure(figsize=(8, 5))
    ax.scatter(x, y)
    for label, xv, yv in zip(labels, x, y):
        ax.annotate(label, (xv, yv), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.axhline(0.0, color="gray", linewidth=1, linestyle="--")
    ax.set_xlabel("mean trajectory distance")
    ax.set_ylabel(_delta_label(workspace_type, "survival delta"))
    output_path = _series_overview_root(output_root) / "trajectory-vs-survival.png"
    finalize_plot(fig, output_path)
    return GeneratedPlotArtifact(
        plot_id="trajectory-vs-survival",
        level="series",
        plot_group="series_overview",
        relative_output_path=str(output_path.relative_to(ws)),
        title="Trajectory Distance vs Survival Delta",
        description="Relates behavioral divergence to survival difference across experiments.",
        producer_kind="framework",
    )


def _render_efficiency_vs_survival(*, ws: Path, workspace_type: str, entries, output_root: Path):
    labels = _labels(entries)
    x = [entry["behavior_metrics"]["standard_metrics"]["net_energy_efficiency"]["mean"] for entry in entries]
    y = [
        entry["comparison_summary"]["candidate_survival_rate"]
        - entry["comparison_summary"]["reference_survival_rate"]
        for entry in entries
    ]
    fig, ax = create_figure(figsize=(8, 5))
    ax.scatter(x, y)
    for label, xv, yv in zip(labels, x, y):
        ax.annotate(label, (xv, yv), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.axhline(0.0, color="gray", linewidth=1, linestyle="--")
    ax.set_xlabel("net energy efficiency")
    ax.set_ylabel(_delta_label(workspace_type, "survival delta"))
    output_path = _series_overview_root(output_root) / "efficiency-vs-survival.png"
    finalize_plot(fig, output_path)
    return GeneratedPlotArtifact(
        plot_id="efficiency-vs-survival",
        level="series",
        plot_group="series_overview",
        relative_output_path=str(output_path.relative_to(ws)),
        title="Efficiency vs Survival Delta",
        description="Relates net energy efficiency to survival difference across experiments.",
        producer_kind="framework",
    )


def _render_series_progression(*, ws: Path, workspace_type: str, entries, output_root: Path):
    labels = _labels(entries)
    xs = list(range(len(labels)))
    death = [entry["run_summary"]["death_rate"] for entry in entries]
    vitality = [entry["run_summary"]["mean_final_vitality"] for entry in entries]
    efficiency = [entry["behavior_metrics"]["standard_metrics"]["net_energy_efficiency"]["mean"] for entry in entries]
    cand = [entry["comparison_summary"]["candidate_survival_rate"] for entry in entries]
    ref = [entry["comparison_summary"]["reference_survival_rate"] for entry in entries]
    fig, ax = create_figure(figsize=(10, 5.5))
    ax.plot(xs, death, marker="o", label="death rate")
    ax.plot(xs, vitality, marker="o", label="mean final vitality")
    ax.plot(xs, efficiency, marker="o", label="net energy efficiency")
    cand_label, ref_label = _survival_label_pair(workspace_type)
    ax.plot(xs, cand, marker="o", label=cand_label)
    ax.plot(xs, ref, marker="o", label=ref_label)
    ax.set_title("Series Progression")
    ax.set_ylabel("metric value")
    ax.set_xlabel("experiment")
    ax.set_xticks(xs, labels, rotation=30, ha="right")
    ymax = max(death + vitality + efficiency + cand + ref)
    ax.set_ylim(0.0, max(1.0, ymax * 1.08))
    ax.legend(ncol=2)
    output_path = _series_overview_root(output_root) / "series-progression.png"
    finalize_plot(fig, output_path)
    return GeneratedPlotArtifact(
        plot_id="series-progression",
        level="series",
        plot_group="series_overview",
        relative_output_path=str(output_path.relative_to(ws)),
        title="Series Progression",
        description="Tracks key run and comparison metrics over experiment order on one shared y-axis.",
        producer_kind="framework",
    )


def _render_paired_outcome_categories(*, ws: Path, workspace_type: str, entries, output_root: Path):
    labels = _labels(entries)
    category_order = [
        "both reached horizon",
        "candidate reached only",
        "reference reached only",
        "both died, candidate longer",
        "both died, reference longer",
        "both died equal",
    ]
    category_labels = _role_category_labels(workspace_type)
    colors = {
        "both reached horizon": "#1b9e77",
        "candidate reached only": "#66a61e",
        "reference reached only": "#d95f02",
        "both died, candidate longer": "#7570b3",
        "both died, reference longer": "#e7298a",
        "both died equal": "#999999",
    }
    category_series: dict[str, list[int]] = {key: [] for key in category_order}
    for entry in entries:
        comparison_result = _entry_comparison_result(entry, plot_id="paired-outcome-categories")
        valid = _require_non_empty(
            _valid_episode_results(comparison_result),
            plot_id="paired-outcome-categories",
        )
        counts = {key: 0 for key in category_order}
        for er in valid:
            counts[_paired_outcome_category(entry, er["outcome"])] += 1
        for key in category_order:
            category_series[key].append(counts[key])

    fig, ax = create_figure(figsize=(11, 5.5))
    xs = list(range(len(labels)))
    bottom = [0] * len(labels)
    for key in category_order:
        values = category_series[key]
        ax.bar(xs, values, bottom=bottom, label=category_labels[key], color=colors[key])
        bottom = [b + v for b, v in zip(bottom, values)]
    ax.set_xticks(xs, labels, rotation=30, ha="right")
    ax.set_ylabel("paired episode count")
    ax.legend(fontsize=8, ncol=2)
    output_path = _series_overview_root(output_root) / "paired-outcome-categories.png"
    finalize_plot(fig, output_path)
    return GeneratedPlotArtifact(
        plot_id="paired-outcome-categories",
        level="series",
        plot_group="series_overview",
        relative_output_path=str(output_path.relative_to(ws)),
        title="Paired Outcome Categories",
        description=(
            "Read this plot first when survival rate feels too binary: it separates "
            "true horizon-reaching wins from cases where both sides still died but "
            "one side consistently lasted longer."
        ),
        producer_kind="framework",
    )


def _render_horizon_vs_lifespan_delta(*, ws: Path, workspace_type: str, entries, output_root: Path):
    labels = _labels(entries)
    x = [
        entry["comparison_summary"]["candidate_survival_rate"]
        - entry["comparison_summary"]["reference_survival_rate"]
        for entry in entries
    ]
    y = [entry["comparison_summary"]["total_steps_delta"]["mean"] for entry in entries]
    fig, ax = create_figure(figsize=(8.5, 5.5))
    ax.scatter(x, y)
    for label, xv, yv in zip(labels, x, y):
        ax.annotate(label, (xv, yv), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.axhline(0.0, color="gray", linewidth=1, linestyle="--")
    ax.axvline(0.0, color="gray", linewidth=1, linestyle="--")
    ax.set_xlabel(_delta_label(workspace_type, "survival rate"))
    ax.set_ylabel(_delta_label(workspace_type, "mean total steps lived"))
    output_path = _series_overview_root(output_root) / "horizon-vs-lifespan-delta.png"
    finalize_plot(fig, output_path)
    return GeneratedPlotArtifact(
        plot_id="horizon-vs-lifespan-delta",
        level="series",
        plot_group="series_overview",
        relative_output_path=str(output_path.relative_to(ws)),
        title="Horizon vs Lifespan Delta",
        description=(
            "Use the quadrants here to separate experiments that improve horizon "
            "survival, experiments that only improve time-lived below the horizon, "
            "and experiments that get worse on both axes."
        ),
        producer_kind="framework",
    )


def _render_sub_horizon_advantage(*, ws: Path, workspace_type: str, entries, output_root: Path):
    labels = _labels(entries)
    left_label, right_label = _longer_label_pair(workspace_type)
    candidate_counts: list[int] = []
    reference_counts: list[int] = []
    equal_counts: list[int] = []
    mean_deltas: list[float] = []
    for entry in entries:
        valid = _sub_horizon_results(entry)
        candidate = 0
        reference = 0
        equal = 0
        deltas: list[float] = []
        for er in valid:
            longer = er["outcome"]["longer_survivor"]
            deltas.append(float(er["outcome"]["total_steps_delta"]))
            if longer == "candidate":
                candidate += 1
            elif longer == "reference":
                reference += 1
            else:
                equal += 1
        candidate_counts.append(candidate)
        reference_counts.append(reference)
        equal_counts.append(equal)
        mean_deltas.append(sum(deltas) / len(deltas) if deltas else 0.0)

    fig, ax = create_figure(figsize=(11, 5.5))
    xs = list(range(len(labels)))
    ax.bar(xs, candidate_counts, label=left_label, color="#7570b3")
    ax.bar(xs, reference_counts, bottom=candidate_counts, label=right_label, color="#e7298a")
    ax.bar(
        xs,
        equal_counts,
        bottom=[c + r for c, r in zip(candidate_counts, reference_counts)],
        label="equal",
        color="#999999",
    )
    totals = [c + r + e for c, r, e in zip(candidate_counts, reference_counts, equal_counts)]
    for x, total, mean_delta in zip(xs, totals, mean_deltas):
        ax.annotate(
            f"Δ={mean_delta:.1f}",
            (x, total),
            fontsize=8,
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
        )
    ax.set_xticks(xs, labels, rotation=30, ha="right")
    ax.set_ylabel("sub-horizon paired episode count")
    ax.legend(fontsize=8)
    output_path = _series_overview_root(output_root) / "sub-horizon-advantage.png"
    finalize_plot(fig, output_path)
    return GeneratedPlotArtifact(
        plot_id="sub-horizon-advantage",
        level="series",
        plot_group="series_overview",
        relative_output_path=str(output_path.relative_to(ws)),
        title="Sub-Horizon Advantage",
        description=(
            "This plot ignores all horizon-reaching episodes and asks a narrower "
            "question: when both sides fail, which one still remains viable for "
            "longer, and by roughly how much?"
        ),
        producer_kind="framework",
    )


_GENERIC_SERIES_PLOTS = (
    ("survival-rates", _render_survival_rates),
    ("paired-survival-counts", _render_paired_survival_counts),
    ("trajectory-vs-survival", _render_trajectory_vs_survival),
    ("efficiency-vs-survival", _render_efficiency_vs_survival),
    ("series-progression", _render_series_progression),
    ("paired-outcome-categories", _render_paired_outcome_categories),
    ("horizon-vs-lifespan-delta", _render_horizon_vs_lifespan_delta),
    ("sub-horizon-advantage", _render_sub_horizon_advantage),
)


def _valid_episode_results(comparison_result: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for er in comparison_result.get("episode_results", []):
        if er.get("result_mode") != "comparison_succeeded":
            continue
        if er.get("metrics") is None or er.get("outcome") is None:
            continue
        out.append(er)
    return out


def _entry_comparison_result(entry: dict[str, Any], *, plot_id: str) -> dict[str, Any]:
    comparison_result = entry.get("_comparison_result")
    if not isinstance(comparison_result, dict):
        raise ValueError(f"Comparison result missing for plot '{plot_id}'")
    return comparison_result


def _entry_side_horizon(entry: dict[str, Any], side: str) -> int | None:
    envelope = entry.get("_comparison_envelope")
    if not isinstance(envelope, dict):
        return None
    config_key = "candidate_config" if side == "candidate" else "reference_config"
    config = envelope.get(config_key)
    if not isinstance(config, dict):
        return None
    execution = config.get("execution")
    if not isinstance(execution, dict):
        return None
    max_steps = execution.get("max_steps")
    if isinstance(max_steps, bool):
        return None
    if isinstance(max_steps, int | float):
        return int(max_steps)
    return None


def _did_reach_horizon(entry: dict[str, Any], outcome: dict[str, Any], side: str) -> bool:
    termination_reason = outcome.get(f"{side}_termination_reason")
    if termination_reason is not None:
        return termination_reason == "max_steps_reached"
    total_steps = outcome.get(f"{side}_total_steps")
    horizon = _entry_side_horizon(entry, side)
    return (
        isinstance(total_steps, int | float)
        and horizon is not None
        and total_steps >= horizon
    )


def _paired_outcome_category(entry: dict[str, Any], outcome: dict[str, Any]) -> str:
    candidate_survived = _did_reach_horizon(entry, outcome, "candidate")
    reference_survived = _did_reach_horizon(entry, outcome, "reference")
    if candidate_survived and reference_survived:
        return "both reached horizon"
    if candidate_survived and not reference_survived:
        return "candidate reached only"
    if reference_survived and not candidate_survived:
        return "reference reached only"
    longer = outcome.get("longer_survivor")
    if longer == "candidate":
        return "both died, candidate longer"
    if longer == "reference":
        return "both died, reference longer"
    return "both died equal"


def _role_category_labels(workspace_type: str) -> dict[str, str]:
    left, right = _role_label_pair(workspace_type)
    return {
        "both reached horizon": "both reached horizon",
        "candidate reached only": f"{left} reached only",
        "reference reached only": f"{right} reached only",
        "both died, candidate longer": f"both died, {left} longer",
        "both died, reference longer": f"both died, {right} longer",
        "both died equal": "both died equal",
    }


def _sub_horizon_results(entry: dict[str, Any]) -> list[dict[str, Any]]:
    comparison_result = _entry_comparison_result(entry, plot_id="sub-horizon-advantage")
    valid = _valid_episode_results(comparison_result)
    filtered: list[dict[str, Any]] = []
    for er in valid:
        outcome = er["outcome"]
        if _did_reach_horizon(entry, outcome, "candidate"):
            continue
        if _did_reach_horizon(entry, outcome, "reference"):
            continue
        filtered.append(er)
    return filtered


def _require_non_empty(valid: list[dict[str, Any]], *, plot_id: str) -> list[dict[str, Any]]:
    if not valid:
        raise ValueError(f"No valid episode results available for plot '{plot_id}'")
    return valid


def _render_steps_delta_hist(
    *,
    ws: Path,
    entry: dict[str, Any],
    comparison_result: dict[str, Any],
    output_root: Path,
):
    valid = _require_non_empty(
        _valid_episode_results(comparison_result),
        plot_id="paired-steps-delta-hist",
    )
    values = [er["outcome"]["total_steps_delta"] for er in valid]
    fig, ax = create_figure()
    ax.hist(values, bins=min(12, max(3, len(set(values)))))
    ax.axvline(0.0, color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel(_delta_label(entry["workspace_type"], "total steps delta"))
    ax.set_ylabel("episode pairs")
    output_path = _experiment_comparison_root(output_root) / "paired-steps-delta-hist.png"
    finalize_plot(fig, output_path)
    return GeneratedPlotArtifact(
        plot_id="paired-steps-delta-hist",
        level="experiment",
        plot_group="experiment_comparison",
        relative_output_path=str(output_path.relative_to(ws)),
        title=f"{entry['experiment_id']} Steps Delta Histogram",
        description="Distribution of paired episode length differences for this experiment.",
        producer_kind="framework",
    )


def _render_final_vitality_delta_hist(
    *,
    ws: Path,
    entry: dict[str, Any],
    comparison_result: dict[str, Any],
    output_root: Path,
):
    valid = _require_non_empty(
        _valid_episode_results(comparison_result),
        plot_id="paired-final-vitality-delta-hist",
    )
    values = [er["outcome"]["final_vitality_delta"] for er in valid]
    fig, ax = create_figure()
    ax.hist(values, bins=min(12, max(3, len(set(round(v, 3) for v in values)))))
    ax.axvline(0.0, color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel(_delta_label(entry["workspace_type"], "final vitality delta"))
    ax.set_ylabel("episode pairs")
    output_path = _experiment_comparison_root(output_root) / "paired-final-vitality-delta-hist.png"
    finalize_plot(fig, output_path)
    return GeneratedPlotArtifact(
        plot_id="paired-final-vitality-delta-hist",
        level="experiment",
        plot_group="experiment_comparison",
        relative_output_path=str(output_path.relative_to(ws)),
        title=f"{entry['experiment_id']} Final Vitality Delta Histogram",
        description="Distribution of final vitality differences across paired episodes.",
        producer_kind="framework",
    )


def _render_episode_outcomes_strip(
    *,
    ws: Path,
    entry: dict[str, Any],
    comparison_result: dict[str, Any],
    output_root: Path,
):
    valid = _require_non_empty(
        _valid_episode_results(comparison_result),
        plot_id="episode-outcomes-strip",
    )
    left_role, right_role = _role_label_pair(entry["workspace_type"])
    mapping = {"reference": 0, "equal": 1, "candidate": 2}
    colors = {"reference": "#d95f02", "equal": "#7570b3", "candidate": "#1b9e77"}
    xs = list(range(1, len(valid) + 1))
    ys = [mapping[er["outcome"]["longer_survivor"]] for er in valid]
    cs = [colors[er["outcome"]["longer_survivor"]] for er in valid]
    fig, ax = create_figure(figsize=(10, 3.5))
    ax.scatter(xs, ys, c=cs)
    ax.set_yticks([0, 1, 2], [f"{right_role} longer", "equal", f"{left_role} longer"])
    ax.set_xlabel("episode pair")
    output_path = _experiment_comparison_root(output_root) / "episode-outcomes-strip.png"
    finalize_plot(fig, output_path)
    return GeneratedPlotArtifact(
        plot_id="episode-outcomes-strip",
        level="experiment",
        plot_group="experiment_comparison",
        relative_output_path=str(output_path.relative_to(ws)),
        title=f"{entry['experiment_id']} Episode Outcomes",
        description="Shows, per episode pair, which side survived longer or whether both tied.",
        producer_kind="framework",
    )


def _render_mismatch_vs_outcome(
    *,
    ws: Path,
    entry: dict[str, Any],
    comparison_result: dict[str, Any],
    output_root: Path,
):
    valid = _require_non_empty(
        _valid_episode_results(comparison_result),
        plot_id="mismatch-vs-outcome",
    )
    x = [er["metrics"]["action_divergence"]["action_mismatch_rate"] for er in valid]
    y = [er["outcome"]["total_steps_delta"] for er in valid]
    fig, ax = create_figure()
    ax.scatter(x, y)
    ax.axhline(0.0, color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel("action mismatch rate")
    ax.set_ylabel(_delta_label(entry["workspace_type"], "total steps delta"))
    output_path = _experiment_comparison_root(output_root) / "mismatch-vs-outcome.png"
    finalize_plot(fig, output_path)
    return GeneratedPlotArtifact(
        plot_id="mismatch-vs-outcome",
        level="experiment",
        plot_group="experiment_comparison",
        relative_output_path=str(output_path.relative_to(ws)),
        title=f"{entry['experiment_id']} Mismatch vs Outcome",
        description="Relates action mismatch rate to paired outcome difference within one experiment.",
        producer_kind="framework",
    )


def _render_trajectory_distance_distribution(
    *,
    ws: Path,
    entry: dict[str, Any],
    comparison_result: dict[str, Any],
    output_root: Path,
):
    valid = _require_non_empty(
        _valid_episode_results(comparison_result),
        plot_id="trajectory-distance-distribution",
    )
    values = [er["metrics"]["position_divergence"]["mean_trajectory_distance"] for er in valid]
    fig, ax = create_figure(figsize=(8, 3.5))
    ax.boxplot(values, orientation="horizontal")
    ax.scatter(values, [1] * len(values), alpha=0.4, s=12)
    ax.set_yticks([])
    ax.set_xlabel("mean trajectory distance")
    output_path = _experiment_comparison_root(output_root) / "trajectory-distance-distribution.png"
    finalize_plot(fig, output_path)
    return GeneratedPlotArtifact(
        plot_id="trajectory-distance-distribution",
        level="experiment",
        plot_group="experiment_comparison",
        relative_output_path=str(output_path.relative_to(ws)),
        title=f"{entry['experiment_id']} Trajectory Distance Distribution",
        description="Summarizes how far paired trajectories diverged during this experiment.",
        producer_kind="framework",
    )


def _render_steps_lived_distribution(
    *,
    ws: Path,
    entry: dict[str, Any],
    comparison_result: dict[str, Any],
    output_root: Path,
):
    valid = _require_non_empty(
        _valid_episode_results(comparison_result),
        plot_id="steps-lived-distribution",
    )
    left_label, right_label = _role_label_pair(entry["workspace_type"])
    candidate_steps = [er["outcome"]["candidate_total_steps"] for er in valid]
    reference_steps = [er["outcome"]["reference_total_steps"] for er in valid]
    fig, ax = create_figure(figsize=(8, 4.5))
    ax.boxplot(
        [candidate_steps, reference_steps],
        tick_labels=[left_label, right_label],
    )
    ax.set_ylabel("total steps lived")
    output_path = _experiment_comparison_root(output_root) / "steps-lived-distribution.png"
    finalize_plot(fig, output_path)
    return GeneratedPlotArtifact(
        plot_id="steps-lived-distribution",
        level="experiment",
        plot_group="experiment_comparison",
        relative_output_path=str(output_path.relative_to(ws)),
        title=f"{entry['experiment_id']} Steps Lived Distribution",
        description=(
            "Use this to see whether one side tends to fail later even without "
            "turning those later failures into more horizon reaches. Wide or shifted "
            "boxes indicate lifespan differences hidden by survival rate alone."
        ),
        producer_kind="framework",
    )


_GENERIC_EXPERIMENT_PLOTS = (
    ("paired-steps-delta-hist", _render_steps_delta_hist),
    ("paired-final-vitality-delta-hist", _render_final_vitality_delta_hist),
    ("episode-outcomes-strip", _render_episode_outcomes_strip),
    ("mismatch-vs-outcome", _render_mismatch_vs_outcome),
    ("trajectory-distance-distribution", _render_trajectory_distance_distribution),
    ("steps-lived-distribution", _render_steps_lived_distribution),
)
