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

    series_id: str
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
        series_id: str,
        override_guard: bool = False,
        update_notes: bool = False,
        catalogs: dict | None = None,
        progress: object | None = None,
    ) -> WorkspaceExperimentSeriesServiceResult:
        """Execute all enabled experiments declared in one registered series."""
        from axis.framework.persistence import ExperimentRepository
        from axis.framework.workspaces.compare import compare_workspace
        from axis.framework.metrics import load_or_compute_run_behavior_metrics
        from axis.framework.workspaces.comparison_envelope import (
            WorkspaceComparisonEnvelope,
        )
        from axis.framework.workspaces.config_materialization import (
            materialize_candidate_config,
            materialize_role_config,
            resolve_base_config_paths,
        )
        from axis.framework.workspaces.execute import execute_workspace
        from axis.framework.workspaces.series_paths import resolve_series_paths
        from axis.framework.workspaces.sync import (
            sync_manifest_after_series_compare,
            sync_manifest_after_series_run,
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

        series_paths = resolve_series_paths(ws, series_id=series_id)
        series_paths.results_root.mkdir(parents=True, exist_ok=True)
        series_paths.measurements_root.mkdir(parents=True, exist_ok=True)
        series_paths.comparisons_root.mkdir(parents=True, exist_ok=True)
        series = self._load_experiment_series_fn(ws, series_id=series_id)
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
        measurement_root_dir = str(series_paths.measurements_root.relative_to(ws))
        workflow = manifest.measurement_workflow
        temp_root = ws / ".axis_tmp" / "experiment_series" / series_id / _series_run_id()
        repo = ExperimentRepository(series_paths.results_root)

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
                measurement_number = _next_measurement_number(
                    _ensure_measurement_root(series_paths.measurements_root),
                    workflow.experiment_dir_pattern if workflow else "experiment_{number}",
                )
                effective_workflow = workflow
                if effective_workflow is None:
                    from axis.framework.workspaces.types import MeasurementWorkflowConfig
                    effective_workflow = MeasurementWorkflowConfig()
                measurement_dir_path = (
                    series_paths.measurements_root /
                    effective_workflow.experiment_dir_pattern.format(number=measurement_number)
                )
                measurement_dir_path.mkdir(parents=True, exist_ok=False)
                exec_results = execute_workspace(
                    ws,
                    config_overrides_by_role={"candidate": materialized.temp_config_path},
                    progress=progress,
                    progress_description_prefix=progress_prefix,
                    show_workspace_progress=False,
                    results_root=series_paths.results_root,
                )
                run_notes = experiment.notes or experiment.title
                for er in exec_results:
                    config = er.experiment_result.experiment_config
                    execution = getattr(config, "execution", None)
                    sync_manifest_after_series_run(
                        ws,
                        series_id=series_id,
                        result_path=str(
                            (series_paths.results_root / er.experiment_result.experiment_id).relative_to(ws)
                        ),
                        role=er.role,
                        output_form="point" if config.experiment_type.value == "single_run" else "sweep",
                        trace_mode=getattr(execution, "trace_mode", None),
                        system_type=config.system_type,
                        primary_run_id="run-0000" if config.experiment_type.value == "single_run" else None,
                        baseline_run_id="run-0000" if config.experiment_type.value != "single_run" else None,
                        run_notes=run_notes,
                        label=label,
                        measurement_path=str(measurement_dir_path.relative_to(ws)),
                    )
                by_role = {er.role: er.experiment_result.experiment_id for er in exec_results}
                reference_experiment_id = by_role["reference"]
                current_experiment_id = by_role["candidate"]
                compare_result_envelope, comparison_output_path = compare_workspace(
                    ws,
                    reference_experiment=reference_experiment_id,
                    candidate_experiment=current_experiment_id,
                    extension_catalog=(
                        catalogs.get("comparison_extensions") if catalogs else None
                    ),
                    progress=progress,
                    progress_description=f"{progress_prefix} | Episode comparisons",
                    results_root=series_paths.results_root,
                    comparisons_root=series_paths.comparisons_root,
                )
                sync_manifest_after_series_compare(
                    ws,
                    series_id=series_id,
                    comparison_output_path=comparison_output_path,
                )
                comparison_number = compare_result_envelope.comparison_number
                tokens = {
                    "label": label,
                    "number": measurement_number,
                    "role": effective_workflow.default_run_summary_role,
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
                    comparison_number=comparison_number,
                    comparison_log_path=comparison_log_path,
                    run_summary_role=None,
                    run_summary_log_path=run_summary_log_path,
                    run_summary_experiment_id=current_experiment_id,
                    run_summary_run_id="run-0000",
                    catalogs=catalogs,
                    comparison_output_path=comparison_output_path,
                    results_root=series_paths.results_root,
                )
                run_summary_role = effective_workflow.default_run_summary_role
                measurement_dir = str(measurement_dir_path.relative_to(ws))
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
                    _ensure_measurement_root(series_paths.measurements_root),
                    workflow.experiment_dir_pattern if workflow else "experiment_{number}",
                )
                effective_workflow = workflow
                if effective_workflow is None:
                    from axis.framework.workspaces.types import MeasurementWorkflowConfig
                    effective_workflow = MeasurementWorkflowConfig()
                measurement_dir_path = (
                    series_paths.measurements_root /
                    effective_workflow.experiment_dir_pattern.format(number=measurement_number)
                )
                measurement_dir_path.mkdir(parents=True, exist_ok=False)
                exec_results = execute_workspace(
                    ws,
                    config_overrides_by_role={
                        "system_under_test": materialized.temp_config_path,
                    },
                    progress=progress,
                    progress_description_prefix=progress_prefix,
                    show_workspace_progress=False,
                    results_root=series_paths.results_root,
                )
                run_notes = experiment.notes or experiment.title
                for er in exec_results:
                    config = er.experiment_result.experiment_config
                    execution = getattr(config, "execution", None)
                    sync_manifest_after_series_run(
                        ws,
                        series_id=series_id,
                        result_path=str(
                            (series_paths.results_root / er.experiment_result.experiment_id).relative_to(ws)
                        ),
                        role=er.role,
                        output_form="point" if config.experiment_type.value == "single_run" else "sweep",
                        trace_mode=getattr(execution, "trace_mode", None),
                        system_type=config.system_type,
                        primary_run_id="run-0000" if config.experiment_type.value == "single_run" else None,
                        baseline_run_id="run-0000" if config.experiment_type.value != "single_run" else None,
                        run_notes=run_notes,
                        label=label,
                        measurement_path=str(measurement_dir_path.relative_to(ws)),
                    )
                current_experiment_id = exec_results[0].experiment_result.experiment_id
                baseline_experiment_id = current_experiment_id if not executed_ids else aggregate_entries[0].candidate_experiment_id
                compare_result_envelope, comparison_output_path = compare_workspace(
                    ws,
                    reference_experiment=baseline_experiment_id,
                    candidate_experiment=current_experiment_id,
                    extension_catalog=(
                        catalogs.get("comparison_extensions") if catalogs else None
                    ),
                    progress=progress,
                    progress_description=f"{progress_prefix} | Episode comparisons",
                    results_root=series_paths.results_root,
                    comparisons_root=series_paths.comparisons_root,
                )
                sync_manifest_after_series_compare(
                    ws,
                    series_id=series_id,
                    comparison_output_path=comparison_output_path,
                )
                comparison_number = compare_result_envelope.comparison_number
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
                    comparison_number=comparison_number,
                    comparison_log_path=comparison_log_path,
                    run_summary_role=None,
                    run_summary_log_path=run_summary_log_path,
                    run_summary_experiment_id=current_experiment_id,
                    run_summary_run_id="run-0000",
                    catalogs=catalogs,
                    comparison_output_path=comparison_output_path,
                    results_root=series_paths.results_root,
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
            notes_path = series_paths.notes_path
            notes_path.parent.mkdir(parents=True, exist_ok=True)
            notes_path.write_text(
                render_notes_scaffold(
                    series_title=series.title,
                    experiments=notes_experiments,
                ),
                encoding="utf-8",
            )
            notes_updated = True

        return WorkspaceExperimentSeriesServiceResult(
            series_id=series_id,
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
