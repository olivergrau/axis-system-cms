# System C Worked Examples

## Metadata
- Project: AXIS -- Complex Mechanistic Systems Experiment
- Author: Oliver Grau
- Type: Worked Example / Formal Companion Note
- Status: Draft v1.0
- Companion: System C Model (01_System C Model.md)

---

## 1. Purpose of this Document

This document provides step-by-step numerical worked examples for **System C**.

The goal is:

- to validate the internal consistency of the predictive extension,
- to demonstrate how predictive modulation changes action scoring,
- to show both disappointment-driven damping and positive-surprise reinforcement,
- and to provide reproducible numerical walkthroughs for later system design work.

No new concepts are introduced.
All examples follow the formal definitions in:

- `01_System C Model.md`
- `01_System A Baseline.md` for inherited baseline structures

---

## 2. Scope and Constraints

These worked examples assume the first concrete System C instance:

- single drive only: hunger
- predictive feature vector = local resource vector
- local predictive memory over context-action pairs
- both negative and positive predictive traces active
- no planning
- deterministic score evaluation

The examples are numerical illustrations of the design model, not implementation traces.

---

## 3. Structure of Worked Examples

Each example follows the same structure:

1. Initial State Definition
2. Local Observation and Predictive Features
3. Predictive Memory Retrieval
4. Drive Evaluation
5. Predictive Modulation
6. Action Scoring
7. Policy Selection
8. Transition and New Observation
9. Prediction Error
10. Trace and Memory Update
11. Post-State Interpretation

This extends the System A worked-example structure with explicit predictive phases.

---

## 4. Common Parameters and Notation

Unless stated otherwise, all examples use the following values.

### 4.1 Agent and Policy Parameters

| Parameter | Symbol | Value |
|---|---|---|
| Max energy | $E_{\max}$ | 100.0 |
| Inverse temperature | $\beta$ | 2.0 |
| Consume weight | $w_{consume}$ | 2.5 |
| Stay suppression | $\lambda_{stay}$ | 0.1 |

### 4.2 Predictive Parameters

| Parameter | Symbol | Value |
|---|---|---|
| Predictive memory learning rate | $\eta_q$ | 0.5 |
| Negative trace learning rate | $\eta_f$ | 0.4 |
| Positive trace learning rate | $\eta_c$ | 0.4 |
| Positive modulation gain | $\lambda_{+}$ | 0.8 |
| Negative modulation gain | $\lambda_{-}$ | 1.0 |
| Minimum modulation | $\mu_{\min}$ | 0.5 |
| Maximum modulation | $\mu_{\max}$ | 1.8 |

### 4.3 Aggregation Weights

For both positive and negative aggregation:

$$
w_c = 0.40,\quad
w_{up} = w_{down} = w_{left} = w_{right} = 0.15
$$

These sum to $1.0$ and satisfy the required center-cell dominance.

### 4.4 Action Set

$$
\mathcal{A} = \{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}, \text{CONSUME}, \text{STAY}\}
$$

### 4.5 Hunger Projection

$$
\phi_H(\text{UP},u_t) = r_{up}
$$

$$
\phi_H(\text{DOWN},u_t) = r_{down}
$$

$$
\phi_H(\text{LEFT},u_t) = r_{left}
$$

$$
\phi_H(\text{RIGHT},u_t) = r_{right}
$$

$$
\phi_H(\text{CONSUME},u_t) = w_{consume}\,r_c
$$

$$
\phi_H(\text{STAY},u_t) = -\lambda_{stay}
$$

### 4.6 Softmax

All policy probabilities are computed via:

$$
P(a) = \frac{\exp(\beta \psi_C(a))}{\sum_{a'} \exp(\beta \psi_C(a'))}
$$

---

## 5. Example Group A: Disappointment-Driven Damping

### A1. Failed Expected Consumption

#### 1. Objective

Show how repeated under-delivery on `CONSUME` suppresses the consume action in a familiar predictive context.

#### 2. Initial State

Energy:

$$
e_t = 40,\qquad E_{\max} = 100
$$

Therefore:

$$
d_H(t) = 1 - \frac{40}{100} = 0.6
$$

Predictive context:

$$
s_t = s^{(food)}
$$

Observation / predictive feature vector:

$$
y_t = r_t = (0.7,\ 0.2,\ 0.1,\ 0.0,\ 0.0)
$$

Interpretation:

- current cell contains substantial resource
- the upward neighbor is weakly promising
- other directions are weak or empty

#### 3. Predictive State Before Action

Prediction for `CONSUME` in this context:

$$
q_t(s^{(food)}, \text{CONSUME}) = \hat y_{t+1} = (0.6,\ 0.1,\ 0.1,\ 0.0,\ 0.0)
$$

Existing predictive traces:

$$
f_t(s^{(food)}, \text{CONSUME}) = 0.8
$$

$$
c_t(s^{(food)}, \text{CONSUME}) = 0.1
$$

Assume all other actions in this context have neutral predictive traces:

$$
f_t = 0,\qquad c_t = 0
$$

#### 4. Predictive Modulation

For `CONSUME`:

$$
\tilde{\mu}_H(s_t,\text{CONSUME}) =
\exp(0.8 \cdot 0.1 - 1.0 \cdot 0.8)
= \exp(-0.72)
\approx 0.487
$$

After clipping:

$$
\mu_H(s_t,\text{CONSUME}) = \mathrm{clip}(0.487, 0.5, 1.8) = 0.5
$$

For all other actions:

$$
\mu_H(s_t,a) = 1
$$

#### 5. Baseline Hunger Projection

$$
\phi_H(\text{UP},u_t)=0.2
$$

$$
\phi_H(\text{DOWN},u_t)=0.1
$$

$$
\phi_H(\text{LEFT},u_t)=0.0
$$

$$
\phi_H(\text{RIGHT},u_t)=0.0
$$

$$
\phi_H(\text{CONSUME},u_t)=2.5 \cdot 0.7 = 1.75
$$

$$
\phi_H(\text{STAY},u_t)=-0.1
$$

#### 6. Action Scores

Using:

$$
\psi_C(a)=d_H(t)\,\phi_H(a,u_t)\,\mu_H(s_t,a)
$$

we obtain:

| Action | $d_H$ | $\phi_H$ | $\mu_H$ | $\psi_C(a)$ |
|---|---:|---:|---:|---:|
| UP | 0.6 | 0.2 | 1.0 | 0.120 |
| DOWN | 0.6 | 0.1 | 1.0 | 0.060 |
| LEFT | 0.6 | 0.0 | 1.0 | 0.000 |
| RIGHT | 0.6 | 0.0 | 1.0 | 0.000 |
| CONSUME | 0.6 | 1.75 | 0.5 | 0.525 |
| STAY | 0.6 | -0.1 | 1.0 | -0.060 |

#### 7. Interpretation Before Transition

`CONSUME` remains the strongest action, but its score is substantially reduced from the unmodulated baseline:

$$
0.6 \cdot 1.75 = 1.05
$$

to:

$$
0.525
$$

Prediction has therefore not removed hunger or consumption pressure.
It has damped an action that has repeatedly under-delivered in this context.

#### 8. Actual Outcome

Assume the agent selects `CONSUME`, but the realized next resource vector is:

$$
y_{t+1} = (0.0,\ 0.1,\ 0.0,\ 0.0,\ 0.0)
$$

This means expected current-cell reward largely failed to materialize.

#### 9. Signed Prediction Error

Prediction:

$$
\hat y_{t+1} = (0.6,\ 0.1,\ 0.1,\ 0.0,\ 0.0)
$$

Observed:

$$
y_{t+1} = (0.0,\ 0.1,\ 0.0,\ 0.0,\ 0.0)
$$

Hence:

$$
\delta_t^{-} = (0.6,\ 0.0,\ 0.1,\ 0.0,\ 0.0)
$$

$$
\delta_t^{+} = (0,\ 0,\ 0,\ 0,\ 0)
$$

Aggregation:

$$
\varepsilon_t^{-} = 0.40\cdot 0.6 + 0.15\cdot 0.0 + 0.15\cdot 0.1 + 0.15\cdot 0 + 0.15\cdot 0
= 0.255
$$

$$
\varepsilon_t^{+} = 0
$$

#### 10. Trace Update

$$
f_{t+1}(s_t,\text{CONSUME}) = (1-0.4)\cdot 0.8 + 0.4 \cdot 0.255
= 0.48 + 0.102
= 0.582
$$

$$
c_{t+1}(s_t,\text{CONSUME}) = (1-0.4)\cdot 0.1 + 0.4 \cdot 0
= 0.06
$$

#### 11. Predictive Memory Update

