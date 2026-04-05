"""
Minimal CLI for the AXIS Experimentation Framework.

Provides a thin, stateless command-line interface over the execution
and repository layers.  Every command reconstructs state from persisted
artifacts — no hidden caches or session state.

Usage::

    python -m axis_system_a.cli experiments list   --root ./experiments
    python -m axis_system_a.cli experiments run     <config_path> --root ./experiments
    python -m axis_system_a.cli experiments resume  <experiment_id> --root ./experiments
    python -m axis_system_a.cli experiments show    <experiment_id> --root ./experiments
    python -m axis_system_a.cli runs list --experiment <experiment_id> --root ./experiments
    python -m axis_system_a.cli runs show <run_id> --experiment <experiment_id> --root ./experiments
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml

from axis_system_a.experiment import ExperimentConfig
from axis_system_a.experiment_executor import ExperimentExecutor
from axis_system_a.repository import ExperimentRepository


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    # Shared flags available on every leaf sub-command so that
    # ``--root`` / ``--output`` can appear *anywhere* on the command line.
    # Uses SUPPRESS so leaf defaults don't overwrite a value already parsed
    # by the top-level parser when the flag appears before the sub-command.
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
  axis experiments run config.yaml --redo       Re-run, replacing old results
  axis experiments show <experiment_id>         Inspect experiment details
  axis experiments resume <experiment_id>       Resume incomplete experiment

  axis runs list --experiment <experiment_id>   List runs in an experiment
  axis runs show <run_id> --experiment <eid>    Inspect a specific run

  axis visualize --experiment <eid> --run <rid> --episode 1
                                                Open episode viewer
  axis visualize --experiment <eid> --run <rid> --episode 1 \\
       --start-step 10 --start-phase AFTER_ACTION
                                                Start at a specific step/phase

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
        description="Create, inspect, and manage experiments.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  axis experiments list
  axis experiments run experiments/configs/my_config.yaml
  axis experiments run experiments/configs/my_config.yaml --redo
  axis experiments show my-experiment
  axis experiments resume my-experiment
""",
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
    run_p.add_argument(
        "--redo", action="store_true", default=False,
        help="Delete existing experiment results and re-run from scratch",
    )

    resume_p = exp_action.add_parser(
        "resume", parents=[common], help="Resume an incomplete experiment")
    resume_p.add_argument(
        "experiment_id", help="ID of the experiment to resume")

    show_p = exp_action.add_parser(
        "show", parents=[common], help="Show experiment details (config, runs, summary)")
    show_p.add_argument(
        "experiment_id", help="ID of the experiment to inspect")

    # -- runs ----------------------------------------------------------------
    runs_parser = entity_sub.add_parser(
        "runs",
        help="Inspect runs within an experiment (list, show)",
        description="List and inspect individual runs inside an experiment.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  axis runs list --experiment my-experiment
  axis runs show run-001 --experiment my-experiment
""",
    )
    runs_action = runs_parser.add_subparsers(dest="action", title="actions")

    list_runs_p = runs_action.add_parser(
        "list", parents=[common], help="List all runs in an experiment")
    list_runs_p.add_argument(
        "--experiment", required=True, help="Experiment ID to list runs for",
    )

    show_run_p = runs_action.add_parser(
        "show", parents=[common],
        help="Show run details (config, episodes, summary statistics)",
    )
    show_run_p.add_argument("run_id", help="ID of the run to inspect")
    show_run_p.add_argument(
        "--experiment", required=True, help="Experiment ID the run belongs to",
    )

    # -- visualize -----------------------------------------------------------
    viz_parser = entity_sub.add_parser(
        "visualize", parents=[common],
        help="Launch interactive episode viewer (grid, overlays, step analysis)",
        description=(
            "Open the PySide6 visualization window for a specific episode. "
            "Shows the world grid, agent movement, debug overlays, and a "
            "step-by-step decision analysis panel."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  axis visualize --experiment my-exp --run run-001 --episode 1
  axis visualize --experiment my-exp --run run-001 --episode 1 --start-step 10
  axis visualize --experiment my-exp --run run-001 --episode 1 \\
       --start-step 5 --start-phase AFTER_ACTION
""",
    )
    viz_parser.add_argument(
        "--experiment", required=True, help="Experiment ID")
    viz_parser.add_argument(
        "--run", required=True, help="Run ID within the experiment")
    viz_parser.add_argument(
        "--episode", type=int, required=True,
        help="Episode index (1-based)",
    )
    viz_parser.add_argument(
        "--start-step", type=int, default=None,
        help="Step index to start at (0-based, default: 0)",
    )
    viz_parser.add_argument(
        "--start-phase",
        choices=["BEFORE", "AFTER_REGEN", "AFTER_ACTION"],
        default=None,
        help="Phase within the step to start at (default: BEFORE)",
    )

    return parser


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def _load_config_file(path: Path) -> ExperimentConfig:
    """Load and validate an ExperimentConfig from a JSON or YAML file."""
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    return ExperimentConfig.model_validate(data)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def _cmd_experiments_list(
    repo: ExperimentRepository, output: str,
) -> None:
    experiment_ids = repo.list_experiments()
    entries = []
    for eid in experiment_ids:
        entry: dict = {"experiment_id": eid}
        try:
            entry["status"] = repo.load_experiment_status(eid).value
        except Exception:
            entry["status"] = "unknown"
        try:
            meta = repo.load_experiment_metadata(eid)
            entry["name"] = meta.name
            entry["created_at"] = meta.created_at
        except Exception:
            pass
        runs = repo.list_runs(eid)
        entry["num_runs"] = len(runs)
        completed = 0
        for rid in runs:
            try:
                from axis_system_a.repository import RunStatus
                if repo.load_run_status(eid, rid) == RunStatus.COMPLETED:
                    completed += 1
            except Exception:
                pass
        entry["num_completed_runs"] = completed
        entries.append(entry)

    if output == "json":
        print(json.dumps(entries, indent=2))
    else:
        if not entries:
            print("No experiments found.")
            return
        for e in entries:
            parts = [
                e["experiment_id"],
                f"status={e['status']}",
                f"runs={e['num_runs']}",
                f"completed={e['num_completed_runs']}",
            ]
            if e.get("created_at"):
                parts.append(f"created={e['created_at']}")
            print("  ".join(parts))


