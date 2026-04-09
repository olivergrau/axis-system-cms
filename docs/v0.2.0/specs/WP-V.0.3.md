# WP-V.0.3 Implementation Brief -- Capture World Metadata in Framework Runner

## Context

WP-V.0.1 extended the SDK trace types with `world_data` (per-step), `world_type` and `world_config` (per-episode). WP-V.0.2 implemented `world_metadata()` on all three world classes. The framework runner does not yet call `world_metadata()` or populate the new trace fields.

This work package completes Phase V-0 by wiring the runner to capture world metadata on every step and to include world identity in the episode trace.

### Predecessor State (After WP-V.0.2)

The runner in `src/axis/framework/runner.py` builds `BaseStepTrace` with `intermediate_snapshots={}` and `system_data` from the system's decide/transition results. It does not call `world.world_metadata()` and does not pass `world_data` to `BaseStepTrace`. The `BaseEpisodeTrace` is constructed without `world_type` or `world_config`.

Current `_run_step()` (lines 58-78):
```python
    step_trace = BaseStepTrace(
        timestep=timestep,
        action=decide_result.action,
        world_before=world_before,
        world_after=world_after,
        intermediate_snapshots={},
        agent_position_before=position_before,
        agent_position_after=position_after,
        vitality_before=vitality_before,
        vitality_after=vitality_after,
        terminated=transition_result.terminated,
        termination_reason=transition_result.termination_reason,
        system_data={
            "decision_data": decide_result.decision_data,
            "trace_data": transition_result.trace_data,
        },
    )
```

Current `run_episode()` (lines 120-128):
```python
    return BaseEpisodeTrace(
        system_type=system.system_type(),
        steps=tuple(steps),
        total_steps=len(steps),
        termination_reason=termination_reason,
        final_vitality=system.vitality(agent_state),
        final_position=world.agent_position,
    )
```

### Architectural Decisions (Binding)

From `visualization-architecture.md` Section 9.4:

- **In `_run_step()`**: After `world.tick()`, call `world.world_metadata()` and include the result as `world_data` in the `BaseStepTrace`
- **In `run_episode()`**: Include `world_type` from `world_config` and `world_config` as a dict in `BaseEpisodeTrace`

### Reference Documents

- `docs/v0.2.0/architecture/evolution/visualization-architecture.md` -- Section 9.4
- `docs/v0.2.0/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.0.3

---

## Objective

Modify the framework runner to:

1. Call `world.world_metadata()` after `world.tick()` and pass the result as `world_data` in `BaseStepTrace`
2. Accept `world_config` as a parameter in `run_episode()` and include `world_type` and `world_config` in `BaseEpisodeTrace`

After this change, persisted replays carry full world metadata for the visualization layer to consume.

---

## Scope

### 1. Modify `_run_step()` to capture world metadata

**File**: `src/axis/framework/runner.py`

After the `world.tick()` call (line 42) and before capturing the AFTER_ACTION snapshot, call `world.world_metadata()`:

```python
    # 3. World advances its own dynamics (e.g. regeneration)
    world.tick()

    # 3a. Capture world metadata (after dynamics, before action)
    world_data = world.world_metadata()
```

Then include `world_data` in the `BaseStepTrace` construction:

```python
    step_trace = BaseStepTrace(
        timestep=timestep,
        action=decide_result.action,
        world_before=world_before,
        world_after=world_after,
        intermediate_snapshots={},
        agent_position_before=position_before,
        agent_position_after=position_after,
        vitality_before=vitality_before,
        vitality_after=vitality_after,
        terminated=transition_result.terminated,
        termination_reason=transition_result.termination_reason,
        system_data={
            "decision_data": decide_result.decision_data,
            "trace_data": transition_result.trace_data,
        },
        world_data=world_data,
    )
