# Prediction

The **prediction** package provides predictive memory, context encoding,
and signed prediction error decomposition. These components enable an
agent to form expectations about future observations and detect when
reality diverges from expectation.

**Import path:** `from axis.systems.construction_kit.prediction import ...`

**Source:** `src/axis/systems/construction_kit/prediction/`

---

## Feature Extraction

Extracts a predictive feature vector from an observation.

```python
from axis.systems.construction_kit.prediction.features import extract_predictive_features

features = extract_predictive_features(observation)
# Returns: (center_resource, up_resource, down_resource, left_resource, right_resource)
```

$$\Omega(u_t) \to y_t = (r_\text{center}, r_\text{up}, r_\text{down}, r_\text{left}, r_\text{right})$$

The function extracts the 5 local resource values from a Von Neumann
observation in canonical order. This is the explicit abstraction boundary
so that future systems can swap in a different feature extractor without
touching the rest of the predictive pipeline.

---

## Context Encoding

Encodes a feature vector into a discrete context index via binary
quantization.

```python
from axis.systems.construction_kit.prediction.context import encode_context

context = encode_context(features, threshold=0.5)
# Returns: integer in [0, 31]
```

$$C(y_t) \to s_t \in \{0, 1, \ldots, 31\}$$

Each feature is mapped to 0 (below threshold) or 1 (at or above
threshold). The 5 bits are packed into an integer:

| Bit 4 (MSB) | Bit 3 | Bit 2 | Bit 1 | Bit 0 (LSB) |
|:-----------:|:-----:|:-----:|:-----:|:-----------:|
| center | up | down | left | right |

This yields $|S| = 2^5 = 32$ discrete contexts.

---

## Predictive Memory

Stores expected next-step features per (context, action) pair.

```python
from axis.systems.construction_kit.prediction.memory import (
    PredictiveMemory,
    create_predictive_memory,
    get_prediction,
    update_predictive_memory,
)

memory = create_predictive_memory()                      # all zeros
predicted = get_prediction(memory, context=5, action="up")  # 5-tuple
memory = update_predictive_memory(
    memory, context=5, action="up",
    observed_features=(0.8, 0.0, 0.0, 0.0, 0.0),
    learning_rate=0.3,
)
```

Update rule (EMA):

$$q_{t+1}(s_t, a_t) = (1 - \eta_q) \cdot q_t(s_t, a_t) + \eta_q \cdot y_{t+1}$$

`PredictiveMemory` is a frozen Pydantic model. Updates return a new
instance. Entries are stored as sorted tuples for serialization
compatibility.

---

## Prediction Error

Computes signed prediction error with scalar aggregation.

```python
from axis.systems.construction_kit.prediction.error import (
    PredictionError,
    compute_prediction_error,
)

error = compute_prediction_error(
    predicted=(0.5, 0.0, 0.0, 0.0, 0.0),
    observed=(0.8, 0.0, 0.0, 0.0, 0.0),
    positive_weights=(0.5, 0.125, 0.125, 0.125, 0.125),
    negative_weights=(0.5, 0.125, 0.125, 0.125, 0.125),
)
# error.scalar_positive: weighted sum of positive surprises
# error.scalar_negative: weighted sum of negative surprises
```

Component-wise decomposition:

$$
\delta_t^+ = \max(y_{t+1} - \hat{y}_{t+1}, 0)
$$

$$
\delta_t^- = \max(\hat{y}_{t+1} - y_{t+1}, 0)
$$

Scalar aggregation:

$$
\varepsilon_t^+ = \sum_j w_j^+ \cdot \delta_{t,j}^+
$$

$$
\varepsilon_t^- = \sum_j w_j^- \cdot \delta_{t,j}^-
$$

The default weight vector $(0.5, 0.125, 0.125, 0.125, 0.125)$ emphasizes
the center cell (current position) at 4x the weight of each neighbor.

---

## See Also

- [Traces](traces.md) -- dual-trace accumulation from prediction errors
- [Modulation](modulation.md) -- action score modulation from traces
- [System C Math Spec](../system-design/system-c/index.md) -- full mathematical model
