"""CLI commands for trace and run comparison."""

from __future__ import annotations

import argparse
import json
import sys


def cmd_compare(args: argparse.Namespace, repo, output: str, catalogs: dict | None = None) -> None:
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
        # Collect distinct validation errors across all failed episodes.
        all_errors: list[str] = []
        for r in result.episode_results:
            if r.validation and r.validation.errors:
                for e in r.validation.errors:
                    if e not in all_errors:
                        all_errors.append(e)
        if all_errors:
            print(
                f"  No valid episode pairs to summarise — all failed "
                f"validation: {', '.join(all_errors)}.")
            print(
                "  This typically means the world configuration or start "
                "conditions differ between the two runs.")
        else:
            print("  No valid episode pairs to summarise.")
        return

    print("  --- Per-episode results ---")
    for r in result.episode_results:
        ep = r.identity.reference_episode_index
        if r.result_mode.value != "comparison_succeeded":
            print(
                f"  Episode {ep}: VALIDATION FAILED ({', '.join(r.validation.errors)})")
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
