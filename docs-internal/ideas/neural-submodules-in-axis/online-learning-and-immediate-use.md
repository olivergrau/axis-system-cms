# Online Learning and Immediate Use in AXIS

## 1. The Core Question

AXIS agents are not naturally divided into a clean training phase and a clean
inference phase.

They:

- act in the world
- receive consequences
- update internal state
- and continue acting

This raises the first crucial question for neural submodules:

> Can a system with neural components learn and use the learned changes almost
> immediately, without a strict separation between training and inference?

The short answer is:

> Yes, this is possible with current technology, but not in the naive sense of
> “the network is training and inferring at exactly the same instant on the
> same signal path.”

What is possible is **interleaved online learning**:

1. perform inference at step $t$ using current weights $	heta_t$
2. observe the outcome
3. compute an update from the new evidence
4. obtain new weights $	heta_{t+1}$
5. use $	heta_{t+1}$ immediately at the next step

This is not a strict train/infer split. It is a rolling perception-action-
learning loop.

---

## 2. Why the Distinction Matters

When people say “training” and “inference,” they often imagine the modern
large-model workflow:

- long offline training
- frozen model deployment
- pure inference afterward

That is **not** the only way neural systems work.

Other valid regimes already exist:

- online reinforcement learning
- continual learning
- test-time adaptation
- self-supervised predictive learning during interaction

In these regimes, the model keeps changing while it is being used.

So the real question is not:

> can neural weights change while the agent is alive?

They clearly can.

The real questions are:

- how often should they change?
- from what signal should they change?
- how stable is behavior under continual change?
- how local or global is the learning update?
- how much opacity does this introduce?

---

## 3. Biological Analogy

Biological systems do not appear to have a hard “training phase” and
“deployment phase.”

They:

- act
- adapt
- reuse what was just learned
- and continue acting

However, biological learning is not best understood as “full-network
backpropagation after every action.”

It is more likely a layered mixture of:

- fast online adaptation
- slower consolidation
- local plasticity
- predictive error correction
- state-dependent modulation of learning

For AXIS, this suggests that the biologically plausible direction is **not**
to freeze all weights after a giant offline optimization and call that the
whole story.

It is more plausible to explore:

- small modules
- local learning signals
- incremental updates
- immediate reuse of updated internal models

---

## 4. What “Simultaneous” Really Means

Strict simultaneity is usually the wrong mental model.

For an interacting agent, there are at least three distinct timing regimes:

### 4.1 Frozen Inference

Weights are fixed during a run.

Learning happens only before deployment.

This is the easiest regime technically, but the least aligned with the AXIS
question.

### 4.2 Interleaved Online Learning

The agent uses current weights to act now, then updates them from the resulting
experience, then uses the updated weights on the next step.

This is the most realistic first target for AXIS.

### 4.3 Continuous Adaptation with Asynchronous Updates

One process performs inference, another process updates weights from recent
experience, and the active policy periodically receives refreshed parameters.

This is common in larger RL-style systems, but it is probably too heavy for
the first AXIS experiments.

For AXIS, “simultaneous learning and use” should therefore be read as:

> stepwise interleaving with immediate downstream behavioral consequences.

That is sufficient to capture the core phenomenon.

---

## 5. Is This Feasible with Current Technology?

Yes.

The feasibility question splits into two parts.

### 5.1 Technical Feasibility

Technically, it is already straightforward to build agents that:

- run a forward pass
- compute a loss from the result of an action
- perform a gradient update
- continue with the updated parameters

This is standard in:

- online RL
- continual learning
- predictive self-supervision
- test-time adaptation

So the answer at the engineering level is clearly yes.

### 5.2 Scientific Feasibility for AXIS

The harder question is not whether we can do it, but whether we can do it in a
way that remains useful for AXIS.

The risks are:

- unstable behavior
- catastrophic forgetting
- noisy self-generated supervision
- poor reproducibility
- loss of interpretability

So for AXIS the question is:

> can we introduce online neural adaptation while preserving a meaningful
> mechanistic explanation of the whole system?

