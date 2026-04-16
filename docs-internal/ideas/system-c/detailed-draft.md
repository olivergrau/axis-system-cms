# AXIS - System C Detailed Draft

## Predictive Action Modulation in a Mechanistic Drive Architecture

---

## 1. Purpose

This document consolidates the current System C drafts into a single detailed working model.

System C extends the AXIS baseline with:

- local expectation
- retrospective prediction error
- action-specific modulation based on learned reliability and opportunity

The goal is to introduce prediction without breaking the architectural principles of AXIS:

- drives remain the primary motivational sources
- prediction does not become a separate drive
- the agent does not gain a global world model
- the policy remains structurally simple
- learning remains local, interpretable, and memory-based

This document is intended as a mathematically closed pre-specification draft.

Its purpose is to make the System C model precise enough that a formal spec can be derived without changing the underlying mathematics.

---

## 2. Consolidated Design Decision

The previous pre-drafts explored two different integration paths:

- prediction error as an input to drive activation
- prediction error as action-level modulation

For the consolidated System C draft, we resolve this in favor of the second path.

### Chosen Principle

Prediction modifies how drives express themselves over actions, not how strong the drives are in themselves.

Formally:

- drive activation remains scalar:
  $$
  d_i(t)
  $$
- prediction enters at the action projection layer:
  $$
  \phi_i(a, u_t) \rightarrow \phi_i^{C}(a, u_t, q_t, z_t)
  $$

where:

- $q_t$ is predictive memory
- $z_t$ is the prediction-derived modulation state

This choice is consistent with:

- the current `draft.md`
- the AXIS separation of concerns
- the requirement that prediction should act on actions, not on raw drive magnitude

### Consequence

Earlier formulations such as

$$
d_H(t) = h_t + \lambda \varepsilon_t
$$

are treated as rejected or pre-consolidation variants.

They are useful as conceptual stepping stones, but they are not part of the consolidated System C design.

---

## 3. Scope of System C

System C is intentionally narrower than a general predictive cognition model.

It introduces:

- expectation over the next local observation
- signed prediction error
- negative modulation for disappointed actions
- positive modulation for unexpectedly beneficial actions

It does not introduce:

- multi-step simulation
- branching action rollouts
- explicit planning
- a spatial world model
- black-box function approximation

System C is therefore predictive, but not planning-based.

---

## 4. Relationship to Earlier Drafts

The existing documents contribute different pieces:

- `draft.md` provides the correct architectural direction:
  prediction acts through action modulation
- `pre-draft/system-c.md` provides the conceptual separation between sensory expectation, internal-state expectation, and environmental regularity
- `pre-draft/system-c-refined.md` provides the most useful minimal representation of predictive memory as a context-action expectation store
- `pre-draft/system-c-math.md` provides the cleanest general treatment of retrospective prediction error and signed surprise

### Consolidated Resolution

System C keeps:

- retrospective prediction error
- a shared predictive memory
- drive-specific interpretation at the action level
- local, observation-conditioned expectations

System C rejects, for this draft:

- drive-magnitude updates from prediction error
- prediction as an independent drive
- a full-observation prediction target as the minimal version

For the first consolidated hunger-centered instantiation, prediction is restricted to the local resource configuration.

At the architectural level, however, System C should not be tied to resource signals alone.

---

## 5. Agent Architecture

System C adds a predictive layer between perception and final action arbitration.

### 5.1 General AXIS Action Structure

The generic AXIS action structure is:

$$
\psi(a) = \sum_{i \in \mathcal{D}} \alpha_i(t)\, \Pi_i(a,t)
$$

where:

- $\mathcal{D}$ is the finite set of active drives
- $\alpha_i(t) \ge 0$ is the arbitration weight of drive $i$
- $\Pi_i(a,t)$ is the action-level contribution of drive $i$

For standard drive-based systems:

$$
\Pi_i(a,t) = d_i(t)\,\phi_i(a,u_t)
$$

where:

- $d_i(t)$ is the scalar drive activation
- $\phi_i(a,u_t)$ is the drive-specific action projection

### 5.2 System C Structure

System C extends the action projection by inserting prediction-sensitive modulation into the drive contribution:

