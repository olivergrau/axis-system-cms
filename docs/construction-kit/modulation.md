# Modulation

The **modulation** package provides exponential action score modulation
driven by dual traces. It rescales raw action scores by a factor
derived from learned frustration and confidence, suppressing unreliable
actions and reinforcing positively surprising ones while preserving the
sign semantics of negative baseline penalties such as `stay`.

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

## Compute Prediction Bias

Computes a bounded **additive** correction from the same signed trace
signal.

```python
from axis.systems.construction_kit.modulation.modulation import compute_prediction_bias

delta = compute_prediction_bias(
    frustration=0.3, confidence=0.1,
    positive_sensitivity=1.0,
    negative_sensitivity=1.5,
    prediction_bias_clip=0.25,
)
```

$$
\Delta_{pred} = \mathrm{clip}\left(
\tanh(\lambda_+ c - \lambda_- f),
[-b_{clip}, b_{clip}]
\right)
$$

This term is useful when a system wants prediction to contribute a small
additive reshaping term instead of, or in addition to, multiplicative
gain control.

---

## Describe Action Modulation

Returns the full structured modulation breakdown for all actions:

- final scores
- multiplicative modulation factors
- additive prediction biases
- per-action frustration values
- per-action confidence values

```python
from axis.systems.construction_kit.modulation.modulation import describe_action_modulation

details = describe_action_modulation(
    action_scores=(0.3, 0.2, 0.1, 0.4, 0.5, -0.05),
    context=15,
    actions=("up", "down", "left", "right", "consume", "stay"),
    trace_state=traces,
    positive_sensitivity=1.0,
    negative_sensitivity=1.5,
    modulation_min=0.3,
    modulation_max=2.0,
    modulation_mode="hybrid",
)
```

This is the most useful entry point for systems that need both:

- executable final scores
- and detailed introspection for traces, metrics, or visualization

System C+W uses `describe_action_modulation()` twice per step:

- once with the hunger trace state
- once with the curiosity trace state

That dual use is still purely generic construction-kit behavior; the
system decides only which trace state and parameters to pass in.

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
\text{modulated}(a) =
\begin{cases}
\text{base\_score}(a) \times \mu(s_t, a), & \text{if } \text{base\_score}(a) \ge 0 \\
\text{base\_score}(a) \div \mu(s_t, a), & \text{if } \text{base\_score}(a) < 0
\end{cases}
$$

This rule matters for actions represented as negative penalties rather
than positive preferences:

- If $\mu > 1$, a positive score is reinforced, while a negative score
  becomes less negative.
- If $\mu < 1$, a positive score is suppressed, while a negative score
  becomes more negative.

In System C, this is especially relevant for `stay`, whose baseline
score is a negative suppression term. Dividing negative scores by
$\mu$ ensures that confidence makes `stay` less penalized and
frustration makes it more strongly penalized.

When trace state is empty (all zeros), every $\mu = 1.0$ and modulated
scores equal raw scores. This guarantees that prediction is neutral until
the agent has accumulated experience.

The `modulation_mode` can be configured as:

- `multiplicative` -- pure gain control
- `additive` -- pure additive prediction bias
- `hybrid` -- multiplicative modulation plus additive prediction bias

System C uses this machinery in a single-drive setting.
System C+W uses the same machinery independently for the hunger and
curiosity channels before downstream drive arbitration.

---

## See Also

- [Prediction](prediction.md) -- predictive memory and error computation
- [Traces](traces.md) -- dual-trace accumulation that feeds modulation
- [System C+W Math Spec](../system-design/system-cw/index.md) -- dual use of generic modulation for hunger and curiosity before arbitration
