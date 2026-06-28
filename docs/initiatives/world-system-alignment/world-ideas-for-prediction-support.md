# World Ideas for Better Prediction Support

This document captures candidate world refinements that could make the current
explicit AXIS prediction system meaningfully useful instead of mostly neutral or
misleading.

It builds directly on:

- [Prediction System Recap](prediction-system-recap.md)
- [Prediction System World-Fit Analysis](prediction-system-world-fit-analysis.md)
- [Prediction System World Assessment Matrix](prediction-system-world-assessment-matrix.md)
- [Prediction-A and the Built-In Worlds: A Mismatch, Not a Failure](../../logbook/2026/2026-06-28-prediction-world-mismatch.md)

The guiding principle is not "add randomness for its own sake."

The guiding principle is:

> introduce biologically plausible, locally recurring, partially learnable
> uncertainty patterns that the current one-step prediction system can actually
> exploit.

## Design Goals

The current prediction system needs worlds with the following properties:

- recurring local contexts
- non-trivial but not arbitrary uncertainty
- local action outcomes that are not fully determined by the current visible resource snapshot
- enough regularity that context-action prediction can improve behavior

The ideas below are therefore judged against AXIS-specific criteria:

- biological plausibility
- fit to the current System C / C+W prediction structure
- implementability in existing grid-based worlds
- risk of creating noise without learnable structure

## Idea Overview

| Idea | Core change | Why it may help Prediction-A | AXIS fit | Main risk |
|---|---|---|---|---|
| 1. Moving weather cells with slip modulation | Local weather fields temporarily raise move-failure or move-deviation probabilities | The same action in similar local contexts can become systematically less reliable in a way the predictor can learn | Strong; reuses dynamic region mechanics already seen in signal-style worlds | Too much randomness turns learnable structure into noise |
| 2. Probabilistic neighbor sensing instead of exact neighbor values | Neighbor cells are perceived as uncertain estimates rather than exact resource magnitudes | Prediction can learn which locally promising moves tend to under- or over-deliver relative to uncertain perception | Very strong; directly addresses the fact that current deterministic local sensing already gives too much away | If estimates are too noisy, baseline and prediction both degrade |
| 3. Weather-driven obstacle volatility | Obstacles remain stable normally, but weather regions can temporarily create or remove passability | Prediction can learn that action reliability depends on dynamic local world state, not just resource gradients | Moderate to strong; combines dynamic world state with local recurrence | Can become too discontinuous if passability changes are too frequent or too global |
| 4. Day/night cycle with changing sensing and transition quality | A global or regional phase changes visibility, perception quality, and possibly action reliability | Prediction can learn recurring temporal structure that modulates how trustworthy actions and observations are | Strong; simple to explain, biologically plausible, and easy to combine with existing worlds | If fully global and perfectly obvious, the benefit may collapse into a trivial rule rather than a real predictive advantage |

## 1. Idea: Moving Weather Cells with Slip Modulation

### Core concept

Introduce transient weather regions that move across the grid. Outside those
regions, movement remains mostly reliable. Inside them, slip probability rises.

This should not be global noise. It should be spatially localized and
temporally persistent enough that the agent can repeatedly encounter similar
conditions.

Examples:

- wind corridor raises left/right drift probability
- rain cell raises generic movement failure probability
- storm patch raises both slip probability and resource-estimation uncertainty

### Why this is a good fit for Prediction-A

This idea directly creates the kind of world structure the current predictor
can use:

- a local context-action pair can recur
- the action outcome is no longer trivially deterministic
- outcome degradation is systematic rather than arbitrary
- confidence and frustration traces can start encoding local action reliability

In other words, the system would no longer only be relearning visible resource
gradients. It could learn:

> "moving right in weather state X tends to disappoint"

instead of:

> "right looked good and was good," which the baseline already knows.

### Biological plausibility

This is plausible in a broad evolutionary sense:

