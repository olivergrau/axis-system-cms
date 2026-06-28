# Stabilization Principles for Online Neural Submodules in AXIS

## 1. Purpose

This document defines a first stabilization-oriented framing for integrating
online-learning neural submodules into AXIS CMS.

The key question is not merely whether neural networks can be added to AXIS.
They can.

The key question is:

> how can a neural component learn during interaction, be used immediately,
> and still remain stable enough that the surrounding mechanistic system does
> not become analytically or behaviorally meaningless?

This matters because AXIS CMS is not a generic machine learning environment.
It already has strong architectural commitments:

- explicit drives
- explicit internal state
- explicit transition semantics
- explicit action space
- explicit reduction paths between systems
- step-level interpretability

So the problem is not “how do we train an agent?”

The problem is:

> how do we let one part of the agent adapt online while keeping the whole
> system mechanistically intelligible and behaviorally stable?

---

## 2. What AXIS CMS Already Has

Before proposing neural online learning, it is important to identify what AXIS
already implements that can be reused as stabilizing structure.

### 2.1 Explicit State Decomposition

The implemented systems already separate internal state into bounded,
interpretable components.

Examples:

- `System A`: energy + observation buffer
- `System A+W`: energy + observation buffer + visit-count world model
- `System C`: energy + observation buffer + predictive memory + trace state
- `System C+W`: energy + observation buffer + world model + shared predictive memory + dual traces

This is already a major stabilizer, because it prevents the entire system from
being one undifferentiated adaptive black box.

### 2.2 Explicit Drives

Behavior is not currently driven by a learned reward-maximizing controller.
It is driven by explicit motivational structure:

- hunger
- curiosity
- arbitration
- bounded modulation

This is important because it means a learned submodule does not need to invent
all behavior from scratch. It can remain downstream or upstream of an already
well-structured behavioral mechanism.

### 2.3 Existing Multi-Timescale Structure

AXIS CMS already contains something very close to a primitive fast/slow
adaptation split.

In `System C` and `System C+W`:

- prediction error is computed every step
- traces accumulate over time
- action modulation changes immediately from those traces
- predictive memory changes more slowly than the current action itself

This means AXIS already has a natural place for introducing online neural
learning without redesigning the whole architecture.

### 2.4 Bounded Behavioral Expression

Current predictive systems do not let prediction arbitrarily rewrite action
selection.

They use bounded modulation:

$$
\mu(a) = \mathrm{clip}\left(\exp(\lambda_+ c(a) - \lambda_- f(a)),\; \mu_{min},\; \mu_{max}\right)
$$

This is already a biological-style stabilizer:

- prediction influence is graded
- prediction influence is bounded
- baseline action generation remains visible

That pattern should be preserved.

### 2.5 Reduction Logic

Several AXIS systems already have explicit reduction paths.

Examples:

- `A+W -> A` when curiosity is neutralized
- `C -> A` when predictive influence is neutralized
- `C+W -> A+W` when predictive modulation is neutralized

This is essential for online neural integration.

Any learned submodule should preserve a reduction path back to the analytical
baseline.

---

## 3. Why Classical RL Is Not Yet the Right First Move

A practitioner familiar with RL may correctly observe:

> online learning and immediate reuse already exist in RL.

That is true.

However, in AXIS the first problem is not whether online learning is possible.
It is whether online learning can be introduced **without destroying subsystem
clarity**.

Classical or neural RL usually couples several things at once:

- value estimation
- policy shaping
- credit assignment
- exploration strategy
- representation learning

From an AXIS perspective, this is too much at once.

The danger is not only opacity. It is also **entanglement**:

- if behavior changes, what changed?
- the predictor?
- the latent representation?
- the policy head?
- the exploration mechanism?
- the update target?

This is why the first AXIS move should not be global RL, even if the user is
comfortable with RL.

Instead, AXIS should first isolate **one online-learning function** and study
its interaction with the existing mechanistic scaffold.

---

## 4. The Central Biological Hypothesis

The main working hypothesis for this initiative is:

> biological systems do not remain stable by separating learning and acting
> completely, but by constraining plasticity through locality, gating,
> boundedness, and multiple time scales.

This hypothesis is stronger and more useful for AXIS than a generic appeal to
"brain-like learning."

It yields four concrete stabilization principles.

---

## 5. Principle 1: Locality of Plasticity

### 5.1 Statement

