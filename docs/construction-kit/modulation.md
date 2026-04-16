# Modulation

The **modulation** package provides exponential action score modulation
driven by dual traces. It multiplies raw action scores by a factor
derived from learned frustration and confidence, suppressing unreliable
actions and reinforcing positively surprising ones.

**Import path:** `from axis.systems.construction_kit.modulation import ...`

**Source:** `src/axis/systems/construction_kit/modulation/`

---

## Compute Modulation

Computes a single modulation factor from frustration and confidence values.

```python
from axis.systems.construction_kit.modulation.modulation import compute_modulation

mu = compute_modulation(
    frustration=0.3, confidence=0.1,
    positive_sensitivity=1.0,    # lambda_+
    negative_sensitivity=1.5,    # lambda_-
    modulation_min=0.3,
    modulation_max=2.0,
)
```

$$
\tilde{\mu} = \exp(\lambda_+ \cdot c - \lambda_- \cdot f)
$$

$$
\mu = \text{clip}(\tilde{\mu}, \mu_\min, \mu_\max)
$$

The loss-averse parameterization ($\lambda_- > \lambda_+$) means that equal
frustration and confidence produce a net suppressive effect. This mirrors
prospect theory: losses loom larger than equivalent gains.

| Parameter | Symbol | Default | Role |
|-----------|:------:|:-------:|------|
| `positive_sensitivity` | $\lambda_+$ | 1.0 | Confidence amplification |
| `negative_sensitivity` | $\lambda_-$ | 1.5 | Frustration suppression |
| `modulation_min` | $\mu_\min$ | 0.3 | Floor (prevents full suppression) |
| `modulation_max` | $\mu_\max$ | 2.0 | Ceiling (limits reinforcement) |

---

## Modulate Action Scores

Applies modulation to all action scores at once by looking up each
action's frustration and confidence from the trace state.

```python
from axis.systems.construction_kit.modulation.modulation import modulate_action_scores

modulated = modulate_action_scores(
    action_scores=(0.3, 0.2, 0.1, 0.4, 0.5, -0.05),
    context=15,
    actions=("up", "down", "left", "right", "consume", "stay"),
    trace_state=traces,
    positive_sensitivity=1.0,
    negative_sensitivity=1.5,
    modulation_min=0.3,
    modulation_max=2.0,
)
```

For each action $a$:

$$
\text{modulated}(a) = \text{base\_score}(a) \times \mu(s_t, a)
$$

When trace state is empty (all zeros), every $\mu = 1.0$ and modulated
scores equal raw scores. This guarantees that prediction is neutral until
the agent has accumulated experience.

---

## See Also

- [Prediction](prediction.md) -- predictive memory and error computation
- [Traces](traces.md) -- dual-trace accumulation that feeds modulation
