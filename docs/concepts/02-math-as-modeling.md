# Math as a Modeling Tool

**AXIS Conceptual Series -- Document 2 of 5**

> **Reading order:**
> [1. AXIS CMS Vision](01-axis-cms-vision.md) |
> **2. Math as Modeling** |
> [3. Agent Framework](03-agent-framework.md) |
> [4. System A](04-system-a.md) |
> [5. System A+W](05-system-aw.md)

---

## 1. Why This Document Exists

Before we present the mathematical models behind AXIS agents, it is
worth pausing to ask: *why math at all?*

Mathematics is not the only way to specify agent behavior. Behavior
trees, rule systems, neural networks, evolutionary algorithms, and
plain procedural code are all viable alternatives. Each has
trade-offs. The choice of mathematical formalism in AXIS is deliberate
and has specific consequences for what we can and cannot do with the
resulting agents.

This document explains the reasoning behind that choice.

---

## 2. Models and Reality

A model is a simplified representation of a system that captures
some of its structure while ignoring the rest. Every model is wrong
in the strict sense -- it is not the thing it models. But some models
are useful because they isolate the mechanisms we care about and make
them amenable to analysis.

In AXIS, we model **agent behavior**: the process by which an
autonomous entity perceives its environment, maintains internal state,
and selects actions. The "real system" we are modeling is not a
physical organism -- it is a *class of mechanisms* that produce
recognizable behavioral patterns (foraging, exploration, response
to scarcity).

A mathematical model of agent behavior has three components:

1. **State variables** -- quantities that change over time and
   characterize the agent and its environment
   ($e_t$, $u_t$, $m_t$, $w_t$, ...).
2. **Transition rules** -- functions that define how state variables
   evolve from one timestep to the next
   ($x_{t+1} = F(x_t, u_t, a_t)$).
3. **Parameters** -- constants that control the quantitative behavior
   of the transition rules ($\beta$, $\gamma$, $\lambda_{\text{stay}}$, ...).

Given initial conditions and parameter values, the model produces a
deterministic trajectory (or a distribution over trajectories, if the
policy is stochastic). This trajectory *is* the model's prediction
of agent behavior.

---

## 3. What Mathematical Formalism Gives Us

### 3.1 Precision

A formula is unambiguous. The statement

$$d_H(t) = \max\!\bigl(0,\ \min\!\bigl(1,\ 1 - \frac{e_t}{E_{\max}}\bigr)\bigr)$$

admits exactly one interpretation. There is no room for "it depends
on what you mean by hunger." Compare this to a natural-language
specification like "the agent gets hungrier as its energy decreases"
-- which is true of infinitely many possible functions, some linear,
some exponential, some with thresholds, some with saturation.

Mathematical precision eliminates specification ambiguity. When two
people read the formula, they compute the same number.

### 3.2 Composability

Mathematical functions compose naturally. If the hunger drive
produces a score vector $\phi_H(a)$ and the curiosity drive produces
$\phi_C(a)$, the combined modulation is:

$$\psi(a) = w_H(t) \cdot d_H(t) \cdot \phi_H(a) + w_C(t) \cdot d_C(t) \cdot \phi_C(a)$$

This is a linear combination -- the most natural way to blend
multiple signals. The structure is transparent: each drive
contributes independently, weighted by its dynamic weight and
activation. Adding a third drive means adding one more term.

In code-first approaches, composition often requires refactoring.
In math, it is syntactic.

### 3.3 Analyzability

With a mathematical model, we can reason about behavior *before*
running any code:

- **Boundary analysis.** What happens when $e_t = 0$?
  Then $d_H(t) = 1$, and the hunger modulation dominates all
  action scores. We know this from the formula, without simulation.

- **Parameter sensitivity.** How does behavior change as
  $\beta \to \infty$? The softmax policy converges to argmax --
  the agent becomes deterministic. Again, we know this from the math.

- **Reduction properties.** When $\mu_C = 0$, the curiosity
  contribution vanishes and System A+W reduces to System A.
  This is a mathematical identity that we can verify algebraically.

- **Fixed points and attractors.** In what states does the agent's
  behavior stabilize? Under what conditions does the agent converge
  to pure exploitation vs. pure exploration?

None of these analyses require running the code. They follow from
the equations directly. This is the power of mathematical formalism:
it makes the model a first-class object of study, independent of
any particular implementation.

### 3.4 Reproducibility

A mathematical model is implementation-independent. Two programmers
implementing the same equations in different languages (Python, Rust,
Julia) must produce identical numerical results. The equations serve
as a language-neutral specification that any implementation can be
verified against.

