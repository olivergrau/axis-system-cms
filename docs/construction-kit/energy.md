# Energy

**Package:** `axis.systems.construction_kit.energy`

**Source:** `src/axis/systems/construction_kit/energy/functions.py`

Pure utility functions for energy management. These handle the
fundamental energy operations that most survival-based systems need:
clamping, normalization, termination checking, and action cost dispatch.

All functions are stateless -- no classes, no side effects.

---

## `clip_energy`

Clamps energy to the valid range $[0, E_{max}]$.

```python
from axis.systems.construction_kit.energy.functions import clip_energy
```

```python
def clip_energy(energy: float, max_energy: float) -> float
```

**Returns:** `max(0.0, min(energy, max_energy))`

Use this after computing energy deltas (cost - gain) to ensure energy
stays within bounds.

---

## `compute_vitality`

Returns the agent's normalized vitality -- the metric the framework
reads via `SystemInterface.vitality()`.

```python
from axis.systems.construction_kit.energy.functions import compute_vitality
```

```python
def compute_vitality(energy: float, max_energy: float) -> float
```

**Returns:** `energy / max_energy`

Value is in $[0, 1]$ when energy is properly clamped.

---

## `check_energy_termination`

Checks whether the agent should terminate due to energy depletion.

```python
from axis.systems.construction_kit.energy.functions import check_energy_termination
```

```python
def check_energy_termination(energy: float) -> tuple[bool, str | None]
```

**Returns:**

- `(True, "energy_depleted")` when `energy <= 0.0`
- `(False, None)` otherwise

Use the return values directly in `TransitionResult(terminated=...,
termination_reason=...)`.

---

## `get_action_cost`

Returns the energy cost for an action, dispatching by action type.

```python
from axis.systems.construction_kit.energy.functions import get_action_cost
```

```python
def get_action_cost(
    action: str,
    *,
    move_cost: float,
    stay_cost: float,
    custom_costs: dict[str, float] | None = None,
) -> float
```

**Dispatch logic:**

1. If `action` is a movement direction (in `MOVEMENT_DELTAS` from
   `axis.sdk.actions`): returns `move_cost`.
2. If `custom_costs` is provided and contains the action: returns
   `custom_costs[action]`.
3. Otherwise (stay or unknown): returns `stay_cost`.

**Example `custom_costs`:** `{"consume": 0.5, "scan": 0.3}`

---

## Usage Example

```python
from axis.systems.construction_kit.energy.functions import (
    clip_energy, compute_vitality, check_energy_termination, get_action_cost,
)

# In your transition function:
cost = get_action_cost(
    action_outcome.action,
    move_cost=1.0,
    stay_cost=0.5,
    custom_costs={"consume": 0.5},
)

resource_consumed = action_outcome.data.get("resource_consumed", 0.0)
energy_gain = energy_gain_factor * resource_consumed

new_energy = clip_energy(
    agent_state.energy - cost + energy_gain,
    max_energy,
)

terminated, reason = check_energy_termination(new_energy)

# In your vitality() method:
vitality = compute_vitality(new_energy, max_energy)
```

---

## Design References

- [System A Formal Specification](../system-design/system-a/01_System A Baseline.md)
  -- energy dynamics model
- [Configuration Reference](../manuals/config-manual.md) -- transition
  config parameters
