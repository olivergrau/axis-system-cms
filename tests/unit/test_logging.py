"""Tests for the logging and observability module."""

import json
import logging
from unittest.mock import patch

import pytest

from axis_system_a import (
    Action,
    AgentSnapshot,
    AgentState,
    Cell,
    CellType,
    DecisionTrace,
    HungerDriveOutput,
    LoggingConfig,
    MemoryState,
    Position,
    RegenSummary,
    SelectionMode,
    TerminationReason,
    TransitionTrace,
    WorldSnapshot,
)
from axis_system_a.logging import (
    AxisLogger,
    format_episode_dict,
    format_episode_human,
    format_step_dict,
    format_step_human,
    render_decision_trace,
    render_transition_trace,
)
from axis_system_a.results import (
    EpisodeResult,
    EpisodeSummary,
    StepResult,
    compute_episode_summary,
)
from tests.fixtures.observation_fixtures import make_observation


# ---------------------------------------------------------------------------
# Local helpers (same pattern as test_results.py)
# ---------------------------------------------------------------------------


def _make_drive_output() -> HungerDriveOutput:
    return HungerDriveOutput(
        activation=0.5,
        action_contributions=(0.1, 0.1, 0.1, 0.1, 0.3, -0.05),
    )


def _make_decision_trace() -> DecisionTrace:
    return DecisionTrace(
        raw_contributions=(0.1, 0.1, 0.1, 0.1, 0.3, -0.05),
        admissibility_mask=(True, True, True, True, True, True),
        masked_contributions=(0.1, 0.1, 0.1, 0.1, 0.3, -0.05),
        probabilities=(0.15, 0.15, 0.15, 0.15, 0.2, 0.2),
        selected_action=Action.CONSUME,
        temperature=1.0,
        selection_mode=SelectionMode.ARGMAX,
    )


def _make_world_snapshot() -> WorldSnapshot:
    empty = Cell(cell_type=CellType.EMPTY, resource_value=0.0)
    return WorldSnapshot(
        grid=((empty,),), agent_position=Position(x=0, y=0),
        width=1, height=1,
    )


def _make_transition_trace(*, terminated: bool = False) -> TransitionTrace:
    ws = _make_world_snapshot()
    ms = MemoryState(capacity=5)
    return TransitionTrace(
        action=Action.CONSUME,
        position_before=Position(x=1, y=1),
        position_after=Position(x=1, y=1),
        moved=False,
        consumed=True,
        resource_consumed=0.5,
        energy_before=50.0,
        energy_after=53.0 if not terminated else 0.0,
        energy_delta=3.0 if not terminated else -50.0,
        memory_entries_before=0,
        memory_entries_after=1,
        terminated=terminated,
        world_before=ws,
        world_after_regen=ws,
        world_after_action=ws,
        agent_snapshot_before=AgentSnapshot(
            energy=50.0, position=Position(x=1, y=1),
            memory_entry_count=0, memory_timestep_range=None,
        ),
        agent_snapshot_after=AgentSnapshot(
            energy=53.0 if not terminated else 0.0,
            position=Position(x=1, y=1),
            memory_entry_count=1, memory_timestep_range=(0, 0),
        ),
        memory_state_before=ms,
        memory_state_after=MemoryState(entries=(), capacity=5),
        observation_before=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
        observation_after=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
        regen_summary=RegenSummary(cells_updated=0, regen_rate=0.0),
        termination_reason=(
            TerminationReason.ENERGY_DEPLETED if terminated else None
        ),
    )


def _make_step_result(
    *, timestep: int = 0, terminated: bool = False,
) -> StepResult:
    return StepResult(
        timestep=timestep,
        observation=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
        selected_action=Action.CONSUME,
        drive_output=_make_drive_output(),
        decision_result=_make_decision_trace(),
        transition_trace=_make_transition_trace(terminated=terminated),
        energy_before=50.0,
        energy_after=53.0 if not terminated else 0.0,
        terminated=terminated,
    )


