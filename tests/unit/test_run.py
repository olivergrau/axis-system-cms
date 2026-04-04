"""Tests for run-level orchestration models and functions."""

import pytest
from pydantic import ValidationError

from axis_system_a import (
    EpisodeResult,
    Position,
    RunConfig,
    RunContext,
    RunResult,
    RunSummary,
    TerminationReason,
)
from axis_system_a.run import compute_run_summary, resolve_episode_seeds
from axis_system_a.runner import run_episode
from axis_system_a.world import create_world
from tests.fixtures.scenario_fixtures import make_config
from tests.utils.assertions import assert_model_frozen


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sim_config(**overrides):
    return make_config(overrides={
        "world": {"grid_width": 3, "grid_height": 3},
        "execution": {"max_steps": 5},
        "logging": {"enabled": False},
        **overrides,
    })


def _run_short_episode(*, seed: int = 42, max_steps: int = 5,
                        grid_width: int = 3, grid_height: int = 3,
                        initial_energy: float = 50.0) -> EpisodeResult:
    """Run a short real episode and return the result."""
    config = make_config(overrides={
        "general": {"seed": seed},
        "world": {"grid_width": grid_width, "grid_height": grid_height},
        "agent": {"initial_energy": initial_energy, "max_energy": 100.0,
                  "memory_capacity": 5},
        "execution": {"max_steps": max_steps},
        "logging": {"enabled": False},
    })
    world = create_world(config.world, Position(x=0, y=0))
    return run_episode(config, world)


# ---------------------------------------------------------------------------
# RunConfig tests
# ---------------------------------------------------------------------------


class TestRunConfig:
    def test_valid_construction(self):
        config = RunConfig(
            simulation=_sim_config(),
            num_episodes=5,
            base_seed=42,
        )
        assert config.num_episodes == 5
        assert config.base_seed == 42

    def test_num_episodes_zero_invalid(self):
        with pytest.raises(ValidationError):
            RunConfig(simulation=_sim_config(), num_episodes=0)

    def test_num_episodes_negative_invalid(self):
        with pytest.raises(ValidationError):
            RunConfig(simulation=_sim_config(), num_episodes=-1)

    def test_frozen(self):
        config = RunConfig(simulation=_sim_config(), num_episodes=3)
        assert_model_frozen(config, "num_episodes", 10)

    def test_default_agent_position(self):
        config = RunConfig(simulation=_sim_config(), num_episodes=1)
        assert config.agent_start_position == Position(x=0, y=0)

    def test_base_seed_none_allowed(self):
        config = RunConfig(simulation=_sim_config(), num_episodes=1)
        assert config.base_seed is None

    def test_run_id_optional(self):
        config = RunConfig(simulation=_sim_config(), num_episodes=1)
        assert config.run_id is None

    def test_description_optional(self):
        config = RunConfig(
            simulation=_sim_config(), num_episodes=1,
            description="test run",
        )
        assert config.description == "test run"


# ---------------------------------------------------------------------------
# RunContext tests
# ---------------------------------------------------------------------------


class TestRunContext:
    def test_valid_construction(self):
        rc = RunConfig(simulation=_sim_config(), num_episodes=3, base_seed=42)
        ctx = RunContext(
            run_id="test-run",
            run_config=rc,
            episode_seeds=(42, 43, 44),
        )
        assert ctx.run_id == "test-run"
        assert len(ctx.episode_seeds) == 3

    def test_frozen(self):
        rc = RunConfig(simulation=_sim_config(), num_episodes=1, base_seed=42)
        ctx = RunContext(
            run_id="test", run_config=rc, episode_seeds=(42,),
        )
        assert_model_frozen(ctx, "run_id", "other")


# ---------------------------------------------------------------------------
# RunSummary tests
# ---------------------------------------------------------------------------


class TestRunSummary:
    def test_valid_construction(self):
        s = RunSummary(
            num_episodes=10, mean_steps=5.0,
            mean_final_energy=30.0, death_rate=0.3,
        )
        assert s.num_episodes == 10
        assert s.death_rate == 0.3

    def test_frozen(self):
        s = RunSummary(
            num_episodes=1, mean_steps=1.0,
            mean_final_energy=0.0, death_rate=0.0,
        )
        assert_model_frozen(s, "mean_steps", 99.0)

    def test_death_rate_above_one_invalid(self):
        with pytest.raises(ValidationError):
            RunSummary(
                num_episodes=1, mean_steps=1.0,
                mean_final_energy=0.0, death_rate=1.1,
            )

    def test_death_rate_negative_invalid(self):
        with pytest.raises(ValidationError):
            RunSummary(
                num_episodes=1, mean_steps=1.0,
                mean_final_energy=0.0, death_rate=-0.1,
            )


