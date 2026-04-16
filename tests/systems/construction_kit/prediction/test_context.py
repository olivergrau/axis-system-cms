"""Tests for context encoding."""

from __future__ import annotations

import pytest

from axis.systems.construction_kit.prediction.context import encode_context


class TestEncodeContext:

    def test_all_zero_features(self) -> None:
        assert encode_context((0.0, 0.0, 0.0, 0.0, 0.0)) == 0

    def test_all_above_threshold(self) -> None:
        assert encode_context((0.8, 0.6, 0.9, 0.7, 0.5)) == 31  # 11111

    def test_only_center_above(self) -> None:
        """Center is bit 4 (MSB)."""
        assert encode_context((0.5, 0.0, 0.0, 0.0, 0.0)) == 0b10000  # 16

    def test_only_up_above(self) -> None:
        """Up is bit 3."""
        assert encode_context((0.0, 0.5, 0.0, 0.0, 0.0)) == 0b01000  # 8

    def test_only_down_above(self) -> None:
        """Down is bit 2."""
        assert encode_context((0.0, 0.0, 0.5, 0.0, 0.0)) == 0b00100  # 4

    def test_only_left_above(self) -> None:
        """Left is bit 1."""
        assert encode_context((0.0, 0.0, 0.0, 0.5, 0.0)) == 0b00010  # 2

    def test_only_right_above(self) -> None:
        """Right is bit 0 (LSB)."""
        assert encode_context((0.0, 0.0, 0.0, 0.0, 0.5)) == 0b00001  # 1

    def test_threshold_edge_exactly_at(self) -> None:
        """Exactly at threshold (0.5) maps to 1."""
        assert encode_context((0.5, 0.5, 0.5, 0.5, 0.5)) == 31

    def test_threshold_edge_just_below(self) -> None:
        """Just below threshold maps to 0."""
        assert encode_context((0.499, 0.499, 0.499, 0.499, 0.499)) == 0

    def test_custom_threshold(self) -> None:
        features = (0.3, 0.3, 0.3, 0.3, 0.3)
        assert encode_context(features, threshold=0.3) == 31
        assert encode_context(features, threshold=0.4) == 0

    def test_mixed_pattern(self) -> None:
        """Center and right above, others below -> 10001 = 17."""
        assert encode_context((0.8, 0.1, 0.2, 0.3, 0.6)) == 0b10001  # 17

    def test_result_range(self) -> None:
        """Result is always in [0, 31]."""
        for c in [0.0, 0.5, 1.0]:
            for u in [0.0, 0.5, 1.0]:
                ctx = encode_context((c, u, 0.0, 0.0, 0.0))
                assert 0 <= ctx <= 31
