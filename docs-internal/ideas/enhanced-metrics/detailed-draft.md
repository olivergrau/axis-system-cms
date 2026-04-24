# AXIS Enhanced Metrics

## Detailed Draft for Behavioral Metrics Beyond Survival

---

## 1. Purpose

This document refines the initial enhanced-metrics idea into a more
implementation-aware detailed draft.

The goal is to strengthen AXIS experiment interpretation without introducing
unclear analysis semantics or accidental architectural drift.

The intended outcome is:

- richer behavioral evaluation than survival metrics alone
- a first wave that is directly compatible with the current AXIS trace model
- a clear separation between:
  - metrics that are immediately derivable
  - metrics that require new framework semantics
  - metrics that require environment-change-aware analysis

This document is not yet a final specification.

It is meant to prepare a later spec by fixing:

- the most useful first-wave metric set
- the current trace-mode constraints
- the right integration boundaries
- and the open semantic questions for later waves


## 2. Core Experimental Goal

The central experimental question remains:

> does prediction measurably alter behavior, not only survival, compared to
> pure hunger-driven reactivity?

This is especially relevant for comparisons such as:

- `system_a` vs `system_c`
- later `system_aw` vs `system_cw`

The key point is that AXIS should be able to distinguish between:

- surviving longer
- behaving more efficiently
- behaving more adaptively
- and behaving more rigidly

These are not the same thing.


## 3. Current AXIS Baseline

The current framework already provides a solid starting point.

### 3.1 Existing run-level summaries are intentionally small

Today, the built-in run summary is still minimal and system-agnostic.

It includes:

- `mean_steps`
- `std_steps`
- `mean_final_vitality`
- `std_final_vitality`
- `death_rate`

This is enough for survival-oriented evaluation, but not enough for behavioral
interpretation.

### 3.2 Step-level traces are already rich

The replay contract already records, per step:

- action
- world before / after
- agent position before / after
- vitality before / after
- system-specific trace payload
- world-specific trace payload

This is the main reason the enhanced-metrics idea is viable.

### 3.3 System C already exposes prediction-relevant internals

System C currently records useful predictive fields into trace data, including:

- predictive context
- predictive features
- modulated scores
- predicted features
- observed features
- positive prediction error
- negative prediction error

This means a significant first-wave metric set can be computed without changing
the core System C mechanics.


## 4. Main Design Constraint

The most important constraint for this idea is:

> AXIS should only promote metrics to first-class framework artifacts when
> their meaning is explicit and stable across the current execution and trace
> model

This matters because some proposed metrics sound intuitive but hide unresolved
questions such as:

- what exactly counts as a "similar context"?
- what counts as "adaptation" in a stochastic policy?
- what counts as environmental change in a general world?

So the detailed draft should not treat all metrics as equally mature.


## 5. Trace-Mode Reality

The detailed draft should explicitly acknowledge the current AXIS execution
lanes.

### 5.1 `full` and `delta` are analysis-capable

Behavioral metrics that depend on step traces are currently compatible with:

- `trace_mode: full`
- `trace_mode: delta`

This is because `delta` is reconstructible into replay-rich episode traces.

### 5.2 `light` is not a behavioral-analysis lane

`trace_mode: light` is intentionally summary-oriented.

It does not carry the stepwise data required for most enhanced metrics.

Therefore, this detailed draft should treat `light` as:

- compatible with the existing survival metrics only
- incompatible with most enhanced behavioral metrics

This should be made explicit in any later spec and public documentation.


## 6. Recommended Metric Stratification

The most important refinement to the original draft is to split the metrics
into waves of increasing semantic and engineering difficulty.

### 6.1 Wave 1: Directly Derivable from Current Traces

These are metrics that can be computed from the current trace contract without
introducing ambiguous new semantics.

Recommended first-wave set:

- mean steps survived
- death rate
- mean final vitality
- successful consume rate
- consume-on-empty rate
- failed movement rate
- action entropy
- action inertia
- coverage
- coverage efficiency
- revisit rate
- policy sharpness

For System C and later predictive systems:

- mean prediction error
- signed prediction error
- confidence trace mean
- frustration trace mean
- prediction modulation strength

These metrics are the best first implementation target because they are:

- meaningful
- technically feasible
- relatively easy to validate against traces
- and compatible with the current AXIS data model

### 6.2 Wave 2: Requires Formal Context Semantics

These metrics are promising, but should not be implemented until AXIS fixes a
clear definition of context identity or context similarity.

This wave includes:

- local action consistency
- repeated failed action rate
- post-failure adaptation
- contextual inertia

The core issue is that these metrics depend on questions such as:

- is context defined by raw local observation?
- by discretized predictive context?
- by action admissibility pattern?
- by world-relative neighborhood?
- by system-specific internal representation?

Until AXIS resolves this, these metrics remain analytically interesting but
not yet framework-stable.

### 6.3 Wave 3: Requires Explicit Environment-Change Semantics

The most ambitious metrics in the original draft depend on identifying that the
world has meaningfully changed around the agent.

This wave includes:

- recovery after change
- stale-bias persistence after outcome reversal
- regeneration-aware adaptation timing

