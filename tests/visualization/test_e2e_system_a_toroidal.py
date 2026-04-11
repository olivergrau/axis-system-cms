"""Tests for WP-V.5.3: End-to-End System A + Toroidal."""

from __future__ import annotations

import pytest

from tests.visualization.e2e_helpers import (
    build_frame,
    load_episode_through_pipeline,
    run_and_persist_experiment,
)


@pytest.fixture(scope="module")
def system_a_toroidal(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("e2e_a_toro")
    repo, eid = run_and_persist_experiment(
        tmp_path, "system_a", world_type="toroidal", max_steps=10, seed=42,
    )
    handle, wadapter, sadapter = load_episode_through_pipeline(repo, eid)
    return handle, wadapter, sadapter


class TestSystemAToroidal:

    def test_experiment_runs(self, system_a_toroidal) -> None:
        handle, _, _ = system_a_toroidal
        assert handle.validation.valid is True

    def test_world_type(self, system_a_toroidal) -> None:
        handle, _, _ = system_a_toroidal
        assert handle.episode_trace.world_type == "toroidal"

    def test_adapter_type(self, system_a_toroidal) -> None:
        _, wadapter, _ = system_a_toroidal
        assert type(wadapter).__name__ == "ToroidalWorldVisualizationAdapter"

    def test_topology_indicators(self, system_a_toroidal) -> None:
        handle, wadapter, sadapter = system_a_toroidal
        frame = build_frame(handle, wadapter, sadapter)
        assert len(frame.topology_indicators) == 4

    def test_wrap_edges_present(self, system_a_toroidal) -> None:
        handle, wadapter, sadapter = system_a_toroidal
        frame = build_frame(handle, wadapter, sadapter)
        edges = {ind.data["edge"] for ind in frame.topology_indicators}
        assert edges == {"left", "right", "top", "bottom"}

    def test_world_info(self, system_a_toroidal) -> None:
        handle, wadapter, sadapter = system_a_toroidal
        frame = build_frame(handle, wadapter, sadapter)
        assert frame.status.world_info is not None
        assert "Toroidal" in frame.status.world_info

    def test_five_analysis_sections(self, system_a_toroidal) -> None:
        handle, wadapter, sadapter = system_a_toroidal
        frame = build_frame(handle, wadapter, sadapter)
        assert len(frame.analysis_sections) == 6

    def test_boundary_phases_build(self, system_a_toroidal) -> None:
        handle, wadapter, sadapter = system_a_toroidal
        # Phase 0 (BEFORE) and phase 2 (AFTER_ACTION) always available;
        # phase 1 (AFTER_REGEN) requires intermediate_snapshots.
        for phase in [0, 2]:
            frame = build_frame(
                handle, wadapter, sadapter, step_index=0, phase_index=phase)
            assert frame is not None

    def test_multi_step(self, system_a_toroidal) -> None:
        handle, wadapter, sadapter = system_a_toroidal
        for i in range(min(handle.validation.total_steps, 5)):
            frame = build_frame(handle, wadapter, sadapter, step_index=i)
            assert frame is not None
