"""Comprehensive tests for the paired trace comparison package (WP-11)."""

from __future__ import annotations

import pytest

from axis.framework.comparison.actions import compute_action_usage
from axis.framework.comparison.alignment import compute_alignment, iter_aligned_steps
from axis.framework.comparison.compare import compare_episode_traces
from axis.framework.comparison.extensions import (
    _EXTENSION_REGISTRY,
    build_system_specific_analysis,
)

# Ensure system_c comparison extension is registered for tests.
import axis.systems.system_c.comparison  # noqa: F401
import axis.systems.system_cw.comparison  # noqa: F401
from axis.framework.comparison.metrics import (
    compute_action_divergence,
    compute_position_divergence,
    compute_vitality_divergence,
)
from axis.framework.comparison.outcome import compute_outcome
from axis.framework.comparison.types import (
    AmbiguityState,
    PairedTraceComparisonResult,
    PairingMode,
    ResultMode,
)
from axis.framework.comparison.validation import validate_trace_pair
from axis.framework.run import RunConfig
from axis.framework.config import ExecutionConfig, FrameworkConfig, GeneralConfig
from axis.framework.persistence import RunMetadata
from axis.sdk.world_types import BaseWorldConfig

from tests.framework.comparison.fixtures import (
    make_divergent_pair,
    make_episode,
    make_identical_pair,
    make_step,
    make_system_c_step,
    make_system_cw_step,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_config(base_seed: int | None = 42, system_type: str = "system_a") -> RunConfig:
    return RunConfig(
        system_type=system_type,
        system_config={},
        framework_config=FrameworkConfig(
            general=GeneralConfig(seed=1),
            execution=ExecutionConfig(max_steps=100),
            world=BaseWorldConfig(),
        ),
        num_episodes=1,
        base_seed=base_seed,
    )


def _run_metadata(run_id: str = "run-001", base_seed: int | None = 42) -> RunMetadata:
    return RunMetadata(
        run_id=run_id,
        experiment_id="exp-001",
        created_at="2026-01-01",
        base_seed=base_seed,
    )


# ===================================================================
# WP-01: Result model tests
# ===================================================================

class TestResultModels:
    def test_models_are_frozen(self):
        ref, cand = make_identical_pair(2)
        result = compare_episode_traces(ref, cand)
        with pytest.raises(Exception):
            # type: ignore[misc]
            result.result_mode = ResultMode.COMPARISON_FAILED_VALIDATION

    def test_result_json_serializable(self):
        ref, cand = make_identical_pair(3)
        result = compare_episode_traces(ref, cand)
        data = result.model_dump(mode="json")
        assert isinstance(data, dict)
        assert data["result_mode"] == "comparison_succeeded"

    def test_ambiguity_state_enum(self):
        assert AmbiguityState.NOT_APPLICABLE == "not_applicable"
        assert AmbiguityState.AMBIGUOUS_DUE_TO_TIE == "ambiguous_due_to_tie"
        assert AmbiguityState.MISSING_REQUIRED_SIGNAL == "missing_required_signal"


# ===================================================================
# WP-02: Validation tests
# ===================================================================

class TestValidation:
    def test_valid_pair(self):
        ref, cand = make_identical_pair()
        val, _, _ = validate_trace_pair(ref, cand)
        assert val.is_valid_pair
        assert len(val.errors) == 0
        assert val.world_type_match
        assert val.world_config_match
        assert val.start_position_match

    def test_world_type_mismatch(self):
        ref, cand = make_identical_pair()
        cand = make_episode(
            list(cand.steps), system_type="system_c", world_type="hex_grid")
        val, _, _ = validate_trace_pair(ref, cand)
        assert not val.is_valid_pair
        assert "world_type_mismatch" in val.errors

    def test_world_config_mismatch(self):
        ref = make_episode([make_step(0)], world_config={"size": 5})
        cand = make_episode(
            [make_step(0)], system_type="system_c", world_config={"size": 10})
        val, _, _ = validate_trace_pair(ref, cand)
        assert val.is_valid_pair
        assert "world_config_mismatch" not in val.errors
        assert not val.world_config_match

    def test_start_position_mismatch(self):
        ref = make_episode([make_step(0, pos_before=(0, 0), pos_after=(0, 1))])
        cand = make_episode([
            make_step(0, pos_before=(3, 3), pos_after=(3, 4))],
            system_type="system_c",
        )
        val, _, _ = validate_trace_pair(ref, cand)
        assert not val.is_valid_pair
        assert "start_position_mismatch" in val.errors

    def test_seed_match_derived(self):
        ref, cand = make_identical_pair()
        rc_ref = _run_config(base_seed=100)
        rc_cand = _run_config(base_seed=100, system_type="system_c")
        val, mode, seed = validate_trace_pair(
            ref, cand,
            reference_run_config=rc_ref, candidate_run_config=rc_cand,
            reference_episode_index=0, candidate_episode_index=0,
        )
        assert val.is_valid_pair
        assert mode == PairingMode.DERIVED_SEED
        assert seed == 100

    def test_seed_mismatch(self):
        ref, cand = make_identical_pair()
        rc_ref = _run_config(base_seed=100)
        rc_cand = _run_config(base_seed=200, system_type="system_c")
        val, _, _ = validate_trace_pair(
            ref, cand,
            reference_run_config=rc_ref, candidate_run_config=rc_cand,
            reference_episode_index=0, candidate_episode_index=0,
        )
        assert not val.is_valid_pair
        assert "episode_seed_mismatch" in val.errors

    def test_shared_labels(self):
        ref = make_episode(
            [make_step(0, action="move_north"), make_step(1, action="consume")])
        cand = make_episode([
            make_step(0, action="consume"), make_step(1, action="stay")],
            system_type="system_c",
        )
        val, _, _ = validate_trace_pair(ref, cand)
        assert "consume" in val.shared_action_labels

    def test_no_shared_labels_fails(self):
        ref = make_episode([make_step(0, action="move_north")])
        cand = make_episode(
            [make_step(0, action="fly_south")], system_type="system_c")
        val, _, _ = validate_trace_pair(ref, cand)
        assert not val.is_valid_pair
        assert "action_space_no_shared_labels" in val.errors


# ===================================================================
# WP-03: Alignment tests
# ===================================================================

class TestAlignment:
    def test_equal_length(self):
        ref, cand = make_identical_pair(5)
        a = compute_alignment(ref, cand)
        assert a.aligned_steps == 5
        assert a.reference_extra_steps == 0
        assert a.candidate_extra_steps == 0

    def test_unequal_length(self):
        ref = make_episode([make_step(i) for i in range(5)])
        cand = make_episode([make_step(i)
                            for i in range(3)], system_type="system_c")
        a = compute_alignment(ref, cand)
        assert a.aligned_steps == 3
        assert a.reference_extra_steps == 2
        assert a.candidate_extra_steps == 0

    def test_zero_length(self):
        ref = make_episode([make_step(0)])
        cand = make_episode([], system_type="system_c",
                            termination_reason="immediate")
        a = compute_alignment(ref, cand)
        assert a.aligned_steps == 0

    def test_iter_aligned(self):
        ref, cand = make_identical_pair(4)
        pairs = list(iter_aligned_steps(ref, cand))
        assert len(pairs) == 4
        assert pairs[0][0].timestep == 0


class TestCompareEpisodeTraceOptions:
    def test_compare_episode_traces_accepts_world_config_differences(self):
        ref = make_episode([make_step(0)], world_config={"size": 5})
        cand = make_episode(
            [make_step(0)],
            system_type="system_c",
            world_config={"size": 10},
        )
        result = compare_episode_traces(
            ref,
            cand,
        )
        assert result.result_mode == ResultMode.COMPARISON_SUCCEEDED
        assert not result.validation.world_config_match


# ===================================================================
# WP-04: Action usage tests
# ===================================================================

class TestActionUsage:
    def test_identical_usage(self):
        ref, cand = make_identical_pair(5)
        val, _, _ = validate_trace_pair(ref, cand)
        usage = compute_action_usage(ref, cand, val.shared_action_labels)
        assert usage.reference_most_used == "move_north"
        assert usage.candidate_most_used == "move_north"
        for entry in usage.shared_action_usage:
            assert entry.delta == 0

    def test_divergent_usage(self):
        ref, cand = make_divergent_pair(5, diverge_at=2)
        val, _, _ = validate_trace_pair(ref, cand)
        usage = compute_action_usage(ref, cand, val.shared_action_labels)
        assert usage.reference_most_used == "move_north"
        assert usage.candidate_most_used is not None

    def test_tie_handling(self):
        steps = [make_step(0, action="a"), make_step(1, action="b")]
        ref = make_episode(steps)
        cand = make_episode(steps, system_type="system_c")
        val, _, _ = validate_trace_pair(ref, cand)
        usage = compute_action_usage(ref, cand, val.shared_action_labels)
        assert usage.reference_most_used_ambiguity == AmbiguityState.AMBIGUOUS_DUE_TO_TIE

    def test_non_shared_actions(self):
        ref = make_episode(
            [make_step(0, action="a"), make_step(1, action="b")])
        cand = make_episode([
            make_step(0, action="b"), make_step(1, action="c")],
            system_type="system_c",
        )
        val, _, _ = validate_trace_pair(ref, cand)
        usage = compute_action_usage(ref, cand, val.shared_action_labels)
        assert "a" in usage.reference_only_actions
        assert "c" in usage.candidate_only_actions


# ===================================================================
# WP-05: Divergence metrics tests
# ===================================================================

class TestDivergenceMetrics:
    def test_no_action_divergence(self):
        ref, cand = make_identical_pair(5)
        d = compute_action_divergence(ref, cand)
        assert d.first_action_divergence_step is None
        assert d.action_mismatch_count == 0
        assert d.action_mismatch_rate == 0.0

    def test_action_divergence(self):
        ref, cand = make_divergent_pair(5, diverge_at=2)
        d = compute_action_divergence(ref, cand)
        assert d.first_action_divergence_step == 2
        assert d.action_mismatch_count == 3
        assert d.action_mismatch_rate == pytest.approx(0.6)

    def test_no_position_divergence(self):
        ref, cand = make_identical_pair(5)
        d = compute_position_divergence(ref, cand)
        assert d.max_trajectory_distance == 0

    def test_position_divergence(self):
        ref, cand = make_divergent_pair(5, diverge_at=2)
        d = compute_position_divergence(ref, cand)
        assert d.max_trajectory_distance > 0
        assert len(d.distance_series) == 5

    def test_vitality_divergence_identical(self):
        ref, cand = make_identical_pair(5)
        d = compute_vitality_divergence(ref, cand)
        assert d.max_absolute_difference == pytest.approx(0.0)

    def test_vitality_divergence_different(self):
        ref, cand = make_divergent_pair(5, diverge_at=2)
        d = compute_vitality_divergence(ref, cand)
        assert len(d.difference_series) == 5

    def test_empty_traces(self):
        ref = make_episode([], termination_reason="immediate")
        cand = make_episode([], system_type="system_c",
                            termination_reason="immediate")
        d = compute_action_divergence(ref, cand)
        assert d.action_mismatch_rate == 0.0
        pd = compute_position_divergence(ref, cand)
        assert pd.max_trajectory_distance == 0


# ===================================================================
# WP-06: Outcome comparison tests
# ===================================================================

class TestOutcomeComparison:
    def test_equal_outcome(self):
        ref, cand = make_identical_pair(5)
        o = compute_outcome(ref, cand)
        assert o.longer_survivor == "equal"
        assert o.total_steps_delta == 0

    def test_candidate_longer(self):
        ref = make_episode([make_step(i)
                           for i in range(3)], termination_reason="death")
        cand = make_episode(
            [make_step(i) for i in range(5)],
            system_type="system_c", termination_reason="max_steps",
        )
        o = compute_outcome(ref, cand)
        assert o.longer_survivor == "candidate"
        assert o.total_steps_delta == 2

    def test_reference_longer(self):
        ref = make_episode([make_step(i) for i in range(7)])
        cand = make_episode([make_step(i)
                            for i in range(3)], system_type="system_c")
        o = compute_outcome(ref, cand)
        assert o.longer_survivor == "reference"


# ===================================================================
# WP-07: Top-level compare tests
# ===================================================================

class TestCompareEpisodeTraces:
    def test_successful_comparison(self):
        ref, cand = make_identical_pair()
        result = compare_episode_traces(ref, cand)
        assert result.result_mode == ResultMode.COMPARISON_SUCCEEDED
        assert result.metrics is not None
        assert result.alignment is not None
        assert result.outcome is not None

    def test_failed_validation(self):
        ref = make_episode([make_step(0)], world_type="grid_2d")
        cand = make_episode(
            [make_step(0)], system_type="system_c", world_type="hex")
        result = compare_episode_traces(ref, cand)
        assert result.result_mode == ResultMode.COMPARISON_FAILED_VALIDATION
        assert result.metrics is None

    def test_identity_populated(self):
        ref, cand = make_identical_pair()
        meta_ref = _run_metadata("ref-run")
        meta_cand = _run_metadata("cand-run")
        result = compare_episode_traces(
            ref, cand,
            reference_run_metadata=meta_ref,
            candidate_run_metadata=meta_cand,
            reference_episode_index=0,
            candidate_episode_index=0,
        )
        assert result.identity.reference_run_id == "ref-run"
        assert result.identity.candidate_run_id == "cand-run"

    def test_full_roundtrip_json(self):
        ref, cand = make_divergent_pair()
        result = compare_episode_traces(ref, cand)
        data = result.model_dump(mode="json")
        restored = PairedTraceComparisonResult.model_validate(data)
        assert restored.result_mode == result.result_mode
        assert restored.metrics is not None


# ===================================================================
# WP-09: Extension dispatch tests
# ===================================================================

class TestExtensionDispatch:
    def test_system_c_registered(self):
        assert "system_c" in _EXTENSION_REGISTRY

    def test_no_extension_returns_none(self):
        ref, cand = make_identical_pair(3, system_type_cand="system_a")
        alignment = compute_alignment(ref, cand)
        result = build_system_specific_analysis(ref, cand, alignment)
        # system_a has no extension
        assert result is None

    def test_system_c_extension_called(self):
        ref = make_episode([make_step(0)], system_type="system_a")
        cand_step = make_system_c_step(0)
        cand = make_episode([cand_step], system_type="system_c")
        alignment = compute_alignment(ref, cand)
        result = build_system_specific_analysis(ref, cand, alignment)
        assert result is not None
        assert "system_c_prediction" in result

    def test_system_cw_extension_called(self):
        ref = make_episode([make_system_cw_step(0)], system_type="system_cw")
        cand = make_episode([make_system_cw_step(0)], system_type="system_cw")
        alignment = compute_alignment(ref, cand)
        result = build_system_specific_analysis(ref, cand, alignment)
        assert result is not None
        assert "system_cw_comparison" in result


# ===================================================================
# WP-10: System C extension tests
# ===================================================================

class TestSystemCExtension:
    def test_prediction_active_detection(self):
        raw = {"move_north": 1.0, "consume": 0.5}
        mod = {"move_north": 1.5, "consume": 0.3}
        ref = make_episode([make_step(0)], system_type="system_a")
        cand = make_episode(
            [make_system_c_step(0, raw_contributions=raw,
                                modulated_scores=mod)],
            system_type="system_c",
        )
        result = compare_episode_traces(ref, cand)
        ext = result.system_specific_analysis
        assert ext is not None
        sc = ext["system_c_prediction"]
        assert sc["prediction_active_step_count"] == 1
        assert sc["prediction_active_step_rate"] == 1.0

    def test_no_modulation_effect(self):
        raw = {"move_north": 1.0, "consume": 0.5}
        ref = make_episode([make_step(0)], system_type="system_a")
        cand = make_episode(
            [make_system_c_step(0, raw_contributions=raw,
                                modulated_scores=raw)],
            system_type="system_c",
        )
        result = compare_episode_traces(ref, cand)
        sc = result.system_specific_analysis["system_c_prediction"]
        assert sc["prediction_active_step_count"] == 0

    def test_top_action_changed(self):
        raw = {"move_north": 1.0, "consume": 0.9}
        mod = {"move_north": 0.8, "consume": 1.1}  # top flips
        ref = make_episode([make_step(0)], system_type="system_a")
        cand = make_episode(
            [make_system_c_step(0, raw_contributions=raw,
                                modulated_scores=mod)],
            system_type="system_c",
        )
        result = compare_episode_traces(ref, cand)
        sc = result.system_specific_analysis["system_c_prediction"]
        assert sc["top_action_changed_by_modulation_count"] == 1

    def test_missing_system_data_graceful(self):
        ref = make_episode([make_step(0)], system_type="system_a")
        cand = make_episode([make_step(0)], system_type="system_c")
        result = compare_episode_traces(ref, cand)
        sc = result.system_specific_analysis["system_c_prediction"]
        assert sc["prediction_active_step_count"] == 0
        assert sc["mean_modulation_delta"] == 0.0

    def test_modulation_delta_computed(self):
        raw = {"a": 1.0, "b": 2.0}
        mod = {"a": 1.5, "b": 2.5}  # delta = (0.5 + 0.5) / 2 = 0.5
        ref = make_episode([make_step(0)], system_type="system_a")
        cand = make_episode(
            [make_system_c_step(0, raw_contributions=raw,
                                modulated_scores=mod)],
            system_type="system_c",
        )
        result = compare_episode_traces(ref, cand)
        sc = result.system_specific_analysis["system_c_prediction"]
        assert sc["mean_modulation_delta"] == pytest.approx(0.5)


class TestSystemCWExtension:
    def test_cw_full_analysis(self):
        ref = make_episode(
            [make_system_cw_step(0, combined_scores=(0.1, 0.3, 0.2, 0.1, -0.1, -0.2))],
            system_type="system_cw",
        )
        cand = make_episode(
            [make_system_cw_step(0, combined_scores=(0.4, 0.3, 0.2, 0.1, -0.1, -0.2))],
            system_type="system_cw",
        )
        result = compare_episode_traces(ref, cand)
        ext = result.system_specific_analysis
        assert ext is not None
        data = ext["system_cw_comparison"]
        assert data["comparison_scope"] == "cw_full"
        assert data["behavioral_prediction_impact_rate_delta"] == pytest.approx(1.0)
        assert "mean_feature_prediction_error_delta" in data

    def test_aw_cw_intersection_only(self):
        ref = make_episode(
            [make_step(
                0,
                action="up",
                system_data={
                    "decision_data": {
                        "curiosity_drive": {
                            "activation": 0.2,
                            "composite_novelty": (0.1, 0.1, 0.1, 0.1),
                        },
                        "arbitration": {
                            "hunger_weight": 0.7,
                            "curiosity_weight": 0.3,
                        },
                    },
                    "trace_data": {"visit_count_at_current": 1.0},
                },
            )],
            system_type="system_aw",
        )
        cand = make_episode([make_system_cw_step(0)], system_type="system_cw")
        result = compare_episode_traces(ref, cand)
        ext = result.system_specific_analysis
        assert ext is not None
        data = ext["system_cw_comparison"]
        assert data["comparison_scope"] == "aw_cw_intersection"
        assert "mean_hunger_weight_delta" in data
        assert "mean_feature_prediction_error_delta" not in data

    def test_c_cw_prediction_intersection_only(self):
        ref = make_episode(
            [make_system_c_step(
                0,
                action="up",
                raw_contributions={"up": 0.1, "consume": 0.2},
                modulated_scores={"up": 0.4, "consume": 0.1},
            )],
            system_type="system_c",
        )
        cand = make_episode([make_system_cw_step(0)], system_type="system_cw")
        result = compare_episode_traces(ref, cand)
        ext = result.system_specific_analysis
        assert ext is not None
        data = ext["system_cw_comparison"]
        assert data["comparison_scope"] == "c_cw_prediction_intersection"
        assert "prediction_modulation_delta_shift" in data
        assert "mean_hunger_weight_delta" not in data


# ===================================================================
# Run-level comparison tests
# ===================================================================

class TestRunSummary:
    def test_summary_stats_math(self):
        from axis.framework.comparison.summary import _stats
        s = _stats([1.0, 2.0, 3.0, 4.0, 5.0])
        assert s.mean == pytest.approx(3.0)
        assert s.min == pytest.approx(1.0)
        assert s.max == pytest.approx(5.0)
        assert s.n == 5
        assert s.std > 0

    def test_summary_single_value(self):
        from axis.framework.comparison.summary import _stats
        s = _stats([42.0])
        assert s.mean == pytest.approx(42.0)
        assert s.std == 0.0
        assert s.n == 1

    def test_summary_empty(self):
        from axis.framework.comparison.summary import _stats
        s = _stats([])
        assert s.n == 0

    def test_compute_run_summary(self):
        from axis.framework.comparison.summary import compute_run_summary
        # 3 episode comparisons
        results = []
        for i in range(3):
            ref, cand = make_divergent_pair(
                n_steps=10, diverge_at=2 + i)
            r = compare_episode_traces(ref, cand)
            results.append(r)

        summary = compute_run_summary(results)
        assert summary.num_episodes_compared == 3
        assert summary.num_valid_pairs == 3
        assert summary.num_invalid_pairs == 0
        assert summary.action_mismatch_rate.n == 3
        assert summary.action_mismatch_rate.mean > 0

    def test_summary_with_invalid_pair(self):
        from axis.framework.comparison.summary import compute_run_summary
        # 2 valid + 1 invalid
        results = []
        for _ in range(2):
            ref, cand = make_identical_pair(3)
            results.append(compare_episode_traces(ref, cand))

        # Invalid: world type mismatch
        ref = make_episode([make_step(0)], world_type="grid_2d")
        cand = make_episode([make_step(0)], system_type="system_c", world_type="hex")
        results.append(compare_episode_traces(ref, cand))

        summary = compute_run_summary(results)
        assert summary.num_episodes_compared == 3
        assert summary.num_valid_pairs == 2
        assert summary.num_invalid_pairs == 1

    def test_survival_counting(self):
        from axis.framework.comparison.summary import compute_run_summary
        # ref dies, cand survives
        ref = make_episode(
            [make_step(i) for i in range(3)],
            termination_reason="energy_depleted",
        )
        cand = make_episode(
            [make_step(i) for i in range(5)],
            system_type="system_c",
            termination_reason="max_steps_reached",
        )
        results = [compare_episode_traces(ref, cand)]
        summary = compute_run_summary(results)
        assert summary.reference_survival_rate == 0.0
        assert summary.candidate_survival_rate == 1.0
        assert summary.candidate_longer_count == 1

    def test_run_comparison_result_json(self):
        from axis.framework.comparison.types import RunComparisonResult, RunComparisonSummary
        from axis.framework.comparison.summary import compute_run_summary
        results = []
        for _ in range(2):
            ref, cand = make_identical_pair(3)
            results.append(compare_episode_traces(ref, cand))
        summary = compute_run_summary(results)
        run_result = RunComparisonResult(
            reference_run_id="run-0000",
            candidate_run_id="run-0000",
            reference_system_type="system_a",
            candidate_system_type="system_c",
            episode_results=tuple(results),
            summary=summary,
        )
        data = run_result.model_dump(mode="json")
        restored = RunComparisonResult.model_validate(data)
        assert restored.summary.num_valid_pairs == 2
        assert len(restored.episode_results) == 2