$$  
\psi_C(a) = \sum_{i \in \mathcal{D}} \alpha_i(t)\, d_i(t)\, \phi_i(a, u_t)\, \mu_i(s_t, a)
$$

where:

- $s_t = C(y_t)$ is the discretized local predictive context
- $\mu_i(\cdot)$ is a prediction-based modulation factor

Equivalently:

$$
\Pi_i^{C}(a,t) = d_i(t)\,\phi_i(a,u_t)\,\mu_i(s_t,a)
$$

For the first detailed draft, the main instantiated case is hunger:

$$  
\psi_C(a) = \alpha_H(t)\, d_H(t)\, \phi_H(a, u_t)\, \mu_H(s_t, a)
$$

This preserves the role of the drive while allowing prediction to reshape the action distribution.

### 5.3 Fixed Integration Decision

System C applies prediction-sensitive modulation at the per-drive projection level, before arbitration.

That is:

- first, each drive contribution is modulated by $\mu_i(s_t,a)$
- then, the modulated drive contributions are combined by arbitration weights $\alpha_i(t)$

This ordering is part of the consolidated model and is no longer treated as open.

---

## 6. State and Memory

### 6.1 Internal State

The internal state remains minimal:

$$
x_t = (e_t, q_t, z_t)
$$

where:

- $e_t \in [0, E_{\max}]$ is energy
- $q_t \in \mathcal{Q}$ is predictive memory
- $z_t \in \mathcal{Z}$ is the prediction-derived modulation state

The exact internal helper structure can later be expanded if needed, but this is sufficient for the current draft.

### 6.2 Existing Episodic Memory

The observation buffer remains separate:

$$
m_{t+1} = M(m_t, u_{t+1})
$$

Its role is still:

- raw episodic trace
- short-term sensory history
- support structure for other systems

It is not the predictive memory.

### 6.3 Predictive Feature Space

System C should be defined over a local predictive feature vector, not over a resource vector alone.

Let:

$$
y_t = \Omega(u_t) \in \mathcal{Y}
$$

where:

- $u_t$ is the full current observation
- $\Omega$ is a feature extraction map for prediction-relevant local structure
- $y_t$ is the predictive feature vector used by System C

This is the correct abstraction boundary.

It keeps System C general across systems while still allowing minimal concrete instantiations.

### 6.4 Formal Constraints on the Predictive Feature Map

For System C, $\Omega$ is constrained as follows:

$$
\Omega : \mathcal{U} \rightarrow \mathcal{Y}
$$

with the properties:

- locality: $\Omega(u_t)$ depends only on the current local observation $u_t$
- determinism: identical observations produce identical predictive features
- boundedness: $\mathcal{Y}$ is a bounded subset of $\mathbb{R}^k$ for finite $k$
- system-level uniformity: one fixed $\Omega$ is used for the whole system, not one per drive

The last condition is important:

> System C uses a shared predictive substrate per system.

Drive-specific semantics arise later through modulation and interpretation, not through separate predictive feature maps.

### 6.5 Predictive Memory

Predictive memory stores expected next predictive features conditioned on current predictive context and action.

Define a context map:

$$
C : \mathcal{Y} \rightarrow \mathcal{S}
$$

Then:

$$
q_t(s,a) = \hat y_t^{(s,a)} \in \mathcal{Y}
$$

with:

- $s \in \mathcal{S}$ a discretized local predictive context
- $a \in \mathcal{A}$ an action

The prediction function is:

$$
P(q_t, y_t, a_t) = q_t(C(y_t), a_t)
$$

### 6.6 Formal Constraints on the Context Encoder

The context encoder is:

$$
C : \mathcal{Y} \rightarrow \mathcal{S}
$$

where $\mathcal{S}$ is a finite context set.

For System C, $C$ must satisfy:

- determinism
- finite image: $|\mathcal{S}| < \infty$
- locality inheritance: if $\Omega$ is local, then $C \circ \Omega$ remains local

The role of $C$ is discretization, not abstraction into a hidden world model.

### 6.7 First Concrete Instantiation: Hunger-Relevant Resource Features

For the current System C detailed draft, the first concrete instantiation is still hunger-centered.

In that instantiation:

$$
y_t = r_t = (r_c, r_{up}, r_{down}, r_{left}, r_{right}) \in [0,1]^5
$$

