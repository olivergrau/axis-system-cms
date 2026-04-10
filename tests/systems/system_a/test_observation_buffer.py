"""WP-2.4 unit tests -- update_observation_buffer."""

from __future__ import annotations

from axis.systems.system_a.observation_buffer import update_observation_buffer
from axis.systems.system_a.types import (
    CellObservation,
    ObservationBuffer,
    Observation,
)


def _make_observation() -> Observation:
    cell = CellObservation(traversability=1.0, resource=0.0)
    return Observation(current=cell, up=cell, down=cell, left=cell, right=cell)


class TestObservationBuffer:
    """update_observation_buffer() unit tests."""

    def test_empty_buffer_append(self) -> None:
        mem = ObservationBuffer(entries=(), capacity=5)
        new_buffer = update_observation_buffer(mem, _make_observation(), timestep=0)
        assert len(new_buffer.entries) == 1
        assert new_buffer.entries[0].timestep == 0

    def test_buffer_ordering(self) -> None:
        mem = ObservationBuffer(entries=(), capacity=5)
        for t in range(3):
            mem = update_observation_buffer(mem, _make_observation(), timestep=t)
        assert mem.entries[0].timestep == 0
        assert mem.entries[1].timestep == 1
        assert mem.entries[2].timestep == 2

    def test_fifo_eviction(self) -> None:
        mem = ObservationBuffer(entries=(), capacity=2)
        for t in range(3):
            mem = update_observation_buffer(mem, _make_observation(), timestep=t)
        assert len(mem.entries) == 2
        assert mem.entries[0].timestep == 1  # oldest evicted
        assert mem.entries[1].timestep == 2

    def test_capacity_respected(self) -> None:
        mem = ObservationBuffer(entries=(), capacity=3)
        for t in range(5):
            mem = update_observation_buffer(mem, _make_observation(), timestep=t)
        assert len(mem.entries) == 3

    def test_returns_new_instance(self) -> None:
        mem = ObservationBuffer(entries=(), capacity=5)
        new_buffer = update_observation_buffer(mem, _make_observation(), timestep=0)
        assert new_buffer is not mem
        assert len(mem.entries) == 0  # original unchanged
        assert len(new_buffer.entries) == 1
