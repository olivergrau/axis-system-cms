# System C+W Specification

## Predictive Dual-Drive Agent with Minimal World Model

**Status:** Draft  
**Based on:** `docs-internal/ideas/system-cw/draft.md`, `docs-internal/ideas/system-cw/detailed-draft.md`  
**Related systems:** `System A+W`, `System C`  
**Target role:** conceptual and mathematical system specification  

---

## 1. Purpose

This document specifies **System C+W** as a new AXIS system that unifies:

- the hunger drive of System A / A+W
- the curiosity drive of System A+W
- the minimal spatial world model of System A+W
- the prediction-based action modulation of System C

The central design goal is:

> to construct a dual-drive agent whose exploratory and exploitative action
> tendencies remain motivationally distinct, while both are filtered through a
> shared learned estimate of local action reliability.

System C+W is therefore intended to answer a more specific research question
than either neighboring system alone:

> What behavioral repertoire emerges when hunger and curiosity jointly shape
> action tendencies, but prediction learns which local context-action pairs are
> metabolically or epistemically trustworthy?

---

## 2. Scope

This specification defines:

- the conceptual system identity of `system_cw`
- the mathematical structure of its internal state
- the dual-drive decision model
- the predictive feature and context model
- the predictive update semantics
- the modulation and arbitration pipeline
- the main reduction properties and design constraints

This specification does **not** define:

- implementation modules or file layout
- exact Python types or class signatures
- visualization details
- CLI registration details
- test-plan decomposition

Those belong to a later engineering specification.

---

## 3. Design Commitments

System C+W inherits the core AXIS commitments from System A+W and System C.

### 3.1 Drives remain motivational sources

Prediction must not directly alter drive magnitudes.

If

$$
d_H(t), \quad d_C(t)
$$

are hunger and curiosity activations, then prediction may not redefine them as:

$$
d'_H(t)=d_H(t)+\Delta_{pred}, \qquad d'_C(t)=d_C(t)+\Delta_{pred}
$$

Prediction acts only on **action expression**, never on motivational need.

### 3.2 Prediction remains retrospective

Prediction error is computed only after:

- an action has been chosen
- the world has advanced
- the post-action observation has been obtained

System C+W therefore remains:

- non-planning
- non-simulative
- local
- mechanistically interpretable

### 3.3 The world model remains minimal

The world model stores only visit-count structure in an agent-relative frame.

It must not become:

- a planner
- a route cache
- a remembered map of resources
- a latent transition model

### 3.4 Shared experience, drive-specific interpretation

System C+W uses:

- one shared predictive memory
- one drive-specific confidence/frustration trace pair for hunger
- one drive-specific confidence/frustration trace pair for curiosity

but allows:

- drive-specific modulation parameters for hunger
- drive-specific modulation parameters for curiosity

This preserves a single experiential substrate at the predictive-memory level
while allowing exploitative and exploratory behavior to accumulate and express
different local trust histories.

---

## 4. Formal Definition

System C+W is defined as the 11-tuple:

$$
A^{(CW)} =
(\mathcal{X}, \mathcal{U}, \mathcal{M}, \mathcal{W}, \mathcal{Q}, \mathcal{Z}, \mathcal{A}, \mathcal{D}, F, \Gamma, \pi)
$$

where:

- $\mathcal{X}$ is the internal state space
- $\mathcal{U}$ is the local observation space
- $\mathcal{M}$ is the episodic observation-memory space
- $\mathcal{W}$ is the minimal world-model space
- $\mathcal{Q}$ is the predictive memory space
- $\mathcal{Z}$ is the drive-specific prediction-derived trace space
- $\mathcal{A}$ is the action space
- $\mathcal{D} = \{D_H, D_C\}$ is the drive set
- $F$ is the transition function
- $\Gamma$ is the action-expression architecture
- $\pi$ is the policy

The concrete action set remains the standard AXIS action set:

$$
\mathcal{A} = \{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}, \text{CONSUME}, \text{STAY}\}
$$

---

## 5. Internal State

The internal state at time $t$ is:

