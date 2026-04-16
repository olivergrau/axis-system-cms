# Policy

**Package:** `axis.systems.construction_kit.policy`

**Source:** `src/axis/systems/construction_kit/policy/`

The policy layer converts pre-computed action scores into an action
choice. It applies admissibility masking (blocking impossible actions),
softmax normalization, and either stochastic or deterministic selection.

---

## SoftmaxPolicy

Softmax action selection with admissibility masking. Accepts a generic
tuple of per-action scores from any source -- a single drive, combined
multi-drive scores, or custom scoring logic. Satisfies `PolicyInterface`.

```python
from axis.systems.construction_kit.policy.softmax import SoftmaxPolicy
```

### Constructor

```python
SoftmaxPolicy(
    *,
    temperature: float,     # softmax temperature (lower = peakier)
    selection_mode: str,    # "sample" or "argmax"
)
```

### `select(action_scores, observation, rng) -> PolicyResult`

```python
def select(
    self,
    action_scores: tuple[float, ...],  # 6-element tuple, one per action
    observation: Observation,           # used for admissibility masking
    rng: np.random.Generator,          # framework-provided RNG for reproducibility
) -> PolicyResult
```

**Pipeline:**

1. **Admissibility mask** -- derives per-action admissibility from the
   observation's traversability values.
2. **Mask application** -- sets scores for inadmissible actions to $-\infty$.
3. **Softmax** -- numerically stable exponential normalization:
   $P(a_i) = \frac{e^{\beta \cdot (s_i - s_{max})}}{\sum_j e^{\beta \cdot (s_j - s_{max})}}$

    where $\beta = 1 / \text{temperature}$ and the sum runs over
    admissible actions only. Masked actions receive probability 0.

4. **Selection** -- either sample from the distribution or take argmax.

### Admissibility Masking

| Action | Admissible when... |
|--------|-------------------|
| up | `observation.up.traversability > 0` |
| down | `observation.down.traversability > 0` |
| left | `observation.left.traversability > 0` |
| right | `observation.right.traversability > 0` |
| consume | Always admissible |
| stay | Always admissible |

Movement into non-traversable cells (obstacles, out of bounds) is
blocked. Consume and stay are always available.

### Selection Modes

- **`"sample"`** -- Draws from the probability distribution using
  `rng.choice()`. Provides stochastic exploration.
- **`"argmax"`** -- Picks the action with highest probability
  deterministically. Useful for evaluation or when drive scores
  already encode sufficient exploration.

### Temperature Effects

- **Low temperature** (e.g. 0.1) -- near-argmax behavior, highest-scored
  action dominates.
- **High temperature** (e.g. 5.0) -- near-uniform distribution, actions
  selected almost randomly.
- **Temperature 1.0** -- standard softmax.

---

## PolicyResult

The `select()` method returns an SDK `PolicyResult`:

```python
from axis.sdk.types import PolicyResult
```

| Field | Type | Description |
|-------|------|-------------|
| `action` | `str` | Selected action name (e.g. `"right"`) |
| `policy_data` | `dict[str, Any]` | Full pipeline diagnostics (see below) |

**`policy_data` contents:**

| Key | Type | Description |
|-----|------|-------------|
| `raw_contributions` | `tuple[float, ...]` | Input action scores |
| `admissibility_mask` | `tuple[bool, ...]` | Per-action admissibility |
| `masked_contributions` | `tuple[float, ...]` | Scores after masking |
| `probabilities` | `tuple[float, ...]` | Post-softmax probabilities |
| `selected_action` | `str` | Chosen action |
| `temperature` | `float` | Temperature used |
| `selection_mode` | `str` | Mode used |

This data flows into `DecideResult.decision_data` and is persisted in
step traces for visualization and analysis.

---

## Usage Example

```python
from axis.systems.construction_kit.policy.softmax import SoftmaxPolicy

policy = SoftmaxPolicy(temperature=1.0, selection_mode="sample")

# In decide():
# action_scores can come from a single drive or combined multi-drive scores
action_scores = hunger_output.action_contributions

result = policy.select(action_scores, observation, rng)
action = result.action           # e.g. "consume"
probs = result.policy_data["probabilities"]  # for tracing
```

!!! note "Generic interface"
    `SoftmaxPolicy.select()` accepts any `tuple[float, ...]` of action
    scores. It does not depend on a specific drive output type. This
    means you can pass scores from `HungerDrive`, combined scores from
    `combine_drive_scores`, or any custom scoring function.

---

## Design References

- [System A Formal Specification](../system-design/system-a/01_System A Baseline.md)
  -- softmax policy model
- [System A+W Manual -- Tuning Guide](../manuals/system-aw-manual.md#5-tuning-guide)
  -- temperature interaction with drive scores
