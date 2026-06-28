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
) -> tuple[str, str, int, Path]:
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
    Tuple of (experiment_id, run_id, episode_index, results_root)
    suitable for passing to the visualization launch infrastructure.

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
    repo_roots = _discover_workspace_results_roots(ws)
    experiment_locations = _discover_workspace_experiments(repo_roots)
    if not experiment_locations:
        raise ValueError(
            f"No execution results in workspace "
            f"'{manifest.workspace_id}'. Run 'axis workspaces run' first."
        )

    # Explicit experiment ID provided.
    if experiment:
        repo_root = experiment_locations.get(experiment)
        if repo_root is None:
            raise ValueError(
                f"Experiment '{experiment}' not found in workspace results. "
                f"Available: {sorted(experiment_locations)}"
            )
        repo = ExperimentRepository(repo_root)
        rid = _resolve_run_for_viz(repo, experiment, explicit_run=run)
        return experiment, rid, episode, repo_root

    # Auto-resolve: filter by role if applicable.
    candidates = list(experiment_locations)
    if role:
        # For development workspaces, use manifest fields to resolve
        if role == "baseline" and manifest.baseline_results:
            for rpath in manifest.baseline_results:
                eid = _extract_eid(rpath)
                if eid and eid in experiment_locations:
                    repo = ExperimentRepository(experiment_locations[eid])
                    rid = _resolve_run_for_viz(repo, eid, explicit_run=run)
                    return eid, rid, episode, experiment_locations[eid]

        if role == "candidate" and manifest.current_candidate_result:
            eid = _extract_eid(manifest.current_candidate_result)
            if eid and eid in experiment_locations:
                repo = ExperimentRepository(experiment_locations[eid])
                rid = _resolve_run_for_viz(repo, eid, explicit_run=run)
                return eid, rid, episode, experiment_locations[eid]

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
            for eid in candidates:
                try:
                    repo = ExperimentRepository(experiment_locations[eid])
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
        repo = ExperimentRepository(experiment_locations[eid])
        rid = _resolve_run_for_viz(repo, eid, explicit_run=run)
        return eid, rid, episode, experiment_locations[eid]

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
            repo = ExperimentRepository(experiment_locations[eid])
            rid = _resolve_run_for_viz(repo, eid, explicit_run=run)
            return eid, rid, episode, experiment_locations[eid]
        elif role == "candidate" and len(ordered) >= 2:
            eid = ordered[1]
            repo = ExperimentRepository(experiment_locations[eid])
            rid = _resolve_run_for_viz(repo, eid, explicit_run=run)
            return eid, rid, episode, experiment_locations[eid]

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


def _discover_workspace_results_roots(workspace_path: Path) -> list[Path]:
    """Return all workspace-local results roots relevant to visualization."""
    ws = Path(workspace_path)
    roots: list[Path] = []
    primary_root = ws / "results"
    if primary_root.is_dir():
        roots.append(primary_root)

    series_root = ws / "series"
    if series_root.is_dir():
        for path in sorted(series_root.glob("*/results")):
            if path.is_dir():
                roots.append(path)
    return roots


def _discover_workspace_experiments(repo_roots: list[Path]) -> dict[str, Path]:
    """Map experiment IDs to the unique results root containing them."""
    from axis.framework.persistence import ExperimentRepository

    locations: dict[str, Path] = {}
    for repo_root in repo_roots:
        repo = ExperimentRepository(repo_root)
        for experiment_id in repo.list_experiments():
            previous = locations.get(experiment_id)
            if previous is not None and previous != repo_root:
                raise ValueError(
                    f"Experiment '{experiment_id}' appears in multiple workspace "
                    f"results roots: '{previous}' and '{repo_root}'."
                )
            locations[experiment_id] = repo_root
    return locations


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
