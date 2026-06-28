# Prediction System Recap

This document is a focused re-entry guide into the current AXIS prediction
system. It is written to help a scientifically and mathematically oriented
reader rebuild the full picture quickly after some time away from the codebase.

The emphasis is on the existing explicit prediction system used by System C and
extended by System C+W.

See also:

- [System C Cheat Sheet](../../cheat-sheets/system-c.md)
- [System C+W Cheat Sheet](../../cheat-sheets/system-cw.md)
- [Prediction](../../construction-kit/prediction.md)
- [Traces](../../construction-kit/traces.md)
- [Modulation](../../construction-kit/modulation.md)
- [Tutorial: Understanding Prediction-Error-Driven Behavior](../../tutorials/prediction-error-tutorial.md)

## 1. The Big Picture

The prediction system adds a second adaptive stream on top of the base drives.

The base drives still generate the raw action tendencies:

- in System C: hunger only
- in System C+W: hunger and curiosity

Prediction does **not** replace these drives. Instead, it learns whether a
specific action in a specific local context tends to be more reliable or more
disappointing than expected.

So the system has two layers:

1. a base motivational layer
2. a prediction-derived trust layer

The trust layer is built from repeated mismatches between:

- what the system predicted would happen
- what actually happened

Those mismatches are split into:

- negative surprise, which drives frustration
- positive surprise, which drives confidence

Over time, this changes which actions the agent tends to trust locally.

```text
Base drives                 Prediction layer
-----------                ---------------------------
hunger / curiosity  --->   predict -> compare -> trace
      |                              |
      v                              v
 raw action scores           frustration / confidence
      |                              |
      +------------- combine / modulate -------------> final action scores
```

## 2. What the System Predicts

The prediction system is not a global world model. It is a local predictive
memory indexed by discrete context and action.

Formally:

\[
q_t(s,a) = \hat y_{t+1}^{(s,a)}
\]

This means:

- the current local context is encoded as \(s\)
- for each possible action \(a\), the system stores an expected next feature vector

So the prediction memory does not answer:

> "What will happen in the world in general?"

It answers:

> "If I do action \(a\) in local context \(s\), what local sensory outcome do I expect next?"

```text
                predictive memory q

        context s0                context s1
      +----------------+       +----------------+
UP    | y_hat(s0,UP)   |       | y_hat(s1,UP)   |
DOWN  | y_hat(s0,DOWN) |       | y_hat(s1,DOWN) |
LEFT  | y_hat(s0,LEFT) |       | y_hat(s1,LEFT) |
RIGHT | y_hat(s0,RIGHT)|       | y_hat(s1,RIGHT)|
...   | ...            |       | ...            |
      +----------------+       +----------------+

lookup key during the step: (s_t, a_t)
```

## 3. System C: The Predictive Feature Vector

In System C, the predicted feature vector is resource-centered:

\[
y_t = (r_c, r_u, r_d, r_l, r_r)
\]

where:

- \(r_c\): resource on the current cell
- \(r_u\): resource above
- \(r_d\): resource below
- \(r_l\): resource left
- \(r_r\): resource right

So System C predicts the *next local resource layout* after an action.

This is important:

- prediction is not abstract reward prediction
- prediction is not a scalar value function
- prediction is local sensory expectation over resource features

## 4. From Observation to Context

The current local feature vector is mapped into a discrete context:

\[
s_t = C(y_t)
\]

In System C, this is a 5-bit binarized encoding over thresholded resource
presence. So many similar local situations collapse into the same context.

This gives the prediction system its character:

- explicit
- local
- quantized
- memory-efficient

and also limited:

- no planning rollout
- no continuous latent representation
- no global spatial state

## 5. The Per-Step Prediction Loop

The predictive part of a step looks like this:

1. observe the current local features \(y_t\)
2. encode them into a context \(s_t\)
3. select an action \(a_t\)
4. retrieve the predicted next features \(\hat y_{t+1} = q_t(s_t,a_t)\)
5. execute the action
6. observe the actual next features \(y_{t+1}\)
7. compare prediction and reality
8. update predictive memory
9. update frustration/confidence for \((s_t,a_t)\)
10. use these traces later to modulate action scores

