# Prediction System World Assessment Matrix

This document turns the world-fit analysis into a concrete assessment matrix for
existing AXIS world families.

The purpose is operational:

- classify current worlds as prediction-neutral, prediction-fragile,
  prediction-favorable, or prediction-misleading
- explain why the current explicit prediction system is or is not expected to
  help in each case
- separate worlds that already exist from reference cases that are only
  theoretical comparison points for now

This document is a continuation of:

- [Prediction System World-Fit Analysis](prediction-system-world-fit-analysis.md)

## 1. Rating Scale

The labels used here mean:

### Prediction-neutral

The current prediction system is not expected to add much, because the local
observation and baseline drive logic already capture most of what matters.

### Prediction-fragile

The system might help in a narrow regime, but the benefit is easily destroyed by
aliasing, depletion history, or weak context recurrence.

### Prediction-favorable

The current prediction system should plausibly help, because there is genuine
local action unreliability or stable local deceptiveness that one-step
prediction can learn.

### Prediction-misleading

The current prediction system is likely to learn the wrong lesson because the
same local context corresponds to different hidden world states that matter for
the outcome.

## 2. Existing AXIS Resource-World Families

The current relevant resource-world family is the grid-based world with:

- local resource observations
- deterministic movement over traversable cells
- deterministic resource extraction
- deterministic regeneration dynamics
- optional cooldown before regeneration resumes
- configurable regeneration eligibility layouts
- obstacles / blockades via non-traversable cells

In code terms, the important current world knobs are:

- `regeneration_mode = all_traversable`
- `regeneration_mode = sparse_fixed_ratio`
- `regeneration_mode = clustered`
- `resource_regen_rate`
- `resource_regen_cooldown_steps`
- obstacle density / topology

Important current fact:

> the existing built-in `grid_2d` and `toroidal` resource worlds do not appear
> to implement stochastic movement failure or stochastic resource-yield
> transitions. Their resource and movement semantics are currently deterministic,
> aside from the agent's own stochastic policy sampling.

So when we refer below to a `stochastic transition world`, that is currently a
**reference world class**, not an already implemented standard AXIS resource
world, unless such a world is added separately.

## 3. Matrix Overview

```text
Existing / reference world class                  Rating
--------------------------------------------------------
uniform deterministic resource world              prediction-neutral
clustered deterministic resource world            prediction-fragile
cooldown / regrowth world                         prediction-misleading or fragile
blockade / obstacle world                         conditional, usually neutral-to-fragile
toroidal deterministic resource world             prediction-neutral
signal landscape world                            not a direct fit for current System C resource prediction
stochastic local transition world                 prediction-favorable (reference case, not current standard world)
deceptive local transition world                  prediction-favorable (reference case, not current standard world)
```

## 4. Assessment by World Family

### A. Uniform Deterministic Resource World

Current status: effectively present through ordinary `grid_2d` / `toroidal`
configurations with non-clustered regeneration.

Rating: **prediction-neutral**

Why:

- movement is deterministic
- local resource observation already tells the baseline system which direction
  looks best
- there is little hidden local action unreliability to learn
- prediction mostly re-encodes what the observation already says

ASCII intuition:

```text
          [ UP: low ]
[ L: low ] [ A: here ] [ R: high ]
         [ DOWN: low ]

Baseline already says: move RIGHT.
If the world behaves deterministically, prediction adds little.
```

Expected result:

- little or no survival benefit from prediction alone
- any effect likely small, noisy, or configuration-sensitive

### B. Clustered Deterministic Resource World

Current status: effectively present via `regeneration_mode = clustered` and
clustered eligibility in the grid worlds.

Rating: **prediction-fragile**

Why:

- patch edges can create recurring local patterns
- in principle, prediction could learn that some locally attractive patch-edge
  moves over- or under-deliver
- but depletion and revisit history make the same local pattern mean different
  things at different times

ASCII intuition:

```text
same-looking pre-action fringe            different hidden patch state

          [ UP: 0.0 ]
[ L: 0.0 ] [ A: 0.0 ] [ R: 0.7 ]   ->    move RIGHT
         [ DOWN: 0.0 ]

first time:  new current = 0.7
later time:  new current = 0.1
```

Interpretation:

- if the context encoder cannot represent the patch's hidden depletion state,
  prediction averages incompatible cases
- frustration may then encode depletion history rather than true action unreliability

Expected result:

- weak or unstable benefit
- high sensitivity to revisit structure, regeneration rate, and context granularity

### C. Cooldown / Regrowth World

Current status: present through `resource_regen_cooldown_steps` plus deterministic regeneration.

Rating: **prediction-misleading** in the strong case, **prediction-fragile** in milder cases

Why:

- cooldown creates hidden temporal phase information
- the same local visible situation can correspond to different regrowth states
- if regrowth phase is not directly visible in the observation/context, the
  predictor is trying to learn a multi-modal transition under one context key

