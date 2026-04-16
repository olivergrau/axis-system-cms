# AXIS - Paired Trace Comparison

## Draft for Comparative Run Analysis Across Systems

---

## 1. Purpose

This document proposes a first draft for a **paired trace comparison** concept in AXIS.

The goal is to make behavioral differences between two systems observable in a structured and interpretable way when both systems are executed under matched experimental conditions.

The primary motivating example is:

- `System A` as the hunger-driven baseline
- `System C` as the prediction-augmented hunger system

This document is not an engineering specification.

It is a draft-level design document intended to define:

- what a paired comparison means in AXIS
- what kinds of differences should be measured
- which signals are already available in current traces
- which later trace extensions may be desirable for deeper analysis

---

## 2. Problem Statement

AXIS already supports:

- deterministic experiment execution
- explicit system configurations
- deterministic episode seeding
- persisted episode traces for replay and visualization

This is sufficient to inspect runs individually.

However, it does not yet provide a formal concept for comparing two runs as a paired analytical object.

Without such a concept, an important question remains underspecified:

> What exactly changed in behavior when a new mechanism was introduced?

For example, when moving from `System A` to `System C`, we do not only want to know whether survival improved.

We also want to know:

- when behavior first diverged
- how strongly action selection changed
- whether trajectory structure changed
- whether prediction altered decisions only weakly or actually re-ranked actions

This requires a comparison layer above single-run replay.

---

## 3. Core Proposal

Introduce a conceptual analysis object:

> a **paired trace comparison**

This object compares two episode traces generated under matched conditions and produces a structured difference report.

The intended first use case is:

- same world type
- same world configuration
- same episode seed
- same start position
- different system type or system configuration

Conceptually:

```text
Episode Trace A + Episode Trace B + pairing constraints
-> comparison metrics
-> comparison report
```

The result is not a replay trace.

It is an analysis artifact derived from two replay traces.

---

## 4. Comparison Unit

The fundamental unit of comparison should be:

> one episode trace from run A paired with one episode trace from run B

This means the primary comparison object is episode-level, not run-level.

Run-level comparisons can later be defined as aggregates over many paired episode comparisons.

### 4.1 Why Episode-Level Pairing Comes First

Episode-level pairing has three advantages:

- it preserves interpretability
- it supports stepwise divergence analysis
- it makes causal comparison under matched seeds possible

By contrast, pure run-level summary comparison loses the stepwise structure that is central for understanding behavioral change.

---

## 5. Pairing Constraints

Two episode traces may only be treated as a valid paired comparison if the following constraints hold.

### 5.1 Required Constraints

- same world type
- same world configuration
- same episode seed
- same start position
- same episode index within the run, if episode seeds are derived by index

### 5.2 Expected Differences

The following may differ:

- `system_type`
- `system_config`
- any internal mechanism that changes decision making

### 5.3 Pairing Principle

The comparison must preserve all relevant environmental causes while changing only the system-side cause under investigation.

This gives paired comparison its interpretive value.

---

## 6. Three Analysis Levels

The comparison concept should distinguish three levels of analytical questions.

### 6.1 Level 1: Outcome Comparison

This level measures what happened by the end of the episode.

Typical metrics:

- total steps survived
- final vitality
- termination reason
- total movement count
- total consume count
- total stay count
- total path length
- total consumed resource, if derivable

These metrics answer:

> Did one system perform differently overall?

### 6.2 Level 2: Behavioral Divergence

This level measures how the two trajectories differed over time.

Typical metrics:

- first timestep at which selected actions differ
- action mismatch count
- action mismatch rate
- first timestep at which positions differ
- position divergence over time
- vitality difference over time
- whether the trajectories ever reconverge

These metrics answer:

> When and how did behavior start to separate?

### 6.3 Level 3: Mechanism Comparison

This level explains why behavior differed, using system-specific signals where available.

For `System C`, useful metrics include:

- how often `modulated_scores` differ from raw `action_contributions`
- how often prediction changes the top-ranked action
- how large the modulation effect is per action
- how often positive versus negative prediction error dominates

These metrics answer:

> Did the new mechanism merely perturb scores, or did it actually restructure action choice?

---

## 7. Minimal Comparison Metrics

A first viable paired comparison draft should define a small metric core.

The following five metrics are sufficient for an initial version.

### 7.1 First Action Divergence Step

Definition:

- the first timestep `t` at which the selected action in trace A differs from trace B

Interpretation:

- identifies when the two systems first behaviorally separate

### 7.2 Action Mismatch Rate

Definition:

- the fraction of aligned timesteps for which the selected action differs

Interpretation:

- quantifies the overall behavioral divergence in action space

### 7.3 Trajectory Divergence Over Time

Definition:

- a stepwise position difference measure between both traces

Possible initial form:

- Manhattan distance between agent positions at each aligned timestep

Interpretation:

- captures how far behavior diverges in world space

### 7.4 Vitality Curve Difference

Definition:

- stepwise difference in vitality or energy over aligned timesteps

Interpretation:

- captures the physiological consequence of behavioral divergence

### 7.5 Prediction-Induced Top-Action Change Count

Definition:

- for `System C`, count the timesteps where the top action under raw drive scores differs from the top action under modulated scores

Interpretation:

- distinguishes weak score perturbation from behaviorally meaningful modulation

This metric is asymmetric and system-specific.

That is acceptable.

The comparison object should allow both:

- system-agnostic metrics
- system-specific mechanism metrics

---

## 8. Data Already Available in Current Traces

