# WP-06: Softmax Policy

**Phase**: 1 -- Foundation
**Dependencies**: WP-01, WP-02
**Scope**: Medium (interface change)
**Spec reference**: Section 7.5

---

## Objective

Extract the softmax policy from System A into the construction kit with a **generalized interface** that accepts generic action score tuples instead of `HungerDriveOutput`. This eliminates the need for System AW's delegation wrapper and makes the policy drive-agnostic.

---

## What Moves

| Current location | Target location | Change |
|-----------------|----------------|--------|
| `system_a/policy.py :: SystemAPolicy` | `construction_kit/policy/softmax.py` | Renamed to `SoftmaxPolicy`, interface generalized |

---

## Interface Change

**Current** (`SystemAPolicy`):
```python
def select(self, drive_outputs: HungerDriveOutput, observation: Observation, rng) -> PolicyResult:
```

**New** (`SoftmaxPolicy`):
```python
def select(self, action_scores: tuple[float, ...], observation: Observation, rng) -> PolicyResult:
```

The internal logic (admissibility masking, softmax, selection) is unchanged. Only the entry point changes: instead of reading `drive_outputs.action_contributions`, the method receives scores directly.

---

## New File

### `src/axis/systems/construction_kit/policy/softmax.py`

Contains `SoftmaxPolicy` with the following structure (adapted from `system_a/policy.py`):

- `__init__(self, *, temperature: float, selection_mode: str)` -- unchanged
- `select(self, action_scores, observation, rng) -> PolicyResult` -- accepts generic scores
- `_compute_admissibility_mask(observation)` -- unchanged static method
- `_apply_mask(scores, mask)` -- unchanged static method (parameter renamed from `contributions` to `scores`)
- `_softmax(scores, beta, mask)` -- unchanged static method
- `_select_from_distribution(probabilities, rng)` -- unchanged method

Action names constant `_ACTION_NAMES` moves into this file.

Internal imports:
- `from axis.systems.construction_kit.observation.types import Observation` (from WP-02)
- `from axis.sdk.types import PolicyResult`

---

## Source Files Modified

### `src/axis/systems/system_a/policy.py`
- **Delete this file entirely**. Replaced by `construction_kit/policy/softmax.py`.

### `src/axis/systems/system_a/system.py`
- Change: `from axis.systems.system_a.policy import SystemAPolicy` -> `from axis.systems.construction_kit.policy.softmax import SoftmaxPolicy`
- Change: `self._policy = SystemAPolicy(...)` -> `self._policy = SoftmaxPolicy(...)`
- Change in `decide()`: the policy call changes from:
  ```python
  policy_result = self._policy.select(drive_output, observation, rng)
  ```
  to:
  ```python
  policy_result = self._policy.select(drive_output.action_contributions, observation, rng)
  ```

### `src/axis/systems/system_aw/policy.py`
- **Delete this file entirely**. Was a delegation wrapper. System AW already computes combined action scores before calling the policy.

### `src/axis/systems/system_aw/system.py`
- Change: `from axis.systems.system_aw.policy import SystemAWPolicy` -> `from axis.systems.construction_kit.policy.softmax import SoftmaxPolicy`
- Change: `self._policy = SystemAWPolicy(...)` -> `self._policy = SoftmaxPolicy(...)`
- The `decide()` call already passes `scores` (the combined action scores from arbitration), so: `self._policy.select(scores, observation, rng)` -- this works directly with the new interface.

---

## Test Files Modified

### System A tests
- `tests/systems/system_a/test_policy.py` -- major update:
  - Change import to `SoftmaxPolicy`
  - All test calls that pass `HungerDriveOutput` to `select()` need to pass `drive_output.action_contributions` instead
  - Tests for internal methods (`_compute_admissibility_mask`, `_softmax`, etc.) update to reference `SoftmaxPolicy`
- `tests/systems/system_a/test_system_a.py` -- update policy import
- `tests/systems/system_a/test_pipeline.py` -- update if it references policy directly

### System AW tests
- `tests/systems/system_aw/test_policy.py` -- major update:
  - Remove `SystemAWPolicy` references
  - Use `SoftmaxPolicy` directly
  - Remove delegation-specific tests (they tested the wrapper pattern)
  - Tests for the actual softmax behavior remain, adapted to new interface
- `tests/systems/system_aw/test_worked_examples.py` -- update policy import

### Construction kit tests (new)
- `tests/systems/construction_kit/test_softmax_policy.py` -- comprehensive unit tests:
  - Admissibility masking from observation traversability
  - Softmax distribution computation
  - Argmax vs sample selection modes
  - Temperature sensitivity
  - Generic score tuple input (not tied to any drive type)
  - Edge cases: all-blocked except stay/consume, uniform scores

---

## Verification

1. `python -m pytest tests/ -x` -- all tests pass
2. `grep -r "SystemAPolicy" src/` -- zero hits
3. `grep -r "SystemAWPolicy" src/` -- zero hits
4. `python -c "from axis.systems.construction_kit.policy.softmax import SoftmaxPolicy"` -- succeeds

---

## Files Created
- `src/axis/systems/construction_kit/policy/softmax.py`
- `tests/systems/construction_kit/test_softmax_policy.py`

## Files Deleted
- `src/axis/systems/system_a/policy.py`
- `src/axis/systems/system_aw/policy.py`

## Files Modified
- `src/axis/systems/system_a/system.py` (update imports, minor wiring change in `decide()`)
- `src/axis/systems/system_aw/system.py` (update imports, simplification)
- 4+ test files (update imports and call patterns)
