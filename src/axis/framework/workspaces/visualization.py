"""Workspace-aware visualization target resolution (WP-07).

Uses the Experiment Output abstraction to resolve run IDs from
experiment outputs.  Point outputs use primary_run_id; sweep outputs
require explicit selection.
"""

from __future__ import annotations

from pathlib import Path


def resolve_visualization_target(
    workspace_path: Path,
    episode: int,
    role: str | None = None,
    experiment: str | None = None,
    run: str | None = None,
) -> tuple[str, str, int]:
    """Resolve a workspace into visualization coordinates.

    Uses the Experiment Output abstraction to resolve run IDs.
    Point outputs use the primary run; sweep outputs require
    explicit run selection via ``--run``.

    Parameters
    ----------
    workspace_path:
        Path to the workspace root.
    episode:
        Episode index (1-based, as per CLI convention).
    role:
        Optional role filter (``reference`` or ``candidate``) for
        system_comparison workspaces.
    experiment:
        Optional explicit experiment ID.  If provided, it must exist
        in the workspace's results.  If omitted, the resolver picks
        a single unambiguous experiment (filtered by role if given).
    run:
        Optional explicit run ID.  Required for sweep outputs.

    Returns
    -------
    Tuple of (experiment_id, run_id, episode_index) suitable for
    passing to the existing visualization launch infrastructure.

    Raises
    ------
    ValueError
        If resolution is ambiguous and no ``--experiment`` flag was
        provided, or the specified experiment doesn't exist,
        or a sweep output is selected without explicit run selection.
    """
    from axis.framework.persistence import ExperimentRepository
    from axis.framework.workspaces.types import load_manifest

    ws = Path(workspace_path)
    manifest = load_manifest(ws)
    repo = ExperimentRepository(ws / "results")

    experiments = repo.list_experiments()
    if not experiments:
        raise ValueError(
            f"No execution results in workspace "
            f"'{manifest.workspace_id}'. Run 'axis workspaces run' first."
        )

    # Explicit experiment ID provided.
    if experiment:
        if experiment not in experiments:
            raise ValueError(
                f"Experiment '{experiment}' not found in workspace results. "
                f"Available: {experiments}"
            )
        rid = _resolve_run_for_viz(repo, experiment, explicit_run=run)
        return experiment, rid, episode

    # Auto-resolve: filter by role if applicable.
    candidates = experiments
    if role:
        # For development workspaces, use manifest fields to resolve
        if role == "baseline" and manifest.baseline_results:
            for rpath in manifest.baseline_results:
                eid = _extract_eid(rpath)
                if eid and eid in experiments:
                    rid = _resolve_run_for_viz(repo, eid, explicit_run=run)
                    return eid, rid, episode

        if role == "candidate" and manifest.current_candidate_result:
            eid = _extract_eid(manifest.current_candidate_result)
            if eid and eid in experiments:
                rid = _resolve_run_for_viz(repo, eid, explicit_run=run)
                return eid, rid, episode

        # Match experiments by the system_type declared for this role.
        target_system = None
        if role == "reference":
            target_system = manifest.reference_system
        elif role == "candidate":
            target_system = manifest.candidate_system
        elif role == "system_under_test":
            target_system = manifest.system_under_test

        if target_system:
            filtered = []
            for eid in experiments:
                try:
                    meta = repo.load_experiment_metadata(eid)
                    if meta.system_type == target_system:
                        filtered.append(eid)
                except (FileNotFoundError, ValueError):
                    continue
            candidates = filtered

    if not candidates:
        raise ValueError(
            f"No experiments matching role '{role}' found in workspace results."
        )

    if len(candidates) == 1:
        eid = candidates[0]
        rid = _resolve_run_for_viz(repo, eid, explicit_run=run)
        return eid, rid, episode

    # Multiple candidates — try manifest ordering.
    if manifest.primary_results and len(manifest.primary_results) >= 1:
        from axis.framework.workspaces.types import result_entry_path
        ordered = []
        for entry in manifest.primary_results:
            path_str = result_entry_path(entry)
            eid = _extract_eid(path_str)
            if eid and eid in candidates and eid not in ordered:
                ordered.append(eid)
        if role == "reference" and ordered:
            eid = ordered[0]
            rid = _resolve_run_for_viz(repo, eid, explicit_run=run)
            return eid, rid, episode
        elif role == "candidate" and len(ordered) >= 2:
            eid = ordered[1]
            rid = _resolve_run_for_viz(repo, eid, explicit_run=run)
            return eid, rid, episode

    # Still ambiguous — annotate with output form for easier selection.
    labeled = []
    for eid in candidates:
        form = "?"
        if manifest.primary_results:
            from axis.framework.workspaces.types import result_entry_path
            for entry in manifest.primary_results:
                entry_path = result_entry_path(entry)
                if _extract_eid(entry_path) == eid:
                    form = getattr(entry, "output_form", None) or "?"
                    break
        labeled.append(f"{eid} [{form}]")
    raise ValueError(
        f"Multiple experiments found in workspace results: {labeled}. "
        f"Use --experiment <id> to select one."
    )


def _extract_eid(path_str: str) -> str | None:
    """Extract experiment ID from a result path.

    Handles both formats:
    - ``results/<eid>`` (experiment-root)
    - ``results/<eid>/runs/<rid>`` (legacy run-level)
    """
    parts = path_str.split("/")
    if len(parts) >= 2:
        return parts[1]
    return None


def _resolve_run_for_viz(
    repo, experiment_id: str, *, explicit_run: str | None = None,
) -> str:
    """Resolve the visualization run from an experiment output.

    For point outputs, returns primary_run_id.
    For sweep outputs, requires an explicit run selection.
    """
    from axis.framework.experiment_output import (
        ExperimentOutputForm,
        PointExperimentOutput,
        SweepExperimentOutput,
        load_experiment_output,
    )

    exp_output = load_experiment_output(repo, experiment_id)

    if getattr(exp_output, "trace_mode", None) == "light":
        raise ValueError(
            f"Experiment '{experiment_id}' was executed in light trace mode and "
            "does not provide replay-compatible artifacts for visualization."
        )

    if isinstance(exp_output, SweepExperimentOutput):
        if not explicit_run:
            raise ValueError(
                f"Experiment '{experiment_id}' is a sweep (OFAT) output. "
                f"Sweep visualization requires explicit run selection. "
                f"Use --experiment {experiment_id} --run <run-id> to select "
                f"a specific run. Available runs: "
                f"{list(exp_output.run_ids)}"
            )
        if explicit_run not in exp_output.run_ids:
            raise ValueError(
                f"Run '{explicit_run}' not found in experiment "
                f"'{experiment_id}'. Available: {list(exp_output.run_ids)}"
            )
        return explicit_run

    if isinstance(exp_output, PointExperimentOutput):
        return exp_output.primary_run_id

    raise ValueError(
        f"Experiment '{experiment_id}': unrecognized output type "
        f"'{exp_output.output_form}'."
    )
