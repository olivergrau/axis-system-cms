"""System A+W sensor -- re-exports System A's Von Neumann sensor."""

from axis.systems.system_a.sensor import SystemASensor

# System A+W uses the same sensor as System A.
# The observation model is unchanged (Model Section 1.1):
#   u_t = S(world_view, position)
# producing a 10-dimensional Observation vector.

SystemAWSensor = SystemASensor

__all__ = ["SystemAWSensor"]
