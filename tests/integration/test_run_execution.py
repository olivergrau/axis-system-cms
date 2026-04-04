"""Integration tests for run-level execution, determinism, and aggregation."""

from __future__ import annotations

from axis_system_a import (
    EpisodeResult,
    RunConfig,
    RunResult,
    TerminationReason,
)
from axis_system_a.run import RunExecutor, execute_run
from tests.fixtures.scenario_fixtures import make_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_run_config(
    num_episodes: int = 3,
    base_seed: int = 42,
    max_steps: int = 10,
    **overrides,
) -> RunConfig:
    sim_config = make_config(overrides={
        "world": {"grid_width": 3, "grid_height": 3},
        "execution": {"max_steps": max_steps},
        "logging": {"enabled": False},
        **overrides,
    })
    return RunConfig(
        simulation=sim_config,
        num_episodes=num_episodes,
        base_seed=base_seed,
    )


# ---------------------------------------------------------------------------
# Basic execution tests
# ---------------------------------------------------------------------------


class TestRunExecutorBasic:
    def test_executes_correct_number_of_episodes(self):
        config = _make_run_config(num_episodes=3)
        result = RunExecutor().execute(config)
        assert len(result.episode_results) == 3
        assert result.num_episodes == 3

    def test_executes_single_episode(self):
        config = _make_run_config(num_episodes=1)
        result = RunExecutor().execute(config)
        assert len(result.episode_results) == 1

    def test_all_episodes_have_results(self):
        config = _make_run_config(num_episodes=5)
        result = RunExecutor().execute(config)
        for er in result.episode_results:
            assert isinstance(er, EpisodeResult)

    def test_seeds_stored_in_result(self):
        config = _make_run_config(num_episodes=4, base_seed=100)
        result = RunExecutor().execute(config)
        assert len(result.seeds) == 4
        assert result.seeds == (100, 101, 102, 103)

    def test_run_id_auto_generated(self):
        config = _make_run_config(num_episodes=1)
        result = RunExecutor().execute(config)
        assert isinstance(result.run_id, str)
        assert len(result.run_id) > 0

    def test_run_id_preserved(self):
        sim_config = make_config(overrides={
            "world": {"grid_width": 3, "grid_height": 3},
            "execution": {"max_steps": 5},
            "logging": {"enabled": False},
        })
        config = RunConfig(
            simulation=sim_config, num_episodes=1,
            base_seed=42, run_id="my-run-123",
        )
        result = RunExecutor().execute(config)
        assert result.run_id == "my-run-123"

    def test_config_stored_in_result(self):
        config = _make_run_config(num_episodes=2)
        result = RunExecutor().execute(config)
        assert result.config == config

    def test_execute_run_convenience(self):
        config = _make_run_config(num_episodes=2)
        result = execute_run(config)
        assert isinstance(result, RunResult)
        assert result.num_episodes == 2


# ---------------------------------------------------------------------------
# Determinism tests
# ---------------------------------------------------------------------------


class TestRunExecutorDeterminism:
    def test_same_seed_same_results(self):
        config = _make_run_config(num_episodes=3, base_seed=42, max_steps=10)
        r1 = RunExecutor().execute(config)
        r2 = RunExecutor().execute(config)

        for i in range(3):
            assert r1.episode_results[i].total_steps == \
                r2.episode_results[i].total_steps
            assert r1.episode_results[i].final_agent_state.energy == \
                r2.episode_results[i].final_agent_state.energy
            assert r1.episode_results[i].termination_reason == \
                r2.episode_results[i].termination_reason

    def test_different_seeds_different_results(self):
        c1 = _make_run_config(num_episodes=5, base_seed=42, max_steps=50)
        c2 = _make_run_config(num_episodes=5, base_seed=99, max_steps=50)
        r1 = RunExecutor().execute(c1)
        r2 = RunExecutor().execute(c2)

        # At least one episode should differ in total_steps or final_energy
        any_different = any(
            r1.episode_results[i].total_steps !=
            r2.episode_results[i].total_steps
            or r1.episode_results[i].final_agent_state.energy !=
            r2.episode_results[i].final_agent_state.energy
            for i in range(5)
        )
        assert any_different

    def test_episodes_use_different_seeds(self):
        """Episodes within a run should have different trajectories."""
        # Use a resource-rich world so stochastic policy choices
        # lead to different paths and final energies.
        config = _make_run_config(
            num_episodes=5, base_seed=42, max_steps=20,
            agent={"initial_energy": 50.0, "max_energy": 100.0,
                   "memory_capacity": 5},
            world={"grid_width": 5, "grid_height": 5,
                   "resource_regen_rate": 0.3},
            policy={"selection_mode": "sample", "temperature": 1.0,
                    "stay_suppression": 0.1, "consume_weight": 1.5},
        )
        result = RunExecutor().execute(config)

        # With stochastic sampling on a resource world,
        # not all episodes should have identical final energy.
        final_energies = [
            er.final_agent_state.energy for er in result.episode_results
        ]
        assert len(set(final_energies)) > 1, (
            "All episodes have identical final energy — seeds may not differ"
        )


# ---------------------------------------------------------------------------
# Aggregation tests
# ---------------------------------------------------------------------------


class TestRunExecutorAggregation:
    def test_summary_mean_steps(self):
        config = _make_run_config(num_episodes=5, base_seed=42, max_steps=20)
        result = RunExecutor().execute(config)
        expected = sum(
            er.total_steps for er in result.episode_results
        ) / result.num_episodes
        assert result.summary.mean_steps == expected

    def test_summary_mean_final_energy(self):
        config = _make_run_config(num_episodes=5, base_seed=42, max_steps=20)
        result = RunExecutor().execute(config)
        expected = sum(
            er.final_agent_state.energy for er in result.episode_results
        ) / result.num_episodes
        assert result.summary.mean_final_energy == expected

    def test_summary_death_rate(self):
        config = _make_run_config(num_episodes=5, base_seed=42, max_steps=20)
        result = RunExecutor().execute(config)
        deaths = sum(
            1 for er in result.episode_results
            if er.termination_reason == TerminationReason.ENERGY_DEPLETED
        )
        expected = deaths / result.num_episodes
        assert result.summary.death_rate == expected

    def test_summary_num_episodes(self):
        config = _make_run_config(num_episodes=4, base_seed=42)
        result = RunExecutor().execute(config)
        assert result.summary.num_episodes == 4


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestRunExecutorEdgeCases:
    def test_max_steps_one(self):
        config = _make_run_config(num_episodes=3, base_seed=42, max_steps=1)
        result = RunExecutor().execute(config)
        for er in result.episode_results:
            assert er.total_steps == 1

    def test_all_episodes_die(self):
        config = _make_run_config(
            num_episodes=3, base_seed=42, max_steps=100,
            agent={"initial_energy": 2.0, "max_energy": 100.0,
                   "memory_capacity": 5},
        )
        result = RunExecutor().execute(config)
        assert result.summary.death_rate == 1.0
        for er in result.episode_results:
            assert er.termination_reason == TerminationReason.ENERGY_DEPLETED
