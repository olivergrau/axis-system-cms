"""Action score modulation from prediction-derived traces.

Provides:
- compute_modulation: single (context, action) modulation factor
- modulate_action_scores: batch modulation across all actions
"""

from axis.systems.construction_kit.modulation.modulation import (
    compute_modulation,
    modulate_action_scores,
)

__all__ = [
    "compute_modulation",
    "modulate_action_scores",
]