- terrain and weather conditions affect locomotion reliability
- organisms often adapt to patches of wind, rain, mud, current, or unstable ground
- such conditions are local, repeated, and only partially observable

### AXIS-oriented implementation direction

Good AXIS-compatible constraints would be:

- keep the base grid world and resource logic
- add a world-level moving weather field
- allow each weather type to modulate move reliability
- keep weather motion relatively slow compared to agent action frequency
- make weather local rather than global

This should likely be configurable through a world block rather than through
system configuration.

### Important guardrails

- weather must persist long enough to be learnable
- slip increase should be moderate, not catastrophic
- there should still be baseline-accessible structure so that comparisons remain meaningful

## 2. Idea: Probabilistic Neighbor Sensing Instead of Exact Neighbor Values

### Core concept

The current local observation is often too revealing.

If the agent sees exact neighbor resource magnitudes, then baseline hunger-based
action selection already captures much of the useful short-horizon signal.

A more plausible sensor model would be:

- current cell: relatively accurate measurement, because the agent is on it
- neighbor cells: uncertain estimate of resource presence or approximate intensity
- empty or poor cells: usually perceived as low-probability opportunities, not exact zeros known with certainty

This introduces epistemic uncertainty into perception rather than only into transition.

### Why this is a good fit for Prediction-A

This idea may be the strongest direct improvement for the current prediction
system because it changes the baseline informational regime itself.

Right now, the agent often already knows too much before acting.

With uncertain neighbor sensing:

- the visible pre-action signal becomes approximate
- action outcomes become informative relative to prior expectation
- prediction can learn systematic calibration patterns

That means the system can start learning things such as:

- some estimated-rich patterns tend to disappoint
- some weak-looking patterns are often better than they appear
- certain local sensory signatures are trustworthy, others are not

This is much closer to how a one-step predictive mechanism can create value.

### Biological plausibility

This is strongly biologically plausible:

- distal sensing is usually weaker than direct contact
- organisms often estimate rather than measure distant resource value
- perception is noisy, thresholded, and modality-dependent

### AXIS-oriented implementation direction

A practical v1 framing would be:

- retain the current observation shape
- reinterpret neighbor channels as probabilistic estimates
- make estimate noise depend on distance and maybe weather
- reveal the actual current-cell value only after arrival

This keeps the agent loop conceptually stable while changing the semantics of
what the sensors mean.

### Important guardrails

- estimates must still correlate with reality
- current-cell sensing should stay more accurate than neighbor sensing
- the world should not degenerate into pure hidden-state guessing

## 3. Idea: Weather-Driven Obstacle Volatility

### Core concept

Obstacles should remain stable most of the time.

But when a weather cell passes through a region, passability can change with a
controlled probability:

- fallen tree or debris creates a new blockage
- water level recedes and a path opens
- unstable terrain becomes temporarily non-traversable

Outside weather influence, obstacle topology stays stable.

### Why this is a good fit for Prediction-A

This creates dynamic transition reliability without making the whole world
chaotic.

A predictor may learn:

- a route that is normally reliable becomes risky under weather influence
- certain local contexts are only safe while the region is stable

This is useful if, and only if, the weather/terrain regime creates recurring
patterns rather than one-off surprises.

### Biological plausibility

This is plausible when framed as environmental disturbance:

- weather changes terrain usability
- blocked paths appear or disappear
- landscape affordances are condition-dependent

### AXIS-oriented implementation direction

This idea likely works best as a second-order extension of Idea 1 rather than a
standalone first change.

Reason:

- slip modulation is simpler and already useful
- obstacle volatility adds more hidden state and more implementation complexity
- combined too early, both effects may become hard to interpret experimentally

So the likely AXIS sequence is:

1. add moving weather with slip modulation
2. test whether Prediction-A gains a measurable benefit
3. only then add weather-scoped obstacle volatility

### Important guardrails

- keep obstacle changes local
- avoid excessive topology churn
- ensure changes are tied to interpretable world-state mechanisms

