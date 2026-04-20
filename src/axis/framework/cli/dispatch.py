"""CLI command dispatch."""

from __future__ import annotations

import argparse
import sys

from axis.framework.cli.commands.compare import cmd_compare
from axis.framework.cli.commands.experiments import (
    cmd_experiments_list,
    cmd_experiments_resume,
    cmd_experiments_run,
    cmd_experiments_show,
)
from axis.framework.cli.commands.runs import cmd_runs_list, cmd_runs_show
from axis.framework.cli.commands.visualize import cmd_visualize
from axis.framework.cli.commands.workspaces import (
    cmd_workspaces_check,
    cmd_workspaces_compare,
    cmd_workspaces_comparison_result,
    cmd_workspaces_run,
    cmd_workspaces_scaffold,
    cmd_workspaces_set_candidate,
    cmd_workspaces_show,
    cmd_workspaces_sweep_result,
)


def dispatch(
    args: argparse.Namespace,
    ctx: object,
    parser: argparse.ArgumentParser,
) -> int:
    """Route parsed CLI arguments to the appropriate command handler.

    Returns an integer exit code (0 = success, 1 = error).

    *ctx* is a ``CLIContext`` instance carrying the composed dependencies.
    """
    repo = ctx.repo  # type: ignore[attr-defined]
    catalogs = ctx.catalogs  # type: ignore[attr-defined]
    try:
        if args.entity == "visualize":
            cmd_visualize(args, repo, catalogs=catalogs)
            return 0

        if args.entity == "compare":
            cmd_compare(args, repo, args.output, catalogs=catalogs)
            return 0

        if not getattr(args, "action", None):
            parser.print_help()
            return 1

        output = args.output

        if args.entity == "experiments":
            if args.action == "list":
                cmd_experiments_list(repo, output)
            elif args.action == "run":
                cmd_experiments_run(
                    repo, args.config_path, output,
                    catalogs=catalogs,
                )
            elif args.action == "resume":
                cmd_experiments_resume(
                    repo, args.experiment_id, output,
                    catalogs=catalogs,
                )
            elif args.action == "show":
                cmd_experiments_show(repo, args.experiment_id, output)
            else:
                parser.print_help()
                return 1
        elif args.entity == "runs":
            if args.action == "list":
                cmd_runs_list(repo, args.experiment, output)
            elif args.action == "show":
                cmd_runs_show(repo, args.experiment, args.run_id, output)
            else:
                parser.print_help()
                return 1
        elif args.entity == "workspaces":
            if args.action == "scaffold":
                cmd_workspaces_scaffold(output)
            elif args.action == "check":
                cmd_workspaces_check(
                    args.workspace_path, output,
                    inspection_service=ctx.inspection_service)
            elif args.action == "show":
                cmd_workspaces_show(
                    args.workspace_path, output,
                    inspection_service=ctx.inspection_service)
            elif args.action == "run":
                run_filter = None
                if getattr(args, "baseline_only", False):
                    run_filter = "baseline"
                elif getattr(args, "candidate_only", False):
                    run_filter = "candidate"
                cmd_workspaces_run(
                    args.workspace_path, output,
                    run_filter=run_filter,
                    run_service=ctx.run_service)
            elif args.action == "compare":
                cmd_workspaces_compare(
                    args.workspace_path, output,
                    reference_experiment=getattr(
                        args, "reference_experiment", None),
                    candidate_experiment=getattr(
                        args, "candidate_experiment", None),
                    compare_service=ctx.compare_service)
            elif args.action == "comparison-result":
                cmd_workspaces_comparison_result(
                    args.workspace_path, output,
                    comparison_number=getattr(args, "number", None),
                )
            elif args.action == "set-candidate":
                cmd_workspaces_set_candidate(
                    args.workspace_path, args.config_path, output,
                    run_service=ctx.run_service)
            elif args.action == "sweep-result":
                cmd_workspaces_sweep_result(
                    args.workspace_path, output,
                    experiment=getattr(args, "experiment", None),
                    inspection_service=ctx.inspection_service,
                )
            else:
                parser.print_help()
                return 1
        else:
            parser.print_help()
            return 1
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0
