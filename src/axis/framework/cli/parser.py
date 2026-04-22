"""CLI argument parser construction."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--root", default=argparse.SUPPRESS,
        help="Path to experiment repository root (default: ./experiments/results)",
    )
    common.add_argument(
        "--output", choices=["text", "json"], default=argparse.SUPPRESS,
        help="Output format (default: text)",
    )

    parser = argparse.ArgumentParser(
        prog="axis",
        description="AXIS Experimentation Framework CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  axis experiments list                         List all experiments
  axis experiments run config.yaml              Run experiment from config
  axis experiments show <experiment_id>         Inspect experiment details
  axis experiments resume <experiment_id>       Resume incomplete experiment

  axis runs list --experiment <experiment_id>   List runs in an experiment
  axis runs show <run_id> --experiment <eid>    Inspect a specific run

  axis visualize --experiment <eid> --run <rid> --episode 1

  axis compare --reference-experiment <eid> --reference-run <rid> --reference-episode 0 \\
               --candidate-experiment <eid2> --candidate-run <rid2> --candidate-episode 0

  axis workspaces show <workspace-path>         Inspect workspace state
  axis workspaces compare <workspace-path>      Run a workspace comparison

  Use --output json on any command for machine-readable output.
  Use --root <path> to point to a non-default repository location.
""",
    )
    parser.add_argument(
        "--root", default="./experiments/results",
        help="Path to experiment repository root (default: ./experiments/results)",
    )
    parser.add_argument(
        "--output", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )

    entity_sub = parser.add_subparsers(dest="entity", title="commands")

    # -- experiments ---------------------------------------------------------
    exp_parser = entity_sub.add_parser(
        "experiments",
        help="Manage experiments (list, run, resume, show)",
    )
    exp_action = exp_parser.add_subparsers(dest="action", title="actions")

    exp_action.add_parser(
        "list", parents=[common], help="List all experiments")

    run_p = exp_action.add_parser(
        "run", parents=[common],
        help="Execute a new experiment from a YAML/JSON config file",
    )
    run_p.add_argument(
        "config_path", help="Path to experiment config (YAML or JSON)")

    resume_p = exp_action.add_parser(
        "resume", parents=[common], help="Resume an incomplete experiment")
    resume_p.add_argument(
        "experiment_id", help="ID of the experiment to resume")

    show_p = exp_action.add_parser(
        "show", parents=[common], help="Show experiment details")
    show_p.add_argument(
        "experiment_id", help="ID of the experiment to inspect")

    # -- runs ----------------------------------------------------------------
    runs_parser = entity_sub.add_parser(
        "runs",
        help="Inspect runs within an experiment (list, show)",
    )
    runs_action = runs_parser.add_subparsers(dest="action", title="actions")

    list_runs_p = runs_action.add_parser(
        "list", parents=[common], help="List all runs in an experiment")
    list_runs_p.add_argument(
        "--experiment", required=True, help="Experiment ID",
    )

    show_run_p = runs_action.add_parser(
        "show", parents=[common], help="Show run details",
    )
    show_run_p.add_argument("run_id", help="ID of the run to inspect")
    show_run_p.add_argument(
        "--experiment", required=True, help="Experiment ID the run belongs to",
    )

    # -- compare -------------------------------------------------------------
    cmp_parser = entity_sub.add_parser(
        "compare", parents=[common],
        help="Compare two episode traces or full runs (paired trace comparison)",
    )
    cmp_parser.add_argument(
        "--reference-experiment", required=True, help="Reference experiment ID")
    cmp_parser.add_argument(
        "--reference-run", required=True, help="Reference run ID")
    cmp_parser.add_argument(
        "--reference-episode", type=int, default=None,
        help="Reference episode index (omit for full-run comparison)")
    cmp_parser.add_argument(
        "--candidate-experiment", required=True, help="Candidate experiment ID")
    cmp_parser.add_argument(
        "--candidate-run", required=True, help="Candidate run ID")
    cmp_parser.add_argument(
        "--candidate-episode", type=int, default=None,
        help="Candidate episode index (omit for full-run comparison)")

    # -- visualize -----------------------------------------------------------
    viz_parser = entity_sub.add_parser(
        "visualize", parents=[common],
        help="Launch interactive episode viewer",
    )
    viz_parser.add_argument(
        "--experiment", default=None, help="Experiment ID")
    viz_parser.add_argument(
        "--run", default=None, help="Run ID within the experiment")
    viz_parser.add_argument(
        "--workspace", default=None,
        help="Workspace path (alternative to --experiment/--run)")
    viz_parser.add_argument(
        "--role", default=None,
        help="Role filter for workspace visualization (reference/candidate)")
    viz_parser.add_argument(
        "--episode", type=int, required=True, help="Episode index (1-based)",
    )
    viz_parser.add_argument(
        "--step", type=int, default=None, help="Initial step (0-based)",
    )
    viz_parser.add_argument(
        "--phase", type=int, default=None, help="Initial phase index",
    )
    viz_parser.add_argument(
        "--scale", type=float, default=1.0,
        help="UI scale factor (default: 1.0). E.g. 1.5 for a larger window.",
    )

    # -- workspaces ------------------------------------------------------------
    ws_parser = entity_sub.add_parser(
        "workspaces",
        help="Manage experiment workspaces (scaffold, check, show, run, compare)",
    )
    ws_action = ws_parser.add_subparsers(dest="action", title="actions")

    ws_action.add_parser(
        "scaffold", parents=[common],
        help="Interactively create a new workspace",
    )

    ws_check_p = ws_action.add_parser(
        "check", parents=[common], help="Validate a workspace",
    )
    ws_check_p.add_argument(
        "workspace_path", help="Path to workspace directory")

    ws_show_p = ws_action.add_parser(
        "show", parents=[common], help="Show workspace summary",
    )
    ws_show_p.add_argument(
        "workspace_path", help="Path to workspace directory")

    ws_run_p = ws_action.add_parser(
        "run", parents=[common], help="Execute workspace configs",
    )
    ws_run_p.add_argument(
        "workspace_path", help="Path to workspace directory")
    ws_run_p.add_argument(
        "--baseline-only", action="store_true", default=False,
        help="Run only the baseline config (system_development)")
    ws_run_p.add_argument(
        "--candidate-only", action="store_true", default=False,
        help="Run only the candidate config (system_development)")

    ws_cmp_p = ws_action.add_parser(
        "compare", parents=[common], help="Run workspace comparison",
    )
    ws_cmp_p.add_argument(
        "workspace_path", help="Path to workspace directory")
    ws_cmp_p.add_argument(
        "--reference-experiment", default=None,
        help="Experiment ID for reference side (must exist in workspace results)")
    ws_cmp_p.add_argument(
        "--candidate-experiment", default=None,
        help="Experiment ID for candidate side (must exist in workspace results)")

    ws_cr_p = ws_action.add_parser(
        "comparison-result", parents=[common],
        help="Display stored workspace comparison result(s)",
    )
    ws_cr_p.add_argument(
        "workspace_path", help="Path to workspace directory")
    ws_cr_p.add_argument(
        "--number", type=int, default=None,
        help="Comparison number to display (e.g. 1, 2). "
             "If omitted, lists all or shows the only one.")

    ws_sc_p = ws_action.add_parser(
        "set-candidate", parents=[common],
        help="Set the candidate config for a development workspace",
    )
    ws_sc_p.add_argument(
        "workspace_path", help="Path to workspace directory")
    ws_sc_p.add_argument(
        "config_path",
        help="Workspace-relative path to the candidate config file "
             "(e.g. configs/candidate-system_demo.yaml)")

    ws_sr_p = ws_action.add_parser(
        "sweep-result", parents=[common],
        help="Inspect a sweep (OFAT) result in a workspace",
    )
    ws_sr_p.add_argument(
        "workspace_path", help="Path to workspace directory")
    ws_sr_p.add_argument(
        "--experiment", default=None,
        help="Explicit experiment ID (defaults to newest sweep)")

    return parser