This means:

- the architecture is defined generically over $y_t$
- the first working instance uses local resource features

This is important because it avoids coupling the architecture itself to one world or one drive.

### 6.8 Why This Abstraction Is Necessary

If System C were defined directly in terms of resource values only, it would become too tightly bound to the System A hunger case.

That would be too narrow for AXIS.

Examples:

- in a hunger-centered agent, $\Omega(u_t)$ may extract local resource availability
- in a scan-based or signal-driven agent, $\Omega(u_t)$ may extract local signal structure
- in later systems, different drives may use different readouts from the same predictive substrate

Therefore:

- resource-only prediction is a valid first instance
- resource-only prediction is not the correct general definition of System C

---

## 7. Prediction Error

After executing action $a_t$ and receiving the next predictive feature observation $y_{t+1}$, the signed prediction error is:

$$
\delta_t = y_{t+1} - \hat y_{t+1}
$$

where:

$$
\hat y_{t+1} = q_t(C(y_t), a_t)
$$

### 7.1 Signed Decomposition

System C explicitly requires both directions of prediction evaluation.

Define componentwise:

$$
\delta_t^{+} = \max(y_{t+1} - \hat y_{t+1}, 0)
$$

$$
\delta_t^{-} = \max(\hat y_{t+1} - y_{t+1}, 0)
$$

Interpretation:

- $\delta_t^{-}$: disappointment, under-delivery, failed expectation
- $\delta_t^{+}$: positive surprise, over-delivery, unexpectedly favorable outcome

This is a non-optional part of the consolidated design.

System C must learn both:

- what actions became less trustworthy
- what actions became more promising than expected

### 7.2 Scalar Aggregation

For action-level modulation, the vector-valued signed error is aggregated into scalars.

Let:

$$
\varepsilon_t^{-} = G^{-}(\delta_t^{-})
$$

$$
\varepsilon_t^{+} = G^{+}(\delta_t^{+})
$$

In the general System C model:

$$
G^{-} : \mathcal{Y} \rightarrow \mathbb{R}_{\ge 0},
\qquad
G^{+} : \mathcal{Y} \rightarrow \mathbb{R}_{\ge 0}
$$

with the properties:

- non-negativity
- determinism
- boundedness on bounded inputs

For the first hunger-centered instantiation, the aggregation uses the current cell and the four local neighbors:

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

and normalized by:

$$
\sum_{j \in \{c,up,down,left,right\}} w_j^{-} = 1,
\qquad
\sum_{j \in \{c,up,down,left,right\}} w_j^{+} = 1
$$

with the structural bias:

$$
w_c^{\pm} \ge w_{up}^{\pm}, w_{down}^{\pm}, w_{left}^{\pm}, w_{right}^{\pm}
$$

These weights are treated as system parameters, not as drive-specific adaptive variables.

This preserves realism without giving up locality.

---

## 8. Predictive Traces

The current `draft.md` introduced a negative frustration trace.
The consolidated System C model extends this symmetrically with a positive reinforcement trace.

The trace state is defined over:

$$
f_t, c_t : \mathcal{S} \times \mathcal{A} \rightarrow \mathbb{R}_{\ge 0}
$$

### 8.1 Negative Trace

$$
f_t(s,a) \ge 0
$$

interpreted as accumulated disappointment or unreliability.

Update:

$$
f_{t+1}(s_t,a_t) = (1-\eta_f) f_t(s_t,a_t) + \eta_f \varepsilon_t^{-}
$$

### 8.2 Positive Trace

$$
c_t(s,a) \ge 0
$$

interpreted as accumulated positive surprise or learned opportunity.

Update:

$$
c_{t+1}(s_t,a_t) = (1-\eta_c) c_t(s_t,a_t) + \eta_c \varepsilon_t^{+}
$$

For all unvisited context-action pairs:

$$
f_{t+1}(s,a) = f_t(s,a), \quad c_{t+1}(s,a) = c_t(s,a)
$$

for $(s,a) \neq (s_t,a_t)$.

### 8.3 Modulation State

The prediction-derived modulation state is therefore:

$$
z_t = (f_t, c_t)
$$

This state is conceptually distinct from predictive memory:

- $q_t$ stores expected outcomes
- $z_t$ stores learned action valence from signed prediction error

