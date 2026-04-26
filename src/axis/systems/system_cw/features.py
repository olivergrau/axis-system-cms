"""System C+W predictive feature extraction."""

from __future__ import annotations

from axis.systems.construction_kit.drives.types import CuriosityDriveOutput
from axis.systems.construction_kit.observation.types import Observation


def extract_predictive_features_cw(
    observation: Observation,
    curiosity_output: CuriosityDriveOutput,
) -> tuple[float, ...]:
    """Assemble the shared C+W predictive feature vector."""
    mean_local_novelty = sum(curiosity_output.composite_novelty) / 4.0
    return (
        observation.current.resource,
        observation.up.resource,
        observation.down.resource,
        observation.left.resource,
        observation.right.resource,
        curiosity_output.composite_novelty[0],
        curiosity_output.composite_novelty[1],
        curiosity_output.composite_novelty[2],
        curiosity_output.composite_novelty[3],
        mean_local_novelty,
    )
