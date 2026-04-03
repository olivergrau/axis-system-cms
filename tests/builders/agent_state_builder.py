"""Fluent builder for AgentState objects."""

from __future__ import annotations

from axis_system_a import AgentState, MemoryEntry, MemoryState


class AgentStateBuilder:
    """Fluent builder for constructing AgentState objects in tests.

    Default: energy=50.0, memory capacity=5, empty memory.
    """

    def __init__(self) -> None:
        self._energy = 50.0
        self._capacity = 5
        self._entries: tuple[MemoryEntry, ...] = ()

    def with_energy(self, energy: float) -> AgentStateBuilder:
        self._energy = energy
        return self

    def with_memory_capacity(self, capacity: int) -> AgentStateBuilder:
        self._capacity = capacity
        return self

    def with_empty_memory(self) -> AgentStateBuilder:
        self._entries = ()
        return self

    def with_memory_entries(self, entries: tuple[MemoryEntry, ...]) -> AgentStateBuilder:
        self._entries = entries
        return self

    def build(self) -> AgentState:
        return AgentState(
            energy=self._energy,
            memory_state=MemoryState(
                entries=self._entries, capacity=self._capacity),
        )
