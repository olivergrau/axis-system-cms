# WP-3.6 Implementation Brief -- Framework Test Suite

## Context

We are implementing **Phase 3 -- Framework Alignment**. WP-3.1 through WP-3.5 delivered the system registry, episode runner, executors, persistence layer, and CLI. This work package provides a comprehensive test suite for all Phase 3 framework components, tested **independently of any specific system** using a mock `SystemInterface`.

### Predecessor State (After WP-3.5)

```
src/axis/framework/
    config.py            # ExperimentConfig, FrameworkConfig, OFAT utilities
    registry.py          # System registry (System A auto-registered)
    runner.py            # run_episode(), setup_episode()
    run.py               # RunConfig, RunExecutor, RunResult, RunSummary
    experiment.py        # resolve_run_configs, ExperimentExecutor, ExperimentResult
    persistence.py       # ExperimentRepository, statuses, metadata
    cli.py               # CLI module

tests/v02/framework/
    test_config.py       # Phase 1 config tests (already exists)
    test_registry.py     # WP-3.1 registry tests
    test_runner.py       # WP-3.2 runner tests
    test_run.py          # WP-3.3 run executor tests
    test_experiment.py   # WP-3.3 experiment executor tests
    test_persistence.py          # WP-3.4 repository tests
    test_executor_persistence.py # WP-3.4 executor+persistence integration
    test_cli.py          # WP-3.5 CLI tests
```

Each WP included its own tests. WP-3.6 adds **cross-cutting integration tests** and **mock-system tests** that validate the framework works with a system other than System A, proving system-agnosticism.

### Architectural Decisions (Binding)

- **Q18 = New test suites**: Fresh test suites for the new structure
- **Q11 = Explicit registry**: Registry tested with mock systems
- **Q1 = Two-phase step**: Runner tested with mock decide/transition
- All framework tests must work without importing `axis.systems.system_a`

### Reference Documents

- `docs/v0.2.0/architecture/evolution/modular-architecture-roadmap.md` -- WP-3.6 definition
- All WP-3.x specs for component behavior

---

## Objective

1. **Mock System**: Define a minimal `MockSystem` implementing `SystemInterface` for framework-only testing
2. **Cross-component integration tests**: Test the full pipeline from config -> registry -> executor -> runner -> persistence -> resume
3. **OFAT path resolution tests**: Test both framework and system path variations end-to-end
4. **Edge cases and error handling**: Cover failure modes, boundary conditions, and error paths across all framework components
5. **Behavioral equivalence**: Verify that the framework pipeline with System A produces the same results as the WP-2.4 equivalence tests (confirming the runner is correctly wired)

---

## Scope

### 1. Mock System (`tests/v02/framework/mock_system.py`)

A minimal `SystemInterface` implementation for testing framework components without depending on System A.

```python
class MockSystem:
    """Minimal system for framework testing.

    Implements a trivial agent that always moves right. Energy decreases
    by 1 per step. Terminates when energy reaches 0.
    """

    def system_type(self) -> str:
        return "mock"

    def action_space(self) -> tuple[str, ...]:
        return ("up", "down", "left", "right", "stay")

    def initialize_state(self) -> dict:
        return {"energy": self._initial_energy}

    def vitality(self, agent_state) -> float:
        return agent_state["energy"] / self._max_energy

    def decide(self, world_view, agent_state, rng) -> DecideResult:
        return DecideResult(action="right", decision_data={"reason": "always_right"})

    def observe(self, world_view, position) -> dict:
        return {"position": (position.x, position.y)}

    def transition(self, agent_state, action_outcome, new_observation) -> TransitionResult:
        new_energy = max(0.0, agent_state["energy"] - 1.0)
        return TransitionResult(
            new_state={"energy": new_energy},
            trace_data={"energy_before": agent_state["energy"], "energy_after": new_energy},
            terminated=new_energy <= 0.0,
            termination_reason="energy_depleted" if new_energy <= 0.0 else None,
        )

    def action_handlers(self) -> dict:
        return {}  # No custom actions (only base actions)

    def action_context(self) -> dict:
        return {}
```

**Key design**: The mock system uses plain dicts for agent state (not Pydantic models). This validates that the framework truly treats agent state as opaque `Any`. It uses only base actions (no custom handlers) to test the simplest path.

### 2. Mock System Registration

The mock system is registered in test fixtures, not auto-registered at import time:

