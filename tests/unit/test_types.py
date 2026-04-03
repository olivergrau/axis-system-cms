"""Tests for fundamental runtime types."""

import pytest
from pydantic import ValidationError

from axis_system_a import (
    AgentState,
    CellObservation,
    MemoryEntry,
    MemoryState,
    Observation,
    Position,
    clip_energy,
)
from tests.utils.assertions import assert_model_frozen


class TestPosition:
    def test_creation(self):
        p = Position(x=3, y=7)
        assert p.x == 3
        assert p.y == 7

    def test_frozen(self):
        assert_model_frozen(Position(x=3, y=7), "x", 5)

    def test_equality(self):
        assert Position(x=3, y=7) == Position(x=3, y=7)

    def test_inequality(self):
        assert Position(x=3, y=7) != Position(x=3, y=8)

    def test_hashable(self):
        p = Position(x=3, y=7)
        assert {p: "value"}[Position(x=3, y=7)] == "value"
        assert len({Position(x=0, y=0), Position(x=0, y=0)}) == 1

    def test_serialization(self):
        p = Position(x=3, y=7)
        assert p.model_dump() == {"x": 3, "y": 7}

    def test_negative_coords_valid(self):
        p = Position(x=-1, y=-5)
        assert p.x == -1
        assert p.y == -5


class TestCellObservation:
    def test_creation(self):
        c = CellObservation(traversability=1.0, resource=0.5)
        assert c.traversability == 1.0
        assert c.resource == 0.5

    def test_frozen(self):
        assert_model_frozen(
            CellObservation(traversability=1.0,
                            resource=0.5), "traversability", 0.0
        )

    def test_boundary_zero(self):
        c = CellObservation(traversability=0.0, resource=0.0)
        assert c.traversability == 0.0
        assert c.resource == 0.0

    def test_boundary_one(self):
        c = CellObservation(traversability=1.0, resource=1.0)
        assert c.traversability == 1.0
        assert c.resource == 1.0

    def test_traversability_above_one_invalid(self):
        with pytest.raises(ValidationError):
            CellObservation(traversability=1.1, resource=0.5)

    def test_resource_negative_invalid(self):
        with pytest.raises(ValidationError):
            CellObservation(traversability=1.0, resource=-0.1)

    def test_serialization(self):
        c = CellObservation(traversability=1.0, resource=0.3)
        assert c.model_dump() == {"traversability": 1.0, "resource": 0.3}


class TestObservation:
    def test_creation(self, sample_observation: Observation):
        assert sample_observation.current is not None
        assert sample_observation.up is not None

    def test_frozen(self, sample_observation: Observation):
        assert_model_frozen(
            sample_observation, "current",
            CellObservation(traversability=0.0, resource=0.0),
        )

    def test_has_all_directions(self):
        fields = set(Observation.model_fields.keys())
        assert fields == {"current", "up", "down", "left", "right"}

    def test_to_vector_length(self, sample_observation: Observation):
        v = sample_observation.to_vector()
        assert len(v) == 10

    def test_to_vector_ordering(self):
        obs = Observation(
            current=CellObservation(traversability=1.0, resource=0.1),
            up=CellObservation(traversability=1.0, resource=0.2),
            down=CellObservation(traversability=0.0, resource=0.3),
            left=CellObservation(traversability=1.0, resource=0.4),
            right=CellObservation(traversability=0.0, resource=0.5),
        )
        expected = (1.0, 0.1, 1.0, 0.2, 0.0, 0.3, 1.0, 0.4, 0.0, 0.5)
        assert obs.to_vector() == expected

    def test_dimension(self, sample_observation: Observation):
        assert sample_observation.dimension == 10

    def test_serialization_roundtrip(self, sample_observation: Observation):
        dump = sample_observation.model_dump()
        reconstructed = Observation(**dump)
        assert reconstructed == sample_observation

    def test_json_roundtrip(self, sample_observation: Observation):
        json_str = sample_observation.model_dump_json()
        reconstructed = Observation.model_validate_json(json_str)
        assert reconstructed == sample_observation