That distinction was only implicit in the earlier drafts and is made explicit here.

---

## 9. Action Modulation

### 9.1 Required Behavioral Property

The modulation rule must satisfy all of the following:

- disappointed actions are damped
- positively surprising actions are reinforced
- the modulation remains action-specific
- the modulation remains local and interpretable
- when prediction is disabled, the system reduces cleanly to the baseline

### 9.2 Chosen Modulation Form

We use a single multiplicative modulation factor derived from both traces:

$$
\tilde{\mu}_H(s,a) = \exp\!\left(\lambda_{+} c_t(s,a) - \lambda_{-} f_t(s,a)\right)
$$

with:

- $\lambda_{+} \ge 0$
- $\lambda_{-} \ge 0$

and a clipped final modulation:

$$
\mu_H(s,a) =
\mathrm{clip}\!\left(\tilde{\mu}_H(s,a), \mu_{\min}, \mu_{\max}\right)
$$

with:

$$
0 < \mu_{\min} \le 1 \le \mu_{\max} < \infty
$$

The clipping bounds have explicit semantics:

- $\mu_{\min}$ is the maximal allowed suppression floor
- $\mu_{\max}$ is the maximal allowed reinforcement ceiling

They are not only numerical stabilizers.

They define the admissible behavioral range of predictive modulation.

This yields:

- stronger-than-expected beneficial outcomes increase future preference
- weaker-than-expected outcomes decrease future preference
- amplification and suppression remain bounded

### 9.3 Hunger Projection

The hunger contribution becomes:

$$
\Pi_H^{C}(a,t) = d_H(t)\, \phi_H(a, u_t)\, \mu_H(s_t,a)
$$

where:

$$
d_H(t) = h_t = 1 - \frac{e_t}{E_{\max}}
$$

and hunger itself remains unchanged at the activation level.

If arbitration weights are made explicit, then:

$$
\psi_H(a) = \alpha_H(t)\,\Pi_H^{C}(a,t)
$$

### 9.4 Why Multiplicative Modulation Is Chosen

This draft chooses multiplicative modulation over additive correction because:

- it preserves the interpretation of the baseline projection
- it acts as a bias on confidence/reliability rather than a separate score source
- it gives a clean reduction:
  if $\lambda_{+}=\lambda_{-}=0$, then $\mu_H=1$
- it is symmetric and compact once both positive and negative traces exist

### 9.5 Interpretation

Each factor now has a distinct meaning:

- $d_H(t)$: how strong the homeostatic need is
- $\phi_H(a, u_t)$: what the current local perception suggests
- $\mu_H(s_t,a)$: whether this action in this context has historically under- or over-delivered

This is the central consolidated semantics of System C.

---

## 10. Predictive Memory Update

Predictive memory is updated retrospectively after observing the realized outcome.

For the selected context-action pair:

$$
q_{t+1}(s_t,a_t) = (1-\eta_q)\, q_t(s_t,a_t) + \eta_q\, y_{t+1}
$$

with:

$$
s_t = C(y_t)
$$

and $\eta_q \in (0,1]$.

For all other pairs:

$$
q_{t+1}(s,a) = q_t(s,a)
$$

for $(s,a) \neq (s_t,a_t)$.

This gives System C a simple and interpretable expectation update rule:

- local
- context-conditioned
- action-conditioned
- non-neural
- non-planning

The update is a convex combination because $\eta_q \in (0,1]$ and $\mathcal{Y}$ is bounded.

Therefore the expectation state remains inside the admissible feature range whenever $y_{t+1} \in \mathcal{Y}$.

---

## 11. Decision and Update Cycle

The consolidated System C cycle is:

### 11.1 Perception

$$
u_t = S(s_t^{world})
$$

extract:

$$
y_t = \Omega(u_t)
$$

For the first hunger-centered instantiation:

$$
y_t = r_t = (r_c, r_{up}, r_{down}, r_{left}, r_{right})
$$

### 11.2 Drive Activation

$$
d_H(t) = 1 - \frac{e_t}{E_{\max}}
$$

More generally:

$$
d_i(t)
$$

remains prediction-independent at the activation layer.

### 11.3 Context Encoding

$$
s_t = C(y_t)
$$

