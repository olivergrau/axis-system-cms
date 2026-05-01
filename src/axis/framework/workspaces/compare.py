"""Workspace-aware comparison routing (WP-09).

Uses the workspace-local repository (``<workspace>/results/``) for
loading traces and writes comparison output to
``<workspace>/comparisons/``.

Each comparison produces a sequentially numbered, self-contained
envelope file (``comparison-001.json``, ``comparison-002.json``, …)
that embeds full copies of both experiment configurations alongside
the comparison metrics.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from axis.framework.workspaces.comparison_envelope import (
    WorkspaceComparisonEnvelope,
)
from axis.framework.workspaces.compare_resolution import (
    resolve_comparison_targets,
)


def _next_comparison_number(comparisons_dir: Path) -> int:
    """Determine the next sequential comparison number."""
    if not comparisons_dir.is_dir():
        return 1
    existing = [
        f.name for f in comparisons_dir.iterdir()
        if re.match(r"comparison-\d+\.json$", f.name)
    ]
    if not existing:
        return 1
    numbers = [
        int(re.search(r"comparison-(\d+)\.json$", n).group(1))
        for n in existing
    ]
    return max(numbers) + 1


def compare_workspace(
    workspace_path: Path,
    reference_experiment: str | None = None,
    candidate_experiment: str | None = None,
    *,
    extension_catalog: object | None = None,
    progress: object | None = None,
    progress_description: str | None = None,
    results_root: Path | None = None,
    comparisons_root: Path | None = None,
) -> tuple[WorkspaceComparisonEnvelope, str]:
    """Run a comparison for a workspace and save results.

    All data is read from and written to the workspace.  The
    workspace-local repository at ``<workspace>/results/`` is used
    for loading episode traces.

    Returns
    -------
    tuple
        (envelope, workspace_relative_path) — the self-contained
        comparison envelope and its workspace-relative output path.

    Raises
    ------
    ValueError
        If no runs exist or resolution fails (propagated from
        compare_resolution).
    """
    from axis.framework.comparison import compare_runs
    from axis.framework.persistence import ExperimentRepository

    ws = Path(workspace_path)
    if results_root is None and comparisons_root is None:
        plan = resolve_comparison_targets(
            ws, reference_experiment, candidate_experiment,
        )
    else:
        from axis.framework.comparison import compare_runs
        from axis.framework.experiment_output import load_experiment_output
        from axis.framework.persistence import ExperimentRepository

        if not reference_experiment or not candidate_experiment:
            raise ValueError(
                "Explicit reference and candidate experiment IDs are required "
                "when compare_workspace(...) uses custom results/comparisons roots."
            )
        repo = ExperimentRepository(Path(results_root) if results_root is not None else ws / "results")
        ref_output = load_experiment_output(repo, reference_experiment)
        cand_output = load_experiment_output(repo, candidate_experiment)
        if getattr(ref_output, "trace_mode", None) == "light":
            raise ValueError(
                f"The reference experiment '{reference_experiment}' was executed in "
                "light trace mode and cannot be used for replay-based comparison."
            )
        if getattr(cand_output, "trace_mode", None) == "light":
            raise ValueError(
                f"The candidate experiment '{candidate_experiment}' was executed in "
                "light trace mode and cannot be used for replay-based comparison."
            )
        result = compare_runs(
            repo,
            reference_experiment,
            ref_output.primary_run_id,
            candidate_experiment,
            cand_output.primary_run_id,
            extension_catalog=extension_catalog,
            progress=progress,
            progress_description=progress_description,
        )
        ref_config = repo.load_experiment_config(reference_experiment).model_dump(mode="json")
        cand_config = repo.load_experiment_config(candidate_experiment).model_dump(mode="json")
        comparisons_dir = Path(comparisons_root) if comparisons_root is not None else ws / "comparisons"
        comparisons_dir.mkdir(parents=True, exist_ok=True)
        num = _next_comparison_number(comparisons_dir)
        filename = f"comparison-{num:03d}.json"
        output_path = comparisons_dir / filename
        envelope = WorkspaceComparisonEnvelope(
            comparison_number=num,
            timestamp=datetime.now(timezone.utc).isoformat(),
            reference_config=ref_config,
            candidate_config=cand_config,
            comparison_result=result.model_dump(mode="json"),
        )
        output_path.write_text(json.dumps(envelope.model_dump(mode="json"), indent=2))
        return envelope, str(output_path.relative_to(ws))

    # Use the workspace-local repository for loading traces.
    repo = ExperimentRepository(Path(results_root) if results_root is not None else ws / "results")

    ref_output = None
    cand_output = None
    try:
        from axis.framework.experiment_output import load_experiment_output

        ref_output = load_experiment_output(repo, plan.reference.experiment_id)
        cand_output = load_experiment_output(repo, plan.candidate.experiment_id)
    except Exception:
        ref_output = None
        cand_output = None

    for label, output in (("reference", ref_output), ("candidate", cand_output)):
        if output is not None and getattr(output, "trace_mode", None) == "light":
            raise ValueError(
                f"The {label} experiment '{output.experiment_id}' was executed in "
                "light trace mode and cannot be used for replay-based comparison."
            )

    result = compare_runs(
        repo,
        plan.reference.experiment_id,
        plan.reference.run_id,
        plan.candidate.experiment_id,
        plan.candidate.run_id,
        extension_catalog=extension_catalog,
        progress=progress,
        progress_description=progress_description,
    )

    # Load full config copies from the workspace results.
    ref_config = repo.load_experiment_config(
        plan.reference.experiment_id,
    ).model_dump(mode="json")
    cand_config = repo.load_experiment_config(
        plan.candidate.experiment_id,
    ).model_dump(mode="json")

    # Write comparison output to workspace comparisons/.
    comparisons_dir = Path(comparisons_root) if comparisons_root is not None else ws / "comparisons"
    comparisons_dir.mkdir(exist_ok=True)

    num = _next_comparison_number(comparisons_dir)
    filename = f"comparison-{num:03d}.json"
    output_path = comparisons_dir / filename

    envelope = WorkspaceComparisonEnvelope(
        comparison_number=num,
        timestamp=datetime.now(timezone.utc).isoformat(),
        reference_config=ref_config,
        candidate_config=cand_config,
        comparison_result=result.model_dump(mode="json"),
    )

    output_path.write_text(
        json.dumps(envelope.model_dump(mode="json"), indent=2),
    )

    return envelope, str(output_path.relative_to(ws))
