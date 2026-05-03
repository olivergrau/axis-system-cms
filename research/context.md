## AXIS CMS – Motivation, Current State, and Next Step

### Motivation

The goal of AXIS is to understand the foundations of cognitive systems not through black-box models, but through **explicit, mechanistic construction**.

At its core, the central question is:

> What are the minimal mechanisms required for adaptive, goal-directed behavior to emerge?

The approach is based on a few key principles:

* Behavior is **not hardcoded**, but arises from
  **coupled mathematical subsystems** (drives, memory, prediction)

* Systems operate within a simple but strict loop:

  ```
  observe → decide → act → world evolves → observe → transition
  ```

* Intelligence is treated as an **emergent property** of the interaction
  between system and environment

A fundamental assumption is:

> Systems cannot be understood in isolation, only in the context of their environment.

This should not be read as a permanent rejection of machine learning,
reinforcement learning, or other more black-box-like methods.

What it means for AXIS CMS is something narrower and more architectural:

> if such methods enter the system, they should do so as bounded subsystems,
> not as a monolithic replacement for the whole architecture.

So the real commitment is not:

* "never use learned or partially opaque methods"

The real commitment is:

* keep the system decomposable
* keep the main feedback structure understandable
* make the role of any learned component explicit at the system level

That still leaves room for future learned subsystems such as:

* goal-directed movement modules
* local prediction helpers
* logic or routing layers
* perception-related preprocessing
* specialized behavioral control subroutines

This is closer to a compositional picture of cognition: many interacting
subsystems with different roles, some more explicit and some potentially more
learned, embedded in a larger feedback architecture.

---

### Current State: AXIS CMS

AXIS CMS is a fully functional experimentation framework for building and analyzing such systems.

Core properties:

* Modular architecture:

  * **Systems** (agent logic)
  * **Worlds** (environment dynamics)
  * **Framework** (execution, logging, comparison, visualization)

* Mechanistic system progression:

  * **System A**: pure hunger drive (baseline)
  * **System A+W**: hunger + curiosity + minimal world model
  * **System C**: predictive modulation
  * **System C+W**: combined drives, world model, and prediction

* Core modeling concepts:

  * Drives (hunger, curiosity)
  * Observation buffer (episodic memory)
  * Visit-count world model (spatial familiarity)
  * Predictive memory with confidence / frustration traces
  * Drive arbitration (e.g. hunger vs curiosity)

* Experimental infrastructure:

  * deterministic execution (seeded runs)
  * experiment series (OFAT, parameter sweeps)
  * behavioral metrics (survival, efficiency, coverage, etc.)
  * full step-level traces and replay
  * structured comparison between runs and systems

In essence:

> AXIS CMS is a controlled laboratory for minimal cognitive systems.

---

### Key Insights So Far

Several important findings have already emerged:

* **Behavior is strongly environment-dependent**
  The same system behaves very differently across different world configurations

* **Prediction is not universally useful**
  It performs well in structured environments (e.g. clustered resources),
  but provides little value in uniform or sparse distributions

* **Exploration emerges from structure, not randomness**
  Curiosity produces movement along novelty gradients, not random behavior

* **Drive interaction creates phase-like behavior**
  e.g. exploration vs foraging depending on energy state

These are not just observations, but reproducible outcomes of the models.

---

### Current Gap / Next Step

So far, the focus has been on:

* building systems
* running experiments
* collecting and comparing metrics

What is missing is:

> a structured, explicit formulation of the insights and principles

Without this, AXIS CMS remains:

* a powerful framework
* but without a clearly articulated knowledge layer or theory

---

### New Direction: Jupyter Notebook-Based Analysis

The next step is to build a structured set of Jupyter Notebooks that:

* explain the systems
* demonstrate their behavior
* analyze experimental results
* connect models to broader cognitive and biological ideas

The goal is to combine:

* **theory** (Markdown explanations)
* **mathematics**
* **code execution**
* **experimental data**
* **visualization**
* **interpretation**

In other words:

> turn AXIS CMS from an experimentation framework into a documented, explainable research environment

These notebooks will serve as:

* a formalization of the current understanding
* a communication layer for others (and future self)
* a bridge from mechanistic models to higher-level cognitive system theory

