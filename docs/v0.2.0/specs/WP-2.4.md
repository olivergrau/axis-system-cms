# WP-2.4 Implementation Brief -- System A Test Suite

## Context

We are implementing the **modular architecture evolution** of the AXIS project. WP-2.1 through WP-2.3 extracted the world model, built the action engine, and restructured System A to implement `SystemInterface`.

This work package is **WP-2.4**. It provides comprehensive testing of the extracted System A, including unit tests for each sub-component, integration tests for the full decide/transition pipeline, and **behavioral equivalence tests** that verify the new implementation produces identical results to the legacy `axis_system_a` code.

### Predecessor State (After WP-2.3)

```
src/axis/
    sdk/                                    # Complete SDK contracts
    framework/
        config.py                           # FrameworkConfig, ExperimentConfig, OFAT helpers
    world/
        model.py                            # CellType, RegenerationMode, Cell, World
        factory.py                          # create_world()
        actions.py                          # ActionRegistry, movement/stay handlers
        dynamics.py                         # apply_regeneration()
    systems/system_a/
        types.py                            # AgentState, Observation, MemoryState, etc.
        config.py                           # SystemAConfig (agent, policy, transition, world_dynamics)
        sensor.py                           # SystemASensor
        drive.py                            # SystemAHungerDrive
        policy.py                           # SystemAPolicy
        transition.py                       # SystemATransition
        memory.py                           # update_memory()
        actions.py                          # handle_consume()
        system.py                           # SystemA (implements SystemInterface)
```

WP-2.3 includes basic verification tests. WP-2.4 goes deeper with comprehensive unit tests, integration tests, and behavioral equivalence validation.

### Architectural Decisions (Binding)

- **Full determinism**: Given the same seed, the new code must produce identical results to the legacy code
- **Behavioral equivalence**: The same configuration and seed through legacy `run_episode()` and new `SystemA.decide()`/`SystemA.transition()` must produce identical action sequences, energy trajectories, and termination outcomes

### Reference Documents

- `docs/v0.2.0/architecture/evolution/modular-architecture-roadmap.md` -- WP-2.4 definition
- `docs/v0.2.0/specs/WP-2.3.md` -- System A implementation details
- `docs/v0.2.0/specs/WP-2.1.md` -- World model
- `docs/v0.2.0/specs/WP-2.2.md` -- Action engine

---

## Objective

Provide comprehensive test coverage for the extracted System A and world components:

1. **Unit tests** for each sub-component in isolation
2. **Integration tests** for the full decide/transition pipeline
3. **Behavioral equivalence tests** comparing new vs legacy implementations
4. **Config validation tests** for the typed `SystemAConfig`
5. **Action registration tests** for the consume handler with `ActionRegistry`

---

## Scope

### 1. Unit Tests -- Sensor (`tests/v02/systems/system_a/test_sensor.py`)

Tests for `SystemASensor` in isolation.

| Test | Description |
|------|-------------|
| `test_center_cell_observation` | Agent on resource cell -> `current.resource > 0, current.traversability == 1.0` |
| `test_obstacle_neighbor` | Obstacle to the north -> `up.traversability == 0.0, up.resource == 0.0` |
| `test_resource_neighbor` | Resource cell to the east -> `right.resource > 0, right.traversability == 1.0` |
| `test_empty_neighbor` | Empty cell -> `traversability == 1.0, resource == 0.0` |
| `test_out_of_bounds_corner` | Agent at (0,0) -> `up.traversability == 0.0, left.traversability == 0.0` |
| `test_out_of_bounds_edge` | Agent on edge -> one direction out of bounds |
| `test_observation_dimension` | `observation.to_vector()` produces 10-element tuple |
| `test_observation_vector_values` | Vector elements match individual field values |
| `test_sensor_interface_conformance` | `isinstance(sensor, SensorInterface)` |
| `test_pure_function` | Calling observe twice with same inputs produces equal results |