So prediction is retrospective:

- first the system acts
- then it sees whether the outcome confirmed or disappointed the expectation

```text
 y_t -> context s_t -> choose a_t -> retrieve y_hat_{t+1}
                                |
                                v
                           execute action
                                |
                                v
                         observe actual y_{t+1}
                                |
                                v
                 compare y_{t+1} with y_hat_{t+1}
                                |
               +----------------+----------------+
               |                                 |
               v                                 v
         update q(s_t,a_t)                 update traces
```

## 6. Memory Update

After the next observation is available, the prediction memory is updated by
an exponential moving average:

\[
q_{t+1}(s_t,a_t)
=
(1-\eta_q)\,q_t(s_t,a_t)
+
\eta_q\,y_{t+1}
\]

Interpretation:

- \(\eta_q\) small: slow, stable learning
- \(\eta_q\) large: fast, reactive learning

So the memory gradually tracks what tends to happen after an action in that
context.

## 7. Prediction Error: The Central Quantity

Once the system has both:

- prediction \(\hat y_{t+1}\)
- observation \(y_{t+1}\)

it computes a component-wise mismatch.

The signed raw error would be:

\[
\delta_t = y_{t+1} - \hat y_{t+1}
\]

But the actual AXIS design immediately splits this into positive and negative
parts.

## 8. Positive and Negative Surprise

Component-wise:

\[
\delta_{t,j}^+ = \max(y_{t+1,j} - \hat y_{t+1,j}, 0)
\]

\[
\delta_{t,j}^- = \max(\hat y_{t+1,j} - y_{t+1,j}, 0)
\]

This means:

- \(\delta^+\): the world was better, richer, or stronger than expected on that feature
- \(\delta^-\): the world was poorer, weaker, or more disappointing than expected on that feature

In System C this is directly about local resource structure.

### Resource interpretation

If the system predicted a high resource value on a feature but actually saw a
low one, then:

- negative surprise increases
- that context-action pair becomes more frustrating over time

If it predicted a low resource value but actually saw a high one, then:

- positive surprise increases
- that context-action pair becomes more confidence-inducing over time

So yes: in System C, surprise is directly tied to how the local *resource
configuration* after the action compares to the expected one.

```text
per feature j:

expected:   y_hat_j ----->
observed:   y_j      ----->

case 1: y_j > y_hat_j   -> positive surprise  delta_j^+ > 0, delta_j^- = 0
case 2: y_j < y_hat_j   -> negative surprise  delta_j^- > 0, delta_j^+ = 0
case 3: y_j = y_hat_j   -> no surprise        delta_j^+ = delta_j^- = 0
```

## 9. Scalar Error Aggregation

The system does not feed the full error vector directly into the traces.
Instead, it aggregates the positive and negative channels separately:

\[
\varepsilon_t^+ = \sum_j w_j^+ \, \delta_{t,j}^+
\]

\[
\varepsilon_t^- = \sum_j w_j^- \, \delta_{t,j}^-
\]

So there is no single undifferentiated prediction-error scalar in the current
system. There are two distinct scalar channels:

- \(\varepsilon_t^+\): positive surprise
- \(\varepsilon_t^-\): negative surprise

These weights define which feature dimensions matter most when the system says:

- "this outcome was better than expected"
- "this outcome was worse than expected"

In System C, the current-cell feature typically has the largest weight, and the
neighbor features share the rest.

```text
feature channels:   [ current |   up   |  down  |  left  | right ]
weights example:    [  0.50   | 0.125  | 0.125  | 0.125  | 0.125 ]
                      ^
                      |
          current-cell outcome usually matters most
```

## 10. Frustration and Confidence

This is the key point.

Frustration and confidence are not direct one-step emotions. They are local
adaptive traces over repeated prediction errors.

For the active context-action pair \((s_t,a_t)\):

\[
f_{t+1}(s_t,a_t) = (1-\eta_f)\,f_t(s_t,a_t) + \eta_f\,\varepsilon_t^-
\]

