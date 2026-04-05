"""Shared fixtures for visualization tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from axis_system_a import SimulationConfig
from axis_system_a.experiment import (
    ExperimentConfig,
    ExperimentType,
    compute_experiment_summary,
)
from axis_system_a.repository import (
    ExperimentMetadata,
    ExperimentRepository,
    RunMetadata,
)
from axis_system_a.results import EpisodeResult
from axis_system_a.run import RunConfig, RunResult, compute_run_summary
from axis_system_a.runner import run_episode
from axis_system_a.types import Position
from axis_system_a.visualization.replay_access import ReplayAccessService
from axis_system_a.visualization.replay_models import ReplayEpisodeHandle
from axis_system_a.visualization.snapshot_resolver import SnapshotResolver
from axis_system_a.visualization.viewer_state import (
    ViewerState,
    create_initial_state,
)
from axis_system_a.world import create_world
from tests.fixtures.scenario_fixtures import make_config


def _small_config() -> SimulationConfig:
    return make_config(overrides={
        "world": {"grid_width": 3, "grid_height": 3},
        "execution": {"max_steps": 5},
        "logging": {"enabled": False},
    })


def _make_episode() -> EpisodeResult:
    sim = _small_config()
    world = create_world(sim.world, Position(x=0, y=0))
    return run_episode(sim, world)


@pytest.fixture
def small_config() -> SimulationConfig:
    """3x3 grid, 5 steps, logging off."""
    return _small_config()


@pytest.fixture
def small_episode() -> EpisodeResult:
    """A real episode from a 3x3 grid / 5-step config."""
    return _make_episode()


@pytest.fixture
def populated_repo(tmp_path: Path) -> ExperimentRepository:
    """Repository with one experiment, one run, and one persisted episode."""
    repo = ExperimentRepository(tmp_path)
    exp_id = "test-exp"
    run_id = "run-0000"

    repo.create_experiment_dir(exp_id)
    repo.create_run_dir(exp_id, run_id)

    sim = _small_config()
    exp_config = ExperimentConfig(
        experiment_type=ExperimentType.SINGLE_RUN,
        baseline=sim,
        num_episodes_per_run=1,
        base_seed=42,
    )
    repo.save_experiment_config(exp_id, exp_config)

    exp_meta = ExperimentMetadata(
        experiment_id=exp_id,
        created_at="2025-01-01T00:00:00",
        experiment_type="single_run",
        name="test-exp",
    )
    repo.save_experiment_metadata(exp_id, exp_meta)

    run_config = RunConfig(
        simulation=sim,
        num_episodes=1,
        base_seed=42,
        run_id=run_id,
    )
    repo.save_run_config(exp_id, run_id, run_config)

    run_meta = RunMetadata(
        run_id=run_id,
        experiment_id=exp_id,
        created_at="2025-01-01T00:00:00",
        base_seed=42,
    )
    repo.save_run_metadata(exp_id, run_id, run_meta)

    episode = _make_episode()
    repo.save_episode_result(exp_id, run_id, 1, episode)

    summary = compute_run_summary((episode,))
    repo.save_run_summary(exp_id, run_id, summary)

    return repo


@pytest.fixture
def access_service(populated_repo: ExperimentRepository) -> ReplayAccessService:
    """ReplayAccessService over the populated repo."""
    return ReplayAccessService(populated_repo)


@pytest.fixture
def replay_episode_handle(
    access_service: ReplayAccessService,
) -> ReplayEpisodeHandle:
    """A validated ReplayEpisodeHandle from the populated repo."""
    return access_service.load_replay_episode("test-exp", "run-0000", 1)


@pytest.fixture
def snapshot_resolver() -> SnapshotResolver:
    """A fresh SnapshotResolver instance."""
    return SnapshotResolver()


@pytest.fixture
def initial_viewer_state(
    replay_episode_handle: ReplayEpisodeHandle,
) -> ViewerState:
    """A ViewerState at (0, BEFORE), STOPPED, no selection."""
    return create_initial_state(replay_episode_handle)
