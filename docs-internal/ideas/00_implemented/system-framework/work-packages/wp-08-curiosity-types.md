# WP-08: Curiosity Drive and Spatial World Model

**Phase**: 1 -- Foundation
**Dependencies**: WP-01, WP-02, WP-03
**Scope**: Medium
**Spec reference**: Section 7.7

---

## Objective

Fully extract the curiosity drive implementation, the spatial world model, and their types from System AW into the construction kit. After this WP, System AW has no drive or memory logic of its own -- it composes entirely from kit components.

---

## What Moves

| Current location | Target location | Change |
|-----------------|----------------|--------|
| `system_aw/types.py :: CuriosityDriveOutput` | `construction_kit/drives/types.py` | Exact copy |
| `system_aw/types.py :: WorldModelState` | `construction_kit/memory/types.py` | Exact copy |
| `system_aw/drive_curiosity.py :: SystemAWCuriosityDrive` | `construction_kit/drives/curiosity.py` | Renamed to `CuriosityDrive` |
| `system_aw/drive_curiosity.py :: compute_spatial_novelty` | `construction_kit/drives/curiosity.py` | Exact copy |
| `system_aw/drive_curiosity.py :: compute_sensory_novelty` | `construction_kit/drives/curiosity.py` | Exact copy |
| `system_aw/drive_curiosity.py :: compute_composite_novelty` | `construction_kit/drives/curiosity.py` | Exact copy |
| `system_aw/drive_curiosity.py :: compute_novelty_saturation` | `construction_kit/drives/curiosity.py` | Exact copy |
| `system_aw/drive_curiosity.py :: compute_curiosity_activation` | `construction_kit/drives/curiosity.py` | Exact copy |
| `system_aw/world_model.py` (entire module) | `construction_kit/memory/world_model.py` | Exact copy, updated imports |

---

## New Files

### `src/axis/systems/construction_kit/drives/curiosity.py`

Contains `CuriosityDrive` (renamed from `SystemAWCuriosityDrive`) and all supporting pure functions.

Internal imports:
- `from axis.systems.construction_kit.drives.types import CuriosityDriveOutput`
- `from axis.systems.construction_kit.observation.types import Observation` (from WP-02)
- `from axis.systems.construction_kit.memory.types import ObservationBuffer, WorldModelState` (from WP-03 + this WP)
- `from axis.systems.construction_kit.memory.world_model import all_spatial_novelties`

No imports from any concrete system.

### `src/axis/systems/construction_kit/memory/world_model.py`

Contains all functions from `system_aw/world_model.py`:
- `DIRECTION_DELTAS` constant
- `create_world_model()` -> `WorldModelState`
- `update_world_model(state, action, moved)` -> `WorldModelState`
- `get_visit_count(state, rel_pos)` -> `int`
- `get_neighbor_position(state, direction)` -> `tuple[int, int]`
- `spatial_novelty(state, direction, k)` -> `float`
- `all_spatial_novelties(state, k)` -> `tuple[float, float, float, float]`

Internal imports:
- `from axis.systems.construction_kit.memory.types import WorldModelState`

No imports from any concrete system.

---

## Files Modified (adding to existing construction kit files)

### `src/axis/systems/construction_kit/drives/types.py`
- **Add**: `CuriosityDriveOutput` class (from WP-05, this file already has `HungerDriveOutput`)

### `src/axis/systems/construction_kit/memory/types.py`
- **Add**: `WorldModelState` class (from WP-03, this file already has `BufferEntry`, `ObservationBuffer`)

---

## Source Files Modified (System AW)

### `src/axis/systems/system_aw/types.py`
- **Remove**: `CuriosityDriveOutput`, `WorldModelState`
- **Keep**: `AgentStateAW` only
- **Update imports**: `AgentStateAW` references `ObservationBuffer` (from kit via WP-03) and `WorldModelState` (from kit via this WP):
  ```python
  from axis.systems.construction_kit.memory.types import ObservationBuffer, WorldModelState
  ```

### `src/axis/systems/system_aw/drive_curiosity.py`
- **Delete this file entirely**. Replaced by `construction_kit/drives/curiosity.py`.

### `src/axis/systems/system_aw/world_model.py`
- **Delete this file entirely**. Replaced by `construction_kit/memory/world_model.py`.

### `src/axis/systems/system_aw/system.py`
- Change curiosity drive import:
  ```python
  # Before:
  from axis.systems.system_aw.drive_curiosity import SystemAWCuriosityDrive
  # After:
  from axis.systems.construction_kit.drives.curiosity import CuriosityDrive
  ```
- Change world model import:
  ```python
  # Before:
  from axis.systems.system_aw.world_model import create_world_model
  # After:
  from axis.systems.construction_kit.memory.world_model import create_world_model
  ```
