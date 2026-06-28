# Neural Submodules in AXIS

## Motivation

The current AXIS systems are explicit mathematical constructions. Their state
variables, update rules, and behavioral consequences are visible and
analyzable. This is a major strength and should remain a defining property of
the framework.

At the same time, some subproblems inside AXIS are natural candidates for more
flexible function approximators:

- predictive mappings from local context to expected outcome
- compact memory structures for world regularities
- bounded action-selection refinements
- structured behavior modules that are too awkward to specify manually

The goal of this initiative is therefore not to replace AXIS with generic
neural agents. The goal is to investigate where neural networks can be used as
carefully delimited submodules inside otherwise explicit AXIS systems.

## Core Position

AXIS should continue to model explicit cognitive motifs at the system level.
Neural networks should be introduced where they help represent or adapt a
subfunction that is already conceptually understood.

That implies:

- the global system architecture remains explicit
- drives, arbitration, and major loop structure remain inspectable
- neural modules should have clear inputs, outputs, and update rules
- every neural insertion should have a reduction path back to a simpler manual model

## Candidate Integration Points

The most promising initial targets are:

1. Predictive submodules
   Replace hand-written or table-based predictors with neural approximators.
   This fits especially well for System C and C+W, where prediction already
   plays a central behavioral role.

2. Spatial or contextual memory compression
   Replace large explicit maps or traces with learned latent summaries when
   the explicit structure becomes too large or noisy.

3. Local policy refinement
   Keep explicit drives and modulation, but let a small neural submodule rank
   or bias actions within a bounded interface.

4. Behavioral motifs
   Introduce small learned modules for tasks such as exploration preference,
   novelty response, or local avoidance patterns.

## Non-Goals

This initiative is not about:

- turning AXIS into an opaque end-to-end RL benchmark
- removing explicit mathematical state descriptions
- replacing system design with large-scale generic training
- chasing performance without interpretability

## First Practical Direction

The most coherent first step is to introduce a neural predictor into an
already prediction-centric system, rather than to learn the whole agent.

That suggests the following sequence:

1. Start from System C or C+W.
2. Keep the explicit agent loop, drives, and arbitration logic.
3. Replace only the prediction function with a neural module.
4. Keep prediction error as an explicit exposed quantity.
5. Compare behavior against the manual predictor baseline.

## Key Questions

This initiative should answer at least the following:

- Which AXIS submodules benefit from neural approximation without making the system opaque?
- Can we support online learning and immediate use inside the agent loop?
- What stabilization principles are needed so a continuously adapting module does not become behaviorally chaotic?
- How should persistence, runtime state, and visualization represent neural submodules?
- When is a neural submodule better than the manual baseline, and when is it not?

## Expected Outcome

The desired outcome is not a single "neural AXIS" system. The desired outcome
is a principled integration strategy that defines:

- where neural modules belong
- how they are trained or adapted
- how their behavior remains interpretable enough for AXIS research
- how they coexist with explicit mathematical models and their baselines
