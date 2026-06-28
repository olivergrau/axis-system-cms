# Online Learning and Immediate Use

## Core Question

AXIS agents interact with the world continuously. They do not naturally split
into a separate training phase and inference phase. This raises a central
technical question:

Can a neural submodule learn while the agent is acting, and can the updated
knowledge be used immediately in subsequent decisions?

The answer is yes in principle. Modern neural systems can be used in this way.
But this only works if the learning process is constrained carefully enough to
avoid destabilizing behavior.

## What "Online Learning" Means Here

In this initiative, online learning means:

- the module receives experience during normal agent-world interaction
- parameter updates happen during the run, not only before or after it
- later actions can depend on weights that were changed by earlier steps in the same run

Formally, if a neural submodule has parameters \(\theta_t\), then a step can
look like this:

\[
y_t = f_\theta(x_t)
\]

\[
\theta_{t+1} = \theta_t - \eta \nabla_\theta \mathcal{L}_t
\]

and then the next behavioral step already uses \(\theta_{t+1}\):

\[
y_{t+1} = f_{\theta_{t+1}}(x_{t+1})
\]

This is immediate-use learning.

## This Is Technically Possible Today

Nothing in current ML technology prevents this.

It can be implemented with:

- per-step or mini-batch gradient updates
- replay-buffer-supported online updates
- eligibility-style short-term traces
- slowly updated target networks
- mixed fast and slow parameter components

Reinforcement learning already contains many partial examples of this idea. The
difference is that AXIS would not treat the whole agent as a monolithic RL
policy. Instead, the neural component would live inside an otherwise explicit
system loop.

## Why This Is Difficult

Online immediate-use learning is possible, but dangerous. The main problems are:

1. Instability
   If the module changes too much in one step, behavior can swing abruptly.

2. Forgetting
   New experience can overwrite old regularities too quickly.

3. Self-reinforced error
   The module can shape its own future data distribution, which may amplify bad
   predictions or maladaptive routines.

4. Non-stationarity
   The agent changes while the world interaction also changes, so the learning
   target itself is moving.

5. Behavioral coupling
   A predictor is not passive. If its outputs modulate action, then learning
   changes behavior and behavior changes future learning.

## Why AXIS Is Actually a Good Place to Study This

AXIS already imposes useful structure:

- the loop is explicit
- drives are explicit
- arbitration is explicit
- many systems already expose interpretable internal quantities
- the worlds are small and controllable

This means neural online learning can be embedded inside a scaffold that is far
more analyzable than a generic end-to-end agent.

In other words, AXIS is a good testbed precisely because it is not a black-box
RL platform.

## Operational Regimes

Several regimes are possible.

### 1. Stepwise Immediate Update

Every step performs:

1. forward pass
2. action selection or modulation
3. environment transition
4. error computation
5. backward/update

This is closest to biological continuous adaptation, but also the most fragile.

### 2. Interleaved Micro-Batch Update

The agent acts for a small number of steps, stores transitions, and updates the
neural module every \(k\) steps.

This reduces oscillation while still keeping learning online.

### 3. Dual-Timescale Update

A fast state adapts immediately, while slower weights consolidate less often.

This better matches biological intuitions and may be the best long-term fit for
AXIS.

## Most Plausible AXIS Interpretation

The most plausible first AXIS implementation is not unrestricted per-step
gradient descent on a large policy network. It is something narrower:

- a small neural predictor or scoring module
- bounded influence on action selection
- slow update rates
- explicit exposure of prediction error and confidence-like quantities
- optional replay or smoothing to reduce variance

## Biological Orientation

Real biological systems do not appear to separate life into "training mode" and
"inference mode". They act, adapt, stabilize, forget selectively, consolidate,
and re-use what was just learned.

But they also do not change everything all at once. They rely on multiple
stabilizing mechanisms:

- locality of plasticity
- multiple time scales
- gated adaptation
- bounded expression
- structural persistence beneath short-term fluctuation

This should guide AXIS more than the naive machine-learning picture of one
large network learning everything end-to-end in a single loop.

## Immediate Engineering Consequence

The framework should assume that a neural submodule may need:

- persistent parameters
- transient online-learning state
- optional optimizer state
- explicit configuration for update cadence and learning rate
- visualization hooks for prediction error, confidence, or adaptation pressure

## Conclusion

Yes, AXIS can support neural modules that learn and immediately use what they
learned during the same run.

But this should not be treated as a trivial drop-in. It only becomes useful if
the neural submodule is introduced with structural safeguards and explicit
behavioral boundaries.

That leads directly to the next question: which stabilization principles should
govern such modules inside AXIS?
