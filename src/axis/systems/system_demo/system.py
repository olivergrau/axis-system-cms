"""System Demo -- minimal system for workflow testing."""

from __future__ import annotations

from typing import Any

import numpy as np

from pydantic import BaseModel, ConfigDict
from axis.sdk.types import DecideResult, TransitionResult


class DemoState(BaseModel):
    """Minimal agent state: just a counter and energy."""

    model_config = ConfigDict(frozen=True)

    energy: float = 100.0
    step_count: int = 0


class DemoConfig(BaseModel):
    """Configuration for the demo system."""

    model_config = ConfigDict(frozen=True)

    initial_energy: float = 100.0
    max_energy: float = 100.0
    energy_per_step: float = 1.0
    temperature: float = 1.0


class SystemDemo:
    """Minimal system implementing SystemInterface for workflow testing."""

    def __init__(self, config: DemoConfig) -> None:
        self._config = config

    def system_type(self) -> str:
        return "system_demo"

    def action_space(self) -> tuple[str, ...]:
        return ("up", "down", "left", "right", "stay")

    def initialize_state(self) -> DemoState:
        return DemoState(energy=self._config.initial_energy)

    def vitality(self, agent_state: Any) -> float:
        return agent_state.energy / self._config.max_energy

    def decide(
        self,
        world_view: Any,
        agent_state: Any,
        rng: np.random.Generator,
    ) -> DecideResult:
        actions = self.action_space()
        # Simple softmax-like selection biased by temperature
        n = len(actions)
        logits = np.ones(n) / self._config.temperature
        probs = np.exp(logits) / np.sum(np.exp(logits))
        idx = rng.choice(n, p=probs)
        return DecideResult(
            action=actions[idx],
            decision_data={"step": agent_state.step_count, "probs": probs.tolist()},
        )

    def transition(
        self,
        agent_state: Any,
        action_outcome: Any,
        new_observation: Any,
    ) -> TransitionResult:
        new_energy = max(0.0, agent_state.energy - self._config.energy_per_step)
        new_state = DemoState(
            energy=new_energy,
            step_count=agent_state.step_count + 1,
        )
        terminated = new_energy <= 0.0
        return TransitionResult(
            new_state=new_state,
            trace_data={"energy": new_energy},
            terminated=terminated,
            termination_reason="energy_depleted" if terminated else None,
        )

    def action_handlers(self) -> dict[str, Any]:
        return {}

    def observe(self, world_view: Any, position: Any) -> Any:
        return {}

    def action_context(self) -> dict[str, Any]:
        return {}