### 2. Unit Tests -- Drive (`tests/v02/systems/system_a/test_drive.py`)

Tests for `SystemAHungerDrive` in isolation.

| Test | Description |
|------|-------------|
| `test_full_energy_zero_activation` | `energy == max_energy` -> `activation == 0.0` |
| `test_zero_energy_full_activation` | `energy == 0` -> `activation == 1.0` |
| `test_half_energy_half_activation` | `energy == max_energy / 2` -> `activation == 0.5` |
| `test_movement_contribution_proportional_to_resource` | Resource neighbor -> contribution = `activation * resource_value` |
| `test_consume_contribution_weighted` | `contribution = activation * consume_weight * current_resource` |
| `test_stay_contribution_negative` | `contribution = -stay_suppression * activation` |
| `test_zero_resource_neighbors_zero_movement_contributions` | No resources nearby -> all movement contributions == 0 |
| `test_contributions_tuple_length` | Always 6 elements `(up, down, left, right, consume, stay)` |
| `test_drive_interface_conformance` | `isinstance(drive, DriveInterface)` |

### 3. Unit Tests -- Policy (`tests/v02/systems/system_a/test_policy.py`)

Tests for `SystemAPolicy` in isolation.

| Test | Description |
|------|-------------|
| `test_argmax_deterministic` | Same inputs always produce same action |
| `test_argmax_selects_highest` | Action with highest contribution is selected |
| `test_sample_uses_rng` | Different seeds produce different actions (probabilistically) |
| `test_sample_reproducible` | Same seed produces same action |
| `test_obstacle_direction_zero_probability` | Non-traversable direction gets `probability == 0` |
| `test_all_actions_blocked_except_stay` | Only stay has non-zero probability when all movements blocked |
| `test_returns_policy_result` | Returns `PolicyResult` with `action: str` and `policy_data: dict` |
| `test_policy_data_contains_probabilities` | `policy_data` has `"probabilities"` key |
| `test_policy_data_contains_admissibility` | `policy_data` has `"admissibility_mask"` key |
| `test_policy_interface_conformance` | `isinstance(policy, PolicyInterface)` |
| `test_action_is_string` | `result.action` is a string like `"up"`, not an enum |

### 4. Unit Tests -- Transition (`tests/v02/systems/system_a/test_transition.py`)

Tests for `SystemATransition` in isolation.

| Test | Description |
|------|-------------|
| `test_movement_costs_energy` | After move: `energy_after == energy_before - move_cost` |
| `test_consume_costs_energy_and_gains` | After consume: `energy_after == energy_before - consume_cost + gain_factor * consumed` |
| `test_stay_costs_energy` | After stay: `energy_after == energy_before - stay_cost` |
| `test_energy_clipped_to_max` | Overconsume doesn't exceed `max_energy` |
| `test_energy_clipped_to_zero` | Energy doesn't go below 0 |
| `test_termination_on_zero_energy` | `terminated=True, termination_reason="energy_depleted"` |
| `test_no_termination_above_zero` | `terminated=False, termination_reason=None` |
| `test_memory_updated` | Memory entries count increases by 1 |
| `test_memory_fifo` | Oldest entry dropped when capacity exceeded |
| `test_returns_transition_result` | Returns `TransitionResult` with correct structure |
| `test_trace_data_contains_energy_fields` | `trace_data` has energy_before, energy_after, energy_delta |
| `test_new_state_is_agent_state` | `result.new_state` is `AgentState` |
| `test_transition_interface_conformance` | `isinstance(transition, TransitionInterface)` |

### 5. Unit Tests -- Memory (`tests/v02/systems/system_a/test_memory.py`)

Tests for `update_memory()`.

| Test | Description |
|------|-------------|
| `test_empty_memory_append` | First entry added to empty memory |
| `test_memory_ordering` | Entries in chronological order |
| `test_fifo_eviction` | Oldest entry removed when capacity exceeded |
| `test_capacity_respected` | Never exceeds capacity |
| `test_returns_new_instance` | Original memory unchanged |

