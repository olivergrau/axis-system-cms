"""Integration tests for the logging and observability layer.

Validates: non-interference with results, deterministic JSONL output,
round-trip JSON validity, and resilience to logging failures.
"""

from __future__ import annotations

import json

from axis_system_a import LoggingConfig, TerminationReason
from axis_system_a.runner import run_episode
from tests.builders.world_builder import WorldBuilder
from tests.fixtures.scenario_fixtures import make_config


def _resource_world():
    return WorldBuilder().with_all_food(0.8).with_food(1, 1, 0.5).build()


def _empty_world():
    return WorldBuilder().build()


def _short_config(**extra_overrides):
    overrides = {
        "world": {"grid_width": 3, "grid_height": 3},
        "agent": {"initial_energy": 5.0, "max_energy": 100.0,
                  "memory_capacity": 5},
        "execution": {"max_steps": 20},
    }
    overrides.update(extra_overrides)
    return make_config(overrides=overrides)


class TestLoggingNonInterference:
    def test_results_identical_with_and_without_logging(self):
        """Logging must not alter episode results."""
        config_no_log = _short_config(
            logging={"enabled": False},
        )
        config_with_log = _short_config(
            logging={"enabled": True, "console_enabled": False,
                     "jsonl_enabled": False},
        )
        world1 = _empty_world()
        world2 = _empty_world()
        r1 = run_episode(config_no_log, world1)
        r2 = run_episode(config_with_log, world2)

        assert r1.total_steps == r2.total_steps
        assert r1.termination_reason == r2.termination_reason
        assert r1.final_agent_state == r2.final_agent_state
        assert r1.summary == r2.summary


class TestJsonlOutput:
    def test_deterministic_output(self, tmp_path):
        """Same seed must produce byte-identical JSONL."""
        path1 = str(tmp_path / "run1.jsonl")
        path2 = str(tmp_path / "run2.jsonl")

        for path in (path1, path2):
            config = _short_config(
                logging={"enabled": True, "console_enabled": False,
                         "jsonl_enabled": True, "jsonl_path": path},
            )
            world = _empty_world()
            run_episode(config, world)

        content1 = (tmp_path / "run1.jsonl").read_text()
        content2 = (tmp_path / "run2.jsonl").read_text()
        assert content1 == content2

    def test_round_trip_valid_json(self, tmp_path):
        """Every JSONL line must be valid JSON."""
        path = str(tmp_path / "out.jsonl")
        config = _short_config(
            logging={"enabled": True, "console_enabled": False,
                     "jsonl_enabled": True, "jsonl_path": path},
        )
        world = _empty_world()
        run_episode(config, world)

        text = (tmp_path / "out.jsonl").read_text().strip()
        for line in text.split("\n"):
            parsed = json.loads(line)
            assert isinstance(parsed, dict)

    def test_contains_all_steps(self, tmp_path):
        """Number of step lines must match total_steps."""
        path = str(tmp_path / "out.jsonl")
        config = _short_config(
            logging={"enabled": True, "console_enabled": False,
                     "jsonl_enabled": True, "jsonl_path": path},
        )
        world = _empty_world()
        result = run_episode(config, world)

        text = (tmp_path / "out.jsonl").read_text().strip()
        lines = text.split("\n")
        step_lines = [
            json.loads(line) for line in lines
            if json.loads(line).get("type") == "step"
        ]
        assert len(step_lines) == result.total_steps

    def test_has_episode_summary(self, tmp_path):
        """Last line must be the episode summary."""
        path = str(tmp_path / "out.jsonl")
        config = _short_config(
            logging={"enabled": True, "console_enabled": False,
                     "jsonl_enabled": True, "jsonl_path": path},
        )
        world = _empty_world()
        run_episode(config, world)

        text = (tmp_path / "out.jsonl").read_text().strip()
        last_line = json.loads(text.split("\n")[-1])
        assert last_line["type"] == "episode"


class TestLoggingFailureResilience:
    def test_unwritable_path_does_not_crash(self, tmp_path):
        """Episode must complete even if JSONL path is unwritable."""
        path = str(tmp_path / "nonexistent_dir" / "out.jsonl")
        config = _short_config(
            logging={"enabled": True, "console_enabled": False,
                     "jsonl_enabled": True, "jsonl_path": path},
        )
        world = _empty_world()
        result = run_episode(config, world)

        assert result.total_steps > 0
        assert result.termination_reason is TerminationReason.ENERGY_DEPLETED
