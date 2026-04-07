"""Tests for the run executor (WP-3.3)."""

from __future__ import annotations

import pytest

from axis.framework.run import (
    RunConfig,
    RunExecutor,
    RunResult,
    RunSummary,
    compute_run_summary,
    resolve_episode_seeds,
)
from axis.sdk.trace import BaseEpisodeTrace
from tests.v02.builders.config_builder import FrameworkConfigBuilder
from tests.v02.builders.system_config_builder import SystemAConfigBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _default_run_config(
    *,
    num_episodes: int = 3,
    base_seed: int = 42,
    max_steps: int = 50,
) -> RunConfig:
    return RunConfig(
        system_type="system_a",
        system_config=SystemAConfigBuilder().build(),
        framework_config=FrameworkConfigBuilder().with_max_steps(max_steps).build(),
        num_episodes=num_episodes,
        base_seed=base_seed,
    )


# ---------------------------------------------------------------------------
# RunConfig tests
# ---------------------------------------------------------------------------


class TestRunConfig:
    """RunConfig construction and immutability."""

    def test_run_config_construction(self) -> None:
        rc = _default_run_config()
        assert rc.system_type == "system_a"
        assert rc.num_episodes == 3

    def test_run_config_frozen(self) -> None:
        rc = _default_run_config()
        with pytest.raises(Exception):
            rc.num_episodes = 5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# resolve_episode_seeds tests
# ---------------------------------------------------------------------------


class TestResolveEpisodeSeeds:
    """Episode seed derivation."""

    def test_deterministic(self) -> None:
        s1 = resolve_episode_seeds(5, 42)
        s2 = resolve_episode_seeds(5, 42)
        assert s1 == s2

    def test_sequential(self) -> None:
        seeds = resolve_episode_seeds(3, 100)
        assert seeds == (100, 101, 102)

    def test_none_base_seed(self) -> None:
        seeds = resolve_episode_seeds(3, None)
        assert len(seeds) == 3
        assert all(isinstance(s, int) for s in seeds)


# ---------------------------------------------------------------------------
# RunExecutor tests
# ---------------------------------------------------------------------------


class TestRunExecutor:
    """Run execution and result structure."""

    def test_returns_run_result(self) -> None:
        executor = RunExecutor()
        result = executor.execute(_default_run_config())
        assert isinstance(result, RunResult)

    def test_episode_count(self) -> None:
        executor = RunExecutor()
        result = executor.execute(_default_run_config(num_episodes=2))
        assert len(result.episode_traces) == 2
        assert result.num_episodes == 2

    def test_seeds(self) -> None:
        executor = RunExecutor()
        result = executor.execute(_default_run_config(num_episodes=3))
        assert len(result.seeds) == 3

    def test_summary_mean_steps(self) -> None:
        executor = RunExecutor()
        result = executor.execute(_default_run_config())
        assert result.summary.mean_steps > 0

    def test_summary_vitality_based(self) -> None:
        executor = RunExecutor()
        result = executor.execute(_default_run_config())
        assert 0.0 <= result.summary.mean_final_vitality <= 1.0

    def test_summary_death_rate(self) -> None:
        cfg = _default_run_config(num_episodes=2, max_steps=5)
        executor = RunExecutor()
        result = executor.execute(cfg)
        assert 0.0 <= result.summary.death_rate <= 1.0

    def test_deterministic(self) -> None:
        executor = RunExecutor()
        r1 = executor.execute(_default_run_config(num_episodes=2))
        r2 = executor.execute(_default_run_config(num_episodes=2))
        assert r1.summary.mean_steps == r2.summary.mean_steps
        assert r1.summary.mean_final_vitality == r2.summary.mean_final_vitality
        for t1, t2 in zip(r1.episode_traces, r2.episode_traces):
            a1 = [s.action for s in t1.steps]
            a2 = [s.action for s in t2.steps]
            assert a1 == a2

    def test_uses_registry(self) -> None:
        """System is resolved via the registry (indirect test)."""
        executor = RunExecutor()
        result = executor.execute(_default_run_config())
        assert result.episode_traces[0].system_type == "system_a"


# ---------------------------------------------------------------------------
# compute_run_summary tests
# ---------------------------------------------------------------------------


class TestComputeRunSummary:
    """Summary computation edge cases."""

    def test_empty(self) -> None:
        summary = compute_run_summary(())
        assert summary.num_episodes == 0
        assert summary.mean_steps == 0.0
        assert summary.death_rate == 0.0
