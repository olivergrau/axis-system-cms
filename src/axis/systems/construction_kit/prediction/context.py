"""Context encoding -- C(y_t) -> s_t with binary quantization."""

from __future__ import annotations


def encode_context(
    features: tuple[float, ...],
    *,
    threshold: float = 0.5,
) -> int:
    """Encode predictive features into a discrete context index.

    Binary thresholding: each feature is mapped to 0 (below threshold)
    or 1 (at or above threshold). The 5-bit result is packed into an
    integer in [0, 31].

    Context index layout (MSB to LSB):
        bit 4: center, bit 3: up, bit 2: down, bit 1: left, bit 0: right

    Args:
        features: Predictive feature vector y_t (5 elements).
        threshold: Binary threshold (default 0.5).

    Returns:
        Integer context index in [0, 31].
    """
    context = 0
    for i, value in enumerate(features):
        if value >= threshold:
            context |= 1 << (len(features) - 1 - i)
    return context
