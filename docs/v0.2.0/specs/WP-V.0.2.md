# WP-V.0.2 Implementation Brief -- Implement World Metadata on Existing Worlds

## Context

WP-V.0.1 added `world_metadata() -> dict[str, Any]` to `MutableWorldProtocol` and extended the trace types with `world_data`, `world_type`, and `world_config`. No world class implements `world_metadata()` yet.

This work package adds concrete `world_metadata()` implementations to all three existing world types so that the framework runner (WP-V.0.3) can capture meaningful per-step metadata.

### Predecessor State (After WP-V.0.1)

```
src/axis/sdk/world_types.py         # MutableWorldProtocol now has world_metadata()
src/axis/sdk/trace.py               # BaseStepTrace has world_data, BaseEpisodeTrace has world_type/world_config
```

World classes that must implement `world_metadata()`:

| World class | File | Has per-step varying state? |
|------------|------|---------------------------|
| `World` (grid_2d) | `src/axis/world/grid_2d/model.py` | No -- bounded rectangular grid, no dynamic features |
| `ToroidalWorld` | `src/axis/world/toroidal/model.py` | No -- same cell model, topology is static |
| `SignalLandscapeWorld` | `src/axis/world/signal_landscape/model.py` | **Yes** -- hotspots drift each tick |

### Architectural Decisions (Binding)

From `visualization-architecture.md` Section 9.5:

| World type | `world_data` per step | `world_config` snapshot |
|------------|----------------------|------------------------|
| `grid_2d` | `{}` | `{grid_width, grid_height, obstacle_density, ...}` |
| `toroidal` | `{"topology": "toroidal"}` | `{grid_width, grid_height, ...}` |
| `signal_landscape` | `{"hotspots": [{"cx": f, "cy": f, "radius": f, "intensity": f}, ...]}` | `{grid_width, grid_height, num_hotspots, ...}` |

### Reference Documents

- `docs/v0.2.0/architecture/evolution/visualization-architecture.md` -- Sections 9.3, 9.5
- `docs/v0.2.0/architecture/evolution/visualization-architecture-roadmap.md` -- WP-V.0.2

---

## Objective

Implement `world_metadata()` on all three existing world classes, returning per-step metadata appropriate for visualization. The implementations are minimal: `grid_2d` returns `{}`, `toroidal` returns static topology info, `signal_landscape` returns current hotspot positions.

---

## Scope

### 1. `World.world_metadata()` (grid_2d)

**File**: `src/axis/world/grid_2d/model.py`

Add a method to the `World` class:

```python
    def world_metadata(self) -> dict[str, Any]:
        """Return per-step metadata for replay visualization.

        The grid_2d world has no per-step varying state beyond the grid
        itself (which is captured in WorldSnapshot). Returns empty dict.
        """
        return {}
```

**Import**: Add `Any` to the existing `typing` imports. The file currently has `from __future__ import annotations` but no `from typing import Any`. Add:

```python
from typing import Any
```

### 2. `ToroidalWorld.world_metadata()` (toroidal)

**File**: `src/axis/world/toroidal/model.py`

Add a method to the `ToroidalWorld` class:

```python
    def world_metadata(self) -> dict[str, Any]:
        """Return per-step metadata for replay visualization.

        Returns static topology information. The toroidal world's
        topology does not change between steps, but the metadata
        identifies this world as toroidal for visualization purposes.
        """
        return {"topology": "toroidal"}
```

**Import**: Add `Any` to the imports. The file currently has no `typing` imports beyond `annotations`. Add:

```python
from typing import Any
```

### 3. `SignalLandscapeWorld.world_metadata()` (signal_landscape)

**File**: `src/axis/world/signal_landscape/model.py`

Add a method to the `SignalLandscapeWorld` class:

```python
    def world_metadata(self) -> dict[str, Any]:
        """Return per-step metadata for replay visualization.

        Returns current hotspot positions and parameters. These change
        each tick as hotspots drift, so the visualization layer needs
        this data per-step to render hotspot markers.
        """
        return {
            "hotspots": [
                {
                    "cx": h.cx,
                    "cy": h.cy,
                    "radius": h.radius,
                    "intensity": h.intensity,
                }
                for h in self._hotspots
            ],
        }
```

**Import**: The file already has `from typing import Any`.

**Design notes**:

- `self._hotspots` is a `list[Hotspot]` where `Hotspot` has `cx`, `cy`, `radius`, `intensity` attributes (plain class with `__slots__`, defined in `dynamics.py`)
- The method serializes hotspot state into plain dicts, suitable for JSON serialization and storage in `BaseStepTrace.world_data`
- Hotspot positions change each `tick()` due to `drift_hotspots()`, so this metadata varies per step

### 4. Method Placement

In all three world classes, place `world_metadata()` after the `snapshot()` method, keeping the public API surface grouped together.

---

## Out of Scope

Do **not** implement any of the following in WP-V.0.2:

- Framework runner changes to call `world_metadata()` (WP-V.0.3)
- Visualization types, protocols, or adapters (WP-V.1.x)
- Any changes to `BaseWorldConfig` or world factory code
- Any changes to world dynamics or cell models
- `world_config` dict construction (that happens in the runner, WP-V.0.3)

---

## Architectural Constraints

### 1. Protocol Conformance

