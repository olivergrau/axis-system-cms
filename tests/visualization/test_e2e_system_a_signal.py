"""Tests for WP-V.5.3: End-to-End System A + Signal Landscape."""

from __future__ import annotations

import pytest

from tests.visualization.e2e_helpers import (
    build_frame,
    load_episode_through_pipeline,
    run_and_persist_experiment,
)


@pytest.fixture(scope="module")
def system_a_signal(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("e2e_a_signal")
    repo, eid = run_and_persist_experiment(
        tmp_path, "system_a", world_type="signal_landscape",
        max_steps=10, seed=42, grid_width=10, grid_height=10,
        world_config_extras={"num_hotspots": 2},
    )
    handle, wadapter, sadapter = load_episode_through_pipeline(repo, eid)
    return handle, wadapter, sadapter


class TestSystemASignalLandscape:

    def test_experiment_runs(self, system_a_signal) -> None:
        handle, _, _ = system_a_signal
        assert handle.validation.valid is True

    def test_adapter_type(self, system_a_signal) -> None:
        _, wadapter, _ = system_a_signal
        assert type(
            wadapter).__name__ == "SignalLandscapeWorldVisualizationAdapter"

    def test_heatmap_colors(self, system_a_signal) -> None:
        _, wadapter, _ = system_a_signal
        cfg = wadapter.cell_color_config()
        assert cfg.resource_color_max == (255, 100, 0)

    def test_topology_indicators(self, system_a_signal) -> None:
        handle, wadapter, sadapter = system_a_signal
        frame = build_frame(handle, wadapter, sadapter)
        # Hotspot indicators present if world_data has hotspots
        for ind in frame.topology_indicators:
            assert ind.indicator_type == "hotspot_center"

    def test_world_info(self, system_a_signal) -> None:
        handle, wadapter, sadapter = system_a_signal
        frame = build_frame(handle, wadapter, sadapter)
        if frame.status.world_info is not None:
            assert "hotspot" in frame.status.world_info.lower()

    def test_five_analysis_sections(self, system_a_signal) -> None:
        handle, wadapter, sadapter = system_a_signal
        frame = build_frame(handle, wadapter, sadapter)
        assert len(frame.analysis_sections) == 5

    def test_boundary_phases_build(self, system_a_signal) -> None:
        handle, wadapter, sadapter = system_a_signal
        for phase in [0, 2]:
            frame = build_frame(
                handle, wadapter, sadapter, step_index=0, phase_index=phase)
            assert frame is not None

    def test_multi_step(self, system_a_signal) -> None:
        handle, wadapter, sadapter = system_a_signal
        for i in range(min(handle.validation.total_steps, 5)):
            frame = build_frame(handle, wadapter, sadapter, step_index=i)
            assert frame is not None
