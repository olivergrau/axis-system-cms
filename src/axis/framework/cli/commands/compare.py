"""CLI commands for trace and run comparison."""

from __future__ import annotations

import argparse
import json
import statistics
from collections.abc import Sequence
from typing import Any

from axis.framework.cli.output import fail, stdout_output


def cmd_compare(args: argparse.Namespace, repo, output: str, catalogs: dict | None = None) -> None:
    """Run paired trace comparison between two episodes or full runs."""
    from axis.framework.progress import create_progress_reporter

    ref_ep = args.reference_episode
    cand_ep = args.candidate_episode

    # Validate: both or neither episode flags must be provided.
    if (ref_ep is None) != (cand_ep is None):
        fail(
            "--reference-episode and --candidate-episode must both be "
            "provided (single-episode mode) or both omitted (run-level mode)."
        )

    with create_progress_reporter(output != "json") as progress:
        if ref_ep is not None:
            _cmd_compare_episode(args, repo, output, catalogs=catalogs)
        else:
            _cmd_compare_runs(
                args, repo, output, catalogs=catalogs, progress=progress,
            )


def _cmd_compare_episode(args: argparse.Namespace, repo, output: str, catalogs: dict | None = None) -> None:
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
        extension_catalog=catalogs.get("comparison_extensions") if catalogs else None,
    )

    if output == "json":
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    else:
        _print_comparison_text(result)


def _cmd_compare_runs(
    args: argparse.Namespace,
    repo,
    output: str,
    catalogs: dict | None = None,
    *,
    progress: object | None = None,
) -> None:
    """Full-run comparison with statistical summary."""
    from axis.framework.comparison import compare_runs

    result = compare_runs(
        repo,
        args.reference_experiment, args.reference_run,
        args.candidate_experiment, args.candidate_run,
        extension_catalog=catalogs.get("comparison_extensions") if catalogs else None,
        progress=progress,
    )

    if output == "json":
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    else:
        print_run_comparison_text(result)


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def _fmt_compare_value(value: Any, *, signed: bool = False) -> str:
    if isinstance(value, float):
        return f"{value:+.4f}" if signed else f"{value:.4f}"
    if value is None:
        return "-"
    return str(value)


def _print_rich_table(
    title: str,
    columns: list[tuple[str, dict[str, Any]]],
    rows: list[tuple[Any, ...]],
    *,
    caption: str | None = None,
) -> None:
    from rich.console import Console
    from rich.table import Table

    out = stdout_output()
    console = Console(file=out.stream, force_terminal=False, color_system=None)
    table = Table(title=title)
    for label, kwargs in columns:
        table.add_column(label, **kwargs)
    for row in rows:
        table.add_row(*(str(cell) for cell in row))
    if caption:
        table.caption = caption
    console.print(table)


