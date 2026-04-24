"""Tests for WP-V.4.4: Launch entry point."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from PySide6.QtWidgets import QApplication  # noqa: E402

from axis.visualization.launch import _import_adapter_modules  # noqa: E402


# ---------------------------------------------------------------------------
# QApplication fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


# ---------------------------------------------------------------------------
# Launch tests
# ---------------------------------------------------------------------------


class TestLaunch:

    def test_import_adapter_modules_no_crash(self, qapp) -> None:
        """Importing adapter modules should not crash even if not all are available."""
        _import_adapter_modules()

    def test_launch_visualization_invalid_step(self, qapp, tmp_path) -> None:
        """start_step out of bounds should raise StepOutOfBoundsError."""
        from axis.framework.persistence import ExperimentRepository
        from axis.sdk.position import Position
        from axis.sdk.snapshot import WorldSnapshot
        from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
        from axis.sdk.world_types import CellView
        from axis.visualization.errors import StepOutOfBoundsError
        from axis.visualization.launch import launch_visualization

        # Set up a minimal repository with 1 experiment/run/episode
        repo = ExperimentRepository(tmp_path)
        exp_dir = tmp_path / "exp" / "runs" / "run" / "episodes"
        exp_dir.mkdir(parents=True)

        # Create a minimal episode trace file
        cell = CellView(cell_type="empty", resource_value=0.0)
        grid = ((cell,),)
        snap = WorldSnapshot(grid=grid, agent_position=Position(
            x=0, y=0), width=1, height=1)
        step = BaseStepTrace(
            timestep=0, action="stay",
            world_before=snap, world_after=snap,
            agent_position_before=Position(x=0, y=0),
            agent_position_after=Position(x=0, y=0),
            vitality_before=1.0, vitality_after=1.0,
            terminated=False,
        )
        episode = BaseEpisodeTrace(
            system_type="test", steps=(step,), total_steps=1,
            termination_reason="max_steps", final_vitality=1.0,
            final_position=Position(x=0, y=0),
        )

        # Save episode
        import json
        episode_file = exp_dir / "episode_0000.json"
        episode_file.write_text(episode.model_dump_json())

        with pytest.raises(StepOutOfBoundsError):
            launch_visualization(
                repo, "exp", "run", 0, start_step=99,
            )

    def test_launch_visualization_not_found(self, qapp, tmp_path) -> None:
        """Invalid experiment should raise ExperimentNotFoundError or EpisodeNotFoundError."""
        from axis.framework.persistence import ExperimentRepository
        from axis.visualization.errors import ReplayError
        from axis.visualization.launch import launch_visualization

        repo = ExperimentRepository(tmp_path)

        with pytest.raises(ReplayError):
            launch_visualization(repo, "nonexistent", "run", 0)

    def test_resolve_initial_window_size_uses_width_percent(self, qapp) -> None:
        from axis.visualization.launch import _resolve_initial_window_size

        width, height = _resolve_initial_window_size(qapp, width_percent=50)
        available = qapp.primaryScreen().availableGeometry()
        assert width == int(available.width() * 0.5)
        assert height <= int(available.height() * 0.9)

    def test_launch_visualization_rejects_light_trace_mode(self, qapp, tmp_path) -> None:
        from axis.framework.persistence import (
            ExperimentMetadata,
            ExperimentRepository,
            ExperimentStatus,
            RunMetadata,
            RunStatus,
        )
        from axis.visualization.launch import launch_visualization

        repo = ExperimentRepository(tmp_path)
        repo.create_experiment_dir("exp")
        repo.save_experiment_metadata(
            "exp",
            ExperimentMetadata(
                experiment_id="exp",
                created_at="2026-04-24T00:00:00Z",
                experiment_type="single_run",
                system_type="system_a",
                output_form="point",
                trace_mode="light",
                primary_run_id="run",
            ),
        )
        repo.save_experiment_status("exp", ExperimentStatus.COMPLETED)
        repo.create_run_dir("exp", "run")
        repo.save_run_metadata(
            "exp",
            "run",
            RunMetadata(
                run_id="run",
                experiment_id="exp",
                created_at="2026-04-24T00:00:00Z",
                trace_mode="light",
            ),
        )
        repo.save_run_status("exp", "run", RunStatus.COMPLETED)

        with pytest.raises(ValueError, match="light trace mode"):
            launch_visualization(repo, "exp", "run", 0)
