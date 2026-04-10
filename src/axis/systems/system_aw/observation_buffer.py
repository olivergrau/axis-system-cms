"""System A+W observation buffer -- re-exports System A's observation buffer update."""

from axis.systems.system_a.observation_buffer import update_observation_buffer

# System A+W uses the same observation buffer update as System A.
# m_{t+1} = M(m_t, u_{t+1})
# FIFO bounded buffer with configurable capacity k.

__all__ = ["update_observation_buffer"]
