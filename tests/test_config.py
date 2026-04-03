"""Tests for configuration models and validation."""

import copy

import pytest
from pydantic import ValidationError

from axis_system_a import (
    AgentConfig,
    ExecutionConfig,
    GeneralConfig,
    PolicyConfig,
    SimulationConfig,
    TransitionConfig,
    WorldConfig,
)


class TestValidConfig:
    def test_valid_config_passes(self, valid_config: SimulationConfig):
        assert valid_config is not None

    def test_sections_accessible(self, valid_config: SimulationConfig):
        assert isinstance(valid_config.general, GeneralConfig)
        assert isinstance(valid_config.world, WorldConfig)
        assert isinstance(valid_config.agent, AgentConfig)
        assert isinstance(valid_config.policy, PolicyConfig)
        assert isinstance(valid_config.transition, TransitionConfig)
        assert isinstance(valid_config.execution, ExecutionConfig)

    def test_frozen(self, valid_config: SimulationConfig):
        with pytest.raises(ValidationError):
            valid_config.general = GeneralConfig(seed=99)

    def test_model_dump_roundtrip(self, valid_config: SimulationConfig):
        dump = valid_config.model_dump()
        reconstructed = SimulationConfig(**dump)
        assert reconstructed == valid_config

    def test_json_roundtrip(self, valid_config: SimulationConfig):
        json_str = valid_config.model_dump_json()
        reconstructed = SimulationConfig.model_validate_json(json_str)
        assert reconstructed == valid_config

    def test_selection_mode_argmax(self, valid_config_dict: dict):
        d = copy.deepcopy(valid_config_dict)
        d["policy"]["selection_mode"] = "argmax"
        config = SimulationConfig(**d)
        assert config.policy.selection_mode.value == "argmax"

    def test_initial_energy_equals_max(self, valid_config_dict: dict):
        d = copy.deepcopy(valid_config_dict)
        d["agent"]["initial_energy"] = 100.0
        d["agent"]["max_energy"] = 100.0
        config = SimulationConfig(**d)
        assert config.agent.initial_energy == config.agent.max_energy

    def test_stay_suppression_zero(self, valid_config_dict: dict):
        d = copy.deepcopy(valid_config_dict)
        d["policy"]["stay_suppression"] = 0.0
        config = SimulationConfig(**d)
        assert config.policy.stay_suppression == 0.0

    def test_negative_seed(self, valid_config_dict: dict):
        d = copy.deepcopy(valid_config_dict)
        d["general"]["seed"] = -123
        config = SimulationConfig(**d)
        assert config.general.seed == -123

    def test_large_seed(self, valid_config_dict: dict):
        d = copy.deepcopy(valid_config_dict)
        d["general"]["seed"] = 2**63
        config = SimulationConfig(**d)
        assert config.general.seed == 2**63


class TestWorldConfigValidation:
    def test_grid_width_zero(self):
        with pytest.raises(ValidationError):
            WorldConfig(grid_width=0, grid_height=10)

    def test_grid_width_negative(self):
        with pytest.raises(ValidationError):
            WorldConfig(grid_width=-5, grid_height=10)

    def test_grid_height_zero(self):
        with pytest.raises(ValidationError):
            WorldConfig(grid_width=10, grid_height=0)

    def test_regen_rate_zero_valid(self):
        config = WorldConfig(grid_width=10, grid_height=10, resource_regen_rate=0.0)
        assert config.resource_regen_rate == 0.0

    def test_regen_rate_one_valid(self):
        config = WorldConfig(grid_width=10, grid_height=10, resource_regen_rate=1.0)
        assert config.resource_regen_rate == 1.0

    def test_regen_rate_default_zero(self):
        config = WorldConfig(grid_width=10, grid_height=10)
        assert config.resource_regen_rate == 0.0

    def test_regen_rate_negative_invalid(self):
        with pytest.raises(ValidationError):
            WorldConfig(grid_width=10, grid_height=10, resource_regen_rate=-0.1)

    def test_regen_rate_above_one_invalid(self):
        with pytest.raises(ValidationError):
            WorldConfig(grid_width=10, grid_height=10, resource_regen_rate=1.1)


class TestAgentConfigValidation:
    def test_initial_energy_zero(self):
        with pytest.raises(ValidationError):
            AgentConfig(initial_energy=0.0,
                        max_energy=100.0, memory_capacity=5)

    def test_initial_energy_negative(self):
        with pytest.raises(ValidationError):
            AgentConfig(initial_energy=-10.0,
                        max_energy=100.0, memory_capacity=5)

    def test_initial_energy_exceeds_max(self):
        with pytest.raises(ValidationError):
            AgentConfig(initial_energy=150.0,
                        max_energy=100.0, memory_capacity=5)

    def test_max_energy_zero(self):
        with pytest.raises(ValidationError):
            AgentConfig(initial_energy=50.0, max_energy=0.0, memory_capacity=5)

    def test_memory_capacity_zero(self):
        with pytest.raises(ValidationError):
            AgentConfig(initial_energy=50.0,
                        max_energy=100.0, memory_capacity=0)

    def test_memory_capacity_negative(self):
        with pytest.raises(ValidationError):
            AgentConfig(initial_energy=50.0,
                        max_energy=100.0, memory_capacity=-1)


