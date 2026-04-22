"""CLI commands for trace and run comparison."""

from __future__ import annotations

import argparse
import json

from axis.framework.cli.output import fail, stdout_output


def cmd_compare(args: argparse.Namespace, repo, output: str, catalogs: dict | None = None) -> None:
    """Run paired trace comparison between two episodes or full runs."""
    ref_ep = args.reference_episode
    cand_ep = args.candidate_episode

    # Validate: both or neither episode flags must be provided.
    if (ref_ep is None) != (cand_ep is None):
        fail(
            "--reference-episode and --candidate-episode must both be "
            "provided (single-episode mode) or both omitted (run-level mode)."
        )

    if ref_ep is not None:
        _cmd_compare_episode(args, repo, output, catalogs=catalogs)
    else:
        _cmd_compare_runs(args, repo, output, catalogs=catalogs)


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


def _cmd_compare_runs(args: argparse.Namespace, repo, output: str, catalogs: dict | None = None) -> None:
    """Full-run comparison with statistical summary."""
    from axis.framework.comparison import compare_runs

    result = compare_runs(
        repo,
        args.reference_experiment, args.reference_run,
        args.candidate_experiment, args.candidate_run,
        extension_catalog=catalogs.get("comparison_extensions") if catalogs else None,
    )

    if output == "json":
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    else:
        print_run_comparison_text(result)


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


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
    for r in result.episode_results:
        ep = r.identity.reference_episode_index
        if r.result_mode.value != "comparison_succeeded":
            out.list_row(
                f"Episode {ep}",
                "[validation_failed]",
                ", ".join(r.validation.errors),
            )
            continue
        m = r.metrics
        o = r.outcome
        assert m is not None and o is not None
        out.list_row(
            f"Episode {ep}",
            f"mismatch={m.action_divergence.action_mismatch_rate:.1%}",
            f"pos_div={m.position_divergence.mean_trajectory_distance:.2f}",
            f"steps={o.reference_total_steps}/{o.candidate_total_steps}",
            f"survivor={o.longer_survivor}",
        )

    out.section("Statistical Summary")
    _print_metric("Action mismatch rate", s.action_mismatch_rate)
    out.hint("How often the two agents chose different actions at the same timestep.")
    _print_metric("Mean trajectory distance", s.mean_trajectory_distance)
    out.hint("Average Manhattan distance between the two agents per episode.")
    _print_metric("Mean vitality difference", s.mean_vitality_difference)
    out.hint("Average absolute difference in vitality between the two agents.")
    _print_metric("Final vitality delta", s.final_vitality_delta, signed=True)
    out.hint("Candidate final vitality minus reference final vitality.")
    _print_metric("Total steps delta", s.total_steps_delta, signed=True)
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


def _print_metric(label: str, stats, *, signed: bool = False) -> None:
    out = stdout_output()
    fmt = "+.4f" if signed else ".4f"
    out.kv(
        label,
        f"mean={stats.mean:{fmt}}, std={stats.std:.4f}, "
        f"min={stats.min:{fmt}}, max={stats.max:{fmt}} (n={stats.n})",
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