```

**Timing decision**: `world_metadata()` is called after `tick()` but before `registry.apply()`. This captures the world's dynamic state (e.g. hotspot positions) after dynamics have run but before the agent's action mutates the world. This timing matches the architecture spec: "After world.tick(), call world.world_metadata()".

### 2. Modify `run_episode()` to accept and pass world identity

**File**: `src/axis/framework/runner.py`

Add `world_config` parameter to `run_episode()`:

```python
def run_episode(
    system: SystemInterface,
    world: MutableWorldProtocol,
    registry: ActionRegistry,
    *,
    max_steps: int,
    seed: int,
    world_config: BaseWorldConfig | None = None,
) -> BaseEpisodeTrace:
```

The parameter is optional with `None` default to maintain backward compatibility with call sites that don't pass it yet.

Include world identity in the `BaseEpisodeTrace` construction:

```python
    world_type = world_config.world_type if world_config is not None else "grid_2d"
    world_config_dict = (
        world_config.model_dump() if world_config is not None else {}
    )

    return BaseEpisodeTrace(
        system_type=system.system_type(),
        steps=tuple(steps),
        total_steps=len(steps),
        termination_reason=termination_reason,
        final_vitality=system.vitality(agent_state),
        final_position=world.agent_position,
        world_type=world_type,
        world_config=world_config_dict,
    )
```

**Design notes**:

- `world_config.model_dump()` serializes the full world config (including extras like `grid_width`, `grid_height`, etc.) into a plain dict
- The `world_type` field comes from `BaseWorldConfig.world_type` which is always present (defaults to `"grid_2d"`)
- When `world_config is None` (backward compat), defaults match `BaseEpisodeTrace` defaults

### 3. Update `_run_single_episode()` in `RunExecutor`

**File**: `src/axis/framework/run.py`

Pass `world_config` through to `run_episode()`:

```python
    def _run_single_episode(
        self,
        system: Any,
        config: RunConfig,
        episode_seed: int,
    ) -> BaseEpisodeTrace:
        """Run one episode and return its trace."""
        world_config = config.framework_config.world

        world, registry = setup_episode(
            system,
            world_config,
            config.agent_start_position,
            seed=episode_seed,
        )

        return run_episode(
            system,
            world,
            registry,
            max_steps=config.framework_config.execution.max_steps,
            seed=episode_seed,
            world_config=world_config,
        )
```

The only change is adding `world_config=world_config` to the `run_episode()` call. The `world_config` variable already exists in this method.

### 4. Update `run_episode()` docstring

Update the docstring to document the new parameter:

```
    world_config : World configuration (optional). When provided, world_type
        and world_config are included in the episode trace for visualization
        adapter resolution.
```

---

## Out of Scope

Do **not** implement any of the following in WP-V.0.3:

- Visualization types, protocols, or adapters (WP-V.1.x)
- Visualization registry or adapter resolution (WP-V.1.4)
- Any PySide6 or UI code
- Changes to `setup_episode()` (it already creates the world correctly)
- Changes to the CLI
- Any modifications to world classes (done in WP-V.0.2)
- Any modifications to SDK trace types (done in WP-V.0.1)

---

## Architectural Constraints

### 1. Backward Compatibility

The `world_config` parameter in `run_episode()` is optional (`None` default). Existing call sites that don't pass it continue to work, producing `BaseEpisodeTrace` with `world_type="grid_2d"` and `world_config={}` defaults.

### 2. `world_metadata()` Call Timing

Called after `world.tick()`, before `registry.apply()`. This captures post-dynamics, pre-action world state. The hotspot positions in signal_landscape reflect the current tick's drift, not the previous tick's.

### 3. No Performance Concern

`world_metadata()` returns a small dict (grid_2d: `{}`, toroidal: 1-key dict, signal_landscape: list of ~3-5 hotspot dicts). The overhead is negligible.

### 4. Serialization Safety

`world_config.model_dump()` produces a JSON-serializable dict. `world.world_metadata()` returns a JSON-serializable dict (guaranteed by WP-V.0.2). Both are safe for `BaseStepTrace`/`BaseEpisodeTrace` frozen model fields.

---

## Testing Requirements

### Extend runner tests (`tests/v02/framework/test_runner.py`)

Add the following tests:

1. **`test_step_trace_has_world_data`**:
   - Run a default episode via `_run_default_episode()`
   - Assert `isinstance(step.world_data, dict)` for each step
   - For grid_2d world, assert `step.world_data == {}`

2. **`test_episode_trace_has_world_type`**:
   - Run a default episode
   - Assert `trace.world_type == "grid_2d"`

3. **`test_episode_trace_has_world_config`**:
   - Run a default episode
   - Assert `isinstance(trace.world_config, dict)`
   - Assert `trace.world_config["world_type"] == "grid_2d"`
   - Assert `trace.world_config["grid_width"] == DEFAULT_GRID_WIDTH`
   - Assert `trace.world_config["grid_height"] == DEFAULT_GRID_HEIGHT`

4. **`test_run_episode_without_world_config_backward_compat`**:
   - Call `run_episode()` without the `world_config` parameter (as existing tests do)
   - Assert `trace.world_type == "grid_2d"` (default)
   - Assert `trace.world_config == {}` (default)

### Signal landscape world_data integration test

Add a new test file or extend existing: `tests/v02/framework/test_runner_world_metadata.py`

5. **`test_signal_landscape_world_data_in_trace`**:
   - Create a `SignalLandscapeWorld` (using factory or manual construction)
   - Create a system (System A or mock)
   - Run an episode with `world_config` set to signal_landscape config
   - Assert `step.world_data` contains `"hotspots"` key for each step
   - Assert hotspot list is non-empty
   - Assert each hotspot has `"cx"`, `"cy"`, `"radius"`, `"intensity"` keys

6. **`test_signal_landscape_world_type_in_episode_trace`**:
   - Run the same signal_landscape episode
   - Assert `trace.world_type == "signal_landscape"`

7. **`test_toroidal_world_data_in_trace`**:
   - Create a `ToroidalWorld`, run an episode
   - Assert `step.world_data == {"topology": "toroidal"}` for each step
   - Assert `trace.world_type == "toroidal"`

### Update `_run_default_episode` helper

Modify the existing `_run_default_episode()` helper to pass `world_config` to `run_episode()`:

```python
def _run_default_episode(
    *,
    config_dict: dict[str, Any] | None = None,
    max_steps: int = DEFAULT_MAX_STEPS,
    seed: int = DEFAULT_SEED,
) -> BaseEpisodeTrace:
    """Run an episode with default settings via the framework runner."""
    cfg = config_dict or _default_config_dict()
    wc = _world_config()
    system = create_system("system_a", cfg)
    world, registry = setup_episode(
        system, wc, Position(x=0, y=0), seed=seed,
    )
    return run_episode(
        system, world, registry,
        max_steps=max_steps,
        seed=seed,
        world_config=wc,
    )
