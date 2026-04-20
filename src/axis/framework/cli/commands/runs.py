"""CLI commands for run inspection."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def cmd_runs_list(repo, experiment_id: str, output: str) -> None:
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


def cmd_runs_show(repo, experiment_id: str, run_id: str, output: str) -> None:
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
        if meta.variation_index is not None:
            info["variation_index"] = meta.variation_index
        if meta.variation_value is not None:
            info["variation_value"] = meta.variation_value
        if meta.is_baseline is not None:
            info["is_baseline"] = meta.is_baseline
    except Exception:
        pass

    # Enclosing output form
    try:
        from axis.framework.experiment_output import load_experiment_output
        exp_output = load_experiment_output(repo, experiment_id)
        info["output_form"] = exp_output.output_form.value
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
        if info.get("output_form"):
            print(f"  Output form: {info['output_form']}")
        if info.get("variation_description"):
            print(f"  Variation: {info['variation_description']}")
        if info.get("is_baseline") is not None:
            print(f"  Is baseline: {info['is_baseline']}")
        if info.get("variation_index") is not None:
            print(f"  Variation index: {info['variation_index']}")
        if info.get("variation_value") is not None:
            print(f"  Variation value: {info['variation_value']}")
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