class TestPolicyConfigValidation:
    def test_temperature_zero(self):
        with pytest.raises(ValidationError):
            PolicyConfig(
                selection_mode="sample",
                temperature=0.0,
                stay_suppression=0.1,
                consume_weight=1.5,
            )

    def test_temperature_negative(self):
        with pytest.raises(ValidationError):
            PolicyConfig(
                selection_mode="sample",
                temperature=-1.0,
                stay_suppression=0.1,
                consume_weight=1.5,
            )

    def test_stay_suppression_negative(self):
        with pytest.raises(ValidationError):
            PolicyConfig(
                selection_mode="sample",
                temperature=1.0,
                stay_suppression=-0.1,
                consume_weight=1.5,
            )

    def test_consume_weight_zero(self):
        with pytest.raises(ValidationError):
            PolicyConfig(
                selection_mode="sample",
                temperature=1.0,
                stay_suppression=0.1,
                consume_weight=0.0,
            )

    def test_consume_weight_negative(self):
        with pytest.raises(ValidationError):
            PolicyConfig(
                selection_mode="sample",
                temperature=1.0,
                stay_suppression=0.1,
                consume_weight=-1.0,
            )

    def test_invalid_selection_mode(self):
        with pytest.raises(ValidationError):
            PolicyConfig(
                selection_mode="greedy",
                temperature=1.0,
                stay_suppression=0.1,
                consume_weight=1.5,
            )


class TestExecutionConfigValidation:
    def test_max_steps_zero(self):
        with pytest.raises(ValidationError):
            ExecutionConfig(max_steps=0)


class TestMissingRequiredField:
    def test_missing_seed(self, valid_config_dict: dict):
        d = copy.deepcopy(valid_config_dict)
        del d["general"]["seed"]
        with pytest.raises(ValidationError):
            SimulationConfig(**d)


class TestTransitionConfigValidation:
    def test_valid_construction(self):
        tc = TransitionConfig(
            move_cost=1.0, consume_cost=1.0, stay_cost=0.5,
            max_consume=1.0, energy_gain_factor=10.0,
        )
        assert tc.move_cost == 1.0

    def test_frozen(self):
        tc = TransitionConfig(
            move_cost=1.0, consume_cost=1.0, stay_cost=0.5,
            max_consume=1.0, energy_gain_factor=10.0,
        )
        with pytest.raises(ValidationError):
            tc.move_cost = 2.0

    def test_move_cost_zero_invalid(self):
        with pytest.raises(ValidationError):
            TransitionConfig(
                move_cost=0.0, consume_cost=1.0, stay_cost=0.5,
                max_consume=1.0, energy_gain_factor=10.0,
            )

    def test_move_cost_negative_invalid(self):
        with pytest.raises(ValidationError):
            TransitionConfig(
                move_cost=-1.0, consume_cost=1.0, stay_cost=0.5,
                max_consume=1.0, energy_gain_factor=10.0,
            )

    def test_consume_cost_zero_invalid(self):
        with pytest.raises(ValidationError):
            TransitionConfig(
                move_cost=1.0, consume_cost=0.0, stay_cost=0.5,
                max_consume=1.0, energy_gain_factor=10.0,
            )

    def test_stay_cost_zero_valid(self):
        tc = TransitionConfig(
            move_cost=1.0, consume_cost=1.0, stay_cost=0.0,
            max_consume=1.0, energy_gain_factor=10.0,
        )
        assert tc.stay_cost == 0.0

    def test_stay_cost_negative_invalid(self):
        with pytest.raises(ValidationError):
            TransitionConfig(
                move_cost=1.0, consume_cost=1.0, stay_cost=-0.1,
                max_consume=1.0, energy_gain_factor=10.0,
            )

    def test_max_consume_zero_invalid(self):
        with pytest.raises(ValidationError):
            TransitionConfig(
                move_cost=1.0, consume_cost=1.0, stay_cost=0.5,
                max_consume=0.0, energy_gain_factor=10.0,
            )

    def test_energy_gain_factor_zero_valid(self):
        tc = TransitionConfig(
            move_cost=1.0, consume_cost=1.0, stay_cost=0.5,
            max_consume=1.0, energy_gain_factor=0.0,
        )
        assert tc.energy_gain_factor == 0.0

    def test_energy_gain_factor_negative_invalid(self):
        with pytest.raises(ValidationError):
            TransitionConfig(
                move_cost=1.0, consume_cost=1.0, stay_cost=0.5,
                max_consume=1.0, energy_gain_factor=-1.0,
            )
