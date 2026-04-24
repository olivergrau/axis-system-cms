"""Small benchmark helper for comparing AXIS execution modes.

Usage examples:

  python scripts/benchmark_execution_modes.py --episodes 20 --steps 200
  python scripts/benchmark_execution_modes.py --episodes 20 --steps 200 --ofat
  python scripts/benchmark_execution_modes.py --episodes 30 --steps 300 --repeats 3
"""

from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
from pathlib import Path

from axis.framework.config import (
    ExperimentConfig,
    ExperimentType,
    ExecutionConfig,
    GeneralConfig,
    LoggingConfig,
)
from axis.framework.experiment import ExperimentExecutor
from axis.framework.persistence import ExperimentRepository
from axis.plugins import discover_plugins
from axis.sdk.world_types import BaseWorldConfig


def build_config(
    *,
    episodes: int,
    steps: int,
    trace_mode: str,
    parallelism_mode: str,
    max_workers: int,
    ofat: bool,
) -> ExperimentConfig:
    kwargs = dict(
        system_type="system_a",
        experiment_type=ExperimentType.OFAT if ofat else ExperimentType.SINGLE_RUN,
        general=GeneralConfig(seed=42),
        execution=ExecutionConfig(
            max_steps=steps,
            trace_mode=trace_mode,
            parallelism_mode=parallelism_mode,
            max_workers=max_workers,
        ),
        world=BaseWorldConfig(grid_width=20, grid_height=20),
        logging=LoggingConfig(enabled=False),
        system={
            "agent": {
                "initial_energy": 100.0,
                "max_energy": 100.0,
                "buffer_capacity": 20,
            },
            "policy": {
                "selection_mode": "argmax",
                "temperature": 1.0,
                "stay_suppression": 0.1,
                "consume_weight": 2.5,
            },
            "transition": {
                "move_cost": 1.0,
                "consume_cost": 0.5,
                "stay_cost": 0.3,
                "max_consume": 1.0,
                "energy_gain_factor": 15.0,
            },
        },
        num_episodes_per_run=episodes,
    )
    if ofat:
        kwargs["parameter_path"] = "framework.execution.max_steps"
        kwargs["parameter_values"] = (steps, max(5, steps // 2), max(10, steps + 20))
    return ExperimentConfig(**kwargs)


def run_once(config: ExperimentConfig) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="axis-bench-") as tmp:
        repo = ExperimentRepository(Path(tmp))
        executor = ExperimentExecutor(repository=repo)
        start = time.perf_counter()
        result = executor.execute(config)
        elapsed = time.perf_counter() - start
        return {
            "trace_mode": config.execution.trace_mode,
            "parallelism_mode": config.execution.parallelism_mode,
            "max_workers": config.execution.max_workers,
            "num_runs": result.summary.num_runs,
            "elapsed_seconds": elapsed,
        }


def run_repeated(
    label: str,
    config: ExperimentConfig,
    *,
    repeats: int,
    suite: str,
) -> dict[str, object]:
    samples: list[float] = []
    base_result: dict[str, object] | None = None
    for _ in range(repeats):
        result = run_once(config)
        samples.append(float(result["elapsed_seconds"]))
        if base_result is None:
            base_result = result

    assert base_result is not None
    return {
        "label": label,
        "suite": suite,
        "trace_mode": base_result["trace_mode"],
        "parallelism_mode": base_result["parallelism_mode"],
        "max_workers": base_result["max_workers"],
        "num_runs": base_result["num_runs"],
        "samples_seconds": samples,
        "min_seconds": min(samples),
        "mean_seconds": statistics.mean(samples),
        "median_seconds": statistics.median(samples),
        "max_seconds": max(samples),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark AXIS execution modes.")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--ofat", action="store_true", default=False)
    args = parser.parse_args()

    discover_plugins()

    scenarios = [
        ("full-sequential", build_config(
            episodes=args.episodes, steps=args.steps,
            trace_mode="full", parallelism_mode="sequential",
            max_workers=1, ofat=args.ofat,
        )),
        ("delta-sequential", build_config(
            episodes=args.episodes, steps=args.steps,
            trace_mode="delta", parallelism_mode="sequential",
            max_workers=1, ofat=args.ofat,
        )),
        ("light-sequential", build_config(
            episodes=args.episodes, steps=args.steps,
            trace_mode="light", parallelism_mode="sequential",
            max_workers=1, ofat=args.ofat,
        )),
    ]

    if args.ofat:
        scenarios.append((
            "full-runs-parallel",
            build_config(
                episodes=args.episodes, steps=args.steps,
                trace_mode="full", parallelism_mode="runs",
                max_workers=args.workers, ofat=True,
            ),
        ))
        scenarios.append((
            "delta-runs-parallel",
            build_config(
                episodes=args.episodes, steps=args.steps,
                trace_mode="delta", parallelism_mode="runs",
                max_workers=args.workers, ofat=True,
            ),
        ))
        scenarios.append((
            "light-runs-parallel",
            build_config(
                episodes=args.episodes, steps=args.steps,
                trace_mode="light", parallelism_mode="runs",
                max_workers=args.workers, ofat=True,
            ),
        ))
    else:
        scenarios.append((
            "full-episodes-parallel",
            build_config(
                episodes=args.episodes, steps=args.steps,
                trace_mode="full", parallelism_mode="episodes",
                max_workers=args.workers, ofat=False,
            ),
        ))
        scenarios.append((
            "delta-episodes-parallel",
            build_config(
                episodes=args.episodes, steps=args.steps,
                trace_mode="delta", parallelism_mode="episodes",
                max_workers=args.workers, ofat=False,
            ),
        ))
        scenarios.append((
            "light-episodes-parallel",
            build_config(
                episodes=args.episodes, steps=args.steps,
                trace_mode="light", parallelism_mode="episodes",
                max_workers=args.workers, ofat=False,
            ),
        ))

    results = []
    suite = "ofat" if args.ofat else "single_run"
    for label, config in scenarios:
        result = run_repeated(
            label,
            config,
            repeats=args.repeats,
            suite=suite,
        )
        results.append(result)

    baseline_label = "full-sequential"
    baseline = next(
        (result for result in results if result["label"] == baseline_label),
        None,
    )
    if baseline is not None:
        baseline_seconds = float(baseline["median_seconds"])
        for result in results:
            result["speedup_vs_full_sequential"] = (
                baseline_seconds / float(result["median_seconds"])
            )

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