\[
c_{t+1}(s_t,a_t) = (1-\eta_c)\,c_t(s_t,a_t) + \eta_c\,\varepsilon_t^+
\]

Interpretation:

- frustration accumulates disappointment and unreliability
- confidence accumulates positive confirmation and unexpectedly good outcomes

Important properties:

- traces are **local** to `(context, action)`
- they are **EMA traces**, not counters
- only the currently experienced `(s_t, a_t)` pair is updated
- all other pairs remain unchanged in that step

So the system learns local predictive trust, not global action reputation.

```text
trace table (conceptual)

(context, action)   frustration   confidence
--------------------------------------------
(s=12, UP)            0.19          0.10
(s=12, LEFT)          0.02          0.21
(s=7, CONSUME)        0.00          0.34

Only the active row for (s_t, a_t) is updated in the current step.
```

## 11. Intuition of the Trace Pair

A useful interpretation is:

- frustration answers: "How often did this action under-deliver here?"
- confidence answers: "How often did this action over-deliver here?"

This gives a simple but powerful local adaptation mechanism.

The base drive may say:

> "Moving right looks attractive because food might be there."

The prediction layer may answer:

> "Yes, but in this kind of local context, moving right has repeatedly disappointed me."

or:

> "In this kind of local context, moving right has often turned out better than expected."

That is the real role of the prediction system.

## 12. From Traces to Action Modulation

The traces do not directly choose actions. They modulate the existing base
scores.

For each action:

\[
\sigma_t(a) = \lambda_+\,c_t(s_t,a) - \lambda_-\,f_t(s_t,a)
\]

\[
\tilde \mu_t(a) = \exp(\sigma_t(a))
\]

\[
\mu_t(a) = \mathrm{clip}(\tilde \mu_t(a), \mu_{\min}, \mu_{\max})
\]

Interpretation:

- more confidence pushes \(\mu_t(a)\) upward
- more frustration pushes \(\mu_t(a)\) downward

In multiplicative mode, positive base scores are multiplied by \(\mu_t(a)\),
while negative base scores are divided by \(\mu_t(a)\) so the sign semantics
stay consistent.

So prediction does not create a separate drive. It reshapes the expression of
existing drives.

```text
base score h(a)
    |
    v
trace evidence:  + lambda_+ * confidence
                 - lambda_- * frustration
    |
    v
sigma(a) -> mu(a) -> modulated score

confidence  -> tends to increase action expression
frustration -> tends to decrease action expression
```

## 13. A Full Mini Example

Assume the current local observation is:

\[
y_t = (0.2, 0.8, 0.1, 0.0, 0.0)
\]

Interpretation:

- current cell has little resource
- upward neighbor looks promising
- downward has a little
- left and right have none

```text
Local 3x3 intuition before the action

          [ UP:    0.8 ]
[ LEFT: 0.0 ] [ AGENT: 0.2 ] [ RIGHT: 0.0 ]
         [ DOWN:  0.1 ]

Chosen action: UP

So the agent currently sits on a weak cell, but sees a much stronger resource
signal directly above.
```

The context encoder maps this to some discrete context \(s_t\).

Suppose the chosen action is `UP` and the stored prediction for this
context-action pair is:

\[
\hat y_{t+1} = (0.6, 0.3, 0.1, 0.0, 0.0)
\]

After moving, the actual next observation is:

\[
y_{t+1} = (0.8, 0.9, 0.0, 0.0, 0.0)
\]

### Step 1: Positive and negative component errors

Component-wise:

\[
\delta_t^+ = \max(y_{t+1} - \hat y_{t+1}, 0) = (0.2, 0.6, 0.0, 0.0, 0.0)
\]

\[
\delta_t^- = \max(\hat y_{t+1} - y_{t+1}, 0) = (0.0, 0.0, 0.1, 0.0, 0.0)
\]

Interpretation:

- the new current-cell feature was better than expected
- the upward-neighbor feature was much better than expected
- the downward feature under-delivered a little

### Step 2: Aggregate to scalar surprise

Use the default System C-style weights:

\[
w^+ = w^- = (0.5, 0.125, 0.125, 0.125, 0.125)
\]

Then:

\[
\varepsilon_t^+ = 0.5\cdot0.2 + 0.125\cdot0.6 + 0.125\cdot0.0 = 0.175
\]

\[
\varepsilon_t^- = 0.5\cdot0.0 + 0.125\cdot0.0 + 0.125\cdot0.1 = 0.0125
\]

So this step was overall more confirming than disappointing.

### Step 3: Update frustration and confidence

Assume the old trace values for `(s_t, UP)` were:

\[
f_t = 0.20, \qquad c_t = 0.10
\]

and the rates are:

\[
\eta_f = 0.2, \qquad \eta_c = 0.15
\]

Then:

\[
f_{t+1} = 0.8\cdot0.20 + 0.2\cdot0.0125 = 0.1625
\]

\[
c_{t+1} = 0.85\cdot0.10 + 0.15\cdot0.175 = 0.11125
\]

So in this concrete step:

- frustration decreases because the action under-delivered only slightly
- confidence increases because the realized outcome was better than expected on the most important channels
- the pair may still remain somewhat mistrusted overall because older frustration is still present

### Step 4: Modulate future action scores

Assume:

\[
\lambda_+ = 1.0, \qquad \lambda_- = 1.5
\]

Then:

\[
\sigma_t(UP) = 1.0\cdot0.11125 - 1.5\cdot0.1625 = -0.1325
\]

\[
\mu_t(UP) = \exp(-0.1325) \approx 0.876
\]

So a future positive base score for `UP` would still be reduced, but only by
about 12.4% in multiplicative mode.

This is the operational meaning of prediction-derived inertia: one confirming
step can weaken prior distrust without erasing it immediately.

```text
example causal chain

move UP in context s_t
        -> observed outcome confirms the move overall
        -> epsilon^+ dominates epsilon^-
        -> old frustration is reduced, but still stays higher than confidence
        -> sigma(UP) becomes negative
        -> mu(UP) < 1
        -> future UP scores are suppressed in this local context
```

## 14. What System C+W Changes

System C+W keeps the same general machinery but changes the semantics.

It still has:

- one shared predictive memory
- context-action indexed prediction
- positive/negative error splitting
- EMA-based frustration/confidence traces
- action-score modulation

But it interprets the predictive outcome in two separate ways:

- hunger-side predictive outcome
- curiosity-side predictive outcome

So C+W does **not** just have one pair of traces. It has two:

- hunger frustration/confidence
- curiosity frustration/confidence

That means the same predictive memory can support two different motivational
interpretations.

This is one of the conceptually important jumps from C to C+W.

## 15. What the Prediction System Is Really Doing

The cleanest summary is this:

The system is learning local action trust.

Not trust in a symbolic sense, but operationally:

- which actions in which local situations tend to under-deliver
- which actions in which local situations tend to over-deliver

This is why the prediction system is useful even though it is mathematically
simple.

It adds a memory of local reliability on top of the raw drive structure.

## 16. Mental Model to Keep

If you want one compact mental model, use this:

1. the drive says what the agent wants
2. the predictor says what the agent expects
3. prediction error says how reality differed
4. frustration remembers repeated disappointment
5. confidence remembers repeated positive confirmation
6. modulation changes how strongly actions are expressed next time

That is the current AXIS prediction system in one chain.

```text
wanting      expecting       comparing        remembering        acting next time
------       ---------       ---------        -----------        ----------------
drive   ->   prediction  ->  error split  ->  traces       ->   score modulation
                     y_hat      delta+/delta-    f / c             action bias
```

## 17. Why This Matters for Neural Extensions

This recap also reveals the right replacement seam for future neural work.

The current explicit system already separates:

- context encoding
- predictive memory
- prediction error decomposition
- trace accumulation
- action modulation

So if a neural predictor is introduced later, the most natural first target is:

- replace the predictive memory mapping \(q(s,a)\)
- keep the rest of the scaffold explicit

That is exactly why System C is such a strong first candidate for neural
submodules.
