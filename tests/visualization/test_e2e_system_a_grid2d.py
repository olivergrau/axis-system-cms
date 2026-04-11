"""Tests for WP-V.5.3: End-to-End System A + Grid2D.

Full pipeline from experiment execution through visualization frame building.
"""

from __future__ import annotations

import pytest

from tests.visualization.e2e_helpers import (
    build_frame,
    load_episode_through_pipeline,
    run_and_persist_experiment,
)


@pytest.fixture(scope="module")
def system_a_grid2d(tmp_path_factory):
    """Run a System A + Grid2D experiment and load through pipeline."""
    tmp_path = tmp_path_factory.mktemp("e2e_a_grid2d")
    repo, eid = run_and_persist_experiment(
        tmp_path, "system_a", world_type="grid_2d", max_steps=10, seed=42,
    )
    handle, wadapter, sadapter = load_episode_through_pipeline(repo, eid)
    return repo, eid, handle, wadapter, sadapter


class TestSystemAGrid2DPipeline:

    def test_experiment_runs(self, system_a_grid2d) -> None:
        _, _, handle, _, _ = system_a_grid2d
        assert handle.validation.valid is True

    def test_system_type(self, system_a_grid2d) -> None:
        _, _, handle, _, _ = system_a_grid2d
        assert handle.episode_trace.system_type == "system_a"

    def test_world_type(self, system_a_grid2d) -> None:
        _, _, handle, _, _ = system_a_grid2d
        assert handle.episode_trace.world_type == "grid_2d"

    def test_step_count(self, system_a_grid2d) -> None:
        _, _, handle, _, _ = system_a_grid2d
        assert handle.validation.total_steps <= 10
        assert handle.validation.total_steps > 0

    def test_grid_dimensions(self, system_a_grid2d) -> None:
        _, _, handle, _, _ = system_a_grid2d
        assert handle.validation.grid_width == 5
        assert handle.validation.grid_height == 5

    def test_step_traces_have_system_data(self, system_a_grid2d) -> None:
        _, _, handle, _, _ = system_a_grid2d
        for step in handle.episode_trace.steps:
            assert "decision_data" in step.system_data
            assert "trace_data" in step.system_data

    def test_adapter_types(self, system_a_grid2d) -> None:
        _, _, _, wadapter, sadapter = system_a_grid2d
        assert type(wadapter).__name__ == "Grid2DWorldVisualizationAdapter"
        assert type(sadapter).__name__ == "SystemAVisualizationAdapter"

    def test_three_phases(self, system_a_grid2d) -> None:
        _, _, _, _, sadapter = system_a_grid2d
        assert len(sadapter.phase_names()) == 3


class TestSystemAGrid2DFrameBuilding:

    def test_build_step_0(self, system_a_grid2d) -> None:
        _, _, handle, wadapter, sadapter = system_a_grid2d
        frame = build_frame(handle, wadapter, sadapter, step_index=0)
        assert frame is not None

    def test_grid_matches_dimensions(self, system_a_grid2d) -> None:
        _, _, handle, wadapter, sadapter = system_a_grid2d
        frame = build_frame(handle, wadapter, sadapter)
        assert frame.grid.width == 5
        assert frame.grid.height == 5
        assert len(frame.grid.cells) == 25

    def test_five_analysis_sections(self, system_a_grid2d) -> None:
        _, _, handle, wadapter, sadapter = system_a_grid2d
        frame = build_frame(handle, wadapter, sadapter)
        assert len(frame.analysis_sections) == 6

    def test_energy_format(self, system_a_grid2d) -> None:
        _, _, handle, wadapter, sadapter = system_a_grid2d
        frame = build_frame(handle, wadapter, sadapter)
        assert "/" in frame.status.vitality_display

    def test_no_topology_indicators(self, system_a_grid2d) -> None:
        _, _, handle, wadapter, sadapter = system_a_grid2d
        frame = build_frame(handle, wadapter, sadapter)
        assert len(frame.topology_indicators) == 0

    def test_no_world_metadata(self, system_a_grid2d) -> None:
        _, _, handle, wadapter, sadapter = system_a_grid2d
        frame = build_frame(handle, wadapter, sadapter)
        assert len(frame.world_metadata_sections) == 0

    def test_world_info_none(self, system_a_grid2d) -> None:
        _, _, handle, wadapter, sadapter = system_a_grid2d
        frame = build_frame(handle, wadapter, sadapter)
        assert frame.status.world_info is None


class TestSystemAGrid2DMultiStep:

    def test_all_steps_build(self, system_a_grid2d) -> None:
        _, _, handle, wadapter, sadapter = system_a_grid2d
        for i in range(handle.validation.total_steps):
            frame = build_frame(handle, wadapter, sadapter, step_index=i)
            assert frame is not None

    def test_vitality_changes(self, system_a_grid2d) -> None:
        _, _, handle, wadapter, sadapter = system_a_grid2d
        vitalities = []
        for i in range(min(handle.validation.total_steps, 5)):
            frame = build_frame(handle, wadapter, sadapter, step_index=i)
            vitalities.append(frame.status.vitality_display)
        # Energy should change over steps (not all identical)
        assert len(set(vitalities)) > 1

    def test_agent_changes(self, system_a_grid2d) -> None:
        _, _, handle, wadapter, sadapter = system_a_grid2d
        positions = []
        for i in range(handle.validation.total_steps):
            frame = build_frame(handle, wadapter, sadapter, step_index=i)
            positions.append((frame.agent.row, frame.agent.col))
        # At least one position change over the episode
        assert len(set(positions)) > 1

    def test_analysis_rows_non_empty(self, system_a_grid2d) -> None:
        _, _, handle, wadapter, sadapter = system_a_grid2d
        frame = build_frame(handle, wadapter, sadapter)
        for section in frame.analysis_sections:
            assert len(section.rows) > 0

    def test_boundary_phases_build(self, system_a_grid2d) -> None:
        _, _, handle, wadapter, sadapter = system_a_grid2d
        # Phase 0 (BEFORE) and phase 2 (AFTER_ACTION) are always available.
        # Phase 1 (AFTER_REGEN) requires intermediate_snapshots, which the
        # runner does not record.
        for phase in [0, 2]:
            frame = build_frame(
                handle, wadapter, sadapter, step_index=0, phase_index=phase)
            assert frame is not None
