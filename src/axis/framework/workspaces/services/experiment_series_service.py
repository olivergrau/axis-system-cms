"""Workspace experiment-series orchestration service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WorkspaceExperimentSeriesServiceResult:
    """Summary of one completed workspace experiment series execution."""

    series_title: str | None
    executed_experiment_count: int
    executed_experiment_ids: list[str]
    measurement_directories: list[str]
    series_summary_markdown_path: str
    series_summary_json_path: str
    series_metrics_csv_path: str
    series_manifest_json_path: str
    notes_updated: bool


class WorkspaceExperimentSeriesService:
    """Execute a workspace-local experiment series end to end."""

    def __init__(
        self,
        measurement_service: object,
        load_manifest_fn,
        load_experiment_series_fn,
        export_measurement_reports_fn,
    ) -> None:
        self._measurement_service = measurement_service
        self._load_manifest_fn = load_manifest_fn
        self._load_experiment_series_fn = load_experiment_series_fn
        self._export_measurement_reports_fn = export_measurement_reports_fn

    def run_series(
        self,
        workspace_path: Path,
        *,
        allow_world_changes: bool = False,
        override_guard: bool = False,
        update_notes: bool = False,
        catalogs: dict | None = None,
        progress: object | None = None,
    ) -> WorkspaceExperimentSeriesServiceResult:
        """Execute all enabled experiments declared in ``experiment.yaml``."""
        from axis.framework.metrics import load_or_compute_run_behavior_metrics
        from axis.framework.persistence import ExperimentRepository
        from axis.framework.workspaces.comparison_envelope import (
            WorkspaceComparisonEnvelope,
        )
        from axis.framework.workspaces.config_materialization import (
            materialize_candidate_config,
            materialize_role_config,
            resolve_base_config_paths,
        )
        from axis.framework.workspaces.services.measurement_service import (
            _next_measurement_number,
        )
        from axis.framework.workspaces.series_notes import (
            SeriesNotesExperiment,
            render_notes_scaffold,
        )
        from axis.framework.workspaces.series_reporting import (
            build_aggregate_entry,
            render_series_outputs,
        )
        from axis.framework.workspaces.types import WorkspaceType

        ws = Path(workspace_path)
        manifest = self._load_manifest_fn(ws)
        if manifest.workspace_type not in (
            WorkspaceType.SYSTEM_COMPARISON,
            WorkspaceType.SINGLE_SYSTEM,
        ):
            raise ValueError(
                "workspaces run-series is only supported for "
                "system_comparison and single_system workspaces. "
                f"Workspace '{manifest.workspace_id}' has type "
                f"'{manifest.workspace_type.value}'."
            )

        series = self._load_experiment_series_fn(ws)
        series_workspace_type = getattr(
            series.workspace_type, "value", series.workspace_type
        )
        if str(series_workspace_type) != manifest.workspace_type.value:
            raise ValueError(
                "Experiment series workspace_type does not match workspace.yaml: "
                f"series='{series_workspace_type}' workspace='{manifest.workspace_type.value}'."
            )

        base_configs = resolve_base_config_paths(ws, manifest)
        if series.base_configs is not None:
            if series.base_configs.reference is not None:
                base_configs["reference"] = series.base_configs.reference
            if series.base_configs.candidate is not None:
                base_configs["candidate"] = series.base_configs.candidate
        measurement_root_dir = (
            manifest.measurement_workflow.root_dir
            if manifest.measurement_workflow is not None
            else "measurements"
        )
        workflow = manifest.measurement_workflow
        temp_root = ws / ".axis_tmp" / "experiment_series" / _series_run_id()
        repo = ExperimentRepository(ws / "results")

        aggregate_entries = []
        executed_ids: list[str] = []
        measurement_directories: list[str] = []
        notes_experiments: list[SeriesNotesExperiment] = []
        enabled_experiments = [
            experiment for experiment in series.experiments if experiment.enabled
        ]

        for experiment_index, experiment in enumerate(enabled_experiments, start=1):
            label_template = series.defaults.labels.measurement_label_pattern
            label = (
                experiment.label
                if experiment.label is not None
                else label_template.format(experiment_id=experiment.id)
            )
            progress_prefix = (
                f"{experiment_index}/{len(enabled_experiments)} {experiment.id}"
            )
            if manifest.workspace_type == WorkspaceType.SYSTEM_COMPARISON:
                materialized = materialize_candidate_config(
                    ws,
                    source_config_path=base_configs["candidate"],
                    candidate_config_delta=experiment.candidate_config_delta,
                    temp_dir=temp_root,
                    experiment_id=experiment.id,
                )
                measurement_result = self._measurement_service.measure(
                    ws,
                    label=label,
                    config_overrides_by_role={"candidate": materialized.temp_config_path},
                    allow_world_changes=allow_world_changes,
                    override_guard=override_guard,
                    run_notes=experiment.notes or experiment.title,
                    extension_catalog=(
                        catalogs.get("comparison_extensions") if catalogs else None
                    ),
                    progress=progress,
                    progress_description_prefix=progress_prefix,
                    show_workspace_progress=False,
                )
                self._export_measurement_reports_fn(
                    ws,
                    comparison_number=measurement_result.comparison_number,
                    comparison_log_path=measurement_result.comparison_log_path,
                    run_summary_role=measurement_result.run_summary_role,
                    run_summary_log_path=measurement_result.run_summary_log_path,
                    allow_world_changes=allow_world_changes,
                    catalogs=catalogs,
                )
                current_experiment_id = measurement_result.run_experiments_by_role["candidate"]
                comparison_output_path = measurement_result.comparison_output_path
                comparison_log_path = measurement_result.comparison_log_path
                run_summary_log_path = measurement_result.run_summary_log_path
                run_summary_role = measurement_result.run_summary_role
                measurement_dir = measurement_result.measurement_dir
            else:
                materialized = materialize_role_config(
                    ws,
                    role="system_under_test",
                    source_config_path=(
                        series.base_configs.system_under_test
                        if series.base_configs is not None
                        and series.base_configs.system_under_test is not None
                        else base_configs["system_under_test"]
                    ),
                    config_delta=experiment.candidate_config_delta,
                    temp_dir=temp_root,
                    experiment_id=experiment.id,
                )
                measurement_number = _next_measurement_number(
                    _ensure_measurement_root(ws / measurement_root_dir),
                    workflow.experiment_dir_pattern if workflow else "experiment_{number}",
                )
                effective_workflow = workflow
                if effective_workflow is None:
                    from axis.framework.workspaces.types import MeasurementWorkflowConfig
                    effective_workflow = MeasurementWorkflowConfig()
                measurement_dir_path = (
                    ws / effective_workflow.root_dir /
                    effective_workflow.experiment_dir_pattern.format(number=measurement_number)
                )
                measurement_dir_path.mkdir(parents=True, exist_ok=False)
                run_results = self._measurement_service._run_service.execute(
                    ws,
                    config_overrides_by_role={
                        "system_under_test": materialized.temp_config_path,
                    },
                    allow_world_changes=allow_world_changes,
                    override_guard=override_guard,
                    run_notes=experiment.notes or experiment.title,
                    progress=progress,
                    progress_description_prefix=progress_prefix,
                    show_workspace_progress=False,
                )
                current_experiment_id = run_results[0].experiment_id
                baseline_experiment_id = current_experiment_id if not executed_ids else aggregate_entries[0].candidate_experiment_id
                compare_result = self._measurement_service._compare_service.compare(
                    ws,
                    reference_experiment=baseline_experiment_id,
                    candidate_experiment=current_experiment_id,
                    allow_world_changes=allow_world_changes,
                    extension_catalog=(
                        catalogs.get("comparison_extensions") if catalogs else None
                    ),
                    progress=progress,
                    progress_description=f"{progress_prefix} | Episode comparisons",
                )
                comparison_output_path = compare_result.output_path
                tokens = {
                    "label": label,
                    "number": measurement_number,
                    "role": "system_under_test",
                }
                comparison_log_path = str((
                    measurement_dir_path /
                    effective_workflow.comparison_log_pattern.format(**tokens)
                ).relative_to(ws))
                run_summary_log_path = str((
                    measurement_dir_path /
                    effective_workflow.run_summary_log_pattern.format(**tokens)
                ).relative_to(ws))
                self._export_measurement_reports_fn(
                    ws,
                    comparison_number=compare_result.comparison_number,
                    comparison_log_path=comparison_log_path,
                    run_summary_role=None,
                    run_summary_log_path=run_summary_log_path,
                    run_summary_experiment_id=current_experiment_id,
                    run_summary_run_id="run-0000",
                    allow_world_changes=allow_world_changes,
                    catalogs=catalogs,
                )
                run_summary_role = "system_under_test"
                measurement_dir = str(measurement_dir_path.relative_to(ws))

            primary_run_id = "run-0000"
            run_summary = repo.load_run_summary(current_experiment_id, primary_run_id)
            behavior_metrics = load_or_compute_run_behavior_metrics(
                repo, current_experiment_id, primary_run_id
            )
            envelope_path = ws / comparison_output_path
            comparison_envelope = WorkspaceComparisonEnvelope.model_validate(
                json.loads(envelope_path.read_text())
            )
            aggregate_entries.append(
                build_aggregate_entry(
                    experiment_id=experiment.id,
                    label=label,
                    title=experiment.title,
                    hypothesis=list(experiment.hypothesis or []),
                    measurement_dir=measurement_dir,
                    comparison_output_path=comparison_output_path,
                    comparison_log_path=comparison_log_path,
                    run_summary_log_path=run_summary_log_path,
                    comparison_envelope=comparison_envelope,
                    run_summary=run_summary,
                    behavior_metrics=behavior_metrics,
                )
            )
            executed_ids.append(experiment.id)
            measurement_directories.append(measurement_dir)
            notes_experiments.append(
                SeriesNotesExperiment(
                    experiment_id=experiment.id,
                    title=experiment.title,
                    measurement_dir=measurement_dir,
                    hypothesis=list(experiment.hypothesis or []),
                )
            )

        aggregate_paths = render_series_outputs(
            ws,
            workspace_type=manifest.workspace_type.value,
            series_title=series.title,
            series_description=series.description,
            measurement_root_dir=measurement_root_dir,
            entries=aggregate_entries,
        )

        notes_updated = False
        if update_notes and series.defaults.notes.scaffold_notes:
            notes_path = ws / "notes.md"
            notes_path.write_text(
                render_notes_scaffold(
                    series_title=series.title,
                    experiments=notes_experiments,
                ),
                encoding="utf-8",
            )
            notes_updated = True

        return WorkspaceExperimentSeriesServiceResult(
            series_title=series.title,
            executed_experiment_count=len(executed_ids),
            executed_experiment_ids=executed_ids,
            measurement_directories=measurement_directories,
            series_summary_markdown_path=aggregate_paths["series_summary_markdown_path"],
            series_summary_json_path=aggregate_paths["series_summary_json_path"],
            series_metrics_csv_path=aggregate_paths["series_metrics_csv_path"],
            series_manifest_json_path=aggregate_paths["series_manifest_json_path"],
            notes_updated=notes_updated,
        )


def _series_run_id() -> str:
    """Return a filesystem-safe UTC timestamp for temp series artifacts."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _ensure_measurement_root(path: Path) -> Path:
    """Create the measurement root directory if needed and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path
