"""Tests for WP-V.5.3: End-to-End System B + Signal Landscape."""

from __future__ import annotations

import pytest

from tests.v02.visualization.e2e_helpers import (
    build_frame,
    load_episode_through_pipeline,
    run_and_persist_experiment,
)


@pytest.fixture(scope="module")
def system_b_signal(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("e2e_b_signal")
    repo, eid = run_and_persist_experiment(
        tmp_path, "system_b", world_type="signal_landscape",
        max_steps=10, seed=42, grid_width=10, grid_height=10,
        world_config_extras={"num_hotspots": 2},
    )
    handle, wadapter, sadapter = load_episode_through_pipeline(repo, eid)
    return handle, wadapter, sadapter


class TestSystemBSignalPipeline:

    def test_experiment_runs(self, system_b_signal) -> None:
        handle, _, _ = system_b_signal
        assert handle.validation.valid is True

    def test_system_type(self, system_b_signal) -> None:
        handle, _, _ = system_b_signal
        assert handle.episode_trace.system_type == "system_b"

    def test_world_type(self, system_b_signal) -> None:
        handle, _, _ = system_b_signal
        assert handle.episode_trace.world_type == "signal_landscape"

    def test_two_phases(self, system_b_signal) -> None:
        _, _, sadapter = system_b_signal
        assert len(sadapter.phase_names()) == 2

    def test_adapter_types(self, system_b_signal) -> None:
        _, wadapter, sadapter = system_b_signal
        assert type(
            wadapter).__name__ == "SignalLandscapeWorldVisualizationAdapter"
        assert type(sadapter).__name__ == "SystemBVisualizationAdapter"

    def test_frame_builds(self, system_b_signal) -> None:
        handle, wadapter, sadapter = system_b_signal
        frame = build_frame(handle, wadapter, sadapter)
        assert frame is not None


class TestSystemBSignalFrame:

    def test_five_analysis_sections(self, system_b_signal) -> None:
        handle, wadapter, sadapter = system_b_signal
        frame = build_frame(handle, wadapter, sadapter)
        assert len(frame.analysis_sections) == 5

    def test_section_titles(self, system_b_signal) -> None:
        handle, wadapter, sadapter = system_b_signal
        frame = build_frame(handle, wadapter, sadapter)
        titles = [s.title for s in frame.analysis_sections]
        assert "Step Overview" in titles
        assert "Decision Weights" in titles
        assert "Outcome" in titles

    def test_heatmap_colors(self, system_b_signal) -> None:
        _, wadapter, _ = system_b_signal
        cfg = wadapter.cell_color_config()
        assert cfg.resource_color_max == (255, 100, 0)

    def test_energy_format(self, system_b_signal) -> None:
        handle, wadapter, sadapter = system_b_signal
        frame = build_frame(handle, wadapter, sadapter)
        assert "/" in frame.status.vitality_display

    def test_multi_step(self, system_b_signal) -> None:
        handle, wadapter, sadapter = system_b_signal
        for i in range(min(handle.validation.total_steps, 5)):
            frame = build_frame(handle, wadapter, sadapter, step_index=i)
            assert frame is not None

    def test_both_phases(self, system_b_signal) -> None:
        handle, wadapter, sadapter = system_b_signal
        for phase in range(2):
            frame = build_frame(
                handle, wadapter, sadapter, step_index=0, phase_index=phase)
            assert frame is not None
