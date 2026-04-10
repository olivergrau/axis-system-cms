"""System A+W memory -- re-exports System A's memory update."""

from axis.systems.system_a.memory import update_memory

# System A+W uses the same memory update as System A.
# m_{t+1} = M(m_t, u_{t+1})
# FIFO bounded buffer with configurable capacity k.

__all__ = ["update_memory"]
