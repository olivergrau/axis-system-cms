# WP-04: Energy Utilities

**Phase**: 1 -- Foundation
**Dependencies**: WP-01
**Scope**: Small
**Spec reference**: Section 7.3

---

## Objective

Extract `clip_energy` from System A and create new shared energy utility functions distilled from patterns repeated across all three systems.

---

## What Moves

| Current location | Target location | Change |
|-----------------|----------------|--------|
| `system_a/types.py :: clip_energy` | `construction_kit/energy/functions.py` | Exact copy |
| (pattern in all 3 systems) | `construction_kit/energy/functions.py :: compute_vitality` | New, distilled |
| (pattern in all 3 systems) | `construction_kit/energy/functions.py :: check_energy_termination` | New, distilled |
| (pattern in A, AW, B transitions) | `construction_kit/energy/functions.py :: get_action_cost` | New, distilled |

---

## New File

### `src/axis/systems/construction_kit/energy/functions.py`

```python
"""Reusable energy management functions for energy-based systems."""

from axis.sdk.actions import MOVEMENT_DELTAS, STAY


def clip_energy(energy: float, max_energy: float) -> float:
    """Clip energy to the valid interval [0, max_energy]."""
    return max(0.0, min(energy, max_energy))


def compute_vitality(energy: float, max_energy: float) -> float:
    """Normalized vitality in [0.0, 1.0]."""
    return energy / max_energy


def check_energy_termination(energy: float) -> tuple[bool, str | None]:
    """Check if energy depletion terminates the episode.

    Returns (terminated, termination_reason).
    """
    terminated = energy <= 0.0
    return terminated, "energy_depleted" if terminated else None


def get_action_cost(
    action: str,
    *,
    move_cost: float,
    stay_cost: float,
    custom_costs: dict[str, float] | None = None,
) -> float:
    """Return the energy cost for a given action.

    Movement actions use move_cost. STAY uses stay_cost.
    Custom actions (consume, scan, etc.) use custom_costs dict.
    Unknown actions default to stay_cost.
    """
    if custom_costs and action in custom_costs:
        return custom_costs[action]
    if action in MOVEMENT_DELTAS:
        return move_cost
    if action == STAY:
        return stay_cost
    return stay_cost
```

---

## Source Files Modified

### `src/axis/systems/system_a/types.py`
- **Remove**: `clip_energy` function
- Types that remain: `HungerDriveOutput`, `AgentState` (moved in later WPs)

### `src/axis/systems/system_a/transition.py`
- Change: `from axis.systems.system_a.types import ... clip_energy` -> `from axis.systems.construction_kit.energy.functions import clip_energy`
- Optionally adopt `get_action_cost` and `check_energy_termination` to replace `_get_action_cost` method and inline termination check

### `src/axis/systems/system_aw/transition.py`
- Change: `from axis.systems.system_a.types import ... clip_energy` -> `from axis.systems.construction_kit.energy.functions import clip_energy`
- Optionally adopt `get_action_cost` and `check_energy_termination`

### System A `system.py` and System AW `system.py`
- Optionally adopt `compute_vitality` in `vitality()` method

### System B `system.py`
- Optional: adopt `compute_vitality`, `check_energy_termination`, `get_action_cost` (with `custom_costs={"scan": scan_cost}`)

**Note**: Adoption of the new utility functions (compute_vitality, check_energy_termination, get_action_cost) by existing systems is optional in this WP. The functions are created and available; systems may adopt them now or in a follow-up cleanup pass.

---

## Test Files Modified

### System A tests
- `tests/systems/system_a/test_transition.py` -- update `clip_energy` import if directly tested

### System AW tests
- `tests/systems/system_aw/test_transition.py` -- update `clip_energy` import if directly tested

### Construction kit tests (new)
- `tests/systems/construction_kit/test_energy.py` -- unit tests for all four functions:
  - `clip_energy`: boundary cases, zero, max, over max, negative
  - `compute_vitality`: normal, zero energy, full energy
  - `check_energy_termination`: zero -> terminated, positive -> not terminated
  - `get_action_cost`: movement, stay, custom, unknown action

---

## Verification

1. `python -m pytest tests/ -x` -- all tests pass
2. `grep -r "clip_energy" src/axis/systems/system_a/types.py` -- zero hits (removed)
3. `python -c "from axis.systems.construction_kit.energy.functions import clip_energy, compute_vitality"` -- succeeds

---

## Files Created
- `src/axis/systems/construction_kit/energy/functions.py`
- `tests/systems/construction_kit/test_energy.py`

## Files Deleted
None.

## Files Modified
- `src/axis/systems/system_a/types.py` (remove clip_energy)
- `src/axis/systems/system_a/transition.py` (update import)
- `src/axis/systems/system_aw/transition.py` (update import)
- Test files with direct clip_energy imports