$$
x_t = (e_t, m_t, \hat p_t, w_t, q_t, z_t^H, z_t^C)
$$

where:

- $e_t \in [0, E_{\max}]$ is current energy
- $m_t$ is the episodic observation buffer
- $\hat p_t \in \mathbb{Z}^2$ is the relative position estimate
- $w_t : \mathbb{Z}^2 \to \mathbb{N}_0$ is the visit-count map
- $q_t : \mathcal{S} \times \mathcal{A} \to \mathcal{Y}$ is predictive memory
- $z_t^H = (f_t^H, c_t^H)$ is the hunger-specific predictive trace state
- $z_t^C = (f_t^C, c_t^C)$ is the curiosity-specific predictive trace state

with

$$
f_t^H, c_t^H, f_t^C, c_t^C
: \mathcal{S} \times \mathcal{A} \to \mathbb{R}_{\ge 0}
$$

interpreted as:

- $f_t^H(s,a)$: hunger-specific frustration / unreliability trace
- $c_t^H(s,a)$: hunger-specific confidence / positive-opportunity trace
- $f_t^C(s,a)$: curiosity-specific frustration / unreliability trace
- $c_t^C(s,a)$: curiosity-specific confidence / positive-opportunity trace

### 5.1 Inherited world-model dynamics

System C+W inherits the A+W dead-reckoning and visit-count update:

$$
\hat p_{t+1} = \hat p_t + \mu_t \cdot \Delta(a_t)
$$

where $\mu_t \in \{0,1\}$ indicates whether movement occurred.

Visit counts update as:

$$
w_{t+1}(\hat p) =
\begin{cases}
w_t(\hat p)+1 & \text{if } \hat p = \hat p_{t+1} \\
w_t(\hat p) & \text{otherwise}
\end{cases}
$$

---

## 6. Observation, Novelty, and Drives

Let the local observation at time $t$ be:

$$
u_t = (r_c, r_u, r_d, r_l, r_r, \ldots)
$$

where the resource-valued components are:

- $r_c(t)$: current-cell resource
- $r_{dir}(t)$: neighboring resource value in direction $dir$

The resource-valued local structure is sufficient for the definition of the raw
drive projections and the baseline energy-regulation dynamics below.

However, System C+W extends the predictive layer with additional derived
features (notably novelty signals) that depend on episodic memory and the
minimal world model. These features are introduced explicitly in Section 8.

### 6.1 Hunger drive

System C+W inherits the System A / A+W hunger activation:

$$
d_H(t) = \mathrm{clamp}\!\left(1 - \frac{e_t}{E_{\max}},\, 0,\, 1\right)
$$

### 6.2 Curiosity drive

System C+W inherits the A+W curiosity activation:

$$
d_C(t) = \mu_C \cdot (1 - \bar\nu_t)
$$

where:

- $\mu_C \in [0,1]$ is base curiosity
- $\bar\nu_t$ is novelty saturation over recent experience

### 6.3 Spatial novelty

For movement directions:

$$
\nu^{spatial}_{dir}(t) = \frac{1}{1 + w_t(\hat p_t + \Delta(dir))}
$$

### 6.4 Sensory novelty

Let $\bar r_{dir}(t)$ be the mean remembered resource intensity in direction
$dir$ across the observation buffer. Then:

$$
\nu^{sensory}_{dir}(t) = |r_{dir}(t) - \bar r_{dir}(t)|
$$

### 6.5 Composite novelty

System C+W inherits the A+W novelty blend:

$$
\nu_{dir}(t) = \alpha \cdot \nu^{spatial}_{dir}(t)
+ (1-\alpha) \cdot \nu^{sensory}_{dir}(t)
$$

with $\alpha \in [0,1]$.

Define the local mean directional novelty:

$$
\bar\nu_{local}(t)
=
\frac{
\nu_u(t)+\nu_d(t)+\nu_l(t)+\nu_r(t)
}{4}
$$

---

## 7. Raw Action Expressions

System C+W computes two separate raw drive projections before prediction.

### 7.1 Hunger projection

Let $G_H(a,t)$ denote the hunger-side raw action expression.

For movement directions:

$$
G_H(dir,t) = d_H(t)\cdot r_{dir}(t)
$$

For consumption:

$$
G_H(\text{CONSUME},t) = d_H(t)\cdot w_{consume}\cdot r_c(t)
$$

For idling:

$$
G_H(\text{STAY},t) = -d_H(t)\cdot \lambda_{stay}
$$

### 7.2 Curiosity projection

Let $G_C(a,t)$ denote the curiosity-side raw action expression.

For movement directions:

$$
G_C(dir,t) = d_C(t)\cdot \nu_{dir}(t)
$$

For non-exploratory actions:

$$
G_C(\text{CONSUME},t) = -d_C(t)\cdot \lambda_{explore}
$$

$$
G_C(\text{STAY},t) = -d_C(t)\cdot \lambda_{explore}
$$

These are exactly the motivationally distinct signals that prediction will
later modulate.

---

## 8. Predictive Feature Space and Context

System C+W extends the System C predictive substrate from purely sensory
resource features to a compact joint resource-novelty feature vector.

### 8.1 Feature vector

The first-wave predictive feature vector is:

$$
y_t^{CW}
=
\Big(
r_c,
r_u,
r_d,
r_l,
r_r,
\nu_u,
\nu_d,
\nu_l,
\nu_r,
\bar\nu_{local}
\Big)
$$

The predictive feature space $\mathcal{Y}$ is defined as the codomain of
$y_t^{CW}$.

This vector is:

- local
- bounded
- agent-relative
- world-model-informed
- still non-planning

The predictive target contains both:

- exogenous resource features
- endogenous novelty-derived features

The novelty-derived features depend on the agent's own episodic memory and
visit-count world model. Predictive memory is therefore not a pure external
world-transition model; it predicts expected next features in the closed-loop
agent-environment interaction.

Although novelty-derived features are included in the shared predictive target,
System C+W v1 does not interpret them as explicit predicted novelty terms in
the curiosity-yield equation. In v1, $\nu_{a_t}(t)$ remains a pre-action
contextual weight.

### 8.2 Feature-space constraint

The predictive feature map must not include:

- absolute coordinates
- the full visit-count map
- explicit path history
- remembered resource locations
- multi-step route estimates

### 8.3 Context encoding

Prediction operates over a finite discrete context set:

$$
s_t = C(y_t^{CW}) \in \mathcal{S}
$$

The encoder $C$ must be:

- low-dimensional
- deterministic
- local

The encoder should aggressively compress the feature space into a small,
well-covered discrete set; it must not create a high-cardinality
pseudo-state space.

This specification does not fix one exact encoding scheme, but it does require
that prediction be keyed by compact local context-action pairs:

$$
(s_t, a_t)
$$

not by a global world state.

---

## 9. Predictive Memory

Shared predictive memory stores expected next predictive features:

$$
q_t(s,a) = \hat y_{t+1}^{(s,a)}
$$

where $\hat y_{t+1}^{(s,a)} \in \mathcal{Y}$ is the expected next
resource-novelty feature vector under context $s$ and action $a$.

After action $a_t$ in context $s_t$, memory updates by exponential averaging:

$$
q_{t+1}(s_t,a_t)
=
(1-\eta_q)\,q_t(s_t,a_t)
+ \eta_q\,y_{t+1}^{CW}
$$

with all other context-action pairs unchanged.

The learning rate $\eta_q$ satisfies:

$$
0 < \eta_q \le 1
$$

---

## 10. Predictive Outcome Semantics

System C+W uses one shared predictive memory, but it derives two drive-relevant
outcome semantics from it.

### 10.1 Local resource-value functional

Define a local resource-value functional:

$$
R_{local}(u_t)
=
\omega_c\,r_c(t)
+ \omega_n \cdot
\frac{r_u(t)+r_d(t)+r_l(t)+r_r(t)}{4}
$$

with:

- $\omega_c \ge 0$
- $\omega_n \ge 0$

and typically normalized so the range remains bounded.

For a predicted next feature vector $\hat y_{t+1}^{(s,a)}$, the corresponding
predicted local resource value is:

$$
\hat R_{local}(t+1 \mid s,a)
=
\omega_c\,\hat r_c
+ \omega_n \cdot
\frac{\hat r_u+\hat r_d+\hat r_l+\hat r_r}{4}
$$

### 10.2 Hunger-side opportunity outcome

Define the actual hunger-side local opportunity shift:

$$
Y_t^H
=
R_{local}(u_{t+1}) - R_{local}(u_t)
$$

and the predicted one:

$$
\hat Y_t^H
=
\hat R_{local}(t+1 \mid s_t,a_t) - R_{local}(u_t)
$$

The hunger-side signed predictive deviations are:

$$
\varepsilon_{H,t}^+ = \max(Y_t^H - \hat Y_t^H, 0)
$$

$$
\varepsilon_{H,t}^- = \max(\hat Y_t^H - Y_t^H, 0)
$$

Interpretation:

- $\varepsilon_H^+$: the action yielded more local metabolic opportunity than expected
- $\varepsilon_H^-$: the action under-delivered metabolically

### 10.3 Curiosity-side novelty-weighted yield

For movement actions, define the actual curiosity-side yield:

$$
Y_t^C
=
\nu_{a_t}(t)\cdot
\Big(
R_{local}(u_{t+1}) - R_{local}(u_t)
\Big)
$$

and its predicted counterpart:

$$
\hat Y_t^C
=
\nu_{a_t}(t)\cdot
\Big(
\hat R_{local}(t+1 \mid s_t,a_t) - R_{local}(u_t)
\Big)
$$

The novelty term $\nu_{a_t}(t)$ is treated as a pre-action contextual weight,
not as a predicted quantity in v1.

For non-movement actions:

$$
Y_t^C(a_t) = -\kappa_{nonmove}^C \cdot d_C(t)
$$

and

$$
\hat Y_t^C(a_t) = -\kappa_{nonmove}^C \cdot d_C(t)
$$

where

$$
\kappa_{nonmove}^C \ge 0
$$

$\kappa_{nonmove}^C$ should be chosen small relative to typical
movement-based curiosity-yield magnitudes, unless strong suppression of
non-movement under curiosity is intended.

The curiosity-side signed deviations are:

$$
\varepsilon_{C,t}^+ = \max(Y_t^C - \hat Y_t^C, 0)
$$

$$
\varepsilon_{C,t}^- = \max(\hat Y_t^C - Y_t^C, 0)
$$

Interpretation:

- novel move + unexpectedly richer local environment $\Rightarrow$ curiosity-positive evidence
- novel move + unexpectedly poorer local environment $\Rightarrow$ curiosity-negative evidence
- movement can produce curiosity-positive evidence through novelty-weighted exploration yield
- `CONSUME` and `STAY` receive no curiosity-positive outcome in v1
- their curiosity-side effect remains suppressive or neutral

### 10.4 Drive-specific evidence

System C+W keeps shared predictive memory but separate drive-level predictive
evidence.

The hunger trace pair is updated from:

$$
\varepsilon_{H,t}^+, \qquad \varepsilon_{H,t}^-
$$

and the curiosity trace pair is updated from:

$$
\varepsilon_{C,t}^+, \qquad \varepsilon_{C,t}^-
$$

This gives System C+W:

- one shared learned expectation model over local contexts
- but two distinct local trust histories over that shared model

---

## 11. Drive-Specific Trace Update

For the active context-action pair $(s_t,a_t)$, the hunger traces update as:

$$
f_{t+1}^H(s_t,a_t)
=
(1-\eta_f^H)\,f_t^H(s_t,a_t)
+ \eta_f^H\,\varepsilon_{H,t}^-
$$

$$
c_{t+1}^H(s_t,a_t)
=
(1-\eta_c^H)\,c_t^H(s_t,a_t)
+ \eta_c^H\,\varepsilon_{H,t}^+
$$

The curiosity traces update as:

$$
f_{t+1}^C(s_t,a_t)
=
(1-\eta_f^C)\,f_t^C(s_t,a_t)
+ \eta_f^C\,\varepsilon_{C,t}^-
$$

