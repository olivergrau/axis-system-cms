"""Tests for :mod:`axis.framework.logging` -- EpisodeLogger."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from axis.framework.config import LoggingConfig
from axis.framework.logging import EpisodeLogger
from axis.sdk.position import Position
from axis.sdk.snapshot import WorldSnapshot
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace
from axis.sdk.world_types import CellView


# ---------------------------------------------------------------------------
# Test data helpers
# ---------------------------------------------------------------------------

def _minimal_snapshot(pos: Position | None = None) -> WorldSnapshot:
    p = pos or Position(x=0, y=0)
    cell = CellView(cell_type="empty", resource_value=0.0)
    grid = ((cell,),)
    return WorldSnapshot(grid=grid, agent_position=p, width=1, height=1)


def _make_step(
    timestep: int = 0,
    action: str = "right",
    pos_before: tuple[int, int] = (0, 0),
    pos_after: tuple[int, int] = (1, 0),
    vitality_before: float = 0.90,
    vitality_after: float = 0.87,
    terminated: bool = False,
    termination_reason: str | None = None,
    decision_data: dict | None = None,
    trace_data: dict | None = None,
) -> BaseStepTrace:
    pb = Position(x=pos_before[0], y=pos_before[1])
    pa = Position(x=pos_after[0], y=pos_after[1])
    system_data: dict = {}
    if decision_data is not None:
        system_data["decision_data"] = decision_data
    if trace_data is not None:
        system_data["trace_data"] = trace_data
    return BaseStepTrace(
        timestep=timestep,
        action=action,
        world_before=_minimal_snapshot(pb),
        world_after=_minimal_snapshot(pa),
        agent_position_before=pb,
        agent_position_after=pa,
        vitality_before=vitality_before,
        vitality_after=vitality_after,
        terminated=terminated,
        termination_reason=termination_reason,
        system_data=system_data,
    )


def _make_episode(
    num_steps: int = 3,
    termination_reason: str = "energy_depleted",
    final_vitality: float = 0.0,
) -> BaseEpisodeTrace:
    steps = []
    for i in range(num_steps):
        terminated = i == num_steps - 1
        steps.append(_make_step(
            timestep=i,
            action="right",
            pos_before=(i, 0),
            pos_after=(i + 1, 0),
            vitality_before=round(1.0 - i * 0.1, 2),
            vitality_after=round(1.0 - (i + 1) * 0.1, 2),
            terminated=terminated,
            termination_reason=termination_reason if terminated else None,
            decision_data={"score": 1.5 + i},
            trace_data={"energy_after": 50.0 - i * 5},
        ))
    final_pos = Position(x=num_steps, y=0)
    return BaseEpisodeTrace(
        system_type="system_a",
        steps=tuple(steps),
        total_steps=num_steps,
        termination_reason=termination_reason,
        final_vitality=final_vitality,
        final_position=final_pos,
    )


# ---------------------------------------------------------------------------
# Disabled / no-op
# ---------------------------------------------------------------------------

class TestDisabledLogger:
    def test_no_console_output(self, capsys: pytest.CaptureFixture) -> None:
        logger = EpisodeLogger(LoggingConfig(enabled=False))
        logger.log_episode(_make_episode(), episode_index=1)
        assert capsys.readouterr().out == ""

    def test_no_file_created(self, tmp_path: Path) -> None:
        jsonl_path = tmp_path / "should-not-exist.jsonl"
        logger = EpisodeLogger(LoggingConfig(enabled=False))
        logger.log_episode(_make_episode(), episode_index=1)
        logger.close()
        assert not jsonl_path.exists()


# ---------------------------------------------------------------------------
# Console -- compact mode
# ---------------------------------------------------------------------------

class TestCompactConsole:
    def _config(self) -> LoggingConfig:
        return LoggingConfig(
            enabled=True,
            console_enabled=True,
            jsonl_enabled=False,
            verbosity="compact",
        )

    def test_step_format(self, capsys: pytest.CaptureFixture) -> None:
        step = _make_step(
            timestep=3, action="right",
            pos_before=(2, 0), pos_after=(3, 0),
            vitality_before=0.90, vitality_after=0.87,
        )
        logger = EpisodeLogger(self._config())
        logger.log_step(step, episode_index=1)
        out = capsys.readouterr().out
        assert "[E1 S003]" in out
        assert "action=right" in out
        assert "pos=(2,0)->(3,0)" in out
        assert "vitality=0.90->0.87" in out

    def test_episode_summary(self, capsys: pytest.CaptureFixture) -> None:
        trace = _make_episode(
            num_steps=3, termination_reason="energy_depleted")
        logger = EpisodeLogger(self._config())
        logger.log_episode(trace, episode_index=1)
        out = capsys.readouterr().out
        assert "[E1 DONE]" in out
        assert "steps=3" in out
        assert "terminated=energy_depleted" in out

    def test_no_decision_or_trace_data(self, capsys: pytest.CaptureFixture) -> None:
        trace = _make_episode()
        logger = EpisodeLogger(self._config())
        logger.log_episode(trace, episode_index=1)
        out = capsys.readouterr().out
        assert "decision:" not in out
        assert "transition:" not in out


# ---------------------------------------------------------------------------
# Console -- verbose mode
# ---------------------------------------------------------------------------

class TestVerboseConsole:
    def test_includes_decision_and_transition(
        self, capsys: pytest.CaptureFixture,
    ) -> None:
        config = LoggingConfig(
            enabled=True, console_enabled=True, jsonl_enabled=False,
            verbosity="verbose",
            include_decision_trace=True,
            include_transition_trace=True,
        )
        trace = _make_episode(num_steps=1)
        EpisodeLogger(config).log_episode(trace, episode_index=1)
        out = capsys.readouterr().out
        assert "decision:" in out
        assert "transition:" in out

    def test_respects_include_decision_false(
        self, capsys: pytest.CaptureFixture,
    ) -> None:
        config = LoggingConfig(
            enabled=True, console_enabled=True, jsonl_enabled=False,
            verbosity="verbose",
            include_decision_trace=False,
            include_transition_trace=True,
        )
        trace = _make_episode(num_steps=1)
        EpisodeLogger(config).log_episode(trace, episode_index=1)
        out = capsys.readouterr().out
        assert "decision:" not in out
        assert "transition:" in out

    def test_respects_include_transition_false(
        self, capsys: pytest.CaptureFixture,
    ) -> None:
        config = LoggingConfig(
            enabled=True, console_enabled=True, jsonl_enabled=False,
            verbosity="verbose",
            include_decision_trace=True,
            include_transition_trace=False,
        )
        trace = _make_episode(num_steps=1)
        EpisodeLogger(config).log_episode(trace, episode_index=1)
        out = capsys.readouterr().out
        assert "decision:" in out
        assert "transition:" not in out


# ---------------------------------------------------------------------------
# Console disabled
# ---------------------------------------------------------------------------

class TestConsoleDisabled:
    def test_no_stdout(self, capsys: pytest.CaptureFixture) -> None:
        config = LoggingConfig(
            enabled=True, console_enabled=False, jsonl_enabled=False,
        )
        trace = _make_episode()
        EpisodeLogger(config).log_episode(trace, episode_index=1)
        assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# JSONL output
# ---------------------------------------------------------------------------

class TestJsonlOutput:
    def _config(self, tmp_path: Path, verbosity: str = "compact") -> LoggingConfig:
        return LoggingConfig(
            enabled=True,
            console_enabled=False,
            jsonl_enabled=True,
            jsonl_path=str(tmp_path / "out.jsonl"),
            verbosity=verbosity,
        )

    def test_step_record_schema(self, tmp_path: Path) -> None:
        config = self._config(tmp_path)
        with EpisodeLogger(config) as logger:
            logger.log_step(_make_step(timestep=0), episode_index=1)
        lines = (tmp_path / "out.jsonl").read_text().strip().splitlines()
        record = json.loads(lines[0])
        assert record["type"] == "step"
        assert record["episode"] == 1
        assert record["timestep"] == 0
        assert record["action"] == "right"
        assert record["position_before"] == [0, 0]
        assert record["position_after"] == [1, 0]
        assert isinstance(record["vitality_before"], float)
        assert isinstance(record["terminated"], bool)

    def test_episode_summary_record(self, tmp_path: Path) -> None:
        config = self._config(tmp_path)
        with EpisodeLogger(config) as logger:
            logger.log_episode(_make_episode(num_steps=2), episode_index=1)
        lines = (tmp_path / "out.jsonl").read_text().strip().splitlines()
        # 2 step records + 1 summary
        assert len(lines) == 3
        summary = json.loads(lines[-1])
        assert summary["type"] == "episode_summary"
        assert summary["system_type"] == "system_a"
        assert summary["total_steps"] == 2
        assert summary["termination_reason"] == "energy_depleted"

    def test_compact_omits_trace_fields(self, tmp_path: Path) -> None:
        config = self._config(tmp_path, verbosity="compact")
        with EpisodeLogger(config) as logger:
            logger.log_step(
                _make_step(decision_data={"x": 1}, trace_data={"y": 2}),
                episode_index=1,
            )
        record = json.loads(
            (tmp_path / "out.jsonl").read_text().strip().splitlines()[0],
        )
        assert "decision_data" not in record
        assert "trace_data" not in record

    def test_verbose_includes_trace_fields(self, tmp_path: Path) -> None:
        config = self._config(tmp_path, verbosity="verbose")
        with EpisodeLogger(config) as logger:
            logger.log_step(
                _make_step(decision_data={"x": 1}, trace_data={"y": 2}),
                episode_index=1,
            )
        record = json.loads(
            (tmp_path / "out.jsonl").read_text().strip().splitlines()[0],
        )
        assert record["decision_data"] == {"x": 1}
        assert record["trace_data"] == {"y": 2}

    def test_verbose_respects_include_flags(self, tmp_path: Path) -> None:
        config = LoggingConfig(
            enabled=True, console_enabled=False,
            jsonl_enabled=True,
            jsonl_path=str(tmp_path / "out.jsonl"),
            verbosity="verbose",
            include_decision_trace=False,
            include_transition_trace=True,
        )
        with EpisodeLogger(config) as logger:
            logger.log_step(
                _make_step(decision_data={"x": 1}, trace_data={"y": 2}),
                episode_index=1,
            )
        record = json.loads(
            (tmp_path / "out.jsonl").read_text().strip().splitlines()[0],
        )
        assert "decision_data" not in record
        assert record["trace_data"] == {"y": 2}

    def test_append_mode(self, tmp_path: Path) -> None:
        path = tmp_path / "out.jsonl"
        path.write_text('{"existing": true}\n')
        config = self._config(tmp_path)
        with EpisodeLogger(config) as logger:
            logger.log_step(_make_step(), episode_index=1)
        lines = path.read_text().strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"existing": True}
        assert json.loads(lines[1])["type"] == "step"

    def test_disabled_no_file_created(self, tmp_path: Path) -> None:
        path = tmp_path / "no-file.jsonl"
        config = LoggingConfig(
            enabled=True, console_enabled=False,
            jsonl_enabled=False,
        )
        with EpisodeLogger(config) as logger:
            logger.log_step(_make_step(), episode_index=1)
        assert not path.exists()

    def test_parent_dirs_created(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "c" / "out.jsonl"
        config = LoggingConfig(
            enabled=True, console_enabled=False,
            jsonl_enabled=True, jsonl_path=str(nested),
        )
        with EpisodeLogger(config) as logger:
            logger.log_step(_make_step(), episode_index=1)
        assert nested.exists()


# ---------------------------------------------------------------------------
# Context manager / close
# ---------------------------------------------------------------------------

class TestLifecycle:
    def test_close_idempotent(self, tmp_path: Path) -> None:
        config = LoggingConfig(
            enabled=True, console_enabled=False,
            jsonl_enabled=True,
            jsonl_path=str(tmp_path / "out.jsonl"),
        )
        logger = EpisodeLogger(config)
        logger.close()
        logger.close()  # should not raise

    def test_context_manager_closes(self, tmp_path: Path) -> None:
        config = LoggingConfig(
            enabled=True, console_enabled=False,
            jsonl_enabled=True,
            jsonl_path=str(tmp_path / "out.jsonl"),
        )
        with EpisodeLogger(config) as logger:
            logger.log_step(_make_step(), episode_index=1)
        # File handle should be closed after exiting context
        assert logger._jsonl_file is None


# ---------------------------------------------------------------------------
# Zero-step episode
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_step_episode(self, capsys: pytest.CaptureFixture) -> None:
        trace = BaseEpisodeTrace(
            system_type="system_a",
            steps=(),
            total_steps=0,
            termination_reason="max_steps_reached",
            final_vitality=1.0,
            final_position=Position(x=0, y=0),
        )
        config = LoggingConfig(
            enabled=True, console_enabled=True, jsonl_enabled=False,
        )
        EpisodeLogger(config).log_episode(trace, episode_index=1)
        out = capsys.readouterr().out
        # Should only have the summary line, no step lines
        assert "[E1 DONE]" in out
        assert "[E1 S" not in out


# ---------------------------------------------------------------------------
# Integration with RunExecutor
# ---------------------------------------------------------------------------

class TestRunExecutorIntegration:
    def test_logging_produces_jsonl(self, tmp_path: Path) -> None:
        from axis.framework.config import (
            ExecutionConfig,
            FrameworkConfig,
            GeneralConfig,
        )
        from axis.framework.run import RunConfig, RunExecutor
        from axis.sdk.world_types import BaseWorldConfig
        from tests.builders.system_config_builder import SystemAConfigBuilder

        jsonl_path = tmp_path / "run.jsonl"
        config = RunConfig(
            system_type="system_a",
            system_config=SystemAConfigBuilder().build(),
            framework_config=FrameworkConfig(
                general=GeneralConfig(seed=42),
                execution=ExecutionConfig(max_steps=5),
                world=BaseWorldConfig(grid_width=3, grid_height=3),
                logging=LoggingConfig(
                    enabled=True,
                    console_enabled=False,
                    jsonl_enabled=True,
                    jsonl_path=str(jsonl_path),
                    verbosity="verbose",
                    include_decision_trace=True,
                    include_transition_trace=True,
                ),
            ),
            num_episodes=2,
            base_seed=42,
        )

        RunExecutor().execute(config)

        assert jsonl_path.exists()
        lines = jsonl_path.read_text().strip().splitlines()
        records = [json.loads(line) for line in lines]

        step_records = [r for r in records if r["type"] == "step"]
        summary_records = [
            r for r in records if r["type"] == "episode_summary"]

        # 2 episodes, each should have a summary
        assert len(summary_records) == 2
        # Each episode has at least 1 step
        assert len(step_records) >= 2
        # Verbose should include decision_data and trace_data
        assert "decision_data" in step_records[0]
        assert "trace_data" in step_records[0]