# ---------------------------------------------------------------------------
# RunResult tests
# ---------------------------------------------------------------------------


class TestRunResult:
    def test_valid_construction(self):
        rc = RunConfig(simulation=_sim_config(), num_episodes=1, base_seed=42)
        ep = _run_short_episode()
        summary = compute_run_summary((ep,))
        result = RunResult(
            run_id="test",
            num_episodes=1,
            episode_results=(ep,),
            summary=summary,
            seeds=(42,),
            config=rc,
        )
        assert result.run_id == "test"
        assert result.num_episodes == 1

    def test_frozen(self):
        rc = RunConfig(simulation=_sim_config(), num_episodes=1, base_seed=42)
        ep = _run_short_episode()
        summary = compute_run_summary((ep,))
        result = RunResult(
            run_id="test", num_episodes=1,
            episode_results=(ep,), summary=summary,
            seeds=(42,), config=rc,
        )
        assert_model_frozen(result, "run_id", "other")


# ---------------------------------------------------------------------------
# resolve_episode_seeds tests
# ---------------------------------------------------------------------------


class TestResolveEpisodeSeeds:
    def test_deterministic_with_base_seed(self):
        seeds = resolve_episode_seeds(5, base_seed=42)
        assert seeds == (42, 43, 44, 45, 46)

    def test_correct_count(self):
        seeds = resolve_episode_seeds(10, base_seed=0)
        assert len(seeds) == 10

    def test_none_seed_generates_correct_count(self):
        seeds = resolve_episode_seeds(7, base_seed=None)
        assert len(seeds) == 7
        assert all(isinstance(s, int) for s in seeds)

    def test_same_base_seed_same_result(self):
        s1 = resolve_episode_seeds(5, base_seed=99)
        s2 = resolve_episode_seeds(5, base_seed=99)
        assert s1 == s2


# ---------------------------------------------------------------------------
# compute_run_summary tests
# ---------------------------------------------------------------------------


class TestComputeRunSummary:
    def test_empty_episodes(self):
        summary = compute_run_summary(())
        assert summary.num_episodes == 0
        assert summary.mean_steps == 0.0
        assert summary.death_rate == 0.0

    def test_mean_steps(self):
        # Use very short episodes with different step counts
        ep1 = _run_short_episode(seed=42, max_steps=2)
        ep2 = _run_short_episode(seed=43, max_steps=5)
        expected = (ep1.total_steps + ep2.total_steps) / 2
        summary = compute_run_summary((ep1, ep2))
        assert summary.mean_steps == pytest.approx(expected)

    def test_mean_final_energy(self):
        ep1 = _run_short_episode(seed=42, max_steps=3)
        ep2 = _run_short_episode(seed=43, max_steps=3)
        expected = (
            ep1.final_agent_state.energy + ep2.final_agent_state.energy
        ) / 2
        summary = compute_run_summary((ep1, ep2))
        assert summary.mean_final_energy == pytest.approx(expected)

    def test_death_rate_all_survived(self):
        # High energy + short max_steps = all survive
        ep1 = _run_short_episode(seed=42, max_steps=2, initial_energy=50.0)
        ep2 = _run_short_episode(seed=43, max_steps=2, initial_energy=50.0)
        summary = compute_run_summary((ep1, ep2))
        assert summary.death_rate == 0.0

    def test_death_rate_all_died(self):
        # Low energy + long max_steps on empty world = all die
        ep1 = _run_short_episode(seed=42, max_steps=100, initial_energy=2.0)
        ep2 = _run_short_episode(seed=43, max_steps=100, initial_energy=2.0)
        assert ep1.termination_reason == TerminationReason.ENERGY_DEPLETED
        assert ep2.termination_reason == TerminationReason.ENERGY_DEPLETED
        summary = compute_run_summary((ep1, ep2))
        assert summary.death_rate == 1.0

    def test_num_episodes_matches(self):
        ep1 = _run_short_episode(seed=42)
        ep2 = _run_short_episode(seed=43)
        ep3 = _run_short_episode(seed=44)
        summary = compute_run_summary((ep1, ep2, ep3))
        assert summary.num_episodes == 3
