"""Tests for debug overlay data models (VWP9)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis_system_a.visualization.debug_overlay_models import (
    ActionPreferenceOverlay,
    ConsumptionOpportunityOverlay,
    DebugOverlayConfig,
    DebugOverlayType,
    DebugOverlayViewModel,
    DriveContributionOverlay,
)


# ---------------------------------------------------------------------------
# DebugOverlayType enum
# ---------------------------------------------------------------------------


class TestDebugOverlayType:
    def test_member_count(self):
        assert len(DebugOverlayType) == 3

    def test_values(self):
        assert DebugOverlayType.ACTION_PREFERENCE == "action_preference"
        assert DebugOverlayType.DRIVE_CONTRIBUTION == "drive_contribution"
        assert DebugOverlayType.CONSUMPTION_OPPORTUNITY == "consumption_opportunity"


# ---------------------------------------------------------------------------
# DebugOverlayConfig
# ---------------------------------------------------------------------------


class TestDebugOverlayConfig:
    def test_defaults_all_false(self):
        cfg = DebugOverlayConfig()
        assert cfg.master_enabled is False
        assert cfg.action_preference_enabled is False
        assert cfg.drive_contribution_enabled is False
        assert cfg.consumption_opportunity_enabled is False

    def test_frozen(self):
        cfg = DebugOverlayConfig()
        with pytest.raises(ValidationError):
            cfg.master_enabled = True

    def test_explicit_true(self):
        cfg = DebugOverlayConfig(
            master_enabled=True,
            action_preference_enabled=True,
        )
        assert cfg.master_enabled is True
        assert cfg.action_preference_enabled is True

    def test_model_copy_update(self):
        cfg = DebugOverlayConfig()
        cfg2 = cfg.model_copy(update={"master_enabled": True})
        assert cfg2.master_enabled is True
        assert cfg.master_enabled is False


# ---------------------------------------------------------------------------
# ActionPreferenceOverlay
# ---------------------------------------------------------------------------

_PROBS = (0.1, 0.2, 0.15, 0.25, 0.2, 0.1)
_MASK = (True, True, True, True, True, True)


class TestActionPreferenceOverlay:
    def test_construction(self):
        o = ActionPreferenceOverlay(
            agent_row=2, agent_col=3,
            probabilities=_PROBS,
            admissibility_mask=_MASK,
            selected_action_index=3,
        )
        assert o.agent_row == 2
        assert o.agent_col == 3
        assert len(o.probabilities) == 6
        assert len(o.admissibility_mask) == 6
        assert o.selected_action_index == 3

    def test_frozen(self):
        o = ActionPreferenceOverlay(
            agent_row=0, agent_col=0,
            probabilities=_PROBS,
            admissibility_mask=_MASK,
            selected_action_index=0,
        )
        with pytest.raises(ValidationError):
            o.agent_row = 1

    def test_negative_row_rejected(self):
        with pytest.raises(ValidationError):
            ActionPreferenceOverlay(
                agent_row=-1, agent_col=0,
                probabilities=_PROBS,
                admissibility_mask=_MASK,
                selected_action_index=0,
            )

    def test_action_index_out_of_range(self):
        with pytest.raises(ValidationError):
            ActionPreferenceOverlay(
                agent_row=0, agent_col=0,
                probabilities=_PROBS,
                admissibility_mask=_MASK,
                selected_action_index=6,
            )


# ---------------------------------------------------------------------------
# DriveContributionOverlay
# ---------------------------------------------------------------------------


class TestDriveContributionOverlay:
    def test_construction(self):
        o = DriveContributionOverlay(
            agent_row=1, agent_col=1,
            activation=0.75,
            action_contributions=(0.1, -0.2, 0.3, -0.4, 0.5, -0.1),
        )
        assert o.activation == 0.75
        assert len(o.action_contributions) == 6

    def test_frozen(self):
        o = DriveContributionOverlay(
            agent_row=0, agent_col=0,
            activation=0.5,
            action_contributions=(0.0,) * 6,
        )
        with pytest.raises(ValidationError):
            o.activation = 0.9

    def test_activation_bounds(self):
        with pytest.raises(ValidationError):
            DriveContributionOverlay(
                agent_row=0, agent_col=0,
                activation=1.5,
                action_contributions=(0.0,) * 6,
            )


# ---------------------------------------------------------------------------
# ConsumptionOpportunityOverlay
# ---------------------------------------------------------------------------


class TestConsumptionOpportunityOverlay:
    def test_construction(self):
        o = ConsumptionOpportunityOverlay(
            agent_row=2, agent_col=2,
            current_resource=0.8,
            neighbor_resources=(0.5, 0.0, 0.3, 0.0),
            neighbor_traversable=(True, False, True, True),
        )
        assert o.current_resource == 0.8
        assert len(o.neighbor_resources) == 4
        assert len(o.neighbor_traversable) == 4

    def test_frozen(self):
        o = ConsumptionOpportunityOverlay(
            agent_row=0, agent_col=0,
            current_resource=0.0,
            neighbor_resources=(0.0,) * 4,
            neighbor_traversable=(True,) * 4,
        )
        with pytest.raises(ValidationError):
            o.current_resource = 0.5

    def test_resource_bounds(self):
        with pytest.raises(ValidationError):
            ConsumptionOpportunityOverlay(
                agent_row=0, agent_col=0,
                current_resource=1.5,
                neighbor_resources=(0.0,) * 4,
                neighbor_traversable=(True,) * 4,
            )


# ---------------------------------------------------------------------------
# DebugOverlayViewModel
# ---------------------------------------------------------------------------


class TestDebugOverlayViewModel:
    def test_all_none_by_default(self):
        vm = DebugOverlayViewModel(config=DebugOverlayConfig())
        assert vm.action_preference is None
        assert vm.drive_contribution is None
        assert vm.consumption_opportunity is None

    def test_with_overlays(self):
        ap = ActionPreferenceOverlay(
            agent_row=0, agent_col=0,
            probabilities=_PROBS,
            admissibility_mask=_MASK,
            selected_action_index=0,
        )
        vm = DebugOverlayViewModel(
            config=DebugOverlayConfig(
                master_enabled=True, action_preference_enabled=True),
            action_preference=ap,
        )
        assert vm.action_preference is not None
        assert vm.config.master_enabled is True

    def test_frozen(self):
        vm = DebugOverlayViewModel(config=DebugOverlayConfig())
        with pytest.raises(ValidationError):
            vm.config = DebugOverlayConfig(master_enabled=True)

    def test_field_names(self):
        fields = set(DebugOverlayViewModel.model_fields.keys())
        expected = {"config", "action_preference",
                    "drive_contribution", "consumption_opportunity"}
        assert fields == expected