These are valuable, but they are not just trace-derived metrics.

They require:

- a formal notion of change event
- or a world-specific interpretation layer

So they should be treated as later analysis work, not as part of the first
framework-wide metric rollout.


## 7. Metric-by-Metric Feasibility Review

### 7.1 Strongly Feasible Now

The following metrics are both sensible and realistic on the current AXIS
stack.

#### Survival Metrics

- mean steps
- death rate
- mean final vitality

These already exist and simply need broader framing.

#### Resource Efficiency Metrics

- successful consume rate
- consume-on-empty rate
- resource gain per step
- net energy efficiency

These are derivable from current transition traces, because action cost and
energy gain are already recorded.

#### Behavioral Structure Metrics

- action entropy
- action inertia
- policy sharpness

These are directly derivable from the action sequence and stored policy
probabilities.

#### Exploration Metrics

- unique cells visited
- coverage efficiency
- revisit rate

These are available from position traces and do not require internal agent
state.

#### Prediction Metrics

- mean prediction error
- signed prediction error
- confidence trace mean
- frustration trace mean
- prediction modulation strength

These align especially well with the current System C trace payload.

### 7.2 Sensible but Semantically Underspecified

The following metrics are good ideas, but currently underspecified:

- local action consistency
- repeated failed action rate in "same or similar context"
- post-failure adaptation
- contextual inertia

These should remain in the design, but explicitly marked as:

- not first-wave framework metrics
- pending formal context semantics

### 7.3 Valuable but Probably World- or Study-Specific

Some metrics are likely better expressed as higher-level analysis packages or
comparison extensions rather than universal run summary fields.

Examples:

- recovery after change
- trap recovery latency
- regeneration adaptation lag

These may still be important for AXIS science, but they should not be assumed
to be universally meaningful across all worlds and systems.


## 8. Recommended Integration Strategy

The enhanced-metrics idea should not begin by enlarging the global summary
schema indiscriminately.

A lower-risk direction is:

1. create a dedicated metric computation layer over episode traces
2. define a stable first-wave metric result model
3. compute these metrics at run level from `full` and `delta` traces
4. surface them in CLI, workspace inspection, and optionally comparison output
5. only later decide which metrics belong in the canonical persisted summary

This is preferable because it avoids prematurely overloading the minimal
run-summary contract.


## 9. Recommended First-Wave Output Model

The first implementation wave should probably introduce a new analysis artifact
rather than immediately replacing `RunSummary`.

A plausible direction is:

- keep existing `RunSummary` for survival-oriented baseline reporting
- add a new run-level behavioral metrics artifact

For example:

- `behavior_metrics.json`
- or a typed run-level analysis object

This keeps the current framework stable while allowing faster iteration on the
metric set.

It also creates a cleaner path for:

- later comparison summaries
- system-specific metrics
- and future workspace integrations


## 10. Comparison-Side Implications

The current generic paired comparison layer focuses on divergence metrics such
as:

- action mismatch
- trajectory distance
- vitality difference

This is useful, but it is not the same as behavioral metrics.

So this idea should not assume that all enhanced metrics naturally belong in
paired comparison.

Instead, the draft should distinguish:

- run-internal behavioral metrics:
  - computed from one system's traces across episodes
- paired divergence metrics:
  - computed by aligning two traces

Some later metrics may exist in both forms, but they should not be collapsed
too early.


## 11. Validation Strategy

A good enhanced-metrics rollout will need more than implementation.

It should validate that the metrics are:

- mathematically well-defined
- mechanically derivable from traces
- intuitively interpretable
- stable under repeated runs

The best first validation path is:

1. build a tiny gold set of hand-checked episodes
2. compute first-wave metrics on these episodes
3. verify each metric against manual expectations
4. compare `system_a` and `system_c` on a small controlled scenario
5. confirm that the metrics produce interpretable differences


## 12. Main Risks

The main risks of this idea are:

- metric inflation without analytical clarity
- embedding system-specific assumptions into framework-wide metrics
- treating `light` runs as if they supported the same analysis depth
- introducing context-sensitive metrics before AXIS defines context formally

The design should therefore remain conservative.

The first wave should prioritize metrics that are:

- directly derivable
- easy to explain
- and hard to misread


## 13. Recommended Next Step

The next document should move from this detailed draft to a spec that fixes:

- the first-wave metric list
- the trace-mode compatibility rules
- the new artifact or summary model
- the distinction between framework-wide and system-specific metrics
- and the validation/test strategy

The right first-wave recommendation is:

- implement a compact behavioral metric layer for `full` and `delta`
- keep ambiguous context-sensitive metrics explicitly out of scope for v1
- preserve the current minimal run summary until the new metric layer proves
  itself


## 14. Recommendation

The enhanced-metrics idea is both sensible and feasible on the current AXIS
stack, but only if it is staged carefully.

The original draft is strongest when read as:

- a good metric direction
- not yet a flat implementation list

So the detailed draft recommends:

- keep the idea
- narrow the first wave
- make trace-mode constraints explicit
- postpone context-sensitive metrics until AXIS defines the required semantics
- and treat behavior metrics as an analysis layer first, not as an immediate
  rewrite of all existing summaries
