"""Fluent builder for MemoryState objects."""

from __future__ import annotations

from axis_system_a import MemoryEntry, MemoryState, Observation


class MemoryBuilder:
    """Fluent builder for constructing MemoryState objects in tests.

    Default: capacity=5, no entries.
    """

    def __init__(self) -> None:
        self._capacity = 5
        self._entries: list[MemoryEntry] = []

    def with_capacity(self, capacity: int) -> MemoryBuilder:
        self._capacity = capacity
        return self

    def with_entry(self, timestep: int, observation: Observation) -> MemoryBuilder:
        self._entries.append(MemoryEntry(
            timestep=timestep, observation=observation))
        return self

    def with_entries(self, entries: tuple[MemoryEntry, ...]) -> MemoryBuilder:
        self._entries.extend(entries)
        return self

    def build(self) -> MemoryState:
        return MemoryState(entries=tuple(self._entries), capacity=self._capacity)
