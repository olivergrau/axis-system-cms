"""Workspace-aware run-summary target resolution."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class WorkspaceRunSummaryTarget(BaseModel, frozen=True):
    """Resolved run-summary target for a workspace."""

    experiment_id: str
    run_id: str
    role: str | None = None
    run_notes: str | None = None


def resolve_run_summary_target(
    workspace_path: Path,
    *,
    role: str | None = None,
    experiment: str | None = None,
    run: str | None = None,
) -> WorkspaceRunSummaryTarget:
    """Resolve a workspace result into one concrete run.

    Auto-resolution is role-aware for comparison/development workspaces and
    defaults to the latest manifest-declared result for single-system
    workspaces. Point outputs resolve to their primary run automatically.
    Sweep outputs require explicit run selection.
    """
    from axis.framework.persistence import ExperimentRepository
    from axis.framework.workspaces.types import load_manifest

    ws = Path(workspace_path)
    manifest = load_manifest(ws)
    repo = ExperimentRepository(ws / "results")
    experiments = repo.list_experiments()

    if not experiments:
        raise ValueError(
            "No execution results found in workspace. "
            "Run 'axis workspaces run' first."
        )

    if run and not experiment:
        raise ValueError(
            "--run requires --experiment because run IDs are scoped to an experiment."
        )

    if experiment:
        if experiment not in experiments:
            raise ValueError(
                f"Experiment '{experiment}' not found in workspace results. "
                f"Available: {experiments}"
            )
        run_id = _resolve_run_for_summary(
            repo, experiment, explicit_run=run,
        )
        notes = _resolve_run_notes(manifest, experiment, role=role)
        return WorkspaceRunSummaryTarget(
            experiment_id=experiment,
            run_id=run_id,
            role=role,
            run_notes=notes,
        )

    workspace_type = manifest.workspace_type.value
    if workspace_type == "single_system":
        if role:
            raise ValueError(
                "single_system workspaces do not use --role for run-summary."
            )
        target = _resolve_latest_single_system(repo, manifest, experiments)
        return WorkspaceRunSummaryTarget(
            experiment_id=target[0],
            run_id=target[1],
            role="system_under_test",
            run_notes=target[2],
        )

    if workspace_type == "system_comparison":
        if role not in {"reference", "candidate"}:
            raise ValueError(
                "system_comparison run-summary requires --role "
                "reference or --role candidate."
            )
        target = _resolve_latest_for_role(
            repo, manifest, experiments, role,
        )
        return WorkspaceRunSummaryTarget(
            experiment_id=target[0],
            run_id=target[1],
            role=role,
            run_notes=target[2],
        )

    if workspace_type == "system_development":
        if role not in {"baseline", "candidate"}:
            raise ValueError(
                "system_development run-summary requires --role "
                "baseline or --role candidate."
            )
        target = _resolve_development_role(repo, manifest, role)
        return WorkspaceRunSummaryTarget(
            experiment_id=target[0],
            run_id=target[1],
            role=role,
            run_notes=target[2],
        )

    raise ValueError(
        f"run-summary is not supported for workspace type '{workspace_type}'."
    )


def _resolve_latest_single_system(
    repo,
    manifest,
    experiments: list[str],
) -> tuple[str, str, str | None]:
    from axis.framework.workspaces.types import result_entry_notes, result_entry_path

    if not manifest.primary_results:
        raise ValueError(
            "No primary_results recorded in workspace manifest. "
            "Run 'axis workspaces run' first."
        )

    for entry in reversed(manifest.primary_results):
        path_str = result_entry_path(entry)
        eid = _extract_eid(path_str)
        if not eid or eid not in experiments:
            continue
        return eid, _resolve_run_for_summary(repo, eid), result_entry_notes(entry)

    raise ValueError(
        "No manifest-declared results found in workspace results. "
        "Run 'axis workspaces run' first."
    )


def _resolve_latest_for_role(
    repo,
    manifest,
    experiments: list[str],
    role: str,
) -> tuple[str, str, str | None]:
    from axis.framework.workspaces.compare_resolution import (
        _resolve_by_system,
        _resolve_latest_by_role,
    )

    resolved = _resolve_latest_by_role(repo, manifest, experiments, role)
    if resolved is not None:
        return resolved[0], resolved[1], _resolve_run_notes(
            manifest, resolved[0], role=role,
        )

    target_system = (
        manifest.reference_system if role == "reference"
        else manifest.candidate_system
    )
    if not target_system:
        raise ValueError(
            f"Workspace manifest does not declare the system for role '{role}'."
        )
    fallback = _resolve_by_system(repo, experiments, target_system, role)
    return fallback[0], fallback[1], _resolve_run_notes(
        manifest, fallback[0], role=role,
    )


def _resolve_development_role(
    repo,
    manifest,
    role: str,
) -> tuple[str, str, str | None]:
    result_path: str | None = None
    if role == "baseline":
        if manifest.baseline_results:
            result_path = manifest.baseline_results[-1]
    elif role == "candidate":
        result_path = (
            manifest.current_candidate_result
            or (manifest.candidate_results[-1] if manifest.candidate_results else None)
        )

    if not result_path:
        raise ValueError(
            f"No {role} result available in workspace. "
            "Run the corresponding workspace side first."
        )

    eid = _extract_eid(result_path)
    if not eid:
        raise ValueError(f"Cannot parse result path: {result_path}")
    return eid, _resolve_run_for_summary(repo, eid), _resolve_run_notes(
        manifest, eid, role=role,
    )


def _extract_eid(path_str: str) -> str | None:
    parts = path_str.split("/")
    if len(parts) >= 2:
        return parts[1]
    return None


def _resolve_run_notes(
    manifest,
    experiment_id: str,
    *,
    role: str | None = None,
) -> str | None:
    from axis.framework.workspaces.types import result_entry_notes, result_entry_path

    result_path = f"results/{experiment_id}"
    entries = manifest.primary_results or []

    if role is not None:
        for entry in reversed(entries):
            if result_entry_path(entry) != result_path:
                continue
            entry_role = getattr(entry, "role", None)
            if entry_role == role:
                return result_entry_notes(entry)

    for entry in reversed(entries):
        if result_entry_path(entry) == result_path:
            return result_entry_notes(entry)
    return None


def _resolve_run_for_summary(
    repo,
    experiment_id: str,
    *,
    explicit_run: str | None = None,
) -> str:
    from axis.framework.experiment_output import (
        PointExperimentOutput,
        SweepExperimentOutput,
        load_experiment_output,
    )

    exp_output = load_experiment_output(repo, experiment_id)

    if getattr(exp_output, "trace_mode", None) == "light":
        raise ValueError(
            f"Experiment '{experiment_id}' was executed in light trace mode. "
            "run-summary currently supports replay-backed run outputs only."
        )

    if isinstance(exp_output, SweepExperimentOutput):
        if not explicit_run:
            raise ValueError(
                f"Experiment '{experiment_id}' is a sweep (OFAT) output. "
                f"run-summary requires explicit run selection for sweep outputs. "
                f"Use --experiment {experiment_id} --run <run-id>. "
                f"Available runs: {list(exp_output.run_ids)}"
            )
        if explicit_run not in exp_output.run_ids:
            raise ValueError(
                f"Run '{explicit_run}' not found in experiment "
                f"'{experiment_id}'. Available: {list(exp_output.run_ids)}"
            )
        return explicit_run

    if isinstance(exp_output, PointExperimentOutput):
        if explicit_run and explicit_run != exp_output.primary_run_id:
            raise ValueError(
                f"Point output '{experiment_id}' only has primary run "
                f"'{exp_output.primary_run_id}', not '{explicit_run}'."
            )
        return exp_output.primary_run_id

    raise ValueError(
        f"Experiment '{experiment_id}': unrecognized output type "
        f"'{exp_output.output_form}'."
    )