def _make_episode_result() -> EpisodeResult:
    step0 = _make_step_result(timestep=0)
    step1 = _make_step_result(timestep=1, terminated=True)
    steps = (step0, step1)
    return EpisodeResult(
        steps=steps,
        total_steps=2,
        termination_reason=TerminationReason.ENERGY_DEPLETED,
        final_agent_state=AgentState(
            energy=0.0, memory_state=MemoryState(capacity=5),
        ),
        final_position=Position(x=1, y=1),
        final_observation=make_observation(0.5, 0.5, 0.5, 0.5, 0.5),
        summary=compute_episode_summary(steps),
    )


# ---------------------------------------------------------------------------
# Trace renderer tests
# ---------------------------------------------------------------------------


class TestRenderDecisionTrace:
    def test_compact_one_line(self):
        trace = _make_decision_trace()
        result = render_decision_trace(trace)
        assert "\n" not in result
        assert "CONSUME" in result
        assert "ARGMAX" in result.upper()

    def test_verbose_multiline(self):
        trace = _make_decision_trace()
        result = render_decision_trace(trace, verbose=True)
        assert "\n" in result
        assert "raw_contributions" in result
        assert "probabilities" in result
        assert "selected_action" in result


class TestRenderTransitionTrace:
    def test_compact_one_line(self):
        trace = _make_transition_trace()
        result = render_transition_trace(trace)
        assert "\n" not in result
        assert "moved=" in result
        assert "consumed=" in result

    def test_verbose_multiline(self):
        trace = _make_transition_trace()
        result = render_transition_trace(trace, verbose=True)
        assert "\n" in result
        assert "position:" in result
        assert "energy:" in result


# ---------------------------------------------------------------------------
# Step formatter tests
# ---------------------------------------------------------------------------


class TestFormatStepHuman:
    def test_compact_contains_key_fields(self):
        step = _make_step_result()
        result = format_step_human(step)
        assert "[STEP 0]" in result
        assert "pos=" in result
        assert "energy=" in result
        assert "CONSUME" in result

    def test_verbose_includes_traces(self):
        step = _make_step_result()
        result = format_step_human(step, verbose=True)
        assert "decision:" in result or "DecisionTrace:" in result
        assert "transition:" in result or "TransitionTrace:" in result


class TestFormatStepDict:
    def test_includes_traces_by_default(self):
        step = _make_step_result()
        d = format_step_dict(step)
        assert d["type"] == "step"
        assert "decision_result" in d
        assert "transition_trace" in d

    def test_excludes_decision_trace(self):
        step = _make_step_result()
        d = format_step_dict(step, include_decision_trace=False)
        assert "decision_result" not in d
        assert "transition_trace" in d

    def test_excludes_transition_trace(self):
        step = _make_step_result()
        d = format_step_dict(step, include_transition_trace=False)
        assert "decision_result" in d
        assert "transition_trace" not in d

    def test_excludes_both_traces(self):
        step = _make_step_result()
        d = format_step_dict(
            step, include_decision_trace=False,
            include_transition_trace=False,
        )
        assert "decision_result" not in d
        assert "transition_trace" not in d


# ---------------------------------------------------------------------------
# Episode formatter tests
# ---------------------------------------------------------------------------


class TestFormatEpisodeHuman:
    def test_contains_key_fields(self):
        episode = _make_episode_result()
        result = format_episode_human(episode)
        assert "[EPISODE]" in result
        assert "steps=2" in result
        assert "ENERGY_DEPLETED" in result


class TestFormatEpisodeDict:
    def test_structure(self):
        episode = _make_episode_result()
        d = format_episode_dict(episode)
        assert d["type"] == "episode"
        assert d["total_steps"] == 2
        assert d["termination_reason"] == "ENERGY_DEPLETED"
        assert "summary" in d
        assert "final_position" in d


# ---------------------------------------------------------------------------
# AxisLogger tests
# ---------------------------------------------------------------------------


