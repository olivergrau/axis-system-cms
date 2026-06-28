# AXIS CMS Research Notebook Roadmap

## Goal

Create a notebook-based research layer that explains, demonstrates, and analyzes AXIS CMS as a framework for mechanistic cognitive systems.

The notebooks should combine:

* conceptual explanation
* mathematical formulation
* executable code
* experiment artifacts
* visualizations
* interpretation

The goal is not only documentation, but formalized understanding.

---

# Proposed Notebook Series

## Cross-Cutting Design Rules

The notebooks should not become arbitrary mixtures of prose, code, and plots.
They should follow a consistent research structure.

Recommended pattern inside each notebook:

1. state the question or purpose clearly
2. explain the mechanism or conceptual model
3. run a minimal demonstration
4. connect the result to persisted AXIS artifacts where appropriate
5. interpret the result
6. state limitations or non-claims

There should also be a deliberate distinction between notebook roles:

* **explain** notebooks
  concept-first, mechanism-first

* **demonstrate** notebooks
  small executable examples and trace walkthroughs

* **analyze** notebooks
  experiment-artifact interpretation and synthesis

Not every notebook must balance these equally, but the dominant role should be
clear.

---

## Research Utility Layer

To avoid repeated boilerplate, the notebook initiative should be supported by a
small shared Python helper layer, for example under:

* `research/lib/`
* `research/utils/`
* `src/axis/research/`

Potential helper modules:

* artifact loading
* series-summary / CSV loading
* trace extraction
* plotting helpers
* tabular formatting helpers
* convenience wrappers for common AXIS analyses

This is important because notebooks should foreground interpretation rather
than repeated infrastructure code.

---

## Evidence Strategy

The notebook series should intentionally combine two kinds of evidence:

* **toy examples**
  simple in-notebook constructions used to explain a mechanism

* **real experiment artifacts**
  persisted AXIS runs, comparisons, traces, and series outputs

Recommended sequence where possible:

1. minimal worked example
2. real AXIS artifact
3. interpretation

This keeps the notebooks both understandable and empirically grounded.

---

## `00_research_methodology_and_evidence.ipynb`

**Purpose:** Establish how AXIS CMS research claims should be read.

Topics:

* what counts as evidence in AXIS
* difference between trace-level evidence and aggregate metrics
* why metrics are not behavior by themselves
* why system/world comparisons matter
* how notebook claims should be scoped

Demonstrations:

* load one run summary
* load one comparison summary
* load one episode trace excerpt
* show how each supports a different kind of claim

Core message:

> AXIS results become meaningful only when mechanistic explanation, traces,
> metrics, and comparisons are interpreted together.

---

## `00_axis_cms_research_program.ipynb`

**Purpose:** Establish the motivation and research framing.

Topics:

* What AXIS is
* What AXIS CMS is
* Why mechanistic systems
* Why mathematical models instead of imperative behavior logic
* Difference between performance optimization and behavioral understanding
* AXIS CMS as a laboratory for minimal cognitive systems

Core message:

> AXIS CMS is not the final AXIS vision. It is the experimental substrate for studying mechanistic cognitive building blocks.

---

## `01_the_agent_environment_loop.ipynb`

**Purpose:** Explain the fundamental loop.

Topics:

* `observe → decide → act → world evolves → observe → transition`
* System vs framework vs world responsibilities
* Why systems do not mutate the world directly
* Why worlds shape behavior
* How traces are produced

Demonstrations:

* load one recorded episode
* inspect one step trace
* show observation, decision data, action outcome, transition data

Core message:

> Behavior is not produced by the agent alone, but by the closed loop between agent, world, and framework.

Secondary methodological message:

> Episode traces are not just logs. They are the primary bridge from code
> execution to mechanistic explanation.

---

## `02_mechanistic_drives_hunger.ipynb`

**Purpose:** Explain the simplest drive model.

Topics:

