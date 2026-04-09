"""Tests for WP-V.5.3: System A Regression.

Determinism and structural invariants for System A visualization.
"""

from __future__ import annotations

import pytest

from tests.visualization.e2e_helpers import (
    build_frame,
    load_episode_through_pipeline,
    run_and_persist_experiment,
)


@pytest.fixture(scope="module")
def regression_run_1(tmp_path_factory):
    """First run with seed=42."""
    tmp_path = tmp_path_factory.mktemp("regr_1")
    repo, eid = run_and_persist_experiment(
        tmp_path, "system_a", max_steps=10, seed=42,
    )
    return load_episode_through_pipeline(repo, eid)


@pytest.fixture(scope="module")
def regression_run_2(tmp_path_factory):
    """Second run with same seed=42 — should produce identical output."""
    tmp_path = tmp_path_factory.mktemp("regr_2")
    repo, eid = run_and_persist_experiment(
        tmp_path, "system_a", max_steps=10, seed=42,
    )
    return load_episode_through_pipeline(repo, eid)


@pytest.fixture(scope="module")
def regression_run_alt(tmp_path_factory):
    """Run with different seed=99."""
    tmp_path = tmp_path_factory.mktemp("regr_alt")
    repo, eid = run_and_persist_experiment(
        tmp_path, "system_a", max_steps=10, seed=99,
    )
    return load_episode_through_pipeline(repo, eid)


class TestSystemARegressionDeterminism:

    def test_same_seed_same_step_count(self, regression_run_1, regression_run_2) -> None:
        h1, _, _ = regression_run_1
        h2, _, _ = regression_run_2
        assert h1.validation.total_steps == h2.validation.total_steps

    def test_same_seed_same_analysis_content(self, regression_run_1, regression_run_2) -> None:
        h1, w1, s1 = regression_run_1
        h2, w2, s2 = regression_run_2
        f1 = build_frame(h1, w1, s1, step_index=0)
        f2 = build_frame(h2, w2, s2, step_index=0)
        titles_1 = [s.title for s in f1.analysis_sections]
        titles_2 = [s.title for s in f2.analysis_sections]
        assert titles_1 == titles_2

    def test_same_seed_same_vitality(self, regression_run_1, regression_run_2) -> None:
        h1, w1, s1 = regression_run_1
        h2, w2, s2 = regression_run_2
        f1 = build_frame(h1, w1, s1, step_index=0)
        f2 = build_frame(h2, w2, s2, step_index=0)
        assert f1.status.vitality_display == f2.status.vitality_display

    def test_same_seed_same_agent_position(self, regression_run_1, regression_run_2) -> None:
        h1, w1, s1 = regression_run_1
        h2, w2, s2 = regression_run_2
        for i in range(min(h1.validation.total_steps, 5)):
            f1 = build_frame(h1, w1, s1, step_index=i)
            f2 = build_frame(h2, w2, s2, step_index=i)
            assert (f1.agent.row, f1.agent.col) == (f2.agent.row, f2.agent.col)

    def test_different_seed_differs(self, regression_run_1, regression_run_alt) -> None:
        h1, w1, s1 = regression_run_1
        h_alt, w_alt, s_alt = regression_run_alt
        # With different seeds, at least one step should have different vitality
        min_steps = min(h1.validation.total_steps,
                        h_alt.validation.total_steps, 5)
        differs = False
        for i in range(min_steps):
            f1 = build_frame(h1, w1, s1, step_index=i)
            f_alt = build_frame(h_alt, w_alt, s_alt, step_index=i)
            if f1.status.vitality_display != f_alt.status.vitality_display:
                differs = True
                break
        assert differs


class TestSystemARegressionStructure:

    def test_decision_pipeline_action_rows(self, regression_run_1) -> None:
        handle, wadapter, sadapter = regression_run_1
        frame = build_frame(handle, wadapter, sadapter)
        dp = [s for s in frame.analysis_sections
              if s.title == "Decision Pipeline"][0]
        action_rows = [r for r in dp.rows if r.sub_rows is not None]
        assert len(action_rows) == 6

    def test_observation_directions(self, regression_run_1) -> None:
        handle, wadapter, sadapter = regression_run_1
        frame = build_frame(handle, wadapter, sadapter)
        obs = [s for s in frame.analysis_sections
               if s.title == "Observation"][0]
        labels = {r.label for r in obs.rows}
        assert {"Current", "Up", "Down", "Left", "Right"} <= labels

    def test_energy_format_structure(self, regression_run_1) -> None:
        handle, wadapter, sadapter = regression_run_1
        frame = build_frame(handle, wadapter, sadapter)
        # Energy format: "X.XX / Y.YY"
        parts = frame.status.vitality_display.split(" / ")
        assert len(parts) == 2
        float(parts[0])  # Should parse
        float(parts[1])  # Should parse

    def test_overlay_items_have_grid_positions(self, regression_run_1) -> None:
        handle, wadapter, sadapter = regression_run_1
        # Build frame with overlays enabled
        from axis.visualization.viewer_state_transitions import (
            set_overlay_enabled,
            toggle_overlay_master,
        )
        from axis.visualization.snapshot_resolver import SnapshotResolver
        from axis.visualization.view_model_builder import ViewModelBuilder
        from axis.visualization.viewer_state import create_initial_state

        num_phases = len(sadapter.phase_names())
        state = create_initial_state(handle, num_phases)
        state = toggle_overlay_master(state)
        for key in ["action_preference", "drive_contribution",
                    "consumption_opportunity"]:
            state = set_overlay_enabled(state, key, True)

        builder = ViewModelBuilder(SnapshotResolver(), wadapter, sadapter)
        frame = builder.build(state)
        # All overlay items should have a 2-tuple grid_position.
        # Neighbor positions may extend one cell beyond grid bounds.
        for overlay in frame.overlay_data:
            for item in overlay.items:
                x, y = item.grid_position
                assert -1 <= x <= handle.validation.grid_width
                assert -1 <= y <= handle.validation.grid_height

    def test_step_overview_fields(self, regression_run_1) -> None:
        handle, wadapter, sadapter = regression_run_1
        frame = build_frame(handle, wadapter, sadapter)
        overview = [s for s in frame.analysis_sections
                    if s.title == "Step Overview"][0]
        labels = {r.label for r in overview.rows}
        assert "Timestep" in labels
        assert "Action" in labels
