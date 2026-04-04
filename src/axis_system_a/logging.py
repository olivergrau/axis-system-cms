"""Logging and observability layer for AXIS System A.

Provides human-readable console output and machine-readable JSONL output
by consuming WP8 structured results. This module is purely passive —
it never modifies system state, and logging failures never crash execution.
"""

from __future__ import annotations

import json
import logging
from typing import IO

from axis_system_a.config import LoggingConfig
from axis_system_a.policy import DecisionTrace
from axis_system_a.results import EpisodeResult, StepResult
from axis_system_a.transition import TransitionTrace

_logger = logging.getLogger("axis_system_a")


# ---------------------------------------------------------------------------
# Trace renderers
# ---------------------------------------------------------------------------


def render_decision_trace(trace: DecisionTrace, *, verbose: bool = False) -> str:
    """Render a DecisionTrace as a human-readable string."""
    if verbose:
        lines = [
            f"  raw_contributions: {trace.raw_contributions}",
            f"  admissibility_mask: {trace.admissibility_mask}",
            f"  masked_contributions: {trace.masked_contributions}",
            f"  probabilities: {trace.probabilities}",
            f"  selected_action: {trace.selected_action.name}",
            f"  temperature: {trace.temperature}",
            f"  selection_mode: {trace.selection_mode.value}",
        ]
        return "DecisionTrace:\n" + "\n".join(lines)
    return (
        f"decision: action={trace.selected_action.name} "
        f"mode={trace.selection_mode.value} temp={trace.temperature}"
    )


def render_transition_trace(
    trace: TransitionTrace, *, verbose: bool = False
) -> str:
    """Render a TransitionTrace as a human-readable string."""
    if verbose:
        lines = [
            f"  action: {trace.action.name}",
            f"  position: {trace.position_before} -> {trace.position_after}",
            f"  moved: {trace.moved}",
            f"  consumed: {trace.consumed}",
            f"  resource_consumed: {trace.resource_consumed}",
            f"  energy: {trace.energy_before} -> {trace.energy_after} "
            f"(delta={trace.energy_delta})",
            f"  terminated: {trace.terminated}",
        ]
        return "TransitionTrace:\n" + "\n".join(lines)
    return (
        f"transition: moved={trace.moved} consumed={trace.consumed} "
        f"energy_delta={trace.energy_delta:+.2f}"
    )


# ---------------------------------------------------------------------------
# Step formatters
# ---------------------------------------------------------------------------


def format_step_human(step: StepResult, *, verbose: bool = False) -> str:
    """Format a StepResult as a human-readable string.

    Compact: single line with key fields.
    Verbose: includes trace renderings.
    """
    pos = step.transition_trace.position_after
    line = (
        f"[STEP {step.timestep}] "
        f"pos=({pos.x},{pos.y}) "
        f"energy={step.energy_before:.1f}\u2192{step.energy_after:.1f} "
        f"action={step.selected_action.name} "
        f"moved={step.transition_trace.moved}"
    )
    if verbose:
        line += "\n  " + render_decision_trace(step.decision_result)
        line += "\n  " + render_transition_trace(step.transition_trace)
    return line


def format_step_dict(
    step: StepResult,
    *,
    include_decision_trace: bool = True,
    include_transition_trace: bool = True,
) -> dict:
    """Convert a StepResult to a dict for JSONL serialization."""
    d = step.to_dict()
    if not include_decision_trace:
        d.pop("decision_result", None)
    if not include_transition_trace:
        d.pop("transition_trace", None)
    d["type"] = "step"
    return d


# ---------------------------------------------------------------------------
# Episode formatters
# ---------------------------------------------------------------------------


def format_episode_human(episode: EpisodeResult) -> str:
    """Format an EpisodeResult as a human-readable summary string."""
    s = episode.summary
    return (
        f"[EPISODE] steps={episode.total_steps} "
        f"terminated={episode.termination_reason.name} "
        f"final_energy={episode.final_agent_state.energy:.1f} "
        f"mean_energy={s.mean_energy:.1f} "
        f"consumes={s.total_consume_events}"
    )


def format_episode_dict(episode: EpisodeResult) -> dict:
    """Convert episode metadata + summary to a dict for JSONL serialization."""
    return {
        "type": "episode",
        "total_steps": episode.total_steps,
        "termination_reason": episode.termination_reason.name,
        "final_energy": episode.final_agent_state.energy,
        "final_position": {
            "x": episode.final_position.x,
            "y": episode.final_position.y,
        },
        "summary": episode.summary.model_dump(mode="python"),
    }


# ---------------------------------------------------------------------------
# AxisLogger
# ---------------------------------------------------------------------------


class AxisLogger:
    """Passive logging facade for AXIS episode execution.

    Consumes WP8 structured results and produces console and/or JSONL output.
    All public methods catch exceptions internally — logging failures
    never propagate to the caller.
    """

    def __init__(self, config: LoggingConfig) -> None:
        self._config = config
        self._jsonl_file: IO[str] | None = None
        self._console_handler: logging.Handler | None = None

        if config.enabled and config.console_enabled:
            if not _logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter("%(message)s"))
                _logger.addHandler(handler)
                self._console_handler = handler
            _logger.setLevel(logging.INFO)

        if config.enabled and config.jsonl_enabled and config.jsonl_path:
            try:
                self._jsonl_file = open(config.jsonl_path, "w")  # noqa: SIM115
            except Exception:
                self._jsonl_file = None

    def log_step(self, step: StepResult) -> None:
        """Log a single step result."""
        if not self._config.enabled:
            return
        try:
            self._log_step_impl(step)
        except Exception:
            pass  # logging must never crash execution

    def log_episode(self, episode: EpisodeResult) -> None:
        """Log an episode result."""
        if not self._config.enabled:
            return
        try:
            self._log_episode_impl(episode)
        except Exception:
            pass  # logging must never crash execution

    def close(self) -> None:
        """Close any open file handles and remove handlers. Idempotent."""
        try:
            if self._jsonl_file is not None:
                self._jsonl_file.close()
                self._jsonl_file = None
        except Exception:
            self._jsonl_file = None
        try:
            if self._console_handler is not None:
                _logger.removeHandler(self._console_handler)
                self._console_handler = None
        except Exception:
            self._console_handler = None

    @staticmethod
    def noop() -> AxisLogger:
        """Create a no-op logger that does nothing."""
        return AxisLogger(LoggingConfig(enabled=False))

    # -- private --

    def _log_step_impl(self, step: StepResult) -> None:
        verbose = self._config.verbosity == "verbose"

        if self._config.console_enabled:
            msg = format_step_human(step, verbose=verbose)
            _logger.info(msg)

        if self._jsonl_file is not None:
            d = format_step_dict(
                step,
                include_decision_trace=self._config.include_decision_trace,
                include_transition_trace=self._config.include_transition_trace,
            )
            self._jsonl_file.write(json.dumps(d, default=str) + "\n")

    def _log_episode_impl(self, episode: EpisodeResult) -> None:
        if self._config.console_enabled:
            msg = format_episode_human(episode)
            _logger.info(msg)

        if self._jsonl_file is not None:
            d = format_episode_dict(episode)
            self._jsonl_file.write(json.dumps(d, default=str) + "\n")
            self._jsonl_file.flush()