$$
q_{t+1}(s_t,\text{CONSUME})
= 0.5 \cdot (0.6,\ 0.1,\ 0.1,\ 0.0,\ 0.0)
 + 0.5 \cdot (0.0,\ 0.1,\ 0.0,\ 0.0,\ 0.0)
$$

$$
= (0.3,\ 0.1,\ 0.05,\ 0.0,\ 0.0)
$$

#### 12. Post-State Interpretation

The context-action pair becomes less optimistic and remains negatively marked.

System C learns:

- expected reward at the current cell should be reduced
- `CONSUME` in this context should remain somewhat suppressed

This is not planning.
It is local action-level reliability learning.

---

## 6. Example Group B: Positive-Surprise Reinforcement

### B1. Unexpectedly Good Upward Move

#### 1. Objective

Show how a movement action becomes reinforced when the realized next local resource pattern is better than predicted.

#### 2. Initial State

Energy:

$$
e_t = 50,\qquad E_{\max}=100
$$

Thus:

$$
d_H(t)=1-\frac{50}{100}=0.5
$$

Predictive context:

$$
s_t = s^{(search)}
$$

Observation:

$$
y_t = r_t = (0.0,\ 0.3,\ 0.1,\ 0.0,\ 0.0)
$$

The local scene weakly favors moving upward.

#### 3. Predictive State Before Action

Prediction for `UP`:

$$
q_t(s^{(search)}, \text{UP}) = \hat y_{t+1} = (0.1,\ 0.2,\ 0.1,\ 0.0,\ 0.0)
$$

Existing traces:

$$
f_t(s^{(search)}, \text{UP}) = 0.1
$$

$$
c_t(s^{(search)}, \text{UP}) = 0.7
$$

#### 4. Predictive Modulation

$$
\tilde{\mu}_H(s_t,\text{UP}) =
\exp(0.8\cdot 0.7 - 1.0\cdot 0.1)
= \exp(0.46)
\approx 1.584
$$

After clipping:

$$
\mu_H(s_t,\text{UP}) = 1.584
$$

All other actions remain neutral:

$$
\mu_H(s_t,a)=1
$$

#### 5. Action Scores

Baseline projection:

$$
\phi_H(\text{UP},u_t)=0.3
$$

$$
\phi_H(\text{DOWN},u_t)=0.1
$$

$$
\phi_H(\text{LEFT},u_t)=0
$$

$$
\phi_H(\text{RIGHT},u_t)=0
$$

$$
\phi_H(\text{CONSUME},u_t)=2.5\cdot 0 = 0
$$

$$
\phi_H(\text{STAY},u_t)=-0.1
$$

Therefore:

| Action | $\phi_H$ | $\mu_H$ | $\psi_C(a)$ |
|---|---:|---:|---:|
| UP | 0.3 | 1.584 | $0.5 \cdot 0.3 \cdot 1.584 = 0.238$ |
| DOWN | 0.1 | 1.0 | 0.050 |
| LEFT | 0.0 | 1.0 | 0.000 |
| RIGHT | 0.0 | 1.0 | 0.000 |
| CONSUME | 0.0 | 1.0 | 0.000 |
| STAY | -0.1 | 1.0 | -0.050 |

#### 6. Interpretation Before Transition

The predictive reinforcement makes `UP` substantially more attractive than its baseline score:

$$
0.5 \cdot 0.3 = 0.15
$$

versus the reinforced score:

$$
0.238
$$

#### 7. Actual Outcome

Assume the agent moves `UP` and encounters a much better-than-expected local pattern:

$$
y_{t+1} = (0.5,\ 0.4,\ 0.2,\ 0.0,\ 0.0)
$$

#### 8. Signed Prediction Error

Predicted:

$$
\hat y_{t+1} = (0.1,\ 0.2,\ 0.1,\ 0.0,\ 0.0)
$$

Observed:

$$
y_{t+1} = (0.5,\ 0.4,\ 0.2,\ 0.0,\ 0.0)
$$

Thus:

$$
\delta_t^{+} = (0.4,\ 0.2,\ 0.1,\ 0.0,\ 0.0)
$$

$$
\delta_t^{-} = (0,\ 0,\ 0,\ 0,\ 0)
$$

Aggregation:

$$
\varepsilon_t^{+} = 0.40\cdot 0.4 + 0.15\cdot 0.2 + 0.15\cdot 0.1 = 0.205
$$

