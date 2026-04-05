"""Tests for debug overlay projection in ViewModelBuilder (VWP9)."""

from __future__ import annotations

import pytest

from axis_system_a.visualization.debug_overlay_models import (
    ActionPreferenceOverlay,
    ConsumptionOpportunityOverlay,
    DebugOverlayConfig,
    DebugOverlayViewModel,
    DriveContributionOverlay,
)
from axis_system_a.visualization.snapshot_resolver import SnapshotResolver
from axis_system_a.visualization.view_model_builder import ViewModelBuilder
from axis_system_a.visualization.viewer_state import ViewerState
from axis_system_a.visualization.viewer_state_transitions import (
    set_overlay_type_enabled,
    toggle_debug_overlay,
)


@pytest.fixture
def builder(snapshot_resolver: SnapshotResolver) -> ViewModelBuilder:
    return ViewModelBuilder(snapshot_resolver)


# ---------------------------------------------------------------------------
# Master toggle controls presence of overlay
# ---------------------------------------------------------------------------


class TestMasterToggle:
    def test_overlay_none_when_disabled(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        frame = builder.build(initial_viewer_state)
        assert frame.debug_overlay is None

    def test_overlay_present_when_enabled(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        frame = builder.build(state)
        assert frame.debug_overlay is not None
        assert isinstance(frame.debug_overlay, DebugOverlayViewModel)

    def test_sub_overlays_none_when_types_disabled(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        frame = builder.build(state)
        assert frame.debug_overlay.action_preference is None
        assert frame.debug_overlay.drive_contribution is None
        assert frame.debug_overlay.consumption_opportunity is None


# ---------------------------------------------------------------------------
# Action preference overlay
# ---------------------------------------------------------------------------


class TestActionPreferenceProjection:
    def test_present_when_enabled(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "action_preference_enabled", True)
        frame = builder.build(state)
        ap = frame.debug_overlay.action_preference
        assert isinstance(ap, ActionPreferenceOverlay)

    def test_probabilities_length(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "action_preference_enabled", True)
        frame = builder.build(state)
        assert len(frame.debug_overlay.action_preference.probabilities) == 6

    def test_mask_length(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "action_preference_enabled", True)
        frame = builder.build(state)
        assert len(frame.debug_overlay.action_preference.admissibility_mask) == 6

    def test_selected_action_in_range(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "action_preference_enabled", True)
        frame = builder.build(state)
        assert 0 <= frame.debug_overlay.action_preference.selected_action_index <= 5

    def test_agent_position_matches(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "action_preference_enabled", True)
        frame = builder.build(state)
        ap = frame.debug_overlay.action_preference
        assert ap.agent_row == frame.agent.row
        assert ap.agent_col == frame.agent.col


# ---------------------------------------------------------------------------
# Drive contribution overlay
# ---------------------------------------------------------------------------


class TestDriveContributionProjection:
    def test_present_when_enabled(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "drive_contribution_enabled", True)
        frame = builder.build(state)
        dc = frame.debug_overlay.drive_contribution
        assert isinstance(dc, DriveContributionOverlay)

    def test_activation_in_range(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "drive_contribution_enabled", True)
        frame = builder.build(state)
        assert 0 <= frame.debug_overlay.drive_contribution.activation <= 1

    def test_contributions_length(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "drive_contribution_enabled", True)
        frame = builder.build(state)
        assert len(
            frame.debug_overlay.drive_contribution.action_contributions) == 6

    def test_agent_position_matches(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "drive_contribution_enabled", True)
        frame = builder.build(state)
        dc = frame.debug_overlay.drive_contribution
        assert dc.agent_row == frame.agent.row
        assert dc.agent_col == frame.agent.col


# ---------------------------------------------------------------------------
# Consumption opportunity overlay
# ---------------------------------------------------------------------------


class TestConsumptionOpportunityProjection:
    def test_present_when_enabled(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "consumption_opportunity_enabled", True,
        )
        frame = builder.build(state)
        co = frame.debug_overlay.consumption_opportunity
        assert isinstance(co, ConsumptionOpportunityOverlay)

    def test_neighbor_resources_length(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "consumption_opportunity_enabled", True,
        )
        frame = builder.build(state)
        assert len(
            frame.debug_overlay.consumption_opportunity.neighbor_resources) == 4

    def test_neighbor_traversable_length(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "consumption_opportunity_enabled", True,
        )
        frame = builder.build(state)
        assert len(
            frame.debug_overlay.consumption_opportunity.neighbor_traversable) == 4

    def test_resource_in_range(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "consumption_opportunity_enabled", True,
        )
        frame = builder.build(state)
        co = frame.debug_overlay.consumption_opportunity
        assert 0 <= co.current_resource <= 1

    def test_agent_position_matches(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "consumption_opportunity_enabled", True,
        )
        frame = builder.build(state)
        co = frame.debug_overlay.consumption_opportunity
        assert co.agent_row == frame.agent.row
        assert co.agent_col == frame.agent.col


# ---------------------------------------------------------------------------
# All overlays enabled simultaneously
# ---------------------------------------------------------------------------


class TestAllOverlaysEnabled:
    def test_all_present(
        self, builder: ViewModelBuilder, initial_viewer_state: ViewerState,
    ):
        state = toggle_debug_overlay(initial_viewer_state)
        state = set_overlay_type_enabled(
            state, "action_preference_enabled", True)
        state = set_overlay_type_enabled(
            state, "drive_contribution_enabled", True)
        state = set_overlay_type_enabled(
            state, "consumption_opportunity_enabled", True,
        )
        frame = builder.build(state)
        assert frame.debug_overlay.action_preference is not None
        assert frame.debug_overlay.drive_contribution is not None
        assert frame.debug_overlay.consumption_opportunity is not None
