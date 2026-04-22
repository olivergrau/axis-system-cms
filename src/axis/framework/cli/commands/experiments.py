"""CLI commands for experiment management."""

from __future__ import annotations

import json
from pathlib import Path

from axis.framework.cli.output import fail, stdout_output


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
        out = stdout_output()
        if not entries:
            out.info("No experiments found.")
            return
        out.title("Experiments")
        for e in entries:
            parts = [
                e["experiment_id"],
                f"[{e['status']}]",
                f"runs={e['num_runs']}",
                f"completed={e['num_completed_runs']}",
            ]
            if e.get("output_form"):
                parts.append(f"form={e['output_form']}")
            if e.get("system_type"):
                parts.append(f"system={e['system_type']}")
            if e.get("created_at"):
                parts.append(f"created={e['created_at']}")
            out.list_row(*parts)


def cmd_experiments_run(
    repo, config_path: str, output: str,
    catalogs: dict | None = None,
) -> None:
    from axis.framework.experiment import ExperimentExecutor

    path = Path(config_path)
    if not path.exists():
        fail(
            f"Config file not found: {config_path}",
            hint="Provide a valid experiment config path.",
        )
    try:
        config = _load_config_file(path)
    except Exception as exc:
        fail(f"Invalid config file: {exc}")

    try:
        result = ExperimentExecutor(
            repository=repo,
            system_catalog=catalogs.get("systems") if catalogs else None,
            world_catalog=catalogs.get("worlds") if catalogs else None,
        ).execute(config)
    except Exception as exc:
        fail(str(exc))

    if output == "json":
        print(json.dumps({
            "experiment_id": result.experiment_id,
            "status": "completed",
            "num_runs": result.summary.num_runs,
        }, indent=2))
    else:
        out = stdout_output()
        out.success("experiment run")
        out.kv("Experiment ID", result.experiment_id)
        out.kv("Runs", result.summary.num_runs)


def cmd_experiments_resume(
    repo, experiment_id: str, output: str,
    catalogs: dict | None = None,
) -> None:
    from axis.framework.experiment import ExperimentExecutor

    if not repo.experiment_dir(experiment_id).exists():
        fail(
            f"Experiment not found: {experiment_id}",
            hint="Run `axis experiments list` to inspect available experiments.",
        )
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
        out = stdout_output()
        out.success("experiment resume")
        out.kv("Experiment ID", experiment_id)
        out.kv("Runs", result.summary.num_runs)


def cmd_experiments_show(repo, experiment_id: str, output: str) -> None:
    if not repo.experiment_dir(experiment_id).exists():
        fail(
            f"Experiment not found: {experiment_id}",
            hint="Run `axis experiments list` to inspect available experiments.",
        )

    from axis.framework.experiment_output import (
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
        out = stdout_output()
        out.title(f"Experiment {experiment_id}")
        out.kv("Status", info.get("status", "unknown"))
        if info.get("experiment_type"):
            out.kv("Type", info["experiment_type"])
        if info.get("output_form"):
            out.kv("Output form", info["output_form"])
        if info.get("system_type"):
            out.kv("System", info["system_type"])
        if info.get("created_at"):
            out.kv("Created", info["created_at"])
        out.kv("Runs", runs)
        if info.get("primary_run_id"):
            out.kv("Primary run", info["primary_run_id"])
        if info.get("baseline_run_id"):
            out.kv("Baseline run", info["baseline_run_id"])
        if info.get("parameter_path"):
            out.kv("Parameter path", info["parameter_path"])
        if info.get("parameter_values"):
            out.kv("Parameter values", info["parameter_values"])
        if info.get("summary"):
            s = info["summary"]
            out.section("Summary")
            out.kv("Runs", s["num_runs"])
            for entry in s.get("run_entries", []):
                out.list_row(
                    entry["run_id"],
                    entry.get("variation_description", ""),
                    indent=4,
                )