```python
@pytest.fixture
def mock_system_registered():
    """Register mock system, yield, then clean up."""
    from axis.framework.registry import register_system

    def mock_factory(config: dict) -> MockSystem:
        return MockSystem(config)

    register_system("mock", mock_factory)
    yield
    # Cleanup: remove from registry
    from axis.framework.registry import _SYSTEM_REGISTRY
    _SYSTEM_REGISTRY.pop("mock", None)
```

**Note**: This requires the registry to support cleanup for testing. If the registry raises on duplicate registration, the fixture must handle that. Alternatively, add an `unregister_system()` function for testing (test-only, not part of public API). Or, each test creates a fresh registry instance.

**Simpler approach**: Use `_SYSTEM_REGISTRY` dict access in the fixture teardown. This is acceptable for tests since `_SYSTEM_REGISTRY` is module-level.

### 3. Test Files

#### `tests/v02/framework/test_mock_system.py` -- Mock System Validation

Verify the mock system itself conforms to `SystemInterface`:

| Test | Description |
|------|-------------|
| `test_mock_conforms_to_system_interface` | `isinstance(mock, SystemInterface)` |
| `test_mock_system_type` | Returns `"mock"` |
| `test_mock_action_space` | Returns base actions tuple |
| `test_mock_initialize_state` | Returns dict with `"energy"` |
| `test_mock_vitality` | Normalized energy value |
| `test_mock_decide` | Returns `DecideResult` with action `"right"` |
| `test_mock_transition` | Returns `TransitionResult`, energy decreases |
| `test_mock_termination` | Terminates at energy 0 |
| `test_mock_observe` | Returns observation dict |
| `test_mock_action_handlers_empty` | No custom actions |
| `test_mock_action_context_empty` | Empty context |

#### `tests/v02/framework/test_framework_integration.py` -- Cross-Component Integration

End-to-end tests using the mock system through the full framework pipeline:

| Test | Description |
|------|-------------|
| `test_registry_to_runner` | Create mock system via registry, run episode, get trace |
| `test_registry_to_executor` | Create RunConfig with mock, execute via RunExecutor |
| `test_experiment_single_run_mock` | Full ExperimentExecutor.execute() with mock system |
| `test_experiment_ofat_framework_path` | OFAT varying `framework.execution.max_steps` with mock |
| `test_experiment_ofat_system_path` | OFAT varying a system config parameter with mock |
| `test_persistence_roundtrip` | Execute with persistence, reload all artifacts |
| `test_resume_with_mock` | Execute partially, resume, verify completion |
| `test_episode_trace_system_data` | `system_data` contains mock system's decision/trace data |
| `test_vitality_in_summary` | `RunSummary.mean_final_vitality` reflects mock energy |
| `test_death_rate_calculation` | Death rate matches terminated episodes |
| `test_deterministic_across_runs` | Same config -> identical results |
| `test_different_seeds_differ` | Different seeds -> different episode outcomes (mock always goes right, but world layout changes with obstacles) |

#### `tests/v02/framework/test_ofat_integration.py` -- OFAT Path Resolution End-to-End

| Test | Description |
|------|-------------|
| `test_ofat_framework_execution_max_steps` | Vary max_steps, verify different step counts |
| `test_ofat_system_parameter` | Vary mock system config param, verify it reaches the system |
| `test_ofat_run_count` | N parameter values -> N runs |
| `test_ofat_seed_spacing` | Run seeds are spaced by 1000 |
| `test_ofat_variation_descriptions` | Correct descriptions in summary entries |
| `test_ofat_deltas_computed` | Delta values relative to first run |
| `test_ofat_invalid_path_rejected` | Bad OFAT path raises at config validation |

#### `tests/v02/framework/test_error_handling.py` -- Error Paths and Edge Cases

| Test | Description |
|------|-------------|
| `test_unknown_system_type` | `create_system("nonexistent", {})` raises `KeyError` |
| `test_missing_experiment_resume` | Resume nonexistent experiment raises |
| `test_empty_run_summary` | 0 episodes -> all-zero summary |
| `test_max_steps_termination` | Episode hits max_steps -> `"max_steps_reached"` |
| `test_system_termination` | System signals terminated -> stops early |
| `test_invalid_action_from_system` | System returns unknown action (not in registry) -> error |
| `test_resume_completed_experiment` | Already completed -> no re-execution |

#### `tests/v02/framework/test_system_a_through_framework.py` -- System A via Framework Pipeline

**This is the capstone test.** Verifies that running System A through the full framework pipeline (registry -> executor -> runner) produces results equivalent to the WP-2.4 behavioral equivalence tests.

