"""Transition trace assertion helpers."""

from __future__ import annotations

import pytest

from axis_system_a import Action


def assert_valid_transition_trace(trace: object) -> None:
    """Composite validation of a TransitionTrace."""
    assert_trace_energy_consistent(trace)
    assert trace.energy_before >= 0.0  # type: ignore[attr-defined]
    assert trace.energy_after >= 0.0  # type: ignore[attr-defined]
    assert isinstance(trace.action, Action)  # type: ignore[attr-defined]


def assert_trace_energy_consistent(trace: object) -> None:
    """Assert energy_delta == energy_after - energy_before."""
    assert trace.energy_delta == pytest.approx(  # type: ignore[attr-defined]
        trace.energy_after - trace.energy_before  # type: ignore[attr-defined]
    )


def assert_trace_movement_consistent(trace: object) -> None:
    """Assert moved <-> position changed."""
    if trace.moved:  # type: ignore[attr-defined]
        # type: ignore[attr-defined]
        assert trace.position_before != trace.position_after
    else:
        # type: ignore[attr-defined]
        assert trace.position_before == trace.position_after