$$
c_{t+1}^C(s_t,a_t)
=
(1-\eta_c^C)\,c_t^C(s_t,a_t)
+ \eta_c^C\,\varepsilon_{C,t}^+
$$

where:

- $\eta_f^H, \eta_c^H \in (0,1]$ are hunger trace learning rates
- $\eta_f^C, \eta_c^C \in (0,1]$ are curiosity trace learning rates

All other trace entries remain unchanged.

Thus:

- hunger frustration/confidence accumulates from metabolic under- or over-delivery
- curiosity frustration/confidence accumulates from exploratory under- or over-delivery

---

## 12. Drive-Specific Predictive Modulation

The drive-specific predictive traces are interpreted separately by hunger and curiosity.

For each drive $D \in \{H, C\}$ define:

$$
\sigma_D(a,t)
=
\lambda_+^D \cdot c_t^D(s_t,a)
- \lambda_-^D \cdot f_t^D(s_t,a)
$$

with drive-specific positive and negative sensitivities:

$$
\lambda_+^D \ge 0, \qquad \lambda_-^D \ge 0
$$

### 12.1 Multiplicative mode

The multiplicative reliability factor is:

$$
\tilde\mu_D(a,t) = \exp(\sigma_D(a,t))
$$

$$
\mu_D(a,t) = \mathrm{clip}\!\big(\tilde\mu_D(a,t), \mu_{min}^D, \mu_{max}^D\big)
$$

with

$$
0 < \mu_{min}^D \le 1 \le \mu_{max}^D
$$

For raw contribution $G_D(a,t)$, multiplicative modulation is:

$$
M_D^{mult}(a,t)
=
\begin{cases}
G_D(a,t)\cdot \mu_D(a,t) & \text{if } G_D(a,t)\ge 0 \\
G_D(a,t)\,/\,\mu_D(a,t) & \text{if } G_D(a,t)<0
\end{cases}
$$

This preserves the sign of already negative penalties.

### 12.2 Additive mode

Define a bounded signed bias:

$$
\delta_D(a,t)
=
\mathrm{clip}\!\big(\tanh(\sigma_D(a,t)), -\beta_{clip}^D, \beta_{clip}^D\big)
$$

$$
b_D(a,t) = \lambda_{pred}^D \cdot \delta_D(a,t)
$$

The additive form is:

$$
M_D^{add}(a,t) = G_D(a,t) + b_D(a,t)
$$

### 12.3 Hybrid mode

The hybrid form combines both:

$$
M_D^{hyb}(a,t) = M_D^{mult}(a,t) + b_D(a,t)
$$

### 12.4 Mode selection

For each drive, the final prediction-shaped action expression is one of:

$$
\tilde G_D(a,t) \in
\left\{
M_D^{mult}(a,t),
M_D^{add}(a,t),
M_D^{hyb}(a,t)
\right\}
$$

This allows hunger and curiosity to respond differently to shared predictive
memory without splitting the predictive substrate itself.

---

## 13. Drive Arbitration and Policy

System C+W inherits A+W’s Maslow-like arbitration weights:

$$
w_H(t) = w_H^{base} + (1-w_H^{base})\cdot d_H(t)^\gamma
$$

$$
w_C(t) = w_C^{base}\cdot (1-d_H(t))^\gamma
$$

where:

- $w_H^{base} > 0$
- $w_C^{base} \ge 0$
- $\gamma > 0$

The final action score is:

$$
\psi_t(a) = w_H(t)\cdot \tilde G_H(a,t) + w_C(t)\cdot \tilde G_C(a,t)
$$

Predictive modulation is applied before drive arbitration. The effective
behavioral influence of prediction is therefore still shaped by the dynamic
arbitration weights $w_H(t)$ and $w_C(t)$.

The intended layering is:

```text
raw drive projection
-> predictive modulation
-> drive arbitration
-> policy
```

The policy $\pi$ then acts on the score vector $\psi_t$ exactly as in the
existing AXIS softmax-policy layer.

This preserves the intended interpretation:

- hunger says what matters metabolically
- curiosity says what matters epistemically
- prediction says which local actions deserve trust
- arbitration decides how the two drives trade off

