# WP-09: Shared Config Types and Consume Action

**Phase**: 1 -- Foundation
**Dependencies**: WP-01
**Scope**: Medium
**Spec reference**: Extends spec Section 7 (gap identified during WP planning)

---

## Objective

Extract shared config types (`AgentConfig`, `PolicyConfig`, `TransitionConfig`) and the `handle_consume` action handler from System A into the construction kit, eliminating the last cross-system source dependencies from System AW to System A.

These were identified during work package planning as cross-system dependencies not covered by the original spec sections 7.1-7.7.

---

## What Moves

| Current location | Target location | Change |
|-----------------|----------------|--------|
| `system_a/config.py :: AgentConfig` | `construction_kit/types/config.py` | Exact copy |
| `system_a/config.py :: PolicyConfig` | `construction_kit/types/config.py` | Exact copy |
| `system_a/config.py :: TransitionConfig` | `construction_kit/types/config.py` | Exact copy |
| `system_a/actions.py :: handle_consume` | `construction_kit/types/actions.py` | Exact copy |

### What Stays

| Location | Reason |
|----------|--------|
| `system_a/config.py :: SystemAConfig` | System-specific composition of shared configs |
| `system_aw/config.py :: SystemAWConfig` | System-specific composition with curiosity + arbitration |
| `system_aw/config.py :: CuriosityConfig` | System AW-specific |
| `system_aw/config.py :: ArbitrationConfig` | System AW-specific (used by arbitration WP-07, but semantics tied to AW's Maslow gating) |

---

## New Files

### `src/axis/systems/construction_kit/types/config.py`

Contains `AgentConfig`, `PolicyConfig`, `TransitionConfig` -- exact copies from `system_a/config.py`. These are general-purpose config types for energy-based systems with softmax policy and movement/consume/stay actions.

### `src/axis/systems/construction_kit/types/actions.py`

Contains `handle_consume` -- exact copy from `system_a/actions.py`. This is a general-purpose consume action handler usable by any system that extracts resources.

Internal imports:
- `from axis.sdk.world_types import ActionOutcome, MutableWorldProtocol`

---

## Source Files Modified

### `src/axis/systems/system_a/config.py`
- **Remove**: `AgentConfig`, `PolicyConfig`, `TransitionConfig`
- **Keep**: `SystemAConfig` (add import from construction_kit)
- Updated:
  ```python
  from axis.systems.construction_kit.types.config import AgentConfig, PolicyConfig, TransitionConfig

  class SystemAConfig(BaseModel):
      agent: AgentConfig
      policy: PolicyConfig
      transition: TransitionConfig
  ```

### `src/axis/systems/system_a/actions.py`
- **Delete this file entirely** or reduce to a re-import if other system_a code references it locally. Preferred: **delete entirely**, update `system_a/system.py` to import from construction_kit.

### `src/axis/systems/system_a/system.py`
- Update `action_handlers()`:
  ```python
  # Before:
  from axis.systems.system_a.actions import handle_consume
  # After:
  from axis.systems.construction_kit.types.actions import handle_consume
  ```

### `src/axis/systems/system_aw/config.py`
- Change: `from axis.systems.system_a.config import AgentConfig, PolicyConfig, TransitionConfig` -> `from axis.systems.construction_kit.types.config import AgentConfig, PolicyConfig, TransitionConfig`
- This is the key cross-system dependency being eliminated.

### `src/axis/systems/system_aw/actions.py`
- **Delete this file entirely**. Was only a re-export of `handle_consume` from System A.

### `src/axis/systems/system_aw/system.py`
- Update `action_handlers()`:
  ```python
  # Before:
  from axis.systems.system_aw.actions import handle_consume
  # After:
  from axis.systems.construction_kit.types.actions import handle_consume
  ```

---

## Test Files Modified

### System A tests
- `tests/systems/system_a/test_config.py` -- update imports for `AgentConfig`, `PolicyConfig`, `TransitionConfig`
- `tests/systems/system_a/test_consume.py` -- update `handle_consume` import
- `tests/systems/system_a/test_pipeline.py` -- update imports
- `tests/systems/system_a/test_system_a.py` -- update imports

### System AW tests
- `tests/systems/system_aw/test_config.py` -- update config type imports
- `tests/systems/system_aw/test_inherited.py` -- update `handle_consume` import
- `tests/systems/system_aw/test_pipeline.py` -- update imports
- `tests/systems/system_aw/test_reduction.py` -- update `SystemAConfig` import (still from `system_a/config.py` which now re-imports from kit)
- `tests/systems/system_aw/test_worked_examples.py` -- update config imports

### Framework tests
- `tests/framework/test_runner.py` -- imports `handle_consume` from system_a; update to construction_kit or leave (this one imports `SystemA` for integration, so `handle_consume` may come via SystemA)

### Test builders
- `tests/builders/system_config_builder.py` -- uses dict-based config, no type imports to change
- `tests/builders/system_aw_config_builder.py` -- uses dict-based config, no type imports to change

### Construction kit tests (new)
- `tests/systems/construction_kit/test_config_types.py` -- unit tests for AgentConfig, PolicyConfig, TransitionConfig validation
- `tests/systems/construction_kit/test_consume_action.py` -- unit tests for handle_consume

---

## Verification

1. `python -m pytest tests/ -x` -- all tests pass
2. `grep -r "from axis.systems.system_a.config import" src/axis/systems/system_aw/` -- zero hits
3. `grep -r "from axis.systems.system_a.actions import" src/axis/systems/system_aw/` -- zero hits
4. `python -c "from axis.systems.construction_kit.types.config import AgentConfig, PolicyConfig, TransitionConfig"` -- succeeds
5. `python -c "from axis.systems.construction_kit.types.actions import handle_consume"` -- succeeds

---

## Files Created
- `src/axis/systems/construction_kit/types/config.py`
- `src/axis/systems/construction_kit/types/actions.py`
- `tests/systems/construction_kit/test_config_types.py`
- `tests/systems/construction_kit/test_consume_action.py`

## Files Deleted
- `src/axis/systems/system_a/actions.py`
- `src/axis/systems/system_aw/actions.py`

## Files Modified
- `src/axis/systems/system_a/config.py` (remove shared types, add import)
- `src/axis/systems/system_a/system.py` (update action handler import)
- `src/axis/systems/system_aw/config.py` (update config import -- key dependency break)
- `src/axis/systems/system_aw/system.py` (update action handler import)
- 9+ test files (update imports)
