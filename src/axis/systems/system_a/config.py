"""System A configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from axis.systems.construction_kit.types.config import (
    AgentConfig,
    PolicyConfig,
    TransitionConfig,
)


class SystemAConfig(BaseModel):
    """Complete System A configuration.

    Parsed from the opaque ``system: dict[str, Any]`` in ExperimentConfig.
    """

    model_config = ConfigDict(frozen=True)

    agent: AgentConfig
    policy: PolicyConfig
    transition: TransitionConfig
