"""System A -- hunger-driven baseline agent."""

from axis.systems.system_a.actions import handle_consume
from axis.systems.system_a.config import SystemAConfig
from axis.systems.system_a.system import SystemA

__all__ = [
    "SystemA",
    "SystemAConfig",
    "handle_consume",
]
