"""Error paths and edge cases (WP-3.6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from axis.framework.config import (
    ExperimentConfig,
    ExperimentType,
    ExecutionConfig,
    GeneralConfig,
    LoggingConfig,
)
from axis.framework.experiment import ExperimentExecutor
from axis.framework.persistence import ExperimentRepository, ExperimentStatus
from axis.framework.registry import (
    _SYSTEM_REGISTRY,
    create_system,
    register_system,
)
from axis.framework.run import RunConfig, RunExecutor, RunResult, compute_run_summary
from axis.framework.runner import run_episode, setup_episode
from axis.sdk.position import Position
from axis.sdk.types import DecideResult, TransitionResult
from axis.sdk.world_types import BaseWorldConfig
from tests.framework.mock_system import MockSystem


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_system_registered():
    def mock_factory(config):
        return MockSystem(config)

    if "mock" not in _SYSTEM_REGISTRY:
        register_system("mock", mock_factory)
    yield
    _SYSTEM_REGISTRY.pop("mock", None)


# ---------------------------------------------------------------------------
# Unknown system type
# ---------------------------------------------------------------------------


class TestUnknownSystemType:
    def test_create_unknown_raises(self) -> None:
        with pytest.raises(KeyError, match="nonexistent"):
            create_system("nonexistent", {})


# ---------------------------------------------------------------------------
# Resume errors
# ---------------------------------------------------------------------------


class TestResumeErrors:
    def test_resume_nonexistent_experiment(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)
        executor = ExperimentExecutor(repository=repo)
        with pytest.raises(FileNotFoundError):
            executor.resume("nonexistent-id")

    def test_resume_requires_repository(self) -> None:
        executor = ExperimentExecutor()
        with pytest.raises(RuntimeError, match="requires a repository"):
            executor.resume("some-id")


# ---------------------------------------------------------------------------
# Empty run summary
# ---------------------------------------------------------------------------


class TestEmptyRunSummary:
    def test_zero_episodes(self) -> None:
        summary = compute_run_summary(())
        assert summary.num_episodes == 0
        assert summary.mean_steps == 0.0
        assert summary.std_steps == 0.0
        assert summary.mean_final_vitality == 0.0
        assert summary.death_rate == 0.0


# ---------------------------------------------------------------------------
# Termination modes
# ---------------------------------------------------------------------------


class TestTerminationModes:
    def test_max_steps_termination(self) -> None:
        # Energy 10, max_steps 3 => agent survives, hits max_steps
        system = MockSystem({"initial_energy": 10.0, "max_energy": 10.0})
        world, registry = setup_episode(
            system,
            BaseWorldConfig(grid_width=5, grid_height=5),
            Position(x=0, y=0),
            seed=42,
        )
        trace = run_episode(
            system, world, registry, max_steps=3, seed=42,
        )
        assert trace.total_steps == 3
        assert trace.termination_reason == "max_steps_reached"
        assert trace.final_vitality > 0.0

    def test_system_termination(self) -> None:
        # Energy 5, max_steps 20 => agent dies at step 5
        system = MockSystem({"initial_energy": 5.0, "max_energy": 5.0})
        world, registry = setup_episode(
            system,
            BaseWorldConfig(grid_width=5, grid_height=5),
            Position(x=0, y=0),
            seed=42,
        )
        trace = run_episode(
            system, world, registry, max_steps=20, seed=42,
        )
        assert trace.total_steps == 5
        assert trace.termination_reason == "energy_depleted"
        assert trace.final_vitality == 0.0


# ---------------------------------------------------------------------------
# Invalid action from system
# ---------------------------------------------------------------------------


class _BadActionSystem(MockSystem):
    """System that returns an unregistered action."""

    def decide(self, world_view, agent_state, rng):
        return DecideResult(action="fly", decision_data={})


class TestInvalidAction:
    def test_invalid_action_raises(self) -> None:
        system = _BadActionSystem()
        world, registry = setup_episode(
            system,
            BaseWorldConfig(grid_width=5, grid_height=5),
            Position(x=0, y=0),
            seed=42,
        )
        with pytest.raises((KeyError, ValueError)):
            run_episode(
                system, world, registry, max_steps=5, seed=42,
            )


# ---------------------------------------------------------------------------
# Resume completed experiment
# ---------------------------------------------------------------------------


class TestResumeCompleted:
    def test_resume_completed_no_reexecution(self, tmp_path: Path) -> None:
        config = ExperimentConfig(
            system_type="mock",
            experiment_type=ExperimentType.SINGLE_RUN,
            general=GeneralConfig(seed=42),
            execution=ExecutionConfig(max_steps=10),
            world=BaseWorldConfig(grid_width=5, grid_height=5),
            logging=LoggingConfig(enabled=False),
            system={"initial_energy": 10.0, "max_energy": 10.0},
            num_episodes_per_run=1,
        )
        repo = ExperimentRepository(tmp_path)
        executor = ExperimentExecutor(repository=repo)
        result = executor.execute(config)

        eid = repo.list_experiments()[0]
        assert repo.load_experiment_status(eid) == ExperimentStatus.COMPLETED

        # Resume should succeed without error
        resumed = ExperimentExecutor(repository=repo).resume(eid)
        assert resumed.summary.num_runs == result.summary.num_runs
        assert repo.load_experiment_status(eid) == ExperimentStatus.COMPLETED
