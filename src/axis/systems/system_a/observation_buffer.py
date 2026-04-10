"""System A observation buffer update function."""

from __future__ import annotations

from axis.systems.system_a.types import BufferEntry, ObservationBuffer, Observation


def update_observation_buffer(
    buffer: ObservationBuffer,
    observation: Observation,
    timestep: int,
) -> ObservationBuffer:
    """Append an observation as a new buffer entry with FIFO overflow.

    Creates a new BufferEntry from the given observation and timestep,
    appends it to the observation buffer, and drops the oldest entry if
    capacity is exceeded. Returns a new ObservationBuffer instance.
    """
    new_entry = BufferEntry(timestep=timestep, observation=observation)
    entries = buffer.entries + (new_entry,)
    if len(entries) > buffer.capacity:
        entries = entries[1:]
    return ObservationBuffer(entries=entries, capacity=buffer.capacity)