### 11.4 Action Projection

$$
\psi_C(a) = \sum_{i \in \mathcal{D}} \alpha_i(t)\, d_i(t)\, \phi_i(a, u_t)\, \mu_i(s_t,a)
$$

with:

$$
\alpha_i(t) \ge 0
$$

and, when normalized arbitration is used:

$$
\sum_{i \in \mathcal{D}} \alpha_i(t) = 1
$$

Minimal instantiated version:

$$
\psi_C(a) = \alpha_H(t)\, d_H(t)\, \phi_H(a, u_t)\, \mu_H(s_t,a)
$$

For a single-drive system with no separate arbitration dynamics, one may set:

$$
\alpha_H(t) = 1
$$

### 11.5 Action Selection

$$
a_t \sim \pi(\psi_C)
$$

For example:

$$
P(a \mid x_t,u_t,m_t,q_t,z_t) =
\frac{\exp(\beta \psi_C(a))}
{\sum_{a'} \exp(\beta \psi_C(a'))}
$$

### 11.6 World Transition

$$
s_{t+1}^{world} = F_{world}(s_t^{world}, a_t)
$$

### 11.7 New Observation

$$
u_{t+1} = S(s_{t+1}^{world})
$$

extract:

$$
y_{t+1} = \Omega(u_{t+1})
$$

### 11.8 Retrieve Prediction

$$
\hat y_{t+1} = q_t(s_t, a_t)
$$

### 11.9 Compute Signed Error

$$
\delta_t^{+} = \max(y_{t+1} - \hat y_{t+1}, 0)
$$

$$
\delta_t^{-} = \max(\hat y_{t+1} - y_{t+1}, 0)
$$

and aggregate:

$$
\varepsilon_t^{+} = G^{+}(\delta_t^{+}), \quad
\varepsilon_t^{-} = G^{-}(\delta_t^{-})
$$

### 11.10 Update Predictive Traces

$$
f_{t+1}(s_t,a_t) = (1-\eta_f) f_t(s_t,a_t) + \eta_f \varepsilon_t^{-}
$$

$$
c_{t+1}(s_t,a_t) = (1-\eta_c) c_t(s_t,a_t) + \eta_c \varepsilon_t^{+}
$$

### 11.11 Update Predictive Memory

$$
q_{t+1}(s_t,a_t) = (1-\eta_q)\, q_t(s_t,a_t) + \eta_q\, y_{t+1}
$$

### 11.12 Update Other Agent State

Energy remains baseline-consistent:

$$  
e_{t+1} = \mathrm{clip}(e_t - \kappa(a_t) + \Delta e_t^{env}, 0, E_{\max})
$$

Observation buffer update remains unchanged:

$$
m_{t+1} = M(m_t, u_{t+1})
$$

---

## 12. Reduction Properties

System C should collapse cleanly to earlier behavior under parameter limits.

### 12.1 Reduction to Baseline Action Projection

If:

$$
\lambda_{+} = \lambda_{-} = 0
$$

then:

$$
\mu_H(s,a) = 1
$$

and the action projection becomes the baseline hunger projection.

For the single-drive hunger instantiation with $\alpha_H(t)=1$:

$$
\psi_C(a) = d_H(t)\,\phi_H(a,u_t)
$$

### 12.2 No Learning Limit

If:

$$
\eta_q = \eta_f = \eta_c = 0
$$

then predictive structures stop changing.

### 12.3 No Positive Reinforcement Limit

If:

$$
\lambda_{+} = 0
$$

the model reduces to disappointment-only modulation.

This corresponds to the earlier one-sided draft and is considered incomplete, not preferred.

---

## 13. Generalization Beyond Hunger

The architecture is not hunger-specific even though the first detailed draft is centered on hunger.

The shared layer is:

- predictive memory $q_t$
- signed prediction error
- trace state $z_t = (f_t, c_t)$

Drive-specific semantics arise in the modulation term and in the choice of aggregation and trace interpretation:

$$
\mu_i(s,a)
$$

Different drives may use the same predictive substrate differently.

Examples:

- hunger: reward under-delivery is suppressive, reward over-delivery is reinforcing
- curiosity: unexpected outcomes may be attractive even when not resource-beneficial
- safety: unpredictability may shift action preference toward caution