Only a bounded submodule should learn online.

The whole agent should not be plastic at once.

### 5.2 Motivation

If every subsystem adapts simultaneously, then:

- behavior becomes difficult to interpret
- debugging becomes much harder
- reduction paths weaken
- failure modes become entangled

### 5.3 AXIS Interpretation

The first online neural component should be one of:

- the predictor in `System C`
- the shared predictor in `System C+W`
- a compact latent memory refiner in `A+W`

The following should remain fixed in the first phase:

- drive equations
- arbitration equations
- action set
- transition semantics
- policy form

### 5.4 Formal View

Let the agent decompose into:

$$
A = (M_{fixed}, M_{learned})
$$

where:

- $M_{fixed}$ contains drives, policy form, transition semantics
- $M_{learned}$ contains one bounded neural submodule

Then online learning updates only:

$$
\theta_{t+1} = \theta_t + \Delta \theta_t
$$

for parameters inside $M_{learned}$, while $M_{fixed}$ remains invariant.

This should be a hard first constraint.

---

## 6. Principle 2: Multi-Timescale Adaptation

### 6.1 Statement

Fast behavioral adjustment and slower structural learning should be separated.

### 6.2 Motivation

Biological systems appear to use different time scales for:

- immediate response
- short-term adaptation
- slower consolidation

AXIS already has a useful analogue in predictive traces.

### 6.3 AXIS Interpretation

Use two layers:

1. **Fast layer**
   - explicit traces
   - immediate action modulation
   - interpretable short-term biasing

2. **Slow layer**
   - neural weight updates
   - compact predictor adaptation
   - slower structural change

This suggests an architecture like:

$$
(u_t, a_t, u_{t+1})
\rightarrow
\varepsilon_t
\rightarrow
z_{t+1}
$$

and separately

$$
\theta_{t+1} = \theta_t - \eta_\theta \nabla_\theta \mathcal{L}_t
$$

with:

$$
\eta_\theta \ll \eta_{trace}
$$

in an operational sense, even if the implementation does not literally use the
same optimizer family.

### 6.4 Practical Consequence

The first online neural prototypes should not let weight updates dominate
moment-to-moment behavior.

Behavior should change primarily through:

- bounded modulation
- fast trace accumulation

while the neural predictor evolves more slowly underneath.

---

## 7. Principle 3: Gated Plasticity

### 7.1 Statement

Learning should not occur uniformly on every signal.

It should be gated.

### 7.2 Motivation

If every small mismatch triggers unconstrained learning, the system becomes
fragile and noisy.

Biological learning appears to be modulated by:

- salience
- surprise
- motivational relevance
- repetition
- context

### 7.3 AXIS Interpretation

Updates may be conditioned on signals such as:

- prediction error magnitude above threshold
- repeated mismatch in similar contexts
- action eligibility
- drive relevance
- non-chaotic recent dynamics

For example, let the learning gate be:

$$
g_t \in [0,1]
$$

with update rule:

$$
\theta_{t+1} = \theta_t - \eta_\theta \, g_t \, \nabla_\theta \mathcal{L}_t
$$

Possible definitions:

$$
g_t = \mathbf{1}[\varepsilon_t > \tau]
$$

or smoother:

$$
g_t = \sigma\left(\alpha (\varepsilon_t - \tau)\right))
$$

where:

- $\tau$ is an update threshold
- $\sigma$ is a sigmoid gate

### 7.4 Strong AXIS Version

For `System C+W`, gating could even be drive-specific:

- hunger-side predictor updates only when homeostatic relevance is high
- curiosity-side predictor updates only when novelty relevance is high

This would align well with the existing dual-trace structure.

---

## 8. Principle 4: Bounded Plasticity

### 8.1 Statement

Even when updates occur, they must be bounded.

### 8.2 Motivation

Online learning fails most often when one update shifts the internal model too
far, causing:

- abrupt behavior changes
- self-reinforcing bad policies
- collapse of earlier structure

### 8.3 AXIS Interpretation

Boundedness should exist at several levels.

#### Weight-space bounds

Examples:

- gradient clipping
- update clipping
- norm constraints
- regularization toward previous weights

Formally:

$$
\|\Delta \theta_t\| \leq \delta_{max}
$$

#### Output-space bounds

The learned module should not be allowed to emit arbitrarily influential
signals.

If it predicts features, then:

- prediction outputs should stay in valid feature ranges
- modulation derived from those outputs should already be clipped by the
  existing AXIS machinery

#### Behavioral bounds

Even if the learned module drifts, the surrounding system should preserve a
controlled behavioral envelope.

This is already partly true in AXIS through bounded modulation and explicit
policy structure.

---

## 9. Principle 5: Persistent Reduction Paths

### 9.1 Statement

A learned subsystem must be disableable or neutralizable.

### 9.2 Motivation

Without a reduction path, AXIS loses one of its strongest explanatory tools:

- compare learned vs non-learned behavior
- test what the learned submodule actually adds
- recover baseline if the learned module destabilizes the system

### 9.3 AXIS Interpretation

Every online neural integration should preserve a neutral mode.

Examples:

- predictor outputs fixed baseline expectation
- modulation forced to 1.0
- learned latent memory ignored
- update gate fixed to 0

Formally, there should exist a parameter regime or switch such that:

$$
A_{learned} 
\rightarrow A_{baseline}
$$

under explicit conditions.

This is not optional. It is part of the AXIS methodology.

---

## 10. A First Stable Online-Learning Pattern for AXIS

Combining the above principles suggests the following first pattern.

### 10.1 Candidate Target

`System C` predictor replacement.

### 10.2 Fixed Components

Remain analytical:

- hunger drive
- raw action scoring
- signed error decomposition
- frustration/confidence traces
- modulation rule
- policy
- transition semantics

### 10.3 Learned Component

A small neural predictor:

$$
\hat y_{t+1} = f_\theta(y_t, a_t)
$$

or

$$
\hat y_{t+1} = f_\theta(s_t, a_t)
$$

### 10.4 Update Regime

At each step or every $k$ steps:

1. infer with current weights
2. act through the ordinary AXIS mechanism
3. observe next features
4. compute predictive loss
5. apply bounded gated update
6. continue with updated predictor

### 10.5 Stabilizers

- update only predictor weights
- small learning rate
- gradient clipping
- optional prediction-error threshold gate
- bounded feature output range
- keep modulation clipped
- preserve ability to set predictor influence to neutral

This is the most AXIS-compatible first regime currently available.

---

## 11. Implications for System C+W

`System C+W` is even more interesting, but also more delicate.

Why?

Because it contains:

- one shared predictive representation
- two drives
- two trace systems
- arbitration

This means online learning can affect not just “which action is favored,” but
also the relationship between homeostatic and exploratory evaluation.

That makes `C+W` a powerful second target, but not the safest first target.

The stabilization principles suggest:

- prototype first in `C`
- only then move to `C+W`
- keep shared prediction but separate trace interpretation
- consider drive-specific update gates later

---

## 12. Main Failure Modes to Watch

The first neural-online AXIS systems should be evaluated specifically for:

### 12.1 Prediction Drift

The predictor adapts, but in a direction that reduces usefulness for action.

### 12.2 Behavioral Oscillation

The agent alternates between incompatible response tendencies because updates
change action rankings too abruptly.

### 12.3 Self-Reinforced Error

The agent changes behavior in a way that generates biased experience, which in
turn pushes the predictor further in the wrong direction.

### 12.4 Trace–Weight Conflict

Fast traces and slow predictor updates may pull in different directions.

This is not necessarily bad, but it must be measured.

### 12.5 Loss of Reduction Clarity

If the learned submodule cannot be neutralized cleanly, AXIS loses the ability
to compare the learned and analytical regimes properly.

---

## 13. Recommended Next Questions

Before choosing a neural architecture, AXIS should next specify:

1. what exact online update schedule is allowed?
2. what loss is used?
3. what gating signal is used?
4. what bounds are enforced on updates?
5. how is neutral fallback implemented?
6. what metrics indicate stability vs instability?

This suggests that the next document in the initiative should be something
like:

- `first-online-learning-regime-draft.md`

focused on one concrete, minimal predictive experiment.

---

## 14. Provisional Conclusion

AXIS does not need to choose between:

- fixed mechanistic systems
- and unconstrained adaptive neural agents

There is a viable middle path.

That middle path is:

> online-learning neural submodules embedded inside a mechanistic architecture,
> with plasticity constrained by locality, multiple time scales, gating,
> bounded updates, and persistent reduction paths.

This is the most promising route for making neural adaptation compatible with
AXIS CMS without losing what makes AXIS valuable in the first place.