- Change: `self._curiosity_drive = SystemAWCuriosityDrive(...)` -> `self._curiosity_drive = CuriosityDrive(...)`

### `src/axis/systems/system_aw/transition.py`
- Change:
  ```python
  # Before:
  from axis.systems.system_aw.world_model import update_world_model
  # After:
  from axis.systems.construction_kit.memory.world_model import update_world_model
  ```

---

## Test Files Modified

### System AW tests

- `tests/systems/system_aw/test_drive_curiosity.py` -- major update:
  - Change: `from axis.systems.system_aw.drive_curiosity import SystemAWCuriosityDrive` -> `from axis.systems.construction_kit.drives.curiosity import CuriosityDrive`
  - Change: `from axis.systems.system_aw.types import CuriosityDriveOutput, WorldModelState` -> import from construction_kit
  - Change: `from axis.systems.system_aw.world_model import create_world_model` -> import from construction_kit
  - Rename all `SystemAWCuriosityDrive` references to `CuriosityDrive`

- `tests/systems/system_aw/test_world_model.py` -- update all imports:
  - Change: `from axis.systems.system_aw.types import WorldModelState` -> `from axis.systems.construction_kit.memory.types import WorldModelState`
  - Change: `from axis.systems.system_aw.world_model import ...` -> `from axis.systems.construction_kit.memory.world_model import ...`

- `tests/systems/system_aw/test_drive_arbitration.py` -- update `CuriosityDriveOutput` import

- `tests/systems/system_aw/test_types.py` -- update `CuriosityDriveOutput`, `WorldModelState` imports

- `tests/systems/system_aw/test_transition.py` -- update `WorldModelState` import, `create_world_model` import

- `tests/systems/system_aw/test_system_aw.py` -- update type imports

- `tests/systems/system_aw/test_worked_examples.py` -- update curiosity drive, world model, and type imports

- `tests/systems/system_aw/test_reduction.py` -- update `CuriosityDrive`, `create_world_model` imports

- `tests/systems/system_aw/test_inherited.py` -- update `WorldModelState` import if present

- `tests/systems/system_aw/test_drive_hunger.py` -- update `WorldModelState` import if present

### Construction kit tests (new)

- `tests/systems/construction_kit/test_curiosity_drive.py` -- unit tests for:
  - `CuriosityDrive`: pipeline (spatial novelty -> sensory novelty -> composite -> saturation -> activation -> contributions)
  - `compute_spatial_novelty`, `compute_sensory_novelty`, `compute_composite_novelty`
  - `compute_novelty_saturation`, `compute_curiosity_activation`
  - Edge cases: empty buffer, alpha=0 (pure sensory), alpha=1 (pure spatial)

- `tests/systems/construction_kit/test_world_model.py` -- unit tests for:
  - `create_world_model`: initial state
  - `update_world_model`: dead reckoning, visit counts
  - `spatial_novelty`, `all_spatial_novelties`: novelty decay
  - `get_visit_count`, `get_neighbor_position`: helpers

---

## Verification

1. `python -m pytest tests/ -x` -- all tests pass
2. `grep -r "SystemAWCuriosityDrive" src/` -- zero hits
3. `grep -r "from axis.systems.system_aw.world_model" src/` -- zero hits
4. `grep -r "from axis.systems.system_aw.drive_curiosity" src/` -- zero hits
5. `grep -r "class WorldModelState" src/axis/systems/system_aw/` -- zero hits
6. `grep -r "class CuriosityDriveOutput" src/axis/systems/system_aw/` -- zero hits
7. `python -c "from axis.systems.construction_kit.drives.curiosity import CuriosityDrive"` -- succeeds
8. `python -c "from axis.systems.construction_kit.memory.world_model import create_world_model"` -- succeeds

---

## Files Created
- `src/axis/systems/construction_kit/drives/curiosity.py`
- `src/axis/systems/construction_kit/memory/world_model.py`
- `tests/systems/construction_kit/test_curiosity_drive.py`
- `tests/systems/construction_kit/test_world_model.py`

## Files Deleted
- `src/axis/systems/system_aw/drive_curiosity.py`
- `src/axis/systems/system_aw/world_model.py`

## Files Modified (construction kit, adding types)
- `src/axis/systems/construction_kit/drives/types.py` (add CuriosityDriveOutput)
- `src/axis/systems/construction_kit/memory/types.py` (add WorldModelState)

## Files Modified (System AW)
- `src/axis/systems/system_aw/types.py` (remove CuriosityDriveOutput, WorldModelState; keep AgentStateAW only)
- `src/axis/systems/system_aw/system.py` (update imports)
- `src/axis/systems/system_aw/transition.py` (update imports)
- 10 test files (update imports)