The consolidated point is:

Prediction is shared as a substrate, but interpreted per drive.

---

## 14. Clarified Non-Goals

To avoid drift, the following are explicitly outside this detailed draft:

- prediction over long trajectories
- action simulation before choice
- explicit value functions
- reward learning in the reinforcement learning sense
- replacing drive architecture with prediction architecture
- using predictive memory as a covert world model

System C remains mechanistic and local.

---

## 15. Resolved Specification Parameters

The model is now mathematically closed and all concrete parameter values have been fixed.

The decisions below were made with two guiding principles:

- **conservative behavioral range** -- prediction should observably influence the agent without overriding its drives
- **biological plausibility** -- where a choice exists, prefer asymmetries that align with known learning dynamics (loss aversion, cautious generalization)

### 15.1 Drive Scope

The first System C implementation targets **hunger-only** with a single drive:

$$
\alpha_H(t) = 1
$$

This isolates the predictive extension cleanly. The only behavioral difference between System C and System A is the prediction-based modulation $\mu_H$. This makes experimental comparison straightforward: any divergence in behavior can be attributed to prediction, not to drive interaction effects.

A future System C+W variant can extend to dual-drive (hunger + curiosity) without changing the predictive architecture.

### 15.2 Context Quantization

The discretization map $C(y_t)$ uses **binary thresholding per cell**:

$$
C(y_t)_j = \begin{cases} 1 & \text{if } y_{t,j} \ge 0.5 \\ 0 & \text{otherwise} \end{cases}
\qquad j \in \{c, up, down, left, right\}
$$

This yields:

$$
|\mathcal{S}| = 2^5 = 32
$$

The total memory footprint is $32 \times |\mathcal{A}|$ entries for each of $q_t$, $f_t$, and $c_t$.

**Rationale:** The grid world's resource distribution is naturally sparse -- cells are either empty or carry a resource. Binary quantization captures the decision-relevant structure (is there something here or not?) without introducing bins that are rarely visited. With 32 contexts and 6 actions, the agent has 192 context-action pairs -- dense enough to learn from within a typical 200-step episode, sparse enough to store as a flat table.

### 15.3 Predictive Memory Initialization

All predictive memory entries are initialized to zero:

$$
q_0(s, a) = \mathbf{0} \in \mathcal{Y} \qquad \forall (s, a) \in \mathcal{S} \times \mathcal{A}
$$

**Rationale:** The agent starts expecting nothing. Any resource encountered becomes a positive surprise, which naturally reinforces early exploration. This is both the simplest initialization and the most biologically plausible one -- a naive agent has no innate expectations about its environment. It also avoids biasing the agent toward specific regions of the grid before it has gathered any experience.

The frustration and confidence traces are likewise initialized to zero:

$$
f_0(s, a) = 0, \qquad c_0(s, a) = 0 \qquad \forall (s, a)
$$

This ensures that $\mu_H(s, a) = 1$ at the start, giving exact System A behavior at $t = 0$.

### 15.4 Modulation Bounds

$$
\mu_{\min} = 0.3, \qquad \mu_{\max} = 2.0
$$

**Rationale:** These bounds define the behavioral range of predictive modulation. At the floor, an action's score is reduced to 30% of its baseline value -- substantial suppression, but the action is never fully eliminated from the softmax distribution. At the ceiling, an action can be boosted to double its baseline score -- a meaningful preference, but one that still respects the drive signal and observation structure.

This conservative range ensures that prediction **nudges** behavior rather than **overriding** it. The agent's drives and current perception remain the dominant forces; prediction acts as a learned confidence bias on top of that.

### 15.5 Learning Rates

$$
\eta_q = 0.3, \qquad \eta_f = 0.2, \qquad \eta_c = 0.15
$$

**Rationale:** The three learning rates are intentionally asymmetric:

- **Predictive memory** ($\eta_q = 0.3$) learns fastest. The agent needs accurate expectations to compute meaningful prediction errors. With $\eta_q = 0.3$, the expectation converges within roughly 5--7 visits to a context-action pair.

- **Frustration trace** ($\eta_f = 0.2$) learns somewhat slower. Negative experiences should accumulate reliably but not cause immediate, permanent avoidance from a single bad outcome.

