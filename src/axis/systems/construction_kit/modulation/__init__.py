"""Action score modulation from prediction-derived traces.

Provides:
- compute_modulation: single (context, action) modulation factor
- compute_prediction_bias: bounded additive prediction correction
- describe_action_modulation: structured modulation details
- modulate_action_scores: batch modulation across all actions
"""

from axis.systems.construction_kit.modulation.modulation import (
    compute_modulation,
    compute_prediction_bias,
    describe_action_modulation,
    modulate_action_scores,
)

__all__ = [
    "compute_modulation",
    "compute_prediction_bias",
    "describe_action_modulation",
    "modulate_action_scores",
]
