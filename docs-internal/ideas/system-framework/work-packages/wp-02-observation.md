# WP-02: Observation Types and Sensor

**Phase**: 1 -- Foundation
**Dependencies**: WP-01
**Scope**: Medium
**Spec reference**: Section 7.1

---

## Objective

Extract `CellObservation`, `Observation`, and the Von Neumann sensor from System A into the construction kit. These types are used by System A, System AW, and their tests. This is the highest-priority extraction because many other WPs depend on it.

---

## What Moves

| Current location | Target location | Change |
|-----------------|----------------|--------|
| `system_a/types.py :: CellObservation` | `construction_kit/observation/types.py` | Exact copy |
| `system_a/types.py :: Observation` | `construction_kit/observation/types.py` | Exact copy |
| `system_a/sensor.py :: SystemASensor` | `construction_kit/observation/sensor.py` | Renamed to `VonNeumannSensor` |

---

## New Files

### `src/axis/systems/construction_kit/observation/types.py`

Contains `CellObservation` and `Observation` -- exact copies from `system_a/types.py` (lines 8-54). No behavioral changes.

### `src/axis/systems/construction_kit/observation/sensor.py`

Contains `VonNeumannSensor` -- exact copy of `SystemASensor` from `system_a/sensor.py`, renamed. Internal imports change:
- `from axis.systems.system_a.types import CellObservation, Observation` becomes `from axis.systems.construction_kit.observation.types import CellObservation, Observation`

---

## Source Files Modified

### `src/axis/systems/system_a/types.py`
- **Remove**: `CellObservation` class (lines 8-19), `Observation` class (lines 21-54)
- **Keep**: `HungerDriveOutput`, `BufferEntry`, `ObservationBuffer`, `AgentState`, `clip_energy` (moved in later WPs)
- **Add import**: `from axis.systems.construction_kit.observation.types import CellObservation, Observation` (needed by remaining types that reference `Observation`, such as `BufferEntry`)

### `src/axis/systems/system_a/sensor.py`
- **Delete this file entirely**. Replaced by `construction_kit/observation/sensor.py`.

### `src/axis/systems/system_a/system.py`
- Change: `from axis.systems.system_a.sensor import SystemASensor` -> `from axis.systems.construction_kit.observation.sensor import VonNeumannSensor`
- Change: `self._sensor = SystemASensor()` -> `self._sensor = VonNeumannSensor()`
- Update `sensor` property return type annotation if present

### `src/axis/systems/system_aw/sensor.py`
- **Delete this file entirely**. Was only `SystemAWSensor = SystemASensor`.

### `src/axis/systems/system_aw/system.py`
- Change: `from axis.systems.system_aw.sensor import SystemAWSensor` -> `from axis.systems.construction_kit.observation.sensor import VonNeumannSensor`
- Change: `self._sensor = SystemAWSensor()` -> `self._sensor = VonNeumannSensor()`

### `src/axis/systems/system_aw/drive_curiosity.py`
- Change: `from axis.systems.system_a.types import ObservationBuffer, Observation` -> `from axis.systems.construction_kit.observation.types import Observation` (ObservationBuffer import updated in WP-03)

### `src/axis/systems/system_aw/transition.py`
- Change: `from axis.systems.system_a.types import Observation, clip_energy` -> split into two imports: `Observation` from construction_kit, `clip_energy` stays from system_a for now (moved in WP-04)

### `src/axis/systems/system_aw/drive_hunger.py`
- Change: `from axis.systems.system_a.types import HungerDriveOutput, Observation` -> `Observation` from construction_kit (HungerDriveOutput moved in WP-05)

### `src/axis/systems/system_aw/policy.py`
- Change: `from axis.systems.system_a.types import Observation` -> `from axis.systems.construction_kit.observation.types import Observation`

### `src/axis/systems/system_aw/drive_arbitration.py`
- No direct Observation imports -- no change needed for this WP.

---

## Test Files Modified

All import changes are mechanical: replace `from axis.systems.system_a.types import ... CellObservation ... Observation ...` with `from axis.systems.construction_kit.observation.types import CellObservation, Observation` and replace `from axis.systems.system_a.sensor import SystemASensor` with `from axis.systems.construction_kit.observation.sensor import VonNeumannSensor`.

### System A tests
- `tests/systems/system_a/test_sensor.py` -- update sensor and type imports
- `tests/systems/system_a/test_drive.py` -- update `Observation` import
- `tests/systems/system_a/test_policy.py` -- update `CellObservation`, `Observation` imports
- `tests/systems/system_a/test_transition.py` -- update `Observation`, `CellObservation` imports
- `tests/systems/system_a/test_observation_buffer.py` -- update `Observation`, `CellObservation` imports
- `tests/systems/system_a/test_memory.py` -- update `Observation`, `CellObservation` imports
- `tests/systems/system_a/test_pipeline.py` -- update type imports
- `tests/systems/system_a/test_system_a.py` -- update sensor and type imports

### System AW tests
- `tests/systems/system_aw/test_drive_curiosity.py` -- update `CellObservation`, `Observation` imports
- `tests/systems/system_aw/test_drive_hunger.py` -- update type imports
- `tests/systems/system_aw/test_policy.py` -- update type imports
- `tests/systems/system_aw/test_transition.py` -- update type imports
- `tests/systems/system_aw/test_inherited.py` -- update sensor + type imports; remove `SystemAWSensor` references
- `tests/systems/system_aw/test_system_aw.py` -- update type imports
- `tests/systems/system_aw/test_pipeline.py` -- update type imports
- `tests/systems/system_aw/test_reduction.py` -- update type imports
- `tests/systems/system_aw/test_worked_examples.py` -- update type imports

### Construction kit tests (new)
- `tests/systems/construction_kit/test_observation_types.py` -- unit tests for CellObservation and Observation
- `tests/systems/construction_kit/test_sensor.py` -- unit tests for VonNeumannSensor

---

## Verification

1. `python -m pytest tests/ -x` -- all 1814 tests pass
2. `grep -r "SystemASensor" src/axis/systems/system_a/` -- zero hits (deleted)
3. `grep -r "SystemAWSensor" src/axis/systems/system_aw/` -- zero hits (deleted)
4. `python -c "from axis.systems.construction_kit.observation.types import CellObservation, Observation"` -- succeeds
5. `python -c "from axis.systems.construction_kit.observation.sensor import VonNeumannSensor"` -- succeeds

---

## Files Created
- `src/axis/systems/construction_kit/observation/types.py`
- `src/axis/systems/construction_kit/observation/sensor.py`
- `tests/systems/construction_kit/test_observation_types.py`
- `tests/systems/construction_kit/test_sensor.py`

## Files Deleted
- `src/axis/systems/system_a/sensor.py`
- `src/axis/systems/system_aw/sensor.py`

## Files Modified
- `src/axis/systems/system_a/types.py` (remove CellObservation, Observation; add import)
- `src/axis/systems/system_a/system.py` (update imports)
- `src/axis/systems/system_aw/system.py` (update imports)
- `src/axis/systems/system_aw/drive_curiosity.py` (update imports)
- `src/axis/systems/system_aw/transition.py` (update imports)
- `src/axis/systems/system_aw/drive_hunger.py` (update imports)
- `src/axis/systems/system_aw/policy.py` (update imports)
- 17 test files (update imports)
