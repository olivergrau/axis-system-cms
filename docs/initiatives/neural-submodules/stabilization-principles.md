# Stabilization Principles for Neural Submodules in AXIS

## Why Stabilization Is the Central Problem

If AXIS integrates neural modules with online learning, then the main
difficulty is not raw implementation. The main difficulty is preserving
coherent behavior while the module is adapting inside the same closed
perception-action loop that it helps shape.

A neural component that updates continuously can easily become unstable,
forgetful, self-reinforcing, or behaviorally opaque. Nature suggests that
adaptive systems remain viable not because they learn without constraint, but
because plasticity is bounded, localized, filtered, and layered across
timescales.

AXIS should therefore adopt stabilization principles from the start rather than
adding them as a late patch.

## AXIS Already Has Structural Advantages

The existing framework already contains several stabilizing ideas in explicit form:

- state is decomposed into interpretable variables
- drives remain explicit rather than hidden in a large latent vector
- behavior is mediated through bounded action sets
- systems can be reduced to simpler baselines
- experiments are run in small, controlled worlds

This matters because stabilization should not rely only on optimizer tricks. It
should also come from architectural constraints.

## Principle 1: Plasticity Must Be Local

Not every part of the system should learn all the time.

A neural submodule should have a narrow responsibility, for example:

- predicting local outcome of a state-action pair
- estimating novelty or uncertainty for a specific drive
- refining a bounded action preference vector

This limits the blast radius of bad updates.

In AXIS terms: first learn subfunctions, not the whole agent.

## Principle 2: Fast Expression, Slow Structural Change

Biological systems appear to combine rapid state changes with slower
consolidation. AXIS should reflect that distinction.

Let:

- \(h_t\) be a fast adaptive state
- \(\theta_t\) be slower structural parameters

Then the system may update both, but at different rates:

\[
h_{t+1} = \Phi(h_t, x_t, y_t)
\]

\[
\theta_{t+1} = \theta_t - \eta_\theta \, g_t \, \nabla_\theta \mathcal{L}_t
\]

with small \(\eta_\theta\) and possibly sparse gating term \(g_t\).

This means the agent can adapt immediately through state while changing its
long-term structure more cautiously.

## Principle 3: Learning Must Be Gated

Plasticity should not be always-on. Updates should depend on conditions such as:

- sufficiently strong prediction error
- novelty threshold exceeded
- stable enough context
- non-saturated drive regime
- explicit learning-enabled configuration

A simple gating form is:

\[
g_t = \mathbf{1}[\varepsilon_t > \tau]
\]

or a softened version:

\[
g_t = \sigma\left(\alpha (\varepsilon_t - \tau)\right)
\]

where \(\varepsilon_t\) is prediction error.

This prevents tiny fluctuations from rewriting the model continuously.

## Principle 4: Behavioral Influence Must Be Bounded

A neural submodule should not get unlimited authority over action. Its outputs
should be passed through bounded interfaces.

For example, if a neural predictor modulates action preferences, then its
effect should be clipped, tempered, or mixed with explicit baseline scores:

\[
s_t(a) = s_t^{base}(a) + \lambda \cdot \mathrm{clip}(m_t(a), -\delta, \delta)
\]

with bounded \(\delta\).

This ensures that learning errors produce biased behavior, not catastrophic
action collapse.

## Principle 5: Keep a Reduction Path

Every neuralized subsystem should admit reduction to a simpler non-neural
baseline.

This is critical scientifically and operationally.

Scientifically:

- we can compare whether the neural version adds anything meaningful
- we can isolate where behavior differences come from

Operationally:

- we can fall back when learning destabilizes
- we retain a debuggable baseline

In practice, this means the manual System C predictor should remain a first
comparison target for a neural System C predictor.

## Principle 6: Preserve Explicit Error Signals

Prediction error, novelty-like quantities, and drive-relevant discrepancies
should remain explicit if possible.

The neural module may approximate a function, but the system should still
expose quantities such as:

- prediction
- realized outcome
- error magnitude
- modulation contribution
- update trigger

This preserves inspectability and keeps the module scientifically usable inside
AXIS experiments.

## Principle 7: Separate Runtime State from Learned Parameters

A neural module inside AXIS may contain:

- learned weights
- transient hidden state
- optimizer state
- online memory or replay buffers

These should not be conflated.

The framework should distinguish:

- what defines the model structurally
- what belongs to the momentary run state
- what is auxiliary training state

This improves persistence, visualization, and experimental control.

## Principle 8: Prefer Small Modules and Controlled Worlds First

Early experiments should use:

- small networks
- short horizons
- single-task submodules
- bounded action spaces
- controlled comparisons against explicit baselines

AXIS should first answer whether neural submodules improve a known explicit
mechanism, not whether giant learned agents can dominate a toy world.

## Principle 9: Stabilization Is Architectural, Not Only Optimizer-Level

Classical ML stabilization tools are still useful:

- replay buffers
- target networks
- gradient clipping
- normalization
- regularization
- conservative learning rates

But AXIS should not rely on these alone. The stronger form of stabilization is
architectural:

- explicit loop placement
- bounded behavioral influence
- local responsibility
- slow structural updates
- transparent diagnostic variables

## A First AXIS Pattern

A good first pattern for neural submodules in AXIS would be:

1. keep the global system explicit
2. neuralize only the predictor
3. expose prediction error explicitly
4. gate updates by error and cadence
5. clip modulation influence on action
6. preserve a manual baseline for direct comparison

This is conservative, but that is a strength. It keeps the scientific signal
visible.

## Conclusion

Online-learning neural modules are plausible in AXIS, but only if stabilization
is treated as a primary design concern.

The correct model is not "insert a network and let it learn everything." The
correct model is "embed a narrowly scoped adaptive module inside a structured,
bounded, and inspectable cognitive loop."