* homeostasis
* energy
* hunger activation
* resource-based action scoring
* System A as baseline
* why this is not planning

Demonstrations:

* plot hunger activation over energy
* calculate action scores for sample observations
* run or load System A experiment
* analyze survival, resource gain, movement behavior

Core message:

> Hunger is modeled as a scalar homeostatic pressure that transforms local resource observations into action tendencies.

---

## `03_curiosity_and_novelty.ipynb`

**Purpose:** Explain curiosity as a mechanistic novelty drive.

Topics:

* spatial novelty
* sensory novelty
* observation buffer
* visit-count world model
* curiosity activation
* curiosity action scores
* hunger-curiosity arbitration

Demonstrations:

* visualize novelty decay from visit counts
* compare spatial vs sensory novelty
* show how curiosity changes movement preferences
* analyze System A+W traces

Core message:

> Exploration is not random. It emerges from mathematically defined novelty gradients.

---

## `04_drive_arbitration_and_behavioral_phases.ipynb`

**Purpose:** Analyze the interaction between hunger and curiosity.

Topics:

* Maslow-like arbitration
* hunger gating curiosity
* phase-like behavior
* exploration vs foraging
* energy as a regime variable

Demonstrations:

* plot hunger and curiosity weights over energy
* inspect transitions between exploration and foraging
* analyze episodes where behavior switches
* compare System A and System A+W

Core message:

> Behavioral regimes emerge from continuous drive interaction, not from hardcoded modes.

---

## `05_worlds_shape_behavior.ipynb`

**Purpose:** Make the world-dependence of behavior explicit.

Topics:

* why systems are environment-dependent
* resource density
* sparse vs dense worlds
* uniform vs clustered worlds
* regeneration dynamics
* obstacles and topology

Demonstrations:

* run or load world variation series
* compare same system across different worlds
* plot survival, efficiency, coverage, trajectory divergence
* interpret why results change

Core message:

> Cognitive mechanisms only become meaningful relative to the structure of the world they operate in.

---

## `06_prediction_and_structure.ipynb`

**Purpose:** Explain prediction as local reliability learning.

Topics:

* predictive memory
* context encoding
* expected next features
* confidence and frustration traces
* modulation of action expression
* why prediction needs environmental regularity

Demonstrations:

* show context encoding examples
* visualize trace updates
* compare prediction in clustered vs uniform resource worlds
* analyze when prediction helps and when it does not

Core message:

> Prediction is useful only when the world contains exploitable structure.

Important analytical caution:

* this notebook should explicitly distinguish
  * prediction as a mechanism
  * prediction as a performance benefit
* the current AXIS findings suggest those are not identical

---

## `07_system_composition_a_aw_c_cw.ipynb`

**Purpose:** Explain the system progression.

Topics:

* System A: hunger only
* System A+W: hunger + curiosity + world model
* System C: hunger + prediction
* System C+W: hunger + curiosity + world model + prediction
* reduction properties
* what each extension adds

Demonstrations:

* side-by-side system table
* load comparable runs
* compare metrics and traces
* show how behavior changes as mechanisms are added

Core message:

> AXIS CMS grows cognition by controlled composition, not by replacing systems with larger black boxes.

This notebook should explicitly include:

* reduction-property discussion
* what each additional mechanism contributes
* what remains unchanged across systems

This is important because controlled reduction is one of the strongest
scientific features of AXIS CMS.

---

## `08_experiment_series_analysis.ipynb`

**Purpose:** Analyze complete experiment series.

Topics:

* series summaries
* OFAT logic
* baseline vs candidate interpretation
* metrics and tradeoffs
* why raw performance is not the only target

Demonstrations:

* load `series-summary.md`, JSON, or CSV artifacts
* create plots for death rate, vitality, energy efficiency, unique cells
* compare experiment variants
* write structured interpretations

Core message:

> Experiments become meaningful only when metrics are connected back to system mechanisms and world conditions.

