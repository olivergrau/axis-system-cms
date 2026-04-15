# WP-05: Hunger Drive

**Phase**: 1 -- Foundation
**Dependencies**: WP-01, WP-02
**Scope**: Small
**Spec reference**: Section 7.4

---

## Objective

Extract `HungerDriveOutput` and `SystemAHungerDrive` from System A into the construction kit. The hunger drive is used directly by System A and wrapped by System AW. After extraction, both systems use `HungerDrive` from the kit directly.

---

## What Moves

| Current location | Target location | Change |
|-----------------|----------------|--------|
| `system_a/types.py :: HungerDriveOutput` | `construction_kit/drives/types.py` | Exact copy |
| `system_a/drive.py :: SystemAHungerDrive` | `construction_kit/drives/hunger.py` | Renamed to `HungerDrive` |

---

## New Files

### `src/axis/systems/construction_kit/drives/types.py`

Contains `HungerDriveOutput` -- exact copy from `system_a/types.py` (lines 57-70).

No dependencies on other construction_kit packages (self-contained Pydantic model).

### `src/axis/systems/construction_kit/drives/hunger.py`

Contains `HungerDrive` -- exact copy of `SystemAHungerDrive` from `system_a/drive.py`, renamed.

Internal imports:
- `from axis.systems.construction_kit.drives.types import HungerDriveOutput`
- `from axis.systems.construction_kit.observation.types import Observation` (from WP-02)

The `compute()` method reads `.energy` from `agent_state` via duck typing -- no change needed. This is the existing behavior.

---

## Source Files Modified

### `src/axis/systems/system_a/types.py`
- **Remove**: `HungerDriveOutput` class
- After WP-02, WP-03, WP-04, and this WP, `system_a/types.py` retains only `AgentState`

### `src/axis/systems/system_a/drive.py`
- **Delete this file entirely**. Replaced by `construction_kit/drives/hunger.py`.

### `src/axis/systems/system_a/system.py`
- Change: `from axis.systems.system_a.drive import SystemAHungerDrive` -> `from axis.systems.construction_kit.drives.hunger import HungerDrive`
- Change: `self._drive = SystemAHungerDrive(...)` -> `self._drive = HungerDrive(...)`

### `src/axis/systems/system_aw/drive_hunger.py`
- **Delete this file entirely**. Was only a delegation wrapper around `SystemAHungerDrive`.

### `src/axis/systems/system_aw/system.py`
- Change: `from axis.systems.system_aw.drive_hunger import SystemAWHungerDrive` -> `from axis.systems.construction_kit.drives.hunger import HungerDrive`
- Change: `self._hunger_drive = SystemAWHungerDrive(...)` -> `self._hunger_drive = HungerDrive(...)`

### `src/axis/systems/system_aw/drive_arbitration.py`
- Change: `from axis.systems.system_a.types import HungerDriveOutput` -> `from axis.systems.construction_kit.drives.types import HungerDriveOutput`

---

## Test Files Modified

Replace `from axis.systems.system_a.drive import SystemAHungerDrive` with `from axis.systems.construction_kit.drives.hunger import HungerDrive`. Replace `from axis.systems.system_a.types import ... HungerDriveOutput ...` with construction_kit import.

### System A tests
- `tests/systems/system_a/test_drive.py` -- update drive and type imports
- `tests/systems/system_a/test_policy.py` -- update `HungerDriveOutput` import
- `tests/systems/system_a/test_system_a.py` -- update drive and type imports

### System AW tests
- `tests/systems/system_aw/test_drive_hunger.py` -- update both drive imports; remove `SystemAWHungerDrive` references, use `HungerDrive`
- `tests/systems/system_aw/test_drive_arbitration.py` -- update `HungerDriveOutput` import
- `tests/systems/system_aw/test_drive_curiosity.py` -- update `HungerDriveOutput` import if present
- `tests/systems/system_aw/test_types.py` -- update `HungerDriveOutput` import
- `tests/systems/system_aw/test_worked_examples.py` -- update `HungerDriveOutput` and drive imports

### Construction kit tests (new)
- `tests/systems/construction_kit/test_hunger_drive.py` -- unit tests for HungerDrive and HungerDriveOutput

---

## Verification

1. `python -m pytest tests/ -x` -- all tests pass
2. `grep -r "SystemAHungerDrive" src/` -- zero hits
3. `grep -r "SystemAWHungerDrive" src/` -- zero hits
4. `python -c "from axis.systems.construction_kit.drives.hunger import HungerDrive"` -- succeeds

---

## Files Created
- `src/axis/systems/construction_kit/drives/types.py`
- `src/axis/systems/construction_kit/drives/hunger.py`
- `tests/systems/construction_kit/test_hunger_drive.py`

## Files Deleted
- `src/axis/systems/system_a/drive.py`
- `src/axis/systems/system_aw/drive_hunger.py`

## Files Modified
- `src/axis/systems/system_a/types.py` (remove HungerDriveOutput)
- `src/axis/systems/system_a/system.py` (update imports)
- `src/axis/systems/system_aw/system.py` (update imports)
- `src/axis/systems/system_aw/drive_arbitration.py` (update imports)
- 8+ test files (update imports)
