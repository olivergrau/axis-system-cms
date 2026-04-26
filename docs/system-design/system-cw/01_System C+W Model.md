# System C+W: A Predictive Dual-Drive Agent with Shared Memory and Drive-Specific Traces

## Metadata
- Project: AXIS -- Complex Mechanistic Systems Experiment
- Type: Formal Research Note
- Status: Draft v1.0
- Scope: Dual-drive agent with shared predictive memory, separate hunger/curiosity traces, and pre-arbitration predictive modulation
- Extends: System A+W and System C
- Constraints: No planning, no route memory, no richer world model than the minimal visit-count model

---

## 1. Objective

This document defines **System C+W** as the predictive extension of the
dual-drive A+W agent.

System C+W preserves the AXIS commitments:

- local sensing,
- explicit internal state,
- mechanistic drives,
- bounded memory structures,
- no hidden planner,
- and interpretable step-level behavior.

It combines:

- the **hunger + curiosity** architecture of System A+W,
- the **shared predictive memory** idea of System C,
- and **drive-specific predictive trust dynamics** for hunger and curiosity.

The central research question is:

> What behavior emerges when a dual-drive agent shares one predictive representation of the local world, but learns separate predictive trust for homeostatic and exploratory value?

---

## 2. Relationship to Earlier Systems

System C+W is best understood as:

- inheriting the raw-drive and arbitration structure of **System A+W**
- while adding a predictive layer inspired by **System C**

It keeps:

- the local Von Neumann observation model,
- the minimal visit-count world model,
- the hunger drive,
- the curiosity drive,
- the softmax policy,
- and the energy transition semantics.

It adds:

- a shared predictive feature vector,
- a shared predictive memory over compact contexts and actions,
- hunger-side and curiosity-side predictive outcome definitions,
- separate hunger and curiosity trace states,
- and separate predictive modulation passes before drive arbitration.

### 2.1 Exact Reduction to A+W

If predictive influence is neutralized on both drives:

$$
\mu_H(s,a) = 1,\qquad \mu_C(s,a) = 1
$$

for all $(s,a)$, then System C+W reduces exactly to the A+W action
pipeline.

### 2.2 Constructive Approximation Toward C

A System-C-like regime is obtained when:

- curiosity drive is disabled or neutralized,
- curiosity arbitration is disabled,
- curiosity-specific evidence and trace updates are ignored,
- novelty-derived predictive features are masked or held constant,
- and predictive context is reduced to resource-valued local structure.

This is a constructive approximation, not the primary exact reduction
guarantee.

---

## 3. Internal State

The internal state at time $t$ is:

$$
x_t = (e_t, m_t, w_t, q_t, z_t^H, z_t^C)
$$

where:

- $e_t \in [0, E_{\max}]$ is energy
- $m_t$ is the observation buffer
- $w_t$ is the minimal visit-count world model
- $q_t$ is the shared predictive memory
- $z_t^H = (f_t^H, c_t^H)$ is the hunger-side trace state
- $z_t^C = (f_t^C, c_t^C)$ is the curiosity-side trace state

The world still owns physical position externally.

---

## 4. Observation and Raw Drives

Let the local observation be:

$$
u_t = (u_t^{cur}, u_t^{up}, u_t^{down}, u_t^{left}, u_t^{right})
$$

with resource and traversability information exactly as in A+W.

### 4.1 Hunger

Hunger activation remains:

$$
d_H(t) = 1 - \frac{e_t}{E_{\max}}
$$

with raw action projection:

$$
\phi_H(a, u_t)
$$

as in Systems A and A+W.

### 4.2 Curiosity

Curiosity computes:

- spatial novelty
- sensory novelty
- composite novelty

using the same minimal world model and observation-buffer mechanisms as
System A+W. The raw curiosity action projection is:

$$
\phi_C(a, u_t, m_t, w_t)
$$

Resource-valued local structure is sufficient for the raw hunger and
curiosity projections and for baseline A+W dynamics. System C+W then
adds novelty-derived predictive features later in the predictive layer.

---

## 5. Shared Predictive Representation

System C+W uses one shared predictive feature vector:

$$
y_t^{CW} = \Omega_{CW}(u_t, \phi_C)
$$

For the first concrete system instance:

$$
y_t^{CW} =
(r_c, r_{up}, r_{down}, r_{left}, r_{right},
\nu_{up}, \nu_{down}, \nu_{left}, \nu_{right}, \bar{\nu})
$$

where:

- the first 5 features are local resource features
- the next 4 are directional composite novelty features
- $\bar{\nu}$ is the mean local novelty

The predictive feature space is:

$$
\mathcal{Y} = \mathrm{range}(y_t^{CW})
$$

The shared predictive target therefore mixes:

- **exogenous resource features**
- **endogenous novelty-derived features**

The novelty-derived features depend on the agent’s own observation
buffer and visit-count world model. Therefore $q_t$ is not a pure
external world-transition model; it predicts expected next features in
the closed-loop agent-environment interaction.

---

## 6. Compact Predictive Context

System C+W encodes the shared feature vector into a compact discrete
context:

$$
s_t = C_{CW}(y_t^{CW})
$$

For the v1 system this is a 6-bit context using:

- current-cell resource threshold
- mean-neighbor resource threshold
- best-neighbor resource threshold
- mean-novelty threshold
- peak-novelty threshold
- novelty-contrast threshold

Thus:

$$
s_t \in \{0,\dots,63\}
$$

The encoder must aggressively compress the feature space into a small,
well-covered discrete set; it must not create a high-cardinality
pseudo-state space.

---

## 7. Shared Predictive Memory

Predictive memory is shared:

$$
q_t : \mathcal{S} \times \mathcal{A} \to \mathcal{Y}
$$

