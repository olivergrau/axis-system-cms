"""AXIS System A — Core types and configuration."""

from axis_system_a.config import (
    AgentConfig,
    ExecutionConfig,
    GeneralConfig,
    LoggingConfig,
    PolicyConfig,
    SimulationConfig,
    TransitionConfig,
    WorldConfig,
)
from axis_system_a.drives import HungerDriveOutput, compute_hunger_drive
from axis_system_a.enums import Action, CellType, SelectionMode, TerminationReason
from axis_system_a.experiment import (
    ExperimentConfig,
    ExperimentResult,
    ExperimentSummary,
    ExperimentType,
    RunSummaryEntry,
    compute_experiment_summary,
    get_config_value,
    resolve_run_configs,
    set_config_value,
    variation_description,
)
from axis_system_a.experiment_executor import (
    ExperimentExecutor,
    execute_experiment,
)
from axis_system_a.logging import AxisLogger
from axis_system_a.memory import update_memory
from axis_system_a.observation import build_observation
from axis_system_a.policy import DecisionTrace, select_action
from axis_system_a.repository import (
    ExperimentMetadata,
    ExperimentRepository,
    ExperimentStatus,
    ExperimentStatusRecord,
    RunMetadata,
    RunStatus,
    RunStatusRecord,
)
from axis_system_a.results import (
    EpisodeResult,
    EpisodeStepRecord,
    EpisodeSummary,
    StepResult,
    compute_episode_summary,
)
from axis_system_a.run import (
    RunConfig,
    RunContext,
    RunExecutor,
    RunResult,
    RunSummary,
    compute_run_summary,
    execute_run,
    resolve_episode_seeds,
)
from axis_system_a.runner import episode_step, run_episode
from axis_system_a.snapshots import (
    AgentSnapshot,
    RegenSummary,
    WorldSnapshot,
    snapshot_agent,
    snapshot_world,
)
from axis_system_a.transition import TransitionStepResult, TransitionTrace, step
from axis_system_a.types import (
    AgentState,
    CellObservation,
    MemoryEntry,
    MemoryState,
    Observation,
    Position,
    clip_energy,
)
from axis_system_a.world import Cell, World, create_world

__all__ = [
    "Action",
    "AgentConfig",
    "AgentSnapshot",
    "AgentState",
    "AxisLogger",
    "Cell",
    "CellObservation",
    "CellType",
    "DecisionTrace",
    "EpisodeResult",
    "EpisodeStepRecord",
    "EpisodeSummary",
    "ExecutionConfig",
    "ExperimentConfig",
    "ExperimentExecutor",
    "ExperimentMetadata",
    "ExperimentRepository",
    "ExperimentResult",
    "ExperimentStatus",
    "ExperimentStatusRecord",
    "ExperimentSummary",
    "ExperimentType",
    "GeneralConfig",
    "HungerDriveOutput",
    "LoggingConfig",
    "MemoryEntry",
    "MemoryState",
    "Observation",
    "PolicyConfig",
    "Position",
    "RegenSummary",
    "RunConfig",
    "RunContext",
    "RunExecutor",
    "RunMetadata",
    "RunResult",
    "RunStatus",
    "RunStatusRecord",
    "RunSummary",
    "RunSummaryEntry",
    "SelectionMode",
    "SimulationConfig",
    "StepResult",
    "TerminationReason",
    "TransitionConfig",
    "TransitionStepResult",
    "TransitionTrace",
    "World",
    "WorldConfig",
    "WorldSnapshot",
    "build_observation",
    "clip_energy",
    "compute_episode_summary",
    "compute_experiment_summary",
    "compute_hunger_drive",
    "compute_run_summary",
    "create_world",
    "episode_step",
    "execute_experiment",
    "execute_run",
    "get_config_value",
    "resolve_episode_seeds",
    "resolve_run_configs",
    "run_episode",
    "select_action",
    "set_config_value",
    "snapshot_agent",
    "snapshot_world",
    "step",
    "update_memory",
    "variation_description",
]
