"""General assertion helpers for tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from axis_system_a import Action


def assert_model_frozen(instance: object, field_name: str, value: object) -> None:
    """Assert that setting a field on a frozen Pydantic model raises ValidationError."""
    with pytest.raises(ValidationError):
        setattr(instance, field_name, value)


def assert_probabilities_sum_to_one(
    probabilities: tuple[float, ...], *, tol: float = 1e-9,
) -> None:
    """Assert the probability distribution sums to 1.0."""
    assert sum(probabilities) == pytest.approx(1.0, abs=tol)


def assert_probabilities_valid(probabilities: tuple[float, ...]) -> None:
    """Assert all probabilities >= 0 and sum to 1.0."""
    assert all(p >= 0.0 for p in probabilities)
    assert_probabilities_sum_to_one(probabilities)


def assert_energy_decreased(before: float, after: float) -> None:
    """Assert energy strictly decreased."""
    assert after < before


def assert_action_selected(decision_result: object, expected: Action) -> None:
    """Assert the selected action matches expected."""
    assert decision_result.selected_action == expected  # type: ignore[attr-defined]
