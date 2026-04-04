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
    )
    parser.add_argument(
        "--root", default="./experiments/results",
        help="Path to experiment repository root (default: ./experiments/results)",
    )
    parser.add_argument(
        "--output", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )

    entity_sub = parser.add_subparsers(dest="entity")

    # -- experiments ---------------------------------------------------------
    exp_parser = entity_sub.add_parser("experiments")
    exp_action = exp_parser.add_subparsers(dest="action")

    exp_action.add_parser(
        "list", parents=[common], help="List all experiments")

    run_p = exp_action.add_parser(
        "run", parents=[common], help="Execute a new experiment")
    run_p.add_argument("config_path", help="Path to experiment config file")

    resume_p = exp_action.add_parser(
        "resume", parents=[common], help="Resume an experiment")
    resume_p.add_argument("experiment_id")

    show_p = exp_action.add_parser(
        "show", parents=[common], help="Show experiment details")
    show_p.add_argument("experiment_id")

    # -- runs ----------------------------------------------------------------
    runs_parser = entity_sub.add_parser("runs")
    runs_action = runs_parser.add_subparsers(dest="action")

    list_runs_p = runs_action.add_parser(
        "list", parents=[common], help="List runs")
    list_runs_p.add_argument("--experiment", required=True)

    show_run_p = runs_action.add_parser(
        "show", parents=[common], help="Show run details")
    show_run_p.add_argument("run_id")
    show_run_p.add_argument("--experiment", required=True)

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
    try:
        result = ExperimentExecutor(repo).execute(config)
    except FileExistsError:
        experiment_id = config.name or "<generated>"
        print(
            f"Error: Experiment already exists: {experiment_id}",
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

    if not args.action:
        parser.print_help()
        return 1

    repo = ExperimentRepository(Path(args.root))
    output = args.output

    try:
        if args.entity == "experiments":
            if args.action == "list":
                _cmd_experiments_list(repo, output)
            elif args.action == "run":
                _cmd_experiments_run(repo, args.config_path, output)
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
