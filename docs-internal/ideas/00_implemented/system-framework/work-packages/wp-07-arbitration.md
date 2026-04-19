# WP-07: Drive Arbitration

**Phase**: 1 -- Foundation
**Dependencies**: WP-01
**Scope**: Medium (generalization)
**Spec reference**: Section 7.6

---

## Objective

Extract drive arbitration from System AW into the construction kit with two refinements:

1. `compute_drive_weights` is adapted to accept raw parameters instead of `ArbitrationConfig` (to eliminate the dependency on a system-specific config type).
2. `compute_action_scores` is generalized to support N drives instead of being hardcoded for two.

---

## What Moves

| Current location | Target location | Change |
|-----------------|----------------|--------|
| `system_aw/types.py :: DriveWeights` | `construction_kit/arbitration/types.py` | Exact copy |
| `system_aw/drive_arbitration.py :: compute_drive_weights` | `construction_kit/arbitration/weights.py` | Renamed to `compute_maslow_weights`, raw params |
| `system_aw/drive_arbitration.py :: compute_action_scores` | `construction_kit/arbitration/scoring.py` | Renamed to `combine_drive_scores`, N-drive |

---

## New Files

### `src/axis/systems/construction_kit/arbitration/types.py`

Contains `DriveWeights` -- exact copy from `system_aw/types.py` (lines 64-76).

### `src/axis/systems/construction_kit/arbitration/weights.py`

Contains `compute_maslow_weights` -- adapted from `compute_drive_weights`:

```python
from axis.systems.construction_kit.arbitration.types import DriveWeights


def compute_maslow_weights(
    primary_activation: float,
    *,
    primary_weight_base: float,
    secondary_weight_base: float,
    gating_sharpness: float,
) -> DriveWeights:
    """Maslow-like hierarchy: primary drive gates secondary drive.

    w_primary = primary_weight_base + (1 - primary_weight_base) * primary_activation^gamma
    w_secondary = secondary_weight_base * (1 - primary_activation)^gamma

    Adapted from System AW's compute_drive_weights.
    """
    gamma = gating_sharpness
    w_primary = primary_weight_base + (1 - primary_weight_base) * (primary_activation ** gamma)
    w_secondary = secondary_weight_base * ((1 - primary_activation) ** gamma)
    return DriveWeights(hunger_weight=w_primary, curiosity_weight=w_secondary)
```

**Note**: The `DriveWeights` field names (`hunger_weight`, `curiosity_weight`) remain unchanged for now to avoid cascading changes. A future WP may rename them to `primary_weight`, `secondary_weight` if generalization demands it.

### `src/axis/systems/construction_kit/arbitration/scoring.py`

Contains `combine_drive_scores` -- generalized N-drive version:

```python
from collections.abc import Sequence


def combine_drive_scores(
    drive_contributions: Sequence[tuple[float, ...]],
    drive_activations: Sequence[float],
    drive_weights: Sequence[float],
) -> tuple[float, ...]:
    """Weighted combination of N drive score vectors.

    psi(a) = sum_i( w_i * d_i * phi_i(a) )

    All contribution tuples must have the same length (number of actions).
    """
    n_drives = len(drive_contributions)
    if n_drives == 0:
        raise ValueError("At least one drive is required")

    n_actions = len(drive_contributions[0])
    result = [0.0] * n_actions

    for i in range(n_drives):
        w = drive_weights[i]
        d = drive_activations[i]
        for j in range(n_actions):
            result[j] += w * d * drive_contributions[i][j]

    return tuple(result)
```

---

## Source Files Modified

### `src/axis/systems/system_aw/drive_arbitration.py`
- **Delete this file entirely**. Replaced by construction_kit modules.

### `src/axis/systems/system_aw/types.py`
- **Remove**: `DriveWeights` class
- **Keep**: `CuriosityDriveOutput` (moved in WP-08), `AgentStateAW`, `WorldModelState`

### `src/axis/systems/system_aw/system.py`
- Change imports:
  ```python
  # Before:
  from axis.systems.system_aw.drive_arbitration import compute_action_scores, compute_drive_weights
  from axis.systems.system_aw.types import ... DriveWeights ...

  # After:
  from axis.systems.construction_kit.arbitration.weights import compute_maslow_weights
  from axis.systems.construction_kit.arbitration.scoring import combine_drive_scores
  ```
- Change in `decide()`:
  ```python
  # Before:
  weights = compute_drive_weights(hunger_output.activation, self._config.arbitration)
  scores = compute_action_scores(hunger_output, curiosity_output, weights)

  # After:
  weights = compute_maslow_weights(
      hunger_output.activation,
      primary_weight_base=self._config.arbitration.hunger_weight_base,
      secondary_weight_base=self._config.arbitration.curiosity_weight_base,
      gating_sharpness=self._config.arbitration.gating_sharpness,
  )
  scores = combine_drive_scores(
      drive_contributions=[hunger_output.action_contributions, curiosity_output.action_contributions],
      drive_activations=[hunger_output.activation, curiosity_output.activation],
      drive_weights=[weights.hunger_weight, weights.curiosity_weight],
  )
  ```
- Update trace data: `"combined_scores": scores` stays as-is (both return `tuple[float, ...]`)

---

## Test Files Modified

### System AW tests
- `tests/systems/system_aw/test_drive_arbitration.py` -- major update:
  - Import from construction_kit instead of system_aw
  - Update `compute_drive_weights` calls to `compute_maslow_weights` with raw params
  - Update `compute_action_scores` calls to `combine_drive_scores` with sequences
  - `ArbitrationConfig` is no longer passed to the function; individual values are passed instead
  - Verify numerical equivalence with existing test expectations
- `tests/systems/system_aw/test_worked_examples.py` -- update arbitration imports
- `tests/systems/system_aw/test_types.py` -- update `DriveWeights` import

### Construction kit tests (new)
- `tests/systems/construction_kit/test_arbitration.py` -- unit tests:
  - `compute_maslow_weights`: primary gates secondary, boundary cases (activation=0, activation=1)
  - `combine_drive_scores`: 1-drive, 2-drive (equivalence with old behavior), 3-drive, empty-drive error
  - Numerical equivalence test: old 2-drive result == new generalized result for same inputs

---

## Verification

1. `python -m pytest tests/ -x` -- all tests pass
2. `python -m pytest tests/systems/system_aw/test_drive_arbitration.py -v` -- all arbitration tests pass with identical numerical results
3. `grep -r "compute_drive_weights\|compute_action_scores" src/axis/systems/system_aw/` -- zero hits
4. `python -c "from axis.systems.construction_kit.arbitration.scoring import combine_drive_scores"` -- succeeds

---

## Files Created
- `src/axis/systems/construction_kit/arbitration/types.py`
- `src/axis/systems/construction_kit/arbitration/weights.py`
- `src/axis/systems/construction_kit/arbitration/scoring.py`
- `tests/systems/construction_kit/test_arbitration.py`

## Files Deleted
- `src/axis/systems/system_aw/drive_arbitration.py`

## Files Modified
- `src/axis/systems/system_aw/types.py` (remove DriveWeights)
- `src/axis/systems/system_aw/system.py` (update imports and decide() wiring)
- 3 test files (update imports and call patterns)
