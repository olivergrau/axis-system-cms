"""Tests for WP-V.5.3: End-to-End System B + Toroidal."""

from __future__ import annotations

import pytest

from tests.visualization.e2e_helpers import (
    build_frame,
    load_episode_through_pipeline,
    run_and_persist_experiment,
)


@pytest.fixture(scope="module")
def system_b_toroidal(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("e2e_b_toro")
    repo, eid = run_and_persist_experiment(
        tmp_path, "system_b", world_type="toroidal", max_steps=10, seed=42,
    )
    handle, wadapter, sadapter = load_episode_through_pipeline(repo, eid)
    return handle, wadapter, sadapter


class TestSystemBToroidal:

    def test_experiment_runs(self, system_b_toroidal) -> None:
        handle, _, _ = system_b_toroidal
        assert handle.validation.valid is True

    def test_world_type(self, system_b_toroidal) -> None:
        handle, _, _ = system_b_toroidal
        assert handle.episode_trace.world_type == "toroidal"

    def test_adapter_type(self, system_b_toroidal) -> None:
        _, wadapter, _ = system_b_toroidal
        assert type(wadapter).__name__ == "ToroidalWorldVisualizationAdapter"

    def test_topology_indicators(self, system_b_toroidal) -> None:
        handle, wadapter, sadapter = system_b_toroidal
        frame = build_frame(handle, wadapter, sadapter)
        assert len(frame.topology_indicators) == 4

    def test_world_info(self, system_b_toroidal) -> None:
        handle, wadapter, sadapter = system_b_toroidal
        frame = build_frame(handle, wadapter, sadapter)
        assert frame.status.world_info is not None
        assert "Toroidal" in frame.status.world_info

    def test_two_phases(self, system_b_toroidal) -> None:
        _, _, sadapter = system_b_toroidal
        assert len(sadapter.phase_names()) == 2

    def test_multi_step(self, system_b_toroidal) -> None:
        handle, wadapter, sadapter = system_b_toroidal
        for i in range(min(handle.validation.total_steps, 5)):
            frame = build_frame(handle, wadapter, sadapter, step_index=i)
            assert frame is not None