def print_run_comparison_text(result) -> None:
    """Pretty-print a RunComparisonResult in text mode."""
    out = stdout_output()
    s = result.summary
    out.title("Run Comparison")
    out.kv(
        "Reference",
        f"{result.reference_system_type}  "
        f"experiment={result.reference_experiment_id}  run={result.reference_run_id}",
    )
    out.kv(
        "Candidate",
        f"{result.candidate_system_type}  "
        f"experiment={result.candidate_experiment_id}  run={result.candidate_run_id}",
    )
    out.kv(
        "Episodes",
        f"{s.num_episodes_compared} compared, "
        f"{s.num_valid_pairs} valid, {s.num_invalid_pairs} invalid",
    )

    if s.num_valid_pairs == 0:
        # Collect distinct validation errors across all failed episodes.
        all_errors: list[str] = []
        for r in result.episode_results:
            if r.validation and r.validation.errors:
                for e in r.validation.errors:
                    if e not in all_errors:
                        all_errors.append(e)
        if all_errors:
            out.section("Validation")
            out.warning(
                "No valid episode pairs to summarize: "
                f"{', '.join(all_errors)}"
            )
            out.hint(
                "This usually means the world configuration or start conditions "
                "differ between the two runs."
            )
        else:
            out.section("Validation")
            out.warning("No valid episode pairs to summarize.")
        return

    out.section("Per-episode Results")
    per_episode_rows: list[tuple[Any, ...]] = []
    for r in result.episode_results:
        ep = r.identity.reference_episode_index
        if r.result_mode.value != "comparison_succeeded":
            per_episode_rows.append(
                (
                    ep,
                    "validation_failed",
                    "-",
                    "-",
                    "-",
                    ", ".join(r.validation.errors),
                )
            )
            continue
        m = r.metrics
        o = r.outcome
        assert m is not None and o is not None
        per_episode_rows.append(
            (
                ep,
                f"{m.action_divergence.action_mismatch_rate:.1%}",
                f"{m.position_divergence.mean_trajectory_distance:.2f}",
                f"{o.reference_total_steps}/{o.candidate_total_steps}",
                o.longer_survivor,
                "",
            )
        )
    _print_rich_table(
        "Per-episode Results",
        [
            ("Episode", {"style": "bold"}),
            ("Mismatch", {"justify": "right"}),
            ("Pos div", {"justify": "right"}),
            ("Steps r/c", {"justify": "right"}),
            ("Survivor", {}),
            ("Notes", {}),
        ],
        per_episode_rows,
        caption="Aligned run-level comparison across matched episode pairs.",
    )

    out.section("Statistical Summary")
    summary_rows = [
        _metric_summary_row("Action mismatch rate", s.action_mismatch_rate),
        _metric_summary_row("Mean trajectory distance", s.mean_trajectory_distance),
        _metric_summary_row("Mean vitality difference", s.mean_vitality_difference),
        _metric_summary_row("Final vitality delta", s.final_vitality_delta, signed=True),
        _metric_summary_row("Total steps delta", s.total_steps_delta, signed=True),
    ]
    _print_rich_table(
        "Statistical Summary",
        [
            ("Metric", {"style": "bold"}),
            ("Mean", {"justify": "right"}),
            ("Std", {"justify": "right"}),
            ("Min", {"justify": "right"}),
            ("Max", {"justify": "right"}),
            ("N", {"justify": "right"}),
        ],
        summary_rows,
        caption="Descriptive statistics across valid episode pairs.",
    )
    out.hint("How often the two agents chose different actions at the same timestep.")
    out.hint("Average Manhattan distance between the two agents per episode.")
    out.hint("Average absolute difference in vitality between the two agents.")
    out.hint("Candidate final vitality minus reference final vitality.")
    out.hint("Candidate episode length minus reference episode length.")
    out.kv(
        "Survival rates",
        f"reference={s.reference_survival_rate:.0%}  "
        f"candidate={s.candidate_survival_rate:.0%}",
    )
    out.kv(
        "Longer survivor",
        f"candidate={s.candidate_longer_count}  "
        f"reference={s.reference_longer_count}  equal={s.equal_count}",
    )
    _print_system_specific_run_summary(result)


def _print_metric(label: str, stats, *, signed: bool = False) -> None:
    out = stdout_output()
    fmt = "+.4f" if signed else ".4f"
    out.kv(
        label,
        f"mean={stats.mean:{fmt}}, std={stats.std:.4f}, "
        f"min={stats.min:{fmt}}, max={stats.max:{fmt}} (n={stats.n})",
    )


def _metric_summary_row(label: str, stats, *, signed: bool = False) -> tuple[str, str, str, str, str, str]:
    return (
        label,
        _fmt_compare_value(stats.mean, signed=signed),
        _fmt_compare_value(stats.std),
        _fmt_compare_value(stats.min, signed=signed),
        _fmt_compare_value(stats.max, signed=signed),
        str(stats.n),
    )


def _summary_stats(values: Sequence[float]):
    class _Stats:
        def __init__(self, mean: float, std: float, min_value: float, max_value: float, n: int):
            self.mean = mean
            self.std = std
            self.min = min_value
            self.max = max_value
            self.n = n

    n = len(values)
    mean = statistics.mean(values)
    std = statistics.stdev(values) if n >= 2 else 0.0
    return _Stats(mean, std, min(values), max(values), n)