The current AXIS trace contract already supports a meaningful first comparison layer.

### 8.1 Available in Base Trace Structure

Current step traces already provide:

- timestep
- selected action
- position before and after
- vitality before and after
- world snapshots
- opaque `system_data`

This is sufficient for:

- outcome metrics
- action divergence metrics
- position divergence metrics
- vitality curve comparison

### 8.2 Available in System A Traces

`System A` currently persists:

- observation
- drive activation
- raw action contributions
- policy probabilities
- selected action
- energy transition data

This gives a stable baseline for hunger-driven behavior without predictive modulation.

### 8.3 Available in System C Traces

`System C` currently persists:

- observation
- drive activation
- raw action contributions
- predictive context
- predictive features
- modulated scores
- policy probabilities
- prediction update data:
  - predicted features
  - observed features
  - positive scalar error
  - negative scalar error

This is already enough to support a first mechanism-aware comparison draft.

---

## 9. Current Limitations of Trace Support

The current trace structure is good enough for a first draft, but not yet ideal for deeper comparison specs.

### 9.1 Episode Seed Is Indirect

The episode seed is currently derivable from run configuration and episode index, but not directly stored on the episode trace itself.

This is workable, but not ideal.

For later specifications, explicit per-episode seed recording would improve clarity and reduce reconstruction assumptions.

### 9.2 Internal Predictive State Is Not Explicitly Persisted

`System C` currently persists prediction errors and modulated scores, but not the full current modulation state.

Not directly persisted:

- per-action frustration trace values
- per-action confidence trace values
- per-action modulation factors as first-class values

This limits how precisely later analysis can explain the internal mechanism of divergence.

### 9.3 Comparison-Relevant Derived Facts Are Not Yet Recorded

Some highly useful analytical facts are currently derivable only indirectly or not at all.

Examples:

- whether modulation changed the top-ranked action
- whether the chosen action differed from the raw-drive optimum
- whether a step counts as "prediction-active" in a strict sense

These can be reconstructed in some cases, but explicit recording may be preferable in a later spec.

---

## 10. Comparison Semantics

The comparison concept should distinguish between three semantic classes of differences.

### 10.1 Performance Difference

A difference in outcome quality.

Examples:

- one system survives longer
- one system retains higher final vitality
- one system consumes more resource

### 10.2 Behavioral Difference

A difference in the realized sequence of actions or visited positions.

Examples:

- earlier movement toward a resource
- more staying
- more directional commitment

### 10.3 Mechanistic Difference

A difference caused by internal system mechanisms rather than direct environmental change.

Examples:

- prediction suppresses a previously preferred move
- prediction reinforces revisiting a productive action-context pair
- modulation changes the selected action despite identical drive baseline

These three difference classes should not be collapsed into a single score.

They should remain analytically distinct.

---

## 11. Relationship to Existing AXIS Layers

The paired comparison concept should not be placed in the SDK itself.

The SDK should continue to define:

- replay contracts
- trace structure
- system execution interfaces

The comparison concept belongs above replay persistence and beside visualization.

A suitable long-term placement would be:

- analysis layer
- replay analysis utilities
- or experiment comparison tooling

Conceptually:

```text
SDK defines traces.
Framework produces traces.
Analysis compares traces.
Visualization presents traces and comparisons.
```

---

## 12. Proposed Initial Scope

The initial draft should stay intentionally narrow.

### 12.1 In Scope

- paired comparison of two episode traces
- comparison under matched seeds and matched world conditions
- system-agnostic outcome metrics
- system-agnostic divergence metrics
- first system-specific metrics for `System C`

### 12.2 Out of Scope for the First Draft

- multi-run statistical significance
- population-level hypothesis testing
- generic comparison logic for arbitrary world ontologies
- automatic causal attribution beyond observable trace differences
- engineering architecture for UI, storage, or CLI

---

## 13. First Spec Questions

Before a deeper specification is written, the following questions should be fixed explicitly.

### 13.1 Pairing Identity

Should pairing be defined by:

- explicit episode seed
- episode index plus run seed derivation
- or both

### 13.2 Alignment Rule

When one episode terminates earlier than the other, should comparison metrics:

- align only on the shared prefix
- pad the shorter trace
- or switch to post-termination outcome-only comparison

### 13.3 Metric Vocabulary

Which metrics should be mandatory in the first spec, and which should remain optional system-specific extensions?

### 13.4 System-Specific Sections

How should a general paired comparison format expose mechanism-specific analysis such as prediction modulation in `System C` without hard-coding those semantics into a generic trace layer?

---

## 14. Recommended Next Step

The next document derived from this draft should be a more formal **paired trace comparison spec**.

That spec should define:

- the pairing contract
- episode alignment rules
- the exact metric set for version 1
- required versus optional fields
- how system-specific analysis blocks attach to a generic comparison report

For the transition from draft to spec, the most important design principle should be:

> keep the comparison framework generic, while allowing system-specific mechanism reports as explicit extensions

---

## 15. Summary

Paired trace comparison should become the first formal analysis concept for answering:

> What changed when one AXIS system was replaced by another under matched conditions?

The current AXIS traces are already strong enough to support a first version of this idea.

They are especially well suited for:

- outcome comparison
- behavioral divergence analysis
- first-pass mechanism analysis for `System C`

For deeper future specs, trace extensions may later improve:

- pairing clarity
- internal mechanism visibility
- direct measurability of predictive influence

The essential point is:

paired comparison is not a replay feature and not a framework concern.

It is a separate analysis concept built on top of the replay traces AXIS already produces.
