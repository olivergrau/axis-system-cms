# System C: A Predictive Single-Drive Agent with Action-Level Modulation

## Metadata
- Project: AXIS -- Complex Mechanistic Systems Experiment
- Author: Oliver Grau
- Type: Formal Research Note
- Status: Draft v1.0
- Scope: Hunger-driven agent with local predictive memory, signed prediction error, and bounded action-level modulation
- Extends: System A Baseline
- Constraints: No world model, no planning, no counterfactual rollout, no meta-cognition, no phenomenology

---

## 1. Objective

This document defines **System C** as a predictive extension of the System A baseline agent.

System C preserves the baseline AXIS commitments:

- local sensing,
- explicit internal state,
- drive-based action selection,
- framework-owned world,
- deterministic internal update rules,
- and interpretable step-level behavior.

It extends the baseline with:

- a **shared predictive feature space**,
- a **predictive memory** over local context-action pairs,
- **retrospective signed prediction error**,
- two bounded local predictive traces:
  - disappointment / unreliability
  - positive surprise / opportunity
- and **action-level predictive modulation** applied before arbitration.

The central research question is:

> What behavior emerges when a mechanistic hunger-driven agent learns not only what is currently locally attractive, but also which actions in similar local contexts have historically under-delivered or over-delivered?

---

## 2. Relationship to System A

System C is a strict architectural extension of System A.

It preserves:

- the local observation model,
- the action space,
- the homeostatic hunger definition,
- the policy form,
- the energy dynamics,
- the observation buffer,
- and the baseline mechanistic worldview.

It adds:

- a predictive memory state,
- a prediction-derived trace state,
- a local predictive feature map,
- signed prediction error,
- and predictive action modulation.

### 2.1 Key Design Decision

Prediction does **not** modify drive magnitude directly.

System C rejects formulations of the form:

$$
d_H(t) = h_t + \lambda \varepsilon_t
$$

Instead, prediction acts on the **expression of the drive over actions**:

$$
\Pi_H(a,t) = d_H(t)\,\phi_H(a,u_t)\,\mu_H(s_t,a)
$$

This preserves the core AXIS principle:

> Drives remain scalar motivational sources. Prediction reshapes action expression, not motivational magnitude.

### 2.2 Reduction to System A

If predictive modulation is disabled:

$$
\mu_H(s,a) = 1
$$

for all context-action pairs, then System C reduces to the baseline System A hunger projection.

---

## 3. Design Principles

### 3.1 Pure Mechanism

All predictive behavior must be explainable through:

- local observations,
- explicit internal state variables,
- deterministic update rules,
- bounded memory structures,
- and drive-based action selection.

### 3.2 Shared Predictive Substrate

The predictive system is defined over one **shared predictive feature map** per system:

$$
y_t = \Omega(u_t)
$$

Prediction is not drive-specific at the feature extraction level.

Drive-specific semantics arise only later through:

- error aggregation,
- trace interpretation,
- and action modulation.

### 3.3 Retrospective Prediction

System C computes prediction error only after the chosen action has been executed and the next observation has been received.

There is no:

- action simulation,
- parallel evaluation of hypothetical outcomes,
- or planning rollout.

### 3.4 Signed Predictive Learning

System C uses both directions of prediction error:

- **negative surprise**: expectation exceeded reality
- **positive surprise**: reality exceeded expectation

This produces:

- damping of unreliable actions
- reinforcement of unexpectedly beneficial actions

### 3.5 Bounded Predictive Influence

Predictive modulation is explicitly bounded:

$$
\mu_{\min} \le \mu_H(s,a) \le \mu_{\max}
$$

Prediction may bias behavior strongly, but it may not dominate the entire system without limit.

### 3.6 No Hidden World Model

Predictive memory stores local context-conditioned expectations in feature space.

It does **not** store:

- global coordinates
- map structure
- explicit future trajectories
- or an internal simulation of the environment

---

## 4. Formal Definition

System C is defined as the 10-tuple:

$$
A^{(C)} = (\mathcal{X}, \mathcal{U}, \mathcal{M}, \mathcal{Q}, \mathcal{Z}, \mathcal{A}, \mathcal{D}, F, \Gamma, \pi)
$$

where:

- $\mathcal{X}$ is the internal state space
- $\mathcal{U}$ is the sensory input space
- $\mathcal{M}$ is the episodic observation memory space
- $\mathcal{Q}$ is the predictive memory space
- $\mathcal{Z}$ is the prediction-derived trace space
- $\mathcal{A}$ is the action space
- $\mathcal{D}$ is the drive space
- $F$ is the state transition system
- $\Gamma$ is the action modulation architecture
- $\pi$ is the policy

For the concrete System C defined here:

- $\mathcal{D} = \{D_H\}$ contains one drive only: hunger

---

## 5. Internal State

