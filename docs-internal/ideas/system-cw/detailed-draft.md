## Q1: Should prediction modulate both hunger and curiosity?

**Answer: Yes. Prediction should modulate both hunger and curiosity action projections separately, prior to drive arbitration, while supporting multiple modulation modes (multiplicative, additive, hybrid).**

---

### Final Design Decision

In `system_cw`, predictive modulation is applied **at the level of drive-specific action tendencies**, not at the level of drive magnitude and not after drive aggregation.

Concretely:

1. Each drive produces its own action tendency:

   * hunger-based contribution
   * curiosity-based contribution

2. Prediction modulates each contribution independently:

   * using the same predictive trace state (confidence / frustration)
   * but applied separately to each drive’s action expression

3. The modulated contributions are then combined via the existing A+W arbitration mechanism.

This preserves the AXIS layering:

* drives define **what matters**
* projections define **how drives express themselves as actions**
* prediction defines **how reliable those actions have been in context**
* arbitration defines **which drive dominates at a given moment**

---

### Modulation Modes

Predictive modulation must support three modes, inherited from System C:

#### 1. Multiplicative (default, conservative)

Prediction rescales the drive contribution:

```text
H_pred(a) = H_raw(a) * μ(a)
C_pred(a) = C_raw(a) * μ(a)
```

Interpretation:

* confidence amplifies
* frustration suppresses
* prediction acts purely as a **reliability filter**

This is the most AXIS-consistent mode.

---

#### 2. Additive (bounded correction)

Prediction adds a small bounded bias:

```text
H_pred(a) = H_raw(a) + b(a)
C_pred(a) = C_raw(a) + b(a)
```

Interpretation:

* prediction can slightly favor or disfavor actions even when raw drive signal is weak or zero
* bias is explicitly bounded, so prediction does not become a new drive

---

#### 3. Hybrid (recommended practical mode)

Combination of both:

```text
H_pred(a) = H_raw(a) * μ(a) + b(a)
C_pred(a) = C_raw(a) * μ(a) + b(a)
```

Interpretation:

* multiplicative part preserves reliability scaling
* additive part enables fine-grained tie-breaking and weak-signal shaping

---

### Why Modulate Both Drives?

Modulating only hunger would leave curiosity blind to experience:

* the agent would keep exploring actions that repeatedly fail
* novelty would remain motivational but not *learnable*

By modulating both:

* hunger learns which consumptive actions are reliable
* curiosity learns which exploratory directions are worth revisiting

This creates a coherent synthesis:

> hunger defines metabolic pressure
> curiosity defines epistemic pressure
> prediction defines local trust in action outcomes

---

### Constraint

Prediction must **never alter drive magnitude directly**. It only modulates action expression.

This ensures:

* interpretability is preserved
* drives remain the only motivational sources
* prediction remains a local, mechanistic adaptation layer rather than a hidden planner

---

## Q2: What counts as positive or negative predictive outcome for curiosity-driven movement?

**Answer: Curiosity success should be defined as novelty-weighted exploration yield.**

For `system_cw`, curiosity should not treat novelty alone as success. A movement is curiosity-successful when it leads the agent into a locally richer action environment, especially if the target direction was novel.

### Local Resource Value

Given an observation (u_t), define the local resource value as:

$$
R_{\text{local}}(u_t)
=

\omega_c r_c(t)
+
\omega_n \cdot
\frac{
r_{up}(t)+r_{down}(t)+r_{left}(t)+r_{right}(t)
}{4}
$$

where:

* $r_c(t)$: resource on the current cell
* $r_{dir}(t)$: resource in neighboring directions
* $\omega_c$: weight for directly available resource
* $\omega_n$: weight for neighboring opportunity

### Raw Exploration Yield

After action (a_t), compare the local resource value before and after the action:

$$
Y_t =
R_{\text{local}}(u_{t+1})
-

R_{\text{local}}(u_t)
$$

Interpretation:

```text
Y_t > 0  → the action led to a locally richer environment
Y_t = 0  → no meaningful local improvement
Y_t < 0  → the action led to a locally poorer environment
```

### Novelty-Weighted Exploration Yield

For movement actions, let (\nu_{a_t}) be the pre-action novelty signal of the chosen direction.

Then define curiosity outcome as:

$$
Y^C_t =
\nu_{a_t} \cdot Y_t
$$

So:

$$
Y^C_t =
\nu_{a_t}
\cdot
\left(
R_{\text{local}}(u_{t+1})
-

R_{\text{local}}(u_t)
\right)
$$

### Positive and Negative Curiosity Outcome

The curiosity-specific predictive outcome is split into positive and negative components:

$$
\varepsilon^{C,+}_t = \max(Y^C_t, 0)
$$

$$
\varepsilon^{C,-}_t = \max(-Y^C_t, 0)
$$

