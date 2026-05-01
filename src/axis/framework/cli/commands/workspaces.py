"""CLI commands for workspace management."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from axis.framework.cli.output import fail, stdout_output


def _format_workspace_status(status: object, *, out=None) -> str:
    """Return a visually emphasized workspace status label."""
    out = out or stdout_output()
    status_text = str(status)
    role = {
        "draft": "warning",
        "active": "success",
        "analyzing": "info",
        "completed": "success",
        "closed": "error",
    }.get(status_text, "emphasis")
    return out.styled(status_text.upper(), role=role)


def _format_workspace_lifecycle(stage: object, *, out=None) -> str:
    """Return a visually emphasized lifecycle label."""
    out = out or stdout_output()
    return out.styled(str(stage).upper(), role="emphasis")


def cmd_workspaces_scaffold(output: str) -> None:
    """Interactive workspace scaffolding."""
    import questionary
    from rich.console import Console

    from axis.framework.registry import registered_system_types
    from axis.framework.workspaces.scaffold import scaffold_workspace
    from axis.framework.workspaces.types import (
        ArtifactKind,
        WorkspaceClass,
        WorkspaceLifecycleStage,
        WorkspaceManifest,
        WorkspaceStatus,
        WorkspaceType,
    )

    console = Console()
    console.print("[bold]AXIS Workspace Scaffolder[/bold]\n")

    def ask_system_name(prompt: str) -> str:
        available = list(registered_system_types())
        if not available:
            return questionary.text(prompt).ask() or "system_a"

        choice = questionary.select(
            prompt,
            choices=[*available, "<custom>"],
            default=available[0],
        ).ask()
        if choice == "<custom>":
            return questionary.text(f"{prompt} (custom):").ask() or "system_a"
        return choice or "system_a"

    workspace_id = questionary.text("Workspace ID:").ask()
    if not workspace_id:
        fail("Scaffolding aborted.")

    title = questionary.text("Title:").ask() or workspace_id

    ws_class = questionary.select(
        "Workspace class:",
        choices=[c.value for c in WorkspaceClass],
    ).ask()

    valid_types = {
        "development": ["system_development"],
        "investigation": ["single_system", "system_comparison"],
    }
    ws_type = questionary.select(
        "Workspace type:",
        choices=valid_types.get(ws_class, []),
    ).ask()

    status = questionary.select(
        "Status:",
        choices=[s.value for s in WorkspaceStatus],
        default="draft",
    ).ask()

    lifecycle = questionary.select(
        "Lifecycle stage:",
        choices=[s.value for s in WorkspaceLifecycleStage],
        default="idea",
    ).ask()

    # Type-specific fields.
    manifest_data: dict = {
        "workspace_id": workspace_id,
        "title": title,
        "workspace_class": ws_class,
        "workspace_type": ws_type,
        "status": status,
        "lifecycle_stage": lifecycle,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
    }

    if ws_class == "investigation":
        manifest_data["question"] = questionary.text(
            "Research question:").ask() or ""
    else:
        manifest_data["development_goal"] = questionary.text(
            "Development goal:",
        ).ask() or ""

    if ws_type == "single_system":
        manifest_data["system_under_test"] = ask_system_name(
            "System under test:",
        )

    elif ws_type == "system_comparison":
        manifest_data["reference_system"] = ask_system_name(
            "Reference system:",
        )
        manifest_data["candidate_system"] = ask_system_name(
            "Candidate system:",
        )

    elif ws_type in ("system_development",):
        kind = "system" if ws_type == "system_development" else "world"
        manifest_data["artifact_kind"] = kind
        manifest_data["artifact_under_development"] = questionary.text(
            f"Artifact under development ({kind}):",
        ).ask() or f"new_{kind}"

    manifest = WorkspaceManifest.model_validate(manifest_data)

    target_dir = questionary.text(
        "Parent directory:", default="workspaces",
    ).ask() or "workspaces"
    target = Path(target_dir) / workspace_id
    result = scaffold_workspace(target, manifest)

    if output == "json":
        print(json.dumps({"workspace_path": str(result)}))
    else:
        console.print(f"\n[green]Workspace created:[/green] {result}")


def cmd_workspaces_check(
    workspace_path: str, output: str,
    inspection_service: object = None,
) -> None:
    """Validate a workspace."""
    ws = Path(workspace_path)
    result, drift_issues = inspection_service.check(ws)

    if output == "json":
        data = result.model_dump(mode="json")
        data["drift_issues"] = [
            i.model_dump(mode="json") for i in drift_issues
        ]
        print(json.dumps(data, indent=2))
    else:
        out = stdout_output()
        out.title(f"Workspace {ws.name}")
        if result.is_valid and not drift_issues:
            out.kv("Validation", "VALID")
        elif result.is_valid:
            out.kv("Validation", "VALID (with drift warnings)")
        else:
            out.kv("Validation", "INVALID")

        if result.issues:
            out.section("Issues")
        for issue in result.issues:
            out.list_row(f"[{issue.severity}]", issue.message)
        if drift_issues:
            out.section("Drift Warnings")
        for issue in drift_issues:
            out.list_row(f"[drift:{issue.severity}]", issue.message)


def cmd_workspaces_close(
    workspace_path: str,
    output: str,
    workflow_service: object = None,
) -> None:
    """Close a workspace and finalize its workflow state."""
    result = workflow_service.close(Path(workspace_path))

    if output == "json":
        print(json.dumps({
            "workspace_path": result.workspace_path,
            "status": result.status,
            "lifecycle_stage": result.lifecycle_stage,
        }, indent=2))
    else:
        out = stdout_output()
        out.success(f"workspace closed: {Path(workspace_path).name}")
        out.kv("Status", result.status)
        out.kv("Lifecycle", result.lifecycle_stage)


def cmd_workspaces_reset(
    workspace_path: str,
    output: str,
    *,
    force: bool = False,
    workflow_service: object = None,
) -> None:
    """Reset generated workspace artifacts and clear manifest tracking."""
    ws = Path(workspace_path)
    plan = workflow_service.plan_reset(ws)

    if output == "json" and not force:
        print(json.dumps({
            "mode": "preview",
            "workspace_path": plan.workspace_path,
            "workspace_global_paths": plan.workspace_global_paths,
            "series_paths_by_id": plan.series_paths_by_id,
            "manifest_fields_to_clear": plan.manifest_fields_to_clear,
            "workspace_global_counts": plan.workspace_global_counts,
            "series_counts_by_id": plan.series_counts_by_id,
            "total_paths": plan.total_paths,
            "total_entries": plan.total_entries,
            "total_files": plan.total_files,
            "total_directories": plan.total_directories,
        }, indent=2))
        return

    if output != "json":
        out = stdout_output()
        out.title(f"Reset Preview: {ws.name}")
        out.kv("Artifact roots", plan.total_paths)
        out.kv("Top-level entries to delete", plan.total_entries)
        out.kv("Nested files", plan.total_files)
        out.kv("Nested directories", plan.total_directories)
        out.section("Workspace Global")
        for rel in plan.workspace_global_paths:
            count = plan.workspace_global_counts.get(rel, 0)
            out.list_row(rel, f"({count} top-level entries)")
        if plan.series_paths_by_id:
            out.section("Series Local")
            for sid, paths in plan.series_paths_by_id.items():
                out.kv("Series", sid)
                for rel in paths:
                    count = plan.series_counts_by_id.get(sid, {}).get(rel, 0)
                    out.list_row(rel, f"({count} top-level entries)", indent=4)
        out.section("Manifest Fields")
        for field_name in plan.manifest_fields_to_clear:
            out.list_row(field_name)
        if not force:
            response = input("Delete the generated workspace artifacts listed above? [y/N] ")
            if response.strip().lower() not in {"y", "yes"}:
                out.warning("workspace reset cancelled")
                return

    result = workflow_service.reset(ws)

    if output == "json":
        print(json.dumps({
            "mode": "executed",
            "workspace_path": result.workspace_path,
            "cleared_results": result.cleared_results,
            "cleared_comparisons": result.cleared_comparisons,
            "cleared_measurements": result.cleared_measurements,
        }, indent=2))
    else:
        out.success(f"workspace reset: {Path(workspace_path).name}")
        out.kv("Cleared results entries", result.cleared_results)
        out.kv("Cleared comparison entries", result.cleared_comparisons)
        out.kv("Cleared measurement entries", result.cleared_measurements)


def cmd_workspaces_show(
    workspace_path: str, output: str,
    inspection_service: object = None,
) -> None:
    """Show workspace summary."""
    ws = Path(workspace_path)
    summary = inspection_service.summarize(ws)

    if output == "json":
        print(json.dumps(summary.model_dump(mode="json"), indent=2))
    else:
        out = stdout_output()
        out.title(f"Workspace {summary.workspace_id}")
        out.kv("Title", summary.title)
        out.kv("Class", summary.workspace_class)
        out.kv("Type", summary.workspace_type)
        out.kv("Status", _format_workspace_status(summary.status, out=out))
        out.kv(
            "Lifecycle",
            _format_workspace_lifecycle(summary.lifecycle_stage, out=out),
        )
        if str(summary.status) == "closed":
            out.hint(
                "Workspace is closed; execution and comparison commands are disabled."
            )
        if summary.description:
            out.kv("Description", summary.description)
        if summary.question:
            out.kv("Question", summary.question)
        if summary.development_goal:
            out.kv("Goal", summary.development_goal)
        if summary.system_under_test:
            out.kv("System under test", summary.system_under_test)
        if summary.reference_system:
            out.kv("Reference", summary.reference_system)
        if summary.candidate_system:
            out.kv("Candidate", summary.candidate_system)
        if summary.artifact_under_development:
            out.kv("Artifact", summary.artifact_under_development)
        _print_artifact_section("Primary configs", summary.primary_configs, out=out)
        _print_artifact_section("Primary results", summary.primary_results, out=out)
        _print_artifact_section(
            "Primary comparisons", summary.primary_comparisons, out=out)
        if summary.experiment_series:
            out.section("Experiment Series")
            for series in summary.experiment_series:
                marker = "OK" if series.exists else "MISSING"
                title_suffix = f" - {series.title}" if series.title else ""
                out.line(
                    f"  [{marker}] {series.id}{title_suffix}"
                    f" ({series.path})"
                )
                _print_artifact_section(
                    "Series results",
                    series.results,
                    out=out,
                )
                _print_artifact_section(
                    "Series comparisons",
                    series.comparisons,
                    out=out,
                )
                _print_artifact_section(
                    "Series measurements",
                    series.measurement_runs,
                    out=out,
                )
        if summary.development_state:
            out.section("Development")
            out.kv("Development state", summary.development_state)
            if summary.baseline_config:
                out.kv("Baseline config", summary.baseline_config)
            if summary.candidate_config:
                out.kv("Candidate config", summary.candidate_config)
            _print_artifact_section(
                "Baseline results", summary.baseline_results, out=out)
            _print_artifact_section(
                "Candidate results", summary.candidate_results, out=out)
            if summary.current_candidate_result:
                marker = "OK" if summary.current_candidate_result.exists else "MISSING"
                out.kv(
                    "Current candidate result",
                    f"[{marker}] {summary.current_candidate_result.path}",
                )
            if summary.current_validation_comparison:
                marker = "OK" if summary.current_validation_comparison.exists else "MISSING"
                out.kv(
                    "Current validation comparison",
                    f"[{marker}] {summary.current_validation_comparison.path}",
                )
                # Show which baseline was used in the last comparison
                if summary.current_validation_comparison.exists:
                    _print_comparison_targets(
                        ws, summary.current_validation_comparison.path, out=out)
        if summary.check_result:
            status = "VALID" if summary.check_result.is_valid else "INVALID"
            out.section("Validation")
            out.kv("Status", status)


def cmd_workspaces_sweep_result(
    workspace_path: str, output: str,
    experiment: str | None = None,
    inspection_service: object = None,
) -> None:
    """Inspect a sweep (OFAT) result in a workspace."""
    result = inspection_service.sweep_result(
        Path(workspace_path), experiment=experiment)

    if output == "json":
        print(json.dumps(result, indent=2))
        return

    out = stdout_output()
    out.title(f"Sweep Result {result['experiment_id']}")
    out.kv("System", result["system_type"])
    if result.get("parameter_path"):
        out.kv("Parameter", result["parameter_path"])
    if result.get("parameter_values"):
        out.kv("Values", result["parameter_values"])
    out.kv("Baseline run", result["baseline_run_id"])
    out.kv("Runs", result["num_runs"])
    out.section("Run Summary")
    for rd in result.get("runs", []):
        label = rd.get("variation", rd["run_id"])
        parts = [rd["run_id"], label]
        if "mean_steps" in rd:
            parts.append(f"mean_steps={rd['mean_steps']:.1f}")
        if "death_rate" in rd:
            parts.append(f"death_rate={rd['death_rate']:.2f}")
        if "mean_final_vitality" in rd:
            parts.append(f"vitality={rd['mean_final_vitality']:.3f}")
        if "delta_mean_steps" in rd:
            parts.append(f"delta_steps={rd['delta_mean_steps']:+.1f}")
        if "delta_death_rate" in rd:
            parts.append(f"delta_death={rd['delta_death_rate']:+.4f}")
        if "delta_mean_final_vitality" in rd:
            parts.append(
                f"delta_vitality={rd['delta_mean_final_vitality']:+.3f}")
        out.list_row(*parts)


def cmd_workspaces_run_summary(
    workspace_path: str,
    output: str,
    *,
    role: str | None = None,
    experiment: str | None = None,
    run: str | None = None,
    inspection_service: object = None,
) -> None:
    """Inspect one resolved run from a workspace."""
    from axis.framework.cli.commands.runs import cmd_runs_show
    from axis.framework.persistence import ExperimentRepository

    ws = Path(workspace_path)
    target = inspection_service.run_summary_target(
        ws,
        role=role,
        experiment=experiment,
        run=run,
    )
    if output != "json" and getattr(target, "run_notes", None):
        out = stdout_output()
        out.kv("Run notes", target.run_notes)
    repo = ExperimentRepository(ws / "results")
    cmd_runs_show(repo, target.experiment_id, target.run_id, output)


def cmd_workspaces_run_metrics(
    workspace_path: str,
    output: str,
    *,
    role: str | None = None,
    experiment: str | None = None,
    run: str | None = None,
    inspection_service: object = None,
) -> None:
    """Inspect behavioral metrics for one resolved run from a workspace."""
    from axis.framework.cli.commands.runs import cmd_runs_metrics
    from axis.framework.persistence import ExperimentRepository

    ws = Path(workspace_path)
    target = inspection_service.run_summary_target(
        ws,
        role=role,
        experiment=experiment,
        run=run,
    )
    repo = ExperimentRepository(ws / "results")
    cmd_runs_metrics(repo, target.experiment_id, target.run_id, output)


def cmd_workspaces_set_candidate(
    workspace_path: str, config_path: str, output: str,
    run_service: object = None,
) -> None:
    """Set the candidate config for a development workspace."""
    run_service.set_candidate(Path(workspace_path), config_path)
    stdout_output().success(f"candidate config set: {config_path}")


def cmd_workspaces_run(
    workspace_path: str, output: str,
    run_filter: str | None = None,
    override_guard: bool = False,
    run_notes: str | None = None,
    run_service: object = None,
) -> None:
    """Execute workspace configs."""
    ws = Path(workspace_path)
    from axis.framework.progress import create_progress_reporter

    with create_progress_reporter(output != "json") as progress:
        summaries = run_service.execute(
            ws,
            run_filter=run_filter,
            override_guard=override_guard,
            run_notes=run_notes,
            progress=progress,
        )

    if output == "json":
        print(json.dumps([{
            "experiment_id": s.experiment_id,
            "num_runs": s.num_runs,
        } for s in summaries], indent=2))
    else:
        out = stdout_output()
        out.success(f"workspace execution: {len(summaries)} experiment(s)")
        for s in summaries:
            out.list_row(s.experiment_id, f"runs={s.num_runs}")


def cmd_workspaces_compare(
    workspace_path: str,
    output: str,
    reference_experiment: str | None = None,
    candidate_experiment: str | None = None,
    compare_service: object = None,
    catalogs: dict | None = None,
) -> None:
    """Run workspace comparison."""
    from axis.framework.progress import create_progress_reporter

    ws = Path(workspace_path)
    with create_progress_reporter(output != "json") as progress:
        svc_result = compare_service.compare(
            ws,
            reference_experiment,
            candidate_experiment,
            extension_catalog=(
                catalogs.get("comparison_extensions") if catalogs else None
            ),
            progress=progress,
        )

    if output == "json":
        # Re-read the envelope for full JSON output.
        env_path = ws / svc_result.output_path
        print(env_path.read_text())
    else:
        out = stdout_output()
        out.success(f"workspace comparison #{svc_result.comparison_number}")
        out.kv("Output", ws / svc_result.output_path)


def cmd_workspaces_measure(
    workspace_path: str,
    output: str,
    *,
    label: str | None = None,
    override_guard: bool = False,
    run_notes: str | None = None,
    measurement_service: object = None,
    catalogs: dict | None = None,
) -> None:
    """Run the system-comparison measurement workflow and export logs."""
    from axis.framework.progress import create_progress_reporter

    ws = Path(workspace_path)
    with create_progress_reporter(output != "json") as progress:
        result = measurement_service.measure(
            ws,
            label=label,
            override_guard=override_guard,
            run_notes=run_notes,
            extension_catalog=(
                catalogs.get("comparison_extensions") if catalogs else None
            ),
            progress=progress,
        )

    from axis.framework.workspaces.measurement_reports import (
        export_measurement_reports,
    )

    export_measurement_reports(
        ws,
        comparison_number=result.comparison_number,
        comparison_log_path=result.comparison_log_path,
        run_summary_role=result.run_summary_role,
        run_summary_log_path=result.run_summary_log_path,
        catalogs=catalogs,
    )

    if output == "json":
        print(json.dumps({
            "measurement_number": result.measurement_number,
            "measurement_dir": result.measurement_dir,
            "label": result.label,
            "comparison_number": result.comparison_number,
            "comparison_output_path": result.comparison_output_path,
            "comparison_log_path": result.comparison_log_path,
            "run_summary_log_path": result.run_summary_log_path,
            "run_summary_role": result.run_summary_role,
            "run_experiment_ids": result.run_experiment_ids,
            "run_experiments_by_role": result.run_experiments_by_role,
        }, indent=2))
    else:
        out = stdout_output()
        out.success(f"workspace measurement #{result.measurement_number}")
        out.kv("Directory", ws / result.measurement_dir)
        out.kv("Comparison log", ws / result.comparison_log_path)
        out.kv("Run-summary log", ws / result.run_summary_log_path)


def cmd_workspaces_run_series(
    workspace_path: str,
    output: str,
    *,
    series_id: str,
    override_guard: bool = False,
    update_notes: bool = False,
    experiment_series_service: object = None,
    catalogs: dict | None = None,
) -> None:
    """Run a declarative workspace experiment series."""
    from axis.framework.progress import create_progress_reporter

    ws = Path(workspace_path)
    with create_progress_reporter(output != "json") as progress:
        result = experiment_series_service.run_series(
            ws,
            series_id=series_id,
            override_guard=override_guard,
            update_notes=update_notes,
            catalogs=catalogs,
            progress=progress,
        )

    if output == "json":
        print(json.dumps({
            "series_id": result.series_id,
            "series_title": result.series_title,
            "executed_experiment_count": result.executed_experiment_count,
            "executed_experiment_ids": result.executed_experiment_ids,
            "measurement_directories": result.measurement_directories,
            "series_summary_markdown_path": result.series_summary_markdown_path,
            "series_summary_json_path": result.series_summary_json_path,
            "series_metrics_csv_path": result.series_metrics_csv_path,
            "series_manifest_json_path": result.series_manifest_json_path,
            "notes_updated": result.notes_updated,
        }, indent=2))
    else:
        out = stdout_output()
        out.success("workspace experiment series completed")
        out.kv("Series", result.series_id)
        out.kv("Experiments executed", result.executed_experiment_count)
        out.kv("Series summary", ws / result.series_summary_markdown_path)
        out.kv("Series JSON", ws / result.series_summary_json_path)
        out.kv("Series CSV", ws / result.series_metrics_csv_path)
        out.kv("Series manifest", ws / result.series_manifest_json_path)
        out.kv("Notes updated", "yes" if result.notes_updated else "no")


def cmd_workspaces_compare_configs(
    workspace_path: str,
    output: str,
) -> None:
    """Display config deltas between reference and candidate configs."""
    from axis.framework.workspaces.config_compare import (
        compare_workspace_configs,
    )

    result = compare_workspace_configs(Path(workspace_path))

    if output == "json":
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    else:
        out = stdout_output()
        out.title("Workspace Config Delta")
        out.kv("Reference config", result.reference_config)
        out.kv("Candidate config", result.candidate_config)
        if result.candidate_delta:
            out.kv("Candidate delta", "")
            _print_changed_config_summary_with_reference(
                result.candidate_delta,
                result.reference_values,
                indent=4,
                out=out,
            )
        else:
            out.hint("No config differences found.")


def cmd_workspaces_comparison_result(
    workspace_path: str,
    output: str,
    comparison_number: int | None = None,
    catalogs: dict | None = None,
    comparison_path: str | None = None,
    results_root: Path | None = None,
) -> None:
    """Display a stored workspace comparison result."""
    from axis.framework.comparison.types import RunComparisonResult
    from axis.framework.workspaces.comparison_envelope import (
        WorkspaceComparisonEnvelope,
    )
    from axis.framework.workspaces.types import WorkspaceType, load_manifest
    from axis.framework.cli.commands.compare import print_run_comparison_text

    ws = Path(workspace_path)
    manifest = load_manifest(ws)

    if manifest.workspace_type not in (
        WorkspaceType.SYSTEM_COMPARISON,
        WorkspaceType.SYSTEM_DEVELOPMENT,
        WorkspaceType.SINGLE_SYSTEM,
    ):
        fail(
            f"comparison-summary is only valid for "
            f"system_comparison, system_development, or single_system "
            f"workspaces, got '{manifest.workspace_type}'."
        )

    if comparison_path is not None:
        target = ws / comparison_path
        if not target.is_file():
            fail(f"Comparison file not found: {comparison_path}")
        files = [target]
        num_available = 1
    else:
        comparisons_dir = ws / "comparisons"
        if not comparisons_dir.is_dir():
            fail("No comparisons directory found.")

        import re
        files = sorted(
            f for f in comparisons_dir.iterdir()
            if re.match(r"comparison-\d+\.json$", f.name)
        )
        num_available = len(files)
        if not files:
            fail(
                "No comparison results found.",
                hint=f"Run `axis workspaces compare {workspace_path}` first.",
            )

        if comparison_number is not None:
            target = comparisons_dir / f"comparison-{comparison_number:03d}.json"
            if not target.is_file():
                fail(
                    f"Comparison #{comparison_number} not found. "
                    f"Available: {', '.join(f.name for f in files)}"
                )
            files = [target]
        else:
            # Default to the latest comparison result if multiple exist.
            files = [files[-1]]

    # Display the selected comparison
    env = WorkspaceComparisonEnvelope.model_validate(
        json.loads(files[0].read_text()))

    result = _resolve_comparison_result(
        ws,
        env,
        extension_catalog=(
            catalogs.get("comparison_extensions") if catalogs else None
        ),
        results_root=results_root,
    )

    if output == "json":
        payload = env.model_dump(mode="json")
        payload["comparison_result"] = result.model_dump(mode="json")
        print(json.dumps(payload, indent=2))
    else:
        out = stdout_output()
        out.title(f"Comparison #{env.comparison_number}")
        out.kv("Timestamp", env.timestamp)
        if comparison_number is None and num_available > 1:
            out.hint("Showing latest comparison by default. Use --number to select another.")
        # Print the comparison metrics using the existing formatter.
        print_run_comparison_text(result)
        out.section("Configurations")
        out.hint("Differing config values are highlighted when terminal styling is enabled.")
        out.kv(
            "Reference config",
            f"system_type={env.reference_config.get('system_type', '?')}",
        )
        _print_config_summary(
            env.reference_config,
            indent=4,
            other_config=env.candidate_config,
            out=out,
        )
        out.kv(
            "Candidate config",
            f"system_type={env.candidate_config.get('system_type', '?')}",
        )
        _print_config_summary(
            env.candidate_config,
            indent=4,
            other_config=env.reference_config,
            out=out,
        )


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def _print_comparison_targets(ws: Path, comparison_path: str, *, out=None) -> None:
    """Print the reference/candidate experiment IDs from a comparison file."""
    out = out or stdout_output()
    cmp_file = ws / comparison_path
    try:
        data = json.loads(cmp_file.read_text())
        cr = data.get("comparison_result", {})
        ref_eid = cr.get("reference_experiment_id", "?")
        cand_eid = cr.get("candidate_experiment_id", "?")
        out.kv("Reference used", ref_eid, indent=4)
        out.kv("Candidate used", cand_eid, indent=4)
    except Exception:
        pass


def _resolve_comparison_result(
    workspace_path: Path,
    envelope,
    *,
    extension_catalog: object | None = None,
    results_root: Path | None = None,
):
    """Return a stored or recomputed comparison result for display."""
    from axis.framework.comparison.types import RunComparisonResult
    return RunComparisonResult.model_validate(envelope.comparison_result)


def _print_artifact_section(label: str, entries: list, *, out=None) -> None:
    """Print a primary artifact section with existence markers."""
    out = out or stdout_output()
    out.blank()
    out.line(f"{label}:")
    if not entries:
        out.kv("Declared", "none")
        return
    found = sum(1 for e in entries if e.exists)
    out.kv("Present", f"{found}/{len(entries)}")
    for e in entries:
        marker = "OK" if e.exists else "MISSING"
        extra = ""
        annotations = []
        if getattr(e, "config", None):
            annotations.append(e.config)
        if getattr(e, "output_form", None):
            annotations.append(e.output_form)
        if getattr(e, "trace_mode", None):
            annotations.append(f"trace={e.trace_mode}")
        if getattr(e, "role", None):
            annotations.append(f"role={e.role}")
        if getattr(e, "label", None):
            annotations.append(f"label={e.label}")
        if getattr(e, "timestamp", None):
            annotations.append(e.timestamp)
        if annotations:
            extra = f"  ({', '.join(annotations)})"
        out.list_row(f"[{marker}]", f"{e.path}{extra}", indent=4)
        if getattr(e, "run_notes", None):
            out.kv("Run notes", e.run_notes, indent=6)
        if getattr(e, "reference_experiment_id", None) or getattr(e, "candidate_experiment_id", None):
            compared = " vs ".join(
                part for part in [
                    getattr(e, "reference_experiment_id", None),
                    getattr(e, "candidate_experiment_id", None),
                ] if part
            )
            if compared:
                out.kv("Compared experiments", compared, indent=6)
        if getattr(e, "comparison_config_changes", None):
            out.kv(
                "Config differences between compared experiments",
                "",
                indent=6,
            )
            _print_changed_config_summary(
                e.comparison_config_changes,
                indent=8,
                out=out,
            )
        if getattr(e, "config_changes", None):
            out.kv(
                "Config changes vs previous comparable run",
                "",
                indent=6,
            )
            _print_changed_config_summary(e.config_changes, indent=8, out=out)


def _flatten_config(
    config: dict,
    *,
    excluded_sections: set[str] | None = None,
) -> dict[str, object]:
    """Flatten a nested config into dotted key/value pairs."""
    excluded_sections = excluded_sections or {"logging"}
    flattened: dict[str, object] = {}

    def _flatten(obj: dict, path: str = "") -> None:
        for key, value in obj.items():
            full_key = f"{path}.{key}" if path else key
            top_level_key = full_key.split(".")[0]
            if top_level_key in excluded_sections:
                continue
            if value is None:
                continue
            if isinstance(value, dict):
                _flatten(value, full_key)
            else:
                flattened[full_key] = value

    _flatten(config)
    return flattened


def _print_config_summary(
    config: dict,
    indent: int = 4,
    *,
    other_config: dict | None = None,
    out=None,
) -> None:
    """Print a full experiment config as flattened key-value pairs.

    Excludes the ``logging`` section and keys with None values.
    """
    out = out or stdout_output()
    prefix = " " * indent
    flattened = _flatten_config(config)
    other_flattened = _flatten_config(other_config) if other_config else {}

    for key, value in flattened.items():
        line = f"{prefix}{key}: {value}"
        if other_config is not None and other_flattened.get(key) != value:
            out.line(out.styled(line, role="diff"))
        else:
            out.line(line)


def _print_changed_config_summary(config: dict, indent: int = 8, *, out=None) -> None:
    """Print a nested changed-config dict as flattened key-value pairs."""
    out = out or stdout_output()
    prefix = " " * indent

    def _flatten(obj: dict, path: str = "") -> None:
        for key, value in obj.items():
            full_key = f"{path}.{key}" if path else key
            if isinstance(value, dict):
                _flatten(value, full_key)
            else:
                out.line(out.styled(f"{prefix}{full_key}: {value}", role="diff"))

    _flatten(config)


def _print_changed_config_summary_with_reference(
    config: dict,
    reference_values: dict,
    indent: int = 8,
    *,
    out=None,
) -> None:
    """Print changed config values with matching reference values when known."""
    out = out or stdout_output()
    prefix = " " * indent
    missing = object()

    def _flatten(
        obj: dict,
        reference_obj: dict,
        path: str = "",
    ) -> None:
        for key, value in obj.items():
            full_key = f"{path}.{key}" if path else key
            reference_value = reference_obj.get(key, missing)
            if isinstance(value, dict):
                next_reference = (
                    reference_value if isinstance(reference_value, dict) else {}
                )
                _flatten(value, next_reference, full_key)
            else:
                suffix = (
                    f" (reference: {reference_value})"
                    if reference_value is not missing
                    else ""
                )
                out.line(out.styled(
                    f"{prefix}{full_key}: {value}{suffix}",
                    role="diff",
                ))

    _flatten(config, reference_values)