The internal state at time $t$ is:

$$
x_t = (e_t, q_t, z_t)
$$

where:

- $e_t \in [0, E_{\max}]$ is the current energy level
- $q_t \in \mathcal{Q}$ is the predictive memory state
- $z_t \in \mathcal{Z}$ is the prediction-derived trace state

The physical world position of the agent is **not** part of the internal state.

As in System A, the world maintains the agent’s physical position externally.

### 5.1 Observation Buffer

System C preserves the baseline observation buffer:

$$
m_{t+1} = M(m_t, u_{t+1})
$$

The observation buffer remains:

- an episodic sensory trace
- separate from predictive memory
- behaviorally secondary in this first System C instance

### 5.2 Predictive Memory

Predictive memory stores expected next predictive features conditioned on current predictive context and action.

Define:

$$
q_t : \mathcal{S} \times \mathcal{A} \rightarrow \mathcal{Y}
$$

with:

- $\mathcal{S}$ a finite context set
- $\mathcal{A}$ the action set
- $\mathcal{Y}$ the bounded predictive feature space

Interpretation:

$$
q_t(s,a) = \hat y_t^{(s,a)}
$$

is the expected next predictive feature vector for action $a$ in context $s$.

### 5.3 Predictive Trace State

The prediction-derived trace state is:

$$
z_t = (f_t, c_t)
$$

where:

$$
f_t, c_t : \mathcal{S} \times \mathcal{A} \rightarrow \mathbb{R}_{\ge 0}
$$

and:

- $f_t(s,a)$ is the local disappointment / unreliability trace
- $c_t(s,a)$ is the local positive-surprise / opportunity trace

---

## 6. Observation and Predictive Feature Space

The local observation is inherited from System A:

$$
u_t = S(s_t^{world})
$$

System C introduces a predictive feature map:

$$
\Omega : \mathcal{U} \rightarrow \mathcal{Y}
$$

and defines:

$$
y_t = \Omega(u_t)
$$

### 6.1 Constraints on the Feature Map

The predictive feature map must satisfy:

- locality
- determinism
- boundedness
- system-level uniformity

Formally:

- locality: $\Omega(u_t)$ depends only on the current local observation
- determinism: equal observations imply equal predictive features
- boundedness: $\mathcal{Y} \subset \mathbb{R}^k$ is bounded for finite $k$
- uniformity: one fixed $\Omega$ is used across the entire system

### 6.2 Concrete Hunger-Centered Instantiation

For the first concrete System C instance, prediction is defined over local resource structure only:

$$
y_t = r_t = (r_c, r_{up}, r_{down}, r_{left}, r_{right}) \in [0,1]^5
$$

This is a **system instance choice**, not a general property of predictive systems.

---

## 7. Context Encoding

System C discretizes predictive feature vectors into a finite local context set:

$$
C : \mathcal{Y} \rightarrow \mathcal{S}
$$

with:

- determinism
- finite image
- locality inheritance from $\Omega$

The predictive context at time $t$ is:

$$
s_t = C(y_t)
$$

The role of $C$ is local discretization only.

It is not a latent world model.

---

## 8. Action Space

System C inherits the System A action space:

$$
\mathcal{A} = \{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}, \text{CONSUME}, \text{STAY}\}
$$

Interpretation:

- movement actions express directional approach behavior
- `CONSUME` attempts local resource extraction at the current cell
- `STAY` expresses non-movement

---

## 9. Drive System

System C remains a single-drive system in its first formal definition.

### 9.1 Hunger Drive Activation

The hunger activation is unchanged from System A:

$$
h_t = 1 - \frac{e_t}{E_{\max}}
$$

$$
d_H(t) = h_t
$$

Prediction does not alter $d_H(t)$ directly.

### 9.2 General AXIS Contribution Form

The generic AXIS action score structure is:

$$
\psi(a) = \sum_{i \in \mathcal{D}} \alpha_i(t)\,\Pi_i(a,t)
$$

with:

- $\alpha_i(t) \ge 0$: arbitration weight
- $\Pi_i(a,t)$: action-level contribution of drive $i$

For standard drive systems:

$$
\Pi_i(a,t) = d_i(t)\,\phi_i(a,u_t)
$$

### 9.3 Predictive Hunger Contribution

System C modifies the hunger contribution to:

$$
\Pi_H^{C}(a,t) = d_H(t)\,\phi_H(a,u_t)\,\mu_H(s_t,a)
$$

For the single-drive case:

$$
\alpha_H(t) = 1
$$

and therefore:

$$
\psi_C(a) = d_H(t)\,\phi_H(a,u_t)\,\mu_H(s_t,a)
$$

### 9.4 Hunger Projection

The baseline projection $\phi_H(a,u_t)$ is inherited from System A:

- movement actions couple to directional local resource signals
- `CONSUME` couples to current-cell resource
- `STAY` is hunger-suppressed

Concretely:

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

where:

- $w_{consume} \ge 0$ is the consume amplification factor
- $\lambda_{stay} \ge 0$ is the hunger-based stay suppression coefficient

---

## 10. Prediction and Prediction Error

### 10.1 Prediction Retrieval

Given the current predictive context $s_t = C(y_t)$ and action $a_t$, the retrieved prediction is:

$$
\hat y_{t+1} = q_t(s_t,a_t)
$$

Equivalently:

$$
P(q_t,y_t,a_t) = q_t(C(y_t),a_t)
$$

### 10.2 Signed Prediction Error

After the action is executed and the next predictive feature vector is observed:

$$
\delta_t = y_{t+1} - \hat y_{t+1}
$$

System C uses the signed decomposition:

$$
\delta_t^{+} = \max(y_{t+1} - \hat y_{t+1}, 0)
$$

$$
\delta_t^{-} = \max(\hat y_{t+1} - y_{t+1}, 0)
$$

Interpretation:

- $\delta_t^{-}$: disappointed expectation
- $\delta_t^{+}$: positive surprise

### 10.3 Aggregation into Scalar Predictive Signals

System C aggregates vector-valued prediction error into scalar predictive traces:

$$
\varepsilon_t^{-} = G^{-}(\delta_t^{-})
$$

$$
\varepsilon_t^{+} = G^{+}(\delta_t^{+})
$$

where:

$$
G^{-}, G^{+} : \mathcal{Y} \rightarrow \mathbb{R}_{\ge 0}
$$

must be deterministic, non-negative, and bounded on bounded inputs.

### 10.4 Concrete Hunger Aggregation

For the first hunger-centered System C instance:

$$
\varepsilon_t^{-} =
\sum_{j \in \{c,up,down,left,right\}} w_j^{-}\,\delta_{t,j}^{-}
$$

$$
\varepsilon_t^{+} =
\sum_{j \in \{c,up,down,left,right\}} w_j^{+}\,\delta_{t,j}^{+}
$$

with:

$$
w_j^{-} \ge 0, \quad w_j^{+} \ge 0
$$

$$
\sum_j w_j^{-} = 1, \qquad \sum_j w_j^{+} = 1
$$

and:

$$
w_c^{\pm} \ge w_{up}^{\pm}, w_{down}^{\pm}, w_{left}^{\pm}, w_{right}^{\pm}
$$

These are fixed system parameters.

---

## 11. Predictive Trace Dynamics

### 11.1 Negative Trace

The disappointment trace is updated by:

$$
f_{t+1}(s_t,a_t) = (1-\eta_f)\,f_t(s_t,a_t) + \eta_f\,\varepsilon_t^{-}
$$

with:

$$
\eta_f \in (0,1]
$$

### 11.2 Positive Trace

The positive-surprise trace is updated by:

$$
c_{t+1}(s_t,a_t) = (1-\eta_c)\,c_t(s_t,a_t) + \eta_c\,\varepsilon_t^{+}
$$

with:

$$
\eta_c \in (0,1]
$$

### 11.3 Unvisited Context-Action Pairs

For all $(s,a) \neq (s_t,a_t)$:

$$
f_{t+1}(s,a) = f_t(s,a)
$$

$$
c_{t+1}(s,a) = c_t(s,a)
$$

---

## 12. Predictive Modulation

### 12.1 Exponential Core

System C defines a predictive modulation core:

$$
\tilde{\mu}_H(s,a) = \exp(\lambda_{+}\,c_t(s,a) - \lambda_{-}\,f_t(s,a))
$$

with:

- $\lambda_{+} \ge 0$
- $\lambda_{-} \ge 0$

### 12.2 Clipped Final Modulation

The final modulation factor is:

$$
\mu_H(s,a) = \mathrm{clip}(\tilde{\mu}_H(s,a), \mu_{\min}, \mu_{\max})
$$

with:

$$
0 < \mu_{\min} \le 1 \le \mu_{\max} < \infty
$$

Interpretation:

- $\mu_{\min}$: maximal allowed suppression floor
- $\mu_{\max}$: maximal allowed reinforcement ceiling

Thus:

- unreliable actions are damped
- over-delivering actions are reinforced
- predictive influence remains bounded

### 12.3 Integration Point

Prediction-sensitive modulation is applied **before arbitration** at the per-drive projection level.

In the single-drive case this means:

$$
\psi_C(a) = d_H(t)\,\phi_H(a,u_t)\,\mu_H(s_t,a)
$$

not:

$$
\psi_C(a) = \mu_H(s_t,a)\,\psi_{\text{combined}}(a)
$$

This ordering is part of the definition of System C.

---

## 13. Predictive Memory Update

For the selected context-action pair:

$$
q_{t+1}(s_t,a_t) = (1-\eta_q)\,q_t(s_t,a_t) + \eta_q\,y_{t+1}
$$

with:

$$
\eta_q \in (0,1]
$$

For all other pairs:

$$
q_{t+1}(s,a) = q_t(s,a)
$$

This is a convex update rule and preserves boundedness of predictive expectations whenever $y_{t+1} \in \mathcal{Y}$.

---

## 14. Policy

System C preserves the softmax policy structure:

$$
P(a \mid x_t,u_t,m_t,q_t,z_t) =
\frac{\exp(\beta \psi_C(a))}
{\sum_{a' \in \mathcal{A}} \exp(\beta \psi_C(a'))}
$$

where:

- $\beta > 0$ is inverse temperature

Inadmissibility constraints, if present in the concrete implementation, are handled in the same way as in System A.

---

## 15. Transition and Update Cycle

System C follows a fully retrospective and local update cycle.

### 15.1 Perception

$$
u_t = S(s_t^{world})
$$

$$
y_t = \Omega(u_t)
$$

### 15.2 Drive Evaluation

$$
d_H(t) = 1 - \frac{e_t}{E_{\max}}
$$

### 15.3 Context Encoding

$$
s_t = C(y_t)
$$

### 15.4 Action Scoring

$$
\psi_C(a) = d_H(t)\,\phi_H(a,u_t)\,\mu_H(s_t,a)
$$

### 15.5 Action Selection

$$
a_t \sim \pi(\psi_C)
$$

### 15.6 World Transition

$$
s_{t+1}^{world} = F_{world}(s_t^{world}, a_t)
$$

### 15.7 New Observation

$$
u_{t+1} = S(s_{t+1}^{world})
$$

$$
y_{t+1} = \Omega(u_{t+1})
$$

### 15.8 Prediction Retrieval

$$
\hat y_{t+1} = q_t(s_t,a_t)
$$

### 15.9 Prediction Error

$$
\delta_t^{+} = \max(y_{t+1} - \hat y_{t+1}, 0)
$$

$$
\delta_t^{-} = \max(\hat y_{t+1} - y_{t+1}, 0)
$$

$$
\varepsilon_t^{+} = G^{+}(\delta_t^{+}), \qquad
\varepsilon_t^{-} = G^{-}(\delta_t^{-})
$$

### 15.10 Predictive Trace Update

$$
f_{t+1}(s_t,a_t) = (1-\eta_f)\,f_t(s_t,a_t) + \eta_f\,\varepsilon_t^{-}
$$

$$
c_{t+1}(s_t,a_t) = (1-\eta_c)\,c_t(s_t,a_t) + \eta_c\,\varepsilon_t^{+}
$$

### 15.11 Predictive Memory Update

$$
q_{t+1}(s_t,a_t) = (1-\eta_q)\,q_t(s_t,a_t) + \eta_q\,y_{t+1}
$$

### 15.12 Energy Update

Energy remains baseline-consistent:

$$
e_{t+1} = \mathrm{clip}(e_t - \kappa(a_t) + \Delta e_t^{env}, 0, E_{\max})
$$

where:

- $\kappa(a_t)$ is the action cost
- $\Delta e_t^{env}$ is the environment-driven energy gain, e.g. via successful consumption

### 15.13 Observation Buffer Update

$$
m_{t+1} = M(m_t,u_{t+1})
$$

---

## 16. Reduction Properties

### 16.1 Reduction to System A

If:

$$
\lambda_{+} = \lambda_{-} = 0
$$

then:

$$
\mu_H(s,a) = 1
$$

and therefore:

$$
\psi_C(a) = d_H(t)\,\phi_H(a,u_t)
$$

which is exactly the baseline System A hunger projection.

### 16.2 Frozen Learning Limit

If:

$$
\eta_q = \eta_f = \eta_c = 0
$$

then predictive memory and predictive traces stop changing over time.

### 16.3 One-Sided Predictive Limit

If:

$$
\lambda_{+} = 0
$$

then System C reduces to disappointment-only predictive damping.

This is mathematically well-defined but considered behaviorally incomplete.

---

## 17. Clarified Non-Goals

System C does **not** include:

- explicit planning
- multi-step prediction
- action rollout trees
- a spatial world model
- prediction-based drive magnitude updates
- reinforcement learning value functions
- neural approximation

System C remains:

- mechanistic
- local
- interpretable
- and drive-centered

---

## 18. Remaining Spec Parameters

The model is mathematically closed, but a formal engineering-independent spec still needs to assign concrete values or encodings for:

- the exact context quantization map $C(y_t)$
- the neighborhood aggregation weights $w_j^{-}, w_j^{+}$
- the clipping bounds $\mu_{\min}, \mu_{\max}$

These are parameterization choices, not conceptual gaps.