### 6. Unit Tests -- Consume Handler (`tests/v02/systems/system_a/test_consume.py`)

Tests for `handle_consume()`.

| Test | Description |
|------|-------------|
| `test_consume_resource_cell` | On resource cell: `consumed=True`, resource extracted |
| `test_consume_empty_cell` | On empty cell: `consumed=False`, `resource_consumed=0.0` |
| `test_partial_consume` | `resource_value > max_consume`: extracts `max_consume`, cell retains remainder |
| `test_full_consume` | `resource_value <= max_consume`: cell becomes EMPTY |
| `test_world_cell_updated` | After consume, world cell reflects reduced resource |
| `test_returns_action_outcome` | Returns `ActionOutcome` with correct fields |
| `test_agent_position_unchanged` | `moved=False`, position same as before |

### 7. Unit Tests -- Config (`tests/v02/systems/system_a/test_config.py`)

Tests for `SystemAConfig` and sub-configs.

| Test | Description |
|------|-------------|
| `test_valid_construction` | Full config dict constructs `SystemAConfig` |
| `test_from_builder_dict` | `SystemAConfigBuilder().build()` dict parses into `SystemAConfig` |
| `test_agent_energy_bounds` | `initial_energy > max_energy` raises |
| `test_policy_config_values` | All policy fields accessible |
| `test_transition_config_values` | All transition fields accessible |
| `test_world_dynamics_defaults` | Default `resource_regen_rate == 0.0` |
| `test_frozen` | Setting fields raises |

### 8. Integration Tests -- Full Pipeline (`tests/v02/systems/system_a/test_pipeline.py`)

Tests that exercise the complete `SystemA.decide()` -> framework applies -> `SystemA.transition()` cycle.

| Test | Description |
|------|-------------|
| `test_decide_returns_valid_action` | `decide()` returns action in `action_space()` |
| `test_decide_action_is_string` | Action is a Python string |
| `test_transition_updates_energy` | After `transition()`, energy is different from before |
| `test_full_step_cycle` | decide -> apply action -> transition -> verify consistent state |
| `test_multi_step_execution` | Run 10 steps manually, verify no crashes, energy trajectory plausible |
| `test_termination_reached` | Run until energy depleted or max steps |
| `test_consume_increases_energy` | Consume on resource cell -> energy increases (net of cost) |
| `test_vitality_tracks_energy` | `vitality()` matches `energy / max_energy` at each step |

These tests manually orchestrate the framework's role: creating a world, calling `decide()`, applying the action via `ActionRegistry`, constructing a new observation, and calling `transition()`.

### 9. Behavioral Equivalence Tests (`tests/v02/systems/system_a/test_equivalence.py`)

**The most critical tests in this WP.** These verify that the new modular implementation produces identical results to the legacy `axis_system_a` code.

#### Approach

For a given configuration and seed:

1. Run the legacy `axis_system_a.runner.run_episode()` to get the reference trajectory
2. Run the new `SystemA` through the same scenario, manually orchestrating the framework's role
3. Compare step-by-step:
   - Same action selected at each timestep
   - Same energy values before and after each step
   - Same agent position after each step
   - Same termination outcome (terminated at same step, same reason)

#### Test Scenarios

| Test | Config | Seed | Expected |
|------|--------|------|----------|
| `test_equivalence_default_config` | Default test constants | `DEFAULT_SEED` | Exact match for all steps |
| `test_equivalence_high_energy` | `initial_energy=200, max_energy=200` | 42 | Longer survival, same actions |
| `test_equivalence_low_energy` | `initial_energy=10, max_energy=100` | 42 | Quick termination, same step |
| `test_equivalence_with_obstacles` | `obstacle_density=0.2` | 42 | Blocked movements match |
| `test_equivalence_with_regen` | `resource_regen_rate=0.05` | 42 | Regen effects match |
| `test_equivalence_argmax_mode` | `selection_mode="argmax"` | 42 | Deterministic, bit-exact match |
| `test_equivalence_sample_mode` | `selection_mode="sample"` | 42 | Stochastic, same seed -> same results |

