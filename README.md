# AXIS System A

AXIS System A is a deterministic agent-environment simulation framework designed to implement and validate a formally specified model of perception, internal drives, and decision-making.

The project follows a specification-first approach: system behavior is defined through structured documents, worked examples, and explicit invariants before implementation.

## Purpose

- Translate a formal system specification into a working runtime
- Ensure correctness through deterministic execution and testable transitions
- Validate behavior against worked examples and defined invariants
- Explore how far structured specifications can guide AI-assisted implementation

## System Overview

The system models a single agent interacting with a discrete grid world through a closed perception-decision-action loop:

- **World**: 2D grid of cells (empty, resource, obstacle) with configurable obstacle density and resource regeneration
- **Observation**: Local sensor model providing the agent with information about its immediate neighborhood (traversability, resource values)
- **Memory**: Bounded ring-buffer recording recent observations for temporal context
- **Drives**: Internal signals (hunger) that generate action contributions based on energy state and observations
- **Policy**: Softmax-based decision mechanism combining drive contributions with admissibility masking, temperature scaling, and configurable selection modes (sample / argmax)
- **Transition Engine**: Deterministic state update — movement, consumption, energy accounting, resource regeneration
- **Episode Loop**: Sequential step execution until termination (energy depletion or max steps)

## Architecture

```
src/axis_system_a/
  types.py                  Position, Observation, CellObservation
  enums.py                  Action, CellType, SelectionMode, RegenerationMode
  config.py                 SimulationConfig and sub-configs (world, agent, policy, ...)
  world.py                  Cell, World, create_world (obstacle placement, sparse eligibility)
  observation.py            Sensor model — local neighborhood extraction
  memory.py                 Bounded observation memory (ring buffer)
  drives.py                 HungerDrive — activation and action contributions
  policy.py                 DecisionTrace — admissibility, masking, softmax, action selection
  transition.py             TransitionTrace — movement, consumption, energy, regeneration
  runner.py                 Episode loop — step execution until termination
  results.py                StepResult, EpisodeResult — full execution trace
  run.py                    RunExecutor — multi-episode batch execution
  experiment.py             ExperimentConfig — multi-run experiment definitions
  experiment_executor.py    ExperimentExecutor — orchestration and persistence
  repository.py             ExperimentRepository — file-based artifact storage
  logging.py                Structured logging (console + JSONL)
  cli.py                    Command-line interface

  visualization/
    snapshot_models.py       ReplaySnapshot, ReplayPhase, ReplayCoordinate
    snapshot_resolver.py     SnapshotResolver — world state at any step/phase
    replay_models.py         EpisodeHandle, replay metadata
    replay_access.py         ReplayAccess — load episodes from repository
    replay_validation.py     Coordinate bounds checking
    viewer_state.py          ViewerState — single source of truth for UI state
    viewer_state_transitions.py  Pure transitions (next/prev step, seek, select, ...)
    view_models.py           GridViewModel, AgentViewModel, StepAnalysisViewModel, ...
    view_model_builder.py    Stateless projection: ViewerState → ViewerFrameViewModel
    debug_overlay_models.py  Overlay data models (action prefs, drive bars, consumption)
    playback_controller.py   Timer-driven auto-play
    errors.py                Visualization-specific exceptions

    ui/
      app.py                 QApplication bootstrap
      main_window.py         Top-level window — splitter layout with panels
      grid_widget.py         Custom QWidget — grid rendering, overlays, mouse interaction
      replay_controls_panel.py  Playback buttons and step/phase display
      status_panel.py        Episode status line
      detail_panel.py        Cell/agent detail on selection
      step_analysis_panel.py Decision analysis — full numeric readout per step
      debug_overlay_panel.py Overlay toggle checkboxes and legend
      session_controller.py  Wires UI signals to state transitions
```

## Experimentation Framework

The CLI supports a three-level hierarchy: **experiments** contain **runs**, and runs contain **episodes**.

- **Experiment configs** define one or more parameter variations (e.g., sweeping energy gain or obstacle density)
- **Runs** execute multiple episodes with a shared configuration and independent seeds
- **Results** are persisted to a file-based repository under `experiments/results/`

Example configs are provided in `experiments/configs/`:

| Config | Description |
|---|---|
| `baseline.json` | Standard single-run baseline |
| `energy-gain-sweep.json` | Sweep over energy gain factor |
| `sparsity-sweep.json` | Sweep over regeneration sparsity |

## CLI

```
axis experiments list                         List all experiments
axis experiments run config.yaml              Run experiment from config
axis experiments run config.yaml --redo       Re-run, replacing old results
axis experiments show <experiment_id>         Inspect experiment details
axis experiments resume <experiment_id>       Resume incomplete experiment

axis runs list --experiment <experiment_id>   List runs in an experiment
axis runs show <run_id> --experiment <eid>    Inspect a specific run

axis visualize --experiment <eid> --run <rid> --episode 1
                                              Open interactive episode viewer
```

Use `--output json` on any command for machine-readable output.
Use `--root <path>` to point to a non-default repository location.

Run with: `python -m axis_system_a.cli <command>`

## Visualization

The interactive episode viewer (`axis visualize`) provides:

- **Grid display**: Color-coded cells (grey = empty, green = resource, black = obstacle), agent position
- **Replay controls**: Play/pause, step forward/backward, phase navigation (BEFORE, AFTER_REGEN, AFTER_ACTION)
- **Step Analysis panel**: Full decision pipeline readout — observation, drive activation, raw/effective contributions, admissibility, probabilities, selected action, energy delta, outcome
- **Debug overlays**: Action preference arrows, drive contribution bars, consumption opportunity indicators (toggle via checkboxes)
- **Detail panel**: Cell and agent details on click/selection

## Configuration

All simulation parameters are defined in a single `SimulationConfig`:

| Section | Key Parameters |
|---|---|
| `world` | `grid_width`, `grid_height`, `obstacle_density`, `resource_regen_rate`, `regeneration_mode`, `regen_eligible_ratio` |
| `agent` | `initial_energy`, `max_energy`, `memory_capacity` |
| `policy` | `selection_mode` (sample/argmax), `temperature`, `stay_suppression`, `consume_weight` |
| `transition` | `move_cost`, `consume_cost`, `stay_cost`, `max_consume`, `energy_gain_factor` |
| `execution` | `max_steps` |

## Development Environment

The project runs inside a Dev Container (VS Code + Docker + WSL2):

- **Python 3.11** with PySide6, Pydantic v2, NumPy
- **Testing**: pytest (1200+ tests across unit, integration, behavioral, e2e, and visualization layers)
- **Linting**: Ruff
- **GPU support**: Optional (not required for core simulation)
- **Display**: X11/Wayland forwarding for PySide6 visualization

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific layer
python -m pytest tests/unit/
python -m pytest tests/visualization/
python -m pytest tests/behavioral/
python -m pytest tests/e2e/
python -m pytest tests/integration/
```

Test categories:

- **Unit**: Core domain models, transitions, policy, world generation
- **Integration**: Multi-component interaction (runner, repository, executor)
- **Behavioral**: Scenario-based validation against specification examples
- **E2E**: Full experiment execution and CLI validation
- **Visualization**: Widget rendering, state transitions, overlay logic, panel content

## Specifications

Design documents live in `docs/specs/`:

- `System A Baseline.md` — formal system specification
- `System A Baseline Worked Examples.md` — step-by-step validation scenarios
- world model specification
- implementation architecture
- `work-packages/` — incremental implementation plan

## License

TBD
