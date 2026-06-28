# Prediction System World-Fit Analysis

This document analyzes the current explicit AXIS prediction system against the
existing world classes and experimental conditions used so far.

The goal is not to propose a neural replacement yet. The goal is to determine
whether the current prediction system, as implemented, can plausibly produce a
real behavioral advantage in the existing 2D grid-world families, and under
what conditions.

This is necessary because earlier experiments have not shown a robust,
convincing survival or behavioral advantage from the prediction layer, while
other additions such as the spatial world model with curiosity clearly have.

## Scope

This document focuses on the current explicit prediction system used by:

- System C
- System C+W

It evaluates that system against worlds based on:

- 2D grid structure
- local resources
- clustered vs uniform layouts
- resource depletion and cooldown / regeneration
- movement constraints or blockades
- simple local observability

The emphasis is on whether the existing prediction mechanism can be expected to
help **in principle**, before discussing redesign or neuralization.

## 1. The Current System's Actual Competence

The current prediction system learns local one-step expectations:

\[
q_t(s,a) \approx \mathbb{E}[y_{t+1} \mid s_t=s, a_t=a]
\]

and transforms repeated mismatch into local trust-like traces:

\[
f_{t+1}(s_t,a_t) = (1-\eta_f)f_t(s_t,a_t) + \eta_f\varepsilon_t^-
\]

\[
c_{t+1}(s_t,a_t) = (1-\eta_c)c_t(s_t,a_t) + \eta_c\varepsilon_t^+
\]

This means the system is good at only one specific kind of learning:

> learning whether a given action, in a given recurring local context, tends to
> under-deliver or over-deliver relative to local next-step expectation.

It is **not** a planner, not a true map learner, not a latent-state inferencer,
and not a long-horizon value learner.

That immediately constrains the kinds of worlds where it can help.

## 2. Necessary Conditions for a Genuine Advantage

The current system can only produce a genuine advantage if all of the following
are approximately true:

1. **Recurring local contexts**
   The same context-action pairs must recur often enough to learn from.

2. **Outcome regularity at the context-action level**
   The same \((s,a)\) pair must induce a meaningfully similar distribution over
   outcomes.

3. **Non-triviality**
   The immediate observation alone must not already determine the action choice
   sufficiently well.

4. **One-step informativeness**
   The next local observation must carry useful signal about whether the action
   was behaviorally good or bad.

5. **Limited hidden-state aliasing**
   Different latent world situations should not collapse too often into the same
   context if they produce very different outcomes.

If these conditions do not hold, prediction will either do nothing useful or
learn misleading local statistics.

## 3. The Central Failure Mode: Context Aliasing Under World Change

The most important weakness of the current system is this:

> It treats local context as the key explanatory state, but many worlds contain
> hidden or history-dependent structure that is not represented in that local context.

A context-action pair may therefore be locally identical while actually meaning
very different things in the world.

### Example: Depleted Resource Revisit

Suppose the agent sees a promising local situation and moves right.

Pre-action local features:

\[
y_t = (r_c, r_u, r_d, r_l, r_r) = (0.1, 0.0, 0.0, 0.0, 0.8)
\]

After thresholding, assume this maps to context \(s=17\).

Action:

\[
a_t = \text{RIGHT}
\]

On the first visit, the next observation may contain high resource:

\[
y_{t+1}^{(1)} = (0.8, 0.1, 0.0, 0.0, 0.0)
\]

Later, after the field has been consumed, the agent encounters a locally very
similar pre-action situation again, still mapping to the same context \(s=17\),
but now the actual next observation is:

\[
y_{t+1}^{(2)} = (0.1, 0.0, 0.0, 0.0, 0.0)
\]

If the context encoding does not represent the relevant difference, the system
will treat both transitions as samples from the same \((s,a)\) pair.

Then the learned prediction becomes a compromised average, and the traces may
register frustration where the deeper truth is not:

> "RIGHT is unreliable here"

but rather:

> "The world state has changed because the resource was already harvested earlier."

This is not a small edge case. It is likely to happen frequently in simple
resource worlds with depletion and revisit.