#### Implementation Pattern

```python
def _run_legacy_episode(config_dict, seed, world_seed=None):
    """Run an episode using the legacy axis_system_a code."""
    from axis_system_a.config import SimulationConfig
    from axis_system_a.runner import run_episode
    from axis_system_a.world import create_world as legacy_create_world
    from axis_system_a.types import Position as LegacyPosition

    sim_config = SimulationConfig(**config_dict)
    pos = LegacyPosition(x=0, y=0)
    world = legacy_create_world(sim_config.world, pos, seed=world_seed)
    return run_episode(sim_config, world)


def _run_new_episode(framework_config, system_config_dict, seed, world_seed=None):
    """Run an episode using the new SystemA + axis.world code."""
    from axis.systems.system_a import SystemA, SystemAConfig, handle_consume
    from axis.world import World, create_world, ActionRegistry, create_action_registry, apply_regeneration
    from axis.sdk.position import Position
    import numpy as np

    # Setup
    config = SystemAConfig(**system_config_dict)
    system = SystemA(config)

    registry = create_action_registry()
    registry.register("consume", handle_consume)

    world = create_world(
        framework_config.world,
        Position(x=0, y=0),
        seed=world_seed,
        # Pass regen params if needed for world factory
    )

    agent_state = system.initialize_state(system_config_dict)
    rng = np.random.default_rng(seed)
    regen_rate = config.world_dynamics.resource_regen_rate

    # Step loop
    actions = []
    energies = []
    positions = []

    for timestep in range(framework_config.execution.max_steps):
        # Phase 1: Regeneration
        apply_regeneration(world, regen_rate=regen_rate)

        # Phase 2: System decides
        decide_result = system.decide(world, agent_state, rng)
        actions.append(decide_result.action)

        # Phase 3: Framework applies action
        context = {"max_consume": config.transition.max_consume}
        outcome = registry.apply(world, decide_result.action, context=context)

        # Phase 4: New observation for system
        sensor = system._sensor
        new_obs = sensor.observe(world, world.agent_position)

        # Phase 5: System processes outcome
        result = system.transition(agent_state, outcome, new_obs)
        agent_state = result.new_state
        energies.append(agent_state.energy)
        positions.append(world.agent_position)

        if result.terminated:
            break

    return actions, energies, positions
```

The equivalence tests compare the `actions`, `energies`, and `positions` lists from both implementations.

**Important**: The legacy and new code must use the **same RNG stream order**. The only RNG consumer is the policy (for stochastic sampling). Both implementations must call `rng.choice()` at the same point in the pipeline to maintain seed equivalence.

### 10. World Component Tests (if not already covered in WP-2.1/2.2)

Additional world tests that may be needed to support equivalence testing:

| Test | Description |
|------|-------------|
| `test_world_factory_matches_legacy` | Same config + seed -> identical grid layout |
| `test_regeneration_matches_legacy` | Same world state + regen rate -> identical cell updates |

---

## Out of Scope

Do **not** implement any of the following in WP-2.4:

- Framework episode runner (WP-3.2)
- System registry (WP-3.1)
- Any modifications to production code (tests only)
- Any modifications to `axis_system_a`
- Visualization tests
- Performance benchmarks

---

## Architectural Constraints

### 1. Legacy Code as Oracle

The legacy `axis_system_a` code is the ground truth. If the new code produces different results, the new code is wrong (unless a documented, intentional behavioral change was agreed upon -- there are none in this migration).

### 2. RNG Stream Equivalence