def _print_system_specific_run_summary(result) -> None:
    out = stdout_output()
    valid = [
        r.system_specific_analysis
        for r in result.episode_results
        if r.result_mode.value == "comparison_succeeded" and r.system_specific_analysis
    ]
    if not valid:
        return

    extension_keys = set.intersection(
        *(set(analysis.keys()) for analysis in valid if isinstance(analysis, dict))
    )
    if not extension_keys:
        return

    out.section("System-specific Summary")
    for extension_key in sorted(extension_keys):
        payloads = []
        for analysis in valid:
            payload = analysis.get(extension_key)
            if isinstance(payload, dict):
                payloads.append(payload)
        if not payloads:
            continue
        summary_rows: list[tuple[Any, ...]] = []
        common_keys = set.intersection(*(set(payload.keys()) for payload in payloads))
        for key in sorted(common_keys):
            values = [payload[key] for payload in payloads]
            if all(isinstance(value, str) for value in values):
                summary_rows.append((key, values[0] if len(set(values)) == 1 else "varies", "-", "-", "-", "-"))
                continue
            if all(
                isinstance(value, (int, float)) and not isinstance(value, bool)
                for value in values
            ):
                stats = _summary_stats([float(value) for value in values])
                summary_rows.append(
                    (
                        key,
                        _fmt_compare_value(stats.mean),
                        _fmt_compare_value(stats.std),
                        _fmt_compare_value(stats.min),
                        _fmt_compare_value(stats.max),
                        str(stats.n),
                    )
                )
        if summary_rows:
            _print_rich_table(
                extension_key,
                [
                    ("Metric", {"style": "bold"}),
                    ("Mean/Value", {"justify": "right"}),
                    ("Std", {"justify": "right"}),
                    ("Min", {"justify": "right"}),
                    ("Max", {"justify": "right"}),
                    ("N", {"justify": "right"}),
                ],
                summary_rows,
            )


def _print_comparison_text(result) -> None:
    """Pretty-print a PairedTraceComparisonResult in text mode."""
    out = stdout_output()
    out.title("Comparison")
    out.kv("Result", result.result_mode.value)
    i = result.identity
    ref = i.reference_system_type
    if i.reference_run_id:
        ref = f"{ref}  run={i.reference_run_id}"
    cand = i.candidate_system_type
    if i.candidate_run_id:
        cand = f"{cand}  run={i.candidate_run_id}"
    out.kv("Reference", ref)
    out.kv("Candidate", cand)

    v = result.validation
    if not v.is_valid_pair:
        out.section("Validation")
        out.error(", ".join(v.errors))
        return

    if result.alignment:
        a = result.alignment
        out.section("Alignment")
        out.kv(
            "Aligned steps",
            f"{a.aligned_steps}  "
            f"(ref={a.reference_total_steps}, cand={a.candidate_total_steps})",
        )

    if result.metrics:
        m = result.metrics
        out.section("Metrics")
        ad = m.action_divergence
        out.kv(
            "Action divergence",
            f"first={ad.first_action_divergence_step}  "
            f"mismatch={ad.action_mismatch_count}  "
            f"rate={ad.action_mismatch_rate:.1%}",
        )
        pd = m.position_divergence
        out.kv(
            "Position divergence",
            f"mean={pd.mean_trajectory_distance:.2f}  max={pd.max_trajectory_distance}",
        )
        vd = m.vitality_divergence
        out.kv(
            "Vitality divergence",
            f"mean={vd.mean_absolute_difference:.4f}  max={vd.max_absolute_difference:.4f}",
        )

    if result.outcome:
        o = result.outcome
        out.section("Outcome")
        out.kv(
            "Reference",
            f"{o.reference_total_steps} steps  "
            f"({o.reference_termination_reason})",
        )
        out.kv(
            "Candidate",
            f"{o.candidate_total_steps} steps  "
            f"({o.candidate_termination_reason})",
        )
        out.kv("Vitality delta", f"{o.final_vitality_delta:+.4f}")
        out.kv("Longer survivor", o.longer_survivor)

    if result.system_specific_analysis:
        out.section("Extensions")
        for key, data in result.system_specific_analysis.items():
            out.kv("Extension", key)
            if isinstance(data, dict):
                for k, val in data.items():
                    out.kv(k, val, indent=4)