class TestAxisLoggerDisabled:
    def test_does_nothing(self, caplog):
        logger = AxisLogger(LoggingConfig(enabled=False))
        step = _make_step_result()
        with caplog.at_level(logging.DEBUG, logger="axis_system_a"):
            logger.log_step(step)
        assert caplog.text == ""
        logger.close()


class TestAxisLoggerConsole:
    def test_console_output(self, caplog):
        config = LoggingConfig(
            enabled=True, console_enabled=True, jsonl_enabled=False,
        )
        logger = AxisLogger(config)
        step = _make_step_result()
        with caplog.at_level(logging.DEBUG, logger="axis_system_a"):
            logger.log_step(step)
        assert "[STEP 0]" in caplog.text
        logger.close()

    def test_episode_console_output(self, caplog):
        config = LoggingConfig(
            enabled=True, console_enabled=True, jsonl_enabled=False,
        )
        logger = AxisLogger(config)
        episode = _make_episode_result()
        with caplog.at_level(logging.DEBUG, logger="axis_system_a"):
            logger.log_episode(episode)
        assert "[EPISODE]" in caplog.text
        logger.close()


class TestAxisLoggerJsonl:
    def test_writes_steps(self, tmp_path):
        path = str(tmp_path / "out.jsonl")
        config = LoggingConfig(
            enabled=True, console_enabled=False,
            jsonl_enabled=True, jsonl_path=path,
        )
        logger = AxisLogger(config)
        logger.log_step(_make_step_result(timestep=0))
        logger.log_step(_make_step_result(timestep=1))
        logger.close()

        lines = (tmp_path / "out.jsonl").read_text().strip().split("\n")
        assert len(lines) == 2

    def test_step_structure(self, tmp_path):
        path = str(tmp_path / "out.jsonl")
        config = LoggingConfig(
            enabled=True, console_enabled=False,
            jsonl_enabled=True, jsonl_path=path,
        )
        logger = AxisLogger(config)
        logger.log_step(_make_step_result())
        logger.close()

        line = (tmp_path / "out.jsonl").read_text().strip()
        d = json.loads(line)
        assert d["type"] == "step"
        assert d["timestep"] == 0

    def test_episode_structure(self, tmp_path):
        path = str(tmp_path / "out.jsonl")
        config = LoggingConfig(
            enabled=True, console_enabled=False,
            jsonl_enabled=True, jsonl_path=path,
        )
        logger = AxisLogger(config)
        logger.log_episode(_make_episode_result())
        logger.close()

        line = (tmp_path / "out.jsonl").read_text().strip()
        d = json.loads(line)
        assert d["type"] == "episode"
        assert d["total_steps"] == 2


class TestAxisLoggerErrorHandling:
    def test_error_does_not_propagate(self, tmp_path):
        path = str(tmp_path / "out.jsonl")
        config = LoggingConfig(
            enabled=True, console_enabled=False,
            jsonl_enabled=True, jsonl_path=path,
        )
        logger = AxisLogger(config)
        # Force an error by closing the file prematurely
        logger._jsonl_file.close()
        # Should not raise
        logger.log_step(_make_step_result())
        logger.log_episode(_make_episode_result())
        logger.close()

    def test_close_idempotent(self, tmp_path):
        path = str(tmp_path / "out.jsonl")
        config = LoggingConfig(
            enabled=True, console_enabled=False,
            jsonl_enabled=True, jsonl_path=path,
        )
        logger = AxisLogger(config)
        logger.close()
        logger.close()  # second close should be safe


class TestAxisLoggerNoop:
    def test_noop_does_nothing(self, caplog):
        logger = AxisLogger.noop()
        step = _make_step_result()
        with caplog.at_level(logging.DEBUG, logger="axis_system_a"):
            logger.log_step(step)
            logger.log_episode(_make_episode_result())
        assert caplog.text == ""

    def test_noop_close_safe(self):
        logger = AxisLogger.noop()
        logger.close()
        logger.close()