$$
\varepsilon_t^{-} = 0
$$

#### 9. Trace Update

$$
c_{t+1}(s_t,\text{UP}) = (1-0.4)\cdot 0.7 + 0.4\cdot 0.205
= 0.42 + 0.082
= 0.502
$$

$$
f_{t+1}(s_t,\text{UP}) = (1-0.4)\cdot 0.1 + 0 = 0.06
$$

#### 10. Predictive Memory Update

$$
q_{t+1}(s_t,\text{UP})
= 0.5\cdot (0.1,\ 0.2,\ 0.1,\ 0,\ 0)
 + 0.5\cdot (0.5,\ 0.4,\ 0.2,\ 0,\ 0)
$$

$$
= (0.3,\ 0.3,\ 0.15,\ 0,\ 0)
$$

#### 11. Post-State Interpretation

This context-action pair now records:

- an upward revision of expected payoff
- persistent positive action bias
- reduced relative disappointment

The key effect is:

> System C can learn not only avoidance of unreliable actions, but also preference for unexpectedly successful actions.

---

## 7. Example Group C: Reduction to System A

### C1. Predictive System Disabled

#### 1. Objective

Show that System C collapses exactly to the System A scoring rule when predictive modulation is disabled.

#### 2. Assumption

Set:

$$
\lambda_{+} = \lambda_{-} = 0
$$

Then, for every $(s,a)$:

$$
\tilde{\mu}_H(s,a) = \exp(0)=1
$$

and therefore:

$$
\mu_H(s,a)=1
$$

#### 3. Action Scoring

System C becomes:

$$
\psi_C(a)=d_H(t)\,\phi_H(a,u_t)\,\mu_H(s_t,a)
= d_H(t)\,\phi_H(a,u_t)
$$

This is exactly the baseline System A hunger score.

#### 4. Interpretation

Prediction is therefore a true extension layer, not a replacement architecture.

This reduction property is critical for:

- conceptual continuity
- controlled experimentation
- and clean comparison against the baseline system

---

## 8. Example Group D: Competing Directional Incentives

### D1. Strong Local Resource vs. Reinforced Directional Move

#### 1. Objective

Show that predictive reinforcement can create a real directional competition against an immediately attractive local consume option, without eliminating the baseline hunger structure.

#### 2. Initial State

Energy:

$$
e_t = 45,\qquad E_{\max}=100
$$

Therefore:

$$
d_H(t)=1-\frac{45}{100}=0.55
$$

Observation:

$$
y_t = r_t = (0.4,\ 0.5,\ 0.1,\ 0.0,\ 0.0)
$$

Interpretation:

- current cell has usable resource
- upward movement looks slightly better locally
- downward movement is weak
- left and right are empty

Predictive context:

$$
s_t = s^{(contest)}
$$

#### 3. Predictive State Before Action

Assume:

$$
f_t(s_t,\text{UP}) = 0.05,\qquad c_t(s_t,\text{UP}) = 0.9
$$

$$
f_t(s_t,\text{CONSUME}) = 0.2,\qquad c_t(s_t,\text{CONSUME}) = 0.1
$$

All other actions are neutral:

$$
f_t = 0,\qquad c_t = 0
$$

#### 4. Predictive Modulation

For `UP`:

$$
\tilde{\mu}_H(s_t,\text{UP})=
\exp(0.8\cdot 0.9 - 1.0\cdot 0.05)
= \exp(0.67)
\approx 1.955
$$

After clipping:

$$
\mu_H(s_t,\text{UP}) = \mathrm{clip}(1.955, 0.5, 1.8)=1.8
$$

For `CONSUME`:

$$
\tilde{\mu}_H(s_t,\text{CONSUME})=
\exp(0.8\cdot 0.1 - 1.0\cdot 0.2)
= \exp(-0.12)
\approx 0.887
$$

Thus:

$$
\mu_H(s_t,\text{CONSUME}) = 0.887
$$

All other actions:

$$
\mu_H(s_t,a)=1
$$

#### 5. Baseline Hunger Projection

$$
\phi_H(\text{UP},u_t)=0.5
$$

$$
\phi_H(\text{DOWN},u_t)=0.1
$$

$$
\phi_H(\text{LEFT},u_t)=0
$$

$$
\phi_H(\text{RIGHT},u_t)=0
$$

$$
\phi_H(\text{CONSUME},u_t)=2.5\cdot 0.4 = 1.0
$$