```

### Existing tests

All existing tests must continue to pass. The backward-compatible `world_config=None` default ensures this.

---

## Implementation Style

- Python 3.11+
- Optional parameter with `None` default for backward compatibility
- Inline `world_type` / `world_config_dict` computation before the return statement (no helper functions)
- Comment `# 3a. Capture world metadata` matching existing step numbering style

---

## Expected Deliverable

1. Modified `src/axis/framework/runner.py`: `_run_step()` calls `world.world_metadata()` and passes `world_data`; `run_episode()` accepts `world_config` and passes `world_type`/`world_config`
2. Modified `src/axis/framework/run.py`: `_run_single_episode()` passes `world_config` to `run_episode()`
3. Extended `tests/v02/framework/test_runner.py` with world metadata tests
4. New or extended `tests/v02/framework/test_runner_world_metadata.py` with signal_landscape and toroidal integration tests
5. Confirmation that all existing tests still pass

---

## Expected File Structure

After WP-V.0.3, these files are **modified**:

```
src/axis/framework/runner.py                           # MODIFIED (_run_step + run_episode)
src/axis/framework/run.py                              # MODIFIED (_run_single_episode)
tests/v02/framework/test_runner.py                     # MODIFIED (new tests + helper update)
tests/v02/framework/test_runner_world_metadata.py      # NEW (integration tests for non-grid_2d worlds)
```

Unchanged:

```
src/axis/sdk/                                          # UNCHANGED (modified in WP-V.0.1)
src/axis/world/                                        # UNCHANGED (modified in WP-V.0.2)
src/axis/framework/config.py                           # UNCHANGED
src/axis/framework/registry.py                         # UNCHANGED
src/axis/framework/cli.py                              # UNCHANGED
```

---

## Important Final Constraint

This work package makes **two surgical changes** to the runner:

1. One line added to `_run_step()`: `world_data = world.world_metadata()` after `world.tick()`, plus passing `world_data=world_data` to `BaseStepTrace`.
2. One parameter added to `run_episode()`: `world_config`, plus 4 lines computing and passing `world_type`/`world_config` to `BaseEpisodeTrace`.
3. One line changed in `run.py`: adding `world_config=world_config` to the `run_episode()` call.

The total production code change is approximately 10 lines. Keep it minimal. The integration tests for signal_landscape and toroidal are more substantial but verify that the full pipeline works end-to-end: world dynamics produce metadata, the runner captures it, and the trace carries it.