```text
Depleted-resource revisit intuition

First encounter before RIGHT:          Later encounter before RIGHT:

          [ UP: 0.0 ]                            [ UP: 0.0 ]
[ L: 0.0 ] [ A: 0.1 ] [ R: 0.8 ]      [ L: 0.0 ] [ A: 0.1 ] [ R: 0.8 ]
        [ DOWN: 0.0 ]                          [ DOWN: 0.0 ]

move RIGHT                                 move RIGHT

new current often rich                     new current now depleted

y_(t+1)^(1) current = 0.8                  y_(t+1)^(2) current = 0.1

Local appearance before the move can look the same, while the hidden world
history makes the actual outcome very different.
```

## 4. Case Analysis by World Type

The following sections analyze the main existing or natural AXIS world classes.

### Case A: Uniform Resource Worlds

#### Description

Resources are spread fairly evenly or randomly with weak local structure.
There are no strong hidden transition rules. The environment is simple and
mostly stationary except for ordinary depletion / regeneration.

#### Expected baseline behavior

A baseline hunger agent already does reasonably well because local resource
contrast is often enough to choose actions.

#### Can prediction help?

Usually only weakly, and often not at all.

Reason:

- if local observation already says which neighbor is richer, baseline action
  selection already captures most of the available information
- prediction only adds value if moving toward apparently rich local options is
  systematically more or less successful than it looks from the present frame

#### Toy example

Suppose the local scores from hunger are:

\[
h_t(UP)=0.1,\quad h_t(RIGHT)=0.8,\quad h_t(DOWN)=0.0,\quad h_t(LEFT)=0.0
\]

If `RIGHT` reliably leads to the locally richest outcome, then prediction will
only relearn what the current observation already indicates.

```text
Uniform-world intuition

          [ UP: low ]
[ L: low ] [ A: here ] [ R: high ]
         [ DOWN: low ]

Baseline hunger already says: move RIGHT.
If RIGHT reliably stays the best local move, prediction adds little.
```

#### Verdict

**Very low expected advantage** unless additional stochastic or deceptive
transition structure is introduced.

### Case B: Clustered Resource Worlds

#### Description

Resources appear in patches or clusters. Local gradients may exist around patch
boundaries.

#### Potential benefit

Prediction might help slightly at patch fringes if a local pattern repeatedly
signals that a direction tends to over- or under-deliver relative to its raw
appearance.

#### But the main issue

Clustered worlds with depletion also create exactly the revisit problem above.
A formerly rich patch area later becomes locally similar but much poorer.

That means the same context can mean:

- active patch fringe
- exhausted patch fringe

If the context encoder does not separate them, prediction learns an average.

#### Toy example

First encounter:

\[
y_t = (0.0, 0.0, 0.0, 0.0, 0.7), \qquad y_{t+1}^{(1)} = (0.7,0.4,0.0,0.0,0.0)
\]

Later encounter after local harvest:

\[
y_t' \approx y_t, \qquad y_{t+1}^{(2)} = (0.1,0.0,0.0,0.0,0.0)
\]

Prediction average becomes less informative, while frustration may rise for the
wrong conceptual reason.

```text
Cluster-fringe revisit intuition

Early visit before RIGHT:                Later visit before RIGHT:

          [ UP: 0.0 ]                            [ UP: 0.0 ]
[ L: 0.0 ] [ A: 0.0 ] [ R: 0.7 ]      [ L: 0.0 ] [ A: 0.0 ] [ R: 0.7 ]
        [ DOWN: 0.0 ]                          [ DOWN: 0.0 ]

move RIGHT                                 move RIGHT

new current = 0.7                          new current = 0.1

The pre-action local pattern can recur, but the patch has changed state due to
prior harvesting.
```

#### Verdict

**Weak to moderate possible advantage**, but only if:

- contexts recur often
- patch-edge structure is stable
- and depletion does not collapse too many semantically different situations into the same context

Otherwise advantage is likely fragile or absent.

### Case C: Worlds with Resource Cooldown / Regeneration

#### Description

Resources regrow after some cooldown period or continuous regeneration process.

#### Why this is tricky

Regeneration introduces hidden temporal state:

- same local geometry
- same visible local neighborhood pattern
- different latent regrowth phase

If the regrowth phase is not visible in the current observation, prediction
cannot represent it directly.

#### Toy example

Suppose a field regrows after 10 steps.

At time \(t_1\):

\[
y_t = (0.0,0.0,0.0,0.0,0.8)
\]

