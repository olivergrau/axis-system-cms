# 3. Repository and Package Structure

## Source Layout

```
src/axis_system_a/
    __init__.py                     Public API (75 symbols)
    types.py                        Position, Observation, CellObservation, AgentState, MemoryState
    enums.py                        Action, CellType, SelectionMode, TerminationReason, RegenerationMode
    config.py                       SimulationConfig and 7 sub-configs
    world.py                        Cell, World, create_world, obstacle/eligibility placement
    observation.py                  build_observation (sensor projection)
    memory.py                       update_memory (FIFO ring buffer)
    drives.py                       compute_hunger_drive, HungerDriveOutput
    policy.py                       select_action, DecisionTrace (admissibility, masking, softmax)
    transition.py                   step(), TransitionTrace (movement, consumption, energy, regen)
    runner.py                       run_episode, episode_step (orchestration loop)
    results.py                      StepResult, EpisodeResult, EpisodeSummary
    snapshots.py                    WorldSnapshot, AgentSnapshot, snapshot functions
    run.py                          RunExecutor, RunConfig, RunResult, RunSummary, seed resolution
    experiment.py                   ExperimentConfig, ExperimentResult, OFAT resolution
    experiment_executor.py          ExperimentExecutor (execute + resume)
    repository.py                   ExperimentRepository (file-based persistence)
    logging.py                      AxisLogger, trace renderers (console + JSONL)
    cli.py                          CLI entry point and command handlers

    visualization/
        __init__.py                 Public facade (46 symbols)
        errors.py                   Exception hierarchy (ReplayError and subtypes)
        snapshot_models.py          ReplayPhase, ReplayCoordinate, ReplaySnapshot
        snapshot_resolver.py        SnapshotResolver (step+phase -> snapshot)
        replay_models.py            EpisodeHandle, RunHandle, ExperimentHandle
        replay_access.py            ReplayAccessService (read-only repository gateway)
        replay_validation.py        validate_episode_for_replay
        viewer_state.py             ViewerState, PlaybackMode, create_initial_state
        viewer_state_transitions.py Pure state transition functions
        view_models.py              All view model types (grid, agent, status, analysis, ...)
        view_model_builder.py       ViewModelBuilder (state -> frame projection)
        debug_overlay_models.py     Overlay config and data models
        playback_controller.py      PlaybackController, phase traversal, boundary detection
        launch.py                   CLI launch orchestration

        ui/
            __init__.py
            app.py                  QApplication bootstrap, signal wiring
            main_window.py          VisualizationMainWindow (layout, frame routing)
            grid_widget.py          GridWidget (rendering, overlays, mouse events)
            replay_controls_panel.py ReplayControlsPanel (buttons, phase combo)
            status_panel.py         StatusPanel (step/phase/energy labels)
            detail_panel.py         DetailPanel (cell/agent details on selection)
            step_analysis_panel.py  StepAnalysisPanel (full decision readout)
            debug_overlay_panel.py  DebugOverlayPanel (checkboxes, legend)
            session_controller.py   VisualizationSessionController (state owner)
```

## Test Layout

```
tests/
    conftest.py                     Root conftest (registers fixture plugins)
    builders/
        world_builder.py            WorldBuilder (fluent, with_food/obstacle/empty)
        agent_state_builder.py      AgentStateBuilder (fluent)
        memory_builder.py           MemoryBuilder (fluent)
    fixtures/
        world_fixtures.py           World/cell fixtures (small_world, corridor, etc.)
        agent_fixtures.py           Agent state fixtures (default, low_energy, etc.)
        observation_fixtures.py     Observation factories (all_open, all_blocked, etc.)
        scenario_fixtures.py        SimulationConfig/step-kwargs fixtures
    utils/
        assertions.py               Model assertion helpers (frozen, probabilities, energy)
        trace_assertions.py         Transition trace consistency assertions
    unit/                           17 files, ~700 tests
    integration/                    6 files, ~130 tests
    behavioral/                     1 file, ~8 tests
    e2e/                            1 file, ~36 tests
    visualization/                  22 files + conftest, ~630 tests
```

## Supporting Artifacts

```
docs/
    architecture/                   This architecture documentation
    manuals/
        cli-manual.md               Comprehensive CLI user manual
    specs/
        System A Baseline.md        Formal system specification
        System A Baseline Worked Examples.md
        Visualization Architecture.md
        Experimentation Framework - Architecture.md
        work-packages/              31 work-package documents (core, experiment, visualization)

experiments/
    configs/
        baseline.json               Single-run baseline (10x10, 10 episodes)
        energy-gain-sweep.json      OFAT sweep: energy_gain_factor [5,10,20]
        sparsity-sweep.json         OFAT sweep: regen_eligible_ratio [0.05..0.50]
    results/                        Persisted experiment artifacts (gitignored)
```

## Module Responsibilities

| Module | Single Responsibility |
|--------|----------------------|
| `types.py` | Immutable value types and agent state |
| `enums.py` | All enumerations used across the system |
| `config.py` | Configuration validation and defaults |
| `world.py` | Grid world model, cell invariants, world factory |
| `observation.py` | Stateless sensor projection from world state |
| `memory.py` | Pure memory update function (FIFO eviction) |
| `drives.py` | Hunger drive computation (activation + contributions) |
| `policy.py` | Decision pipeline (mask -> softmax -> select) |
| `transition.py` | State transition engine (regen -> act -> observe -> update) |
| `runner.py` | Episode loop orchestration (drive -> policy -> transition) |
| `results.py` | Execution trace structures and summary computation |
| `snapshots.py` | Immutable world/agent snapshot capture |
| `run.py` | Multi-episode run execution and summary |
| `experiment.py` | Experiment config, OFAT resolution, result aggregation |
| `experiment_executor.py` | Experiment orchestration and resume |
| `repository.py` | File-based artifact persistence |
| `logging.py` | Non-intrusive structured logging |
| `cli.py` | Command-line interface and dispatch |