## 4. Idea: Day/Night Cycle with Changing Sensing and Transition Quality

### Core concept

Introduce a repeating temporal phase into the world.

The simplest version is a global day/night cycle. A richer version could use
dawn, day, dusk, and night, or regional shading effects that partially decouple
the cycle across the map.

The important point is that the phase changes the operational quality of the
agent-world interaction, for example:

- lower-quality neighbor sensing at night
- slightly higher movement uncertainty at night
- altered visibility of obstacles or terrain affordances
- resource cues that are easier or harder to detect depending on phase

### Why this is a good fit for Prediction-A

This creates a recurring, non-random modulation of local action outcomes and
observation quality.

That is attractive for the current predictor because:

- the regime recurs reliably
- the same context-action pair can have different expected outcomes across phases
- disappointment and confidence can begin to encode temporal environmental reliability

The system could learn things like:

> "moves into weakly sensed cells under night conditions often under-deliver"

or:

> "this local sensory pattern is only trustworthy during day."

### Biological plausibility

This is highly plausible:

- many organisms behave differently under day and night conditions
- visibility, locomotion safety, and cue reliability often depend on time of day
- circadian regularities are among the most basic recurring structures in real environments

### AXIS-oriented implementation direction

A practical AXIS version should likely start simple:

- add a repeating world phase clock
- expose phase either explicitly, weakly, or only indirectly through observation quality
- let phase modulate neighbor-sensing uncertainty first
- optionally add modest movement/slip effects later

This idea is especially compatible with Idea 2:

- day/night can modulate the uncertainty of neighbor estimates
- weather can remain a local effect, while day/night is a broader temporal effect

That gives AXIS two distinct uncertainty sources:

- spatial-local uncertainty from weather
- temporal-global uncertainty from day/night

### Important guardrails

- the phase effect must be strong enough to matter, but not so strong that behavior reduces to a trivial hand-coded schedule
- if the phase is directly exposed, it should still interact with uncertain sensing or transition quality so prediction remains useful
- if the phase is hidden entirely, the system may again suffer from aliasing unless some indirect cues exist

## Recommended Sequencing

These ideas should not be implemented all at once.

A pragmatic order would be:

1. **Probabilistic neighbor sensing**
   This directly attacks the "baseline already sees too much" problem.
2. **Day/night cycle with sensing-quality modulation**
   This adds recurring temporal structure with strong biological plausibility and relatively low implementation complexity.
3. **Moving weather cells with slip modulation**
   This introduces structured local transition uncertainty.
4. **Weather-driven obstacle volatility**
   This can be layered on later if the simpler stochastic structure proves useful.

Reasoning:

- Idea 2 changes what the observation means
- Idea 4 changes the temporal reliability regime of sensing and action
- Idea 1 changes what actions actually do locally
- Idea 3 changes local topology and therefore adds the most interpretive complexity

## Suggested Evaluation Questions

If these ideas are pursued, the next analyses should ask:

- Does Prediction-A now outperform a non-predictive baseline in survival or energy retention?
- Are confidence and frustration traces becoming behaviorally meaningful rather than noisy?
- Do learned prediction effects track recurring local world structure, or merely hidden depletion history again?
- Which single change helps more: uncertain sensing or stochastic transition reliability?
- Does C+W benefit more than C because its spatial world model can contextualize unstable regions better?

## Current Working Conclusion

All three ideas are plausible for AXIS CMS, but they are not equally valuable.

The strongest current candidates are:

- **probabilistic neighbor sensing**, because it weakens the overly informative deterministic observation regime
- **day/night cycle with sensing-quality modulation**, because it introduces recurring temporal structure without requiring immediate topological complexity
- **moving weather cells with slip modulation**, because it creates exactly the kind of local action unreliability the current predictor can learn

The obstacle-volatility idea is promising, but should likely remain a later
extension after the simpler stochastic mechanisms have been tested in isolation.