After these changes, all three world classes must satisfy `MutableWorldProtocol` including the new `world_metadata()` method. This can be verified with:

```python
from axis.sdk.world_types import MutableWorldProtocol

assert isinstance(world_instance, MutableWorldProtocol)
```

### 2. Return Type Consistency

All implementations return `dict[str, Any]`. The returned dicts must be JSON-serializable (only primitive types, lists, and nested dicts -- no Pydantic models, numpy arrays, or custom objects).

### 3. No Side Effects

`world_metadata()` is a pure read operation. It must not mutate the world state.

### 4. Idempotent

Multiple calls to `world_metadata()` on the same world state must return identical results.

---

## Testing Requirements

### Grid_2d world metadata tests

Add to `tests/v02/world/test_world_model.py`:

1. **`test_world_metadata_returns_empty_dict`**:
   - Create a `World` instance with a simple grid
   - Assert `world.world_metadata() == {}`

2. **`test_world_metadata_stable_across_ticks`**:
   - Create a `World`, call `tick()`, call `world_metadata()`
   - Assert still `{}`

### Toroidal world metadata tests

Add to `tests/v02/world/test_toroidal.py`:

3. **`test_toroidal_world_metadata`**:
   - Create a `ToroidalWorld` instance
   - Assert `world.world_metadata() == {"topology": "toroidal"}`

4. **`test_toroidal_world_metadata_stable_across_ticks`**:
   - Create a `ToroidalWorld`, call `tick()`, call `world_metadata()`
   - Assert still `{"topology": "toroidal"}`

### Signal landscape world metadata tests

Add to `tests/v02/world/test_signal_landscape.py`:

5. **`test_signal_landscape_world_metadata_structure`**:
   - Create a `SignalLandscapeWorld` with known hotspots
   - Call `world_metadata()`
   - Assert result has key `"hotspots"`
   - Assert `len(result["hotspots"])` matches number of hotspots
   - Assert each hotspot dict has keys `"cx"`, `"cy"`, `"radius"`, `"intensity"`

6. **`test_signal_landscape_world_metadata_values`**:
   - Create a `SignalLandscapeWorld` with a single hotspot at known position
   - Assert `result["hotspots"][0]["cx"]` and `"cy"` match the hotspot's initial position

7. **`test_signal_landscape_world_metadata_changes_after_tick`**:
   - Create a `SignalLandscapeWorld` with `drift_speed > 0`
   - Capture `world_metadata()` before tick
   - Call `world.tick()`
   - Capture `world_metadata()` after tick
   - Assert hotspot positions have changed (at least one of cx/cy differs)

8. **`test_signal_landscape_world_metadata_json_serializable`**:
   - Call `world_metadata()`, pass result through `json.dumps()`
   - Assert no serialization error

### Protocol conformance

9. **`test_world_protocol_conformance_with_world_metadata`**:
   - For each world type, create an instance and verify `isinstance(w, MutableWorldProtocol)` (this may already exist -- extend if needed)
   - Verify `hasattr(w, 'world_metadata')` and it is callable

### Existing tests

All existing tests must continue to pass.

---

## Implementation Style

- Python 3.11+
- Minimal additions: one method per world class, one import per file (where needed)
- JSON-serializable return values (plain dicts with float/str/int/list)
- Docstrings explaining what metadata is returned and why

---

## Expected Deliverable

1. Modified `src/axis/world/grid_2d/model.py` with `World.world_metadata()`
2. Modified `src/axis/world/toroidal/model.py` with `ToroidalWorld.world_metadata()`
3. Modified `src/axis/world/signal_landscape/model.py` with `SignalLandscapeWorld.world_metadata()`
4. Extended test files with world metadata tests
5. Confirmation that all existing tests still pass

---

## Expected File Structure

After WP-V.0.2, these files are **modified**:

```
src/axis/world/grid_2d/model.py                # MODIFIED (world_metadata method + Any import)
src/axis/world/toroidal/model.py               # MODIFIED (world_metadata method + Any import)
src/axis/world/signal_landscape/model.py       # MODIFIED (world_metadata method)
tests/v02/world/test_world_model.py            # MODIFIED (new tests)
tests/v02/world/test_toroidal.py               # MODIFIED (new tests)
tests/v02/world/test_signal_landscape.py       # MODIFIED (new tests)
```

Unchanged:

```
src/axis/sdk/                                  # UNCHANGED (modified in WP-V.0.1)
src/axis/framework/                            # UNCHANGED (modified in WP-V.0.3)
src/axis/world/grid_2d/dynamics.py             # UNCHANGED
src/axis/world/grid_2d/factory.py              # UNCHANGED
src/axis/world/toroidal/factory.py             # UNCHANGED
src/axis/world/toroidal/config.py              # UNCHANGED
src/axis/world/signal_landscape/dynamics.py    # UNCHANGED
src/axis/world/signal_landscape/factory.py     # UNCHANGED
src/axis/world/signal_landscape/config.py      # UNCHANGED
```

---

## Important Final Constraint

Each `world_metadata()` implementation is a single method returning a plain dict. The grid_2d and toroidal implementations are trivial (return constant dicts). The signal_landscape implementation is slightly more involved (iterates `self._hotspots`) but is still a pure read with no side effects.

Do not add any helper methods, utility functions, or intermediate types. The hotspot serialization is a simple list comprehension inside the method body.