Both implementations must consume RNG values in the same order. The only RNG consumption point in System A is `rng.choice()` inside the policy (stochastic sampling mode). If the observation, drive, and policy pipeline is structurally identical, the RNG streams will align automatically.

### 3. Floating-Point Exactness

Energy calculations must be bit-exact between old and new code. The formulas are identical, so this should hold. If floating-point differences arise, investigate and fix the source.

### 4. Test Independence

Equivalence tests must not depend on the framework episode runner (WP-3.2). They manually orchestrate the framework's role (regeneration, action application, observation construction) to test System A in isolation.

---

## Expected File Structure

After WP-2.4, these files are **new**:

```
tests/v02/systems/system_a/test_sensor.py       # NEW (sensor unit tests)
tests/v02/systems/system_a/test_drive.py         # NEW (drive unit tests)
tests/v02/systems/system_a/test_policy.py        # NEW (policy unit tests)
tests/v02/systems/system_a/test_transition.py    # NEW (transition unit tests)
tests/v02/systems/system_a/test_memory.py        # NEW (memory unit tests)
tests/v02/systems/system_a/test_consume.py       # NEW (consume handler tests)
tests/v02/systems/system_a/test_config.py        # NEW (config validation tests)
tests/v02/systems/system_a/test_pipeline.py      # NEW (integration tests)
tests/v02/systems/system_a/test_equivalence.py   # NEW (behavioral equivalence tests)
```

May also need (if not already present):

```
tests/v02/systems/__init__.py                    # Empty (for test discovery)
tests/v02/systems/system_a/__init__.py           # Empty (for test discovery)
```

Unchanged:

```
src/axis/                                        # NO production code changes
src/axis_system_a/                               # UNCHANGED (used as oracle)
```

---

## Testing Requirements

The tests ARE the deliverable for this WP. Success criteria:

1. All unit tests pass
2. All integration tests pass
3. **All behavioral equivalence tests pass** -- this is the gate for Phase 2 completion
4. All existing tests (1400+) continue to pass
5. Total test count increases significantly (estimated 80-120 new tests)

---

## Implementation Style

- Python 3.11+
- pytest fixtures for common setup (world creation, system construction)
- `@pytest.mark.parametrize` for multi-scenario equivalence tests
- Clear test names following `test_<what>_<condition>_<expected>` pattern
- Builder pattern for config construction (using existing test builders)
- No production code changes in this WP

---

## Expected Deliverable

1. Sensor unit tests at `tests/v02/systems/system_a/test_sensor.py`
2. Drive unit tests at `tests/v02/systems/system_a/test_drive.py`
3. Policy unit tests at `tests/v02/systems/system_a/test_policy.py`
4. Transition unit tests at `tests/v02/systems/system_a/test_transition.py`
5. Memory unit tests at `tests/v02/systems/system_a/test_memory.py`
6. Consume handler tests at `tests/v02/systems/system_a/test_consume.py`
7. Config tests at `tests/v02/systems/system_a/test_config.py`
8. Integration tests at `tests/v02/systems/system_a/test_pipeline.py`
9. Behavioral equivalence tests at `tests/v02/systems/system_a/test_equivalence.py`
10. Confirmation that all tests (old + new) pass

---

## Important Final Constraint

The behavioral equivalence tests are the **primary validation** that the Phase 2 extraction is correct. They prove that the modular architecture produces identical results to the monolithic v0.1.0 code.

These tests must be:

- **Deterministic**: Same seed always produces same result
- **Comprehensive**: Cover different configs, seeds, and scenarios
- **Step-level**: Compare action, energy, and position at EVERY step, not just final outcomes
- **Independent**: Do not depend on the framework episode runner (WP-3.2)

If any equivalence test fails, it means the extraction introduced a behavioral change. The new code must be fixed to match the legacy behavior exactly. There are no acceptable regressions.

Phase 2 is not complete until all equivalence tests pass.
