# Manual vs Neural Predictor in System C and C+W

## Why System C Is the Right First Target

System C and System C+W already place prediction at the center of behavior.
They are therefore the most natural systems for a first neural submodule.

This is much better than trying to neuralize the whole agent immediately,
because the predictor is already:

- conceptually isolated
- mathematically explicit
- behaviorally meaningful
- easy to compare against a baseline

The key idea is simple: retain the rest of the system loop, but replace the
manual predictor with a neural approximator.

## Existing Manual Predictor in System C

System C uses local predictive memory over state-action pairs. The agent keeps
explicit estimates associated with each visited context.

Conceptually, for a given local state-action pair \((s_t, a_t)\), the system stores:

- expected outcome or value-like expectation \(q_t(s_t, a_t)\)
- frustration trace \(f_t(s_t, a_t)\)
- confidence or confirmation trace \(c_t(s_t, a_t)\)

A generic update picture is:

\[
q_{t+1}(s_t, a_t) = (1-\eta_q)\,q_t(s_t, a_t) + \eta_q\,y_{t+1}
\]

\[
f_{t+1}(s_t, a_t) = (1-\eta_f)\,f_t(s_t, a_t) + \eta_f\,\varepsilon_t^{-}
\]

\[
c_{t+1}(s_t, a_t) = (1-\eta_c)\,c_t(s_t, a_t) + \eta_c\,\varepsilon_t^{+}
\]

where:

- \(y_{t+1}\) is the realized outcome signal
- \(\varepsilon_t^{-}\) is a negative prediction discrepancy component
- \(\varepsilon_t^{+}\) is a positive or confirming discrepancy component

These quantities then modulate action preferences. A simplified modulation view is:

\[
m_t(a) = \lambda_+\,c_t(s_t,a) - \lambda_-\,f_t(s_t,a)
\]

and the resulting action score becomes:

\[
s_t(a) = s_t^{base}(a) + m_t(a)
\]

followed by policy normalization or arbitration.

The important point is that prediction is explicit, local, and interpretable.

## Existing Manual Predictor in System C+W

System C+W generalizes this structure across a richer system with hunger and
curiosity-related pressures. The predictor still serves as an explicit memory
of expected outcomes, but now its consequences are distributed across a broader
motivational architecture.

The predictor can influence:

- hunger-relevant trust or avoidance
- curiosity-related attraction to uncertain or informative transitions
- shared modulation of action selection

So the predictor is still local and interpretable, but it participates in a
more layered motivational loop.

## What a Neural Predictor Would Replace

A neural predictor would replace the hand-maintained mapping from local context
to predictive quantities.

Instead of explicit tables or manually updated local traces, we would define a function:

\[
\hat{z}_t = f_\theta(x_t)
\]

where:

- \(x_t\) encodes the relevant local context
- \(\hat{z}_t\) contains predicted outputs
- \(\theta\) are learnable parameters

Depending on design choice, \(\hat{z}_t\) could contain:

- predicted next outcome value
- predicted reduction in hunger-related error
- predicted novelty or confirmation
- uncertainty proxy
- separate channels for positive and negative expectation

The simplest first version would be to predict the same core quantity the
manual predictor already tracks, so comparison remains clean.

## Input Design

For System C, a reasonable input vector \(x_t\) might include:

- local observation features
- current action candidate identity
- drive-relevant scalar state such as energy or hunger proxy
- optional short-term contextual features

For System C+W, the input may also include:

- curiosity-relevant state
- local map or memory-derived features
- uncertainty-related summary variables

The important constraint is that the input should remain scientifically legible.
A compact, explicit feature vector is preferable to large opaque raw encodings
in the first AXIS neural systems.

## Output Design

Several output designs are possible.

### Option 1: Predict One Scalar Outcome

The network predicts a single expected outcome:

\[
\hat{y}_{t+1} = f_\theta(x_t)
\]

Error becomes:

\[
\varepsilon_t = y_{t+1} - \hat{y}_{t+1}
\]

This is the cleanest first move.

### Option 2: Predict Multi-Channel Behavioral Signals

The network predicts a vector:

\[
(\hat{q}_t, \hat{f}_t, \hat{c}_t) = f_\theta(x_t)
\]

This moves closer to the current manual decomposition, but also introduces more
modeling freedom and more ambiguity.

### Option 3: Predict Modulation Directly

The network predicts the modulation term \(m_t(a)\) itself.

This is operationally simple, but scientifically weaker because it hides more
of the internal semantics.

For AXIS, Option 1 is the strongest initial choice.

## Learning Dynamics

A neural predictor would update online from prediction error:

\[
\mathcal{L}_t = \ell\big(f_\theta(x_t), y_{t+1}\big)
\]

\[
\theta_{t+1} = \theta_t - \eta\,\nabla_\theta \mathcal{L}_t
\]

possibly with:

- sparse update cadence
- replay support
- target smoothing
- gated plasticity
- gradient clipping

This differs from the current manual predictor in an important way: the model
can generalize across contexts rather than storing each state-action estimate
independently.

## What We Gain

A neural predictor may provide:

- generalization across similar contexts
- smoother interpolation between rarely visited states
- compact representation of richer regularities
- a natural path toward larger or noisier worlds

This is especially relevant once explicit local tables or simple traces become
too brittle or too sparse.

## What We Lose or Risk

Replacing the manual predictor also sacrifices important properties:

- exact local interpretability weakens
- updates become less transparent
- bad generalization can affect multiple contexts at once
- instability and forgetting become real risks

So the neural predictor should be treated as a scoped experiment, not as an
automatic upgrade.

## Scientific Implications

This replacement changes the scientific meaning of the system.

Manual System C says:

- the predictive structure is explicit and local
- behavior emerges from directly inspectable traces

Neural System C would instead say:

- the predictive function is learned and distributed
- behavior still emerges through explicit drives and arbitration, but one core
  internal mapping is now adaptive and approximated

This is still scientifically useful, but it shifts part of the system from
explicit mechanistic form toward controlled function approximation.

## Engineering Implications

Introducing a neural predictor requires the framework to support:

- model parameter persistence
- runtime hidden state if needed
- optimizer state if online learning is enabled
- configuration of update cadence and learning rate
- inspection and visualization hooks for prediction error and predictor output
- comparison against the manual baseline predictor

This does not require end-to-end neural infrastructure. It requires a clean,
bounded neural submodule interface.

## Recommended First Neural Variant

The most defensible first neural version is:

1. start from System C, not C+W
2. keep the full explicit loop unchanged
3. replace only the predictor
4. predict one scalar outcome first
5. derive error explicitly
6. bound the modulation effect on action
7. compare directly against the manual predictor baseline

Then, once that is understood, extend the same idea to C+W.

## Conclusion

System C and C+W already contain the right seam for neural augmentation. The
predictor is explicit enough to define scientifically, but central enough that
replacing it could produce meaningful behavioral differences.

That makes the predictor the correct first neural submodule in AXIS.
