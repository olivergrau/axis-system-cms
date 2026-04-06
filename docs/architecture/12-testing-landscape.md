# 12. Testing Landscape

## Overview

| Category | Files | Tests | Purpose |
|----------|-------|-------|---------|
| `tests/unit/` | 17 | ~700 | Individual module correctness |
| `tests/integration/` | 6 | ~130 | Multi-module interaction |
| `tests/behavioral/` | 1 | ~8 | System-level behavioral properties |
| `tests/e2e/` | 1 | ~36 | Full CLI end-to-end |
| `tests/visualization/` | 22 | ~630 | Visualization subsystem |
| **Total** | **47** | **~1215** | |

## Test Infrastructure

### Builders (`tests/builders/`)

Fluent test builders for constructing domain objects:

- **WorldBuilder**: `with_size()`, `with_agent_at()`, `with_food()`, `with_obstacle()`, `with_empty()`, `with_all_food()`, `build() -> World`
- **AgentStateBuilder**: `with_energy()`, `with_memory_capacity()`, `with_empty_memory()`, `with_memory_entries()`, `build() -> AgentState`
- **MemoryBuilder**: `with_capacity()`, `with_entry()`, `with_entries()`, `build() -> MemoryState`

### Fixtures (`tests/fixtures/`)

Registered via `pytest_plugins` in root `conftest.py`:

- **world_fixtures**: Pre-built worlds (3x3 with food/obstacles, corridor, all-resource), cell factories, WorldConfig fixtures
- **agent_fixtures**: Default (50/100 energy), full energy, low energy, empty memory
- **observation_fixtures**: `make_observation()` factory, all-open, all-blocked, uniform, sample
- **scenario_fixtures**: `_BASE_CONFIG_DICT`, `make_config(overrides)`, `valid_config_dict`, `default_step_kwargs`

Visualization has its own `conftest.py` providing: `small_episode`, `populated_repo`, `access_service`, `replay_episode_handle`, `snapshot_resolver`, `initial_viewer_state`.

### Assertion Helpers (`tests/utils/`)

- `assert_model_frozen()` -- verifies Pydantic frozen model rejects mutation
- `assert_probabilities_sum_to_one()`, `assert_probabilities_valid()` -- probability vector checks
- `assert_energy_decreased()`, `assert_action_selected()` -- domain assertions
- `assert_valid_transition_trace()`, `assert_trace_energy_consistent()`, `assert_trace_movement_consistent()` -- trace integrity

## Unit Tests (`tests/unit/`)

| File | Tests | Coverage Area |
|------|-------|---------------|
| `test_config.py` | ~74 | Config validation, defaults, edge cases, new `obstacle_density` |
| `test_types.py` | ~59 | Position, AgentState, MemoryState, Observation, clip_energy |
| `test_transition.py` | ~89 | Step function, movement, consumption, costs, boundary conditions |
| `test_world.py` | ~77 | World creation, cell access, obstacle placement, sparse eligibility |
| `test_repository.py` | ~74 | Repository CRUD, status/metadata persistence, discovery |
| `test_experiment.py` | ~57 | ExperimentConfig validation, OFAT resolution, summary computation |
| `test_policy.py` | ~56 | Action selection, probabilities, temperature, masking |
| `test_observation.py` | ~34 | Observation building from world state |
| `test_logging.py` | ~33 | Logger creation, formatters, JSONL output, noop mode |
| `test_drive.py` | ~28 | Hunger drive computation, activation, contributions |
| `test_results.py` | ~24 | EpisodeResult, StepResult, EpisodeSummary, serialization |
| `test_run.py` | ~38 | RunConfig, seed resolution, RunSummary computation |
| `test_enums.py` | ~21 | Enum values, membership, stringification |
| `test_memory.py` | ~16 | Memory update, FIFO eviction, capacity |
| `test_snapshots.py` | ~15 | World/agent snapshot capture |
| `test_runner.py` | ~7 | Episode step and run_episode basics |

## Integration Tests (`tests/integration/`)

| File | Tests | Coverage Area |
|------|-------|---------------|
| `test_experiment_execution.py` | ~35 | Full experiment lifecycle, status transitions, OFAT, failure handling |
| `test_experiment_resume.py` | ~34 | Resume semantics, idempotency, artifact integrity |
| `test_run_execution.py` | ~21 | RunExecutor end-to-end, determinism, aggregation |
| `test_episode_execution.py` | ~24 | run_episode termination, sequential timesteps, result structures |
| `test_step_pipeline.py` | ~4 | Full step pipeline: observation chain continuity |
| `test_logging_integration.py` | ~9 | Logging non-interference, JSONL validity |

## Behavioral Tests (`tests/behavioral/`)

System-level properties validated across full episode executions:

- Energy monotonically decreases on empty grid (no food)
- Energy always bounded within [0, max_energy]
- Agent survives longer with food available
- Same seed produces identical trajectories
- Different seeds produce different trajectories
- Argmax mode is deterministic regardless of RNG

## End-to-End Tests (`tests/e2e/`)

Full CLI end-to-end tests exercising `main()` directly with in-memory configs:

- Complete workflows: run -> show -> list runs -> show run
- OFAT workflows: run -> show -> list with variation descriptions
- Resume workflows: partial -> resume -> completed
- Error cases: missing config, malformed JSON, nonexistent experiment/run
- YAML config loading

## Visualization Tests (`tests/visualization/`)

Comprehensive coverage of the entire visualization subsystem:

| Area | Key Files | Tests |
|------|-----------|-------|
| Data models | `test_snapshot_models.py`, `test_replay_models.py`, `test_view_models.py`, `test_debug_overlay_models.py` | ~80 |
| Snapshot resolution | `test_snapshot_resolver.py` | ~35 |
| Replay access | `test_replay_access.py`, `test_replay_validation.py` | ~54 |
| State management | `test_viewer_state.py`, `test_viewer_state_transitions.py`, `test_playback_controller.py` | ~142 |
| View model building | `test_view_model_builder.py`, `test_debug_overlay_builder.py` | ~66 |
| UI widgets | `test_grid_interaction.py`, `test_detail_panel.py`, `test_step_analysis_panel.py`, `test_replay_controls_panel.py`, `test_debug_overlay_panel.py`, `test_debug_overlay_transitions.py` | ~120 |
| Integration | `test_ui_construction.py`, `test_session_controller.py`, `test_visualization_cli.py`, `test_visualization_e2e.py` | ~128 |

All PySide6 widget tests run with `QT_QPA_PLATFORM=offscreen` (no display server required).

## Testing Patterns

1. **Frozen model tests**: Every Pydantic model is tested for immutability via `assert_model_frozen()`
2. **Field-set tests**: Model tests verify the complete field set to catch accidental additions/removals
3. **Boundary tests**: Navigation, seek, and selection tests check behavior at grid/step boundaries
4. **Determinism tests**: Same seed -> same result, verified at episode, run, and experiment levels
5. **Vacuous test detection**: Some tests operate on fixture data that may not exercise all branches (e.g., obstacle rendering tests on obstacle-free grids)
