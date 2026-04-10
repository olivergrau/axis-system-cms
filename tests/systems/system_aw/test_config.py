"""WP-1 unit tests -- SystemAWConfig."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis.systems.system_aw.config import (
    ArbitrationConfig,
    CuriosityConfig,
    SystemAWConfig,
)
from tests.builders.system_aw_config_builder import SystemAWConfigBuilder


class TestCuriosityConfig:
    """CuriosityConfig validation tests."""

    def test_default_curiosity_config(self) -> None:
        config = CuriosityConfig()
        assert config.base_curiosity == 1.0
        assert config.spatial_sensory_balance == 0.5
        assert config.explore_suppression == 0.3

    def test_custom_curiosity_config(self) -> None:
        config = CuriosityConfig(
            base_curiosity=0.7,
            spatial_sensory_balance=0.8,
            explore_suppression=0.5,
        )
        assert config.base_curiosity == 0.7
        assert config.spatial_sensory_balance == 0.8
        assert config.explore_suppression == 0.5

    def test_curiosity_base_bounds(self) -> None:
        with pytest.raises(ValidationError):
            CuriosityConfig(base_curiosity=-0.1)
        with pytest.raises(ValidationError):
            CuriosityConfig(base_curiosity=1.1)

    def test_alpha_bounds(self) -> None:
        with pytest.raises(ValidationError):
            CuriosityConfig(spatial_sensory_balance=-0.1)
        with pytest.raises(ValidationError):
            CuriosityConfig(spatial_sensory_balance=1.1)

    def test_explore_suppression_nonneg(self) -> None:
        with pytest.raises(ValidationError):
            CuriosityConfig(explore_suppression=-0.1)


class TestArbitrationConfig:
    """ArbitrationConfig validation tests."""

    def test_default_arbitration_config(self) -> None:
        config = ArbitrationConfig()
        assert config.hunger_weight_base == 0.3
        assert config.curiosity_weight_base == 1.0
        assert config.gating_sharpness == 2.0

    def test_custom_arbitration_config(self) -> None:
        config = ArbitrationConfig(
            hunger_weight_base=0.5,
            curiosity_weight_base=2.0,
            gating_sharpness=4.0,
        )
        assert config.hunger_weight_base == 0.5
        assert config.curiosity_weight_base == 2.0
        assert config.gating_sharpness == 4.0

    def test_hunger_weight_base_bounds(self) -> None:
        with pytest.raises(ValidationError):
            ArbitrationConfig(hunger_weight_base=0.0)  # gt=0, not ge=0
        with pytest.raises(ValidationError):
            ArbitrationConfig(hunger_weight_base=1.1)

    def test_gating_sharpness_positive(self) -> None:
        with pytest.raises(ValidationError):
            ArbitrationConfig(gating_sharpness=0.0)
        with pytest.raises(ValidationError):
            ArbitrationConfig(gating_sharpness=-1.0)


class TestSystemAWConfig:
    """SystemAWConfig composition and validation tests."""

    def test_system_aw_config_full(self) -> None:
        d = SystemAWConfigBuilder().build()
        config = SystemAWConfig(**d)
        assert config.agent.initial_energy == 50.0
        assert config.policy.selection_mode == "sample"
        assert config.transition.move_cost == 1.0
        assert config.curiosity.base_curiosity == 1.0
        assert config.arbitration.hunger_weight_base == 0.3

    def test_system_aw_config_defaults(self) -> None:
        d = SystemAWConfigBuilder().build()
        del d["curiosity"]
        del d["arbitration"]
        config = SystemAWConfig(**d)
        assert config.curiosity.base_curiosity == 1.0
        assert config.curiosity.spatial_sensory_balance == 0.5
        assert config.curiosity.explore_suppression == 0.3
        assert config.arbitration.hunger_weight_base == 0.3
        assert config.arbitration.curiosity_weight_base == 1.0
        assert config.arbitration.gating_sharpness == 2.0

    def test_config_frozen(self) -> None:
        d = SystemAWConfigBuilder().build()
        config = SystemAWConfig(**d)
        with pytest.raises(ValidationError):
            config.curiosity.base_curiosity = 0.5  # type: ignore[misc]

    def test_inherited_agent_validation(self) -> None:
        d = SystemAWConfigBuilder().with_initial_energy(
            200.0).with_max_energy(100.0).build()
        with pytest.raises(ValidationError, match="initial_energy"):
            SystemAWConfig(**d)

    def test_reduction_config(self) -> None:
        d = SystemAWConfigBuilder().with_base_curiosity(0.0).build()
        config = SystemAWConfig(**d)
        assert config.curiosity.base_curiosity == 0.0
