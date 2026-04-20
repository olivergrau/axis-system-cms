"""CLI commands for workspace management."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


def cmd_workspaces_scaffold(output: str) -> None:
    """Interactive workspace scaffolding."""
    import questionary
    from rich.console import Console

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

    workspace_id = questionary.text("Workspace ID:").ask()
    if not workspace_id:
        print("Aborted.", file=sys.stderr)
        sys.exit(1)

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
        manifest_data["system_under_test"] = questionary.text(
            "System under test:",
        ).ask() or "system_a"

    elif ws_type == "system_comparison":
        manifest_data["reference_system"] = questionary.text(
            "Reference system:",
        ).ask() or "system_a"
        manifest_data["candidate_system"] = questionary.text(
            "Candidate system:",
        ).ask() or "system_a"

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
        if result.is_valid and not drift_issues:
            print(f"Workspace '{ws.name}': VALID")
        elif result.is_valid:
            print(f"Workspace '{ws.name}': VALID (with drift warnings)")
        else:
            print(f"Workspace '{ws.name}': INVALID")

        for issue in result.issues:
            print(f"  [{issue.severity}] {issue.message}")
        for issue in drift_issues:
            print(f"  [drift:{issue.severity}] {issue.message}")


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
        print(f"Workspace: {summary.workspace_id}")
        print(f"  Title: {summary.title}")
        print(f"  Class: {summary.workspace_class}")
        print(f"  Type: {summary.workspace_type}")
        print(f"  Status: {summary.status}")
        print(f"  Lifecycle: {summary.lifecycle_stage}")
        if summary.description:
            print(f"  Description: {summary.description}")
        if summary.question:
            print(f"  Question: {summary.question}")
        if summary.development_goal:
            print(f"  Goal: {summary.development_goal}")
        if summary.system_under_test:
            print(f"  System under test: {summary.system_under_test}")
        if summary.reference_system:
            print(f"  Reference: {summary.reference_system}")
        if summary.candidate_system:
            print(f"  Candidate: {summary.candidate_system}")
        if summary.artifact_under_development:
            print(f"  Artifact: {summary.artifact_under_development}")
        _print_artifact_section("Primary configs", summary.primary_configs)
        _print_artifact_section("Primary results", summary.primary_results)
        _print_artifact_section(
            "Primary comparisons", summary.primary_comparisons)
        _print_artifact_section(
            "Primary measurements", summary.primary_measurements)
        if summary.development_state:
            print(f"  Development state: {summary.development_state}")
            if summary.baseline_config:
                print(f"  Baseline config: {summary.baseline_config}")
            if summary.candidate_config:
                print(f"  Candidate config: {summary.candidate_config}")
            _print_artifact_section(
                "Baseline results", summary.baseline_results)
            _print_artifact_section(
                "Candidate results", summary.candidate_results)
            if summary.current_candidate_result:
                marker = "OK" if summary.current_candidate_result.exists else "MISSING"
                print(
                    f"  Current candidate result: [{marker}] {summary.current_candidate_result.path}")
            if summary.current_validation_comparison:
                marker = "OK" if summary.current_validation_comparison.exists else "MISSING"
                print(
                    f"  Current validation comparison: [{marker}] {summary.current_validation_comparison.path}")
                # Show which baseline was used in the last comparison
                if summary.current_validation_comparison.exists:
                    _print_comparison_targets(
                        ws, summary.current_validation_comparison.path)
        if summary.check_result:
            status = "VALID" if summary.check_result.is_valid else "INVALID"
            print(f"  Validation: {status}")


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

    print(f"Sweep Result: {result['experiment_id']}")
    print(f"  System: {result['system_type']}")
    if result.get("parameter_path"):
        print(f"  Parameter: {result['parameter_path']}")
    if result.get("parameter_values"):
        print(f"  Values: {result['parameter_values']}")
    print(f"  Baseline run: {result['baseline_run_id']}")
    print(f"  Runs: {result['num_runs']}")
    print()
    for rd in result.get("runs", []):
        label = rd.get("variation", rd["run_id"])
        parts = [f"  {rd['run_id']}  {label}"]
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
        print("  ".join(parts))


def cmd_workspaces_set_candidate(
    workspace_path: str, config_path: str, output: str,
    run_service: object = None,
) -> None:
    """Set the candidate config for a development workspace."""
    run_service.set_candidate(Path(workspace_path), config_path)
    print(f"Candidate config set: {config_path}")


def cmd_workspaces_run(
    workspace_path: str, output: str,
    run_filter: str | None = None,
    run_service: object = None,
) -> None:
    """Execute workspace configs."""
    ws = Path(workspace_path)
    summaries = run_service.execute(ws, run_filter=run_filter)

    if output == "json":
        print(json.dumps([{
            "experiment_id": s.experiment_id,
            "num_runs": s.num_runs,
        } for s in summaries], indent=2))
    else:
        print(
            f"Workspace execution completed: {len(summaries)} experiment(s)")
        for s in summaries:
            print(f"  {s.experiment_id}: {s.num_runs} run(s)")


def cmd_workspaces_compare(
    workspace_path: str,
    output: str,
    reference_experiment: str | None = None,
    candidate_experiment: str | None = None,
    compare_service: object = None,
) -> None:
    """Run workspace comparison."""
    ws = Path(workspace_path)
    svc_result = compare_service.compare(
        ws, reference_experiment, candidate_experiment)

    if output == "json":
        # Re-read the envelope for full JSON output.
        env_path = ws / svc_result.output_path
        print(env_path.read_text())
    else:
        print(
            f"Workspace comparison #{svc_result.comparison_number} completed.")
        print(f"  Output: {ws / svc_result.output_path}")


def cmd_workspaces_comparison_result(
    workspace_path: str,
    output: str,
    comparison_number: int | None = None,
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
        print(
            f"Error: comparison-result is only valid for "
            f"system_comparison, system_development, or single_system "
            f"workspaces, got '{manifest.workspace_type}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    comparisons_dir = ws / "comparisons"
    if not comparisons_dir.is_dir():
        print("Error: No comparisons directory found.", file=sys.stderr)
        sys.exit(1)

    import re
    files = sorted(
        f for f in comparisons_dir.iterdir()
        if re.match(r"comparison-\d+\.json$", f.name)
    )
    if not files:
        print("Error: No comparison results found.", file=sys.stderr)
        sys.exit(1)

    if comparison_number is not None:
        target = comparisons_dir / f"comparison-{comparison_number:03d}.json"
        if not target.is_file():
            print(
                f"Error: Comparison #{comparison_number} not found. "
                f"Available: {', '.join(f.name for f in files)}",
                file=sys.stderr,
            )
            sys.exit(1)
        files = [target]
    elif len(files) == 1:
        pass  # show the only one
    else:
        # List available comparisons
        if output == "json":
            listing = []
            for f in files:
                env = WorkspaceComparisonEnvelope.model_validate(
                    json.loads(f.read_text()))
                cr = env.comparison_result
                listing.append({
                    "number": env.comparison_number,
                    "timestamp": env.timestamp,
                    "reference_system": cr.get("reference_system_type", ""),
                    "candidate_system": cr.get("candidate_system_type", ""),
                    "file": f.name,
                })
            print(json.dumps(listing, indent=2))
        else:
            print(f"Found {len(files)} comparison result(s). "
                  f"Use --number to select one:\n")
            for f in files:
                env = WorkspaceComparisonEnvelope.model_validate(
                    json.loads(f.read_text()))
                cr = env.comparison_result
                ref_sys = cr.get("reference_system_type", "?")
                cand_sys = cr.get("candidate_system_type", "?")
                print(f"  #{env.comparison_number}: {ref_sys} vs {cand_sys} "
                      f"({env.timestamp})")
        return

    # Display the selected comparison
    env = WorkspaceComparisonEnvelope.model_validate(
        json.loads(files[0].read_text()))

    if output == "json":
        print(json.dumps(env.model_dump(mode="json"), indent=2))
    else:
        print(f"Comparison #{env.comparison_number} — {env.timestamp}")
        print()
        # Print the comparison metrics using the existing formatter.
        result = RunComparisonResult.model_validate(env.comparison_result)
        print_run_comparison_text(result)
        print()
        print("  --- Configurations ---")
        print(
            f"  Reference config (system_type={env.reference_config.get('system_type', '?')}):")
        _print_config_summary(env.reference_config, indent=4)
        print(
            f"  Candidate config (system_type={env.candidate_config.get('system_type', '?')}):")
        _print_config_summary(env.candidate_config, indent=4)


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def _print_comparison_targets(ws: Path, comparison_path: str) -> None:
    """Print the reference/candidate experiment IDs from a comparison file."""
    cmp_file = ws / comparison_path
    try:
        data = json.loads(cmp_file.read_text())
        cr = data.get("comparison_result", {})
        ref_eid = cr.get("reference_experiment_id", "?")
        cand_eid = cr.get("candidate_experiment_id", "?")
        print(f"    Reference used: {ref_eid}")
        print(f"    Candidate used: {cand_eid}")
    except Exception:
        pass


def _print_artifact_section(label: str, entries: list) -> None:
    """Print a primary artifact section with existence markers."""
    if not entries:
        print(f"  {label}: (none declared)")
        return
    found = sum(1 for e in entries if e.exists)
    print(f"  {label}: {found}/{len(entries)} present")
    for e in entries:
        marker = "OK" if e.exists else "MISSING"
        extra = ""
        annotations = []
        if getattr(e, "config", None):
            annotations.append(e.config)
        if getattr(e, "output_form", None):
            annotations.append(e.output_form)
        if getattr(e, "role", None):
            annotations.append(f"role={e.role}")
        if getattr(e, "timestamp", None):
            annotations.append(e.timestamp)
        if annotations:
            extra = f"  ({', '.join(annotations)})"
        print(f"    [{marker}] {e.path}{extra}")


def _print_config_summary(config: dict, indent: int = 4) -> None:
    """Print a full experiment config as flattened key-value pairs.

    Excludes the ``logging`` section and keys with None values.
    """
    prefix = " " * indent
    _EXCLUDED_SECTIONS = {"logging"}

    def _flatten(obj: dict, path: str = "") -> None:
        for key, value in obj.items():
            full_key = f"{path}.{key}" if path else key
            top_level_key = full_key.split(".")[0]
            if top_level_key in _EXCLUDED_SECTIONS:
                continue
            if value is None:
                continue
            if isinstance(value, dict):
                _flatten(value, full_key)
            else:
                print(f"{prefix}{full_key}: {value}")

    _flatten(config)
