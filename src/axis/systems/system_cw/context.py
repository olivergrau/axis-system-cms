"""System C+W compact context encoding."""

from __future__ import annotations


def encode_context_cw(
    features: tuple[float, ...],
    *,
    resource_threshold: float = 0.5,
    novelty_threshold: float = 0.35,
    novelty_contrast_threshold: float = 0.15,
) -> int:
    """Encode the 10-D C+W feature vector into a compact 6-bit context."""
    center = features[0]
    neighbors = features[1:5]
    directional_novelty = features[5:9]
    local_mean_novelty = features[9]

    neighbor_mean = sum(neighbors) / 4.0
    best_neighbor = max(neighbors)
    peak_novelty = max(directional_novelty)
    novelty_contrast = peak_novelty - min(directional_novelty)

    bits = (
        center >= resource_threshold,
        neighbor_mean >= resource_threshold,
        best_neighbor >= resource_threshold,
        local_mean_novelty >= novelty_threshold,
        peak_novelty >= novelty_threshold,
        novelty_contrast >= novelty_contrast_threshold,
    )

    context = 0
    for index, flag in enumerate(bits):
        if flag:
            context |= 1 << (len(bits) - 1 - index)
    return context
