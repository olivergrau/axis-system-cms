# Tutorial: Understanding Prediction-Error-Driven Behavior

## Goal of This Tutorial

This tutorial explains a minimal but powerful idea:

> An agent does not need explicit reward maximization to adapt.
> It can learn by comparing **what it expected** with **what actually happened**.

From that comparison, the agent develops:

- expectations about future outcomes,
- accumulated traces of disappointment and positive surprise,
- and a changing behavioral tendency over time.

By the end of this tutorial, you should understand:

- what the agent represents,
- why quantized context matters,
- how prediction error is computed,
- how traces emerge from repeated experience,
- and how this changes behavior.

This tutorial is didactic by design.
It explains the core mechanism in a simplified, general form before connecting it back to AXIS-style predictive agents.

---

## 1. The Basic Idea

A prediction-error-driven agent repeats a simple loop:

1. perceive the current situation,
2. classify it into a context,
3. choose an action,
4. predict what will happen next,
5. observe what actually happens,
6. compute the mismatch,
7. update memory and behavior.

The key principle is:

> The agent does not ask only, "Was this good?"
> It asks, "Was this better or worse than I expected?"

That difference between expectation and reality is the **prediction error**.

---

## 2. From Raw Perception to Context

The agent does not work directly with the full world.
It only has access to a local feature vector.

### 2.1 Feature Vector

For example:

```text
y = (food_right=0.2, food_left=0.0, obstacle=0, energy=0.5)
```

In general:

$$
y_t \in \mathbb{R}^n
$$

This vector is the agent's current local perceptual state.

### 2.2 Why Context Quantization Exists

The agent does not store separate expectations for every possible real-valued input.
Instead, it maps raw input to a discrete context:

$$
s_t \in \mathcal{S}
$$

Examples:

```text
s_1 = "food_right"
s_2 = "no_food"
s_3 = "low_energy"
```

So the context is:

- not the full observation,
- but a coarse abstraction of it.

### 2.3 Why This Matters

Quantized context introduces several important properties:

1. State aggregation:
   similar situations are treated as equivalent.
2. Memory efficiency:
   the agent stores expectations per context-action pair rather than per raw input.
3. Generalization:
   learning in one situation transfers to similar situations.
4. Explicit modeling bias:
   the designer chooses what distinctions matter.

This also creates a trade-off:

- too coarse: important distinctions are lost,
- too fine: learning becomes fragmented and sparse.

---

## 3. The Predictive Model

The core memory structure is:

$$
q(s,a)
$$

This stores the expected next observation for action $a$ in context $s$.

In a more formal interpretation:

$$
q(s,a) \approx \mathbb{E}[y_{t+1} \mid s_t = s,\ a_t = a]
$$

### Example

```text
q("food_right", "move_right") = (0.1, 0, 0, 0.6)
```

Meaning:

> "If I move right in this context, I expect the next perceptual features to look like this."

This is not yet behavior.
It is only a learned expectation.

---

## 4. A Single Step of the System

Suppose the current step is $t$.

1. The agent perceives a feature vector: $y_t$

2. It maps this to a context: $s_t$

3. It selects an action: $a_t$

4. It retrieves the expected next observation: $\hat y_{t+1} = q(s_t,a_t)$

5. After acting, it observes the real next outcome: $y_{t+1}$

Now the system can compare prediction and reality.

---

## 5. Prediction Error

The prediction error is:

$$
\delta_t = y_{t+1} - \hat y_{t+1}
$$

### Example

```text
Prediction: (0.2, 0, 0, 0.5)
Reality:    (0.1, 0, 0, 0.4)
```

Then:

```text
δ = (-0.1, 0, 0, -0.1)
```

This means:

- some components were lower than expected,
- none were higher than expected.

So the action under-delivered.

---

## 6. Positive and Negative Error

The system splits prediction error into two parts:

$$
\delta_t^+ = \max(\delta_t, 0)
$$

$$
\delta_t^- = \max(-\delta_t, 0)
$$

Interpretation:

| Signal | Meaning |
|---|---|
| $\delta_t^+$ | better than expected |
| $\delta_t^-$ | worse than expected |

This split is crucial.

It allows the agent to distinguish between:

- "that action disappointed me"
- and "that action turned out better than expected"

---

## 7. Aggregating Error into Scalar Signals

Prediction error is usually vector-valued.
But behavior modulation often needs a scalar summary.

So the system aggregates:

$$
\varepsilon_t^+ = \sum_j w_j \delta_{t,j}^+
$$

$$
\varepsilon_t^- = \sum_j w_j \delta_{t,j}^-
$$

These produce two scalar signals:

- $\varepsilon_t^+$: positive surprise
- $\varepsilon_t^-$: negative surprise

The weights $w_j$ define which feature components matter most.

This is an important modeling choice.

For example:

- a food-seeking system may weight resource-related components heavily,
- a scout system may weight signal-related components,
- another system may emphasize safety-relevant features.

---

## 8. Traces: How Experience Persists

Single prediction errors do not yet define stable behavior.

The interesting part comes from **accumulation over time**.

The system maintains two traces:

$$
f_t = \lambda f_{t-1} + \varepsilon_t^-
$$

$$
c_t = \lambda c_{t-1} + \varepsilon_t^+
$$

where:

- $f_t$ accumulates disappointment,
- $c_t$ accumulates positive surprise,
- $\lambda \in [0,1)$ controls decay.

### Interpretation

| Variable | Meaning |
|---|---|
| $f_t$ | accumulated negative surprise, frustration, or risk-like pressure |
| $c_t$ | accumulated positive surprise, confirmation, or confidence-like pressure |

### Example

```text
λ = 0.8

t1: ε⁻ = 0.3 -> f = 0.3
t2: ε⁻ = 0.1 -> f = 0.34
t3: ε⁻ = 0   -> f = 0.272
```

The past still matters, but it fades.

This gives the system memory without needing explicit symbolic reasoning.

### Why Traces Matter

These traces are:

- not the predictive model itself,
- not raw knowledge,
- but a dynamic internal state shaped by recent experience.

They capture temporal trends rather than isolated events.

---

## 9. Updating the Predictive Model

The expectation for the actually used context-action pair is updated by:

$$
q(s_t,a_t) \leftarrow q(s_t,a_t) + \eta \bigl(y_{t+1} - q(s_t,a_t)\bigr)
$$

where:

- $\eta \in (0,1]$ is the learning rate.

Only the used entry is updated.

This means:

- the agent does not globally rewrite its model,
- it only adjusts the specific expectation tied to the experienced transition.

This keeps the system local and interpretable.

---

## 10. Separation of Roles

A useful way to understand the architecture is to separate three different things:

### 10.1 Predictive Model

$$
q(s,a)
$$

This answers:

> "What do I expect to happen?"

### 10.2 Internal Experience State

$$
f_t,\ c_t
$$

These answer:

> "How has recent experience shaped my stance toward future behavior?"

### 10.3 Decision Mechanism

This answers:

> "Given expectation and accumulated experience, what should I do now?"

This separation is important because it preserves interpretability:

- prediction,
- emotional-like accumulation,
- and action choice

are not collapsed into one opaque quantity.

---

## 11. Decision Making

At the simplest didactic level, we can imagine action scoring as:

$$
\text{score}(a) = U(q(s_t,a)) + \alpha c_t - \beta f_t
$$

and action selection via:

$$
P(a) = \text{softmax}(\text{score}(a))
$$

Interpretation:

- $U(q(s_t,a))$: expected utility of the predicted next outcome,
- $c_t$: accumulated positive tendency,
- $f_t$: accumulated negative tendency.

This simplified form helps illustrate the idea:

> prediction shapes expectation, and traces shape behavioral tone.

---

## 12. Behavioral Consequences

This mechanism creates a characteristic behavioral pattern:

- repeated disappointment leads to more cautious or avoidant behavior,
- repeated positive surprise leads to more confident or exploratory behavior,
- stable and unsurprising outcomes lead to neutral, steady behavior.

The crucial property is:

> behavior changes not because of one event, but because of the trend of recent prediction errors.

That makes the system adaptive without requiring explicit reward optimization.

---

## 13. How This Connects to AXIS System C

The explanation above is intentionally general.

System C in AXIS uses the same core principle, but with a more precise architectural form:

- prediction is local and context-conditioned,
- positive and negative predictive traces are explicit,
- predictive influence is bounded,
- and prediction acts on **action-level drive expression**, not on drive magnitude itself.

In other words, System C does **not** simply use:

$$
\text{score}(a) = U(q(s_t,a)) + \alpha c_t - \beta f_t
$$

Instead, it uses prediction to modulate the contribution of a drive over actions.

Conceptually:

$$
\text{drive contribution} = \text{drive strength} \times \text{action projection} \times \text{predictive modulation}
$$

That is a more structured and mechanistic design than the simplified tutorial version above.

So this tutorial should be read as:

- an intuitive conceptual introduction,
- not the full formal specification of System C.

---

## 14. Summary

The complete loop can be summarized as:

$$
\text{Perception} \rightarrow \text{Context} \rightarrow \text{Action}
$$

$$
\rightarrow \text{Prediction} \rightarrow \text{Observation} \rightarrow \text{Prediction Error}
$$

$$
\rightarrow \text{Trace Update} \rightarrow \text{Behavioral Bias}
$$

The central idea is:

> The agent does not need explicit reward optimization.
> It adapts by tracking how reality deviates from expectation over time.

This creates a compact but expressive foundation for:

- learning,
- adaptation,
- and behavior shaping

from one core mechanism:

> prediction and its violation.
