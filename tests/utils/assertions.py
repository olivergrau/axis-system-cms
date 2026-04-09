"""Generic assertion helpers that do not depend on any axis domain types."""

from __future__ import annotations

import pytest


def assert_frozen(instance: object, field_name: str, value: object) -> None:
    """Assert that setting a field on a frozen Pydantic model raises."""
    with pytest.raises(Exception):
        setattr(instance, field_name, value)


def assert_valid_probability_distribution(
    probs: tuple[float, ...], *, tol: float = 1e-9
) -> None:
    """Assert all values >= 0 and sum to 1.0."""
    for p in probs:
        assert p >= 0.0, f"Negative probability: {p}"
    total = sum(probs)
    assert abs(total - 1.0) <= tol, f"Probabilities sum to {total}, expected 1.0"


def assert_dict_has_keys(d: dict, *keys: str) -> None:
    """Assert a dict contains all specified keys."""
    missing = [k for k in keys if k not in d]
    assert not missing, f"Dict missing keys: {missing}"


def assert_normalized_metric(value: float) -> None:
    """Assert a value is in [0.0, 1.0]."""
    assert 0.0 <= value <= 1.0, f"Value {value} not in [0.0, 1.0]"
