"""System B internal types -- agent state and scan result."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ScanResult(BaseModel):
    """Result of the most recent scan action."""

    model_config = ConfigDict(frozen=True)

    total_resource: float = 0.0
    cell_count: int = 0


class AgentState(BaseModel):
    """System B agent state: energy + last scan result."""

    model_config = ConfigDict(frozen=True)

    energy: float = Field(..., ge=0)
    last_scan: ScanResult = Field(default_factory=ScanResult)
