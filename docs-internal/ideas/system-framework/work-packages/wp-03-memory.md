# WP-03: Observation Buffer (Memory)

**Phase**: 1 -- Foundation
**Dependencies**: WP-01, WP-02
**Scope**: Small
**Spec reference**: Section 7.2

---

## Objective

Extract `BufferEntry`, `ObservationBuffer`, and `update_observation_buffer` from System A into the construction kit `memory/` package. These are used by both System A and System AW.

---

## What Moves

| Current location | Target location | Change |
|-----------------|----------------|--------|
| `system_a/types.py :: BufferEntry` | `construction_kit/memory/types.py` | Exact copy |
| `system_a/types.py :: ObservationBuffer` | `construction_kit/memory/types.py` | Exact copy |
| `system_a/observation_buffer.py :: update_observation_buffer` | `construction_kit/memory/observation_buffer.py` | Exact copy, updated imports |

---

## New Files

### `src/axis/systems/construction_kit/memory/types.py`

Contains `BufferEntry` and `ObservationBuffer` -- exact copies from `system_a/types.py`.

**Note**: WP-08 will later add `WorldModelState` to this same file.

Internal imports:
- `from axis.systems.construction_kit.observation.types import Observation` (from WP-02)

### `src/axis/systems/construction_kit/memory/observation_buffer.py`

Contains `update_observation_buffer` -- exact copy from `system_a/observation_buffer.py`.

Internal imports:
- `from axis.systems.construction_kit.memory.types import BufferEntry, ObservationBuffer`
- `from axis.systems.construction_kit.observation.types import Observation`

---

## Source Files Modified

### `src/axis/systems/system_a/types.py`
- **Remove**: `BufferEntry` class, `ObservationBuffer` class
- **Keep**: `AgentState` (which references `ObservationBuffer` -- update its import)
- **Add import**: `from axis.systems.construction_kit.memory.types import ObservationBuffer` (needed by `AgentState`)

### `src/axis/systems/system_a/observation_buffer.py`
- **Delete this file entirely**. Replaced by `construction_kit/memory/observation_buffer.py`.

### `src/axis/systems/system_a/transition.py`
- Change: `from axis.systems.system_a.observation_buffer import update_observation_buffer` -> `from axis.systems.construction_kit.memory.observation_buffer import update_observation_buffer`

### `src/axis/systems/system_a/system.py`
- Change: `from axis.systems.system_a.types import AgentState, ObservationBuffer` -> `ObservationBuffer` from construction_kit

### `src/axis/systems/system_aw/types.py`
- Change: `from axis.systems.system_a.types import ObservationBuffer` -> `from axis.systems.construction_kit.memory.types import ObservationBuffer`

### `src/axis/systems/system_aw/system.py`
- Change: `from axis.systems.system_a.types import ObservationBuffer` -> `from axis.systems.construction_kit.memory.types import ObservationBuffer`

### `src/axis/systems/system_aw/transition.py`
- Change: `from axis.systems.system_a.observation_buffer import update_observation_buffer` -> `from axis.systems.construction_kit.memory.observation_buffer import update_observation_buffer`

### `src/axis/systems/system_aw/drive_curiosity.py`
- Change: `ObservationBuffer` import source to construction_kit

### `src/axis/systems/system_aw/observation_buffer.py`
- **Delete this file entirely**. Was only a re-export.

---

## Test Files Modified

Replace `from axis.systems.system_a.types import ... BufferEntry ... ObservationBuffer ...` with construction_kit imports. Replace `from axis.systems.system_a.observation_buffer import update_observation_buffer` with construction_kit import.

### System A tests
- `tests/systems/system_a/test_observation_buffer.py`
- `tests/systems/system_a/test_memory.py`
- `tests/systems/system_a/test_transition.py`
- `tests/systems/system_a/test_pipeline.py`
- `tests/systems/system_a/test_system_a.py`

### System AW tests
- `tests/systems/system_aw/test_drive_curiosity.py`
- `tests/systems/system_aw/test_transition.py`
- `tests/systems/system_aw/test_inherited.py`
- `tests/systems/system_aw/test_system_aw.py`
- `tests/systems/system_aw/test_types.py`
- `tests/systems/system_aw/test_worked_examples.py`
- `tests/systems/system_aw/test_reduction.py`

### Construction kit tests (new)
- `tests/systems/construction_kit/test_memory_types.py` -- unit tests for BufferEntry, ObservationBuffer
- `tests/systems/construction_kit/test_observation_buffer.py` -- unit tests for update_observation_buffer

---

## Verification

1. `python -m pytest tests/ -x` -- all tests pass
2. `grep -r "observation_buffer" src/axis/systems/system_a/` -- only `system_a/types.py` (AgentState import) and `system_a/transition.py` remain, pointing to construction_kit
3. `python -c "from axis.systems.construction_kit.memory.types import BufferEntry, ObservationBuffer"` -- succeeds
4. `python -c "from axis.systems.construction_kit.memory.observation_buffer import update_observation_buffer"` -- succeeds

---

## Files Created
- `src/axis/systems/construction_kit/memory/types.py`
- `src/axis/systems/construction_kit/memory/observation_buffer.py`
- `tests/systems/construction_kit/test_memory_types.py`
- `tests/systems/construction_kit/test_observation_buffer.py`

## Files Deleted
- `src/axis/systems/system_a/observation_buffer.py`
- `src/axis/systems/system_aw/observation_buffer.py`

## Files Modified
- `src/axis/systems/system_a/types.py` (remove BufferEntry, ObservationBuffer)
- `src/axis/systems/system_a/transition.py` (update import)
- `src/axis/systems/system_a/system.py` (update import)
- `src/axis/systems/system_aw/types.py` (update import)
- `src/axis/systems/system_aw/system.py` (update import)
- `src/axis/systems/system_aw/transition.py` (update import)
- `src/axis/systems/system_aw/drive_curiosity.py` (update import)
- 12 test files (update imports)