In AXIS, this property is exploited through **worked examples**:
hand-calculated numerical traces that serve as ground truth for the
implementation. If the code produces different numbers than the
worked example, the code is wrong.

### 3.5 Falsifiability

A mathematically specified model makes concrete predictions. Given
specific initial conditions and parameters, it predicts specific
action probabilities, specific energy trajectories, specific
termination times. These predictions can be checked.

When a prediction fails -- when the code produces a different
result -- we know exactly where to look: the discrepancy is between
the formula and the code. There is no ambiguity about what the
expected behavior "should be."

---

## 4. Alternatives and Their Trade-offs

Mathematics is not the only modeling approach. Here is how other
paradigms compare for the specific goals of AXIS.

### 4.1 Behavior Trees

A behavior tree is a directed graph of conditions and actions.
Nodes check predicates ("is energy low?") and route to sub-trees
that select actions.

**Strengths:** Transparent decision flow. Easy to visualize and
debug. Industry-standard in game AI.

**Limitations for AXIS:** Behavior trees encode a designer's
*intended* decisions, not a mechanism that *generates* decisions.
The tree is prescriptive: the designer decides that "when hungry,
prioritize food." In AXIS, we want the hunger drive to
*automatically* increase food-seeking behavior through the action
modulation function, without anyone encoding the rule. The behavior
emerges from the mechanism.

Behavior trees also do not compose mathematically. Adding a second
drive (curiosity) to a behavior tree requires structural
modification of the tree. In the mathematical model, it requires
adding one term to a sum.

### 4.2 Neural Networks / Learned Policies

A neural network maps observations to actions through layers of
learned weights. Given enough training data and an appropriate
reward signal, it can produce sophisticated behavior.

**Strengths:** Can discover policies that humans would not design.
Scales to complex environments. State of the art in many domains.

**Limitations for AXIS:** The resulting policy is opaque.
Understanding *why* a neural network chose action $a$ requires
interpretability techniques (saliency maps, feature attribution)
that are themselves approximate. The explanatory gap between "the
network assigned this action a Q-value of 3.7" and "the agent
chose this action because its hunger drive activation was 0.8 and
the right neighbor has resource value 0.6" is fundamental.

AXIS agents are designed to be explained by their equations, not
by post-hoc analysis of learned weights.

### 4.3 Reinforcement Learning

Reinforcement learning (RL) specifies a reward function and lets
an optimization process discover the policy. The agent learns to
maximize cumulative reward through trial and error.

**Strengths:** The policy is optimized for the task. RL agents can
outperform hand-designed agents on well-defined objectives.

**Limitations for AXIS:** The reward function is an external
signal that does not correspond to any biological mechanism. Real
organisms do not receive rewards -- they have homeostatic needs.
AXIS replaces the reward function with internal drives that are
defined mechanistically. The agent does not "try to maximize energy"
-- it has a hunger drive whose activation increases as energy
decreases, which in turn modulates action scores toward food-seeking.
The relationship between energy level and behavior is a direct
mathematical consequence, not a learned association.

Additionally, RL requires a training phase that produces a fixed
policy. AXIS agents do not train -- they execute their equations
from the first timestep. Their behavior is determined by the model
and its parameters, not by a training history.

### 4.4 Rule Systems / Expert Systems

Rule systems use if-then rules: "if energy < 20 and food nearby,
then consume."

**Strengths:** Fully transparent. Easy to implement. Rules can be
added modularly.

**Limitations for AXIS:** Rules produce discrete behavior switches
("when this condition is met, do that"). AXIS agents exhibit
*continuous* behavioral transitions. As energy decreases, the
probability of food-seeking behavior increases smoothly, not at a
hard threshold. The softmax policy produces a probability
distribution that shifts gradually as drive activations change.
This continuous modulation is essential for studying regime
transitions (e.g., the shift from exploration to foraging in
System A+W).

### 4.5 Procedural Code

One could simply write the agent behavior directly in code without
any mathematical specification: a Python function that reads the
world state and returns an action.

**Strengths:** No specification overhead. Immediate implementation.

**Limitations for AXIS:** Without a mathematical model, there is no
independent specification to verify against. The code *is* the spec.
This makes it impossible to distinguish implementation bugs from
design decisions. It also eliminates the possibility of
pre-implementation analysis (boundary behavior, parameter
sensitivity, reduction properties).

In AXIS, the math is written first, verified by hand through
worked examples, and only then implemented. The code is a
translation, not the original.

---

## 5. The AXIS Approach: Specification-Driven Development

