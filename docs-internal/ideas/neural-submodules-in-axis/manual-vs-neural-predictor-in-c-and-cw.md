# Manual vs Neural Predictor in System C and C+W

## 1. Purpose

This document recapitulates the existing predictive architecture of
`System C` and `System C+W`, and then lays out what exactly would change if the
manual predictive memory were replaced by a neural predictor.

The goal is not to redesign the whole agent. The goal is to make one very
specific substitution visible:

> replace the current explicit predictive memory mechanism with a learned
> predictor, while preserving as much of the surrounding mechanistic system as
> possible.

This is the cleanest way to test neural integration in AXIS without collapsing
multiple research questions into one.

---

## 2. System C: Existing Manual Predictive Architecture

`System C` is not a learned policy system.

It remains a mechanistic single-drive agent with:

- explicit hunger
- explicit action scoring
- explicit softmax policy
- explicit energy dynamics
- explicit transition semantics

Prediction is attached to the action-expression layer, not to motivation
itself.

### 2.1 Core Decision Principle

System C rejects formulations in which prediction directly changes hunger
magnitude.

It does **not** use something like:

$$
d_H(t) = h_t + \, \lambda \, \varepsilon_t
$$

Instead, prediction acts on the expression of hunger over actions:

$$
\Pi_H(a,t) = d_H(t) \, \phi_H(a,u_t) \, \mu_H(s_t,a)
$$

This means:

- hunger remains the motivational source
- prediction only reshapes which actions hunger expresses more strongly

### 2.2 Predictive Representation

System C extracts a bounded predictive feature vector from the local
observation:

$$
y_t = \Omega(u_t)
$$

This is then compressed into a discrete predictive context:

$$
s_t = C(y_t)
$$

So the predictive system does not work over raw global world states. It works
only over compact local sensory structure.

### 2.3 Manual Predictive Memory

The current predictor is an explicit context-action memory:

$$
q_t : \mathcal{S} \times \mathcal{A} \rightarrow \mathcal{Y}
$$

Interpretation:

$$
q_t(s,a) = \hat y_{t+1}^{(s,a)}
$$

For each context-action pair, the system stores an expected next feature
vector.

This is a manual associative memory, not a learned function approximator.

### 2.4 Manual Predictor Update

The update rule is an exponential moving average:

$$
q_{t+1}(s_t,a_t)
=
(1-\eta_q)\,q_t(s_t,a_t)
+
\eta_q\,y_{t+1}
$$

Only the actually visited pair $(s_t,a_t)$ is updated.

Consequences:

- updates are strictly local
- no interference occurs across unrelated entries
- the memory is fully explicit and inspectable

### 2.5 Signed Prediction Error

The predicted next feature vector is compared to the actual one through signed
error decomposition.

Positive component:

$$
\delta_t^+ = \max(y_{t+1} - \hat y_{t+1}, 0)
$$

Negative component:

$$
\delta_t^- = \max(\hat y_{t+1} - y_{t+1}, 0)
$$

Aggregated scalar errors:

$$
\varepsilon_t^+ = \sum_j w_j^+ \, \delta_{t,j}^+
$$

$$
\varepsilon_t^- = \sum_j w_j^- \, \delta_{t,j}^-
$$

Interpretation:

- $\varepsilon_t^-$ = disappointment / unreliability
- $\varepsilon_t^+$ = positive surprise / opportunity

### 2.6 Trace State

System C does not use prediction error directly as the modulation factor.
Instead it maintains two local traces per context-action pair.

Frustration trace:

$$
f_{t+1}(s_t,a_t)
=
(1-\eta_f)\,f_t(s_t,a_t)
+
\eta_f\,\varepsilon_t^-
$$

Confidence trace:

$$
c_{t+1}(s_t,a_t)
=
(1-\eta_c)\,c_t(s_t,a_t)
+
\eta_c\,\varepsilon_t^+
$$

So prediction is translated into a behaviorally relevant reliability state.

### 2.7 Bounded Predictive Modulation

The traces are converted into a bounded modulation factor:

$$
\mu_H(s_t,a)
=
\mathrm{clip}
\left(
\exp(\lambda_+ c(s_t,a) - \lambda_- f(s_t,a)),
\mu_{min},
\mu_{max}
\right)
$$

This factor multiplies the raw hunger action score.

Thus the full logic of System C is:

1. hunger produces raw action preferences
2. prediction-derived traces alter trust in those actions
3. modulation is bounded
4. policy acts on the modulated scores

---

## 3. System C+W: Existing Manual Predictive Architecture

