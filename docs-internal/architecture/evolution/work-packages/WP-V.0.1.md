# WP-V.0.1 Implementation Brief -- Extend SDK Trace Types

## Context

We are implementing the **three-tier visualization architecture** for the AXIS v0.2.0 project. The visualization system requires world-specific metadata to flow through the replay pipeline so that world visualization adapters can render world-specific indicators (wrap edges for toroidal, hotspot markers for signal_landscape) and so the viewer can resolve the correct adapters by world type.

This work package is the first of Phase V-0 (Replay Contract Extension). It extends the existing SDK trace types to carry world metadata alongside the already-present system metadata.

### Predecessor State

The replay contract types were established in WP-1.3 and are stable:

```
src/axis/sdk/
    __init__.py             # Exports all SDK types
    trace.py                # BaseStepTrace, BaseEpisodeTrace
    snapshot.py             # WorldSnapshot, snapshot_world
    world_types.py          # CellView, WorldView, MutableWorldProtocol, ActionOutcome, BaseWorldConfig
    position.py             # Position
    interfaces.py           # SystemInterface and sub-component interfaces
    types.py                # DecideResult, TransitionResult, PolicyResult
    actions.py              # Base action constants
```

### Current Trace Types

`BaseStepTrace` carries per-step system-specific data via `system_data: dict[str, Any]`. There is no equivalent field for world-specific per-step data.

`BaseEpisodeTrace` carries `system_type: str` for system identification. There are no fields for world identification (`world_type`, `world_config`).

`MutableWorldProtocol` defines the mutable world contract (`tick()`, `extract_resource()`, `snapshot()`, etc.) but has no method for returning per-step world metadata.

### Architectural Decisions (Binding)

From `visualization-architecture.md`:

- **D2**: `world_data` parallel to `system_data` in `BaseStepTrace` -- symmetric design
- **D7**: `world_config` stored in episode trace -- replay viewer parameterizes rendering from trace data
- Backward-compatible defaults: `world_data={}`, `world_type="grid_2d"`, `world_config={}`

### Reference Documents

- `docs/architecture/evolution/visualization-architecture.md` -- Sections 9.1-9.3
- `docs/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.0.1

---

## Objective

Extend the SDK trace types and world protocol to support world metadata in the replay pipeline:

1. Add `world_data: dict[str, Any]` to `BaseStepTrace` -- per-step world metadata
2. Add `world_type: str` and `world_config: dict[str, Any]` to `BaseEpisodeTrace` -- world identity
3. Add `world_metadata() -> dict[str, Any]` to `MutableWorldProtocol` -- the method worlds implement to expose per-step metadata

All additions have backward-compatible defaults so existing code and tests continue to work without modification.

---

## Scope

### 1. Extend `BaseStepTrace`

**File**: `src/axis/sdk/trace.py`

Add a new field after `system_data`:

```python
    # ── World-specific per-step metadata ──
    world_data: dict[str, Any] = Field(default_factory=dict)
```

This parallels `system_data`. The world visualization adapter interprets `world_data` just as the system visualization adapter interprets `system_data`.

**Placement**: After the `system_data` field, with a section comment `# ── World-specific per-step metadata ──`.

**Docstring update**: Add to the class docstring:

```
World-specific metadata (hotspot positions, topology info) is packed
into world_data as an opaque dict. Only the world's visualization
adapter interprets it.
```

### 2. Extend `BaseEpisodeTrace`

**File**: `src/axis/sdk/trace.py`

Add two new fields after `final_position`:

```python
    # ── World identity (for visualization adapter resolution) ──
    world_type: str = "grid_2d"
    world_config: dict[str, Any] = Field(default_factory=dict)
```

**Purpose**:

| Field | Purpose |
|-------|---------|
| `world_type` | Routing key for the visualization registry to resolve the correct `WorldVisualizationAdapter` |
| `world_config` | World configuration as dict, so the viewer can parameterize rendering (grid dimensions, hotspot count, etc.) without re-parsing config files |

**Default values**: `world_type="grid_2d"` and `world_config={}` ensure backward compatibility with episode traces persisted before these fields existed.

**Docstring update**: Add to the class docstring:

```
World identity fields (world_type, world_config) enable the
visualization layer to resolve the correct world adapter for
rendering. Defaults ensure backward compatibility with replays
saved before these fields were added.
```

### 3. Add `world_metadata()` to `MutableWorldProtocol`

**File**: `src/axis/sdk/world_types.py`

Add a new method to `MutableWorldProtocol`:

```python
    def world_metadata(self) -> dict[str, Any]:
        """Return per-step metadata for replay visualization.

        Called by the framework runner after tick() on each step.
        The returned dict is stored as world_data in BaseStepTrace.

        Default: return {} (no world-specific metadata).
        Override to expose internal state such as hotspot positions.
        """
        ...
```

**Placement**: After the `snapshot()` method, with a comment line preceding it.

**Design notes**:

- This is a protocol method with `...` body (not an implementation)
- Worlds that have no per-step varying state (grid_2d) return `{}` from their concrete implementation
- Worlds with dynamic state (signal_landscape hotspots, toroidal wrap info) override to return meaningful data
- The `Any` import is already present in `world_types.py`

### 4. No Changes to `__init__.py`

No new public types are introduced -- only existing types gain new fields. The `__init__.py` exports remain unchanged.

---

## Out of Scope

Do **not** implement any of the following in WP-V.0.1:

- Concrete `world_metadata()` implementations on world classes (WP-V.0.2)
- Framework runner changes to capture world metadata (WP-V.0.3)
- Visualization types (`CellLayout`, `CellColorConfig`, etc.) (WP-V.1.1)
- Adapter protocols (WP-V.1.2)
- Any PySide6 or visualization code
- Any modifications to `src/axis/framework/` or `src/axis/world/`

---

## Architectural Constraints

### 1. Backward Compatibility

All new fields have defaults. Existing code that constructs `BaseStepTrace` or `BaseEpisodeTrace` without the new fields must continue to work:

```python
# This must still work (no world_data argument):
trace = BaseStepTrace(
    timestep=0, action="up",
    world_before=snap, world_after=snap,
    agent_position_before=pos, agent_position_after=pos,
    vitality_before=1.0, vitality_after=0.9,
    terminated=False,
)
assert trace.world_data == {}

# This must still work (no world_type/world_config):
episode = BaseEpisodeTrace(
    system_type="system_a",
    steps=(trace,), total_steps=1,
    termination_reason="max_steps_reached",
    final_vitality=0.9, final_position=pos,
)
assert episode.world_type == "grid_2d"
assert episode.world_config == {}
```

### 2. Frozen Models

All trace types remain frozen (`ConfigDict(frozen=True)`). The new fields follow the same pattern.

### 3. Symmetric Design

`world_data` parallels `system_data`. Both are `dict[str, Any]` with `Field(default_factory=dict)`. The framework assembles both; only the respective visualization adapter interprets them.

### 4. Protocol Method

`world_metadata()` is added to `MutableWorldProtocol` as a protocol method. It must NOT be added to `WorldView` (read-only protocol) since it is a framework-internal concern -- systems never call it.

### 5. No Import Changes

`world_types.py` already imports `Any` from `typing`. No new imports are needed. `trace.py` already imports `Any` and `Field`. No new imports are needed.

---

## Testing Requirements

### Extend existing replay contract tests (`tests/sdk/test_replay_contract.py`)

Add the following tests (do not remove or modify existing tests):

1. **`test_step_trace_world_data_default`**:
   - Construct `BaseStepTrace` without `world_data` argument
   - Assert `trace.world_data == {}`

2. **`test_step_trace_world_data_explicit`**:
   - Construct `BaseStepTrace` with `world_data={"hotspots": [{"cx": 1.5, "cy": 2.3}]}`
   - Assert `trace.world_data["hotspots"][0]["cx"] == 1.5`

3. **`test_step_trace_world_data_round_trip`**:
   - Construct with `world_data` containing nested dict
   - `model_dump()` and reconstruct via `BaseStepTrace(**data)`
   - Assert round-trip produces equal trace

4. **`test_episode_trace_world_type_default`**:
   - Construct `BaseEpisodeTrace` without `world_type` argument
   - Assert `episode.world_type == "grid_2d"`

5. **`test_episode_trace_world_config_default`**:
   - Construct `BaseEpisodeTrace` without `world_config` argument
   - Assert `episode.world_config == {}`

6. **`test_episode_trace_world_identity_explicit`**:
   - Construct with `world_type="signal_landscape"` and `world_config={"grid_width": 20, "num_hotspots": 3}`
   - Assert both fields stored correctly

7. **`test_episode_trace_world_identity_round_trip`**:
   - Construct with world identity fields, `model_dump()`, reconstruct
   - Assert equality

8. **`test_mutable_world_protocol_has_world_metadata`**:
   - Verify that `MutableWorldProtocol` has a `world_metadata` attribute (using `hasattr` on the protocol class)

### Existing tests

All existing tests in `tests/` must still pass without modification.

---

## Implementation Style

- Python 3.11+
- Frozen Pydantic `BaseModel` fields with `Field(default_factory=dict)` for mutable defaults
- Type hints from `typing.Any`
- Section comments matching existing style (`# ── Section name ──`)
- Minimal changes -- add fields and docstring lines, do not restructure existing code

---

## Expected Deliverable

1. Modified `src/axis/sdk/trace.py` with `world_data` on `BaseStepTrace` and `world_type`/`world_config` on `BaseEpisodeTrace`
2. Modified `src/axis/sdk/world_types.py` with `world_metadata()` on `MutableWorldProtocol`
3. Extended `tests/sdk/test_replay_contract.py` with new tests
4. Confirmation that all existing tests still pass

---

## Expected File Structure

After WP-V.0.1, these files are **modified**:

```
src/axis/sdk/trace.py                          # MODIFIED (3 new fields)
src/axis/sdk/world_types.py                    # MODIFIED (1 new protocol method)
tests/sdk/test_replay_contract.py          # MODIFIED (new tests appended)
```

Unchanged:

```
src/axis/sdk/__init__.py                       # UNCHANGED
src/axis/sdk/snapshot.py                       # UNCHANGED
src/axis/sdk/interfaces.py                     # UNCHANGED
src/axis/sdk/types.py                          # UNCHANGED
src/axis/sdk/position.py                       # UNCHANGED
src/axis/sdk/actions.py                        # UNCHANGED
src/axis/world/                                # UNCHANGED (world_metadata implementations are WP-V.0.2)
src/axis/framework/                            # UNCHANGED (runner changes are WP-V.0.3)
```

---

## Important Final Constraint

This work package adds **three fields and one protocol method**. It is intentionally minimal. The fields have defaults that preserve all existing behavior. No existing code path changes. The protocol method is added but not yet implemented by any world class -- that is WP-V.0.2.

Verify backward compatibility by confirming that the entire existing test suite passes without modification after these changes.
