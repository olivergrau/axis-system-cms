"""Helpers for exporting workspace measurement text reports."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path


def export_measurement_reports(
    ws: Path,
    *,
    comparison_number: int,
    comparison_log_path: str,
    run_summary_role: str | None,
    run_summary_log_path: str,
    run_summary_experiment_id: str | None = None,
    run_summary_run_id: str | None = None,
    catalogs: dict | None = None,
    comparison_output_path: str | None = None,
    results_root: Path | None = None,
) -> None:
    """Export comparison-summary and run-summary text reports to files."""
    from axis.framework.cli.commands.runs import cmd_runs_show
    from axis.framework.cli.commands.workspaces import (
        cmd_workspaces_comparison_result,
    )
    from axis.framework.cli.output import stdout_output
    from axis.framework.persistence import ExperimentRepository
    from axis.framework.workspaces.run_summary import (
        resolve_run_summary_target,
    )

    comparison_path = ws / comparison_log_path
    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    with comparison_path.open("w", encoding="utf-8") as stream:
        with redirect_stdout(stream):
            cmd_workspaces_comparison_result(
                str(ws),
                "text",
                comparison_number=comparison_number,
                catalogs=catalogs,
                comparison_path=comparison_output_path,
                results_root=results_root,
            )

    run_summary_path = ws / run_summary_log_path
    run_summary_path.parent.mkdir(parents=True, exist_ok=True)
    repo = ExperimentRepository(results_root or (ws / "results"))
    if run_summary_experiment_id is not None and run_summary_run_id is not None:
        target = type("Target", (), {
            "experiment_id": run_summary_experiment_id,
            "run_id": run_summary_run_id,
            "run_notes": None,
        })()
    else:
        if run_summary_role is None:
            raise ValueError(
                "run_summary_role is required unless an explicit experiment/run "
                "pair is provided for report export."
            )
        target = resolve_run_summary_target(ws, role=run_summary_role)
    with run_summary_path.open("w", encoding="utf-8") as stream:
        with redirect_stdout(stream):
            if getattr(target, "run_notes", None):
                stdout_output().kv("Run notes", target.run_notes)
            cmd_runs_show(repo, target.experiment_id, target.run_id, "text")