- **Confidence trace** ($\eta_c = 0.15$) is the slowest. Positive reinforcement builds more gradually than negative -- the agent becomes cautious faster than it becomes confident. This reflects a **loss-aversion asymmetry** observed in biological learning systems: organisms are generally quicker to learn what to avoid than what to approach.

### 15.6 Sensitivity Parameters

$$
\lambda_{+} = 1.0, \qquad \lambda_{-} = 1.5
$$

**Rationale:** These scale the traces inside the exponential modulation factor:

$$
\tilde{\mu}_H(s, a) = \exp(\lambda_{+} c_t(s, a) - \lambda_{-} f_t(s, a))
$$

The asymmetry ($\lambda_{-} > \lambda_{+}$) reinforces the loss-averse character of the learning rates: not only does frustration accumulate faster, it also has a stronger per-unit effect on the modulation factor. This means the agent is quicker to suppress unreliable actions than to boost promising ones.

With the conservative modulation bounds $[0.3, 2.0]$:

- A frustration trace of $f_t \approx 0.8$ reaches the suppression floor $\mu_{\min} = 0.3$
- A confidence trace of $c_t \approx 0.7$ reaches the reinforcement ceiling $\mu_{\max} = 2.0$

These thresholds are reachable within a typical episode but require several consistent experiences, not a single outlier.

### 15.7 Neighborhood Aggregation Weights

The scalar prediction error aggregation uses center-heavy weighting:

$$
w_c^{\pm} = 0.5, \qquad w_{up}^{\pm} = w_{down}^{\pm} = w_{left}^{\pm} = w_{right}^{\pm} = 0.125
$$

Both positive and negative aggregation use the same weight structure.

**Rationale:** The center cell is where the agent directly acts -- it is the cell where `consume` extracts resources and where the agent stands. Changes at the center cell are the most decision-relevant signal for hunger-driven behavior. The four neighbors provide environmental context (did nearby resources also change?) but carry less direct causal attribution.

The 0.5 / 0.125 split ensures that:

- a center-cell surprise alone produces a scalar error of 0.5 at maximum
- a full-neighborhood surprise (all five cells) produces a scalar error of 1.0 at maximum
- directional patterns (e.g., only left-cell resource changed) contribute a modest 0.125 signal

### 15.8 Summary Parameter Table

| Parameter | Symbol | Value | Role |
|-----------|--------|-------|------|
| Drive scope | $\alpha_H$ | $1$ | Single-drive hunger-only |
| Context bins | $|\mathcal{S}|$ | $32$ | Binary per cell, threshold 0.5 |
| Memory init | $q_0$ | $\mathbf{0}$ | No initial expectations |
| Modulation floor | $\mu_{\min}$ | $0.3$ | Maximum suppression |
| Modulation ceiling | $\mu_{\max}$ | $2.0$ | Maximum reinforcement |
| Memory learning rate | $\eta_q$ | $0.3$ | Expectation convergence |
| Frustration learning rate | $\eta_f$ | $0.2$ | Negative trace accumulation |
| Confidence learning rate | $\eta_c$ | $0.15$ | Positive trace accumulation |
| Positive sensitivity | $\lambda_{+}$ | $1.0$ | Confidence-to-modulation scaling |
| Negative sensitivity | $\lambda_{-}$ | $1.5$ | Frustration-to-modulation scaling |
| Center aggregation weight | $w_c^{\pm}$ | $0.5$ | Prediction error at own cell |
| Neighbor aggregation weight | $w_{dir}^{\pm}$ | $0.125$ | Prediction error at adjacent cells |

---

## 16. Current Architectural Verdict

The consolidated System C model is now internally coherent and fully parameterized.

It is read under the following commitments:

- prediction is retrospective, not counterfactual
- predictive memory is separate from episodic memory
- predictive memory is shared, local, and action-conditioned
- prediction error is evaluated in both directions
- negative surprise damps action preference
- positive surprise reinforces action preference
- prediction acts on action expression, not drive magnitude
- all specification parameters are fixed (Section 15)

Under these commitments, System C is a genuine extension of AXIS rather than a disguised shift to planning or RL.

The model is ready for a formal engineering specification mapping its components to the AXIS SDK and Construction Kit.
