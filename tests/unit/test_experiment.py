"""Tests for experiment-level configuration, resolution, and result structures."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from axis_system_a import (
    ExperimentConfig,
    ExperimentResult,
    ExperimentSummary,
    ExperimentType,
    RunConfig,
    RunResult,
    RunSummary,
    RunSummaryEntry,
    SimulationConfig,
)
from axis_system_a.experiment import (
    compute_experiment_summary,
    get_config_value,
    resolve_run_configs,
    set_config_value,
)
from tests.fixtures.scenario_fixtures import make_config
from tests.utils.assertions import assert_model_frozen


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _baseline(**overrides) -> SimulationConfig:
    return make_config(overrides={
        "world": {"grid_width": 5, "grid_height": 5},
        "execution": {"max_steps": 10},
        "logging": {"enabled": False},
        **overrides,
    })


def _make_run_summary(
    *,
    num_episodes: int = 5,
    mean_steps: float = 8.0,
    std_steps: float = 1.0,
    mean_final_energy: float = 30.0,
    std_final_energy: float = 5.0,
    death_rate: float = 0.2,
    mean_consumption_count: float = 1.5,
    std_consumption_count: float = 0.5,
) -> RunSummary:
    return RunSummary(
        num_episodes=num_episodes,
        mean_steps=mean_steps,
        std_steps=std_steps,
        mean_final_energy=mean_final_energy,
        std_final_energy=std_final_energy,
        death_rate=death_rate,
        mean_consumption_count=mean_consumption_count,
        std_consumption_count=std_consumption_count,
    )


def _make_run_result(
    run_id: str = "test-run",
    summary: RunSummary | None = None,
) -> RunResult:
    """Build a minimal RunResult for summary tests (no real episodes)."""
    sim = _baseline()
    rc = RunConfig(simulation=sim, num_episodes=1, base_seed=42)
    s = summary or _make_run_summary()
    # RunResult requires gt=0 for num_episodes and a non-empty episode tuple.
    # We use a real short episode to satisfy the constraint.
    from axis_system_a.runner import run_episode
    from axis_system_a.types import Position
    from axis_system_a.world import create_world

    world = create_world(sim.world, Position(x=0, y=0))
    ep = run_episode(sim, world)
    return RunResult(
        run_id=run_id,
        num_episodes=1,
        episode_results=(ep,),
        summary=s,
        seeds=(42,),
        config=rc,
    )


# ---------------------------------------------------------------------------
# ExperimentType tests
# ---------------------------------------------------------------------------


class TestExperimentType:
    def test_valid_values(self):
        assert ExperimentType.SINGLE_RUN.value == "single_run"
        assert ExperimentType.OFAT.value == "ofat"

    def test_from_string(self):
        assert ExperimentType("single_run") == ExperimentType.SINGLE_RUN
        assert ExperimentType("ofat") == ExperimentType.OFAT

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            ExperimentType("grid_search")


# ---------------------------------------------------------------------------
# Parameter addressing tests
# ---------------------------------------------------------------------------


class TestParameterAddressing:
    def test_get_agent_initial_energy(self):
        cfg = _baseline(agent={"initial_energy": 42.0, "max_energy": 100.0,
                                "memory_capacity": 5})
        assert get_config_value(cfg, "agent.initial_energy") == 42.0

    def test_get_world_grid_width(self):
        cfg = _baseline()
        assert get_config_value(cfg, "world.grid_width") == 5

    def test_get_execution_max_steps(self):
        cfg = _baseline()
        assert get_config_value(cfg, "execution.max_steps") == 10

    def test_set_returns_new_config(self):
        cfg = _baseline()
        new_cfg = set_config_value(cfg, "execution.max_steps", 99)
        assert get_config_value(new_cfg, "execution.max_steps") == 99
        assert get_config_value(cfg, "execution.max_steps") == 10  # unchanged

    def test_set_agent_initial_energy(self):
        cfg = _baseline(agent={"initial_energy": 50.0, "max_energy": 100.0,
                                "memory_capacity": 5})
        new_cfg = set_config_value(cfg, "agent.initial_energy", 25.0)
        assert get_config_value(new_cfg, "agent.initial_energy") == 25.0

    def test_invalid_section_raises(self):
        cfg = _baseline()
        with pytest.raises(ValueError, match="Unknown config section"):
            get_config_value(cfg, "nonexistent.field")

    def test_invalid_field_raises(self):
        cfg = _baseline()
        with pytest.raises(ValueError, match="does not exist"):
            get_config_value(cfg, "agent.nonexistent_field")

    def test_wrong_depth_raises(self):
        cfg = _baseline()
        with pytest.raises(ValueError, match="section.field"):
            get_config_value(cfg, "agent.initial_energy.nested")

    def test_single_segment_raises(self):
        cfg = _baseline()
        with pytest.raises(ValueError, match="section.field"):
            get_config_value(cfg, "agent")

    def test_set_invalid_field_raises(self):
        cfg = _baseline()
        with pytest.raises(ValueError, match="does not exist"):
            set_config_value(cfg, "agent.nonexistent_field", 10)


# ---------------------------------------------------------------------------
# ExperimentConfig – single_run tests
# ---------------------------------------------------------------------------


class TestExperimentConfigSingleRun:
    def test_valid_construction(self):
        cfg = ExperimentConfig(
            experiment_type=ExperimentType.SINGLE_RUN,
            baseline=_baseline(),
            num_episodes_per_run=5,
            base_seed=42,
        )
        assert cfg.experiment_type == ExperimentType.SINGLE_RUN
        assert cfg.num_episodes_per_run == 5

    def test_frozen(self):
        cfg = ExperimentConfig(
            experiment_type=ExperimentType.SINGLE_RUN,
            baseline=_baseline(),
            num_episodes_per_run=3,
        )
        assert_model_frozen(cfg, "num_episodes_per_run", 10)

    def test_parameter_path_forbidden(self):
        with pytest.raises(ValidationError, match="parameter_path must be None"):
            ExperimentConfig(
                experiment_type=ExperimentType.SINGLE_RUN,
                baseline=_baseline(),
                num_episodes_per_run=3,
                parameter_path="agent.initial_energy",
            )

    def test_parameter_values_forbidden(self):
        with pytest.raises(ValidationError, match="parameter_values must be None"):
            ExperimentConfig(
                experiment_type=ExperimentType.SINGLE_RUN,
                baseline=_baseline(),
                num_episodes_per_run=3,
                parameter_values=(1.0, 2.0),
            )

    def test_optional_name(self):
        cfg = ExperimentConfig(
            experiment_type=ExperimentType.SINGLE_RUN,
            baseline=_baseline(),
            num_episodes_per_run=3,
            name="my-experiment",
        )
        assert cfg.name == "my-experiment"


# ---------------------------------------------------------------------------
# ExperimentConfig – ofat tests
# ---------------------------------------------------------------------------


class TestExperimentConfigOfat:
    def test_valid_construction(self):
        cfg = ExperimentConfig(
            experiment_type=ExperimentType.OFAT,
            baseline=_baseline(),
            num_episodes_per_run=5,
            parameter_path="execution.max_steps",
            parameter_values=(5, 10, 20),
        )
        assert cfg.experiment_type == ExperimentType.OFAT
        assert cfg.parameter_values == (5, 10, 20)

    def test_missing_parameter_path_raises(self):
        with pytest.raises(ValidationError, match="parameter_path is required"):
            ExperimentConfig(
                experiment_type=ExperimentType.OFAT,
                baseline=_baseline(),
                num_episodes_per_run=5,
                parameter_values=(5, 10),
            )

    def test_missing_parameter_values_raises(self):
        with pytest.raises(ValidationError, match="parameter_values is required"):
            ExperimentConfig(
                experiment_type=ExperimentType.OFAT,
                baseline=_baseline(),
                num_episodes_per_run=5,
                parameter_path="execution.max_steps",
            )

    def test_empty_parameter_values_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            ExperimentConfig(
                experiment_type=ExperimentType.OFAT,
                baseline=_baseline(),
                num_episodes_per_run=5,
                parameter_path="execution.max_steps",
                parameter_values=(),
            )

    def test_invalid_parameter_path_raises(self):
        with pytest.raises(ValidationError, match="does not exist"):
            ExperimentConfig(
                experiment_type=ExperimentType.OFAT,
                baseline=_baseline(),
                num_episodes_per_run=5,
                parameter_path="agent.nonexistent",
                parameter_values=(1, 2),
            )


# ---------------------------------------------------------------------------
# Resolution – single_run tests
# ---------------------------------------------------------------------------


class TestResolveRunConfigsSingleRun:
    def test_returns_one_run_config(self):
        exp = ExperimentConfig(
            experiment_type=ExperimentType.SINGLE_RUN,
            baseline=_baseline(),
            num_episodes_per_run=5,
            base_seed=42,
        )
        runs = resolve_run_configs(exp)
        assert len(runs) == 1

    def test_run_wraps_baseline(self):
        bl = _baseline()
        exp = ExperimentConfig(
            experiment_type=ExperimentType.SINGLE_RUN,
            baseline=bl,
            num_episodes_per_run=5,
            base_seed=42,
        )
        runs = resolve_run_configs(exp)
        assert runs[0].simulation == bl
        assert runs[0].num_episodes == 5
        assert runs[0].base_seed == 42

    def test_deterministic(self):
        exp = ExperimentConfig(
            experiment_type=ExperimentType.SINGLE_RUN,
            baseline=_baseline(),
            num_episodes_per_run=5,
            base_seed=42,
        )
        r1 = resolve_run_configs(exp)
        r2 = resolve_run_configs(exp)
        assert r1 == r2


# ---------------------------------------------------------------------------
# Resolution – ofat tests
# ---------------------------------------------------------------------------


class TestResolveRunConfigsOfat:
    def test_returns_correct_count(self):
        exp = ExperimentConfig(
            experiment_type=ExperimentType.OFAT,
            baseline=_baseline(),
            num_episodes_per_run=3,
            parameter_path="execution.max_steps",
            parameter_values=(5, 10, 20, 50),
            base_seed=100,
        )
        runs = resolve_run_configs(exp)
        assert len(runs) == 4

    def test_each_run_has_varied_parameter(self):
        exp = ExperimentConfig(
            experiment_type=ExperimentType.OFAT,
            baseline=_baseline(),
            num_episodes_per_run=3,
            parameter_path="execution.max_steps",
            parameter_values=(5, 10, 20),
        )
        runs = resolve_run_configs(exp)
        assert runs[0].simulation.execution.max_steps == 5
        assert runs[1].simulation.execution.max_steps == 10
        assert runs[2].simulation.execution.max_steps == 20

    def test_other_parameters_unchanged(self):
        bl = _baseline()
        exp = ExperimentConfig(
            experiment_type=ExperimentType.OFAT,
            baseline=bl,
            num_episodes_per_run=3,
            parameter_path="execution.max_steps",
            parameter_values=(5, 10),
        )
        runs = resolve_run_configs(exp)
        for run in runs:
            assert run.simulation.world == bl.world
            assert run.simulation.agent == bl.agent

    def test_stable_ordering(self):
        exp = ExperimentConfig(
            experiment_type=ExperimentType.OFAT,
            baseline=_baseline(),
            num_episodes_per_run=3,
            parameter_path="execution.max_steps",
            parameter_values=(5, 10, 20),
            base_seed=42,
        )
        r1 = resolve_run_configs(exp)
        r2 = resolve_run_configs(exp)
        for i in range(3):
            assert r1[i] == r2[i]

    def test_deterministic_seeds(self):
        exp = ExperimentConfig(
            experiment_type=ExperimentType.OFAT,
            baseline=_baseline(),
            num_episodes_per_run=3,
            parameter_path="execution.max_steps",
            parameter_values=(5, 10, 20),
            base_seed=100,
        )
        runs = resolve_run_configs(exp)
        assert runs[0].base_seed == 100
        assert runs[1].base_seed == 1100
        assert runs[2].base_seed == 2100

    def test_none_seed_produces_none_run_seeds(self):
        exp = ExperimentConfig(
            experiment_type=ExperimentType.OFAT,
            baseline=_baseline(),
            num_episodes_per_run=3,
            parameter_path="execution.max_steps",
            parameter_values=(5, 10),
            base_seed=None,
        )
        runs = resolve_run_configs(exp)
        assert runs[0].base_seed is None
        assert runs[1].base_seed is None

    def test_baseline_config_unchanged_after_resolution(self):
        bl = _baseline()
        original_max_steps = bl.execution.max_steps
        exp = ExperimentConfig(
            experiment_type=ExperimentType.OFAT,
            baseline=bl,
            num_episodes_per_run=3,
            parameter_path="execution.max_steps",
            parameter_values=(5, 10, 20),
        )
        resolve_run_configs(exp)
        assert bl.execution.max_steps == original_max_steps

    def test_run_ids_are_deterministic(self):
        exp = ExperimentConfig(
            experiment_type=ExperimentType.OFAT,
            baseline=_baseline(),
            num_episodes_per_run=3,
            parameter_path="execution.max_steps",
            parameter_values=(5, 10, 20),
        )
        runs = resolve_run_configs(exp)
        assert runs[0].run_id == "run-0000"
        assert runs[1].run_id == "run-0001"
        assert runs[2].run_id == "run-0002"


# ---------------------------------------------------------------------------
# ExperimentSummary tests
# ---------------------------------------------------------------------------


class TestExperimentSummary:
    def test_valid_construction(self):
        entry = RunSummaryEntry(
            run_id="run-0000",
            variation_description="baseline",
            summary=_make_run_summary(),
        )
        es = ExperimentSummary(num_runs=1, run_entries=(entry,))
        assert es.num_runs == 1
        assert len(es.run_entries) == 1

    def test_frozen(self):
        entry = RunSummaryEntry(
            run_id="run-0000",
            variation_description="baseline",
            summary=_make_run_summary(),
        )
        es = ExperimentSummary(num_runs=1, run_entries=(entry,))
        assert_model_frozen(es, "num_runs", 99)


class TestComputeExperimentSummary:
    def test_single_run_no_deltas(self):
        rr = _make_run_result(run_id="run-0000")
        cfg = ExperimentConfig(
            experiment_type=ExperimentType.SINGLE_RUN,
            baseline=_baseline(),
            num_episodes_per_run=1,
        )
        es = compute_experiment_summary((rr,), cfg)
        assert es.num_runs == 1
        assert es.run_entries[0].variation_description == "baseline"
        assert es.run_entries[0].delta_mean_steps is None

    def test_ofat_with_baseline_deltas(self):
        baseline_summary = _make_run_summary(
            mean_steps=10.0, mean_final_energy=40.0, death_rate=0.1,
        )
        varied_summary = _make_run_summary(
            mean_steps=15.0, mean_final_energy=35.0, death_rate=0.3,
        )
        rr = _make_run_result(run_id="run-0000", summary=varied_summary)
        cfg = ExperimentConfig(
            experiment_type=ExperimentType.OFAT,
            baseline=_baseline(),
            num_episodes_per_run=1,
            parameter_path="execution.max_steps",
            parameter_values=(20,),
        )
        es = compute_experiment_summary((rr,), cfg, baseline_summary=baseline_summary)
        entry = es.run_entries[0]
        assert entry.delta_mean_steps == pytest.approx(5.0)
        assert entry.delta_mean_final_energy == pytest.approx(-5.0)
        assert entry.delta_death_rate == pytest.approx(0.2)

    def test_multiple_runs_preserved(self):
        rr1 = _make_run_result(run_id="run-0000")
        rr2 = _make_run_result(run_id="run-0001")
        cfg = ExperimentConfig(
            experiment_type=ExperimentType.OFAT,
            baseline=_baseline(),
            num_episodes_per_run=1,
            parameter_path="execution.max_steps",
            parameter_values=(5, 10),
        )
        es = compute_experiment_summary((rr1, rr2), cfg)
        assert es.num_runs == 2
        assert es.run_entries[0].run_id == "run-0000"
        assert es.run_entries[1].run_id == "run-0001"

    def test_variation_descriptions_ofat(self):
        rr1 = _make_run_result(run_id="run-0000")
        rr2 = _make_run_result(run_id="run-0001")
        cfg = ExperimentConfig(
            experiment_type=ExperimentType.OFAT,
            baseline=_baseline(),
            num_episodes_per_run=1,
            parameter_path="execution.max_steps",
            parameter_values=(5, 10),
        )
        es = compute_experiment_summary((rr1, rr2), cfg)
        assert es.run_entries[0].variation_description == "execution.max_steps=5"
        assert es.run_entries[1].variation_description == "execution.max_steps=10"


# ---------------------------------------------------------------------------
# ExperimentResult tests
# ---------------------------------------------------------------------------


class TestExperimentResult:
    def test_valid_construction(self):
        cfg = ExperimentConfig(
            experiment_type=ExperimentType.SINGLE_RUN,
            baseline=_baseline(),
            num_episodes_per_run=1,
        )
        rr = _make_run_result()
        es = compute_experiment_summary((rr,), cfg)
        result = ExperimentResult(
            experiment_config=cfg,
            run_results=(rr,),
            summary=es,
        )
        assert len(result.run_results) == 1
        assert result.summary.num_runs == 1

    def test_frozen(self):
        cfg = ExperimentConfig(
            experiment_type=ExperimentType.SINGLE_RUN,
            baseline=_baseline(),
            num_episodes_per_run=1,
        )
        rr = _make_run_result()
        es = compute_experiment_summary((rr,), cfg)
        result = ExperimentResult(
            experiment_config=cfg,
            run_results=(rr,),
            summary=es,
        )
        assert_model_frozen(result, "summary", es)


# ---------------------------------------------------------------------------
# Serialization tests
# ---------------------------------------------------------------------------


class TestSerialization:
    def test_experiment_config_to_dict(self):
        cfg = ExperimentConfig(
            experiment_type=ExperimentType.SINGLE_RUN,
            baseline=_baseline(),
            num_episodes_per_run=3,
            name="test-exp",
        )
        d = cfg.model_dump()
        assert d["experiment_type"] == "single_run"
        assert d["name"] == "test-exp"
        assert d["num_episodes_per_run"] == 3

    def test_experiment_summary_to_dict(self):
        entry = RunSummaryEntry(
            run_id="run-0000",
            variation_description="baseline",
            summary=_make_run_summary(),
        )
        es = ExperimentSummary(num_runs=1, run_entries=(entry,))
        d = es.model_dump()
        assert d["num_runs"] == 1
        assert len(d["run_entries"]) == 1
        assert d["run_entries"][0]["run_id"] == "run-0000"

    def test_run_summary_entry_to_dict_with_deltas(self):
        entry = RunSummaryEntry(
            run_id="run-0001",
            variation_description="execution.max_steps=20",
            summary=_make_run_summary(),
            delta_mean_steps=5.0,
            delta_mean_final_energy=-3.0,
            delta_death_rate=0.1,
        )
        d = entry.model_dump()
        assert d["delta_mean_steps"] == 5.0
        assert d["delta_mean_final_energy"] == -3.0
        assert d["delta_death_rate"] == 0.1

    def test_experiment_config_ofat_to_dict(self):
        cfg = ExperimentConfig(
            experiment_type=ExperimentType.OFAT,
            baseline=_baseline(),
            num_episodes_per_run=5,
            parameter_path="execution.max_steps",
            parameter_values=(5, 10, 20),
            base_seed=42,
        )
        d = cfg.model_dump()
        assert d["experiment_type"] == "ofat"
        assert d["parameter_path"] == "execution.max_steps"
        assert d["parameter_values"] == (5, 10, 20)

    def test_all_models_json_compatible(self):
        """All new models should be JSON-serializable via model_dump(mode='json')."""
        cfg = ExperimentConfig(
            experiment_type=ExperimentType.SINGLE_RUN,
            baseline=_baseline(),
            num_episodes_per_run=1,
        )
        rr = _make_run_result()
        es = compute_experiment_summary((rr,), cfg)
        result = ExperimentResult(
            experiment_config=cfg,
            run_results=(rr,),
            summary=es,
        )
        # This should not raise
        d = result.model_dump(mode="json")
        assert isinstance(d, dict)
        assert "experiment_config" in d
        assert "run_results" in d
        assert "summary" in d