def _cmd_experiments_run(
    repo: ExperimentRepository, config_path: str, output: str,
    *, redo: bool = False,
) -> None:
    path = Path(config_path)
    if not path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    try:
        config = _load_config_file(path)
    except Exception as exc:
        print(f"Error: Invalid config file: {exc}", file=sys.stderr)
        sys.exit(1)

    experiment_id = config.name or "<generated>"
    if redo:
        exp_dir = repo.experiment_dir(experiment_id)
        if exp_dir.exists():
            shutil.rmtree(exp_dir)

    try:
        result = ExperimentExecutor(repo).execute(config)
    except FileExistsError:
        print(
            f"Error: Experiment already exists: {experiment_id}. "
            f"Use --redo to overwrite.",
            file=sys.stderr,
        )
        sys.exit(1)

    experiment_id = config.name or result.run_results[0].run_id
    if output == "json":
        print(json.dumps({
            "experiment_id": experiment_id,
            "status": "completed",
            "num_runs": result.summary.num_runs,
        }, indent=2))
    else:
        print(f"Experiment '{experiment_id}' completed.")
        print(f"  Runs: {result.summary.num_runs}")


def _cmd_experiments_resume(
    repo: ExperimentRepository, experiment_id: str, output: str,
) -> None:
    if not repo.experiment_dir(experiment_id).exists():
        print(
            f"Error: Experiment not found: {experiment_id}", file=sys.stderr,
        )
        sys.exit(1)
    result = ExperimentExecutor(repo).resume(experiment_id)
    if output == "json":
        print(json.dumps({
            "experiment_id": experiment_id,
            "status": "completed",
            "num_runs": result.summary.num_runs,
        }, indent=2))
    else:
        print(f"Experiment '{experiment_id}' resumed and completed.")
        print(f"  Runs: {result.summary.num_runs}")


def _cmd_experiments_show(
    repo: ExperimentRepository, experiment_id: str, output: str,
) -> None:
    if not repo.experiment_dir(experiment_id).exists():
        print(
            f"Error: Experiment not found: {experiment_id}", file=sys.stderr,
        )
        sys.exit(1)

    info: dict = {"experiment_id": experiment_id}

    try:
        info["status"] = repo.load_experiment_status(experiment_id).value
    except Exception:
        info["status"] = "unknown"

    try:
        meta = repo.load_experiment_metadata(experiment_id)
        info["experiment_type"] = meta.experiment_type
        info["name"] = meta.name
        info["created_at"] = meta.created_at
    except Exception:
        pass

    try:
        config = repo.load_experiment_config(experiment_id)
        info["config"] = config.model_dump(mode="json")
    except Exception:
        pass

    runs = repo.list_runs(experiment_id)
    info["runs"] = runs

    try:
        summary = repo.load_experiment_summary(experiment_id)
        info["summary"] = summary.model_dump(mode="json")
    except Exception:
        info["summary"] = None

    if output == "json":
        print(json.dumps(info, indent=2))
    else:
        print(f"Experiment: {experiment_id}")
        print(f"  Status: {info.get('status', 'unknown')}")
        if info.get("experiment_type"):
            print(f"  Type: {info['experiment_type']}")
        if info.get("name"):
            print(f"  Name: {info['name']}")
        if info.get("created_at"):
            print(f"  Created: {info['created_at']}")
        print(f"  Runs: {runs}")
        if info.get("summary"):
            s = info["summary"]
            print(f"  Summary: {s['num_runs']} runs")
            for entry in s.get("run_entries", []):
                print(
                    f"    {entry['run_id']}  "
                    f"{entry.get('variation_description', '')}"
                )


