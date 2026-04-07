"""System B -- scout agent with scan action implementing SystemInterface."""

from __future__ import annotations

from typing import Any

import numpy as np

from axis.sdk.actions import MOVEMENT_DELTAS
from axis.sdk.position import Position
from axis.sdk.types import DecideResult, TransitionResult
from axis.systems.system_b.config import SystemBConfig
from axis.systems.system_b.types import AgentState, ScanResult


class SystemB:
    """System B: scout agent with scan action.

    Implements SystemInterface. Navigates the grid using a scan action
    to detect nearby resources. Unlike System A's consume, scanning is
    non-mutating -- it reads but does not extract resources.

    The agent uses scan results to bias movement toward resource-rich
    areas. Energy decreases with each action; the agent terminates
    when energy reaches zero.
    """

    def __init__(self, config: SystemBConfig) -> None:
        self._config = config

    def system_type(self) -> str:
        """Return the system's unique type identifier."""
        return "system_b"

    def action_space(self) -> tuple[str, ...]:
        """Return the ordered tuple of action names."""
        return ("up", "down", "left", "right", "scan", "stay")

    def initialize_state(self) -> AgentState:
        """Create initial agent state from stored config."""
        return AgentState(energy=self._config.agent.initial_energy)

    def vitality(self, agent_state: Any) -> float:
        """Normalized vitality: energy / max_energy."""
        return agent_state.energy / self._config.agent.max_energy

    def decide(
        self,
        world_view: Any,
        agent_state: Any,
        rng: np.random.Generator,
    ) -> DecideResult:
        """Phase 1: observe neighborhood, compute weights, select action."""
        actions = self.action_space()
        n = len(actions)
        weights = [1.0] * n

        # Boost scan if we haven't scanned yet or last scan found nothing
        scan_idx = actions.index("scan")
        if agent_state.last_scan.total_resource == 0:
            weights[scan_idx] = self._config.policy.scan_bonus

        # Boost directions based on neighbor resources
        for i, direction in enumerate(("up", "down", "left", "right")):
            delta = MOVEMENT_DELTAS[direction]
            target = Position(
                x=world_view.agent_position.x + delta[0],
                y=world_view.agent_position.y + delta[1],
            )
            if (
                world_view.is_within_bounds(target)
                and world_view.is_traversable(target)
            ):
                cell = world_view.get_cell(target)
                weights[i] += cell.resource_value * 2.0
            else:
                weights[i] = 0.0  # inadmissible

        # Softmax selection
        beta = 1.0 / self._config.policy.temperature
        max_w = max(w for w in weights if w > 0)
        exp_w = [
            np.exp(beta * (w - max_w)) if w > 0 else 0.0
            for w in weights
        ]
        total = sum(exp_w)
        probs = [e / total for e in exp_w]

        if self._config.policy.selection_mode == "argmax":
            action_idx = probs.index(max(probs))
        else:
            action_idx = int(rng.choice(n, p=probs))

        return DecideResult(
            action=actions[action_idx],
            decision_data={
                "weights": weights,
                "probabilities": probs,
                "last_scan": agent_state.last_scan.model_dump(),
            },
        )

    def transition(
        self,
        agent_state: Any,
        action_outcome: Any,
        new_observation: Any,
    ) -> TransitionResult:
        """Phase 2: energy update, scan result update, termination check."""
        action = action_outcome.action
        tc = self._config.transition

        # Determine energy cost
        if action in MOVEMENT_DELTAS:
            cost = tc.move_cost
        elif action == "scan":
            cost = tc.scan_cost
        else:
            cost = tc.stay_cost

        new_energy = max(0.0, min(
            agent_state.energy - cost,
            self._config.agent.max_energy,
        ))

        # Update scan result if this was a scan action
        if action == "scan":
            last_scan = ScanResult(
                total_resource=action_outcome.resource_consumed,
                cell_count=9,  # 3x3 neighborhood
            )
        else:
            last_scan = agent_state.last_scan

        new_state = AgentState(energy=new_energy, last_scan=last_scan)
        terminated = new_energy <= 0.0

        return TransitionResult(
            new_state=new_state,
            trace_data={
                "energy_before": agent_state.energy,
                "energy_after": new_energy,
                "energy_delta": new_energy - agent_state.energy,
                "action_cost": cost,
                "scan_total": last_scan.total_resource,
            },
            terminated=terminated,
            termination_reason="energy_depleted" if terminated else None,
        )

    def observe(self, world_view: Any, position: Any) -> dict[str, Any]:
        """Produce a minimal observation: just the position."""
        return {"x": position.x, "y": position.y}

    def action_handlers(self) -> dict[str, Any]:
        """Return custom action handlers for ActionRegistry registration."""
        from axis.systems.system_b.actions import handle_scan

        return {"scan": handle_scan}

    def action_context(self) -> dict[str, Any]:
        """Return context dict for System B's action handlers."""
        return {"scan_radius": 1}

    @property
    def config(self) -> SystemBConfig:
        """Access the parsed system config."""
        return self._config
