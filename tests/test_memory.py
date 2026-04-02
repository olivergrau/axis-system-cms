"""Tests for the memory update function."""

import inspect

import pytest

from axis_system_a import (
    CellObservation,
    MemoryEntry,
    MemoryState,
    Observation,
    update_memory,
)


def _make_obs(resource: float = 0.0) -> Observation:
    """Create an observation with a distinctive resource value."""
    cell = CellObservation(traversability=1.0, resource=resource)
    return Observation(
        current=cell, up=cell, down=cell, left=cell, right=cell,
    )


class TestUpdateMemory:
    def test_append_to_empty(self, sample_observation: Observation):
        memory = MemoryState(capacity=5)
        result = update_memory(memory, sample_observation, timestep=0)
        assert len(result.entries) == 1

    def test_entry_has_correct_timestep(self, sample_observation: Observation):
        memory = MemoryState(capacity=5)
        result = update_memory(memory, sample_observation, timestep=3)
        assert result.entries[0].timestep == 3

    def test_entry_has_correct_observation(
        self, sample_observation: Observation
    ):
        memory = MemoryState(capacity=5)
        result = update_memory(memory, sample_observation, timestep=0)
        assert result.entries[0].observation == sample_observation

    def test_preserves_chronological_order(self):
        memory = MemoryState(capacity=5)
        obs_a = _make_obs(0.1)
        obs_b = _make_obs(0.2)
        obs_c = _make_obs(0.3)
        memory = update_memory(memory, obs_a, timestep=0)
        memory = update_memory(memory, obs_b, timestep=1)
        memory = update_memory(memory, obs_c, timestep=2)
        assert memory.entries[0].timestep == 0
        assert memory.entries[1].timestep == 1
        assert memory.entries[2].timestep == 2

    def test_fifo_drops_oldest(self):
        memory = MemoryState(capacity=2)
        obs_a = _make_obs(0.1)
        obs_b = _make_obs(0.2)
        obs_c = _make_obs(0.3)
        memory = update_memory(memory, obs_a, timestep=0)
        memory = update_memory(memory, obs_b, timestep=1)
        memory = update_memory(memory, obs_c, timestep=2)
        assert len(memory.entries) == 2
        assert memory.entries[0].timestep == 1
        assert memory.entries[1].timestep == 2

    def test_size_never_exceeds_capacity(self):
        memory = MemoryState(capacity=3)
        for t in range(10):
            memory = update_memory(memory, _make_obs(t * 0.1), timestep=t)
            assert len(memory.entries) <= 3

    def test_returns_new_instance(self, sample_observation: Observation):
        original = MemoryState(capacity=5)
        result = update_memory(original, sample_observation, timestep=0)
        assert result is not original
        assert len(original.entries) == 0
        assert len(result.entries) == 1

    def test_capacity_preserved(self, sample_observation: Observation):
        memory = MemoryState(capacity=7)
        result = update_memory(memory, sample_observation, timestep=0)
        assert result.capacity == 7

    def test_capacity_one(self):
        memory = MemoryState(capacity=1)
        obs_a = _make_obs(0.1)
        obs_b = _make_obs(0.2)
        memory = update_memory(memory, obs_a, timestep=0)
        assert len(memory.entries) == 1
        assert memory.entries[0].observation == obs_a
        memory = update_memory(memory, obs_b, timestep=1)
        assert len(memory.entries) == 1
        assert memory.entries[0].observation == obs_b

    def test_fill_to_exact_capacity(self):
        memory = MemoryState(capacity=3)
        for t in range(3):
            memory = update_memory(memory, _make_obs(t * 0.1), timestep=t)
        assert len(memory.entries) == 3
        assert memory.entries[0].timestep == 0

    def test_overflow_by_one(self):
        memory = MemoryState(capacity=3)
        for t in range(4):
            memory = update_memory(memory, _make_obs(t * 0.1), timestep=t)
        assert len(memory.entries) == 3
        assert memory.entries[0].timestep == 1

    def test_multiple_overflows_sliding_window(self):
        memory = MemoryState(capacity=2)
        for t in range(5):
            memory = update_memory(memory, _make_obs(t * 0.1), timestep=t)
        assert len(memory.entries) == 2
        assert memory.entries[0].timestep == 3
        assert memory.entries[1].timestep == 4


class TestMemorySeparation:
    def test_memory_entry_no_position_field(self):
        assert "position" not in MemoryEntry.model_fields

    def test_update_memory_takes_no_world_or_policy_args(self):
        sig = inspect.signature(update_memory)
        params = set(sig.parameters.keys())
        assert params == {"memory", "observation", "timestep"}
