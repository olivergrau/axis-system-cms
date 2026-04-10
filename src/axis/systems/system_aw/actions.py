"""System A+W consume action -- re-exports System A's consume handler."""

from axis.systems.system_a.actions import handle_consume

# System A+W uses the same consume handler as System A.
# The energy dynamics are unchanged (Model Section 1.1).

__all__ = ["handle_consume"]