That remains open, but it is plausible if the learned component is small and
its role is narrow.

---

## 6. Where This Fits Best in AXIS

The best fit is not a learned full policy.

The best fit is a learned **predictive submodule**.

Why?

Because prediction naturally supports online adaptation:

- observe current input
- predict next input
- compare prediction to actual outcome
- update predictor
- use improved predictor immediately on the next step

This matches the existing logic of:

- `System C`
- `System C+W`

These systems already contain:

- predictive features
- prediction error
- trace updates
- modulation logic

So the neural component would not need to invent a learning problem from
scratch. It would only replace the current explicit predictor with a learned
one.

This is the cleanest form of “learn and use at the same time” in AXIS.

---

## 7. What Should Be Avoided First

Even though online neural adaptation is feasible, several variants are poor
first choices.

### 7.1 Full End-to-End Policy Learning

This would make it hard to distinguish:

- drive effects
- modulation effects
- policy expression effects
- learning effects

all at once.

It is too large a jump.

### 7.2 Large Recurrent Memory Models

These may eventually be useful, but they introduce too many moving parts too
early:

- latent state
- recurrent instability
- sequence dependence
- harder debugging

### 7.3 Learning Everywhere at Once

If prediction, arbitration, curiosity, and policy all become learned at once,
AXIS loses the clean subsystem boundary that makes it analytically valuable.

---

## 8. A Good First Interpretation for AXIS

The right first interpretation is:

> one small neural module updates online from local prediction error, and the
> agent uses the updated module immediately on subsequent steps.

This preserves:

- explicit drives
- explicit state
- explicit action space
- explicit transition semantics
- explicit error interpretation

while still introducing genuine neural adaptation.

That is enough to test the first major question:

> can a bounded learned component improve behavior inside a mechanistic AXIS
> agent without dissolving the architecture into opacity?

---

## 9. Recommended First Experimental Regimes

### Regime A: Update Every Step

At each step:

1. infer with current weights
2. act
3. observe outcome
4. update predictor once
5. continue

This is the clearest proof of concept.

### Regime B: Update Every $k$ Steps

Same as above, but apply updates only every few steps.

This may improve stability and make comparisons easier.

### Regime C: Two-Speed Learning

Use:

- a fast trace-like adaptation process
- and a slower neural weight update process

This is closer to biological intuition, but should come after the simpler
regimes.

---

## 10. Main Risks

The main risks of interleaved learning-and-use are:

### 10.1 Instability

Small weight changes may produce abrupt behavioral changes.

### 10.2 Error Reinforcement

If the training signal comes from the agent’s own predictions or actions, the
agent may reinforce bad patterns.

### 10.3 Forgetting

Continual updates may destroy earlier useful structure.

### 10.4 Reduced Interpretability

Once weights move during interaction, explanation becomes harder unless the
module role remains very narrow.

### 10.5 Reproducibility Complexity

Now the trajectory depends not only on:

- world dynamics
- random seed
- initial state

but also on:

- optimizer state
- learning schedule
- accumulated online experience

---

## 11. Provisional Conclusion

The answer to the first AXIS question is:

> yes, current technology can absolutely support agents that learn during
> interaction and immediately use the updated knowledge on subsequent steps.

But the correct implementation model is not:

> one timeless network that both trains and infers in a vague continuous way

It is:

> a stepwise or short-horizon interleaving of inference, experience,
> parameter update, and renewed inference.

For AXIS, this is most promising when applied first to:

- prediction
- compact local memory
- or other tightly bounded subfunctions

not to the entire agent.

---

## 12. Immediate Consequence for This Initiative

Before choosing concrete architectures, the initiative should first clarify:

1. which timing regime AXIS wants to test first
2. which submodule is allowed to learn online
3. which learning signal is available locally
4. how online updates are bounded for stability
5. how the effect of learned updates will be measured

This means the next useful document is likely not “which neural architecture
should we pick?” but:

> “what exact online learning regime should AXIS allow for the first neural
> predictive experiment?”
