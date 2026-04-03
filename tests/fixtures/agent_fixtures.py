"""Agent state fixtures."""

from __future__ import annotations

import pytest

from axis_system_a import AgentState, MemoryEntry, MemoryState
from tests.builders.agent_state_builder import AgentStateBuilder


@pytest.fixture
def default_agent() -> AgentState:
    """Agent with energy=50.0 and empty memory (capacity=5)."""
    return AgentStateBuilder().build()


@pytest.fixture
def default_agent_state() -> AgentState:
    """Alias for default_agent (backward compat)."""
    return AgentStateBuilder().build()


@pytest.fixture
def full_energy_agent() -> AgentState:
    """Agent with energy=100.0 and empty memory (capacity=5)."""
    return AgentStateBuilder().with_energy(100.0).build()


@pytest.fixture
def low_energy_agent() -> AgentState:
    """Agent with energy=2.0 and empty memory (capacity=5)."""
    return AgentStateBuilder().with_energy(2.0).build()


@pytest.fixture
def empty_memory() -> MemoryState:
    """Empty MemoryState with capacity=5."""
    return MemoryState(capacity=5)


@pytest.fixture
def sample_memory_entry(sample_observation) -> MemoryEntry:
    """MemoryEntry at timestep 0 with sample_observation."""
    return MemoryEntry(timestep=0, observation=sample_observation)