At time \(t_2\), shortly after harvesting:

\[
y_t' = (0.0,0.0,0.0,0.0,0.8)
\]

If both still quantize to the same context but the hidden regrowth stage differs,
then the action-outcome distribution is multi-modal from the model's perspective.

#### Possible exception

If regeneration creates visibly different local states that survive quantization,
prediction may still help.

#### Verdict

**Often poor fit** unless regrowth state is sufficiently visible in the local
features or encoded by additional context variables.

### Case D: Simple Deterministic Worlds

#### Description

Movement is deterministic, consumption is deterministic, and local observation
truthfully reflects what will happen next.

#### Expected outcome

Prediction provides almost no genuine advantage.

Reason:

- the next local observation is already almost fully implied by the current
  observation plus the chosen action
- there is little uncertainty to calibrate
- there is little hidden unreliability to learn

Prediction then mostly becomes redundant bookkeeping.

```text
Deterministic-world intuition

current observation + chosen action
                |
                v
        next local observation
        is already almost fixed

Little hidden uncertainty -> little extra value for prediction.
```

#### Verdict

**No meaningful advantage expected**.

This is one of the strongest explanations for null results in earlier experiments
if many of them were close to this regime.

### Case E: Stochastic Transition Worlds

#### Description

Certain actions succeed only probabilistically or yield noisy outcomes.
Examples:

- move slips with probability \(p\)
- consume yields only a fraction of visible resource with probability \(q\)
- post-action local resource layout fluctuates around a stable mean

#### This is a genuinely good fit

Now the prediction system has something real to learn:

- not raw local attractiveness alone
- but local action reliability

#### Toy movement example

Suppose in context \(s\), `UP` looks good from hunger, but slips 40% of the time.

Observed next-state outcomes for repeated `UP` attempts may average to:

\[
q(s,UP) \approx (0.25, 0.30, 0.00, 0.00, 0.00)
\]

instead of the naive optimistic outcome:

\[
(0.60, 0.10, 0.00, 0.00, 0.00)
\]

Now repeated disappointment is not a conceptual error. It really is:

> this action in this local context is less reliable than it appears

```text
Stochastic-transition intuition

Same local context s, same action UP

trial 1 -> good landing / good next local state
trial 2 -> slip / weak next local state
trial 3 -> good landing / good next local state
trial 4 -> slip / weak next local state

Prediction can learn the average reliability of UP in that context.
```

#### Verdict

**Strong fit**. This is one of the clearest world classes where the current
prediction system should produce a meaningful advantage.

### Case F: Deceptive Local Attractors

#### Description

A local observation can appear attractive but tends to lead into poor next-step
resource states.

Example patterns:

- apparent rich neighbor that often collapses after entry
- local corridor that looks promising but systematically channels into sparse outcomes
- consume opportunities that visually look similar but differ in realized yield

#### Why this helps prediction

This is exactly the kind of local mismatch the system is designed to absorb.

#### Toy example

Suppose `RIGHT` looks attractive with raw hunger score:

\[
h_t(RIGHT)=0.7
\]

But repeated post-action observations produce large negative surprise:

\[
\varepsilon_t^- \in \{0.2,0.3,0.25,0.28,\dots\}
\]

Then frustration for `(s, RIGHT)` grows, which dampens that action.

```text
Deceptive-local-attractor intuition

visible now:         action seems attractive
realized next step:  local outcome repeatedly disappointing

appearance  ---------------->  optimistic baseline score
experience  ---------------->  growing frustration for (s, RIGHT)
combined    ---------------->  damped future RIGHT tendency
```

#### Caveat

This only works if the deception is a stable contextual property, not merely a
by-product of depletion history.

#### Verdict

**Potentially strong fit**, but only if the deceptiveness is structurally local
and recurring rather than hidden-state aliasing.

### Case G: Blockade / Obstacle Worlds

#### Description

Some directions are blocked, constrained, or often fail due to local geometry.

#### When prediction helps

If the blockade effect is not perfectly explicit in the current observation but
is locally regular, prediction may learn that certain actions under-deliver in
certain local contexts.

#### When prediction does not help

If obstacles are already fully and cleanly represented in the observation used
for baseline scoring, then the baseline policy may already account for them,
leaving little room for improvement.

#### Verdict

