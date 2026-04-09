"""Shared E2E helpers for WP-V.5.3 end-to-end validation tests.

Provides functions to run real experiments, persist them, and load
episodes through the full visualization pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from axis.framework.config import (
    ExecutionConfig,
    FrameworkConfig,
    GeneralConfig,
    LoggingConfig,
)
from axis.framework.persistence import ExperimentRepository
from axis.framework.registry import create_system
from axis.framework.run import RunConfig, RunSummary
from axis.framework.runner import run_episode, setup_episode
from axis.sdk.position import Position
from axis.sdk.world_types import BaseWorldConfig
from axis.visualization.launch import _import_adapter_modules
from axis.visualization.registry import (
    resolve_system_adapter,
    resolve_world_adapter,
)
from axis.visualization.replay_access import ReplayAccessService
from axis.visualization.replay_models import ReplayEpisodeHandle
from axis.visualization.snapshot_resolver import SnapshotResolver
from axis.visualization.view_model_builder import ViewModelBuilder
from axis.visualization.view_models import ViewerFrameViewModel
from axis.visualization.viewer_state import create_initial_state

from tests.v02.builders.system_config_builder import SystemAConfigBuilder


# ---------------------------------------------------------------------------
# System config helpers
# ---------------------------------------------------------------------------


def system_a_config() -> dict[str, Any]:
    """Return a System A config dict suitable for experiment creation."""
    return SystemAConfigBuilder().build()


def system_b_config() -> dict[str, Any]:
    """Return a System B config dict suitable for experiment creation."""
    return {
        "agent": {
            "initial_energy": 100.0,
            "max_energy": 100.0,
        },
        "policy": {
            "selection_mode": "sample",
            "temperature": 1.0,
            "scan_bonus": 2.0,
        },
        "transition": {
            "move_cost": 1.0,
            "scan_cost": 0.5,
            "stay_cost": 0.5,
        },
    }


# ---------------------------------------------------------------------------
# Experiment execution and persistence
# ---------------------------------------------------------------------------


def run_and_persist_experiment(
    tmp_path: Path,
    system_type: str,
    *,
    world_type: str = "grid_2d",
    max_steps: int = 10,
    num_episodes: int = 1,
    seed: int = 42,
    grid_width: int = 5,
    grid_height: int = 5,
    system_config: dict[str, Any] | None = None,
    world_config_extras: dict[str, Any] | None = None,
) -> tuple[ExperimentRepository, str]:
    """Run an experiment and persist it to tmp_path.

    Returns (repo, experiment_id).
    """
    # Build configs
    if system_config is None:
        if system_type == "system_a":
            system_config = system_a_config()
        elif system_type == "system_b":
            system_config = system_b_config()
        else:
            system_config = {}

    wc_dict: dict[str, Any] = {
        "world_type": world_type,
        "grid_width": grid_width,
        "grid_height": grid_height,
    }
    if world_config_extras:
        wc_dict.update(world_config_extras)

    world_config = BaseWorldConfig(**wc_dict)

    framework_config = FrameworkConfig(
        general=GeneralConfig(seed=seed),
        execution=ExecutionConfig(max_steps=max_steps),
        world=world_config,
        logging=LoggingConfig(enabled=False),
    )

    # Set up repository
    repo = ExperimentRepository(tmp_path / "repo")
    experiment_id = "e2e_test"
    repo.create_experiment_dir(experiment_id)
    run_id = "run-0000"
    repo.create_run_dir(experiment_id, run_id)

    # Create system
    system = create_system(system_type, system_config)

    # Run episodes
    for ep_idx in range(num_episodes):
        ep_seed = seed + ep_idx
        world, registry = setup_episode(
            system, world_config,
            Position(x=0, y=0), seed=ep_seed,
        )
        episode_trace = run_episode(
            system, world, registry,
            max_steps=max_steps, seed=ep_seed,
            world_config=world_config,
        )
        repo.save_episode_trace(
            experiment_id, run_id, ep_idx, episode_trace,
        )

    # Save run config
    run_config = RunConfig(
        system_type=system_type,
        system_config=system_config,
        framework_config=framework_config,
        num_episodes=num_episodes,
        base_seed=seed,
        run_id=run_id,
    )
    repo.save_run_config(experiment_id, run_id, run_config)

    return repo, experiment_id


# ---------------------------------------------------------------------------
# Pipeline loading
# ---------------------------------------------------------------------------


def import_all_adapters() -> None:
    """Ensure all adapter visualization modules are registered.

    Uses direct registration as a fallback when the import-time
    side-effect has already fired but registries were cleared.
    """
    from axis.visualization.registry import (
        register_system_visualization,
        register_world_visualization,
        registered_system_visualizations,
        registered_world_visualizations,
    )

    _import_adapter_modules()

    # Re-register if registries were cleared after initial import
    world_registered = registered_world_visualizations()
    if "grid_2d" not in world_registered:
        from axis.world.grid_2d.visualization import _grid_2d_vis_factory
        register_world_visualization("grid_2d", _grid_2d_vis_factory)
    if "toroidal" not in world_registered:
        from axis.world.toroidal.visualization import _toroidal_vis_factory
        register_world_visualization("toroidal", _toroidal_vis_factory)
    if "signal_landscape" not in world_registered:
        from axis.world.signal_landscape.visualization import (
            _signal_landscape_vis_factory,
        )
        register_world_visualization(
            "signal_landscape", _signal_landscape_vis_factory)

    system_registered = registered_system_visualizations()
    if "system_a" not in system_registered:
        from axis.systems.system_a.visualization import _system_a_vis_factory
        register_system_visualization("system_a", _system_a_vis_factory)
    if "system_b" not in system_registered:
        from axis.systems.system_b.visualization import _system_b_vis_factory
        register_system_visualization("system_b", _system_b_vis_factory)


def load_episode_through_pipeline(
    repo: ExperimentRepository,
    experiment_id: str,
    run_id: str = "run-0000",
    episode_index: int = 0,
) -> tuple[ReplayEpisodeHandle, Any, Any]:
    """Load an episode through the replay pipeline.

    Returns (episode_handle, world_adapter, system_adapter).
    """
    import_all_adapters()
    access = ReplayAccessService(repo)
    handle = access.load_replay_episode(
        experiment_id, run_id, episode_index,
    )

    episode = handle.episode_trace
    system_type = episode.system_type
    world_type = getattr(episode, "world_type", "grid_2d")
    world_config = getattr(episode, "world_config", {})

    world_adapter = resolve_world_adapter(world_type, world_config)
    system_adapter = resolve_system_adapter(system_type)

    return handle, world_adapter, system_adapter


def build_frame(
    handle: ReplayEpisodeHandle,
    world_adapter: Any,
    system_adapter: Any,
    step_index: int = 0,
    phase_index: int = 0,
) -> ViewerFrameViewModel:
    """Build a ViewerFrameViewModel from a loaded episode handle."""
    num_phases = len(system_adapter.phase_names())
    state = create_initial_state(handle, num_phases)

    if step_index > 0 or phase_index > 0:
        from axis.visualization.snapshot_models import ReplayCoordinate
        from axis.visualization.viewer_state_transitions import seek
        state = seek(state, ReplayCoordinate(
            step_index=step_index, phase_index=phase_index))

    builder = ViewModelBuilder(
        SnapshotResolver(), world_adapter, system_adapter)
    return builder.build(state)
