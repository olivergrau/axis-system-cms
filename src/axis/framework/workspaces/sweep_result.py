"""Workspace sweep-result inspection.

Resolves and renders sweep outputs from a workspace for the
``axis workspaces sweep-result`` command.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def resolve_sweep_result(
    workspace_path: Path,
    experiment: str | None = None,
) -> dict[str, Any]:
    """Resolve and render a sweep output from a workspace.

    Parameters
    ----------
    workspace_path:
        Path to the workspace root.
    experiment:
        Optional explicit experiment ID.  If omitted selects the
        newest sweep output in ``primary_results``.

    Returns
    -------
    Dict suitable for text or JSON rendering.

    Raises
    ------
    ValueError
        If no sweep outputs exist, or the selected experiment is not
        a sweep output.
    """
    from axis.framework.experiment_output import (
        SweepExperimentOutput,
        load_experiment_output,
    )
    from axis.framework.persistence import ExperimentRepository
    from axis.framework.workspaces.types import load_manifest, result_entry_path

    ws = Path(workspace_path)
    manifest = load_manifest(ws)
    repo = ExperimentRepository(ws / "results")

    # Filter primary_results to sweep outputs.
    sweep_entries: list[tuple[str, Any]] = []  # (eid, entry)
    for entry in (manifest.primary_results or []):
        if getattr(entry, "output_form", None) == "sweep":
            path_str = result_entry_path(entry)
            parts = path_str.split("/")
            if len(parts) >= 2:
                sweep_entries.append((parts[1], entry))

    if not sweep_entries:
        raise ValueError(
            "No sweep outputs found in this workspace. "
            "Run an OFAT config first with 'axis workspaces run'."
        )

    if experiment:
        # Validate explicit selection.
        matching = [e for e in sweep_entries if e[0] == experiment]
        if not matching:
            # Check if it exists but is a point output.
            all_eids = [e[0] for e in sweep_entries]
            experiments = repo.list_experiments()
            if experiment in experiments:
                raise ValueError(
                    f"Experiment '{experiment}' is not a sweep output. "
                    f"Available sweep outputs: {all_eids}"
                )
            raise ValueError(
                f"Experiment '{experiment}' not found in workspace results. "
                f"Available sweep outputs: {all_eids}"
            )
        eid = matching[0][0]
    else:
        # Default: newest sweep (last in primary_results order).
        eid = sweep_entries[-1][0]

    # Load the sweep output.
    exp_output = load_experiment_output(repo, eid)
    if not isinstance(exp_output, SweepExperimentOutput):
        raise ValueError(
            f"Experiment '{eid}' is not a sweep output "
            f"(output_form='{exp_output.output_form}')."
        )

    # Load per-run summaries for delta computation.
    run_details: list[dict[str, Any]] = []
    baseline_summary = None

    for i, rid in enumerate(exp_output.run_ids):
        detail: dict[str, Any] = {
            "run_id": rid,
            "is_baseline": (rid == exp_output.baseline_run_id),
        }
        if i < len(exp_output.variation_descriptions):
            detail["variation"] = exp_output.variation_descriptions[i]
        if (exp_output.parameter_values
                and i < len(exp_output.parameter_values)):
            detail["parameter_value"] = exp_output.parameter_values[i]

        # Load run summary if available.
        try:
            rs = repo.load_run_summary(eid, rid)
            detail["mean_steps"] = rs.mean_steps
            detail["death_rate"] = rs.death_rate
            detail["mean_final_vitality"] = rs.mean_final_vitality
            detail["num_episodes"] = rs.num_episodes
            if rid == exp_output.baseline_run_id:
                baseline_summary = rs
        except FileNotFoundError:
            pass

        run_details.append(detail)

    # Compute deltas relative to baseline.
    if baseline_summary:
        for detail in run_details:
            if detail.get("is_baseline"):
                continue
            if "mean_steps" in detail:
                detail["delta_mean_steps"] = round(
                    detail["mean_steps"] - baseline_summary.mean_steps, 2)
            if "death_rate" in detail:
                detail["delta_death_rate"] = round(
                    detail["death_rate"] - baseline_summary.death_rate, 4)
            if "mean_final_vitality" in detail:
                detail["delta_mean_final_vitality"] = round(
                    detail["mean_final_vitality"]
                    - baseline_summary.mean_final_vitality, 4)

    # Load the persisted experiment summary for authoritative delta fields.
    experiment_summary = None
    try:
        experiment_summary = repo.load_experiment_summary(eid)
    except FileNotFoundError:
        pass

    return {
        "experiment_id": eid,
        "system_type": exp_output.system_type,
        "output_form": "sweep",
        "parameter_path": exp_output.parameter_path,
        "parameter_values": (list(exp_output.parameter_values)
                             if exp_output.parameter_values else None),
        "baseline_run_id": exp_output.baseline_run_id,
        "num_runs": exp_output.num_runs,
        "experiment_summary": (
            experiment_summary.model_dump(mode="json")
            if experiment_summary else None
        ),
        "runs": run_details,
    }