These values update the curiosity-side confidence and frustration traces.

### Interpretation

A movement action is curiosity-positive when:

* the selected direction had high novelty
* and the resulting local environment is richer than before

A movement action is curiosity-negative when:

* the selected direction was novel
* but the resulting local environment is poorer than before

This creates a useful distinction:

```text
novel + richer     → strong curiosity confidence
novel + unchanged  → neutral or weak update
novel + poorer     → curiosity frustration
familiar + richer  → weak curiosity update
familiar + poorer  → weak negative curiosity update
```

### Design Constraint

This must remain **retrospective**.

The agent does not evaluate future resource yield before acting. It only updates prediction after the world transition, using:

$$
u_t,\quad a_t,\quad u_{t+1}
$$

Therefore, this mechanism does not introduce planning. It remains local, mechanistic, and compatible with System C’s predictive update logic.

---

## Q3: Should the predictive context remain purely sensory, or include compact world-model-derived bits?

**Answer: The predictive context should include compact world-model-derived features, but only as low-dimensional indicators.**

The predictive context should no longer be purely sensory in `system_cw`.

System C currently encodes prediction from local sensory resource features only:

$$
y_t = \Omega(u_t) = (r_c, r_u, r_d, r_l, r_r)
$$

For `system_cw`, this should be extended to:

$$
y^{CW}_t =
(
r_c, r_u, r_d, r_l, r_r,
\nu_{up}, \nu_{down}, \nu_{left}, \nu_{right}
)
$$

where:

* $r_c, r_u, r_d, r_l, r_r$ are local sensory resource values
* $\nu_{dir}$ is the compact novelty estimate for each movement direction
* $(\nu_{dir}$ may already combine spatial novelty and sensory novelty

The predictive context then becomes:

$$
s^{CW}_t = C(y^{CW}_t)
$$

Prediction is still keyed by:

$$
(s^{CW}_t, a_t)
$$

not by absolute position, route history, or full map state.

### Recommended v1 feature set

For v1, I would use:

$$
y^{CW}_t =
(
r_c,
r_{up},
r_{down},
r_{left},
r_{right},
\nu_{up},
\nu_{down},
\nu_{left},
\nu_{right}
)
$$

Optionally, add a single local saturation scalar:

$$
\bar{\nu}_{local}
=

\frac{
\nu_{up}+\nu_{down}+\nu_{left}+\nu_{right}
}{4}
$$

Then:

$$
y^{CW}_t =
(
r_c,
r_{up},
r_{down},
r_{left},
r_{right},
\nu_{up},
\nu_{down},
\nu_{left},
\nu_{right},
\bar{\nu}_{local}
)
$$

But I would not go beyond this in v1.

### What should not be included

Do not include:

```text
absolute position
full visit-count map
distance travelled
path history
known resource locations
best known resource direction
multi-step route estimates
```

Those would push the system toward planning or map-based control.

### Why this is still clean

This extension is acceptable because the world-model-derived information is:

```text
local
compact
agent-relative
non-planning
derived from visit count only
used for prediction context, not direct control
```

So we are not giving the agent a planner. We are giving prediction a richer local state description.

### Relationship to Question 2

Question 2 defines the **curiosity outcome**:

$$
Y^C_t =
\nu_{a_t}
\cdot
\left(
R_{\text{local}}(u_{t+1})
-

R_{\text{local}}(u_t)
\right)
$$

Question 3 defines the **context under which that outcome is learned**:

$$
s^{CW}_t = C(y^{CW}_t)
$$

So yes, they are connected:

```text
Q2: What was the curiosity outcome?
Q3: In what kind of local situation should this outcome be remembered?
```

That is the clean mental model.

My recommended answer is:

> `system_cw` should extend the System C sensory context with compact novelty features derived from the A+W world model. Prediction should learn not only which actions work under local resource patterns, but also which actions work under local novelty structure.

---

## Q4: Should there be separate predictive modulation parameters for hunger and curiosity?

**Answer: Yes. Predictive modulation should use shared memory and trace state, but apply drive-specific modulation parameters for hunger and curiosity.**

---

### Core Principle

In `system_cw`, prediction represents a **shared model of action reliability in context**, not separate beliefs per drive.

Therefore:

* **Predictive memory** (q(s,a)) is shared
* **Trace state** (f(s,a)) (frustration) and (c(s,a)) (confidence) is shared
* **Only the interpretation of prediction is drive-specific**

This preserves a single, consistent experiential model of the environment while allowing different drives to respond differently to that experience.

---

### Drive-Specific Modulation

Let the shared predictive evidence be:

$$
\sigma(a) = \lambda_+ \cdot c(s,a) - \lambda_- \cdot f(s,a)
$$

Instead of using a single global parameterization, `system_cw` defines **drive-specific modulation parameters**:

#### Hunger:

$$
\sigma_H(a) = \lambda^{H}_+ \cdot c(s,a) - \lambda^{H}_- \cdot f(s,a)
$$

#### Curiosity:

$$
\sigma_C(a) = \lambda^{C}_+ \cdot c(s,a) - \lambda^{C}_- \cdot f(s,a)
$$

These are then transformed into modulation signals:

$$
\mu_H(a) = \text{modulation}(\sigma_H(a))
$$

$$
\mu_C(a) = \text{modulation}(\sigma_C(a))
$$

and applied to the respective drive contributions:

$$
H_{\text{pred}}(a) = H_{\text{raw}}(a) \cdot \mu_H(a) (+ b_H(a))
$$


$$
C_{\text{pred}}(a) = C_{\text{raw}}(a) \cdot \mu_C(a) (+ b_C(a))
$$

where $b_H(a)$ and $b_C(a)$ are optional additive corrections in additive or hybrid modulation modes.

---

### Supported Modulation Modes (Per Drive)

Each drive should independently support:

* **multiplicative** (reliability scaling)
* **additive** (bounded bias)
* **hybrid** (combined scaling and bias)

This implies that the following parameters should be **separate for hunger and curiosity**:

* positive sensitivity $\lambda^{H}_+, \lambda^{C}_+$
* negative sensitivity $\lambda^{H}_-, \lambda^{C}_-$
* modulation bounds $(\mu^{H}_{\min}, \mu^{H}_{\max}), (\mu^{C}_{\min}, \mu^{C}_{\max})$
* additive bias scale $\lambda^{H}_{\text{pred}}, \lambda^{C}_{\text{pred}}$
* additive bias clipping threshold $\beta^{H}_{\text{clip}}, \beta^{C}_{\text{clip}}$

---

### Interpretation

This design allows the same predictive experience to influence drives differently.

For example:

* A context-action pair may be **energetically unproductive** but **exploratively valuable**
* Hunger may suppress the action due to repeated disappointment
* Curiosity may still amplify the same action due to novelty-weighted yield

This creates a meaningful divergence:

```text
Hunger:     "this action does not pay off metabolically"
Curiosity:  "this action still expands useful exploration"
```

---

### Design Constraint

To preserve interpretability and architectural clarity:

* Predictive memory and trace updates must remain **shared**
* Only modulation parameters and output transformation may differ per drive
* Prediction must not directly alter drive magnitudes

This ensures:

* a single coherent model of environmental feedback
* clear separation between motivation and reliability
* comparability with both System A+W and System C

---

### Summary

`system_cw` should implement:

```text
✔ shared predictive memory and trace state
✔ drive-specific modulation sensitivities
✔ drive-specific modulation bounds
✔ drive-specific additive bias parameters
✔ per-drive modulation modes (multiplicative, additive, hybrid)
```

This yields a system where:

* experience is unified
* interpretation is contextual
* behavior reflects both motivation and learned reliability without collapsing into a single undifferentiated control signal

---

## Q5: How should we preserve interpretability in traces and visualization once two drives and predictive modulation interact?

**Answer: Interpretability should be preserved through layered decision tracing.**

`system_cw` must not only record the final action score. It should record the complete causal decomposition of the decision.

For each action (a), the trace should include:

$$
H_{\text{raw}}(a)
$$

$$
C_{\text{raw}}(a)
$$

$$
\mu_H(a),\quad b_H(a)
$$

$$
\mu_C(a),\quad b_C(a)
$$

$$
H_{\text{pred}}(a)
$$

$$
C_{\text{pred}}(a)
$$

$$
w_H(t),\quad w_C(t)
$$

$$
H_{\text{weighted}}(a)
$$

$$
C_{\text{weighted}}(a)
$$

$$
\psi(a)
$$

$$
P(a)
$$

This makes the final policy output decomposable into:

```text
raw motivation
predictive modulation
drive arbitration
final action probability
```

### Required Trace Sections

Each step trace should include:

```text
Observation
Novelty Features
Predictive Context
Raw Drive Projections
Predictive Modulation per Drive
Drive Arbitration
Final Action Scores
Policy Probabilities
Selected Action
Retrospective Prediction Update
```

### Visualization Principle

The viewer should expose at least three interpretive layers:

```text
Drive Layer        → hunger vs curiosity contributions
Prediction Layer   → confidence/frustration, multipliers, additive biases
Policy Layer       → final scores, probabilities, selected action
```

This prevents `system_cw` from becoming an opaque hybrid system.

### Core Constraint

The trace must preserve the separation between:

```text
motivation
prediction
arbitration
policy
```

This is essential for comparing `system_cw` against `system_a`, `system_a+w`, and `system_c` under the same experimental conditions.