`System C+W` keeps the same predictive logic in spirit, but embeds it into a
richer dual-drive agent.

It preserves:

- hunger
- curiosity
- world model
- arbitration
- explicit transition semantics

and adds a predictive layer over the combined local feature space.

### 3.1 Shared Predictive Feature Space

System C+W uses one shared predictive feature vector:

$$
y_t^{CW} = \Omega_{CW}(u_t, \phi_C)
$$

In the current model, this feature vector includes both:

- local resource structure
- novelty-derived structure

For the v1 formal model:

$$
y_t^{CW} =
(r_c, r_{up}, r_{down}, r_{left}, r_{right},
\nu_{up}, \nu_{down}, \nu_{left}, \nu_{right}, \bar{\nu})
$$

So the predictor is already more than a pure resource predictor.

### 3.2 Shared Context Encoding

The shared predictive feature vector is compressed into a compact context:

$$
s_t = C_{CW}(y_t^{CW})
$$

This is a deliberately low-cardinality predictive address space.

### 3.3 Shared Manual Predictive Memory

The predictor itself is still explicit and table-like:

$$
q_t : \mathcal{S} \times \mathcal{A} \to \mathcal{Y}
$$

with interpretation:

$$
q_t(s,a) = \hat y_{t+1}^{(s,a)}
$$

and EMA update:

$$
q_{t+1}(s_t,a_t)
=
(1-\eta_q)\,q_t(s_t,a_t)
+
\eta_q\,y_{t+1}^{CW}
$$

So `System C+W` still uses an explicit local predictive memory, not a neural
predictor.

### 3.4 Shared Predictor, Drive-Specific Interpretation

The important architectural move in `System C+W` is that one predictor is used
for two different evaluative channels.

#### Hunger-side outcome semantics

A local resource-value functional is applied:

$$
V_R(u_t) = w_c r_c + w_n \bar r_n
$$

Then hunger-side actual and predicted outcomes are:

$$
Y_t^H(a_t) = V_R(u_{t+1}) - V_R(u_t)
$$

$$
\hat Y_t^H(a_t) = \hat V_R(q_t(s_t,a_t)) - V_R(u_t)
$$

#### Curiosity-side outcome semantics

For movement actions:

$$
Y_t^C(a_t) = \nu_{a_t}(t) \cdot Y_t^H(a_t)
$$

$$
\hat Y_t^C(a_t) = \nu_{a_t}(t) \cdot \hat Y_t^H(a_t)
$$

For non-movement actions, the formal model uses an explicit curiosity-side
penalty rule.

So the predictor is shared, but its interpretation is not.

### 3.5 Dual Trace Systems

System C+W then updates:

- hunger-side traces $z_t^H = (f_t^H, c_t^H)$
- curiosity-side traces $z_t^C = (f_t^C, c_t^C)$

Thus the architecture is:

- one shared predictive substrate
- two drive-specific trust dynamics

### 3.6 Pre-Arbitration Dual Modulation

Each drive is modulated separately before arbitration:

- hunger raw scores are modulated by hunger traces
- curiosity raw scores are modulated by curiosity traces
- only then are the two drives combined

This is a crucial design decision.

Prediction does not simply act on the final combined score. It enters one level
below, at the drive-expression layer.

---

## 4. What a Neural Predictor Would Replace

The cleanest substitution is very narrow.

### 4.1 In System C

Replace only the explicit predictive memory:

$$
q_t(s,a)
\quad \leadsto \quad
f_\theta(\cdot)
$$

Candidate forms:

#### Option A: context-action predictor

$$
\hat y_{t+1} = f_\theta(s_t, a_t)
$$

This stays closest to the current implementation style.

#### Option B: feature-action predictor

$$
\hat y_{t+1} = f_\theta(y_t, a_t)
$$

This is often scientifically stronger, because it removes the hard context
compression bottleneck and allows smooth generalization across nearby local
states.

In either case, all of the following remain analytical:

- hunger drive
- signed error decomposition
- trace updates
- modulation rule
- policy
- energy transition

### 4.2 In System C+W

Replace only the shared predictive memory with a learned predictor:

$$
\hat y_{t+1}^{CW} = f_\theta(y_t^{CW}, a_t)
$$

or, more conservatively,

$$
\hat y_{t+1}^{CW} = f_\theta(s_t, a_t)
$$

Again, preserve:

- the shared predictor idea
- drive-specific hunger/curiosity interpretation
- dual trace systems
- pre-arbitration modulation
- bounded behavioral influence

