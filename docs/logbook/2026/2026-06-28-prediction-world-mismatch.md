# Prediction-A and the Built-In Worlds: A Mismatch, Not a Failure

Date: `2026-06-28`
Tags: `prediction`, `worlds`, `system-design`, `alignment`, `postponed`
Related initiatives:

- [World-System Alignment](../../initiatives/world-system-alignment/index.md)
- [Neural Submodules in AXIS](../../initiatives/neural-submodules/index.md)

## Context

The current explicit prediction subsystem was introduced as a local predictive
extension to the baseline resource-seeking agents.

In System C and System C+W, the core idea is simple and mechanistically clear:

- predict the next local sensory outcome for a context-action pair
- compare prediction and reality after action execution
- accumulate negative and positive surprise into frustration and confidence traces
- use those traces to suppress or amplify future action expression in similar local contexts

This design is conceptually elegant. It provides an explicit and inspectable
example of local predictive trust learning.

However, experiments with the existing built-in worlds did not show a robust,
convincing advantage from this subsystem. That raised an important question:

> Is the prediction subsystem implemented badly, or is it simply not matched to
> the worlds it has been tested in?

The work summarized here supports the second interpretation.

## What Was Investigated

The prediction subsystem was analyzed against the existing AXIS world family,
with special attention to:

- deterministic 2D resource worlds
- uniform and clustered regeneration structures
- resource depletion and revisit effects
- cooldown / regrowth timing
- obstacle / blockade conditions
- the distinction between local visible context and hidden world state

This produced three concrete supporting documents:

- [Prediction System Recap](../../initiatives/world-system-alignment/prediction-system-recap.md)
- [Prediction System World-Fit Analysis](../../initiatives/world-system-alignment/prediction-system-world-fit-analysis.md)
- [Prediction System World Assessment Matrix](../../initiatives/world-system-alignment/prediction-system-world-assessment-matrix.md)

## Findings

### 1. Prediction-A is a local one-step reliability learner

The current prediction subsystem learns only a very specific kind of regularity:

- given a local context and a candidate action
- what next local sensory outcome is expected
- and whether that action has tended to under-deliver or over-deliver in that context

It is therefore:

- not a planner
- not a true world model
- not a latent-state tracker
- not a long-horizon value learner

This sharply limits the worlds in which it can be useful.

### 2. The existing built-in resource worlds are mostly deterministic in the wrong way

The present `grid_2d` and `toroidal` resource worlds provide:

- deterministic movement over traversable cells
- deterministic resource extraction
- deterministic regeneration dynamics
- deterministic cooldown countdown
- deterministic obstacle semantics

The only major stochasticity in ordinary use is the system's own policy
sampling. That is not the same as a stochastic transition world.

This matters because Prediction-A needs genuine local action unreliability or
stable local deceptiveness to learn something behaviorally useful.

### 3. Many current worlds are prediction-neutral

In simple local resource worlds, the baseline system already sees enough.
If the local observation clearly says which direction is better, and the world
responds deterministically, then prediction mostly relearns what is already
visible.

That makes many current test worlds prediction-neutral.

### 4. Some current worlds are not only weak fits, but misleading fits

The strongest negative result concerns depletion and regrowth.

In several current world regimes, the same visible local context can correspond
to different hidden world states because of:

- earlier harvesting
- revisit timing
- regrowth / cooldown phase

The current predictor cannot represent those hidden differences if they are not
encoded in the local context key.

That means the system can learn frustration for the wrong reason.

Instead of learning:

> this action is genuinely unreliable in this local situation

it may learn:

> this world state had changed because of history that the predictor cannot represent

This is not a subtle edge case. It is likely central to why prediction failed to
show robust benefit in earlier experiments.

### 5. The null result is meaningful

The lack of clear advantage from the prediction subsystem should not be read as:

- proof that prediction is useless
- proof that the implementation is necessarily wrong
- proof that only neural methods could help

A more defensible reading is:

> Prediction-A is not well aligned with the current built-in world family.

That is a strong and useful negative result.

## Interpretation

The prediction subsystem should now be understood as a reference design rather
than an automatically useful capability.

It demonstrates a coherent mechanistic idea:

- local context-conditioned expectation
- signed prediction error
- local frustration / confidence accumulation
- bounded action modulation

But a coherent mechanistic idea is not enough. It must also meet a world that
contains the right exploitable structure.

The present worlds mostly do not.

This means the project has learned something important about its own modeling
practice:

> designing a plausible cognitive subsystem is not sufficient; the world family
> must contain the right informational and behavioral affordances for that subsystem to matter.

That lesson is highly valuable for later system design, including any future
neural work.

## Consequences

### 1. Neuralization is postponed

No neural version of prediction should be pursued until an explicit subsystem
shows a real benefit in a well-matched world family.

Neuralization of a mismatched subsystem would only hide the conceptual problem
rather than solve it.

### 2. Prediction-A is retained as a useful example

The subsystem should not be discarded.

It remains valuable as:

- a worked example of explicit local predictive learning
- a benchmark for future world classes
- a baseline against which stronger predictive systems can be compared
- a demonstration that elegant internal architecture does not guarantee world fit

### 3. World-System Alignment becomes the active main initiative

The immediate task is now:

- analyze which worlds support which systems
- identify where current worlds are prediction-neutral, fragile, or misleading
- decide whether to adapt worlds, adapt systems, or both

### 4. A second prediction design may be needed

It is plausible that the current built-in worlds do not call for Prediction-A,
but for a different predictive subsystem altogether.

Possible future directions include:

- prediction tied to regrowth or availability rather than next local sensory outcome
- prediction coupled to spatial memory
- prediction over action value rather than raw next-step features
- richer context models that reduce hidden-state aliasing

These are open design questions, not conclusions yet.

## What This Changes Operationally

The immediate project posture is now:

- do not treat prediction as a generally validated subsystem
- do not neuralize prediction yet
- use the current analysis to define fairer world classes
- consider alternative non-neural predictive designs for the existing worlds

In practice, this creates two future tracks:

1. build or identify worlds where Prediction-A should genuinely help
2. investigate whether a Prediction-B architecture is better matched to the current world family

## Next Questions

1. Can we derive biologically plausible stochastic or deceptive world classes
   where Prediction-A gets a fair test?
2. Are the current 2D worlds fundamentally too direct, or only too deterministic?
3. Should the existing worlds be enriched, or should the predictive subsystem be redesigned first?
4. What would a Prediction-B system look like if it were designed specifically
   for depletion, regrowth, and revisit-heavy worlds?

## Closing Assessment

The current conclusion is not that prediction failed.

The better conclusion is:

> the current explicit prediction subsystem and the current built-in world
> family are misaligned.

That is the first result worth preserving historically, because it explains the
absence of experimental advantage and sets the direction for the next stage of
work much more clearly than any positive but weakly founded success story would have.