**Moderate fit at best**, heavily dependent on whether obstacle consequences are
partially hidden or merely explicit.

### Case H: Long-Horizon Sparse-Benefit Worlds

#### Description

A move may look weak locally but open access to better resources several steps
later.

#### Why current prediction struggles

The system only learns from the immediate next local observation, not from long
future returns.

So if the benefit is delayed beyond one step and not visible in \(y_{t+1}\), the
current prediction system cannot exploit it well.

#### Verdict

**Poor fit**. This is outside the competence of the current design.

## 5. Why Earlier Experiments May Have Shown No Clear Advantage

Given the analysis above, null or weak results are not surprising if earlier
worlds were mostly:

- simple
- deterministic or near-deterministic
- heavily driven already by local resource magnitude
- affected by depletion/revisit aliasing
- not rich in stable local stochastic reliability structure

In that regime, prediction either:

1. relearns what the current observation already says
2. averages together incompatible hidden cases
3. produces frustration from world-history effects rather than true local action unreliability
4. has too little room to improve survival beyond the baseline

That would naturally explain why no robust advantage emerged.

## 6. Practical Alignment with Existing AXIS Worlds

Here is a provisional alignment against the current world families.

### Uniform resources

Expected fit: **very low**

Reason:
- little local structure beyond what the current observation already exposes

### Clustered resources

Expected fit: **weak / fragile**

Reason:
- patch-edge regularities may help a little
- depletion/revisit aliasing may erase or corrupt that benefit

### Cooldown / regeneration worlds

Expected fit: **often poor**

Reason:
- hidden regrowth phase can break local context consistency

### Blockade worlds

Expected fit: **conditional**

Reason:
- helpful only if action unreliability is learned rather than already directly visible

### Simple 2D local worlds with deterministic movement and consumption

Expected fit: **negligible**

Reason:
- current observation already nearly determines the next useful choice

```text
World-fit summary

uniform resources                 -> prediction-neutral
clustered + depletion             -> prediction-fragile
cooldown / hidden regrowth        -> often prediction-misleading
deterministic local transitions   -> prediction-redundant
stochastic local transitions      -> prediction-favorable
local deceptive transitions       -> prediction-favorable
long-horizon delayed benefit      -> outside current prediction competence
```

## 7. Interim Conclusion

The current prediction system is not obviously wrong, but it is specialized.

It is best suited to worlds with:

- recurring local contexts
- mild to moderate stochasticity
- stable local transition regularities
- action reliability differences that are not trivially visible at decision time

It is poorly suited to worlds dominated by:

- hidden depletion history
- hidden regrowth phase
- long-horizon benefit structure
- near-deterministic local transitions
- overly simple resource landscapes

This strongly suggests that the lack of robust benefit in earlier experiments
may reflect a real world-model mismatch rather than an implementation bug.

## 8. What to Do Before Neuralizing

Before any neural version is pursued, the explicit system should first be
clarified and tested against the existing worlds.

The immediate research path should be:

1. determine whether the current prediction system can help in the current
   worlds at all
2. identify whether small refinements to context or outcome definition could
   make it materially better aligned
3. only then consider neural approximation of the prediction layer

That means the initiative should be understood as having two phases.

### Phase A: Analysis and evaluation of the existing explicit system

Questions:

- Can the current system in principle help on the current world families?
- Are null results expected from theory?
- Which failure modes dominate: redundancy, aliasing, non-stationarity, or horizon mismatch?
- Can the explicit system be improved without changing its basic philosophy?

### Phase B: Neural extension of the prediction layer

Questions:

- If a refined explicit predictor still has genuine value, can a neural version
  extend it?
- Which parts should remain explicit and which should become learned function approximation?
- Can a neural predictor reduce aliasing or improve generalization without destroying interpretability?

## 9. Concrete Follow-Up Questions

The next useful questions are:

1. Can we define world variants where the current explicit predictor *should*
   help, so that the mechanism gets a fair test?
2. Can we characterize which existing world settings are provably or strongly
   prediction-neutral?
3. Should context encoding be extended to include visible depletion-relevant or
   history-relevant variables?
4. Should outcome definitions in System C and C+W be revised so they better
   capture what actually matters behaviorally?
5. Should the current prediction system remain local one-step trust learning,
   or should the concept itself be reconsidered?
