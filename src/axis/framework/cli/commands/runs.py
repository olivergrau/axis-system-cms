"""CLI commands for run inspection."""

from __future__ import annotations

import json
from typing import Any

from axis.framework.cli.output import fail, stdout_output


def _fmt_metric_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "-"
    return str(value)


def _print_rich_metric_table(
    title: str,
    rows: list[tuple[str, Any]],
    *,
    caption: str | None = None,
) -> None:
    from rich.console import Console
    from rich.table import Table

    out = stdout_output()
    console = Console(file=out.stream, force_terminal=False, color_system=None)
    table = Table(title=title)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    for metric, value in rows:
        table.add_row(metric, _fmt_metric_value(value))
    if caption:
        table.caption = caption
    console.print(table)


def _system_metric_sort_key(key: str) -> tuple[int, str]:
    preferred_order = {
        "arbitration": 0,
        "prediction": 1,
        "modulation": 2,
        "traces": 3,
        "curiosity": 4,
        "world_model": 5,
        "behavior": 6,
        "prediction_impact": 7,
        "comparison": 8,
    }
    suffix = key
    if "_" in key:
        suffix = key.split("system_", 1)[-1]
        if "_" in suffix:
            suffix = suffix.split("_", 1)[-1]
    return (preferred_order.get(suffix, 999), key)


def _render_behavior_metrics_text(behavior: dict) -> None:
    """Render one behavioral metrics payload in text form."""
    out = stdout_output()
    metrics = behavior["standard_metrics"]
    out.section("Behavioral Metrics")
    _print_rich_metric_table(
        "Standard Metrics",
        [
            ("resource_gain_per_step", metrics["resource_gain_per_step"]["mean"]),
            ("net_energy_efficiency", metrics["net_energy_efficiency"]["mean"]),
            ("successful_consume_rate", metrics["successful_consume_rate"]["mean"]),
            ("failed_movement_rate", metrics["failed_movement_rate"]["mean"]),
            ("action_entropy", metrics["action_entropy"]["mean"]),
            ("policy_sharpness", metrics["policy_sharpness"]["mean"]),
            ("unique_cells_visited", metrics["unique_cells_visited"]["mean"]),
            ("coverage_efficiency", metrics["coverage_efficiency"]["mean"]),
            ("revisit_rate", metrics["revisit_rate"]["mean"]),
        ],
        caption="Mean values across the run.",
    )
    if behavior.get("system_specific_metrics"):
        out.section("System Metrics")
        items = sorted(
            behavior["system_specific_metrics"].items(),
            key=lambda item: _system_metric_sort_key(item[0]),
        )
        for key, values in items:
            if not isinstance(values, dict):
                _print_rich_metric_table(key, [(key, values)])
                continue
            _print_rich_metric_table(
                key,
                [(metric_key, metric_value) for metric_key, metric_value in values.items()],
            )


def cmd_runs_list(repo, experiment_id: str, output: str) -> None:
    from axis.framework.persistence import RunStatus

    if not repo.experiment_dir(experiment_id).exists():
        fail(
            f"Experiment not found: {experiment_id}",
            hint="Run `axis experiments list` to inspect available experiments.",
        )

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
        out = stdout_output()
        if not entries:
            out.info("No runs found.")
            return
        out.title(f"Runs For {experiment_id}")
        for e in entries:
            parts = [
                e["run_id"],
                f"[{e['status']}]",
            ]
            if e.get("variation_description"):
                parts.append(e["variation_description"])
            if e.get("has_summary"):
                parts.append("summary=yes")
            out.list_row(*parts)


def cmd_runs_show(repo, experiment_id: str, run_id: str, output: str) -> None:
    if not repo.run_dir(experiment_id, run_id).exists():
        fail(
            f"Run not found: {run_id} in experiment {experiment_id}",
            hint="Run `axis runs list --experiment <experiment-id>` to inspect available runs.",
        )

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
        if meta.trace_mode is not None:
            info["trace_mode"] = meta.trace_mode
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

    try:
        from axis.framework.metrics import load_or_compute_run_behavior_metrics
        behavior_metrics = load_or_compute_run_behavior_metrics(
            repo, experiment_id, run_id,
        )
        info["behavior_metrics"] = behavior_metrics.model_dump(mode="json")
    except Exception:
        info["behavior_metrics"] = None

    episodes = repo.list_episode_files(experiment_id, run_id)
    info["num_episodes"] = len(episodes)

    if output == "json":
        print(json.dumps(info, indent=2))
    else:
        out = stdout_output()
        out.title(f"Run {run_id}")
        out.kv("Experiment", experiment_id)
        out.kv("Status", info.get("status", "unknown"))
        if info.get("output_form"):
            out.kv("Output form", info["output_form"])
        if info.get("variation_description"):
            out.kv("Variation", info["variation_description"])
        if info.get("is_baseline") is not None:
            out.kv("Is baseline", info["is_baseline"])
        if info.get("variation_index") is not None:
            out.kv("Variation index", info["variation_index"])
        if info.get("variation_value") is not None:
            out.kv("Variation value", info["variation_value"])
        if info.get("created_at"):
            out.kv("Created", info["created_at"])
        if info.get("trace_mode"):
            out.kv("Trace mode", info["trace_mode"])
        if info.get("base_seed") is not None:
            out.kv("Base seed", info["base_seed"])
        out.kv("Episodes", info["num_episodes"])
        if info.get("summary"):
            s = info["summary"]
            out.section("Summary")
            out.list_row(
                f"mean_steps={s['mean_steps']:.1f}",
                f"death_rate={s['death_rate']:.2f}",
                f"mean_final_vitality={s['mean_final_vitality']:.3f}",
            )
        if info.get("behavior_metrics"):
            _render_behavior_metrics_text(info["behavior_metrics"])


def cmd_runs_metrics(repo, experiment_id: str, run_id: str, output: str) -> None:
    """Show or compute run-level behavioral metrics."""
    if not repo.run_dir(experiment_id, run_id).exists():
        fail(
            f"Run not found: {run_id} in experiment {experiment_id}",
            hint="Run `axis runs list --experiment <experiment-id>` to inspect available runs.",
        )

    from axis.framework.metrics import load_or_compute_run_behavior_metrics

    metrics = load_or_compute_run_behavior_metrics(repo, experiment_id, run_id)
    payload = metrics.model_dump(mode="json")

    if output == "json":
        print(json.dumps(payload, indent=2))
    else:
        out = stdout_output()
        out.title(f"Behavioral Metrics For {run_id}")
        out.kv("Experiment", experiment_id)
        out.kv("System", payload["system_type"])
        out.kv("Trace mode", payload["trace_mode"])
        out.kv("Episodes", payload["num_episodes"])
        _render_behavior_metrics_text(payload)
