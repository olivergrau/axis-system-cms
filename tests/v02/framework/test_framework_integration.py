"""Cross-component integration tests using MockSystem (WP-3.6).

These tests prove the framework is system-agnostic by running the full
pipeline (registry -> executor -> runner -> persistence -> resume) with
a mock system that never imports from axis.systems.system_a.
"""

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
from axis.framework.experiment import ExperimentExecutor, ExperimentResult
from axis.framework.persistence import (
    ExperimentRepository,
    ExperimentStatus,
    RunStatus,
)
from axis.framework.registry import _SYSTEM_REGISTRY, register_system
from axis.framework.run import RunConfig, RunExecutor, RunResult, RunSummary
from axis.framework.runner import run_episode, setup_episode
from axis.sdk.position import Position
from axis.sdk.trace import BaseEpisodeTrace
from axis.sdk.world_types import BaseWorldConfig
from tests.v02.framework.mock_system import MockSystem


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_system_registered():
    """Register the mock system for each test and clean up after."""
    def mock_factory(config):
        return MockSystem(config)

    if "mock" not in _SYSTEM_REGISTRY:
        register_system("mock", mock_factory)
    yield
    _SYSTEM_REGISTRY.pop("mock", None)


def _mock_experiment_config(
    *,
    max_steps: int = 15,
    num_episodes: int = 2,
    seed: int = 42,
) -> ExperimentConfig:
    return ExperimentConfig(
        system_type="mock",
        experiment_type=ExperimentType.SINGLE_RUN,
        general=GeneralConfig(seed=seed),
        execution=ExecutionConfig(max_steps=max_steps),
        world=BaseWorldConfig(grid_width=5, grid_height=5),
        logging=LoggingConfig(enabled=False),
        system={"initial_energy": 10.0, "max_energy": 10.0},
        num_episodes_per_run=num_episodes,
    )


def _mock_run_config(
    *,
    max_steps: int = 15,
    num_episodes: int = 2,
    seed: int = 42,
) -> RunConfig:
    from axis.framework.config import FrameworkConfig

    return RunConfig(
        system_type="mock",
        system_config={"initial_energy": 10.0, "max_energy": 10.0},
        framework_config=FrameworkConfig(
            general=GeneralConfig(seed=seed),
            execution=ExecutionConfig(max_steps=max_steps),
            world=BaseWorldConfig(grid_width=5, grid_height=5),
            logging=LoggingConfig(enabled=False),
        ),
        num_episodes=num_episodes,
        base_seed=seed,
        run_id="run-0000",
    )


# ---------------------------------------------------------------------------
# Registry -> Runner integration
# ---------------------------------------------------------------------------


class TestRegistryToRunner:
    """Create mock system via registry, run episode via runner."""

    def test_registry_to_runner(self) -> None:
        from axis.framework.registry import create_system

        system = create_system("mock", {"initial_energy": 10.0, "max_energy": 10.0})
        world, registry = setup_episode(
            system,
            BaseWorldConfig(grid_width=5, grid_height=5),
            Position(x=0, y=0),
            seed=42,
        )
        trace = run_episode(
            system, world, registry, max_steps=15, regen_rate=0.0, seed=42,
        )
        assert isinstance(trace, BaseEpisodeTrace)
        assert trace.system_type == "mock"
        assert trace.total_steps == 10
        assert trace.termination_reason == "energy_depleted"


# ---------------------------------------------------------------------------
# Registry -> RunExecutor integration
# ---------------------------------------------------------------------------


class TestRegistryToExecutor:
    """Create RunConfig with mock, execute via RunExecutor."""

    def test_run_executor_with_mock(self) -> None:
        config = _mock_run_config()
        executor = RunExecutor()
        result = executor.execute(config)
        assert isinstance(result, RunResult)
        assert result.num_episodes == 2
        assert result.summary.death_rate > 0


# ---------------------------------------------------------------------------
# Full ExperimentExecutor integration
# ---------------------------------------------------------------------------


class TestExperimentExecutorMock:
    """Full ExperimentExecutor with mock system."""

    def test_single_run_mock(self) -> None:
        config = _mock_experiment_config()
        executor = ExperimentExecutor()
        result = executor.execute(config)
        assert isinstance(result, ExperimentResult)
        assert result.summary.num_runs == 1
        assert len(result.run_results) == 1

    def test_ofat_framework_path(self) -> None:
        config = ExperimentConfig(
            system_type="mock",
            experiment_type=ExperimentType.OFAT,
            general=GeneralConfig(seed=42),
            execution=ExecutionConfig(max_steps=15),
            world=BaseWorldConfig(grid_width=5, grid_height=5),
            logging=LoggingConfig(enabled=False),
            system={"initial_energy": 10.0, "max_energy": 10.0},
            num_episodes_per_run=2,
            parameter_path="framework.execution.max_steps",
            parameter_values=(5, 10, 20),
        )
        executor = ExperimentExecutor()
        result = executor.execute(config)
        assert result.summary.num_runs == 3

    def test_ofat_system_path(self) -> None:
        config = ExperimentConfig(
            system_type="mock",
            experiment_type=ExperimentType.OFAT,
            general=GeneralConfig(seed=42),
            execution=ExecutionConfig(max_steps=15),
            world=BaseWorldConfig(grid_width=5, grid_height=5),
            logging=LoggingConfig(enabled=False),
            system={"initial_energy": 10.0, "max_energy": 10.0, "section": {"param": 1}},
            num_episodes_per_run=1,
            parameter_path="system.section.param",
            parameter_values=(1, 2, 3),
        )
        executor = ExperimentExecutor()
        result = executor.execute(config)
        assert result.summary.num_runs == 3


