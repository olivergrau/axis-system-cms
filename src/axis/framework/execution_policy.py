"""Execution policy types for AXIS experiment throughput control."""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict, Field


class TraceMode(str, enum.Enum):
    """Trace richness mode for experiment execution."""

    FULL = "full"
    LIGHT = "light"
    DELTA = "delta"


class ParallelismMode(str, enum.Enum):
    """Parallelization strategy for experiment execution."""

    SEQUENTIAL = "sequential"
    EPISODES = "episodes"
    RUNS = "runs"


class ExecutionPolicy(BaseModel):
    """Normalized execution policy interpreted by the framework runtime."""

    model_config = ConfigDict(frozen=True)

    trace_mode: TraceMode = TraceMode.FULL
    parallelism_mode: ParallelismMode = ParallelismMode.SEQUENTIAL
    max_workers: int = Field(default=1, ge=1)