| Test | Description |
|------|-------------|
| `test_system_a_registered` | `"system_a" in registered_system_types()` |
| `test_system_a_via_runner` | `run_episode()` with System A produces `BaseEpisodeTrace` |
| `test_system_a_via_executor` | `RunExecutor.execute()` with System A produces `RunResult` |
| `test_system_a_equivalence_default` | Framework runner output matches WP-2.4 equivalence trajectory |
| `test_system_a_equivalence_argmax` | Argmax mode equivalence |
| `test_system_a_equivalence_with_obstacles` | Obstacle scenario equivalence |
| `test_system_a_experiment_single_run` | Full experiment with System A, verify artifacts |
| `test_system_a_experiment_ofat` | OFAT with `system.policy.temperature`, verify per-run variation |

**Implementation approach**: These tests reuse the equivalence test helpers from `tests/v02/systems/system_a/test_equivalence.py` (specifically `_run_legacy_episode()` and the `Trajectory` dataclass) to compare framework runner output against the legacy oracle.

---

## Out of Scope

Do **not** implement any of the following in WP-3.6:

- Visualization tests (WP-4.4)
- System A internal component tests (already covered in WP-2.4)
- CLI end-to-end tests beyond what WP-3.5 provides (no additional CLI tests here)
- Performance benchmarks
- Load/stress testing

---

## Architectural Constraints

### 1. Mock System Independence

The mock system and framework integration tests must **never** import from `axis.systems.system_a`. The mock system is defined entirely within the test directory. This proves the framework is system-agnostic.

### 2. System A Tests Are Separate

The `test_system_a_through_framework.py` file is the only test file that imports both framework and System A code. It exists to validate the complete wiring, not to test System A internals.

### 3. Fixture Isolation

Tests that register mock systems must clean up after themselves to avoid polluting the global registry. Use fixture teardown or context managers.

### 4. Determinism

All tests that run episodes must use explicit seeds for reproducibility.

---

## Expected File Structure

After WP-3.6, these files are **new**:

```
tests/v02/framework/mock_system.py                    # NEW (MockSystem implementation)
tests/v02/framework/test_mock_system.py                # NEW (mock system validation)
tests/v02/framework/test_framework_integration.py      # NEW (cross-component integration)
tests/v02/framework/test_ofat_integration.py           # NEW (OFAT end-to-end)
tests/v02/framework/test_error_handling.py             # NEW (error paths)
tests/v02/framework/test_system_a_through_framework.py # NEW (System A via framework)
```

No production code files are modified in WP-3.6 (this is a test-only WP).

---

## Testing Requirements

This WP **is** the test suite. Success criteria:

1. All mock system tests pass -- proves the framework's protocol-based interface works with non-System-A implementations
2. All integration tests pass -- proves the full pipeline works end-to-end
3. All OFAT tests pass -- proves parameter path resolution works for both framework and system domains
4. All error handling tests pass -- proves graceful failure modes
5. All System A through-framework tests pass -- proves the framework produces equivalent results to the legacy system
6. All existing tests (from WP-3.1 through WP-3.5 and earlier phases) continue to pass
7. Estimated new test count: 50-70 tests
8. Total test suite remains green

---

## Implementation Style

- Python 3.11+
- `MockSystem` uses plain dicts (not Pydantic) for agent state to validate opaque `Any` handling
- pytest fixtures for mock system registration/cleanup
- `@pytest.mark.parametrize` for multi-scenario tests
- `tmp_path` fixture for persistence tests
- Explicit seeds everywhere for determinism
- Clear test names: `test_<what>_<condition>_<expected>`

---

## Expected Deliverable

1. Mock system at `tests/v02/framework/mock_system.py`
2. Mock system tests at `tests/v02/framework/test_mock_system.py`
3. Integration tests at `tests/v02/framework/test_framework_integration.py`
4. OFAT integration tests at `tests/v02/framework/test_ofat_integration.py`
5. Error handling tests at `tests/v02/framework/test_error_handling.py`
6. System A through-framework tests at `tests/v02/framework/test_system_a_through_framework.py`
7. Confirmation that **all** tests pass (full suite)

---

## Important Final Constraint

WP-3.6 marks the **completion of Phase 3**. After this WP:

- The framework is fully system-agnostic
- Any system implementing `SystemInterface` can be registered and run through the pipeline
- System A works identically through the framework as it did via the legacy monolithic code
- The mock system proves the framework accepts non-System-A implementations
- All framework components (registry, runner, executor, persistence, CLI) are tested

Phase 3 is not complete until all WP-3.6 tests pass, including the equivalence tests proving System A works correctly through the new framework.
