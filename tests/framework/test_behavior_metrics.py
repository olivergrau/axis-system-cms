"""Tests for framework-standard behavioral metrics."""

from __future__ import annotations

from pathlib import Path

from axis.framework.metrics import (
    MetricSummaryStats,
    compute_run_behavior_metrics,
)
from axis.framework.metrics.standard import (
    aggregate_run_behavior_metrics,
    compute_episode_behavior_metrics,
)
from axis.framework.persistence import (
    ExperimentMetadata,
    ExperimentRepository,
    RunMetadata,
)
from axis.framework.run import RunConfig, RunExecutor
from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import CellView
from tests.builders.config_builder import FrameworkConfigBuilder
from tests.builders.system_config_builder import SystemAConfigBuilder


def _snapshot(position: Position) -> WorldSnapshot:
    grid = (
        (
            CellView(cell_type="empty", resource_value=0.0),
            CellView(cell_type="empty", resource_value=0.0),
        ),
        (
            CellView(cell_type="empty", resource_value=0.0),
            CellView(cell_type="empty", resource_value=0.0),
        ),
    )
    return WorldSnapshot(
        grid=grid,
        agent_position=position,
        width=2,
        height=2,
    )


def _step(
    timestep: int,
    *,
    action: str,
    before: Position,
    after: Position,
    vitality_before: float,
    vitality_after: float,
    current_resource: float,
    energy_gain: float,
    action_cost: float,
    probabilities: tuple[float, ...],
) -> BaseStepTrace:
    return BaseStepTrace(
        timestep=timestep,
        action=action,
        world_before=_snapshot(before),
        world_after=_snapshot(after),
        agent_position_before=before,
        agent_position_after=after,
        vitality_before=vitality_before,
        vitality_after=vitality_after,
        terminated=False,
        termination_reason=None,
        system_data={
            "decision_data": {
                "observation": {
                    "current": {
                        "traversability": 1.0,
                        "resource": current_resource,
                    },
                },
                "policy": {
                    "probabilities": probabilities,
                },
            },
            "trace_data": {
                "energy_gain": energy_gain,
                "action_cost": action_cost,
            },
        },
        world_data={},
    )


def _handcrafted_trace() -> BaseEpisodeTrace:
    pos_start = Position(x=1, y=1)
    pos_up = Position(x=1, y=0)
    steps = (
        _step(
            0,
            action="consume",
            before=pos_start,
            after=pos_start,
            vitality_before=1.0,
            vitality_after=0.9,
            current_resource=1.0,
            energy_gain=5.0,
            action_cost=1.0,
            probabilities=(0.1, 0.1, 0.1, 0.1, 0.5, 0.1),
        ),
        _step(
            1,
            action="up",
            before=pos_start,
            after=pos_up,
            vitality_before=0.9,
            vitality_after=0.8,
            current_resource=0.0,
            energy_gain=0.0,
            action_cost=1.0,
            probabilities=(0.6, 0.1, 0.1, 0.1, 0.05, 0.05),
        ),
        _step(
            2,
            action="up",
            before=pos_up,
            after=pos_up,
            vitality_before=0.8,
            vitality_after=0.7,
            current_resource=0.0,
            energy_gain=0.0,
            action_cost=1.0,
            probabilities=(0.7, 0.05, 0.05, 0.05, 0.1, 0.05),
        ),
        _step(
            3,
            action="consume",
            before=pos_up,
            after=pos_up,
            vitality_before=0.7,
            vitality_after=0.6,
            current_resource=0.0,
            energy_gain=0.0,
            action_cost=1.0,
            probabilities=(0.1, 0.1, 0.1, 0.1, 0.4, 0.2),
        ),
    )
    return BaseEpisodeTrace(
        system_type="system_a",
        steps=steps,
        total_steps=4,
        termination_reason="max_steps_reached",
        final_vitality=0.6,
        final_position=pos_up,
        world_type="grid_2d",
        world_config={"grid_width": 2, "grid_height": 2},
    )


class TestEpisodeBehaviorMetrics:
    def test_compute_episode_behavior_metrics(self) -> None:
        metrics = compute_episode_behavior_metrics(_handcrafted_trace())
        assert metrics.total_steps == 4
        assert metrics.final_vitality == 0.6
        assert metrics.died is False
        assert metrics.resource_gain_per_step == 1.25
        assert metrics.net_energy_efficiency == 1.25
        assert metrics.successful_consume_rate == 0.5
        assert metrics.consume_on_empty_rate == 0.5
        assert metrics.failed_movement_rate == 0.5
        assert metrics.action_inertia == 1 / 3
        assert metrics.policy_sharpness == 0.55
        assert metrics.unique_cells_visited == 2.0
        assert metrics.coverage_efficiency == 0.5
        assert metrics.revisit_rate == 0.5


class TestRunBehaviorMetricsAggregation:
    def test_aggregate_run_behavior_metrics(self) -> None:
        episode = compute_episode_behavior_metrics(_handcrafted_trace())
        aggregated = aggregate_run_behavior_metrics((episode, episode))
        assert aggregated.mean_steps == 4.0
        assert aggregated.death_rate == 0.0
        assert aggregated.mean_final_vitality == 0.6
        assert aggregated.resource_gain_per_step == MetricSummaryStats(
            mean=1.25, std=0.0, min=1.25, max=1.25, n=2,
        )


class TestBehaviorMetricsParity:
    def test_full_and_delta_produce_equal_metrics(self, tmp_path: Path) -> None:
        repo = ExperimentRepository(tmp_path)

        def _store_run(run_id: str, trace_mode: str) -> None:
            repo.create_run_dir("exp", run_id)
            framework_config = (
                FrameworkConfigBuilder()
                .with_max_steps(12)
                .with_trace_mode(trace_mode)
                .build()
            )
            result = RunExecutor().execute(
                RunConfig(
                    system_type="system_a",
                    system_config=SystemAConfigBuilder().build(),
                    framework_config=framework_config,
                    num_episodes=2,
                    base_seed=42,
                    run_id=run_id,
                ),
            )
            repo.save_run_result("exp", run_id, result, overwrite=True)
            repo.save_run_metadata(
                "exp",
                run_id,
                RunMetadata(
                    run_id=run_id,
                    experiment_id="exp",
                    created_at="now",
                    trace_mode=trace_mode,
                ),
            )
            if trace_mode == "delta":
                for i, trace in enumerate(result.episode_traces, start=1):
                    repo.save_delta_episode_trace("exp", run_id, i, trace)
            else:
                for i, trace in enumerate(result.episode_traces, start=1):
                    repo.save_episode_trace("exp", run_id, i, trace)

        repo.create_experiment_dir("exp")
        repo.save_experiment_metadata(
            "exp",
            ExperimentMetadata(
                experiment_id="exp",
                created_at="now",
                experiment_type="single_run",
                system_type="system_a",
            ),
        )

        _store_run("run-full", "full")
        _store_run("run-delta", "delta")

        full_metrics = compute_run_behavior_metrics(repo, "exp", "run-full")
        delta_metrics = compute_run_behavior_metrics(repo, "exp", "run-delta")

        assert full_metrics.standard_metrics == delta_metrics.standard_metrics