Interpretation:

$$
q_t(s,a) = \hat y_{t+1}^{(s,a)}
$$

It stores the expected next shared predictive feature vector for action
$a$ in context $s$.

Update rule:

$$
q_{t+1}(s_t,a_t) = (1-\eta_q)\,q_t(s_t,a_t) + \eta_q\,y_{t+1}^{CW}
$$

---

## 8. Drive-Specific Outcome Semantics

The shared predictive memory is interpreted differently for the two
drives.

### 8.1 Hunger-Side Outcome

Define a local resource-value functional:

$$
V_R(u_t) = w_c\,r_c + w_n\,\bar r_n
$$

where $\bar r_n$ is the mean neighbor resource value.

Then the hunger-side actual and predicted outcomes are:

$$
Y_t^H(a_t) = V_R(u_{t+1}) - V_R(u_t)
$$

$$
\hat Y_t^H(a_t) = \hat V_R(q_t(s_t,a_t)) - V_R(u_t)
$$

### 8.2 Curiosity-Side Outcome

For movement actions, curiosity uses novelty-weighted exploration yield:

$$
Y_t^C(a_t) = \nu_{a_t}(t)\cdot Y_t^H(a_t)
$$

$$
\hat Y_t^C(a_t) = \nu_{a_t}(t)\cdot \hat Y_t^H(a_t)
$$

The novelty term is treated as a **pre-action contextual weight**, not
as a predicted quantity in v1.

Although novelty-derived features are included in the shared predictive
target, System C+W v1 does not interpret them as explicit predicted
novelty terms in the curiosity-yield equation. In v1,
$\nu_{a_t}(t)$ remains a pre-action contextual weight.

### 8.3 Non-Movement Curiosity Rule

For non-movement actions:

$$
Y_t^C(a_t) = -\kappa_{nonmove}^C \cdot d_C(t)
$$

$$
\hat Y_t^C(a_t) = -\kappa_{nonmove}^C \cdot d_C(t)
$$

where:

$$
\kappa_{nonmove}^C \ge 0
$$

This means non-movement actions cannot generate positive curiosity yield
in v1.

$\kappa_{nonmove}^C$ should be chosen small relative to typical
movement-based curiosity-yield magnitudes, unless strong suppression of
non-movement under curiosity is intended.

Interpretation:

- movement can produce curiosity-positive evidence through novelty-weighted exploration yield
- `CONSUME` and `STAY` receive no curiosity-positive outcome in v1
- their curiosity-side effect remains suppressive or neutral

---

## 9. Drive-Specific Predictive Error and Traces

Hunger-side signed errors:

$$
\varepsilon_{H,t}^+ = \max(Y_t^H - \hat Y_t^H, 0)
$$

$$
\varepsilon_{H,t}^- = \max(\hat Y_t^H - Y_t^H, 0)
$$

Curiosity-side signed errors:

$$
\varepsilon_{C,t}^+ = \max(Y_t^C - \hat Y_t^C, 0)
$$

$$
\varepsilon_{C,t}^- = \max(\hat Y_t^C - Y_t^C, 0)
$$

Trace states remain separate:

$$
z_t^H = (f_t^H, c_t^H), \qquad z_t^C = (f_t^C, c_t^C)
$$

with EMA updates:

$$
f_{t+1}^H = (1-\eta_f^H)f_t^H + \eta_f^H \varepsilon_{H,t}^-
$$

$$
c_{t+1}^H = (1-\eta_c^H)c_t^H + \eta_c^H \varepsilon_{H,t}^+
$$

$$
f_{t+1}^C = (1-\eta_f^C)f_t^C + \eta_f^C \varepsilon_{C,t}^-
$$

$$
c_{t+1}^C = (1-\eta_c^C)c_t^C + \eta_c^C \varepsilon_{C,t}^+
$$

---

## 10. Drive-Specific Modulation

System C+W computes separate predictive modulation factors:

$$
\mu_H(s_t,a) = \sigma_H(f_t^H(s_t,a), c_t^H(s_t,a))
$$

$$
\mu_C(s_t,a) = \sigma_C(f_t^C(s_t,a), c_t^C(s_t,a))
$$

Each drive has its own parameter set:

- positive sensitivity
- negative sensitivity
- lower and upper modulation bounds
- optional additive prediction bias parameters

The effective action-level projections are:

$$
\tilde \Pi_H(a,t) = d_H(t)\,\phi_H(a,u_t)\,\mu_H(s_t,a)
$$

$$
\tilde \Pi_C(a,t) = d_C(t)\,\phi_C(a,u_t,m_t,w_t)\,\mu_C(s_t,a)
$$

---

## 11. Arbitration and Policy

Predictive modulation is applied **before** drive arbitration.
Therefore the behavioral influence of prediction is still shaped by the
dynamic arbitration weights $w_H(t)$ and $w_C(t)$.

The intended layering is:

```text
raw drive projection
→ predictive modulation
→ drive arbitration
→ policy
```

The combined action score is:

$$
\Psi_{CW}(a,t) =
w_H(t)\,\tilde \Pi_H(a,t) + w_C(t)\,\tilde \Pi_C(a,t)
$$

Action selection is then:

$$
\pi(a\mid t) = \mathrm{Softmax}_\beta(\Psi_{CW}(a,t))
$$

with admissibility masking exactly as in earlier systems.

---

## 12. Interpretation

System C+W should be understood as:

- a **shared expectation model**
- with **separate predictive trust dynamics**
- acting on two different motivational channels

This means the agent may learn that the same local predictive context is:

- trustworthy for hunger-side value
- but unreliable for curiosity-side value

or vice versa.

That separation is the central conceptual difference between:

- one shared predictive memory
- and two separate drive-specific trace systems.
