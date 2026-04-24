# Draft: Extended Behavioral Metrics for AXIS Experiments

## Purpose

The current AXIS experiment framework mainly reports:

* steps survived
* death rate

These are useful survival metrics, but they are too coarse to evaluate whether additional mechanisms such as prediction actually change behavior.

This draft proposes a set of extended behavioral metrics for comparing:

* System A: hunger-driven reactive baseline
* System C: hunger + prediction
* later: A+W and C+W

The goal is not to prove that prediction is “better”, but to measure whether it produces a distinct behavioral signature.

AXIS already records step-level traces and separates system, world, and framework concerns, which makes such metrics conceptually compatible with the existing architecture. 

---

## 1. Core Question

The primary experimental question should be:

> Does prediction measurably alter behavior compared to pure hunger-driven reactivity?

A secondary question is:

> Under which environmental conditions does prediction help, harm, or merely change the behavioral pattern?

This is important because prediction may not increase survival in every environment. In simple resource landscapes, System A may already be sufficient.

---

## 2. Metric Categories

## 2.1 Survival Metrics

These remain the baseline.

### Mean Steps Survived

Average number of steps before termination.

### Death Rate

Fraction of episodes ending in zero energy.

### Final Energy / Final Vitality

Useful when episodes end due to max-step limit rather than death.

These metrics answer:

> Does the system stay alive?

But they do not explain how.

---

## 2.2 Resource Efficiency Metrics

These measure whether the agent converts environmental opportunity into internal energy efficiently.

### Resource Gain per Step

$$
\eta_{gain} = \frac{\sum_t \Delta e_t^{env}}{T}
$$

Interpretation:

* high value: agent frequently gains energy
* low value: agent moves without enough intake

### Net Energy Efficiency

$$
\eta_{net} = \frac{\sum_t \Delta e_t^{env}}{\sum_t c(a_t)}
$$

This compares energy gained against energy spent.

### Successful Consume Rate

$$
SCR = \frac{\lvert \{ \text{consume actions with } \Delta R > 0 \} \rvert}{\lvert \{ \text{consume actions} \} \rvert}
$$

This is very important for System C.

If prediction works, it should reduce useless consume attempts in empty or historically disappointing contexts.

### Consume-on-Empty Rate

$$
CER = \frac{\lvert \{ \text{consume actions with } r_c = 0 \} \rvert}{\lvert \{ \text{consume actions} \} \rvert}
$$

Lower is usually better, but not always. In a stochastic baseline, some waste is expected.

---

## 2.3 Behavioral Stability Metrics

These measure whether behavior becomes more structured or remains noisy.

### Action Entropy

For action frequencies over an episode:

$$
H(A) = - \sum_a p(a)\log p(a)
$$

Interpretation:

* high entropy: broad, noisy action distribution
* low entropy: concentrated behavior

Caution: low entropy is not automatically good. It may mean efficient behavior, or pathological repetition.

### Local Action Consistency

Measure how often the agent selects the same action in similar local contexts.

Conceptual form:

$$
Consistency = P(a_t = a_{t'} \mid context_t \approx context_{t'})
$$

Expected difference:

* System A: same context gives similar probabilities, but stochasticity dominates
* System C: prediction may increase consistency if one action has historically worked

### Policy Sharpness

Average max action probability:

$$
Sharpness = \frac{1}{T}\sum_t \max_a P_t(a)
$$

This measures how decisive the policy becomes.

---

## 2.4 Failure Avoidance Metrics

These are probably the most important for comparing A vs. C.

### Failed Movement Rate

$$
FMR = \frac{\lvert \{ \text{movement actions with no displacement} \} \rvert}{\lvert \{ \text{movement actions} \} \rvert}
$$

Useful in worlds with obstacles, walls, corridors, traps.

### Repeated Failed Action Rate

Counts whether the agent repeats the same failed action in the same or similar context.

$$
RFAR = \frac{\lvert \{ \text{repeated failed context-action pairs} \} \rvert}{\lvert \{ \text{failed actions} \} \rvert}
$$

This directly tests prediction.

System A should have no principled way to suppress repeated failure, because its baseline memory is not used for prediction or decision-making. 

### Post-Failure Adaptation

After a failed action at time (t), measure whether the probability of the same action decreases in the next similar context.

$$
Adaptation = P_{before}(a \mid c) - P_{after}(a \mid c)
$$