class TestMemoryEntry:
    def test_creation(self, sample_observation: Observation):
        entry = MemoryEntry(timestep=0, observation=sample_observation)
        assert entry.timestep == 0
        assert entry.observation == sample_observation

    def test_creation_positive_timestep(self, sample_observation: Observation):
        entry = MemoryEntry(timestep=5, observation=sample_observation)
        assert entry.timestep == 5

    def test_frozen(self, sample_memory_entry: MemoryEntry):
        assert_model_frozen(sample_memory_entry, "timestep", 10)

    def test_negative_timestep_invalid(self, sample_observation: Observation):
        with pytest.raises(ValidationError):
            MemoryEntry(timestep=-1, observation=sample_observation)

    def test_has_exactly_two_fields(self):
        assert set(MemoryEntry.model_fields.keys()) == {
            "timestep", "observation"}

    def test_no_position_field(self):
        assert "position" not in MemoryEntry.model_fields

    def test_serialization_roundtrip(self, sample_memory_entry: MemoryEntry):
        dump = sample_memory_entry.model_dump()
        reconstructed = MemoryEntry(**dump)
        assert reconstructed == sample_memory_entry

    def test_json_roundtrip(self, sample_memory_entry: MemoryEntry):
        json_str = sample_memory_entry.model_dump_json()
        reconstructed = MemoryEntry.model_validate_json(json_str)
        assert reconstructed == sample_memory_entry


class TestMemoryState:
    def test_empty(self, empty_memory: MemoryState):
        assert len(empty_memory.entries) == 0
        assert empty_memory.capacity == 5

    def test_with_entries(self, sample_memory_entry: MemoryEntry):
        ms = MemoryState(entries=(sample_memory_entry,), capacity=5)
        assert len(ms.entries) == 1

    def test_at_capacity(self, sample_memory_entry: MemoryEntry):
        entries = tuple(sample_memory_entry for _ in range(3))
        ms = MemoryState(entries=entries, capacity=3)
        assert len(ms.entries) == 3

    def test_exceeds_capacity(self, sample_memory_entry: MemoryEntry):
        entries = tuple(sample_memory_entry for _ in range(4))
        with pytest.raises(ValidationError):
            MemoryState(entries=entries, capacity=3)

    def test_frozen(self, empty_memory: MemoryState):
        assert_model_frozen(empty_memory, "capacity", 10)

    def test_capacity_accessible(self, empty_memory: MemoryState):
        assert empty_memory.capacity == 5

    def test_entries_accessible(self, sample_memory_entry: MemoryEntry):
        ms = MemoryState(entries=(sample_memory_entry,), capacity=5)
        assert ms.entries[0] == sample_memory_entry

    def test_capacity_zero_invalid(self):
        with pytest.raises(ValidationError):
            MemoryState(capacity=0)

    def test_serialization(self, empty_memory: MemoryState):
        dump = empty_memory.model_dump()
        assert dump == {"entries": (), "capacity": 5}


class TestAgentState:
    def test_creation(self, empty_memory: MemoryState):
        state = AgentState(energy=50.0, memory_state=empty_memory)
        assert state.energy == 50.0
        assert state.memory_state == empty_memory

    def test_frozen(self, empty_memory: MemoryState):
        state = AgentState(energy=50.0, memory_state=empty_memory)
        assert_model_frozen(state, "energy", 30.0)

    def test_no_position_field(self):
        assert "position" not in AgentState.model_fields

    def test_energy_zero_valid(self, empty_memory: MemoryState):
        state = AgentState(energy=0.0, memory_state=empty_memory)
        assert state.energy == 0.0

    def test_energy_negative_invalid(self, empty_memory: MemoryState):
        with pytest.raises(ValidationError):
            AgentState(energy=-1.0, memory_state=empty_memory)

    def test_has_exactly_two_fields(self):
        assert set(AgentState.model_fields.keys()) == {
            "energy", "memory_state"}

    def test_serialization_roundtrip(self, empty_memory: MemoryState):
        state = AgentState(energy=50.0, memory_state=empty_memory)
        dump = state.model_dump()
        reconstructed = AgentState(**dump)
        assert reconstructed == state

    def test_json_roundtrip(self, empty_memory: MemoryState):
        state = AgentState(energy=50.0, memory_state=empty_memory)
        json_str = state.model_dump_json()
        reconstructed = AgentState.model_validate_json(json_str)
        assert reconstructed == state


class TestClipEnergy:
    def test_within_bounds(self):
        assert clip_energy(50.0, 100.0) == 50.0

    def test_below_zero(self):
        assert clip_energy(-10.0, 100.0) == 0.0

    def test_above_max(self):
        assert clip_energy(150.0, 100.0) == 100.0

    def test_at_zero(self):
        assert clip_energy(0.0, 100.0) == 0.0

    def test_at_max(self):
        assert clip_energy(100.0, 100.0) == 100.0
