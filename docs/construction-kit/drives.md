# Drives

**Package:** `axis.systems.construction_kit.drives`

**Source:** `src/axis/systems/construction_kit/drives/`

Drives are the motivational core of an agent. Each drive evaluates the
agent's current state and observations, producing a scalar **activation**
level and a tuple of **per-action contribution scores**. These scores
express how strongly the drive favors each action.

**Action ordering convention:** All contribution tuples follow the order
`(UP, DOWN, LEFT, RIGHT, CONSUME, STAY)` -- matching the standard
6-action space used by System A and System A+W.

---

## HungerDrive

Scores actions based on energy need and resource availability. As the
agent's energy drops, the drive activation rises, making resource-rich
directions and the consume action more attractive. Satisfies
`DriveInterface`.

```python
from axis.systems.construction_kit.drives.hunger import HungerDrive
```

### Constructor

```python
HungerDrive(
    *,
    consume_weight: float,    # bonus multiplier for consume action
    stay_suppression: float,  # penalty for stay action
    max_energy: float,        # agent's energy capacity
)
```

### `compute(agent_state, observation) -> HungerDriveOutput`

Reads `agent_state.energy` and the observation's resource values.

**Activation:**

$$d_H(t) = \text{clamp}\left(1 - \frac{E_t}{E_{max}}, \; 0, \; 1\right)$$

At full energy $d_H = 0$ (no hunger). At zero energy $d_H = 1$
(maximum hunger).

**Action contributions:**

| Action | Formula | Description |
|--------|---------|-------------|
| Direction (up/down/left/right) | $\varphi_H(\text{dir}) = d_H \cdot r_{\text{dir}}$ | Proportional to neighbor resource |
| Consume | $\varphi_H(\text{consume}) = d_H \cdot w_c \cdot r_{\text{current}}$ | Boosted by `consume_weight` |
| Stay | $\varphi_H(\text{stay}) = -\lambda_{\text{stay}} \cdot d_H$ | Always penalized |

### HungerDriveOutput

```python
from axis.systems.construction_kit.drives.types import HungerDriveOutput
```

Frozen Pydantic model.

| Field | Type | Description |
|-------|------|-------------|
| `activation` | `float` | $d_H \in [0, 1]$ |
| `action_contributions` | `tuple[float, ...]` | 6-element tuple (UP, DOWN, LEFT, RIGHT, CONSUME, STAY) |

---

## CuriosityDrive

Scores actions based on novelty -- encouraging the agent to explore
unfamiliar territory. Combines spatial novelty (visit-count-based) and
sensory novelty (observation-difference-based) into a composite signal.
Satisfies `DriveInterface`.

```python
from axis.systems.construction_kit.drives.curiosity import CuriosityDrive
```

### Constructor

```python
CuriosityDrive(
    *,
    base_curiosity: float,          # mu_C: overall curiosity strength (0 disables)
    spatial_sensory_balance: float,  # alpha: weight of spatial vs sensory novelty
    explore_suppression: float,      # lambda_explore: penalty for non-exploring actions
    novelty_sharpness: float = 1.0,  # k: exponent in spatial novelty decay
)
```

### `compute(observation, buffer, world_model) -> CuriosityDriveOutput`

Runs the full curiosity pipeline:

1. **Spatial novelty** (per direction):

    $$\nu^{\text{spatial}}_{\text{dir}} = \frac{1}{(1 + w(\text{neighbor}))^k}$$

    where $w$ is the visit count from the world model and $k$ is
    `novelty_sharpness`.

2. **Sensory novelty** (per direction):

    $$\nu^{\text{sensory}}_{\text{dir}} = |r_{\text{dir}}(t) - \overline{r}_{\text{dir}}|$$

    where $\overline{r}_{\text{dir}}$ is the mean resource value at
    that direction across the observation buffer.

3. **Composite novelty** (alpha-weighted blend):

    $$\nu_{\text{dir}} = \alpha \cdot \nu^{\text{spatial}}_{\text{dir}} + (1 - \alpha) \cdot \nu^{\text{sensory}}_{\text{dir}}$$