Important note:

This notebook is not only about plotting series outputs. It should help define
how AXIS series are read as structured arguments:

* baseline anchor
* controlled variation
* metric shifts
* mechanistic interpretation
* limits of the conclusion

---

## `09_from_mechanistic_agents_to_cognitive_systems.ipynb`

**Purpose:** Bridge AXIS CMS back to the larger AXIS vision.

Topics:

* what the current systems already demonstrate
* what they do not demonstrate
* why this is not yet a synthetic mind
* missing elements:

  * richer memory
  * perception
  * recursive self-model
  * language
  * long-range planning
  * multi-agent interaction

Core message:

> AXIS CMS is already sufficient to study meaningful cognitive primitives, but
> it is still only an early substrate rather than a complete cognitive system.

---

## Additional Candidate Notebooks

These may be added later if the main sequence proves useful:

### `trace_reading_and_episode_anatomy.ipynb`

Focus:

* how to read one episode trace in detail
* step anatomy
* what different trace fields mean

### `reduction_properties_as_scientific_controls.ipynb`

Focus:

* why reduction properties matter
* A+W to A
* C to A
* C+W to A+W

### `metrics_are_not_behavior.ipynb`

Focus:

* strengths and limits of aggregate metrics
* why trace inspection and comparisons still matter

### `what_prediction_needs_from_worlds.ipynb`

Focus:

* prediction as a relation between mechanism and environment
* why structure in the world is a precondition for useful learning

Core message:

> AXIS CMS studies the lower mechanistic layers from which more complex cognitive architectures may eventually be constructed.

---

# Recommended Build Order

I would not build them strictly from 00 to 09.

I would start with the notebooks that create the strongest intellectual foundation:

1. `00_research_methodology_and_evidence.ipynb`
2. `00_axis_cms_research_program.ipynb`
3. `01_the_agent_environment_loop.ipynb`
4. `05_worlds_shape_behavior.ipynb`
5. `02_mechanistic_drives_hunger.ipynb`
6. `03_curiosity_and_novelty.ipynb`
7. `06_prediction_and_structure.ipynb`

Then later:

8. `04_drive_arbitration_and_behavioral_phases.ipynb`
9. `07_system_composition_a_aw_c_cw.ipynb`
10. `08_experiment_series_analysis.ipynb`
11. `09_from_mechanistic_agents_to_cognitive_systems.ipynb`

Reason: the world-dependence notebook should come early, because it reframes the whole project.

---

# Suggested Repository Placement

```text
notebooks/
  axis-cms-research/
    00_research_methodology_and_evidence.ipynb
    00_axis_cms_research_program.ipynb
    01_the_agent_environment_loop.ipynb
    02_mechanistic_drives_hunger.ipynb
    03_curiosity_and_novelty.ipynb
    04_drive_arbitration_and_behavioral_phases.ipynb
    05_worlds_shape_behavior.ipynb
    06_prediction_and_structure.ipynb
    07_system_composition_a_aw_c_cw.ipynb
    08_experiment_series_analysis.ipynb
    09_from_mechanistic_agents_to_cognitive_systems.ipynb
```

Optional later:

```text
notebooks/
  axis-cms-research/
    assets/
    data/
    figures/
    utils/
```

---

# Notebook Template

Each notebook should follow the same rhythm:

```text
1. Research question
2. Conceptual background
3. Mathematical model
4. AXIS CMS implementation mapping
5. Small worked example
6. Experiment / artifact loading
7. Visualization
8. Interpretation
9. Takeaways
```

That structure prevents the notebooks from becoming random demos.

---

# A strong recommendation

Make the notebooks **research essays with executable evidence**, not tutorials.

A tutorial says:

> Here is how to use the framework.

Your notebooks should say:

> Here is what this mechanism means, why it was modeled this way, and what behavior it produces.

That is the difference between documentation and research output.
