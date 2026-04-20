"""CLI commands for experiment management."""

from __future__ import annotations

import json
import sys
from pathlib import Path


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


def cmd_experiments_list(repo, output: str) -> None:
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
            if meta.output_form:
                entry["output_form"] = meta.output_form
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
            if e.get("output_form"):
                parts.append(f"form={e['output_form']}")
            if e.get("system_type"):
                parts.append(f"system={e['system_type']}")
            if e.get("created_at"):
                parts.append(f"created={e['created_at']}")
            print("  ".join(parts))


def cmd_experiments_run(
    repo, config_path: str, output: str,
    catalogs: dict | None = None,
) -> None:
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
        result = ExperimentExecutor(
            repository=repo,
            system_catalog=catalogs.get("systems") if catalogs else None,
            world_catalog=catalogs.get("worlds") if catalogs else None,
        ).execute(config)
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


def cmd_experiments_resume(
    repo, experiment_id: str, output: str,
    catalogs: dict | None = None,
) -> None:
    from axis.framework.experiment import ExperimentExecutor

    if not repo.experiment_dir(experiment_id).exists():
        print(
            f"Error: Experiment not found: {experiment_id}", file=sys.stderr,
        )
        sys.exit(1)
    result = ExperimentExecutor(
        repository=repo,
        system_catalog=catalogs.get("systems") if catalogs else None,
        world_catalog=catalogs.get("worlds") if catalogs else None,
    ).resume(experiment_id)
    if output == "json":
        print(json.dumps({
            "experiment_id": experiment_id,
            "status": "completed",
            "num_runs": result.summary.num_runs,
        }, indent=2))
    else:
        print(f"Experiment '{experiment_id}' resumed and completed.")
        print(f"  Runs: {result.summary.num_runs}")


def cmd_experiments_show(repo, experiment_id: str, output: str) -> None:
    if not repo.experiment_dir(experiment_id).exists():
        print(
            f"Error: Experiment not found: {experiment_id}", file=sys.stderr,
        )
        sys.exit(1)

    from axis.framework.experiment_output import (
        ExperimentOutputForm,
        PointExperimentOutput,
        SweepExperimentOutput,
        load_experiment_output,
    )

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

    # Load experiment output for form-specific info
    exp_output = None
    try:
        exp_output = load_experiment_output(repo, experiment_id)
        info["output_form"] = exp_output.output_form.value
        if isinstance(exp_output, PointExperimentOutput):
            info["primary_run_id"] = exp_output.primary_run_id
        elif isinstance(exp_output, SweepExperimentOutput):
            info["baseline_run_id"] = exp_output.baseline_run_id
            info["parameter_path"] = exp_output.parameter_path
            info["parameter_values"] = list(
                exp_output.parameter_values) if exp_output.parameter_values else None
    except Exception:
        pass

    if output == "json":
        print(json.dumps(info, indent=2))
    else:
        print(f"Experiment: {experiment_id}")
        print(f"  Status: {info.get('status', 'unknown')}")
        if info.get("experiment_type"):
            print(f"  Type: {info['experiment_type']}")
        if info.get("output_form"):
            print(f"  Output form: {info['output_form']}")
        if info.get("system_type"):
            print(f"  System: {info['system_type']}")
        if info.get("created_at"):
            print(f"  Created: {info['created_at']}")
        print(f"  Runs: {runs}")
        if info.get("primary_run_id"):
            print(f"  Primary run: {info['primary_run_id']}")
        if info.get("baseline_run_id"):
            print(f"  Baseline run: {info['baseline_run_id']}")
        if info.get("parameter_path"):
            print(f"  Parameter path: {info['parameter_path']}")
        if info.get("parameter_values"):
            print(f"  Parameter values: {info['parameter_values']}")
        if info.get("summary"):
            s = info["summary"]
            print(f"  Summary: {s['num_runs']} runs")
            for entry in s.get("run_entries", []):
                print(
                    f"    {entry['run_id']}  "
                    f"{entry.get('variation_description', '')}"
                )