AXIS uses mathematics as the **primary specification** for agent
behavior. The development process follows a specific order:

### Step 1: Biological Motivation

Identify the biological capacity to model. Describe it in
qualitative terms. Example: "An organism that forages for resources,
with behavior modulated by its energy level."

### Step 2: Formal Definition

Express the capacity as mathematical functions. Define state
spaces, input spaces, transition functions, and parameters.
Fix notation. Establish invariants.

### Step 3: Worked Examples

Choose specific parameter values and initial conditions. Compute
the model's behavior by hand, step by step, showing every
intermediate value. These worked examples serve as:

- A validation that the math produces sensible behavior
- A test suite for the implementation
- A pedagogical tool for understanding the model

### Step 4: Implementation

Translate the math to code. Each mathematical object maps to a
code component. The translation should be as direct as possible:
the code should "look like the math."

### Step 5: Verification

Run the implementation against the worked examples. The code must
reproduce the hand-calculated values to numerical precision. Any
discrepancy is a bug in the code, not a "different interpretation"
of the spec.

### Step 6: Visualization and Analysis

Build visualization adapters that display the intermediate values
(drive activations, modulation scores, action probabilities)
alongside the agent's behavior. This closes the loop: the math
defines the behavior, the code produces it, and the visualization
makes it visible.

---

## 6. Mathematical Conventions Used in AXIS

### 6.1 Notation Style

AXIS follows standard mathematical notation from dynamical systems
theory and decision theory:

- **Time index:** Subscript $t$ denotes the value at timestep $t$.
  $e_t$ is energy at time $t$, $u_t$ is the observation at time $t$.

- **Sets:** Calligraphic letters for spaces: $\mathcal{A}$ (action
  space), $\mathcal{X}$ (state space), $\mathcal{U}$ (observation
  space).

- **Functions:** Uppercase letters: $S$ (sensor), $F$ (transition),
  $D$ (drive), $G$ (memory update).

- **Scalars:** Lowercase letters: $e$ (energy), $d$ (drive
  activation), $h$ (hunger), $r$ (resource).

- **Vectors/tuples:** Bold or parenthesized: $u_t = (b_c, r_c, b_{up}, r_{up}, \ldots)$.

- **Parameters:** Greek letters for adjustable parameters: $\beta$
  (inverse temperature), $\gamma$ (gating sharpness), $\alpha$
  (novelty balance), $\kappa$ (energy gain factor).

### 6.2 Clipping Convention

The function $\text{clip}(x, a, b) = \max(a, \min(b, x))$ is used
throughout for bounding values to valid ranges. Energy is always
clipped to $[0, E_{\max}]$, drive activations to $[0, 1]$, and
resource values to $[0, 1]$.

### 6.3 Action Ordering

The canonical action ordering is consistent across all models:

$$\mathcal{A} = (\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}, \text{CONSUME}, \text{STAY})$$

All vectors indexed by action (drive contributions, probabilities,
admissibility masks) follow this ordering.

### 6.4 Coordinate System

The grid uses screen coordinates: $x$ increases to the right,
$y$ increases downward. The direction deltas are:

| Direction | $\Delta x$ | $\Delta y$ |
|---|---|---|
| UP | $0$ | $-1$ |
| DOWN | $0$ | $+1$ |
| LEFT | $-1$ | $0$ |
| RIGHT | $+1$ | $0$ |

---

## 7. From Math to Insight

The deepest value of mathematical modeling is not precision or
reproducibility -- it is the ability to *understand* what a system
does and why.

When we write $w_C(t) = w_C^{\text{base}} \cdot (1 - d_H(t))^{\gamma}$,
we are not just defining a function. We are making a statement about
the relationship between hunger and curiosity: curiosity is fully
available when the agent is well-fed ($d_H \approx 0$, so
$(1 - d_H)^{\gamma} \approx 1$) and completely suppressed when the
agent is starving ($d_H \approx 1$, so $(1 - d_H)^{\gamma} \approx 0$).
The parameter $\gamma$ controls how sharply this transition occurs.

This is a *design decision* expressed as mathematics. We can debate
whether the relationship should be a power law versus an exponential,
whether the gating should be symmetric or asymmetric, whether there
should be a floor on curiosity even under high hunger. Each
alternative is a different function with different behavioral
consequences -- and we can analyze those consequences mathematically,
before writing any code.

This is what it means to use math as a modeling tool: not to make
things complicated, but to make the design space navigable.

---

> **Next:** [The Generic Agent Framework](03-agent-framework.md) --
> The mathematical scaffold that all AXIS agent systems instantiate.
