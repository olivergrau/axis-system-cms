"""Experimentation Framework -- execution, persistence, config, CLI."""

from axis.framework.config import (
    ExperimentConfig,
    ExperimentType,
    ExecutionConfig,
    FrameworkConfig,
    GeneralConfig,
    LoggingConfig,
    extract_framework_config,
    get_config_value,
    parse_parameter_path,
    set_config_value,
)
from axis.framework.execution_policy import (
    ExecutionPolicy,
    ParallelismMode,
    TraceMode,
)
from axis.framework.execution_results import (
    DeltaRunResult,
    LightEpisodeResult,
    LightRunResult,
)
from axis.framework.experiment import (
    ExperimentExecutor,
    ExperimentResult,
    ExperimentSummary,
    RunSummaryEntry,
    compute_experiment_summary,
    execute_experiment,
    is_run_complete,
    resolve_run_configs,
    resume_experiment,
    variation_description,
)
from axis.framework.logging import EpisodeLogger
from axis.framework.persistence import (
    ExperimentMetadata,
    ExperimentRepository,
    ExperimentStatus,
    ExperimentStatusRecord,
    RunMetadata,
    RunStatus,
    RunStatusRecord,
)
from axis.framework.registry import (
    SystemFactory,
    _clear_system_registry,
    create_system,
    get_system_factory,
    register_system,
    registered_system_types,
)
from axis.framework.run import (
    RunConfig,
    RunExecutor,
    RunResult,
    RunSummary,
    compute_run_summary,
    resolve_episode_seeds,
)
from axis.framework.runner import (
    run_episode,
    setup_episode,
)

__all__ = [
    "GeneralConfig",
    "ExecutionConfig",
    "ExecutionPolicy",
    "LoggingConfig",
    "ParallelismMode",
    "TraceMode",
    "FrameworkConfig",
    "ExperimentType",
    "ExperimentConfig",
    "extract_framework_config",
    "parse_parameter_path",
    "get_config_value",
    "set_config_value",
    # WP-3.1: System registry
    "SystemFactory",
    "_clear_system_registry",
    "create_system",
    "get_system_factory",
    "register_system",
    "registered_system_types",
    # WP-3.2: Episode runner
    "run_episode",
    "setup_episode",
    # WP-3.3: Run executor
    "RunConfig",
    "RunExecutor",
    "RunResult",
    "DeltaRunResult",
    "LightEpisodeResult",
    "LightRunResult",
    "RunSummary",
    "compute_run_summary",
    "resolve_episode_seeds",
    # WP-3.3: Experiment executor
    "ExperimentExecutor",
    "ExperimentResult",
    "ExperimentSummary",
    "RunSummaryEntry",
    "compute_experiment_summary",
    "resolve_run_configs",
    "variation_description",
    "execute_experiment",
    "resume_experiment",
    "is_run_complete",
    # WP-3.4: Persistence
    "ExperimentRepository",
    "ExperimentStatus",
    "ExperimentStatusRecord",
    "ExperimentMetadata",
    "RunStatus",
    "RunStatusRecord",
    "RunMetadata",
    # Logging runtime
    "EpisodeLogger",
]
