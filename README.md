# AXIS Experimentation Framework (v0.2.0)

AXIS is a modular agent-environment experimentation framework. It provides
a protocol-based architecture where **systems** (agent logic) and **worlds**
(environment dynamics) are pluggable components, composed via registries and
executed through a unified CLI.

## Architecture

```
src/axis/
  sdk/                  Protocol contracts and shared types
    interfaces.py         SystemInterface, SensorInterface, DriveInterface, ...
    world_types.py        WorldView, MutableWorldProtocol, BaseWorldConfig, ...
    types.py              DecideResult, TransitionResult, PolicyResult
    trace.py              BaseStepTrace, BaseEpisodeTrace
    snapshot.py           WorldSnapshot
    position.py           Position
    actions.py            BASE_ACTIONS, MOVEMENT_DELTAS

  framework/            Orchestration, persistence, CLI
    cli.py                axis CLI entry point
    config.py             ExperimentConfig, FrameworkConfig, OFAT path parsing
    runner.py             Episode loop (setup_episode, run_episode)
    run.py                RunExecutor, RunResult, RunSummary
    experiment.py         ExperimentExecutor, OFAT, resume
    persistence.py        ExperimentRepository (file-based)
    registry.py           System registry (register_system, create_system)

  systems/              Pluggable system implementations
    system_a/             Energy-driven forager (sensor, drive, policy, transition)
    system_b/             Scout agent with scan action

  world/                Pluggable world implementations
    registry.py           World registry (register_world, create_world_from_config)
    actions.py            ActionRegistry, base movement handlers
    grid_2d/              Standard 2D rectangular grid (default)
    toroidal/             Wraparound grid (edges connect)
    signal_landscape/     Dynamic signal-based world with drifting hotspots

  visualization/        Adapter-based interactive episode viewer
    registry.py           Visualization adapter registry
    launch.py             Viewer entry point
    ui/                   Qt-based UI components
```

## CLI

```
axis experiments run <config.yaml>             Run experiment from config
axis experiments list                          List all experiments
axis experiments show <experiment_id>          Inspect experiment details
axis experiments resume <experiment_id>        Resume incomplete experiment

axis runs list --experiment <experiment_id>    List runs in an experiment
axis runs show <run_id> --experiment <eid>     Inspect a specific run

axis visualize --experiment <eid> --run <rid> --episode 1
                                               Open interactive episode viewer
```

Use `--output json` on any command for machine-readable output.
Use `--root <path>` to point to a non-default repository location.

## Experiment Configs

Ready-to-use configs ship at `experiments/configs/`:

| Config | Description |
|---|---|
| `system-a-baseline.yaml` | Single-run baseline (10x10, sparse regen) |
| `system-a-energy-gain-sweep.yaml` | OFAT sweep over energy gain factor |
| `system-a-toroidal-demo.yaml` | System A on a toroidal (wraparound) grid |
| `system-b-sdk-demo.yaml` | System B scout agent on a signal landscape |

```bash
axis experiments run experiments/configs/system-a-baseline.yaml
```

## Key Concepts

- **System**: Encapsulates all agent logic (sensing, decision-making, state
  transitions). Implements `SystemInterface`. Plugged in via `register_system()`.
- **World**: Encapsulates environment topology and dynamics. Implements
  `MutableWorldProtocol`. Plugged in via `register_world()`.
- **Experiment**: One or more runs with a shared config. Supports single-run
  and OFAT (one-factor-at-a-time) sweep modes.
- **Run**: Multiple episodes with a shared configuration and independent seeds.
- **Episode**: One agent lifetime from initialization to termination.

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
python -m pytest

# Run a specific test module
python -m pytest tests/framework/test_cli.py
```

- **Python 3.11+** with PySide6, Pydantic v2, NumPy
- **Testing**: pytest (72 test files across framework, SDK, systems, worlds,
  and visualization)

## Documentation

Manuals and specs are in `docs/`:

- `manuals/cli-manual.md` -- CLI user guide
- `manuals/config-manual.md` -- Configuration reference
- `manuals/system-dev-manual.md` -- Building custom systems
- `manuals/world-dev-manual.md` -- Building custom worlds
- `architecture/` -- Design documents and evolution history
- `specs/` -- Specifications

## License

TBD
