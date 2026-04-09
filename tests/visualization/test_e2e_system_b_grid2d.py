"""Tests for WP-V.5.3: End-to-End System B + Grid2D."""

from __future__ import annotations

import pytest

from tests.visualization.e2e_helpers import (
    build_frame,
    load_episode_through_pipeline,
    run_and_persist_experiment,
)


@pytest.fixture(scope="module")
def system_b_grid2d(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("e2e_b_grid2d")
    repo, eid = run_and_persist_experiment(
        tmp_path, "system_b", world_type="grid_2d", max_steps=10, seed=42,
    )
    handle, wadapter, sadapter = load_episode_through_pipeline(repo, eid)
    return handle, wadapter, sadapter


class TestSystemBGrid2D:

    def test_experiment_runs(self, system_b_grid2d) -> None:
        handle, _, _ = system_b_grid2d
        assert handle.validation.valid is True

    def test_system_type(self, system_b_grid2d) -> None:
        handle, _, _ = system_b_grid2d
        assert handle.episode_trace.system_type == "system_b"

    def test_two_phases(self, system_b_grid2d) -> None:
        _, _, sadapter = system_b_grid2d
        assert len(sadapter.phase_names()) == 2

    def test_frame_builds(self, system_b_grid2d) -> None:
        handle, wadapter, sadapter = system_b_grid2d
        frame = build_frame(handle, wadapter, sadapter)
        assert frame is not None

    def test_five_analysis_sections(self, system_b_grid2d) -> None:
        handle, wadapter, sadapter = system_b_grid2d
        frame = build_frame(handle, wadapter, sadapter)
        assert len(frame.analysis_sections) == 5

    def test_no_topology(self, system_b_grid2d) -> None:
        handle, wadapter, sadapter = system_b_grid2d
        frame = build_frame(handle, wadapter, sadapter)
        assert len(frame.topology_indicators) == 0

    def test_both_phases_build(self, system_b_grid2d) -> None:
        handle, wadapter, sadapter = system_b_grid2d
        for phase in range(2):
            frame = build_frame(
                handle, wadapter, sadapter, step_index=0, phase_index=phase)
            assert frame is not None