---

## 14. Transition Semantics

At each timestep, System C+W follows this conceptual loop:

1. sense the local world and form $u_t$
2. compute hunger activation $d_H(t)$
3. compute novelty signals and curiosity activation $d_C(t)$
4. build predictive features $y_t^{CW}$ and context $s_t$
5. compute raw hunger and curiosity action expressions
6. apply drive-specific predictive modulation to both projections
7. arbitrate the modulated projections into $\psi_t(a)$
8. sample or choose action $a_t$ through policy $\pi$
9. apply the action in the world and receive outcome / next observation
10. update energy, observation memory, relative position, and visit map
11. compute $y_{t+1}^{CW}$
12. compute hunger-side and curiosity-side predictive outcomes
13. form drive-specific positive/negative evidence
14. update hunger and curiosity trace pairs separately
15. update predictive memory $q_t \to q_{t+1}$

This sequence is crucial:

- prediction influences choice before action
- prediction learns only after action

---

## 15. Reduction Properties

### 15.1 Exact reduction to System A+W

If predictive influence is neutralized for both drives, then System C+W reduces
exactly to the A+W dual-drive system.

Sufficient conditions are:

$$
\lambda_+^H = \lambda_-^H = \lambda_{pred}^H = 0
$$

$$
\lambda_+^C = \lambda_-^C = \lambda_{pred}^C = 0
$$

Under these conditions:

$$
\mu_H(a,t)=\mu_C(a,t)=1, \qquad b_H(a,t)=b_C(a,t)=0
$$

and therefore:

$$
\tilde G_H(a,t)=G_H(a,t), \qquad \tilde G_C(a,t)=G_C(a,t)
$$

which yields the original A+W score:

$$
\psi_t(a)=w_H(t)G_H(a,t)+w_C(t)G_C(a,t)
$$

### 15.2 Constructive reduction toward System C

System C+W can be collapsed toward a System C-like regime if:

- curiosity is disabled: $\mu_C = 0$
- curiosity arbitration is neutralized: $w_C^{base}=0$
- curiosity-specific evidence and trace updates are disabled or ignored
- novelty-derived predictive features are masked or held constant
- the predictive context is reduced to resource-valued local features

The final three conditions matter because the default C+W predictive context
includes novelty structure and the default C+W learning loop includes
curiosity-side predictive semantics. Without neutralizing curiosity-side
learning and collapsing the predictive context back to resource-valued local
structure, the default C+W parameterization does not guarantee an exact
reduction to System C.

This is a constructive approximation toward a System C-like regime, not the
primary exact reduction guarantee of the v1 design.

This is acceptable: exact reduction to A+W is the primary extension guarantee
for the v1 design.

---

## 16. Expected Behavioral Regimes

System C+W should exhibit at least four interpretable regimes.

### 16.1 Sated exploratory confidence

- hunger low
- curiosity high
- confidence reinforces exploratory directions that repeatedly open richer local neighborhoods

### 16.2 Sated exploratory frustration

- hunger low
- curiosity high
- novelty remains attractive
- but repeated disappointment suppresses futile exploratory moves

### 16.3 Hungry exploitative confidence

- hunger high
- curiosity strongly gated
- prediction reinforces locally reliable foraging actions

### 16.4 Hungry exploitative frustration

- hunger high
- prediction suppresses repeatedly unproductive local food-chasing patterns

The important qualitative distinction from A+W is:

> novelty remains motivationally real, but not every novel action remains equally trusted.

The important qualitative distinction from C is:

> prediction no longer shapes only metabolic action expression; it also shapes exploration.

---

## 17. Summary

System C+W is a coherent synthesis of A+W and C under one strict rule:

> shared prediction, separate drives, action-level modulation only.

Its defining structure is:

- dual motivation
- minimal world model
- compact local predictive context
- retrospective shared predictive learning
- drive-specific modulation
- Maslow-like arbitration after modulation

This makes System C+W the first AXIS system in which:

- curiosity is a genuine motivational source
- prediction filters both exploitation and exploration
- and learned local trust can diverge from raw local novelty.