This is a clean “prediction effect” metric.

---

## 2.5 Bias and Inertia Metrics

Prediction can help, but it can also make the system too conservative.

### Action Inertia

Probability that the agent repeats the previous action:

$$
I_a = P(a_t = a_{t-1})
$$

Useful for detecting repetitive loops.

### Contextual Inertia

Probability that the agent keeps selecting an action that was previously successful, even when the current local observation changes.

This is important because System C may become biased by stale predictive traces.

### Recovery After Change

In dynamic or regenerating environments:

$$
RecoveryTime = \text{steps until behavior adapts after local outcome changes}
$$

Example:

* a direction used to be bad
* later it becomes useful
* does System C recover, or does prediction suppress it too long?

This is where prediction may harm survival.

---

## 2.6 Exploration and Coverage Metrics

Even before A+W, movement structure matters.

### Unique Cells Visited

$$
Coverage = |{p_t}|
$$

This requires world-level trace access, not agent internal access.

### Coverage per Energy Spent

$$
CoverageEfficiency = \frac{unique\ cells\ visited}{\sum_t c(a_t)}
$$

This distinguishes useful exploration from expensive wandering.

### Revisit Rate

$$
RevisitRate = 1 - \frac{unique\ cells\ visited}{movement\ steps}
$$

High revisit rate can indicate local loops.

For A+W and C+W, this becomes especially important because A+W already has a visit-count world model and novelty mechanism. 

---

## 2.7 Prediction-Specific Metrics

These apply only to System C and later C+W.

### Mean Prediction Error

$$
MPE = \frac{1}{T}\sum_t |prediction_error_t|
$$

Measures calibration quality.

### Signed Prediction Error

$$
SPE = \frac{1}{T}\sum_t prediction_error_t
$$

Useful to detect systematic optimism or pessimism.

### Confidence Trace Mean

Average confidence over the episode.

### Frustration Trace Mean

Average frustration over the episode.

System C contributes local predictive memory, signed prediction error, confidence/frustration traces, and action-level predictive modulation. 

### Prediction Modulation Strength

Average absolute prediction effect on action scores:

$$
PMS = \frac{1}{T}\sum_t \sum_a |\psi_{with\ prediction}(a) - \psi_{without\ prediction}(a)|
$$

This is very valuable.

It tells you whether prediction is actually influencing the policy, even if survival does not change.

---

## 3. Recommended First Metric Set

For the first implementation wave, I would not add everything.

Start with:

1. mean steps survived
2. death rate
3. final energy
4. successful consume rate
5. consume-on-empty rate
6. failed movement rate
7. repeated failed action rate
8. action entropy
9. policy sharpness
10. prediction modulation strength, System C only

This gives you a strong first comparison without overloading the framework.

---

## 4. Interpretation Strategy

A possible outcome table:

| Result                                            | Interpretation                                                                   |
| ------------------------------------------------- | -------------------------------------------------------------------------------- |
| C survives longer and has lower failed repetition | prediction helps                                                                 |
| C behaves differently but does not survive longer | prediction changes behavior, but not fitness                                     |
| C survives worse but has lower entropy            | prediction may cause harmful rigidity                                            |
| C has same metrics as A                           | prediction is too weak, irrelevant, or environment does not expose its advantage |
| C improves only in obstacle/trap worlds           | prediction is context-dependent, not generally superior                          |

The last outcome would be especially interesting.

---

## 5. Working Hypothesis

Prediction should not be expected to produce a universal survival advantage.

A more realistic hypothesis is:

> Prediction improves behavior mainly in environments with repeated local failure patterns, misleading action opportunities, or context-action regularities.

In simple resource landscapes, System A may already be near-optimal enough that prediction adds little.

---

## 6. Design Constraint

Metrics should not accidentally introduce cognition into interpretation.

For example:

* “stability” should mean measurable action-pattern consistency
* “bias” should mean persistence of action preference despite changed evidence
* “efficiency” should mean energy/resource conversion
* “adaptation” should mean changed action probabilities after observed outcomes

No metric should require assuming intention, understanding, or planning.

---

## 7. Summary

The extended metrics should answer three different questions:

1. **Survival:** does the agent live longer?
2. **Efficiency:** does it use resources and actions better?
3. **Behavioral structure:** does prediction create measurable adaptation, stability, or harmful inertia?

This gives AXIS a much stronger experimental basis than survival metrics alone.
