# Arbitration

**Package:** `axis.systems.construction_kit.arbitration`

**Source:** `src/axis/systems/construction_kit/arbitration/`

When an agent has multiple drives, arbitration determines how much each
drive influences the final action scores. The arbitration package
provides two functions: one computes drive weights (implementing a
Maslow-like hierarchy), the other combines weighted drive contributions
into final per-action scores.

---

## `compute_maslow_weights`

Computes drive weights implementing a Maslow-like gating mechanism:
the primary drive (typically hunger) suppresses the secondary drive
(typically curiosity) as its activation increases.

```python
from axis.systems.construction_kit.arbitration.weights import compute_maslow_weights
```

### Signature

```python
def compute_maslow_weights(
    primary_activation: float,       # d_H: primary drive activation [0, 1]
    *,
    primary_weight_base: float,      # w_H_base: minimum primary weight
    secondary_weight_base: float,    # w_C_base: maximum secondary weight
    gating_sharpness: float,         # gamma: gating exponent
) -> DriveWeights
```

### Formulas

$$w_{\text{primary}}(t) = w^{\text{base}}_H + (1 - w^{\text{base}}_H) \cdot d_H(t)^{\gamma}$$

$$w_{\text{secondary}}(t) = w^{\text{base}}_C \cdot (1 - d_H(t))^{\gamma}$$

**Behavior at extremes:**

| State | $d_H$ | $w_{\text{primary}}$ | $w_{\text{secondary}}$ |
|-------|:-----:|:--------------------:|:----------------------:|
| Full energy (no hunger) | 0 | $w^{\text{base}}_H$ | $w^{\text{base}}_C$ |
| Starving (max hunger) | 1 | 1.0 | 0.0 |

Higher $\gamma$ makes the transition between drives sharper. At
$\gamma = 1$ the transition is linear. At $\gamma = 3$ curiosity
drops to near-zero with moderate hunger.

---

## `combine_drive_scores`

Combines contributions from N drives into final per-action scores.
This function is generic -- it works with any number of drives, not
just hunger + curiosity.

```python
from axis.systems.construction_kit.arbitration.scoring import combine_drive_scores
```

### Signature

```python
def combine_drive_scores(
    drive_contributions: Sequence[tuple[float, ...]],  # per-drive action scores
    drive_activations: Sequence[float],                 # per-drive activation
    drive_weights: Sequence[float],                     # per-drive weight
) -> tuple[float, ...]
```

### Formula

For each action $a$:

$$\psi(a) = \sum_{i} w_i \cdot d_i \cdot \varphi_i(a)$$

where $w_i$ is the drive weight, $d_i$ is the drive activation, and
$\varphi_i(a)$ is the drive's contribution for action $a$.

All contribution tuples must have the same length. Raises `ValueError`
if zero drives are provided.

---

## `DriveWeights`

Data model for the weight computation result.

```python
from axis.systems.construction_kit.arbitration.types import DriveWeights
```

Frozen Pydantic model.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `hunger_weight` | `float` | $\geq 0$ | Weight for the primary (hunger) drive |
| `curiosity_weight` | `float` | $\geq 0$ | Weight for the secondary (curiosity) drive |

---

## Usage Example

```python
from axis.systems.construction_kit.arbitration.weights import compute_maslow_weights
from axis.systems.construction_kit.arbitration.scoring import combine_drive_scores

# Compute dynamic weights from hunger activation
weights = compute_maslow_weights(
    hunger_output.activation,
    primary_weight_base=0.3,
    secondary_weight_base=1.0,
    gating_sharpness=2.0,
)

# Combine two drives into final action scores
action_scores = combine_drive_scores(
    drive_contributions=[
        hunger_output.action_contributions,
        curiosity_output.action_contributions,
    ],
    drive_activations=[
        hunger_output.activation,
        curiosity_output.activation,
    ],
    drive_weights=[
        weights.hunger_weight,
        weights.curiosity_weight,
    ],
)

# Pass action_scores to SoftmaxPolicy.select()
```

---

## Design References

- [System A+W Formal Model](../system-design/system-a+w/01_System A+W Model.md)
  -- drive arbitration and Maslow gating
- [System A+W Manual -- Drive Arbitration](../manuals/system-aw-manual.md#33-drive-arbitration)
  -- weight formulas and tuning guide
