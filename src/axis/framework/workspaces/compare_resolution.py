"""Workspace comparison target resolution (WP-08).

Resolves reference and candidate experiments from the workspace-local
repository (``<workspace>/results/``).  Uses the Experiment Output
abstraction to resolve run IDs from experiment-root paths.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from axis.framework.workspaces.types import load_manifest


class WorkspaceCompareTarget(BaseModel, frozen=True):
    """One side of a workspace comparison."""

    experiment_id: str
    run_id: str
    role: str  # reference or candidate


class WorkspaceComparisonPlan(BaseModel, frozen=True):
    """Resolved comparison plan for a workspace."""

    reference: WorkspaceCompareTarget
    candidate: WorkspaceCompareTarget


def resolve_comparison_targets(
    workspace_path: Path,
    reference_experiment: str | None = None,
    candidate_experiment: str | None = None,
) -> WorkspaceComparisonPlan:
    """Resolve workspace artifacts into a comparison plan.

    Uses the Experiment Output abstraction to resolve run IDs.
    Only point-vs-point comparison is supported; sweep outputs
    on either side will be rejected explicitly.

    Parameters
    ----------
    workspace_path:
        Path to the workspace root.
    reference_experiment:
        Explicit experiment ID for the reference side.
    candidate_experiment:
        Explicit experiment ID for the candidate side.

    Raises
    ------
    ValueError
        If the workspace has no runs, the workspace type does not
        support comparison, or resolution is ambiguous.
    """
    from axis.framework.persistence import ExperimentRepository
    from axis.framework.workspaces.handler import get_handler

    ws = Path(workspace_path)
    manifest = load_manifest(ws)

    results_dir = ws / "results"
    if not results_dir.is_dir():
        raise ValueError(
            "No results directory found in workspace. "
            "Run 'axis workspaces run' first."
        )

    repo = ExperimentRepository(results_dir)
    experiments = repo.list_experiments()

    if not experiments:
        raise ValueError(
            "No execution results found in workspace. "
            "Run 'axis workspaces run' first."
        )

    # --- Resolve explicit overrides first (generic for all types) ---
    if reference_experiment and candidate_experiment:
        ref_eid, ref_rid = _validate_explicit(
            repo, experiments, reference_experiment, "reference")
        cand_eid, cand_rid = _validate_explicit(
            repo, experiments, candidate_experiment, "candidate")
        return WorkspaceComparisonPlan(
            reference=WorkspaceCompareTarget(
                experiment_id=ref_eid, run_id=ref_rid, role="reference"),
            candidate=WorkspaceCompareTarget(
                experiment_id=cand_eid, run_id=cand_rid, role="candidate"),
        )

    if reference_experiment or candidate_experiment:
        raise ValueError(
            "Both --reference-experiment and --candidate-experiment "
            "must be provided together, or neither."
        )

    # --- Auto-resolve (delegated to type-specific handler) ---
    handler = get_handler(manifest.workspace_type)
    return handler.resolve_comparison_targets(ws, manifest, repo, experiments)


def _resolve_run_from_output(repo, experiment_id: str) -> str:
    """Resolve the primary run ID from an experiment using the output abstraction.

    For point outputs, returns the primary_run_id.
    Sweep outputs are rejected — workspace comparison only supports point-vs-point.
    """
    from axis.framework.experiment_output import (
        ExperimentOutputForm,
        PointExperimentOutput,
        SweepExperimentOutput,
        load_experiment_output,
    )

    exp_output = load_experiment_output(repo, experiment_id)

    if isinstance(exp_output, SweepExperimentOutput):
        raise ValueError(
            f"Experiment '{experiment_id}' is a sweep (OFAT) output. "
            f"Workspace comparison only supports point-vs-point. "
            f"Use 'axis workspaces sweep-result' to inspect sweep outputs, "
            f"or 'axis compare' directly with explicit run IDs."
        )

    if isinstance(exp_output, PointExperimentOutput):
        return exp_output.primary_run_id

    raise ValueError(
        f"Experiment '{experiment_id}': unrecognized output type "
        f"'{exp_output.output_form}'."
    )


def _validate_explicit(
    repo, experiments: list[str], eid: str, role: str,
) -> tuple[str, str]:
    """Validate an explicitly provided experiment ID and resolve its run."""
    if eid not in experiments:
        raise ValueError(
            f"Experiment '{eid}' not found in workspace "
            f"results. Available: {experiments}"
        )
    rid = _resolve_run_from_output(repo, eid)
    return eid, rid


def _resolve_by_system(
    repo, experiments: list[str], target_system: str, role: str,
) -> tuple[str, str]:
    """Find the experiment matching a system type.

    If multiple experiments match, the last one (most recent) is used.
    Resolves run ID through the output abstraction.
    """
    matches: list[str] = []
    for eid in experiments:
        try:
            meta = repo.load_experiment_metadata(eid)
            if meta.system_type == target_system:
                runs = repo.list_runs(eid)
                if runs:
                    matches.append(eid)
        except (FileNotFoundError, ValueError):
            continue

    if not matches:
        raise ValueError(
            f"No experiments for {role} system '{target_system}' found "
            f"in workspace results. Run 'axis workspaces run' first."
        )
    # Use the most recent match (last in list).
    eid = matches[-1]
    rid = _resolve_run_from_output(repo, eid)
    return eid, rid


def _resolve_by_manifest_order(
    repo, manifest, experiments: list[str],
) -> "WorkspaceComparisonPlan":
    """Resolve when both sides use the same system_type.

    Filters ``primary_results`` to **point outputs only** so mixed
    point/sweep histories remain usable without introducing
    sweep comparison.  Uses first point output as reference, latest
    point output as candidate.

    Result paths are experiment-root (``results/<eid>``).
    """
    ordered_eids: list[str] = []

    # Filter primary_results to point outputs and extract experiment IDs.
    if manifest.primary_results:
        from axis.framework.workspaces.types import result_entry_path
        for entry in manifest.primary_results:
            # Only consider point outputs for comparison.
            entry_form = getattr(entry, "output_form", None)
            if entry_form and entry_form != "point":
                continue
            path_str = result_entry_path(entry)
            parts = path_str.split("/")
            if len(parts) >= 2:
                eid = parts[1]  # results/<eid>
                if eid in experiments and eid not in ordered_eids:
                    ordered_eids.append(eid)

    # Fall back to sorted experiment IDs if manifest didn't help.
    if len(ordered_eids) < 2:
        from axis.framework.experiment_output import load_experiment_output, PointExperimentOutput
        for eid in experiments:
            if eid in ordered_eids:
                continue
            try:
                out = load_experiment_output(repo, eid)
                if isinstance(out, PointExperimentOutput):
                    ordered_eids.append(eid)
            except (FileNotFoundError, ValueError):
                continue

    if len(ordered_eids) < 2:
        raise ValueError(
            "Need at least 2 point outputs in workspace results for "
            "comparison. Sweep outputs are not valid comparison targets — "
            "use 'axis workspaces sweep-result' to inspect sweep results."
        )

    ref_eid = ordered_eids[0]
    cand_eid = ordered_eids[-1]
    ref_rid = _resolve_run_from_output(repo, ref_eid)
    cand_rid = _resolve_run_from_output(repo, cand_eid)

    return WorkspaceComparisonPlan(
        reference=WorkspaceCompareTarget(
            experiment_id=ref_eid, run_id=ref_rid, role="reference"),
        candidate=WorkspaceCompareTarget(
            experiment_id=cand_eid, run_id=cand_rid, role="candidate"),
    )
