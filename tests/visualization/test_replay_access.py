"""Tests for WP-V.3.1: Replay Access Service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from axis.framework.config import (
    ExperimentConfig,
    ExperimentType,
    ExecutionConfig,
    GeneralConfig,
)
from axis.framework.persistence import ExperimentRepository
from axis.framework.run import RunConfig, RunSummary
from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import (
    BaseEpisodeTrace,
    BaseStepTrace,
    DeltaEpisodeTrace,
    DeltaStepTrace,
    WorldDelta,
)
from axis.sdk.world_types import BaseWorldConfig, CellView

from axis.visualization.errors import (
    EpisodeNotFoundError,
    ExperimentNotFoundError,
    MalformedArtifactError,
    ReplayContractViolation,
    RunNotFoundError,
)
from axis.visualization.replay_access import ReplayAccessService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cell() -> CellView:
    return CellView(cell_type="empty", resource_value=0.0)


def _make_snapshot(width: int = 5, height: int = 5) -> WorldSnapshot:
    grid = tuple(
        tuple(_make_cell() for _ in range(width))
        for _ in range(height)
    )
    return WorldSnapshot(
        grid=grid, agent_position=Position(x=0, y=0),
        width=width, height=height,
    )


def _make_step(timestep: int = 0) -> BaseStepTrace:
    snap = _make_snapshot()
    return BaseStepTrace(
        timestep=timestep,
        action="stay",
        world_before=snap,
        world_after=snap,
        agent_position_before=Position(x=0, y=0),
        agent_position_after=Position(x=0, y=0),
        vitality_before=1.0,
        vitality_after=0.9,
        terminated=False,
    )


def _make_episode(num_steps: int = 3) -> BaseEpisodeTrace:
    steps = tuple(_make_step(timestep=i) for i in range(num_steps))
    return BaseEpisodeTrace(
        system_type="test",
        steps=steps,
        total_steps=num_steps,
        termination_reason="max_steps",
        final_vitality=0.9,
        final_position=Position(x=0, y=0),
    )


def _make_experiment_config() -> ExperimentConfig:
    return ExperimentConfig(
        system_type="test",
        experiment_type=ExperimentType.SINGLE_RUN,
        general=GeneralConfig(seed=42),
        execution=ExecutionConfig(max_steps=100),
        world=BaseWorldConfig(),
        system={},
        num_episodes_per_run=1,
    )


def _framework_config():
    from axis.framework.config import FrameworkConfig, LoggingConfig
    return FrameworkConfig(
        general=GeneralConfig(seed=42),
        execution=ExecutionConfig(max_steps=100),
        world=BaseWorldConfig(),
        logging=LoggingConfig(),
    )


def _make_run_config() -> RunConfig:
    return RunConfig(
        system_type="test",
        system_config={},
        framework_config=_framework_config(),
        num_episodes=1,
    )


def _setup_repo(
    tmp_path: Path,
    *,
    experiments: list[str] | None = None,
    runs: dict[str, list[str]] | None = None,
    episodes: dict[tuple[str, str], list[int]] | None = None,
    save_configs: bool = True,
) -> ExperimentRepository:
    """Build a populated ExperimentRepository for testing."""
    repo = ExperimentRepository(tmp_path)
    experiments = experiments or []
    runs = runs or {}
    episodes = episodes or {}

    for exp_id in experiments:
        repo.create_experiment_dir(exp_id)
        if save_configs:
            repo.save_experiment_config(exp_id, _make_experiment_config())

    for exp_id, run_ids in runs.items():
        for run_id in run_ids:
            repo.create_run_dir(exp_id, run_id)
            if save_configs:
                repo.save_run_config(exp_id, run_id, _make_run_config())

    for (exp_id, run_id), indices in episodes.items():
        for idx in indices:
            repo.save_episode_trace(
                exp_id, run_id, idx, _make_episode(),
            )

    return repo


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDiscovery:

    def test_list_experiments(self, tmp_path: Path) -> None:
        repo = _setup_repo(
            tmp_path, experiments=["exp_a", "exp_b"],
        )
        svc = ReplayAccessService(repo)
        assert svc.list_experiments() == ("exp_a", "exp_b")

    def test_list_runs(self, tmp_path: Path) -> None:
        repo = _setup_repo(
            tmp_path,
            experiments=["exp_a"],
            runs={"exp_a": ["run_1", "run_2"]},
        )
        svc = ReplayAccessService(repo)
        assert svc.list_runs("exp_a") == ("run_1", "run_2")

    def test_list_episode_indices(self, tmp_path: Path) -> None:
        repo = _setup_repo(
            tmp_path,
            experiments=["exp_a"],
            runs={"exp_a": ["run_1"]},
            episodes={("exp_a", "run_1"): [0, 1, 2]},
        )
        svc = ReplayAccessService(repo)
        assert svc.list_episode_indices("exp_a", "run_1") == (0, 1, 2)


class TestNotFoundErrors:

    def test_experiment_not_found(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        svc = ReplayAccessService(repo)
        with pytest.raises(ExperimentNotFoundError):
            svc.list_runs("nonexistent")

    def test_run_not_found(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path, experiments=["exp_a"])
        svc = ReplayAccessService(repo)
        with pytest.raises(RunNotFoundError):
            svc.list_episode_indices("exp_a", "nonexistent")

    def test_episode_not_found(self, tmp_path: Path) -> None:
        repo = _setup_repo(
            tmp_path,
            experiments=["exp_a"],
            runs={"exp_a": ["run_1"]},
        )
        svc = ReplayAccessService(repo)
        with pytest.raises(EpisodeNotFoundError):
            svc.load_episode_trace("exp_a", "run_1", 99)


class TestLoading:

    def test_load_episode_trace(self, tmp_path: Path) -> None:
        repo = _setup_repo(
            tmp_path,
            experiments=["exp_a"],
            runs={"exp_a": ["run_1"]},
            episodes={("exp_a", "run_1"): [0]},
        )
        svc = ReplayAccessService(repo)
        trace = svc.load_episode_trace("exp_a", "run_1", 0)
        assert isinstance(trace, BaseEpisodeTrace)
        assert trace.total_steps == 3

    def test_load_delta_episode_trace(self, tmp_path: Path) -> None:
        repo = _setup_repo(
            tmp_path,
            experiments=["exp_a"],
            runs={"exp_a": ["run_1"]},
        )
        initial = _make_snapshot()
        delta_episode = DeltaEpisodeTrace(
            system_type="test",
            initial_world=initial,
            steps=(
                DeltaStepTrace(
                    timestep=0,
                    action="stay",
                    regen_delta=WorldDelta(agent_position=Position(x=0, y=0)),
                    action_delta=WorldDelta(agent_position=Position(x=0, y=0)),
                    agent_position_before=Position(x=0, y=0),
                    agent_position_after=Position(x=0, y=0),
                    vitality_before=1.0,
                    vitality_after=0.9,
                    terminated=False,
                ),
            ),
            total_steps=1,
            termination_reason="max_steps",
            final_vitality=0.9,
            final_position=Position(x=0, y=0),
        )
        repo.save_delta_episode_trace("exp_a", "run_1", 0, delta_episode)
        svc = ReplayAccessService(repo)
        trace = svc.load_episode_trace("exp_a", "run_1", 0)
        assert isinstance(trace, BaseEpisodeTrace)
        assert trace.total_steps == 1

    def test_load_replay_episode_valid(self, tmp_path: Path) -> None:
        repo = _setup_repo(
            tmp_path,
            experiments=["exp_a"],
            runs={"exp_a": ["run_1"]},
            episodes={("exp_a", "run_1"): [0]},
        )
        svc = ReplayAccessService(repo)
        handle = svc.load_replay_episode("exp_a", "run_1", 0)
        assert handle.validation.valid is True
        assert handle.episode_index == 0
        assert handle.experiment_id == "exp_a"
        assert handle.run_id == "run_1"

    def test_load_replay_episode_invalid(self, tmp_path: Path) -> None:
        # Create an episode with 0 steps
        repo = _setup_repo(
            tmp_path,
            experiments=["exp_a"],
            runs={"exp_a": ["run_1"]},
        )
        empty_episode = BaseEpisodeTrace(
            system_type="test",
            steps=(),
            total_steps=0,
            termination_reason="empty",
            final_vitality=1.0,
            final_position=Position(x=0, y=0),
        )
        repo.save_episode_trace("exp_a", "run_1", 0, empty_episode)
        svc = ReplayAccessService(repo)
        with pytest.raises(ReplayContractViolation):
            svc.load_replay_episode("exp_a", "run_1", 0)

    def test_validate_episode_no_raise(self, tmp_path: Path) -> None:
        repo = _setup_repo(
            tmp_path,
            experiments=["exp_a"],
            runs={"exp_a": ["run_1"]},
        )
        empty_episode = BaseEpisodeTrace(
            system_type="test",
            steps=(),
            total_steps=0,
            termination_reason="empty",
            final_vitality=1.0,
            final_position=Position(x=0, y=0),
        )
        repo.save_episode_trace("exp_a", "run_1", 0, empty_episode)
        svc = ReplayAccessService(repo)
        result = svc.validate_episode("exp_a", "run_1", 0)
        assert result.valid is False
        assert len(result.violations) > 0


class TestHandles:

    def test_get_experiment_handle(self, tmp_path: Path) -> None:
        repo = _setup_repo(
            tmp_path,
            experiments=["exp_a"],
            runs={"exp_a": ["run_1"]},
        )
        svc = ReplayAccessService(repo)
        handle = svc.get_experiment_handle("exp_a")
        assert handle.experiment_id == "exp_a"
        assert handle.available_runs == ("run_1",)
        assert handle.experiment_config.system_type == "test"

    def test_get_run_handle(self, tmp_path: Path) -> None:
        repo = _setup_repo(
            tmp_path,
            experiments=["exp_a"],
            runs={"exp_a": ["run_1"]},
            episodes={("exp_a", "run_1"): [0, 1]},
        )
        svc = ReplayAccessService(repo)
        handle = svc.get_run_handle("exp_a", "run_1")
        assert handle.experiment_id == "exp_a"
        assert handle.run_id == "run_1"
        assert handle.available_episodes == (0, 1)
        assert handle.run_config.system_type == "test"


class TestMalformedArtifact:

    def test_malformed_artifact_error(self, tmp_path: Path) -> None:
        repo = _setup_repo(
            tmp_path,
            experiments=["exp_a"],
            runs={"exp_a": ["run_1"]},
        )
        # Write garbage to episode file
        episode_path = repo.episode_path("exp_a", "run_1", 0)
        episode_path.write_text("{invalid json content}")
        svc = ReplayAccessService(repo)
        with pytest.raises(MalformedArtifactError):
            svc.load_episode_trace("exp_a", "run_1", 0)
