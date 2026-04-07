"""Minimal mock system for framework-only testing.

Implements SystemInterface with plain dicts (not Pydantic) to validate
that the framework truly treats agent state as opaque Any.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from axis.sdk.types import DecideResult, TransitionResult


class MockSystem:
    """Trivial system: always moves right, energy decreases by 1 per step.

    Terminates when energy reaches 0. Uses plain dicts for agent state.
    No custom action handlers (only base actions).
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg = config or {}
        self._initial_energy = cfg.get("initial_energy", 10.0)
        self._max_energy = cfg.get("max_energy", 10.0)
        self._energy_cost = cfg.get("energy_cost", 1.0)

    def system_type(self) -> str:
        return "mock"

    def action_space(self) -> tuple[str, ...]:
        return ("up", "down", "left", "right", "stay")

    def initialize_state(self) -> dict[str, Any]:
        return {"energy": self._initial_energy}

    def vitality(self, agent_state: Any) -> float:
        return agent_state["energy"] / self._max_energy

    def decide(
        self,
        world_view: Any,
        agent_state: Any,
        rng: np.random.Generator,
    ) -> DecideResult:
        return DecideResult(
            action="right",
            decision_data={"reason": "always_right"},
        )

    def observe(self, world_view: Any, position: Any) -> dict[str, Any]:
        return {"position": (position.x, position.y)}

    def transition(
        self,
        agent_state: Any,
        action_outcome: Any,
        new_observation: Any,
    ) -> TransitionResult:
        new_energy = max(0.0, agent_state["energy"] - self._energy_cost)
        return TransitionResult(
            new_state={"energy": new_energy},
            trace_data={
                "energy_before": agent_state["energy"],
                "energy_after": new_energy,
            },
            terminated=new_energy <= 0.0,
            termination_reason="energy_depleted" if new_energy <= 0.0 else None,
        )

    def action_handlers(self) -> dict[str, Any]:
        return {}

    def action_context(self) -> dict[str, Any]:
        return {}