def _cmd_runs_list(
    repo: ExperimentRepository, experiment_id: str, output: str,
) -> None:
    if not repo.experiment_dir(experiment_id).exists():
        print(
            f"Error: Experiment not found: {experiment_id}", file=sys.stderr,
        )
        sys.exit(1)

    from axis_system_a.repository import RunStatus

    run_ids = repo.list_runs(experiment_id)
    entries = []
    for rid in run_ids:
        entry: dict = {"run_id": rid}
        try:
            entry["status"] = repo.load_run_status(experiment_id, rid).value
        except Exception:
            entry["status"] = "unknown"
        try:
            meta = repo.load_run_metadata(experiment_id, rid)
            entry["variation_description"] = meta.variation_description
        except Exception:
            pass
        try:
            repo.load_run_summary(experiment_id, rid)
            entry["has_summary"] = True
        except Exception:
            entry["has_summary"] = False
        entries.append(entry)

    if output == "json":
        print(json.dumps(entries, indent=2))
    else:
        if not entries:
            print("No runs found.")
            return
        for e in entries:
            parts = [
                e["run_id"],
                f"status={e['status']}",
            ]
            if e.get("variation_description"):
                parts.append(e["variation_description"])
            if e.get("has_summary"):
                parts.append("summary=yes")
            print("  ".join(parts))


def _cmd_runs_show(
    repo: ExperimentRepository, experiment_id: str, run_id: str, output: str,
) -> None:
    if not repo.run_dir(experiment_id, run_id).exists():
        print(
            f"Error: Run not found: {run_id} in experiment {experiment_id}",
            file=sys.stderr,
        )
        sys.exit(1)

    info: dict = {"run_id": run_id, "experiment_id": experiment_id}

    try:
        info["status"] = repo.load_run_status(experiment_id, run_id).value
    except Exception:
        info["status"] = "unknown"

    try:
        meta = repo.load_run_metadata(experiment_id, run_id)
        info["variation_description"] = meta.variation_description
        info["created_at"] = meta.created_at
        info["base_seed"] = meta.base_seed
    except Exception:
        pass

    try:
        config = repo.load_run_config(experiment_id, run_id)
        info["config"] = config.model_dump(mode="json")
    except Exception:
        pass

    try:
        summary = repo.load_run_summary(experiment_id, run_id)
        info["summary"] = summary.model_dump(mode="json")
    except Exception:
        info["summary"] = None

    episodes = repo.list_episode_files(experiment_id, run_id)
    info["num_episodes"] = len(episodes)

    if output == "json":
        print(json.dumps(info, indent=2))
    else:
        print(f"Run: {run_id}")
        print(f"  Experiment: {experiment_id}")
        print(f"  Status: {info.get('status', 'unknown')}")
        if info.get("variation_description"):
            print(f"  Variation: {info['variation_description']}")
        if info.get("created_at"):
            print(f"  Created: {info['created_at']}")
        if info.get("base_seed") is not None:
            print(f"  Base seed: {info['base_seed']}")
        print(f"  Episodes: {info['num_episodes']}")
        if info.get("summary"):
            s = info["summary"]
            print(
                f"  Summary: mean_steps={s['mean_steps']:.1f}  "
                f"death_rate={s['death_rate']:.2f}  "
                f"mean_energy={s['mean_final_energy']:.1f}"
            )


def _cmd_visualize(
    repo: ExperimentRepository, args: argparse.Namespace,
) -> int:
    """Launch the interactive visualization session."""
    from axis_system_a.visualization.launch import launch_visualization_from_cli
    from axis_system_a.visualization.snapshot_models import ReplayPhase

    start_phase = ReplayPhase[args.start_phase] if args.start_phase else None

    return launch_visualization_from_cli(
        repository=repo,
        experiment_id=args.experiment,
        run_id=args.run,
        episode_index=args.episode,
        start_step=args.start_step,
        start_phase=start_phase,
    )


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns exit code (0=success, 1=error)."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.entity:
        parser.print_help()
        return 1

    repo = ExperimentRepository(Path(args.root))

    try:
        if args.entity == "visualize":
            return _cmd_visualize(repo, args)

        if not getattr(args, "action", None):
            parser.print_help()
            return 1

        output = args.output

        if args.entity == "experiments":
            if args.action == "list":
                _cmd_experiments_list(repo, output)
            elif args.action == "run":
                _cmd_experiments_run(
                    repo, args.config_path, output,
                    redo=getattr(args, "redo", False),
                )
            elif args.action == "resume":
                _cmd_experiments_resume(repo, args.experiment_id, output)
            elif args.action == "show":
                _cmd_experiments_show(repo, args.experiment_id, output)
            else:
                parser.print_help()
                return 1
        elif args.entity == "runs":
            if args.action == "list":
                _cmd_runs_list(repo, args.experiment, output)
            elif args.action == "show":
                _cmd_runs_show(repo, args.experiment, args.run_id, output)
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


if __name__ == "__main__":
    sys.exit(main())