ASCII intuition:

```text
same local pattern now, different latent regrowth state

visible local context at t1   -> move RIGHT -> rich arrival
visible local context at t2   -> move RIGHT -> poor arrival

Difference is not local geometry, but regrowth history.
```

Expected result:

- prediction can become misleading if hidden regrowth phase dominates outcomes
- null results or inconsistent results are entirely plausible here

### D. Blockade / Obstacle World

Current status: present through obstacle density / non-traversable cells.

Rating: **conditional**, usually between prediction-neutral and prediction-fragile

Why:

- if obstacles are already explicit in the local observation and admissibility
  mask, the baseline already handles them
- prediction adds value only if there is additional local transition structure
  beyond what the observation and action mask already expose

ASCII intuition:

```text
explicit obstacle case

          [ UP: blocked ]
[ L: open ] [ A: here ] [ R: open ]
         [ DOWN: open ]

If UP is already masked or clearly penalized, prediction has little extra work to do.
```

Expected result:

- mostly little gain in plain deterministic obstacle worlds
- maybe some gain only if obstacles interact with resources in a more deceptive,
  partially hidden way

### E. Toroidal Deterministic Resource World

Current status: present (`toroidal`).

Rating: **prediction-neutral**

Why:

- topology changes global geometry, but the local transition itself is still
  deterministic and resource-centered
- without additional stochastic or deceptive local transition structure,
  prediction still has little unique signal to exploit

Expected result:

- topology alone does not create the kind of local unreliability the current
  prediction system needs

### F. Signal Landscape World

Current status: present (`signal_landscape`), but not a direct match to the
current System C resource semantics.

Rating: **not directly assessable under current System C resource prediction**

Why:

- Signal Landscape uses drifting hotspot signals rather than the ordinary local
  consumable-resource semantics of System C's current predictive feature design
- this world is more relevant to systems built around signal sensing than to
  the current resource-prediction setup of System C

Expected result:

- not the right benchmark for the current explicit prediction system in its
  present form

## 5. Reference Cases That Are Not Yet Standard AXIS Worlds

These cases are important because they are the worlds where the current
prediction system would have the clearest theoretical chance to shine.

### G. Stochastic Local Transition World

Current status: **reference case, not currently a standard built-in resource world**

Rating: **prediction-favorable**

Definition:

- local action outcomes are probabilistic in a stable way
- examples:
  - movement slips with probability `p`
  - consumption yield is noisy with stable local statistics
  - post-action next local observation fluctuates around a stable mean

Why this matters:

- repeated disappointment or confirmation is meaningful here
- frustration and confidence can track real local reliability
- prediction is no longer just relearning the visible current frame

ASCII intuition:

```text
same context s, same action RIGHT

trial 1 -> strong arrival
trial 2 -> weak arrival
trial 3 -> strong arrival
trial 4 -> weak arrival

Prediction can learn average local reliability of RIGHT in s.
```

Interpretation:

This is probably the clearest class of worlds where the current explicit
prediction architecture should show a measurable benefit.

### H. Deceptive Local Transition World

Current status: **reference case, not currently a standard built-in resource world**

Rating: **prediction-favorable**

Definition:

- a local action appears attractive from current observation
- but repeatedly leads to poorer-than-expected next local outcomes
- the deceptiveness is stable and contextual, not just hidden depletion history

Why this matters:

- this is exactly the semantics that frustration/confidence are meant to encode
- the predictor can learn: this visible opportunity often under-delivers here

## 6. What This Means for Earlier Experiments

If most earlier experiments used only current built-in deterministic resource
worlds, then the absence of a robust System C advantage is not surprising.

The most likely explanation is structural, not accidental:

1. many worlds are prediction-neutral because the baseline already sees enough
2. clustered and cooldown worlds can become prediction-fragile or prediction-misleading
3. the strongest favorable cases are not yet the default built-in world family

So the null result is meaningful.

It may indicate that the current prediction mechanism is not well matched to the
worlds it was tested in, rather than that the implementation is broken.

## 7. Practical Next Step Matrix

```text
World family / condition                         Recommendation
-----------------------------------------------------------------------
uniform deterministic grid                       use as prediction-neutral control
clustered deterministic grid                     use as fragile test, interpret carefully
cooldown/regrowth worlds                         use as aliasing stress test
blockade worlds                                  use only with careful semantic justification
stochastic transition worlds                     add explicitly if prediction is to get a fair test
deceptive local transition worlds                add explicitly if frustration/confidence are to be validated
```

## 8. Conclusion

At the moment, the strongest answer is:

> No, the current standard AXIS resource worlds do not obviously provide the
> best conditions for the current explicit prediction system to demonstrate a
> real advantage.

And specifically:

> No, a true stochastic-transition resource world does not appear to be part of
> the current standard built-in world family.

That makes it a useful missing reference case.
