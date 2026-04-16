"""
System-agnostic CLI for the AXIS Experimentation Framework.

Provides a thin, stateless command-line interface over the execution
and repository layers.  Every command reconstructs state from persisted
artifacts -- no hidden caches or session state.

Usage::

    axis experiments list                         List all experiments
    axis experiments run  <config_path>           Run from config file
    axis experiments resume <experiment_id>       Resume incomplete experiment
    axis experiments show <experiment_id>         Inspect experiment details

    axis runs list --experiment <experiment_id>   List runs in an experiment
    axis runs show <run_id> --experiment <eid>    Inspect a specific run

    axis visualize --experiment <eid> --run <rid> --episode 1
                                                   (stub -- Phase 4)
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


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
  axis experiments run config.yaml              Run experiment from config
  axis experiments show <experiment_id>         Inspect experiment details
  axis experiments resume <experiment_id>       Resume incomplete experiment

  axis runs list --experiment <experiment_id>   List runs in an experiment
  axis runs show <run_id> --experiment <eid>    Inspect a specific run

  axis visualize --experiment <eid> --run <rid> --episode 1

  axis compare --reference-experiment <eid> --reference-run <rid> --reference-episode 0 \\
               --candidate-experiment <eid2> --candidate-run <rid2> --candidate-episode 0

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
        "--experiment", required=True, help="Experiment ID")
    viz_parser.add_argument(
        "--run", required=True, help="Run ID within the experiment")
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

    return parser


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def _load_config_file(path: Path):
    """Load and validate an ExperimentConfig from a JSON or YAML file."""
    from axis.framework.config import ExperimentConfig

    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        import yaml
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    return ExperimentConfig.model_validate(data)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def _cmd_experiments_list(repo, output: str) -> None:
    from axis.framework.persistence import RunStatus

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
            entry["system_type"] = meta.system_type
            entry["created_at"] = meta.created_at
        except Exception:
            pass
        runs = repo.list_runs(eid)
        entry["num_runs"] = len(runs)
        completed = 0
        for rid in runs:
            try:
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
            if e.get("system_type"):
                parts.append(f"system={e['system_type']}")
            if e.get("created_at"):
                parts.append(f"created={e['created_at']}")
            print("  ".join(parts))


def _cmd_experiments_run(repo, config_path: str, output: str) -> None:
    from axis.framework.experiment import ExperimentExecutor

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
        result = ExperimentExecutor(repository=repo).execute(config)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if output == "json":
        print(json.dumps({
            "experiment_id": result.experiment_id,
            "status": "completed",
            "num_runs": result.summary.num_runs,
        }, indent=2))
    else:
        print(f"Experiment completed.")
        print(f"  ID: {result.experiment_id}")
        print(f"  Runs: {result.summary.num_runs}")


def _cmd_experiments_resume(repo, experiment_id: str, output: str) -> None:
    from axis.framework.experiment import ExperimentExecutor

    if not repo.experiment_dir(experiment_id).exists():
        print(
            f"Error: Experiment not found: {experiment_id}", file=sys.stderr,
        )
        sys.exit(1)
    result = ExperimentExecutor(repository=repo).resume(experiment_id)
    if output == "json":
        print(json.dumps({
            "experiment_id": experiment_id,
            "status": "completed",
            "num_runs": result.summary.num_runs,
        }, indent=2))
    else:
        print(f"Experiment '{experiment_id}' resumed and completed.")
        print(f"  Runs: {result.summary.num_runs}")


def _cmd_experiments_show(repo, experiment_id: str, output: str) -> None:
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
        info["system_type"] = meta.system_type
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
        if info.get("system_type"):
            print(f"  System: {info['system_type']}")
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


def _cmd_runs_list(repo, experiment_id: str, output: str) -> None:
    from axis.framework.persistence import RunStatus

    if not repo.experiment_dir(experiment_id).exists():
        print(
            f"Error: Experiment not found: {experiment_id}", file=sys.stderr,
        )
        sys.exit(1)

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


def _cmd_runs_show(repo, experiment_id: str, run_id: str, output: str) -> None:
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
                f"mean_final_vitality={s['mean_final_vitality']:.3f}"
            )


def _cmd_compare(args: argparse.Namespace, repo, output: str) -> None:
    """Run paired trace comparison between two episodes or full runs."""
    ref_ep = args.reference_episode
    cand_ep = args.candidate_episode

    # Validate: both or neither episode flags must be provided.
    if (ref_ep is None) != (cand_ep is None):
        print(
            "Error: --reference-episode and --candidate-episode must both be "
            "provided (single-episode mode) or both omitted (run-level mode).",
            file=sys.stderr,
        )
        sys.exit(1)

    if ref_ep is not None:
        _cmd_compare_episode(args, repo, output)
    else:
        _cmd_compare_runs(args, repo, output)


def _cmd_compare_episode(args: argparse.Namespace, repo, output: str) -> None:
    """Single-episode comparison (existing behavior)."""
    from axis.framework.comparison import compare_episode_traces

    ref_trace = repo.load_episode_trace(
        args.reference_experiment, args.reference_run, args.reference_episode,
    )
    cand_trace = repo.load_episode_trace(
        args.candidate_experiment, args.candidate_run, args.candidate_episode,
    )

    ref_config = None
    cand_config = None
    ref_meta = None
    cand_meta = None
    try:
        ref_config = repo.load_run_config(
            args.reference_experiment, args.reference_run)
    except Exception:
        pass
    try:
        cand_config = repo.load_run_config(
            args.candidate_experiment, args.candidate_run)
    except Exception:
        pass
    try:
        ref_meta = repo.load_run_metadata(
            args.reference_experiment, args.reference_run)
    except Exception:
        pass
    try:
        cand_meta = repo.load_run_metadata(
            args.candidate_experiment, args.candidate_run)
    except Exception:
        pass

    result = compare_episode_traces(
        ref_trace,
        cand_trace,
        reference_run_config=ref_config,
        candidate_run_config=cand_config,
        reference_run_metadata=ref_meta,
        candidate_run_metadata=cand_meta,
        reference_episode_index=args.reference_episode,
        candidate_episode_index=args.candidate_episode,
    )

    if output == "json":
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    else:
        _print_comparison_text(result)


def _cmd_compare_runs(args: argparse.Namespace, repo, output: str) -> None:
    """Full-run comparison with statistical summary."""
    from axis.framework.comparison import compare_runs

    result = compare_runs(
        repo,
        args.reference_experiment, args.reference_run,
        args.candidate_experiment, args.candidate_run,
    )

    if output == "json":
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    else:
        _print_run_comparison_text(result)


def _print_run_comparison_text(result) -> None:
    """Pretty-print a RunComparisonResult in text mode."""
    s = result.summary
    print(
        f"Run Comparison: {result.reference_system_type} vs "
        f"{result.candidate_system_type}")
    print(
        f"  Reference: experiment={result.reference_experiment_id} "
        f"run={result.reference_run_id}")
    print(
        f"  Candidate: experiment={result.candidate_experiment_id} "
        f"run={result.candidate_run_id}")
    print(
        f"  Episodes: {s.num_episodes_compared} compared, "
        f"{s.num_valid_pairs} valid, {s.num_invalid_pairs} invalid")
    print()

    if s.num_valid_pairs == 0:
        print("  No valid pairs to summarise.")
        return

    print("  --- Per-episode results ---")
    for r in result.episode_results:
        ep = r.identity.reference_episode_index
        if r.result_mode.value != "comparison_succeeded":
            print(f"  Episode {ep}: VALIDATION FAILED ({', '.join(r.validation.errors)})")
            continue
        m = r.metrics
        o = r.outcome
        assert m is not None and o is not None
        print(
            f"  Episode {ep}: mismatch={m.action_divergence.action_mismatch_rate:.1%}, "
            f"pos_div={m.position_divergence.mean_trajectory_distance:.2f}, "
            f"steps={o.reference_total_steps}/{o.candidate_total_steps}, "
            f"survivor={o.longer_survivor}")
    print()

    print("  --- Statistical summary (across all valid episode pairs) ---")
    print()
    _print_metric("Action mismatch rate", s.action_mismatch_rate)
    print(
        "      How often the two agents chose different actions at the same "
        "timestep.")
    print(
        "      0% = identical behavior, 100% = every decision differed.")
    print()
    _print_metric("Mean trajectory distance", s.mean_trajectory_distance)
    print(
        "      Average Manhattan distance (grid cells) between the two agents "
        "per episode.")
    print(
        "      0 = agents always on the same cell, higher = paths diverged "
        "on the grid.")
    print()
    _print_metric("Mean vitality difference", s.mean_vitality_difference)
    print(
        "      Average absolute difference in health (vitality) between the "
        "agents per episode.")
    print(
        "      0 = identical health curves, higher = one agent was "
        "consistently healthier.")
    print()
    _print_metric("Final vitality delta", s.final_vitality_delta, signed=True)
    print(
        "      Candidate's final vitality minus reference's final vitality.")
    print(
        "      Positive = candidate ended healthier, "
        "negative = reference ended healthier.")
    print()
    _print_metric("Total steps delta", s.total_steps_delta, signed=True)
    print(
        "      Candidate's episode length minus reference's episode length.")
    print(
        "      Positive = candidate survived longer, "
        "negative = reference survived longer.")
    print()
    print(
        f"  Survival rates: reference={s.reference_survival_rate:.0%}, "
        f"candidate={s.candidate_survival_rate:.0%}")
    print(
        "      Fraction of episodes where the agent reached max_steps "
        "(was not terminated early).")
    print()
    print(
        f"  Longer survivor: candidate={s.candidate_longer_count}, "
        f"reference={s.reference_longer_count}, equal={s.equal_count}")
    print(
        "      Per-episode count of which system lasted more steps.")


def _print_metric(label: str, stats, *, signed: bool = False) -> None:
    fmt = "+.4f" if signed else ".4f"
    print(
        f"  {label}: mean={stats.mean:{fmt}}, std={stats.std:.4f}, "
        f"min={stats.min:{fmt}}, max={stats.max:{fmt}} (n={stats.n})"
    )


def _print_comparison_text(result) -> None:
    """Pretty-print a PairedTraceComparisonResult in text mode."""
    print(f"Comparison: {result.result_mode.value}")
    i = result.identity
    print(f"  Reference: {i.reference_system_type}", end="")
    if i.reference_run_id:
        print(f" run={i.reference_run_id}", end="")
    print()
    print(f"  Candidate: {i.candidate_system_type}", end="")
    if i.candidate_run_id:
        print(f" run={i.candidate_run_id}", end="")
    print()

    v = result.validation
    if not v.is_valid_pair:
        print(f"  Validation FAILED: {', '.join(v.errors)}")
        return

    if result.alignment:
        a = result.alignment
        print(
            f"  Alignment: {a.aligned_steps} aligned steps "
            f"(ref={a.reference_total_steps}, cand={a.candidate_total_steps})")

    if result.metrics:
        m = result.metrics
        ad = m.action_divergence
        print(
            f"  Action divergence: first={ad.first_action_divergence_step}, "
            f"mismatch={ad.action_mismatch_count} "
            f"({ad.action_mismatch_rate:.1%})")
        pd = m.position_divergence
        print(
            f"  Position divergence: mean={pd.mean_trajectory_distance:.2f}, "
            f"max={pd.max_trajectory_distance}")
        vd = m.vitality_divergence
        print(
            f"  Vitality divergence: mean={vd.mean_absolute_difference:.4f}, "
            f"max={vd.max_absolute_difference:.4f}")

    if result.outcome:
        o = result.outcome
        print(
            f"  Outcome: ref={o.reference_total_steps} steps "
            f"({o.reference_termination_reason}), "
            f"cand={o.candidate_total_steps} steps "
            f"({o.candidate_termination_reason})")
        print(
            f"  Vitality delta: {o.final_vitality_delta:+.4f}, "
            f"longer survivor: {o.longer_survivor}")

    if result.system_specific_analysis:
        for key, data in result.system_specific_analysis.items():
            print(f"  Extension [{key}]:")
            if isinstance(data, dict):
                for k, val in data.items():
                    print(f"    {k}: {val}")


def _cmd_visualize(args: argparse.Namespace, repo) -> None:
    """Launch the interactive visualization viewer."""
    from axis.visualization.launch import launch_visualization

    episode_index = args.episode
    sys.exit(launch_visualization(
        repo, args.experiment, args.run, episode_index,
        start_step=args.step, start_phase=args.phase,
        scale=args.scale,
    ))


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns exit code (0=success, 1=error)."""
    from axis.framework.persistence import ExperimentRepository
    from axis.plugins import discover_plugins

    discover_plugins()

    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.entity:
        parser.print_help()
        return 1

    repo = ExperimentRepository(Path(args.root))

    try:
        if args.entity == "visualize":
            _cmd_visualize(args, repo)
            return 0

        if args.entity == "compare":
            _cmd_compare(args, repo, args.output)
            return 0

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