# ---------------------------------------------------------------------------
# Persistence roundtrip
# ---------------------------------------------------------------------------


class TestPersistenceRoundtrip:
    """Execute with persistence, reload all artifacts."""

    def test_persistence_roundtrip(self, tmp_path: Path) -> None:
        config = _mock_experiment_config()
        repo = ExperimentRepository(tmp_path)
        executor = ExperimentExecutor(repository=repo)
        result = executor.execute(config)

        # Verify all artifacts
        eids = repo.list_experiments()
        assert len(eids) == 1
        eid = eids[0]

        assert repo.load_experiment_status(eid) == ExperimentStatus.COMPLETED
        loaded_config = repo.load_experiment_config(eid)
        assert loaded_config.system_type == "mock"

        meta = repo.load_experiment_metadata(eid)
        assert meta.system_type == "mock"

        runs = repo.list_runs(eid)
        assert len(runs) == 1
        rid = runs[0]
        assert repo.load_run_status(eid, rid) == RunStatus.COMPLETED

        loaded_summary = repo.load_run_summary(eid, rid)
        assert loaded_summary.num_episodes == 2

        loaded_result = repo.load_run_result(eid, rid)
        assert loaded_result.num_episodes == 2

        episodes = repo.list_episode_files(eid, rid)
        assert len(episodes) == 2

    def test_resume_with_mock(self, tmp_path: Path) -> None:
        config = _mock_experiment_config()
        repo = ExperimentRepository(tmp_path)
        executor = ExperimentExecutor(repository=repo)
        result = executor.execute(config)

        eid = repo.list_experiments()[0]
        rid = repo.list_runs(eid)[0]

        # Corrupt run status to simulate failure
        repo.save_run_status(eid, rid, RunStatus.FAILED)

        # Resume
        resumed = ExperimentExecutor(repository=repo).resume(eid)
        assert resumed.summary.num_runs == 1
        assert repo.load_run_status(eid, rid) == RunStatus.COMPLETED


# ---------------------------------------------------------------------------
# Trace and summary validation
# ---------------------------------------------------------------------------


class TestTraceAndSummary:
    """Validate trace content and summary aggregation."""

    def test_episode_trace_system_data(self) -> None:
        system = MockSystem()
        world, registry = setup_episode(
            system,
            BaseWorldConfig(grid_width=5, grid_height=5),
            Position(x=0, y=0),
            seed=42,
        )
        trace = run_episode(
            system, world, registry, max_steps=5, regen_rate=0.0, seed=42,
        )
        step = trace.steps[0]
        assert "decision_data" in step.system_data
        assert step.system_data["decision_data"]["reason"] == "always_right"
        assert "trace_data" in step.system_data
        assert "energy_before" in step.system_data["trace_data"]

    def test_vitality_in_summary(self) -> None:
        config = _mock_run_config(max_steps=5, num_episodes=1)
        result = RunExecutor().execute(config)
        # Mock starts at 10, loses 1/step for 5 steps -> final energy 5, vitality 0.5
        assert result.summary.mean_final_vitality == pytest.approx(0.5)

    def test_death_rate_calculation(self) -> None:
        # With max_steps=15 and initial_energy=10, agent dies at step 10
        config = _mock_run_config(max_steps=15, num_episodes=3)
        result = RunExecutor().execute(config)
        # All episodes should terminate via energy depletion
        assert result.summary.death_rate == pytest.approx(1.0)

    def test_no_death_when_steps_limited(self) -> None:
        # With max_steps=3 and initial_energy=10, agent survives
        config = _mock_run_config(max_steps=3, num_episodes=2)
        result = RunExecutor().execute(config)
        assert result.summary.death_rate == pytest.approx(0.0)

    def test_deterministic_across_runs(self) -> None:
        config = _mock_run_config(max_steps=15, num_episodes=2)
        r1 = RunExecutor().execute(config)
        r2 = RunExecutor().execute(config)
        assert r1.summary.mean_steps == r2.summary.mean_steps
        assert r1.summary.death_rate == r2.summary.death_rate

    def test_different_seeds_same_mock_results(self) -> None:
        # MockSystem always goes right regardless of seed, so step count is deterministic
        c1 = _mock_run_config(max_steps=15, num_episodes=1, seed=1)
        c2 = _mock_run_config(max_steps=15, num_episodes=1, seed=999)
        r1 = RunExecutor().execute(c1)
        r2 = RunExecutor().execute(c2)
        # Both should die at step 10 since mock always goes right with same energy
        assert r1.summary.mean_steps == r2.summary.mean_steps
