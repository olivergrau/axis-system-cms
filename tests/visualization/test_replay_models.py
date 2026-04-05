"""Tests for visualization replay models."""

from __future__ import annotations

import pytest

from axis_system_a.visualization.replay_models import (
    ReplayEpisodeHandle,
    ReplayExperimentHandle,
    ReplayPhaseAvailability,
    ReplayRunHandle,
    ReplayStepDescriptor,
    ReplayValidationResult,
)


class TestReplayPhaseAvailability:
    def test_construction(self):
        pa = ReplayPhaseAvailability(
            before=True, after_regen=True, after_action=False,
        )
        assert pa.before is True
        assert pa.after_regen is True
        assert pa.after_action is False

    def test_frozen(self):
        pa = ReplayPhaseAvailability(
            before=True, after_regen=True, after_action=True,
        )
        with pytest.raises(Exception):
            pa.before = False  # type: ignore[misc]


class TestReplayStepDescriptor:
    def test_construction(self):
        pa = ReplayPhaseAvailability(
            before=True, after_regen=True, after_action=True,
        )
        sd = ReplayStepDescriptor(
            step_index=0,
            phase_availability=pa,
            has_agent_position=True,
            has_agent_energy=True,
            has_world_state=True,
        )
        assert sd.step_index == 0
        assert sd.phase_availability.before is True
        assert sd.has_agent_position is True
        assert sd.has_agent_energy is True
        assert sd.has_world_state is True

    def test_frozen(self):
        pa = ReplayPhaseAvailability(
            before=True, after_regen=True, after_action=True,
        )
        sd = ReplayStepDescriptor(
            step_index=0,
            phase_availability=pa,
            has_agent_position=True,
            has_agent_energy=True,
            has_world_state=True,
        )
        with pytest.raises(Exception):
            sd.step_index = 1  # type: ignore[misc]


class TestReplayValidationResult:
    def test_valid_result(self):
        vr = ReplayValidationResult(valid=True, total_steps=5)
        assert vr.valid is True
        assert vr.total_steps == 5
        assert vr.violations == ()
        assert vr.step_descriptors == ()
        assert vr.grid_width is None

    def test_invalid_result_with_violations(self):
        vr = ReplayValidationResult(
            valid=False,
            total_steps=3,
            violations=("violation A", "violation B"),
        )
        assert vr.valid is False
        assert len(vr.violations) == 2
        assert "violation A" in vr.violations

    def test_frozen(self):
        vr = ReplayValidationResult(valid=True, total_steps=1)
        with pytest.raises(Exception):
            vr.valid = False  # type: ignore[misc]


class TestReplayExperimentHandle:
    def test_construction(self, access_service):
        handle = access_service.get_experiment_handle("test-exp")
        assert handle.experiment_id == "test-exp"
        assert len(handle.available_runs) > 0

    def test_frozen(self, access_service):
        handle = access_service.get_experiment_handle("test-exp")
        with pytest.raises(Exception):
            handle.experiment_id = "x"  # type: ignore[misc]


class TestReplayRunHandle:
    def test_construction(self, access_service):
        handle = access_service.get_run_handle("test-exp", "run-0000")
        assert handle.experiment_id == "test-exp"
        assert handle.run_id == "run-0000"
        assert 1 in handle.available_episodes

    def test_frozen(self, access_service):
        handle = access_service.get_run_handle("test-exp", "run-0000")
        with pytest.raises(Exception):
            handle.run_id = "x"  # type: ignore[misc]


class TestReplayEpisodeHandle:
    def test_construction(self, access_service):
        handle = access_service.load_replay_episode("test-exp", "run-0000", 1)
        assert handle.experiment_id == "test-exp"
        assert handle.run_id == "run-0000"
        assert handle.episode_index == 1
        assert handle.validation.valid is True

    def test_frozen(self, access_service):
        handle = access_service.load_replay_episode("test-exp", "run-0000", 1)
        with pytest.raises(Exception):
            handle.episode_index = 99  # type: ignore[misc]
