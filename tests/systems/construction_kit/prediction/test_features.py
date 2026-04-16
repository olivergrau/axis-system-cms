"""Tests for predictive feature extraction."""

from __future__ import annotations

import pytest

from axis.systems.construction_kit.observation.types import CellObservation, Observation
from axis.systems.construction_kit.prediction.features import extract_predictive_features


def _obs(c: float, u: float, d: float, l: float, r: float) -> Observation:
    """Build an Observation with given resource values (traversability=1)."""
    def cell(res: float) -> CellObservation:
        return CellObservation(traversability=1.0, resource=res)
    return Observation(
        current=cell(c), up=cell(u), down=cell(d), left=cell(l), right=cell(r),
    )


class TestExtractPredictiveFeatures:

    def test_extracts_correct_order(self) -> None:
        obs = _obs(0.1, 0.2, 0.3, 0.4, 0.5)
        features = extract_predictive_features(obs)
        assert features == (0.1, 0.2, 0.3, 0.4, 0.5)

    def test_all_zeros(self) -> None:
        obs = _obs(0.0, 0.0, 0.0, 0.0, 0.0)
        assert extract_predictive_features(obs) == (0.0, 0.0, 0.0, 0.0, 0.0)

    def test_all_ones(self) -> None:
        obs = _obs(1.0, 1.0, 1.0, 1.0, 1.0)
        assert extract_predictive_features(obs) == (1.0, 1.0, 1.0, 1.0, 1.0)

    def test_returns_tuple_of_length_5(self) -> None:
        obs = _obs(0.5, 0.5, 0.5, 0.5, 0.5)
        result = extract_predictive_features(obs)
        assert isinstance(result, tuple)
        assert len(result) == 5

    def test_ignores_traversability(self) -> None:
        """Only resource values are extracted, not traversability."""
        cell_blocked = CellObservation(traversability=0.0, resource=0.7)
        cell_open = CellObservation(traversability=1.0, resource=0.3)
        obs = Observation(
            current=cell_blocked, up=cell_open, down=cell_blocked,
            left=cell_open, right=cell_blocked,
        )
        features = extract_predictive_features(obs)
        assert features == (0.7, 0.3, 0.7, 0.3, 0.7)