$$
\phi_H(\text{STAY},u_t)=-0.1
$$

#### 6. Action Scores

| Action | $\phi_H$ | $\mu_H$ | $\psi_C(a)=0.55\cdot\phi_H\cdot\mu_H$ |
|---|---:|---:|---:|
| UP | 0.5 | 1.8 | 0.495 |
| DOWN | 0.1 | 1.0 | 0.055 |
| LEFT | 0.0 | 1.0 | 0.000 |
| RIGHT | 0.0 | 1.0 | 0.000 |
| CONSUME | 1.0 | 0.887 | 0.488 |
| STAY | -0.1 | 1.0 | -0.055 |

#### 7. Interpretation

This is a genuine competition case.

Without prediction:

$$
\psi_{\text{baseline}}(\text{UP}) = 0.55\cdot 0.5 = 0.275
$$

$$
\psi_{\text{baseline}}(\text{CONSUME}) = 0.55\cdot 1.0 = 0.55
$$

So the baseline strongly prefers `CONSUME`.

With prediction:

$$
\psi_C(\text{UP}) = 0.495
$$

$$
\psi_C(\text{CONSUME}) = 0.488
$$

The reinforced directional move now slightly overtakes `CONSUME`.

This illustrates the intended System C behavior:

> action preference can be locally restructured by predictive history without changing the underlying hunger magnitude.

---

## 9. Example Group E: Consumption Still Dominates Under High Need

### E1. Severe Hunger Overrides Moderate Predictive Damping

#### 1. Objective

Show that even when `CONSUME` carries a negative predictive history, strong current need plus strong current-cell resource can still make it the dominant action.

#### 2. Initial State

Energy:

$$
e_t = 10,\qquad E_{\max}=100
$$

Therefore:

$$
d_H(t)=1-\frac{10}{100}=0.9
$$

Observation:

$$
y_t = r_t = (0.9,\ 0.2,\ 0.1,\ 0.0,\ 0.0)
$$

Predictive context:

$$
s_t = s^{(urgent)}
$$

#### 3. Predictive State Before Action

Assume `CONSUME` has an established negative history:

$$
f_t(s_t,\text{CONSUME}) = 0.6
$$

$$
c_t(s_t,\text{CONSUME}) = 0.1
$$

All movement actions are neutral:

$$
f_t=0,\qquad c_t=0
$$

#### 4. Predictive Modulation

For `CONSUME`:

$$
\tilde{\mu}_H(s_t,\text{CONSUME})=
\exp(0.8\cdot 0.1 - 1.0\cdot 0.6)
= \exp(-0.52)
\approx 0.595
$$

Thus:

$$
\mu_H(s_t,\text{CONSUME})=0.595
$$

All other actions:

$$
\mu_H(s_t,a)=1
$$

#### 5. Baseline Hunger Projection

$$
\phi_H(\text{UP},u_t)=0.2
$$

$$
\phi_H(\text{DOWN},u_t)=0.1
$$

$$
\phi_H(\text{LEFT},u_t)=0
$$

$$
\phi_H(\text{RIGHT},u_t)=0
$$

$$
\phi_H(\text{CONSUME},u_t)=2.5\cdot 0.9 = 2.25
$$

$$
\phi_H(\text{STAY},u_t)=-0.1
$$

#### 6. Action Scores

| Action | $\phi_H$ | $\mu_H$ | $\psi_C(a)=0.9\cdot\phi_H\cdot\mu_H$ |
|---|---:|---:|---:|
| UP | 0.2 | 1.0 | 0.180 |
| DOWN | 0.1 | 1.0 | 0.090 |
| LEFT | 0.0 | 1.0 | 0.000 |
| RIGHT | 0.0 | 1.0 | 0.000 |
| CONSUME | 2.25 | 0.595 | 1.205 |
| STAY | -0.1 | 1.0 | -0.090 |

#### 7. Interpretation

Despite substantial predictive damping, `CONSUME` remains overwhelmingly dominant:

$$
\psi_C(\text{CONSUME}) = 1.205
$$

versus:

$$
\psi_C(\text{UP}) = 0.180
$$

This is an important boundary condition for System C:

> predictive history biases hunger expression, but does not erase the effect of acute homeostatic need and strong immediate opportunity.

The result is neither blind repetition nor blind avoidance.
It is a bounded predictive correction on top of a still drive-centered architecture.