4. **Novelty saturation** (from buffer):

    $$\bar{\nu}_t = \text{mean over buffer entries of } \sigma_j$$

    where $\sigma_j$ is the mean per-direction absolute deviation of
    resource values from their means.

5. **Drive activation:**

    $$d_C = \mu_C \cdot (1 - \bar{\nu}_t)$$

6. **Action contributions:**

    | Action | Score |
    |--------|-------|
    | Direction | $\varphi_C(\text{dir}) = \nu_{\text{dir}}$ |
    | Consume | $\varphi_C(\text{consume}) = -\lambda_{\text{explore}}$ |
    | Stay | $\varphi_C(\text{stay}) = -\lambda_{\text{explore}}$ |

### CuriosityDriveOutput

```python
from axis.systems.construction_kit.drives.types import CuriosityDriveOutput
```

Frozen Pydantic model.

| Field | Type | Description |
|-------|------|-------------|
| `activation` | `float` | $d_C \in [0, 1]$ |
| `spatial_novelty` | `tuple[float, float, float, float]` | Per-direction spatial novelty |
| `sensory_novelty` | `tuple[float, float, float, float]` | Per-direction sensory novelty |
| `composite_novelty` | `tuple[float, float, float, float]` | Per-direction blended novelty |
| `action_contributions` | `tuple[float, ...]` | 6-element tuple (UP, DOWN, LEFT, RIGHT, CONSUME, STAY) |

---

## Standalone Novelty Functions

The curiosity module also exports five standalone functions that can be
used independently of the `CuriosityDrive` class:

```python
from axis.systems.construction_kit.drives.curiosity import (
    compute_spatial_novelty,
    compute_sensory_novelty,
    compute_composite_novelty,
    compute_novelty_saturation,
    compute_curiosity_activation,
)
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `compute_spatial_novelty` | `(world_model, k=1.0) -> tuple[float, float, float, float]` | Per-direction spatial novelty from visit counts |
| `compute_sensory_novelty` | `(observation, buffer) -> tuple[float, float, float, float]` | Per-direction sensory novelty from observation vs buffer mean |
| `compute_composite_novelty` | `(spatial, sensory, alpha) -> tuple[float, float, float, float]` | Alpha-weighted blend of spatial and sensory novelty |
| `compute_novelty_saturation` | `(buffer) -> float` | Mean novelty saturation from observation buffer (0.0 when empty) |
| `compute_curiosity_activation` | `(base_curiosity, novelty_saturation) -> float` | $d_C = \mu_C \cdot (1 - \bar{\nu}_t)$ |

These functions are useful for custom drive implementations that need
individual novelty computations without the full curiosity pipeline.

---

## Usage Example

```python
from axis.systems.construction_kit.drives.hunger import HungerDrive
from axis.systems.construction_kit.drives.curiosity import CuriosityDrive

# Single-drive system (System A style)
hunger = HungerDrive(
    consume_weight=3.0,
    stay_suppression=0.1,
    max_energy=100.0,
)
hunger_output = hunger.compute(agent_state, observation)
# Pass hunger_output.action_contributions to policy

# Dual-drive system (System A+W style)
curiosity = CuriosityDrive(
    base_curiosity=1.0,
    spatial_sensory_balance=0.7,
    explore_suppression=0.3,
    novelty_sharpness=2.0,
)
curiosity_output = curiosity.compute(observation, buffer, world_model)
# Combine with hunger via arbitration, then pass to policy
```

---

## Design References

- [System A Formal Specification](../system-design/system-a/01_System A Baseline.md)
  -- hunger drive model
- [System A+W Formal Model](../system-design/system-a+w/01_System A+W Model.md)
  -- curiosity drive, novelty functions, composite novelty
- [System A+W Manual -- Drive Pipeline](../manuals/system-aw-manual.md#3-drive-pipeline)
  -- formula reference with tuning guide
