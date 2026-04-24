"""Episode logging runtime.

Consumes :class:`~axis.framework.config.LoggingConfig` to produce
human-readable console output and/or machine-readable JSONL files
from episode traces.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import IO

from axis.framework.config import LoggingConfig
from axis.framework.execution_policy import TraceMode
from axis.framework.execution_results import LightEpisodeResult
from axis.sdk.trace import BaseEpisodeTrace, BaseStepTrace, DeltaEpisodeTrace


class EpisodeLogger:
    """Logs episode step traces to console and/or JSONL file.

    Use as a context manager to ensure the JSONL file is closed::

        with EpisodeLogger(config) as logger:
            for ep_idx, trace in enumerate(traces, 1):
                logger.log_episode(trace, ep_idx)
    """

    def __init__(self, config: LoggingConfig, *, trace_mode: TraceMode = TraceMode.FULL) -> None:
        self._config = config
        self._trace_mode = trace_mode
        self._noop = not config.enabled
        self._jsonl_file: IO[str] | None = None

        if self._noop:
            return

        if config.jsonl_enabled:
            path = Path(config.jsonl_path)  # type: ignore[arg-type]
            path.parent.mkdir(parents=True, exist_ok=True)
            self._jsonl_file = open(path, "a")  # noqa: SIM115

    # -- Context manager -----------------------------------------------------

    def __enter__(self) -> EpisodeLogger:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._jsonl_file is not None:
            self._jsonl_file.close()
            self._jsonl_file = None

    # -- Public API ----------------------------------------------------------

    def log_episode(
        self,
        trace: BaseEpisodeTrace | LightEpisodeResult | DeltaEpisodeTrace,
        episode_index: int,
    ) -> None:
        """Log every step in *trace* followed by an episode summary."""
        if self._noop:
            return
        if self._config.console_enabled:
            self._print_episode_start(trace, episode_index)
        if isinstance(trace, BaseEpisodeTrace):
            for step in trace.steps:
                self.log_step(step, episode_index)
        self.log_episode_summary(trace, episode_index)

    def log_step(self, step: BaseStepTrace, episode_index: int) -> None:
        if self._noop:
            return

        cfg = self._config

        if cfg.console_enabled:
            self._print_step(step, episode_index)

        if self._jsonl_file is not None:
            self._write_step_jsonl(step, episode_index)

    def log_episode_summary(
        self,
        trace: BaseEpisodeTrace | LightEpisodeResult | DeltaEpisodeTrace,
        episode_index: int,
    ) -> None:
        if self._noop:
            return

        cfg = self._config

        if cfg.console_enabled:
            self._print_episode_summary(trace, episode_index)

        if self._jsonl_file is not None:
            self._write_episode_summary_jsonl(trace, episode_index)

    # -- Console formatting --------------------------------------------------

    def _print_episode_start(
        self,
        trace: BaseEpisodeTrace | LightEpisodeResult | DeltaEpisodeTrace,
        ep: int,
    ) -> None:
        print(
            f"[E{ep} START] "
            f"steps={trace.total_steps}"
        )

    def _print_step(self, step: BaseStepTrace, ep: int) -> None:
        cfg = self._config
        pb = step.agent_position_before
        pa = step.agent_position_after
        line = (
            f"[E{ep} S{step.timestep:03d}] "
            f"action={step.action}  "
            f"pos=({pb.x},{pb.y})->({pa.x},{pa.y})  "
            f"vitality={step.vitality_before:.2f}->{step.vitality_after:.2f}"
        )
        print(line)

        if cfg.verbosity == "verbose":
            if cfg.include_decision_trace:
                dd = step.system_data.get("decision_data")
                if dd is not None:
                    self._print_structured_block("Decision", dd)
            if cfg.include_transition_trace:
                td = step.system_data.get("trace_data")
                if td is not None:
                    self._print_structured_block("Transition", td)

    def _print_structured_block(self, label: str, data: object) -> None:
        print(f"  {label}:")
        rendered = json.dumps(data, default=str, indent=2)
        for line in rendered.splitlines():
            print(f"    {line}")

    def _print_episode_summary(
        self,
        trace: BaseEpisodeTrace | LightEpisodeResult | DeltaEpisodeTrace,
        ep: int,
    ) -> None:
        fp = trace.final_position
        print(
            f"[E{ep} DONE] "
            f"steps={trace.total_steps}  "
            f"terminated={trace.termination_reason}  "
            f"final_vitality={trace.final_vitality:.2f}  "
            f"final_pos=({fp.x},{fp.y})"
        )

    # -- JSONL formatting ----------------------------------------------------

    def _write_step_jsonl(self, step: BaseStepTrace, ep: int) -> None:
        cfg = self._config
        record: dict = {
            "type": "step",
            "episode": ep,
            "timestep": step.timestep,
            "action": step.action,
            "position_before": [
                step.agent_position_before.x,
                step.agent_position_before.y,
            ],
            "position_after": [
                step.agent_position_after.x,
                step.agent_position_after.y,
            ],
            "vitality_before": step.vitality_before,
            "vitality_after": step.vitality_after,
            "terminated": step.terminated,
            "termination_reason": step.termination_reason,
        }

        if cfg.verbosity == "verbose":
            if cfg.include_decision_trace:
                record["decision_data"] = step.system_data.get("decision_data")
            if cfg.include_transition_trace:
                record["trace_data"] = step.system_data.get("trace_data")

        assert self._jsonl_file is not None
        self._jsonl_file.write(json.dumps(record, default=str) + "\n")
        self._jsonl_file.flush()

    def _write_episode_summary_jsonl(
        self,
        trace: BaseEpisodeTrace | LightEpisodeResult | DeltaEpisodeTrace,
        ep: int,
    ) -> None:
        record = {
            "type": "episode_summary",
            "episode": ep,
            "total_steps": trace.total_steps,
            "termination_reason": trace.termination_reason,
            "final_vitality": trace.final_vitality,
            "final_position": [trace.final_position.x, trace.final_position.y],
        }
        if isinstance(trace, BaseEpisodeTrace):
            record["system_type"] = trace.system_type
        else:
            record["result_type"] = trace.result_type
        assert self._jsonl_file is not None
        self._jsonl_file.write(json.dumps(record, default=str) + "\n")
        self._jsonl_file.flush()
