"""Tests for debug overlay state transitions (VWP9)."""

from __future__ import annotations

from axis_system_a.visualization.debug_overlay_models import DebugOverlayConfig
from axis_system_a.visualization.viewer_state import ViewerState, create_initial_state
from axis_system_a.visualization.viewer_state_transitions import (
    set_overlay_type_enabled,
    toggle_debug_overlay,
)


class TestToggleDebugOverlay:
    def test_toggle_on(self, initial_viewer_state: ViewerState):
        new = toggle_debug_overlay(initial_viewer_state)
        assert new.debug_overlay_config.master_enabled is True

    def test_toggle_off(self, initial_viewer_state: ViewerState):
        on = toggle_debug_overlay(initial_viewer_state)
        off = toggle_debug_overlay(on)
        assert off.debug_overlay_config.master_enabled is False

    def test_does_not_mutate_original(self, initial_viewer_state: ViewerState):
        toggle_debug_overlay(initial_viewer_state)
        assert initial_viewer_state.debug_overlay_config.master_enabled is False

    def test_preserves_other_state(self, initial_viewer_state: ViewerState):
        new = toggle_debug_overlay(initial_viewer_state)
        assert new.coordinate == initial_viewer_state.coordinate
        assert new.episode_handle is initial_viewer_state.episode_handle
        assert new.playback_mode == initial_viewer_state.playback_mode


class TestSetOverlayTypeEnabled:
    def test_enable_action_preference(self, initial_viewer_state: ViewerState):
        new = set_overlay_type_enabled(
            initial_viewer_state, "action_preference_enabled", True,
        )
        assert new.debug_overlay_config.action_preference_enabled is True

    def test_enable_drive_contribution(self, initial_viewer_state: ViewerState):
        new = set_overlay_type_enabled(
            initial_viewer_state, "drive_contribution_enabled", True,
        )
        assert new.debug_overlay_config.drive_contribution_enabled is True

    def test_enable_consumption_opportunity(self, initial_viewer_state: ViewerState):
        new = set_overlay_type_enabled(
            initial_viewer_state, "consumption_opportunity_enabled", True,
        )
        assert new.debug_overlay_config.consumption_opportunity_enabled is True

    def test_disable(self, initial_viewer_state: ViewerState):
        on = set_overlay_type_enabled(
            initial_viewer_state, "action_preference_enabled", True,
        )
        off = set_overlay_type_enabled(on, "action_preference_enabled", False)
        assert off.debug_overlay_config.action_preference_enabled is False

    def test_does_not_mutate_original(self, initial_viewer_state: ViewerState):
        set_overlay_type_enabled(
            initial_viewer_state, "action_preference_enabled", True,
        )
        assert initial_viewer_state.debug_overlay_config.action_preference_enabled is False

    def test_preserves_other_overlay_flags(self, initial_viewer_state: ViewerState):
        s1 = set_overlay_type_enabled(
            initial_viewer_state, "action_preference_enabled", True,
        )
        s2 = set_overlay_type_enabled(s1, "drive_contribution_enabled", True)
        assert s2.debug_overlay_config.action_preference_enabled is True
        assert s2.debug_overlay_config.drive_contribution_enabled is True

    def test_preserves_master_flag(self, initial_viewer_state: ViewerState):
        on = toggle_debug_overlay(initial_viewer_state)
        new = set_overlay_type_enabled(on, "action_preference_enabled", True)
        assert new.debug_overlay_config.master_enabled is True
