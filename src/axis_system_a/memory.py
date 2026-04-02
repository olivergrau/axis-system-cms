"""Deterministic memory update for the baseline episodic memory system."""

from __future__ import annotations

from axis_system_a.types import MemoryEntry, MemoryState, Observation


def update_memory(
    memory: MemoryState,
    observation: Observation,
    timestep: int,
) -> MemoryState:
    """Append an observation as a new memory entry with FIFO overflow.

    Creates a new MemoryEntry from the given observation and timestep,
    appends it to the memory buffer, and drops the oldest entry if
    capacity is exceeded. Returns a new MemoryState instance.
    """
    new_entry = MemoryEntry(timestep=timestep, observation=observation)
    entries = memory.entries + (new_entry,)
    if len(entries) > memory.capacity:
        entries = entries[1:]
    return MemoryState(entries=entries, capacity=memory.capacity)
