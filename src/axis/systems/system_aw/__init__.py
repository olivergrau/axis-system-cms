"""System A+W -- dual-drive agent with curiosity and world model."""

from axis.systems.system_aw.config import SystemAWConfig
from axis.systems.system_aw.system import SystemAW

__all__ = [
    "SystemAW",
    "SystemAWConfig",
]