This would keep the main conceptual structure of `System C+W` intact.

---

## 5. Scientific Implications of the Substitution

### 5.1 What is Gained

#### Better generalization

The manual predictor generalizes only through the discrete context encoder.
A neural predictor can generalize across similar local states and action
situations.

That matters especially when:

- feature spaces become richer
- thresholds become brittle
- the context table becomes sparsely covered

#### Better scalability of predictive representation

In `System C+W`, the predictive target already mixes:

- exogenous resource structure
- endogenous novelty-derived structure

A table-based predictor becomes increasingly awkward as this feature space
becomes richer or more continuous.

A neural predictor is a more natural substrate for such mixed local
representations.

#### Stronger biological plausibility for adaptation

A learned predictor that changes through local prediction error is closer to a
plausible adaptive sensorimotor mechanism than a hard table with one explicit
entry per context-action pair.

### 5.2 What is Lost

#### Exact finite inspectability

Today the predictive memory has explicit entries:

- context
n- action
- expected next feature vector

With a neural predictor, the predictor becomes:

- distributed
- weight-based
- only indirectly interpretable

So some predictor-level transparency is lost.

#### Strict locality of update

With the manual predictor:

- only one visited context-action entry changes per step

With a neural predictor:

- one parameter update may change outputs across many inputs

This introduces interference and stability concerns.

#### Cleaner coverage reasoning

In the manual system, one can reason sharply about:

- which contexts have been visited
- which entries have been updated
- which associations are missing

A neural predictor changes the problem from explicit coverage to function
approximation quality.

---

## 6. Engineering Implications of the Substitution

### 6.1 Replace Memory Lookup + EMA with Forward + Update

Current manual pattern:

- `get_prediction(...)`
- `compute_prediction_error(...)`
- `update_predictive_memory(...)`

Neural replacement pattern:

- forward pass to compute $\hat y_{t+1}$
- compute predictive loss
- optimizer step on predictor parameters

So the transition logic becomes more ML-like, but only inside the predictive
submodule.

### 6.2 State and Persistence Changes

Manual predictor state is currently lightweight and explicit.

A neural predictor raises questions such as:

- are predictor weights part of agent state?
- is optimizer state part of agent state?
- are weights reset per episode or preserved across episodes in a run?
- does online adaptation survive a workspace run boundary?

These are not implementation details. They materially change the scientific
meaning of the experiment.

### 6.3 Runtime and Debugging

Manual predictor:

- cheap lookup
- cheap EMA update
- easy tracing

Neural predictor:

- forward pass
- backward pass
- optimizer state
- more opaque debugging

This is still technically manageable in AXIS grid worlds if the model remains
small, but the cost profile changes.

---

## 7. What Must Remain Invariant

To keep the substitution scientifically meaningful, the following invariants
should be preserved.

### 7.1 For System C

- prediction acts on action expression, not hunger magnitude
- signed error remains explicit
- traces remain explicit
- modulation remains bounded
- neutral predictor mode still reduces behavior toward the non-predictive baseline

### 7.2 For System C+W

- predictor remains shared
- hunger and curiosity interpretation remain separate
- traces remain drive-specific
- modulation remains pre-arbitration
- predictive influence remains bounded
- reduction toward `A+W` remains possible

If these invariants are abandoned, the neural version becomes a different
research object rather than a clean predictive substitution.

---

## 8. Best Replacement Strategy

### 8.1 First Prototype

The best first prototype is:

- `System C`
- explicit drives unchanged
- explicit traces unchanged
- explicit modulation unchanged
- neural next-feature predictor only

This isolates the scientific question:

> what changes when explicit local predictive memory is replaced by a learned
> local predictor, while the rest of the cognitive architecture stays fixed?

### 8.2 Second Prototype

Then move to:

- `System C+W`
- same substitution idea
- preserve shared predictor + dual trace interpretation

This is scientifically richer, because it tests whether one learned predictive
substrate can support both:

- homeostatic evaluation
- exploratory evaluation

without collapsing the drive architecture.

---

## 9. Bottom-Line Conclusion

The existing predictors in `System C` and `System C+W` are:

- explicit
- local
- table-like
- EMA-updated
- tightly integrated into a larger analytical modulation system

A neural variant should therefore not replace the whole decision pipeline.
It should replace only the predictive substrate.

That gives the cleanest scientific comparison:

- **manual local predictor** vs **learned local predictor**
- with the surrounding mechanistic system held fixed

This is the strongest path if AXIS wants to test neural integration without
immediately sacrificing the interpretability that makes the current systems
valuable.