---

### Methodological Clarification

The notebook layer should not become a loose collection of visualizations or
ad-hoc result dumps. It should function as a **research layer** with a clear
epistemic role.

That means the notebooks should distinguish between different kinds of work:

* **explanation**
  clarify concepts, mechanisms, equations, and architectural roles

* **demonstration**
  show small executable examples or trace excerpts that make the mechanism
  concrete

* **analysis**
  interpret real experiment artifacts, metrics, and comparisons

Each notebook does not need to weight all three equally, but each should make
its role explicit.

Recommended internal structure per notebook:

1. research question or purpose
2. theoretical or mechanistic setup
3. executable demonstration
4. interpretation
5. limitations / what this does **not** show

This is important because AXIS CMS is not only a software project. It is meant
to become a structured body of mechanistic understanding.

---

### What Counts as Evidence in AXIS CMS

The research layer should make explicit that not all outputs have the same
status.

Within AXIS CMS, useful evidence exists at multiple levels:

* **worked toy examples**
  small synthetic examples created inside a notebook to clarify one mechanism

* **single-step or single-episode traces**
  useful for local mechanistic explanation

* **run-level metrics**
  useful for aggregate behavioral tendencies

* **series-level comparisons**
  useful for understanding parameter tradeoffs and world-dependence

* **cross-system comparisons**
  useful for understanding what additional mechanisms actually change

A key rule for the notebook initiative should be:

> Metrics alone are not behavior, and traces alone are not sufficient for
> generalization.

The strongest AXIS arguments usually come from combining:

* a mechanism claim
* a local trace demonstration
* an aggregate metric pattern
* a comparison against an alternative system or world condition

---

### Data Strategy for the Notebook Layer

The notebook layer should intentionally use **two complementary data sources**:

* **didactic toy constructions**
  small in-notebook examples that isolate one formula or mechanism

* **real AXIS experiment artifacts**
  persisted traces, run summaries, comparison outputs, and series summaries

This distinction matters:

* toy examples are easier to understand
* real artifacts are necessary for scientific credibility

The best notebooks will often follow this sequence:

1. introduce the mechanism with a minimal example
2. reproduce it with real persisted AXIS data
3. interpret the result in relation to system design and world structure

---

### Research Utility Layer

To keep notebooks readable, the research initiative should avoid placing too
much parsing, formatting, and plotting boilerplate directly in notebook cells.

It is therefore useful to build a small shared helper layer, for example under
one of these roots:

* `research/lib/`
* `research/utils/`
* `src/axis/research/`

Potential shared helpers:

* loading `series-summary.json`, `series-metrics.csv`, and comparison outputs
* loading episode traces and extracting selected steps
* small plotting helpers for metrics and trajectories
* helper functions for arbitration, novelty, and prediction tables
* formatting utilities for notebook display

This keeps notebooks focused on ideas and interpretation rather than repeated
infrastructure code.

---

### Why This Next Step Fits AXIS CMS

The research notebook initiative is not separate from AXIS CMS. It is the next
natural layer above it.

AXIS CMS already provides:

* systems
* worlds
* runs
* comparisons
* metrics
* traces
* experiment series

What it does not yet provide in a sufficiently explicit way is a structured
knowledge layer that says:

* what these mechanisms mean
* what they demonstrate
* where their limits are
* how the empirical patterns connect back to cognitive-system questions

So the notebook initiative should be understood as:

> the interpretive and explanatory layer built on top of the existing AXIS CMS
> laboratory

That is the step that turns a strong experimentation framework into a clearer
research environment.

---

### Scope Clarification

AXIS CMS currently focuses on explicit mechanistic modeling because that is the
right level for the present stage of the project.

But this should not be mistaken for a claim that future cognitive systems must
avoid all more opaque methods.

The stronger constraint is architectural, not ideological:

* the overall system should remain inspectable enough to study
* subsystems should have intelligible roles
* new learned components should enrich the architecture rather than collapse it
  into one undifferentiated global black box

So the meaningful contrast is not:

* mechanistic models vs any learned models

It is:

* compositional, inspectable architectures
* vs total system-level opacity

That distinction matters because it keeps AXIS CMS open to future growth while
preserving the central goal of structured understanding.
