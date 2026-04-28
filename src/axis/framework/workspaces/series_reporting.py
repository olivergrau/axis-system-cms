"""Aggregate reporting for workspace experiment series execution."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from axis.framework.comparison.types import RunComparisonResult
from axis.framework.metrics.types import RunBehaviorMetrics
from axis.framework.run import RunSummary
from axis.framework.workspaces.comparison_envelope import WorkspaceComparisonEnvelope


@dataclass(frozen=True)
class ExperimentSeriesAggregateEntry:
    """Normalized aggregate data for one executed experiment."""

    experiment_id: str
    label: str
    title: str
    hypothesis: list[str]
    measurement_dir: str
    comparison_output_path: str
    comparison_log_path: str
    run_summary_log_path: str
    reference_experiment_id: str
    candidate_experiment_id: str
    run_summary: dict[str, Any]
    behavior_metrics: dict[str, Any]
    comparison_summary: dict[str, Any]


def render_series_outputs(
    workspace_path: Path,
    *,
    workspace_type: str,
    series_title: str | None,
    series_description: str | None,
    measurement_root_dir: str,
    entries: list[ExperimentSeriesAggregateEntry],
) -> dict[str, str]:
    """Render markdown/json/csv aggregate outputs under measurements/."""
    ws = Path(workspace_path)
    measurements_dir = ws / measurement_root_dir
    measurements_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = measurements_dir / "series-summary.md"
    json_path = measurements_dir / "series-summary.json"
    csv_path = measurements_dir / "series-metrics.csv"
    manifest_path = measurements_dir / "series-manifest.json"

    markdown_path.write_text(
        _render_markdown(workspace_type, series_title, series_description, entries),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(
            {
                "series_title": series_title,
                "series_description": series_description,
                "experiments": [asdict(entry) for entry in entries],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_csv(csv_path, entries)
    manifest_path.write_text(
        json.dumps(
            {
                "series_title": series_title,
                "series_description": series_description,
                "experiment_order": [entry.experiment_id for entry in entries],
                "measurement_directories": [entry.measurement_dir for entry in entries],
                "comparison_outputs": [entry.comparison_output_path for entry in entries],
                "aggregate_outputs": {
                    "markdown": str(markdown_path.relative_to(ws)),
                    "json": str(json_path.relative_to(ws)),
                    "csv": str(csv_path.relative_to(ws)),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "series_summary_markdown_path": str(markdown_path.relative_to(ws)),
        "series_summary_json_path": str(json_path.relative_to(ws)),
        "series_metrics_csv_path": str(csv_path.relative_to(ws)),
        "series_manifest_json_path": str(manifest_path.relative_to(ws)),
    }


def build_aggregate_entry(
    *,
    experiment_id: str,
    label: str,
    title: str,
    hypothesis: list[str],
    measurement_dir: str,
    comparison_output_path: str,
    comparison_log_path: str,
    run_summary_log_path: str,
    comparison_envelope: WorkspaceComparisonEnvelope,
    run_summary: RunSummary,
    behavior_metrics: RunBehaviorMetrics,
) -> ExperimentSeriesAggregateEntry:
    """Build one aggregate entry from structured artifacts."""
    comparison_result = RunComparisonResult.model_validate(
        comparison_envelope.comparison_result
    )
    return ExperimentSeriesAggregateEntry(
        experiment_id=experiment_id,
        label=label,
        title=title,
        hypothesis=hypothesis,
        measurement_dir=measurement_dir,
        comparison_output_path=comparison_output_path,
        comparison_log_path=comparison_log_path,
        run_summary_log_path=run_summary_log_path,
        reference_experiment_id=comparison_result.reference_experiment_id or "",
        candidate_experiment_id=comparison_result.candidate_experiment_id or "",
        run_summary=run_summary.model_dump(mode="json"),
        behavior_metrics=behavior_metrics.model_dump(mode="json"),
        comparison_summary=comparison_result.summary.model_dump(mode="json"),
    )


def _flatten_metric_payload(entry: ExperimentSeriesAggregateEntry) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "experiment_id": entry.experiment_id,
        "label": entry.label,
        "title": entry.title,
    }
    payload.update(entry.run_summary)

    standard = entry.behavior_metrics.get("standard_metrics", {})
    for key, value in standard.items():
        if key in {"mean_steps", "death_rate", "mean_final_vitality"}:
            continue
        if isinstance(value, dict) and "mean" in value:
            payload[key] = value["mean"]
        else:
            payload[key] = value

    system_specific = entry.behavior_metrics.get("system_specific_metrics", {})
    for key, value in sorted(system_specific.items()):
        if isinstance(value, dict) and "mean" in value:
            payload[key] = value["mean"]
        else:
            payload[key] = value

    comparison = entry.comparison_summary
    payload["comparison_reference_survival_rate"] = comparison["reference_survival_rate"]
    payload["comparison_candidate_survival_rate"] = comparison["candidate_survival_rate"]
    payload["comparison_mean_trajectory_distance"] = comparison[
        "mean_trajectory_distance"
    ]["mean"]
    payload["comparison_total_steps_delta"] = comparison["total_steps_delta"]["mean"]
    payload["comparison_final_vitality_delta"] = comparison[
        "final_vitality_delta"
    ]["mean"]
    return payload


def _write_csv(path: Path, entries: list[ExperimentSeriesAggregateEntry]) -> None:
    rows = [_flatten_metric_payload(entry) for entry in entries]
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _render_markdown(
    workspace_type: str,
    series_title: str | None,
    series_description: str | None,
    entries: list[ExperimentSeriesAggregateEntry],
) -> str:
    title = series_title or "Experiment Series Summary"
    lines: list[str] = [f"# {title}", ""]
    if series_description:
        lines.extend([series_description, ""])

    lines.extend([
        "## Overview",
        "",
        f"- Experiments executed: {len(entries)}",
        f"- Baseline experiment: `{entries[0].experiment_id}`",
        "",
        "## At A Glance",
        "",
    ])
    lines.extend(_render_table(entries))
    lines.extend(["", "## Progression View", ""])
    for index, entry in enumerate(entries):
        if index == 0:
            lines.append(
                f"- `{entry.experiment_id}` establishes the baseline for the series."
            )
            continue
        previous = entries[index - 1]
        delta = _delta_line(entry, previous)
        lines.append(f"- `{entry.experiment_id}` vs `{previous.experiment_id}`: {delta}")

    lines.extend(["", "## Baseline View", ""])
    baseline = entries[0]
    for entry in entries[1:]:
        delta = _delta_line(entry, baseline)
        lines.append(f"- `{entry.experiment_id}` vs `{baseline.experiment_id}`: {delta}")

    lines.extend([""])
    if workspace_type == "system_comparison":
        lines.extend(["## Reference-System View", ""])
        for entry in entries:
            comparison = entry.comparison_summary
            lines.append(
                "- "
                f"`{entry.experiment_id}` candidate survival "
                f"{comparison['candidate_survival_rate']:.3f} vs reference "
                f"{comparison['reference_survival_rate']:.3f}; "
                f"mean trajectory distance {comparison['mean_trajectory_distance']['mean']:.3f}; "
                f"final vitality delta {comparison['final_vitality_delta']['mean']:.3f}"
            )
    else:
        lines.extend(["## Baseline Comparison View", ""])
        for entry in entries:
            comparison = entry.comparison_summary
            lines.append(
                "- "
                f"`{entry.experiment_id}` current survival "
                f"{comparison['candidate_survival_rate']:.3f} vs baseline "
                f"{comparison['reference_survival_rate']:.3f}; "
                f"mean trajectory distance {comparison['mean_trajectory_distance']['mean']:.3f}; "
                f"final vitality delta {comparison['final_vitality_delta']['mean']:.3f}"
            )

    lines.extend(["", "## Experiment Notes", ""])
    for entry in entries:
        lines.append(f"### {entry.title} (`{entry.experiment_id}`)")
        lines.append("")
        lines.append(f"- Measurement directory: `{entry.measurement_dir}`")
        lines.append(f"- Candidate experiment: `{entry.candidate_experiment_id}`")
        lines.append(f"- Reference experiment: `{entry.reference_experiment_id}`")
        if entry.hypothesis:
            lines.append("- Hypotheses:")
            for item in entry.hypothesis:
                lines.append(f"  - {item}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_table(entries: list[ExperimentSeriesAggregateEntry]) -> list[str]:
    lines = [
        "| Experiment | Death rate | Mean vitality | Gain/step | Energy eff. | Unique cells | Candidate surv. | Reference surv. |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for entry in entries:
        metrics = entry.behavior_metrics["standard_metrics"]
        comparison = entry.comparison_summary
        lines.append(
            "| "
            f"`{entry.experiment_id}` | "
            f"{entry.run_summary['death_rate']:.3f} | "
            f"{entry.run_summary['mean_final_vitality']:.3f} | "
            f"{metrics['resource_gain_per_step']['mean']:.3f} | "
            f"{metrics['net_energy_efficiency']['mean']:.3f} | "
            f"{metrics['unique_cells_visited']['mean']:.3f} | "
            f"{comparison['candidate_survival_rate']:.3f} | "
            f"{comparison['reference_survival_rate']:.3f} |"
        )
    return lines


def _delta_line(
    current: ExperimentSeriesAggregateEntry,
    reference: ExperimentSeriesAggregateEntry,
) -> str:
    current_metrics = current.behavior_metrics["standard_metrics"]
    reference_metrics = reference.behavior_metrics["standard_metrics"]
    death_delta = current.run_summary["death_rate"] - reference.run_summary["death_rate"]
    efficiency_delta = (
        current_metrics["net_energy_efficiency"]["mean"]
        - reference_metrics["net_energy_efficiency"]["mean"]
    )
    cells_delta = (
        current_metrics["unique_cells_visited"]["mean"]
        - reference_metrics["unique_cells_visited"]["mean"]
    )
    return (
        f"death_rate {death_delta:+.3f}, "
        f"net_energy_efficiency {efficiency_delta:+.3f}, "
        f"unique_cells_visited {cells_delta:+.3f}"
    )
